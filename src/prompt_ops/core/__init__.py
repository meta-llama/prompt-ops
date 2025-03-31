"""
Core module for prompt migration and optimization.

This module provides the main functionality for migrating and optimizing prompts.
"""

from .migrator import PromptMigrator
from .prompt_strategies import (
    BaseStrategy,
    BasicOptimizationStrategy
)
from .metrics import MetricBase, ExactMatchMetric, LLMAsJudgeMetric
from .evaluation import (
    Evaluator,
    StatisticalEvaluator,
    StatisticalResults,
    create_evaluator
)

__all__ = [
    'PromptMigrator',
    'BaseStrategy',
    'BasicOptimizationStrategy',
    'MetricBase',
    'ExactMatchMetric',
    'LLMAsJudgeMetric',
    'Evaluator',
    'StatisticalEvaluator',
    'StatisticalResults',
    'create_evaluator'
]