# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Thompson sampling algorithms for PDO dueling bandit optimization.

This module implements Double Thompson Sampling with variance-based selection
and multi-ranker fusion for prompt duel optimization.
"""

import math
from typing import Dict, List, Optional, Tuple

import numpy as np

# ------------------------- utilities -------------------------


def _normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    mn, mx = x.min(), x.max()
    if mx == mn:
        return np.zeros_like(x)
    return (x - mn) / (mx - mn)


def beta_var(a: float, b: float) -> float:
    """Variance of Beta(a, b)."""
    s = a + b
    return (a * b) / (s * s * (s + 1.0))


def fused_selection_score(
    theta: np.ndarray,
    elo_mu: np.ndarray,
    ts_mu: np.ndarray,
    ts_cons: np.ndarray,
    dirichlet: bool = True,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    """
    Build a *higher-is-better* fused score from:
      - Copeland (from θ sample)
      - Borda (from θ sample)
      - Winrate (from θ sample)
      - Elo μ
      - TrueSkill μ, conservative

    Returns:
        fused_scores: (K,) fused score
        weights:      (F,) weights used to aggregate (sampled via Dirichlet if enabled)
        features:     dict of individual feature vectors for debugging
    """
    rng = np.random.default_rng(seed)
    K = theta.shape[0]

    # Scores from the *sampled* probability matrix theta
    copeland = np.sum(theta > 0.5, axis=1)
    borda = theta.sum(axis=1)
    winrate = theta.mean(axis=1)

    # Normalize all to [0,1], higher is better
    feats = [
        _normalize(copeland),
        _normalize(borda),
        _normalize(winrate),
        _normalize(elo_mu),
        _normalize(ts_mu),
        _normalize(ts_cons),
    ]
    features = {
        "copeland": feats[0],
        "borda": feats[1],
        "winrate": feats[2],
        "elo_mu": feats[3],
        "ts_mu": feats[4],
        "ts_cons": feats[5],
    }

    F = len(feats)
    M = np.vstack(feats)  # (F, K)

    if dirichlet:
        w = rng.dirichlet(np.ones(F))
    else:
        w = np.ones(F) / F

    fused = (w[:, None] * M).sum(axis=0)  # (K,)
    return fused, w, features


# ------------------------- main sampler -------------------------


def sample_duel_pair(
    K: int,
    W: np.ndarray,
    alpha: float,
    t: int,
    allowed_indices: Optional[List[int]] = None,
    rng: Optional[np.random.Generator] = None,
    **kwargs,
) -> Tuple[int, int]:
    """
    Default sampler: Double-Thompson-Sampling (D-TS) for Copeland dueling bandits.

    Simpler, faithful D-TS:
      1) Build UCB/LCB bounds and Copeland candidate set C from UCB counts
      2) Thompson-sample pairwise win probs and choose first from C by sampled Copeland
      3) Thompson draw conditioned on first to pick the second

    Extra keyword args are accepted for backward compatibility and ignored.
    """

    if rng is None:
        rng = np.random.default_rng()

    if allowed_indices is None:
        allowed_indices = list(range(K))

    # Allow caller to pass precomputed N via kwargs; otherwise derive from W
    N = kwargs.get("N")
    if N is None:
        N = W + W.T

    if N.sum() == 0:
        first, second = rng.choice(allowed_indices, size=2, replace=False)
        return first, second

    # 1) Bounds and Copeland candidate set C
    upper = np.full((K, K), 0.5)
    lower = np.full((K, K), 0.5)
    log_term = math.log(max(t, 2))

    for i in range(K):
        for j in range(i + 1, K):
            if N[i, j] > 0:
                p_ij = W[i, j] / N[i, j]
                delta = math.sqrt(alpha * log_term / N[i, j])
                upper[i, j] = min(p_ij + delta, 1.0)
                lower[i, j] = max(p_ij - delta, 0.0)
            else:
                upper[i, j] = 1.0
                lower[i, j] = 0.0
            upper[j, i] = 1.0 - lower[i, j]
            lower[j, i] = 1.0 - upper[i, j]

    zeta_upper = np.sum(upper > 0.5, axis=1)
    C = np.flatnonzero(zeta_upper == zeta_upper.max())
    # Restrict to allowed indices
    C = [i for i in C if i in allowed_indices]
    if not C:
        C = allowed_indices

    # 2) Thompson-sampled Copeland to choose first
    theta1 = np.zeros((K, K))
    for i in range(K):
        for j in range(i + 1, K):
            th = rng.beta(W[i, j] + 1, W[j, i] + 1)
            theta1[i, j] = th
            theta1[j, i] = 1.0 - th

    copeland_scores = np.sum(theta1 > 0.5, axis=1)
    max_score = copeland_scores[C].max()
    first_candidates = [i for i in C if copeland_scores[i] == max_score]
    first = int(rng.choice(first_candidates))

    # 3) Thompson draw conditioned on the first to pick second
    theta2 = np.full(K, 0.5)
    for k in range(K):
        if k != first:
            theta2[k] = rng.beta(W[k, first] + 1, W[first, k] + 1)

    cand = [k for k in allowed_indices if k != first and lower[k, first] <= 0.5]
    if not cand:
        cand = [k for k in allowed_indices if k != first]

    best_val = max(theta2[k] for k in cand)
    second_choices = [k for k in cand if abs(theta2[k] - best_val) < 1e-12]
    second = int(rng.choice(second_choices))

    return first, second


def sample_duel_pair_fused(
    K: int,
    W: np.ndarray,  # wins matrix
    alpha: float,
    t: int,
    allowed_indices: Optional[List[int]] = None,
    elo_mu: Optional[np.ndarray] = None,
    ts_mu: Optional[np.ndarray] = None,
    ts_cons: Optional[np.ndarray] = None,
    tau: float = 0.2,  # softmax temperature for exploration across rankers
    dirichlet_weights: bool = True,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[int, int]:
    """
    Fused sampler (previous default):
      - First arm: Dirichlet-weighted fusion of Copeland/Borda/Winrate/Elo/TrueSkill
      - Second arm: uncertainty (Beta variance) against the first
    """

    if rng is None:
        rng = np.random.default_rng()

    if allowed_indices is None:
        allowed_indices = list(range(K))

    N = W + W.T
    if N.sum() == 0:  # no duels yet
        first, second = rng.choice(allowed_indices, size=2, replace=False)
        return first, second

    if elo_mu is None:
        elo_mu = np.zeros(K)
    if ts_mu is None:
        ts_mu = np.zeros(K)
    if ts_cons is None:
        ts_cons = np.zeros(K)

    # ---------- Step 1: compute CI bounds ----------
    upper = np.full((K, K), 0.5)
    lower = np.full((K, K), 0.5)

    for i in range(K):
        for j in range(i + 1, K):
            if N[i, j] > 0:
                p_ij = W[i, j] / N[i, j]
                pair_t = max(N[i, j], 2)
                delta = math.sqrt(alpha * math.log(pair_t) / N[i, j])
                upper[i, j] = min(p_ij + delta, 1.0)
                lower[i, j] = max(p_ij - delta, 0.0)
            else:
                upper[i, j] = 1.0
                lower[i, j] = 0.0
            upper[j, i] = 1.0 - lower[i, j]
            lower[j, i] = 1.0 - upper[i, j]

    # ---------- Step 2: Thompson-sample θ matrix ----------
    theta = np.zeros((K, K))
    for i in range(K):
        for j in range(i + 1, K):
            a = W[i, j] + 1
            b = W[j, i] + 1
            th = rng.beta(a, b)
            theta[i, j] = th
            theta[j, i] = 1.0 - th

    # ---------- Step 3: fuse rankers & sample FIRST arm via softmax ----------
    fused, weights, feature_dict = fused_selection_score(
        theta=theta,
        elo_mu=elo_mu,
        ts_mu=ts_mu,
        ts_cons=ts_cons,
        dirichlet=dirichlet_weights,
        seed=None,
    )

    scores = fused[allowed_indices] + rng.normal(0, 1e-6, size=len(allowed_indices))
    scores_stable = scores / max(tau, 1e-8)
    scores_stable -= scores_stable.max()
    probs = np.exp(scores_stable)
    probs /= probs.sum()
    first = rng.choice(allowed_indices, p=probs)

    # Step 4: Choose SECOND arm by uncertainty vs first
    cand = [k for k in allowed_indices if k != first and lower[k, first] <= 0.5]
    if not cand:
        cand = [k for k in allowed_indices if k != first]

    if cand:
        rng.shuffle(cand)
        variances = np.array([beta_var(W[k, first] + 1, W[first, k] + 1) for k in cand])
        variances += rng.normal(0, 1e-6, size=len(variances))
        match_counts = W.sum(axis=1)
        decay = 1 / (1 + match_counts[cand])
        weighted = variances * decay
        probs = weighted / weighted.sum()
        second = rng.choice(cand, p=probs)
    else:
        second = rng.choice([k for k in range(K) if k != first])

    return int(first), int(second)
