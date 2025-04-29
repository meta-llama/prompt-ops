# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Utility functions for working with optimization strategies.
"""

from typing import Literal, Optional


def map_auto_mode_to_dspy(auto_mode: Optional[Literal["basic", "intermediate", "advanced"]]) -> str:
    """Map our naming convention to DSPy's expected values.
    
    Args:
        auto_mode: Our naming convention ('basic', 'intermediate', 'advanced')
        
    Returns:
        The corresponding DSPy auto mode ('light', 'medium', 'heavy')
    """
    mapping = {
        "basic": "light",
        "intermediate": "medium",
        "advanced": "heavy"
    }
    return mapping.get(auto_mode, "light")  # Default to light if not found
