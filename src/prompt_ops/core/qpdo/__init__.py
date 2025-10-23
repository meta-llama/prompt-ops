# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
QPDO (Quick Prompt Duel Optimizer) module.

This module provides a dueling bandit optimization approach for prompt optimization
using Thompson sampling, multiple ranking systems, and reflective prompt evolution.
"""

from .optimization_engine import QPDOEngine
from .ranking_systems import (
    TrueSkillFromCounts,
    avg_winrate_ranking,
    borda_ranking,
    copeland_ranking,
    elo_ranking,
)
from .thompson_sampling import sample_duel_pair

# Legacy imports removed; mutation now handled inside optimization engine.

__all__ = [
    "QPDOEngine",
    "sample_duel_pair",
    "copeland_ranking",
    "borda_ranking",
    "avg_winrate_ranking",
    "elo_ranking",
    "TrueSkillFromCounts",
]
