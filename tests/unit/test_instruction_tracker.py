# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Unit tests for the InstructionProposalTracker.

This module tests the functionality of the InstructionProposalTracker class
to ensure it correctly tracks timing and progress during instruction proposal.
"""

import json
import time
import unittest
from unittest.mock import Mock, patch

from llama_prompt_ops.core.utils.telemetry import (
    CandidateInfo,
    InstructionProposalTracker,
)


class TestCandidateInfo(unittest.TestCase):
    """Test cases for the CandidateInfo dataclass."""

    def test_candidate_info_creation(self):
        """Test creating a CandidateInfo instance."""
        candidate = CandidateInfo(idx=1)
        self.assertEqual(candidate.idx, 1)
        self.assertIsNone(candidate.instructions)
        self.assertIsNone(candidate.start_ts)
        self.assertIsNone(candidate.end_ts)

    def test_candidate_info_duration_calculation(self):
        """Test duration calculation with timestamps."""
        candidate = CandidateInfo(idx=1, start_ts=1.0, end_ts=2.5)
        self.assertEqual(candidate.duration, 1.5)

    def test_candidate_info_duration_none_when_incomplete(self):
        """Test duration returns None when timestamps are incomplete."""
        candidate = CandidateInfo(idx=1, start_ts=1.0)
        self.assertIsNone(candidate.duration)

        candidate = CandidateInfo(idx=1, end_ts=2.0)
        self.assertIsNone(candidate.duration)


class TestInstructionProposalTracker(unittest.TestCase):
    """Test cases for the InstructionProposalTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the logger to avoid actual logging during tests
        self.mock_logger = Mock()
        with patch(
            "llama_prompt_ops.core.utils.telemetry.get_logger",
            return_value=self.mock_logger,
        ):
            self.tracker = InstructionProposalTracker(total=3, bar_length=10)

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        self.assertEqual(self.tracker.total, 3)
        self.assertEqual(self.tracker.bar_length, 10)
        self.assertEqual(len(self.tracker.candidates), 0)

    def test_start_candidate(self):
        """Test starting a candidate proposal."""
        with patch("time.time", return_value=100.0):
            self.tracker.start_candidate(1)

        self.assertEqual(len(self.tracker.candidates), 1)
        candidate = self.tracker.candidates[0]
        self.assertEqual(candidate.idx, 1)
        self.assertEqual(candidate.start_ts, 100.0)
        self.assertIsNone(candidate.end_ts)
        self.assertIsNone(candidate.instructions)

        # Check that progress was NOT displayed on start (to avoid duplicates)
        self.mock_logger.progress.assert_not_called()

    def test_end_candidate(self):
        """Test ending a candidate proposal."""
        # Start a candidate first
        with patch("time.time", return_value=100.0):
            self.tracker.start_candidate(1)

        # End the candidate
        with patch("time.time", return_value=101.5):
            self.tracker.end_candidate(1, "Test instruction")

        candidate = self.tracker.candidates[0]
        self.assertEqual(candidate.end_ts, 101.5)
        self.assertEqual(candidate.instructions, "Test instruction")
        self.assertEqual(candidate.duration, 1.5)

        # Check that progress was displayed once (only on end)
        self.assertEqual(self.mock_logger.progress.call_count, 1)

    def test_multiple_candidates(self):
        """Test tracking multiple candidates."""
        instructions = ["Instruction 1", "Instruction 2", "Instruction 3"]

        for i in range(1, 4):
            with patch("time.time", return_value=100.0 + i):
                self.tracker.start_candidate(i)

            # Small delay simulation
            with patch("time.time", return_value=100.0 + i + 0.5):
                self.tracker.end_candidate(i, instructions[i - 1])

        self.assertEqual(len(self.tracker.candidates), 3)

        for i, candidate in enumerate(self.tracker.candidates):
            self.assertEqual(candidate.idx, i + 1)
            self.assertEqual(candidate.instructions, instructions[i])
            self.assertEqual(candidate.duration, 0.5)

    def test_progress_display_format(self):
        """Test that progress display shows correct format."""
        # Complete one candidate
        with patch("time.time", return_value=100.0):
            self.tracker.start_candidate(1)
        with patch("time.time", return_value=101.0):
            self.tracker.end_candidate(1, "Test instruction")

        # Check the progress message format
        progress_calls = self.mock_logger.progress.call_args_list

        # Should have been called once (only on end)
        self.assertEqual(len(progress_calls), 1)

        # Check the progress message (after completion)
        final_call = progress_calls[-1]
        message = final_call[0][0]  # First argument of the call

        self.assertIn("⏳ Proposing instructions:", message)
        self.assertIn("1/3", message)
        self.assertIn("33.3%", message)
        self.assertIn("avg:", message)

    def test_get_summary(self):
        """Test getting a summary of tracked candidates."""
        # Track some candidates
        with patch("time.time", return_value=100.0):
            self.tracker.start_candidate(1)
        with patch("time.time", return_value=101.0):
            self.tracker.end_candidate(1, "Short instruction")

        with patch("time.time", return_value=102.0):
            self.tracker.start_candidate(2)
        with patch("time.time", return_value=103.5):
            self.tracker.end_candidate(
                2, "A much longer instruction that should be truncated in the preview"
            )

        summary = self.tracker.get_summary()

        self.assertEqual(summary["total_candidates"], 3)
        self.assertEqual(summary["completed_candidates"], 2)
        self.assertEqual(summary["total_time"], 2.5)  # 1.0 + 1.5
        self.assertEqual(summary["average_time_per_candidate"], 1.25)

        # Check candidate details
        candidates = summary["candidates"]
        self.assertEqual(len(candidates), 2)

        self.assertEqual(candidates[0]["idx"], 1)
        self.assertEqual(candidates[0]["duration"], 1.0)
        self.assertEqual(candidates[0]["instructions_length"], 17)
        self.assertEqual(candidates[0]["instructions_preview"], "Short instruction")

        self.assertEqual(candidates[1]["idx"], 2)
        self.assertEqual(candidates[1]["duration"], 1.5)
        # The string is 65 characters, which is less than 100, so it won't be truncated
        self.assertEqual(candidates[1]["instructions_length"], 65)
        # Since it's under 100 chars, it should be the full string without truncation
        self.assertEqual(
            candidates[1]["instructions_preview"],
            "A much longer instruction that should be truncated in the preview",
        )

    def test_to_json(self):
        """Test JSON serialization of tracker summary."""
        with patch("time.time", return_value=100.0):
            self.tracker.start_candidate(1)
        with patch("time.time", return_value=101.0):
            self.tracker.end_candidate(1, "Test instruction")

        json_str = self.tracker.to_json()

        # Should be valid JSON
        data = json.loads(json_str)

        self.assertEqual(data["total_candidates"], 3)
        self.assertEqual(data["completed_candidates"], 1)
        self.assertEqual(len(data["candidates"]), 1)

    def test_zero_total_candidates(self):
        """Test tracker behavior with zero total candidates."""
        with patch(
            "llama_prompt_ops.core.utils.telemetry.get_logger",
            return_value=self.mock_logger,
        ):
            tracker = InstructionProposalTracker(total=0)

        # Should not crash when displaying progress
        tracker._display_progress(0)

        # Logger should not be called for zero total
        self.mock_logger.progress.assert_not_called()

    def test_progress_bar_visualization(self):
        """Test that progress bar shows correct filled/unfilled characters."""
        # Test with a specific bar length for predictable output
        with patch(
            "llama_prompt_ops.core.utils.telemetry.get_logger",
            return_value=self.mock_logger,
        ):
            tracker = InstructionProposalTracker(total=4, bar_length=8)

        # Complete 2 out of 4 candidates (50%)
        tracker._display_progress(2)

        # Get the progress message
        call_args = self.mock_logger.progress.call_args
        message = call_args[0][0]

        # Should show 4 filled characters (50% of 8) and 4 unfilled
        self.assertIn("████░░░░", message)
        self.assertIn("2/4", message)
        self.assertIn("50.0%", message)


if __name__ == "__main__":
    unittest.main()
