"""
Unit tests for prompt strategies.

This module tests the correct API usage of prompt optimization strategies,
particularly ensuring that dspy.MIPROv2 is called with correct parameters.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from llama_prompt_ops.core.prompt_strategies import (
    BasicOptimizationStrategy,
    OptimizationError,
)


class TestBasicOptimizationStrategy:
    """Test BasicOptimizationStrategy for correct dspy API usage."""

    def test_num_threads_parameter_passing(self):
        """
        Test that num_threads is correctly passed via eval_kwargs to optimizer.compile,
        not to dspy.MIPROv2 constructor.

        This test prevents regression of the bug where num_threads was incorrectly
        passed to MIPROv2 constructor, causing a TypeError.
        """
        # Arrange
        strategy = BasicOptimizationStrategy(num_threads=8)
        strategy.trainset = [MagicMock()]  # Mock dataset
        strategy.valset = [MagicMock()]
        strategy.metric = MagicMock()

        # Mock task and prompt models
        mock_task_model = MagicMock()
        mock_prompt_model = MagicMock()
        strategy.task_model = mock_task_model
        strategy.prompt_model = mock_prompt_model

        with (
            patch("dspy.MIPROv2") as mock_mipro,
            patch("dspy.ChainOfThought") as mock_cot,
        ):

            # Set up mock optimizer
            mock_optimizer_instance = MagicMock()
            mock_mipro.return_value = mock_optimizer_instance

            # Set up mock program
            mock_program = MagicMock()
            mock_cot.return_value = mock_program

            # Set up mock optimized program result
            mock_optimized_program = MagicMock()
            mock_optimizer_instance.compile.return_value = mock_optimized_program

            # Act
            prompt_data = {
                "text": "test prompt",
                "inputs": ["input"],
                "outputs": ["output"],
            }
            result = strategy.run(prompt_data)

            # Assert - Check that num_threads is NOT in the MIPROv2 constructor call
            mock_mipro.assert_called_once()
            constructor_kwargs = mock_mipro.call_args.kwargs
            assert (
                "num_threads" not in constructor_kwargs
            ), "num_threads should not be passed to dspy.MIPROv2 constructor"

            # Assert - Check that num_threads IS in the compile call via eval_kwargs
            mock_optimizer_instance.compile.assert_called_once()
            compile_kwargs = mock_optimizer_instance.compile.call_args.kwargs
            assert (
                "eval_kwargs" in compile_kwargs
            ), "eval_kwargs should be present in optimizer.compile call"
            assert compile_kwargs["eval_kwargs"] == {
                "num_threads": 8
            }, "eval_kwargs should contain the correct num_threads value"

            # Assert - Check that the result is the optimized program
            assert result == mock_optimized_program

    def test_mipro_v2_constructor_parameters(self):
        """
        Test that all expected parameters are passed to dspy.MIPROv2 constructor,
        excluding num_threads.
        """
        # Arrange
        strategy = BasicOptimizationStrategy(
            num_threads=4,
            max_bootstrapped_demos=3,
            max_labeled_demos=2,
            auto="basic",
            num_candidates=5,
            max_errors=2,
            seed=42,
            init_temperature=0.7,
            verbose=True,
            track_stats=False,
            metric_threshold=0.8,
        )
        strategy.trainset = [MagicMock()]
        strategy.valset = [MagicMock()]
        strategy.metric = MagicMock()
        strategy.task_model = MagicMock()
        strategy.prompt_model = MagicMock()

        with (
            patch("dspy.MIPROv2") as mock_mipro,
            patch("dspy.ChainOfThought") as mock_cot,
        ):

            mock_optimizer_instance = MagicMock()
            mock_mipro.return_value = mock_optimizer_instance
            mock_program = MagicMock()
            mock_cot.return_value = mock_program
            mock_optimizer_instance.compile.return_value = MagicMock()

            # Act
            prompt_data = {"text": "test", "inputs": [], "outputs": []}
            strategy.run(prompt_data)

            # Assert - Check expected parameters are present and correct
            mock_mipro.assert_called_once()
            kwargs = mock_mipro.call_args.kwargs

            # Check key parameters are present
            assert kwargs["max_bootstrapped_demos"] == 3
            assert kwargs["max_labeled_demos"] == 2
            assert kwargs["auto"] == "light"  # 'basic' maps to 'light'
            assert kwargs["num_candidates"] == 5
            assert kwargs["max_errors"] == 2
            assert kwargs["seed"] == 42
            assert kwargs["init_temperature"] == 0.7
            assert kwargs["verbose"] == True
            assert kwargs["track_stats"] == False
            assert kwargs["metric_threshold"] == 0.8

            # Ensure num_threads is NOT present
            assert "num_threads" not in kwargs

    def test_auto_mode_mapping(self):
        """
        Test that auto mode values are correctly mapped from our API to dspy's API.
        """
        test_cases = [
            ("basic", "light"),
            ("intermediate", "medium"),
            ("advanced", "heavy"),
        ]

        for our_value, expected_dspy_value in test_cases:
            with (
                patch("dspy.MIPROv2") as mock_mipro,
                patch("dspy.ChainOfThought") as mock_cot,
            ):

                # Arrange
                strategy = BasicOptimizationStrategy(auto=our_value)
                strategy.trainset = [MagicMock()]
                strategy.valset = [MagicMock()]
                strategy.metric = MagicMock()
                strategy.task_model = MagicMock()
                strategy.prompt_model = MagicMock()

                mock_optimizer_instance = MagicMock()
                mock_mipro.return_value = mock_optimizer_instance
                mock_program = MagicMock()
                mock_cot.return_value = mock_program
                mock_optimizer_instance.compile.return_value = MagicMock()

                # Act
                prompt_data = {"text": "test", "inputs": [], "outputs": []}
                strategy.run(prompt_data)

                # Assert
                kwargs = mock_mipro.call_args.kwargs
                assert (
                    kwargs["auto"] == expected_dspy_value
                ), f"auto='{our_value}' should map to '{expected_dspy_value}'"

    def test_compile_method_parameters(self):
        """
        Test that all expected parameters are passed to optimizer.compile method.
        """
        # Arrange
        strategy = BasicOptimizationStrategy(
            num_trials=3,
            minibatch=False,
            minibatch_size=10,
            program_aware_proposer=False,
            data_aware_proposer=False,
            requires_permission_to_run=True,
        )
        strategy.trainset = [MagicMock()]
        strategy.valset = [MagicMock()]
        strategy.metric = MagicMock()
        strategy.task_model = MagicMock()
        strategy.prompt_model = MagicMock()

        with (
            patch("dspy.MIPROv2") as mock_mipro,
            patch("dspy.ChainOfThought") as mock_cot,
        ):

            mock_optimizer_instance = MagicMock()
            mock_mipro.return_value = mock_optimizer_instance
            mock_program = MagicMock()
            mock_cot.return_value = mock_program
            mock_optimizer_instance.compile.return_value = MagicMock()

            # Act
            prompt_data = {"text": "test", "inputs": [], "outputs": []}
            strategy.run(prompt_data)

            # Assert
            mock_optimizer_instance.compile.assert_called_once()
            kwargs = mock_optimizer_instance.compile.call_args.kwargs

            # Check compile-specific parameters
            assert kwargs["num_trials"] == 3
            assert kwargs["minibatch"] == False
            assert kwargs["minibatch_size"] == 10
            assert kwargs["program_aware_proposer"] == False
            assert kwargs["data_aware_proposer"] == False
            assert kwargs["requires_permission_to_run"] == True
            assert kwargs["provide_traceback"] == True

    def test_exception_handling_with_meaningful_error(self):
        """
        Test that optimization errors are properly wrapped and provide meaningful messages.
        """
        # Arrange
        strategy = BasicOptimizationStrategy()
        strategy.trainset = [MagicMock()]
        strategy.valset = [MagicMock()]
        strategy.metric = MagicMock()
        strategy.task_model = MagicMock()
        strategy.prompt_model = MagicMock()

        with (
            patch("dspy.MIPROv2") as mock_mipro,
            patch("dspy.ChainOfThought") as mock_cot,
        ):

            # Configure the mock to raise an exception
            mock_mipro.side_effect = RuntimeError("Simulated dspy error")

            # Act & Assert
            prompt_data = {"text": "test", "inputs": [], "outputs": []}
            with pytest.raises(OptimizationError) as exc_info:
                strategy.run(prompt_data)

            # Check that the original error message is preserved
            assert "Simulated dspy error" in str(exc_info.value)
            assert "Optimization failed" in str(exc_info.value)

    def test_fallback_when_dspy_not_available(self):
        """
        Test that strategy gracefully falls back when dspy is not available.
        """
        # Arrange
        strategy = BasicOptimizationStrategy()
        # Simulate dspy not being available by not setting trainset
        strategy.trainset = None

        # Act
        prompt_data = {"text": "test prompt", "inputs": [], "outputs": []}
        result = strategy.run(prompt_data)

        # Assert
        assert isinstance(result, str)
        assert "test prompt" in result
        assert "Optimized for" in result

    def test_model_adapter_unwrapping(self):
        """
        Test that DSPyModelAdapter instances are properly unwrapped.
        """
        # Arrange
        strategy = BasicOptimizationStrategy()
        strategy.trainset = [MagicMock()]
        strategy.valset = [MagicMock()]
        strategy.metric = MagicMock()

        # Create mock adapters with _model attribute
        mock_task_adapter = MagicMock()
        mock_task_adapter._model = "unwrapped_task_model"
        mock_prompt_adapter = MagicMock()
        mock_prompt_adapter._model = "unwrapped_prompt_model"

        strategy.task_model = mock_task_adapter
        strategy.prompt_model = mock_prompt_adapter

        with (
            patch("dspy.MIPROv2") as mock_mipro,
            patch("dspy.ChainOfThought") as mock_cot,
        ):

            mock_optimizer_instance = MagicMock()
            mock_mipro.return_value = mock_optimizer_instance
            mock_program = MagicMock()
            mock_cot.return_value = mock_program
            mock_optimizer_instance.compile.return_value = MagicMock()

            # Act
            prompt_data = {"text": "test", "inputs": [], "outputs": []}
            strategy.run(prompt_data)

            # Assert - Check that unwrapped models are passed to MIPROv2
            kwargs = mock_mipro.call_args.kwargs
            assert kwargs["task_model"] == "unwrapped_task_model"
            assert kwargs["prompt_model"] == "unwrapped_prompt_model"
