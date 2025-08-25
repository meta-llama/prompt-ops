# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import time
import unittest
from unittest.mock import MagicMock, Mock, patch

from llama_prompt_ops.core.utils.realtime_tracker import (
    RealtimeProposalInterceptor,
    create_realtime_lm_wrapper,
    enable_realtime_tracking,
)
from llama_prompt_ops.core.utils.telemetry import InstructionProposalTracker


class TestRealtimeLMWrapper(unittest.TestCase):
    """Test cases for RealtimeLMWrapper."""

    def setUp(self):
        """Set up test fixtures."""

        # Create a simple mock LM class instead of MagicMock
        class MockLM:
            def __init__(self):
                self.call_count = 0
                self.calls = []

            def __call__(self, *args, **kwargs):
                self.call_count += 1
                self.calls.append((args, kwargs))
                return ["Generated instruction"]

        self.mock_lm = MockLM()
        self.tracker = InstructionProposalTracker(total=5)
        self.wrapper = create_realtime_lm_wrapper(self.mock_lm, self.tracker)

    def test_wrapper_initialization(self):
        """Test wrapper is properly initialized."""
        self.assertEqual(self.wrapper._wrapped_lm, self.mock_lm)
        self.assertEqual(self.wrapper._tracker, self.tracker)
        self.assertTrue(self.wrapper._is_proposing)
        self.assertEqual(self.wrapper._proposal_count, 0)

    def test_attribute_forwarding(self):
        """Test that attributes are forwarded to wrapped LM."""

        # The new wrapper copies attributes from the wrapped LM during initialization
        # So we need to test that the wrapper has the same attributes as the mock LM
        # Create a new mock with an attribute
        class MockLMWithAttr:
            def __init__(self):
                self.some_attribute = "test_value"
                self.call_count = 0

            def __call__(self, *args, **kwargs):
                self.call_count += 1
                return ["Generated instruction"]

        mock_with_attr = MockLMWithAttr()
        new_wrapper = create_realtime_lm_wrapper(mock_with_attr, self.tracker)
        self.assertEqual(new_wrapper.some_attribute, "test_value")

    def test_call_without_tracking(self):
        """Test LM call when not in proposing mode."""
        self.wrapper.set_proposing_mode(False)
        result = self.wrapper("test prompt")

        self.assertEqual(self.mock_lm.call_count, 1)
        self.assertEqual(self.mock_lm.calls[0][0], ("test prompt",))
        self.assertEqual(result, ["Generated instruction"])
        # No tracking should occur
        self.assertEqual(len(self.tracker.candidates), 0)

    def test_call_with_tracking(self):
        """Test LM call with tracking enabled."""
        self.wrapper.set_proposing_mode(True)
        result = self.wrapper("Generate an instruction for this task")

        self.assertEqual(self.mock_lm.call_count, 1)
        self.assertEqual(result, ["Generated instruction"])
        # Tracking should occur
        self.assertEqual(len(self.tracker.candidates), 1)
        self.assertEqual(self.tracker.candidates[0].idx, 1)

    def test_multiple_calls_tracking(self):
        """Test multiple LM calls are tracked correctly."""
        self.wrapper.set_proposing_mode(True)

        for i in range(3):
            self.wrapper(f"Generate instruction {i}")

        self.assertEqual(self.mock_lm.call_count, 3)
        self.assertEqual(len(self.tracker.candidates), 3)

        # Check candidate indices
        for i, candidate in enumerate(self.tracker.candidates):
            self.assertEqual(candidate.idx, i + 1)

    def test_error_handling(self):
        """Test error handling during LM call."""

        # Create a mock that raises an error
        class ErrorMockLM:
            def __init__(self):
                self.call_count = 0

            def __call__(self, *args, **kwargs):
                raise Exception("LM Error")

        error_mock = ErrorMockLM()
        error_wrapper = create_realtime_lm_wrapper(error_mock, self.tracker)
        error_wrapper.set_proposing_mode(True)

        with self.assertRaises(Exception):
            error_wrapper("test prompt")

        # Error should still be tracked
        self.assertEqual(len(self.tracker.candidates), 1)
        self.assertIn(
            "Error generating instruction", self.tracker.candidates[0].instructions
        )

    def test_extract_instruction_string(self):
        """Test instruction extraction from string result."""
        result = "This is a test instruction"
        extracted = self.wrapper._extract_instruction(result)
        self.assertEqual(extracted, result)

    def test_extract_instruction_list(self):
        """Test instruction extraction from list result."""
        result = ["First instruction", "Second instruction"]
        extracted = self.wrapper._extract_instruction(result)
        self.assertEqual(extracted, "First instruction")

    def test_extract_instruction_object(self):
        """Test instruction extraction from object with text attribute."""
        result = Mock()
        result.text = "Instruction from object"
        extracted = self.wrapper._extract_instruction(result)
        self.assertEqual(extracted, "Instruction from object")

    def test_extract_instruction_truncation(self):
        """Test long instructions are truncated."""
        long_text = "x" * 300
        extracted = self.wrapper._extract_instruction(long_text)
        self.assertEqual(len(extracted), 203)  # 200 + "..."
        self.assertTrue(extracted.endswith("..."))


