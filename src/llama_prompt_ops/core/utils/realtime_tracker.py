# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Real-time tracking for DSPy instruction proposals.

This module provides real-time progress tracking by intercepting LLM calls
during the instruction proposal phase.
"""

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from .logging import get_logger
from .telemetry import InstructionProposalTracker


def create_realtime_lm_wrapper(
    wrapped_lm, tracker: Optional[InstructionProposalTracker] = None
):
    """
    Create a wrapper for DSPy LM that provides real-time tracking of instruction proposals.

    This function dynamically creates a wrapper class that inherits from the wrapped LM's class,
    ensuring it passes DSPy's type checks while adding tracking functionality.

    Args:
        wrapped_lm: The original DSPy LM instance to wrap
        tracker: Optional instruction proposal tracker

    Returns:
        An instance of the wrapper that inherits from the wrapped LM's class
    """

    # Get the base class of the wrapped LM
    base_class = wrapped_lm.__class__

    # Create a dynamic wrapper class that inherits from the base class
    class RealtimeLMWrapper(base_class):
        """
        Wrapper for DSPy LM that provides real-time tracking of instruction proposals.

        This wrapper intercepts LLM calls and updates progress in real-time as each
        instruction is generated.
        """

        def __init__(self):
            """Initialize the wrapper by copying attributes from wrapped LM."""
            # Don't call super().__init__() to avoid re-initialization
            # Instead, copy all attributes from the wrapped LM
            for attr, value in wrapped_lm.__dict__.items():
                setattr(self, attr, value)

            # Add our tracking attributes
            self._wrapped_lm = wrapped_lm
            self._tracker = tracker
            self._logger = get_logger()
            self._proposal_count = 0
            self._lock = threading.Lock()
            self._is_proposing = True  # Always active during proposal phase
            self._proposal_pattern = (
                "propose.*instruction"  # Pattern to detect proposal calls
            )

        def __call__(self, *args, **kwargs):
            """
            Intercept LM calls and track instruction proposals in real-time.

            This method detects when the LM is being used for instruction proposals
            and updates the progress tracker accordingly.
            """
            # Check if this is an instruction proposal call
            is_proposal_call = self._detect_proposal_call(args, kwargs)

            if is_proposal_call and self._tracker:
                with self._lock:
                    self._proposal_count += 1
                    current_count = self._proposal_count

                # Start tracking this candidate
                self._tracker.start_candidate(current_count)

                # Log that we're starting a new proposal
                self._logger.progress(
                    f"Starting instruction proposal {current_count}", level="DEBUG"
                )

            # Call the wrapped LM directly
            start_time = time.time()
            try:
                result = self._wrapped_lm(*args, **kwargs)
                duration = time.time() - start_time

                if is_proposal_call and self._tracker:
                    # Extract instruction from result if possible
                    instruction_text = self._extract_instruction(result)

                    # End tracking for this candidate
                    self._tracker.end_candidate(current_count, instruction_text)

                    self._logger.progress(
                        f"Completed instruction proposal {current_count} in {duration:.2f}s",
                        level="DEBUG",
                    )

                return result

            except Exception as e:
                # Still update tracker on error
                if is_proposal_call and self._tracker:
                    self._tracker.end_candidate(
                        current_count, f"Error generating instruction: {str(e)}"
                    )
                raise

        def _detect_proposal_call(self, args: tuple, kwargs: dict) -> bool:
            """
            Detect if this LM call is for instruction proposal.

            Args:
                args: Positional arguments to the LM
                kwargs: Keyword arguments to the LM

            Returns:
                True if this appears to be an instruction proposal call
            """
            # During proposal mode, we track all LM calls
            # This ensures we don't miss any instruction generation
            if self._is_proposing:
                # Look for instruction-related prompts in the arguments
                prompt_text = ""
                if args:
                    prompt_text = str(args[0]) if args else ""
                elif "prompt" in kwargs:
                    prompt_text = str(kwargs.get("prompt", ""))
                elif "messages" in kwargs:
                    # Handle chat-style prompts
                    messages = kwargs.get("messages", [])
                    if messages:
                        prompt_text = " ".join(
                            str(m.get("content", ""))
                            for m in messages
                            if isinstance(m, dict)
                        )

                # Log for debugging
                if prompt_text:
                    self._logger.progress(
                        f"LM call during proposal phase: {prompt_text[:100]}...",
                        level="DEBUG",
                    )

                # During proposal phase, consider all non-empty prompts as potential proposals
                return bool(prompt_text.strip())

            return False

        def _extract_instruction(self, result: Any) -> str:
            """
            Extract instruction text from LM result.

            Args:
                result: The result from the LM call

            Returns:
                Extracted instruction text or a placeholder
            """
            if isinstance(result, str):
                return result[:200] + "..." if len(result) > 200 else result
            elif isinstance(result, list) and result:
                first_result = str(result[0])
                return (
                    first_result[:200] + "..."
                    if len(first_result) > 200
                    else first_result
                )
            elif hasattr(result, "text"):
                text = str(result.text)
                return text[:200] + "..." if len(text) > 200 else text
            else:
                return "Generated instruction"

        def set_proposing_mode(self, is_proposing: bool):
            """
            Set whether we're currently in instruction proposal mode.

            Args:
                is_proposing: True if we're proposing instructions
            """
            self._is_proposing = is_proposing
            if is_proposing:
                self._proposal_count = 0

    # Create and return an instance of the wrapper
    return RealtimeLMWrapper()


class RealtimeProposalInterceptor:
    """
    Intercepts DSPy's proposal process to provide real-time tracking.

    This class patches DSPy's GroundedProposer to wrap the LM with our
    real-time tracker during instruction proposal.
    """

    def __init__(self, num_candidates: int = 10):
        """
        Initialize the interceptor.

        Args:
            num_candidates: Expected number of instruction candidates
        """
        self.num_candidates = num_candidates
        self.logger = get_logger()
        self.tracker = None
        self.original_lm = None
        self.wrapped_lm = None
        self.original_call = None
        self.original_settings_lm = None

    def patch_proposer(self, optimizer):
        """
        Patch the DSPy proposer to use our real-time tracking.

        Args:
            optimizer: The DSPy optimizer instance (e.g., MIPROv2)
        """
        from dspy.propose.grounded_proposer import GroundedProposer

        # Store the original method
        original_propose = GroundedProposer.propose_instructions_for_program

        # Create our wrapper
        def wrapped_propose_instructions(proposer_self, *args, **kwargs):
            """Wrapped version that adds real-time tracking."""

            # Initialize tracker for this proposal session
            self.tracker = InstructionProposalTracker(total=self.num_candidates)

            # Get the prompt model from the proposer or optimizer
            prompt_model = getattr(proposer_self, "prompt_model", None)
            if not prompt_model and hasattr(optimizer, "prompt_model"):
                prompt_model = optimizer.prompt_model

            # Import dspy to access settings
            import dspy

            if prompt_model:
                # Store original LM
                self.original_lm = prompt_model

                # Create a wrapper that tracks calls
                wrapper = create_realtime_lm_wrapper(prompt_model, self.tracker)

                # Replace the LM in all possible places
                if hasattr(proposer_self, "prompt_model"):
                    proposer_self.prompt_model = wrapper
                if hasattr(optimizer, "prompt_model"):
                    optimizer.prompt_model = wrapper

                # Also update DSPy settings if the LM is there
                if hasattr(dspy, "settings") and hasattr(dspy.settings, "lm"):
                    if dspy.settings.lm == prompt_model:
                        self.original_settings_lm = dspy.settings.lm
                        dspy.settings.lm = wrapper

                # Store the wrapper for cleanup
                self.wrapped_lm = wrapper

                self.logger.progress("Enabled real-time instruction proposal tracking")

            try:
                # Call the original method
                result = original_propose(proposer_self, *args, **kwargs)
                return result

            finally:
                # Import dspy for cleanup
                import dspy

                # Restore original LMs
                if self.original_lm:
                    if hasattr(proposer_self, "prompt_model"):
                        proposer_self.prompt_model = self.original_lm
                    if hasattr(optimizer, "prompt_model"):
                        optimizer.prompt_model = self.original_lm

                # Restore DSPy settings if we changed it
                if hasattr(self, "original_settings_lm") and self.original_settings_lm:
                    if hasattr(dspy, "settings") and hasattr(dspy.settings, "lm"):
                        dspy.settings.lm = self.original_settings_lm

                # Log summary if we have a tracker
                if self.tracker:
                    summary = self.tracker.get_summary()
                    self.logger.progress(
                        f"Instruction proposal complete: "
                        f"{summary['completed_candidates']}/{summary['total_candidates']} "
                        f"in {summary['total_time']:.2f}s"
                    )

        # Apply the patch
        GroundedProposer.propose_instructions_for_program = wrapped_propose_instructions

        return original_propose

    def unpatch_proposer(self, original_method):
        """
        Restore the original proposer method.

        Args:
            original_method: The original propose_instructions_for_program method
        """
        from dspy.propose.grounded_proposer import GroundedProposer

        if original_method:
            GroundedProposer.propose_instructions_for_program = original_method


def enable_realtime_tracking(optimizer, num_candidates: int = 10):
    """
    Enable real-time tracking for a DSPy optimizer.

    Args:
        optimizer: The DSPy optimizer instance (e.g., MIPROv2)
        num_candidates: Expected number of instruction candidates

    Returns:
        The interceptor instance (for cleanup if needed)
    """
    interceptor = RealtimeProposalInterceptor(num_candidates)
    original_method = interceptor.patch_proposer(optimizer)

    # Store the original method on the optimizer for cleanup
    optimizer._original_propose_method = original_method
    optimizer._proposal_interceptor = interceptor

    return interceptor
