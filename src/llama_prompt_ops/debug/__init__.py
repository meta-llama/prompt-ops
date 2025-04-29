# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Debug utilities for prompt-ops.

This package contains debugging tools for the prompt-ops library.
"""

from .debug_proposer import patch_dspy_proposer, DebugGroundedProposer

__all__ = ["patch_dspy_proposer", "DebugGroundedProposer"]
