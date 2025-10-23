# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Ranking systems for QPDO dueling bandit optimization.

This module implements multiple ranking algorithms including Copeland,
Borda, Elo, average win-rate, and TrueSkill rankings.
"""

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Optional dependency handling
try:
    from trueskill import Rating, rate

    HAS_TRUESKILL = True
except ImportError:
    HAS_TRUESKILL = False


def copeland_ranking(win_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Copeland ranking with win-rate tie-breaker.

    Primary score: (# opponents beaten) - (# opponents lost to).
    Tie-breaker: higher average win rate across opponents.

    Args:
        win_matrix: W[i,j] = wins of i over j

    Returns:
        Tuple of (ranking_order, copeland_scores)
    """
    total_matches = win_matrix + win_matrix.T
    n = len(win_matrix)

    copeland_scores = np.zeros(n)
    avg_winrate = np.zeros(n)

    for i in range(n):
        wins = 0
        losses = 0
        winrate_sum = 0.0
        opp_count = 0
        for j in range(n):
            if i == j:
                continue
            tm = total_matches[i, j]
            if tm > 0:
                if win_matrix[i, j] > win_matrix[j, i]:
                    wins += 1
                elif win_matrix[i, j] < win_matrix[j, i]:
                    losses += 1

                winrate_sum += win_matrix[i, j] / tm
                opp_count += 1
        copeland_scores[i] = wins - losses
        avg_winrate[i] = (winrate_sum / opp_count) if opp_count > 0 else 0.0

    # Sort by Copeland desc, then average win rate desc (tie-breaker)
    ranking_order = np.lexsort((-avg_winrate, -copeland_scores))
    return ranking_order, copeland_scores


