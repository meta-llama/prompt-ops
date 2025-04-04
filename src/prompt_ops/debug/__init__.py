"""
Debug utilities for prompt-ops.

This package contains debugging tools for the prompt-ops library.
"""

from .debug_proposer import patch_dspy_proposer, DebugGroundedProposer

__all__ = ["patch_dspy_proposer", "DebugGroundedProposer"]
