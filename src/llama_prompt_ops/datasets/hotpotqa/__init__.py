"""
HotpotQA adapter for prompt-ops.

This module provides adapters and metrics for working with the HotpotQA dataset,
which requires multi-hop reasoning to answer complex questions.
"""

from .adapter import HotpotQAAdapter
from .metric import HotpotQAMetric

__all__ = ["HotpotQAAdapter", "HotpotQAMetric"]