def borda_ranking(win_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Borda count ranking: sum of win rates against all opponents.

    Args:
        win_matrix: W[i,j] = wins of i over j

    Returns:
        Tuple of (ranking_order, borda_scores)
    """
    total_matches = win_matrix + win_matrix.T
    borda_scores = np.zeros(len(win_matrix))

    for i in range(len(win_matrix)):
        total_score = 0
        for j in range(len(win_matrix)):
            if i != j and total_matches[i, j] > 0:
                win_rate = win_matrix[i, j] / total_matches[i, j]
                total_score += win_rate
        borda_scores[i] = total_score

    ranking_order = np.argsort(-borda_scores)
    return ranking_order, borda_scores


def avg_winrate_ranking(win_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Average win rate ranking: average win rate across all opponents.

    Args:
        win_matrix: W[i,j] = wins of i over j

    Returns:
        Tuple of (ranking_order, avg_winrate_scores)
    """
    total_matches = win_matrix + win_matrix.T
    avg_winrate_scores = np.zeros(len(win_matrix))

    for i in range(len(win_matrix)):
        total_winrate = 0
        num_opponents = 0
        for j in range(len(win_matrix)):
            if i != j and total_matches[i, j] > 0:
                win_rate = win_matrix[i, j] / total_matches[i, j]
                total_winrate += win_rate
                num_opponents += 1

        if num_opponents > 0:
            avg_winrate_scores[i] = total_winrate / num_opponents
        else:
            avg_winrate_scores[i] = 0.5  # Default for no matches

    ranking_order = np.argsort(-avg_winrate_scores)
    return ranking_order, avg_winrate_scores


def elo_ranking(
    win_matrix: np.ndarray, k_factor: float = 32, initial_rating: float = 1500
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Elo ranking system.

    Args:
        win_matrix: W[i,j] = wins of i over j
        k_factor: Elo K-factor for rating updates
        initial_rating: Initial rating for all players

    Returns:
        Tuple of (ranking_order, elo_ratings)
    """
    n = len(win_matrix)
    elo_ratings = np.full(n, initial_rating, dtype=float)

    # Process all matches in order (simplified approach)
    for i in range(n):
        for j in range(i + 1, n):
            wins_i = win_matrix[i, j]
            wins_j = win_matrix[j, i]

            # Process each individual match
            for _ in range(int(wins_i)):
                # i beats j
                expected_i = 1 / (1 + 10 ** ((elo_ratings[j] - elo_ratings[i]) / 400))
                expected_j = 1 - expected_i

                elo_ratings[i] += k_factor * (1 - expected_i)
                elo_ratings[j] += k_factor * (0 - expected_j)

            for _ in range(int(wins_j)):
                # j beats i
                expected_i = 1 / (1 + 10 ** ((elo_ratings[j] - elo_ratings[i]) / 400))
                expected_j = 1 - expected_i

                elo_ratings[i] += k_factor * (0 - expected_i)
                elo_ratings[j] += k_factor * (1 - expected_j)

    ranking_order = np.argsort(-elo_ratings)
    return ranking_order, elo_ratings


def aggregate_ranks(rankings: List[np.ndarray]) -> np.ndarray:
    """
    Aggregate multiple rankings using Borda count.

    Args:
        rankings: List of ranking orders (each is array of indices)

    Returns:
        Aggregated scores (higher is better)
    """
    if not rankings:
        return np.array([])

    n = len(rankings[0])
    scores = np.zeros(n)

    for ranking in rankings:
        for position, candidate in enumerate(ranking):
            # Higher position = lower score in ranking, so invert
            scores[candidate] += n - position

    return scores


def compare_json_task(
    response1: Dict[str, Any], response2: Dict[str, Any]
) -> Tuple[float, float, float, List[str]]:
    """
    Compare two JSON responses for task evaluation.

    Args:
        response1: First JSON response
        response2: Second JSON response (ground truth or comparison)

    Returns:
        Tuple of (precision, recall, f1_score, diff_log)
    """
    # Simple implementation - can be enhanced based on specific task needs
    if response1 == response2:
        return 1.0, 1.0, 1.0, []

    # Basic field-by-field comparison
    diff_log = []
    matching_fields = 0
    total_fields = max(len(response1), len(response2))

    if total_fields == 0:
        return 1.0, 1.0, 1.0, []

    for key in set(response1.keys()) | set(response2.keys()):
        if key in response1 and key in response2:
            if response1[key] == response2[key]:
                matching_fields += 1
            else:
                diff_log.append(
                    f"Field '{key}': got {response1[key]}, expected {response2[key]}"
                )
        elif key in response1:
            diff_log.append(f"Extra field '{key}': {response1[key]}")
        else:
            diff_log.append(f"Missing field '{key}': {response2[key]}")

    precision = matching_fields / len(response1) if response1 else 0.0
    recall = matching_fields / len(response2) if response2 else 0.0
    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return precision, recall, f1_score, diff_log


class TrueSkillFromCounts:
    """TrueSkill ranking system implementation."""

    def __init__(
        self,
        mu0: float = 25.0,
        sigma0: float = 25.0 / 3,
        solver: str = "exact",
        damping: float = 0.9,
        epochs: int = 50,
        track_history: bool = False,
    ):
        if not HAS_TRUESKILL:
            raise ImportError(
                "TrueSkill library not available. Install with: pip install trueskill"
            )

        self.mu0 = mu0
        self.sigma0 = sigma0
        self.solver = solver
        self.damping = damping
        self.epochs = epochs
        self.track_history = track_history

    def fit(self, win_matrix: np.ndarray):
        """
        Fit TrueSkill ratings from win matrix.

        Args:
            win_matrix: W[i,j] = wins of i over j

        Returns:
            TrueSkillRatings object with mu, sigma, conservative scores, and ranking
        """
        n = len(win_matrix)

        # Initialize ratings
        ratings = [Rating(mu=self.mu0, sigma=self.sigma0) for _ in range(n)]

        # Process all matches
        for epoch in range(self.epochs):
            for i in range(n):
                for j in range(i + 1, n):
                    wins_i = int(win_matrix[i, j])
                    wins_j = int(win_matrix[j, i])

                    # Process each match
                    for _ in range(wins_i):
                        # i beats j
                        new_ratings = rate([(ratings[i],), (ratings[j],)], ranks=[0, 1])
                        ratings[i] = new_ratings[0][0]
                        ratings[j] = new_ratings[1][0]

                    for _ in range(wins_j):
                        # j beats i
                        new_ratings = rate([(ratings[j],), (ratings[i],)], ranks=[0, 1])
                        ratings[j] = new_ratings[0][0]
                        ratings[i] = new_ratings[1][0]

        # Extract final ratings
        mu = np.array([r.mu for r in ratings])
        sigma = np.array([r.sigma for r in ratings])
        conservative = mu - 3 * sigma  # Conservative estimate

        # Create ranking based on conservative scores
        rank_order = np.argsort(-conservative)

        return TrueSkillRatings(
            mu=mu, sigma=sigma, conservative=conservative, rank_order=rank_order
        )


class TrueSkillRatings:
    """Container for TrueSkill rating results."""

    def __init__(
        self,
        mu: np.ndarray,
        sigma: np.ndarray,
        conservative: np.ndarray,
        rank_order: np.ndarray,
    ):
        self.mu = mu
        self.sigma = sigma
        self.conservative = conservative
        self.rank_order = rank_order