class TestRealtimeProposalInterceptor(unittest.TestCase):
    """Test cases for RealtimeProposalInterceptor."""

    def setUp(self):
        """Set up test fixtures."""
        self.interceptor = RealtimeProposalInterceptor(num_candidates=5)
        self.mock_optimizer = MagicMock()
        self.mock_optimizer.prompt_model = MagicMock()

    @patch("llama_prompt_ops.core.utils.realtime_tracker.InstructionProposalTracker")
    def test_patch_proposer(self, mock_tracker_class):
        """Test patching the proposer method."""
        # Mock the GroundedProposer class at the dspy module level
        with patch("dspy.propose.grounded_proposer.GroundedProposer") as mock_proposer:
            original_method = MagicMock()
            mock_proposer.propose_instructions_for_program = original_method

            # Patch the proposer
            returned_method = self.interceptor.patch_proposer(self.mock_optimizer)

            # Check that method was replaced
            self.assertNotEqual(
                mock_proposer.propose_instructions_for_program, original_method
            )
            self.assertEqual(returned_method, original_method)

    def test_unpatch_proposer(self):
        """Test unpatching the proposer method."""
        original_method = MagicMock()

        with patch("dspy.propose.grounded_proposer.GroundedProposer") as mock_proposer:
            self.interceptor.unpatch_proposer(original_method)
            self.assertEqual(
                mock_proposer.propose_instructions_for_program, original_method
            )


class TestEnableRealtimeTracking(unittest.TestCase):
    """Test cases for enable_realtime_tracking function."""

    def test_enable_realtime_tracking(self):
        """Test enabling real-time tracking on an optimizer."""
        mock_optimizer = MagicMock()

        with patch.object(RealtimeProposalInterceptor, "patch_proposer") as mock_patch:
            mock_patch.return_value = MagicMock()  # Original method

            interceptor = enable_realtime_tracking(mock_optimizer, num_candidates=10)

            # Check that interceptor was created and attached
            self.assertIsInstance(interceptor, RealtimeProposalInterceptor)
            self.assertEqual(interceptor.num_candidates, 10)
            self.assertTrue(hasattr(mock_optimizer, "_original_propose_method"))
            self.assertTrue(hasattr(mock_optimizer, "_proposal_interceptor"))
            mock_patch.assert_called_once_with(mock_optimizer)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios for real-time tracking."""

    def test_full_tracking_flow(self):
        """Test a complete tracking flow."""

        # Create mock LM with side effects
        class MockLMWithSideEffects:
            def __init__(self):
                self.call_count = 0
                self.responses = [
                    ["First instruction"],
                    ["Second instruction"],
                    ["Third instruction"],
                ]

            def __call__(self, *args, **kwargs):
                response = self.responses[self.call_count]
                self.call_count += 1
                return response

        mock_lm = MockLMWithSideEffects()

        # Create tracker
        tracker = InstructionProposalTracker(total=3)

        # Create wrapper
        wrapper = create_realtime_lm_wrapper(mock_lm, tracker)
        wrapper.set_proposing_mode(True)

        # Simulate instruction generation
        for i in range(3):
            wrapper(f"Generate instruction {i}")
            time.sleep(0.01)  # Simulate processing time

        # Verify tracking
        self.assertEqual(len(tracker.candidates), 3)
        summary = tracker.get_summary()
        self.assertEqual(summary["completed_candidates"], 3)
        self.assertEqual(summary["total_candidates"], 3)

        # Check that all candidates have durations
        for candidate in tracker.candidates:
            self.assertIsNotNone(candidate.duration)
            # Duration should be >= 0 (might be 0 for very fast operations)
            self.assertGreaterEqual(candidate.duration, 0)


if __name__ == "__main__":
    unittest.main()
