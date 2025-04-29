# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Evaluation module for prompt optimization.

This module provides evaluation capabilities for optimized prompts,
including statistical evaluation with confidence intervals.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Type
from dataclasses import dataclass

try:
    import dspy
    from dspy.evaluate import Evaluate as DSPyEvaluate
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    logging.warning("DSPy not installed. Evaluation features will not be available.")

try:
    import numpy as np
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not installed. Statistical evaluation features will not be available.")


@dataclass
class StatisticalResults:
    """Container for statistical evaluation results."""
    
    mean_score: float
    std_dev: float
    confidence_interval: Tuple[float, float]
    n_runs: int
    sample_size: int
    all_scores: List[float]
    p_value: Optional[float] = None


class Evaluator:
    """Base evaluator class that wraps DSPy's Evaluate functionality."""
    
    def __init__(
        self,
        metric: Optional[Callable] = None,
        devset: Optional[List[Any]] = None,
        num_threads: int = 4,
        display_progress: bool = True,
        display_table: bool = True
    ):
        """Initialize the evaluator.
        
        Args:
            metric: Function that computes a score for a prediction against a reference
            devset: List of examples to evaluate on
            num_threads: Number of threads to use for parallel evaluation
            display_progress: Whether to display a progress bar during evaluation
            display_table: Whether to display a summary table after evaluation
        """
        self.metric = metric
        self.devset = devset
        self.num_threads = num_threads
        self.display_progress = display_progress
        self.display_table = display_table
        
        if not DSPY_AVAILABLE:
            raise ImportError("DSPy is required for evaluation. Please install it with 'pip install dspy'.")
        
        self._dspy_evaluator = DSPyEvaluate(
            metric=metric,
            devset=devset,
            num_threads=num_threads,
            display_progress=display_progress,
            display_table=display_table
        )
    
    def evaluate(self, program, return_outputs=False):
        """Evaluate a program on the devset.
        
        Args:
            program: The program to evaluate (typically a DSPy program)
            return_outputs: Whether to return the outputs along with the score
            
        Returns:
            If return_outputs is False, returns the average score.
            If return_outputs is True, returns (score, outputs).
        """
        return self._dspy_evaluator(program, return_outputs=return_outputs)


class StatisticalEvaluator(Evaluator):
    """Evaluator that provides statistical significance testing capabilities."""
    
    def __init__(
        self,
        n_runs: int = 5,
        confidence_level: float = 0.95,
        **kwargs
    ):
        """Initialize the statistical evaluator.
        
        Args:
            n_runs: Number of evaluation runs to perform
            confidence_level: Confidence level for interval calculation (e.g., 0.95 for 95%)
            **kwargs: Additional arguments passed to the base Evaluator
        """
        super().__init__(**kwargs)
        
        if not SCIPY_AVAILABLE:
            raise ImportError("SciPy is required for statistical evaluation. Please install it with 'pip install scipy'.")
        
        self.n_runs = n_runs
        self.confidence_level = confidence_level
    
    def calculate_statistics(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate statistical measures including confidence intervals."""
        if not scores:
            raise ValueError("No scores available to calculate statistics")

        mean = np.mean(scores)
        std = np.std(scores, ddof=1)
        n = len(scores)
        sem = stats.sem(scores)
        
        ci = stats.t.interval(
            confidence=self.confidence_level,
            df=n - 1,
            loc=mean,
            scale=sem,
        )

        return {
            "mean": mean,
            "std": std,
            "confidence_interval": ci,
            "standard_error": sem,
        }
    
    def evaluate_with_statistics(self, program, **kwargs) -> StatisticalResults:
        """Run multiple evaluations to get statistically significant results."""
        all_scores = []
        
        for _ in range(self.n_runs):
            score = self._dspy_evaluator(program, **kwargs)
            all_scores.append(score)
        
        stats_dict = self.calculate_statistics(all_scores)
        
        return StatisticalResults(
            mean_score=stats_dict["mean"],
            std_dev=stats_dict["std"],
            confidence_interval=stats_dict["confidence_interval"],
            n_runs=self.n_runs,
            sample_size=len(self.devset),
            all_scores=all_scores,
        )

def create_evaluator(
    metric: Optional[Callable] = None,
    devset: Optional[List[Any]] = None,
    statistical: bool = False,
    **kwargs
) -> Union[Evaluator, StatisticalEvaluator]:
    """Factory function to create an appropriate evaluator.
    
    Args:
        metric: Function that computes a score for a prediction against a reference
        devset: List of examples to evaluate on
        statistical: Whether to use statistical evaluation
        **kwargs: Additional arguments for the evaluator
        
    Returns:
        An Evaluator or StatisticalEvaluator instance
    """
    if statistical:
        return StatisticalEvaluator(metric=metric, devset=devset, **kwargs)
    return Evaluator(metric=metric, devset=devset, **kwargs)
