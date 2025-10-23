# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
QPDO optimization engine.

This module implements the core dueling bandit optimization loop using
Thompson sampling, multiple ranking systems, and instruction evolution.
"""

import json
import logging
import random
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    from ..model import ModelAdapter

from .meta_prompt import (
    DATASET_DESCRIPTOR_PROMPT,
    EVALUATE_PROMPT,
    EVALUATE_SCHEMA,
    INITIAL_INSTRUCTION_TIPS,
    INSTRUCTION_PROPOSER_TEMPLATE,
    MUTATE_PROMPT_TEMPLATE,
    MUTATE_PROMPT_TEMPLATE_WITH_LABELS,
    MUTATION_TIPS,
    REASON_PROMPT,
    get_reason_schema,
)
from .ranking_systems import (
    TrueSkillFromCounts,
    aggregate_ranks,
    avg_winrate_ranking,
    borda_ranking,
    compare_json_task,
    copeland_ranking,
    elo_ranking,
)
from .thompson_sampling import sample_duel_pair

# Mutation via judge (old instruction_evolution mutation is deprecated here)

# Optional dependency handling
try:
    from tabulate import tabulate

    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


class QPDOEngine:
    """
    QPDO (Quick Prompt Duel Optimizer) engine.

    Implements dueling bandit optimization using Thompson sampling,
    multiple ranking systems, and instruction evolution.
    """

    def __init__(
        self,
        task_model: "ModelAdapter",
        judge_model: "ModelAdapter",
        metric: Optional[Callable] = None,
        # Algorithm parameters
        total_rounds: int = 100,
        num_duels_per_round: int = 3,
        num_eval_examples_per_duel: int = 50,
        num_initial_instructions: int = 2,
        use_labels: bool = False,
        thompson_alpha: float = 1.2,
        num_top_prompts_to_combine: int = 3,
        num_new_prompts_to_generate: int = 1,
        max_new_prompts_to_generate: int = 50,
        num_to_prune_each_round: int = 1,
        gen_new_prompt_round_frequency: int = 1,
        max_concurrent_threads: int = 8,
        # Generation config
        max_tokens: int = 4096,
        # Task configuration
        task_json_output_schema: Optional[Dict] = None,
        task_json_default_values: Optional[Dict] = None,
        answer_choices: Optional[List[str]] = None,
        ranking_method: str = "copeland",
    ):
        """
        Initialize QPDO optimization engine.

        Args:
            task_model: ModelAdapter for task execution
            judge_model: ModelAdapter for evaluation/judging
            metric: Optional metric function for evaluation
            total_rounds: Number of optimization rounds
            num_duels_per_round: Number of duels per round
            num_eval_examples_per_duel: Examples per duel
            num_initial_instructions: Initial instruction pool size
            use_labels: Whether to use supervised learning
            thompson_alpha: Thompson sampling alpha parameter
            num_top_prompts_to_combine: Top prompts for combination
            num_new_prompts_to_generate: New prompts per round
            max_new_prompts_to_generate: Maximum total new prompts
            num_to_prune_each_round: Prompts to prune per round
            gen_new_prompt_round_frequency: Frequency of prompt generation
            max_concurrent_threads: Max threads for parallel execution
            task_json_output_schema: JSON schema for task outputs
            task_json_default_values: Default values for task outputs
        """
        self.task_model = task_model
        self.judge_model = judge_model
        self.metric = metric

        # Algorithm configuration
        self.total_rounds = total_rounds
        self.num_duels_per_round = num_duels_per_round
        self.num_eval_examples_per_duel = num_eval_examples_per_duel
        self.num_initial_instructions = num_initial_instructions
        self.use_labels = use_labels
        self.alpha = thompson_alpha
        self.num_combine_top = num_top_prompts_to_combine
        self.num_generate_new = num_new_prompts_to_generate
        # No upper limit enforced; kept param for backward compatibility but unused
        self.num_prune = num_to_prune_each_round
        self.frequency = gen_new_prompt_round_frequency
        self.max_threads = max_concurrent_threads
        self.max_tokens = max_tokens
        # Alias for new mutation config name (n_top)
        self.n_top = num_top_prompts_to_combine

        # Task configuration
        self.task_json_output_schema = task_json_output_schema
        self.task_json_default_values = task_json_default_values or {}
        self.answer_choices = answer_choices or ["Yes", "No"]
        self.ranking_method = ranking_method

        # State variables
        self.instruction_pool: List[str] = []
        self.allowed_prompt_indices: List[int] = []
        self.win_matrix: Optional[np.ndarray] = None
        self.prompt_misclassified_examples: Dict[int, List] = defaultdict(list)
        self.prompt_performance_metrics: Dict[int, List] = defaultdict(list)

        # Initialize TrueSkill if available
        try:
            self.trueskill = TrueSkillFromCounts(
                mu0=25.0,
                sigma0=25.0 / 3,
                solver="exact",
                damping=0.9,
                epochs=50,
                track_history=False,
            )
        except ImportError:
            self.trueskill = None
            logging.warning("TrueSkill not available, will use other ranking methods")

    def initialize_instruction_pool(
        self,
        base_instruction: str,
        examples: List[str],
        labels: Optional[List[str]] = None,
    ) -> None:
        """Initialize the instruction pool with base and generated instructions."""
        print(f"Generating {self.num_initial_instructions} initial instructions...")

        # Debug: ignoring base_instruction by design
        print(
            f"Debug: (ignoring base_instruction) examples type: {type(examples)}, length: {len(examples) if isinstance(examples, list) else 'N/A'}"
        )
        print(f"Debug: labels type: {type(labels)}")
        print(f"Debug: judge_model type: {type(self.judge_model)}")

        self.instruction_pool = self._generate_initial_instructions(
            examples=examples,
            labels=labels,
            total_instructions=self.num_initial_instructions,
            n_sample_examples=3,
        )

        self.allowed_prompt_indices = list(range(len(self.instruction_pool)))

        # Initialize matrices
        pool_size = len(self.instruction_pool)
        self.win_matrix = np.zeros((pool_size, pool_size), dtype=int)
        # Removed example agreement tracking for conciseness

        print(f"✓ Initialized with {len(self.instruction_pool)} instructions")

    def _generate_initial_instructions(
        self,
        examples: List[str],
        labels: Optional[List[str]],
        total_instructions: int,
        n_sample_examples: int = 3,
    ) -> List[str]:
        """Generate initial instructions using diverse prompt engineering tips (ignore system prompt)."""
        print(f"Generating {total_instructions} new instructions...")

        # Build dataset summary (unlabeled snapshot)
        sampled_indices = random.sample(
            range(len(examples)), min(n_sample_examples, len(examples))
        )
        sample_examples = [examples[i] for i in sampled_indices]
        examples_text_for_summary = "\n\n".join([f"- {ex}" for ex in sample_examples])
        summary_prompt = DATASET_DESCRIPTOR_PROMPT.format(
            examples=examples_text_for_summary
        )
        # Use higher temperature for initial prompt generation to encourage diversity
        dataset_summary = self.judge_model.generate(
            summary_prompt, temperature=0.7, max_tokens=self.max_tokens
        )

        tip_categories = list(INITIAL_INSTRUCTION_TIPS.keys())
        distributed_tips = [
            tip_categories[i % len(tip_categories)] for i in range(total_instructions)
        ]

        # Build batch prompts
        batch_prompts: List[str] = []
        for tip_category in distributed_tips:
            tip = INITIAL_INSTRUCTION_TIPS[tip_category]

            # Sample questions and get corresponding indices
            sample_indices = random.sample(
                range(len(examples)), min(n_sample_examples, len(examples))
            )

            # Always use only inputs (ignore labels per user request)
            questions_text = "\n".join([f"- {examples[i]}" for i in sample_indices])

            instruction_prompt = INSTRUCTION_PROPOSER_TEMPLATE.format(
                dataset_summary=dataset_summary,
                questions=questions_text,
                tip=tip,
            )

            batch_prompts.append(instruction_prompt)

        # Generate in batch using the judge model
        batch_results = self.judge_model.generate_batch(
            batch_prompts,
            max_threads=self.max_threads,
            temperature=0.7,
            max_tokens=self.max_tokens,
        )

        # Extract single instruction from each result (expects a JSON array with one string)
        instructions: List[str] = []
        for i, result_text in enumerate(batch_results):
            try:
                start = result_text.find("[")
                end = result_text.rfind("]") + 1
                json_str = (
                    result_text[start:end]
                    if start >= 0 and end > start
                    else result_text
                )
                arr = json.loads(json_str)
                if isinstance(arr, list) and arr:
                    instruction = arr[0]
                else:
                    instruction = result_text.strip()
            except Exception:
                instruction = result_text.strip()

            instructions.append(instruction)
            # print(f"Generated instruction {i+1}/{total_instructions} with tip '{distributed_tips[i]}'")

        return instructions

    def run_duel_round(
        self,
        examples: List[str],
        labels: Optional[List[str]] = None,
        current_step: int = 1,
    ) -> Tuple[List[Tuple[int, int]], List[List[int]], List[Dict]]:
        """Run a single round of duels."""
        tau = 0.2
        dirichlet_weights = True
        num_instructions = len(self.instruction_pool)

        # Compute rank/rating signals for this round
        signals = self.compute_rank_signals()
        elo_mu = signals["elo_mu"]
        ts_mu = signals["ts_mu"]
        ts_cons = signals["ts_cons"]

        duel_pairs = []
        rng = np.random.default_rng()

        # Sample duel pairs using Thompson sampling
        for _ in range(self.num_duels_per_round):
            i, j = sample_duel_pair(
                K=num_instructions,
                W=self.win_matrix,
                alpha=self.alpha,
                t=current_step,
                allowed_indices=self.allowed_prompt_indices,
                elo_mu=elo_mu,
                ts_mu=ts_mu,
                ts_cons=ts_cons,
                tau=tau,
                dirichlet_weights=dirichlet_weights,
                rng=rng,
            )
            duel_pairs.append((i, j))

        # Prepare prompts for evaluation
        formatted_prompts = []
        example_batches = []
        seen_answer_choices = set(["A", "B"])  # Global superset for schema

        for i, j in duel_pairs:
            selected_examples_indices = random.sample(
                range(len(examples)),
                min(self.num_eval_examples_per_duel, len(examples)),
            )
            example_batches.append(selected_examples_indices)

            # Create prompts for both instructions
            for ex_idx in selected_examples_indices:
                # Build structured task prompts for both instructions using REASON_PROMPT
                # Use configured answer choices (default Yes/No), optionally overridden per-label choices
                answer_choices = list(self.answer_choices)
                if labels is not None and ex_idx < len(labels):
                    try:
                        if isinstance(labels[ex_idx], str):
                            label_obj = json.loads(labels[ex_idx])
                        else:
                            label_obj = labels[ex_idx]
                        if (
                            isinstance(label_obj, dict)
                            and "choices" in label_obj
                            and isinstance(label_obj["choices"], list)
                        ):
                            answer_choices = [str(c) for c in label_obj["choices"]]
                    except Exception:
                        pass

                # Track choices and build string
                for choice in answer_choices:
                    seen_answer_choices.add(choice)
                answer_choices_str = ", ".join(answer_choices)

                formatted_prompts.append(
                    REASON_PROMPT.format(
                        instruction=self.instruction_pool[i],
                        question=examples[ex_idx],
                        answer_choices_str=answer_choices_str,
                    )
                )
                formatted_prompts.append(
                    REASON_PROMPT.format(
                        instruction=self.instruction_pool[j],
                        question=examples[ex_idx],
                        answer_choices_str=answer_choices_str,
                    )
                )

        # Execute prompts (single batch, threaded by max_concurrent_threads)
        print(f"Executing {len(formatted_prompts)} prompts...")
        # Use configured base answer choices for schema (no unioning)
        base_choices = list(self.answer_choices)
        try:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "qpdo_reasoned_answer",
                    "schema": get_reason_schema(base_choices),
                    "strict": True,
                },
            }
            prompt_outputs = self.task_model.generate_batch(
                formatted_prompts,
                max_threads=self.max_threads,
                temperature=0.0,
                response_format=response_format,
                max_tokens=self.max_tokens,
            )
        except Exception:
            prompt_outputs = self.task_model.generate_batch(
                formatted_prompts,
                max_threads=self.max_threads,
                temperature=0.0,
                max_tokens=self.max_tokens,
            )

        # Save performance metrics if labels are available
        if labels is not None:
            self._save_prompt_performance(
                duel_pairs, example_batches, prompt_outputs, examples, labels
            )

        return duel_pairs, example_batches, prompt_outputs

    def evaluate_duel_responses(
        self,
        duel_pairs: List[Tuple[int, int]],
        example_batches: List[List[int]],
        prompt_outputs: List[str],
        examples: List[str],
        labels: Optional[List[str]] = None,
    ) -> None:
        """Evaluate duel responses using LLM judge."""
        evaluation_prompts = []
        duel_meta = []  # (i, j, swapped_bool) where swapped means X:=j, Y:=i
        response_cursor = 0

        for pair_idx, (i, j) in enumerate(duel_pairs):
            for ex_idx in example_batches[pair_idx]:
                response_i_raw = prompt_outputs[response_cursor]
                response_j_raw = prompt_outputs[response_cursor + 1]
                response_cursor += 2

                # Randomly swap X/Y assignment with p=0.5
                swapped = random.random() < 0.5
                if not swapped:
                    ra_raw, rb_raw = response_i_raw, response_j_raw
                else:
                    ra_raw, rb_raw = response_j_raw, response_i_raw

                # Parse structured task outputs (fallback to base choice if missing)
                ra = self._parse_json_response(ra_raw, {})
                rb = self._parse_json_response(rb_raw, {})

                question_text = examples[ex_idx]
                reasoning_X = ra.get("reasoning", "")
                answer_X = ra.get("answer", "") or (
                    self.answer_choices[0] if self.answer_choices else ""
                )
                reasoning_Y = rb.get("reasoning", "")
                answer_Y = rb.get("answer", "") or (
                    self.answer_choices[0] if self.answer_choices else ""
                )

                evaluation_prompts.append(
                    EVALUATE_PROMPT.format(
                        question=question_text,
                        reasoning_X=reasoning_X,
                        answer_X=answer_X,
                        reasoning_Y=reasoning_Y,
                        answer_Y=answer_Y,
                    )
                )
                duel_meta.append((i, j, swapped))

                # Example agreement tracking removed for conciseness

        # Get judge evaluations in parallel
        print(f"Getting judge evaluations for {len(evaluation_prompts)} comparisons...")
        try:
            judge_rf = {
                "type": "json_schema",
                "json_schema": {
                    "name": "qpdo_evaluate_verdict",
                    "schema": EVALUATE_SCHEMA,
                    "strict": True,
                },
            }
            judge_outputs = self.judge_model.generate_batch(
                evaluation_prompts,
                max_threads=self.max_threads,
                temperature=0.0,
                response_format=judge_rf,
                max_tokens=self.max_tokens,
            )
        except Exception:
            judge_outputs = self.judge_model.generate_batch(
                evaluation_prompts,
                max_threads=self.max_threads,
                temperature=0.0,
                max_tokens=self.max_tokens,
            )

        # Process judge results and update win matrix (map back using swapped flag)
        for (i, j, swapped), result_text in zip(duel_meta, judge_outputs):
            result = self._parse_json_response(result_text, {"winner": "X"})
            winner = result.get("winner", "X")
            if not swapped:
                # X := i, Y := j
                if winner == "X":
                    self.win_matrix[i][j] += 1
                elif winner == "Y":
                    self.win_matrix[j][i] += 1
            else:
                # X := j, Y := i
                if winner == "X":
                    self.win_matrix[j][i] += 1
                elif winner == "Y":
                    self.win_matrix[i][j] += 1

    def compute_rank_signals(self) -> Dict[str, np.ndarray]:
        """Compute ranking signals for Thompson sampling."""
        _, elo_mu = elo_ranking(self.win_matrix)

        if self.trueskill:
            try:
                ratings = self.trueskill.fit(self.win_matrix)
                ts_mu = ratings.mu
                ts_cons = ratings.conservative
            except:
                # Fallback if TrueSkill fails
                K = self.win_matrix.shape[0]
                ts_mu = np.zeros(K)
                ts_cons = np.zeros(K)
        else:
            K = self.win_matrix.shape[0]
            ts_mu = np.zeros(K)
            ts_cons = np.zeros(K)

        # Handle None case for elo_mu
        if elo_mu is None or np.isscalar(elo_mu):
            elo_mu = np.zeros(self.win_matrix.shape[0], dtype=float)

        return {
            "elo_mu": elo_mu,
            "ts_mu": ts_mu,
            "ts_cons": ts_cons,
        }

    def update_prompt_pool(
        self, examples: List[str], labels: Optional[List[str]] = None
    ) -> List[str]:
        """Prune worst prompts, then expand with mutations from top prompts."""
        # Cache examples/labels for mutation prompts if needed
        self._examples_cache = examples
        self._labels_cache = labels
        # 1) Prune worst first
        losers = self._get_worst_indices(self.num_prune)
        if losers:
            # Build keep index list (sorted) and reindex instruction pool
            keep = [
                i for i in range(len(self.instruction_pool)) if i not in set(losers)
            ]
            self.instruction_pool = [self.instruction_pool[i] for i in keep]

            # Shrink win_matrix to active set (delete loser rows/cols)
            if self.win_matrix is not None:
                self.win_matrix = np.delete(self.win_matrix, losers, axis=0)
                self.win_matrix = np.delete(self.win_matrix, losers, axis=1)

            # Reset active prompt indices to contiguous range
            self.allowed_prompt_indices = list(range(len(self.instruction_pool)))

            # Reset per-prompt metrics tracking (indices changed)
            self.prompt_misclassified_examples = defaultdict(list)
            self.prompt_performance_metrics = defaultdict(list)

        # 2) Then expand with mutants
        if not self.instruction_pool:
            return []

        max_top = min(self.n_top, len(self.instruction_pool))
        leader_indices = self._get_leader_indices(max_top)
        mutations_per_prompt = self._distribute_mutations(
            self.num_generate_new, max_top
        )

        new_instructions: List[str] = []
        for i, base_idx in enumerate(leader_indices):
            n_mut = mutations_per_prompt[i]
            if n_mut > 0:
                mutants = self._mutate_best(base_idx, n_mut, self.instruction_pool)
                new_instructions.extend(mutants)

        # Add new instructions to pool
        for instruction in new_instructions:
            self.instruction_pool.append(instruction)
            self.allowed_prompt_indices.append(len(self.instruction_pool) - 1)

            # Expand matrices
            self.win_matrix = np.pad(
                self.win_matrix, ((0, 1), (0, 1)), constant_values=0
            )
            # No example agreement padding needed

        return [self.instruction_pool[i] for i in leader_indices]

    def _get_rank_order(self) -> np.ndarray:
        method = (getattr(self, "ranking_method", "copeland") or "copeland").lower()
        if method == "copeland":
            order, _ = copeland_ranking(self.win_matrix)
            return order
        if method == "borda":
            order, _ = borda_ranking(self.win_matrix)
            return order
        if method == "avg_winrate":
            order, _ = avg_winrate_ranking(self.win_matrix)
            return order
        if method == "elo":
            order, _ = elo_ranking(self.win_matrix)
            return order
        if method == "aggregate":
            rankers = [
                copeland_ranking,
                borda_ranking,
                avg_winrate_ranking,
                elo_ranking,
            ]
            rankings = [ranker(self.win_matrix)[0] for ranker in rankers]
            scores = aggregate_ranks(rankings)
            # Higher is better in aggregate_ranks; return best-first order
            return np.argsort(-scores)
        order, _ = copeland_ranking(self.win_matrix)
        return order

    def _get_leader_indices(self, n_top: int) -> List[int]:
        if n_top <= 0:
            return []
        rank_order = self._get_rank_order()  # best-first
        return list(rank_order[: min(n_top, len(rank_order))])

    def _get_worst_indices(self, n_worst: int) -> List[int]:
        if n_worst <= 0 or self.win_matrix is None or len(self.win_matrix) <= 1:
            return []
        rank_order = self._get_rank_order()  # best-first
        return (
            list(rank_order[-n_worst:])
            if n_worst < len(rank_order)
            else list(rank_order)
        )

    def _distribute_mutations(self, total: int, k: int) -> List[int]:
        if k <= 0 or total <= 0:
            return [0] * max(k, 0)
        base = total // k
        rem = total % k
        return [base + (1 if i < rem else 0) for i in range(k)]

    def _mutate_best(
        self,
        best_idx: int,
        n_new: int,
        instructions_list: List[str],
    ) -> List[str]:
        """Return ≤ n_new brand-new prompts using batch processing."""
        mutation_prompts: List[str] = []
        tip_keys = list(MUTATION_TIPS.keys())

        for i in range(n_new):
            tip_category = tip_keys[i % len(tip_keys)]
            tip = MUTATION_TIPS[tip_category]

            if self.use_labels and getattr(self, "_labels_cache", None):
                examples = getattr(self, "_examples_cache", []) or []
                labels = getattr(self, "_labels_cache", []) or []
                n_sample_pairs = 3
                sample_indices = random.sample(
                    range(len(examples)), min(n_sample_pairs, len(examples))
                )
                sample_pairs_text = "\n".join(
                    [
                        f"- Input: {examples[idx]}\n  Output: {labels[idx]}"
                        for idx in sample_indices
                    ]
                )
                mutate_prompt = MUTATE_PROMPT_TEMPLATE_WITH_LABELS.format(
                    instructions=instructions_list[best_idx],
                    sample_pairs=sample_pairs_text,
                    tip=tip,
                )
            else:
                mutate_prompt = MUTATE_PROMPT_TEMPLATE.format(
                    instructions=instructions_list[best_idx],
                    tip=tip,
                )

            mutation_prompts.append(mutate_prompt)

        # Run batch mutation via judge model, expect {"mutated_prompt": ...}
        try:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "qpdo_mutate_instruction",
                    "schema": {
                        "type": "object",
                        "properties": {"mutated_prompt": {"type": "string"}},
                        "required": ["mutated_prompt"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            }
            results = self.judge_model.generate_batch(
                mutation_prompts,
                max_threads=self.max_threads,
                temperature=0.7,
                response_format=response_format,
                max_tokens=self.max_tokens,
            )
        except Exception:
            results = self.judge_model.generate_batch(
                mutation_prompts,
                max_threads=self.max_threads,
                max_tokens=self.max_tokens,
            )

        mutants: List[str] = []
        for result_text in results:
            parsed = self._parse_json_response(result_text, {})
            if isinstance(parsed, dict) and parsed.get("mutated_prompt"):
                mutants.append(str(parsed["mutated_prompt"]).strip())
            else:
                mutants.append(str(result_text).strip())

        return mutants

    def display_leaderboard(self, round_number: int) -> None:
        """Display current leaderboard of instructions."""
        if not HAS_TABULATE:
            print(
                f"Round {round_number} leaderboard (tabulate not available for formatting)"
            )
            return

        copeland_rank, _ = copeland_ranking(self.win_matrix)
        borda_rank, _ = borda_ranking(self.win_matrix)
        avg_winrate_rank, _ = avg_winrate_ranking(self.win_matrix)
        elo_rank, _ = elo_ranking(self.win_matrix)

        if self.trueskill:
            try:
                ratings = self.trueskill.fit(self.win_matrix)
                ts_rank_order = ratings.rank_order
                ts_rank_pos = {idx: pos + 1 for pos, idx in enumerate(ts_rank_order)}
                final_ranking = ts_rank_order
            except:
                final_ranking = copeland_rank
                ts_rank_pos = {idx: pos + 1 for pos, idx in enumerate(copeland_rank)}
        else:
            final_ranking = copeland_rank
            ts_rank_pos = {idx: pos + 1 for pos, idx in enumerate(copeland_rank)}

        # Calculate average F1 scores
        avg_f1_scores = {}
        for idx, entries in self.prompt_performance_metrics.items():
            groups = defaultdict(list)
            for e in entries:
                groups[e.get("example_idx")].append(e["f1"])
            avg_f1_scores[idx] = (
                np.mean([np.mean(v) for v in groups.values()]) if groups else 0.0
            )

        unique_eval_counts = {
            idx: len({m.get("example_idx") for m in entries})
            for idx, entries in self.prompt_performance_metrics.items()
        }

        headers = [
            "Prompt",
            "Evals",
            "Matches",
            "Wins↑",
            "Losses↓",
            "Copeland↓",
            "Borda↓",
            "WinRate↓",
            "Elo↓",
            "TrueSkill↓",
            "F1(%)↑",
        ]

        table = []
        for _, idx in enumerate(final_ranking, 1):
            wins = self.win_matrix[idx].sum()
            losses = self.win_matrix[:, idx].sum()
            avg_f1 = round(avg_f1_scores.get(idx, 0.0) * 100.0, 1)
            matches = int(wins + losses)
            eval_counts = unique_eval_counts.get(idx, 0)

            table.append(
                [
                    idx,
                    eval_counts,
                    matches,
                    wins,
                    losses,
                    list(copeland_rank).index(idx) + 1,
                    list(borda_rank).index(idx) + 1,
                    list(avg_winrate_rank).index(idx) + 1,
                    list(elo_rank).index(idx) + 1,
                    ts_rank_pos[idx],
                    avg_f1,
                ]
            )

        print(f"\nLeaderboard after Round {round_number}:\n")
        print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

    def optimize(
        self,
        base_instruction: str,
        examples: List[str],
        labels: Optional[List[str]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Run the full QPDO optimization process.

        Args:
            base_instruction: Initial instruction to start from
            examples: List of example inputs
            labels: Optional list of labels/answers

        Returns:
            Tuple of (best_instruction, optimization_metadata)
        """
        # Initialize instruction pool
        self.initialize_instruction_pool(base_instruction, examples, labels)

        print(f"\nStarting QPDO optimization:")
        print(f"- Total rounds: {self.total_rounds}")
        print(f"- Duels per round: {self.num_duels_per_round}")
        print(f"- Examples per duel: {self.num_eval_examples_per_duel}")
        print(f"- Initial instructions: {len(self.instruction_pool)}")

        current_step = 1

        for round_number in range(1, self.total_rounds + 1):
            print(f"\n=== Round {round_number}/{self.total_rounds} ===")
            # print(f"Active prompts: {self.allowed_prompt_indices}")

            # Run duels
            duel_pairs, example_batches, prompt_outputs = self.run_duel_round(
                examples, labels, current_step
            )
            current_step += self.num_duels_per_round

            # Evaluate duels
            print("Evaluating duel responses...")
            self.evaluate_duel_responses(
                duel_pairs, example_batches, prompt_outputs, examples, labels
            )

            # Leaderboard printing disabled by default; function kept for manual use

            # Update prompt pool
            if (round_number % self.frequency == 0) and (
                round_number < self.total_rounds
            ):
                print("Updating prompt pool: pruning and generating new prompts...")
                top_instructions = self.update_prompt_pool(examples, labels)

        # Get final results
        print("\n🎉 QPDO optimization complete!")

        # Find best instruction using user-selected ranking method
        final_order = self._get_rank_order()
        best_idx = int(final_order[0]) if len(final_order) > 0 else 0
        best_instruction = self.instruction_pool[best_idx]

        # Prepare metadata
        metadata = {
            "best_instruction_index": int(best_idx),
            "total_instructions_generated": len(self.instruction_pool),
            "total_duels_conducted": int(self.win_matrix.sum()),
            "final_win_matrix": self.win_matrix.tolist(),
            "instruction_pool": self.instruction_pool,
        }

        print(f"Best instruction:")
        print("=" * 80)
        print(best_instruction)
        print("=" * 80)

        return best_instruction, metadata

    # Helper methods

    def _generate_in_batches(
        self,
        model: "ModelAdapter",
        prompts: List[str],
        batch_size: int = 64,
        temperature: float = 0.0,
        response_format: Optional[Dict] = None,
        label: str = "",
    ) -> List[str]:
        """Generate in batches with simple progress logs (e.g., "Task 1/5")."""
        outputs: List[str] = []
        total = len(prompts)
        if total == 0:
            return outputs
        num_batches = (total + batch_size - 1) // batch_size
        for b in range(num_batches):
            start = b * batch_size
            end = min(start + batch_size, total)
            batch = prompts[start:end]
            print(f"{label} batch {b+1}/{num_batches} ({start+1}-{end}/{total})...")
            try:
                kwargs = {"temperature": temperature, "max_tokens": self.max_tokens}
                if response_format is not None:
                    kwargs["response_format"] = response_format
                part = model.generate_batch(
                    batch, max_threads=self.max_threads, **kwargs
                )
            except Exception:
                # Fallback without response_format if unsupported
                part = model.generate_batch(
                    batch,
                    max_threads=self.max_threads,
                    temperature=temperature,
                    max_tokens=self.max_tokens,
                )
            outputs.extend(part)
        return outputs

    def _create_task_prompt(self, instruction: str, input_text: str) -> str:
        """Create a task prompt from instruction and input."""
        return f"### Task\n{instruction}\n\n### Input\n{input_text}\n\n### Response\n"

    def _parse_json_response(self, response: str, default: Dict) -> Dict:
        """Parse JSON response with fallback."""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            return default

    def _save_prompt_performance(
        self,
        duel_pairs: List[Tuple[int, int]],
        example_batches: List[List[int]],
        prompt_outputs: List[str],
        examples: List[str],
        labels: List[str],
    ) -> None:
        """Save performance metrics for prompts."""
        response_cursor = 0
        for pair_idx, (i, j) in enumerate(duel_pairs):
            for ex_idx in example_batches[pair_idx]:
                response_i = prompt_outputs[response_cursor]
                response_j = prompt_outputs[response_cursor + 1]
                response_cursor += 2

                for idx, response in zip((i, j), (response_i, response_j)):
                    try:
                        response_clean = self._parse_json_response(response, {})
                        if isinstance(labels[ex_idx], str):
                            expected = json.loads(labels[ex_idx])
                        else:
                            expected = labels[ex_idx]

                        precision, recall, f1, diff_log = compare_json_task(
                            response_clean, expected
                        )

                        self.prompt_performance_metrics[idx].append(
                            {
                                "precision": precision,
                                "recall": recall,
                                "f1": f1,
                                "example_idx": ex_idx,
                            }
                        )

                        if min(precision, recall, f1) < 0.8:
                            self.prompt_misclassified_examples[idx].append(
                                (ex_idx, diff_log)
                            )
                    except Exception as e:
                        logging.warning(f"Failed to save performance metrics: {e}")

    def _mutate_supervised_prompts(
        self, top_indices: List[int], examples: List[str], labels: List[str]
    ) -> List[str]:
        """Generate new prompts using supervised mutation."""
        new_instructions = []

        for _ in range(self.num_generate_new):
            idx_prompt = random.choice(top_indices)
            task_instructions = self.instruction_pool[idx_prompt]

            items = self.prompt_misclassified_examples.get(idx_prompt, [])
            sampled = random.sample(items, min(3, len(items))) if items else []

            # Format misclassified examples
            misclassified_examples = []
            for ex_idx, diff_log_list in sampled:
                misclassified_examples.append(
                    {
                        "input": examples[ex_idx],
                        "expected": labels[ex_idx],
                        "diff_log": diff_log_list,
                    }
                )

            if misclassified_examples:
                # Use local mutate via MUTATE_PROMPT_TEMPLATE_WITH_LABELS using the champion as base
                mutants = self._mutate_best(
                    idx_prompt, 1, self.instruction_pool, examples, labels
                )
                if mutants:
                    new_instructions.append(mutants[0])

        return new_instructions
