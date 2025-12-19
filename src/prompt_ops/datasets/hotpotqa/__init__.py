# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
HotpotQA adapter for prompt-ops.

This module provides adapters and metrics for working with the HotpotQA dataset,
which requires multi-hop reasoning to answer complex questions.
"""

from .adapter import HotpotQAAdapter
from .metric import HotpotQAMetric

__all__ = ["HotpotQAAdapter", "HotpotQAMetric"]
