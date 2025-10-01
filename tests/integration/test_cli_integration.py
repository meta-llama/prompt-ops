import os
import tempfile
from pathlib import Path

# import unittest.mock which should always be available
from unittest.mock import MagicMock, patch

import pytest
import yaml

# check if cli components are available
# there are legitimate scenarios where these might not be available:::
# 1. during development when only testing core functionality
# 2. in environments where only a subset of dependencies are installed
# 3. when running tests for specific components in isolation
CLI_COMPONENTS_AVAILABLE = False
try:
    from prompt_ops.core.migrator import PromptMigrator
    from prompt_ops.interfaces.cli import cli

    CLI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    # Record the specific import error for diagnostics
    CLI_IMPORT_ERROR = str(e)


@pytest.fixture
def facility_config_path():
    """fixture providing path to the facility config."""
    base_dir = Path(__file__).parent.parent.parent
    return str(
        base_dir / "use-cases" / "facility-support-analyzer" / "facility-simple.yaml"
    )


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config = {
        "dataset": {
            "path": "test_dataset.json",
            "input_field": ["fields", "input"],
            "golden_output_field": "answer",
        },
        "model": {
            "name": "test-model",
            "task_model": "test-model",
            "proposer_model": "test-model",
        },
        "metric": {
            "class": "prompt_ops.core.metrics.FacilityMetric",
            "strict_json": False,
            "output_field": "answer",
        },
        "optimization": {"strategy": "llama"},
    }

    # Using delete=True allows pytest to handle cleanup automatically, The file will be deleted when the context manager exits
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=True) as tmp:
        yaml.dump(config, tmp)
        tmp.flush()  # Ensure all data is written to disk
        yield tmp.name  # Yield inside the context manager


# Define a detailed reason for skipping that explains when and why tests are skipped
def get_skip_reason():
    if not CLI_COMPONENTS_AVAILABLE:
        return (
            f"CLI components not available: {CLI_IMPORT_ERROR if 'CLI_IMPORT_ERROR' in globals() else 'Unknown import error'}. "
            f"These tests verify CLI functionality which is considered optional and separate from core functionality."
        )
    return "CLI components available"


@pytest.fixture
def mock_api_key_check():
    """Mock the API key check function to always return a test API key."""
    with patch("prompt_ops.interfaces.cli.check_api_key", return_value="test_api_key"):
        yield


# Use a more explicit skipif with a function that provides detailed information
@pytest.mark.skipif(not CLI_COMPONENTS_AVAILABLE, reason=get_skip_reason())
class TestCLIIntegration:
    """Integration tests for the CLI interface."""

    @pytest.fixture(autouse=True)
    def setup_test_env(self):
        """Set up test environment for all tests in this class."""
        # Set the test environment variable to bypass API key check
        with patch.dict(os.environ, {"PROMPT_OPS_TEST_ENV": "1"}):
            yield

    def test_cli_migrate_command(self, mock_api_key_check, temp_config_file):
        """Test the migrate command with a config file."""
        # Use Click's test runner instead of directly calling cli()
        from click.testing import CliRunner

        runner = CliRunner()

        # Create mock objects for the migrator and its methods
        mock_migrator = MagicMock()
        mock_dataset_adapter = MagicMock()
        mock_optimized = MagicMock()
        mock_optimized.signature.instructions = "Optimized prompt"

        # Set up return values for the mocked methods
        mock_migrator.load_dataset_with_adapter.return_value = ([], [], [])
        mock_migrator.optimize.return_value = mock_optimized

        # Set up multiple patches
        with (
            patch(
                "prompt_ops.interfaces.cli.PromptMigrator",
                return_value=mock_migrator,
            ),
            patch(
                "prompt_ops.interfaces.cli.get_dataset_adapter_from_config",
                return_value=mock_dataset_adapter,
            ),
            patch(
                "prompt_ops.interfaces.cli.get_models_from_config",
                return_value=(None, None, "test_task_model", "test_prompt_model"),
            ),
            patch("prompt_ops.interfaces.cli.get_metric", return_value=MagicMock()),
            patch("prompt_ops.interfaces.cli.get_strategy", return_value=MagicMock()),
            patch("prompt_ops.interfaces.cli.load_config", return_value={}),
            patch(
                "prompt_ops.interfaces.cli.validate_min_records_in_dataset",
                return_value=None,
            ),
        ):

            # Run the migrate command
            result = runner.invoke(cli, ["migrate", "--config", temp_config_file])

            # Print the output for debugging
            if result.exit_code != 0:
                print(f"Command failed with exit code {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            # Check that the command ran successfully
            assert result.exit_code == 0

            # Check that the migrator methods were called
            mock_migrator.load_dataset_with_adapter.assert_called_once()
            mock_migrator.optimize.assert_called_once()

            # Verify the migrator was properly initialized
            from prompt_ops.interfaces.cli import PromptMigrator

            PromptMigrator.assert_called_once()
            # what was loaded from temp_config_file

    def test_cli_config_loading(self, mock_api_key_check, facility_config_path):
        """Test loading a real config file through the CLI."""
        # Use Click's test runner instead of directly calling cli()
        from click.testing import CliRunner

        runner = CliRunner()

        # Create mock objects for the migrator and its methods
        mock_migrator = MagicMock()
        mock_dataset_adapter = MagicMock()
        mock_optimized = MagicMock()
        mock_optimized.signature.instructions = "Optimized prompt"

        # Set up return values for the mocked methods
        mock_migrator.load_dataset_with_adapter.return_value = ([], [], [])
        mock_migrator.optimize.return_value = mock_optimized

        # Set up multiple patches
        with (
            patch(
                "prompt_ops.interfaces.cli.PromptMigrator",
                return_value=mock_migrator,
            ),
            patch(
                "prompt_ops.interfaces.cli.get_dataset_adapter_from_config",
                return_value=mock_dataset_adapter,
            ),
            patch(
                "prompt_ops.interfaces.cli.get_models_from_config",
                return_value=(None, None, "test_task_model", "test_prompt_model"),
            ),
            patch("prompt_ops.interfaces.cli.get_metric", return_value=MagicMock()),
            patch("prompt_ops.interfaces.cli.get_strategy", return_value=MagicMock()),
            patch("prompt_ops.interfaces.cli.load_config", return_value={}),
            patch(
                "prompt_ops.interfaces.cli.validate_min_records_in_dataset",
                return_value=None,
            ),
        ):

            # Run the migrate command with the real config
            result = runner.invoke(cli, ["migrate", "--config", facility_config_path])

            # Print the output for debugging
            if result.exit_code != 0:
                print(f"Command failed with exit code {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            # Check that the command ran successfully
            assert result.exit_code == 0

            # Check that the migrator methods were called
            mock_migrator.load_dataset_with_adapter.assert_called_once()
            mock_migrator.optimize.assert_called_once()

            # Verify the migrator was properly initialized
            from prompt_ops.interfaces.cli import PromptMigrator

            PromptMigrator.assert_called_once()

            # Verify the config was loaded with the facility_config_path
            from prompt_ops.interfaces.cli import load_config

            load_config.assert_called_once_with(facility_config_path)

    def test_end_to_end_cli_flow(self, mock_api_key_check, temp_config_file):
        """Test the end-to-end CLI flow with mocked components."""
        # Use Click's test runner instead of directly calling cli()
        from click.testing import CliRunner

        runner = CliRunner()

        # Create mock objects for the migrator and its methods
        mock_migrator = MagicMock()
        mock_dataset_adapter = MagicMock()
        mock_optimized = MagicMock()
        mock_optimized.signature.instructions = "Optimized prompt"

        # Set up return values for the mocked methods
        mock_migrator.load_dataset_with_adapter.return_value = ([], [], [])
        mock_migrator.optimize.return_value = mock_optimized

        # Create a temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_output:
            output_path = tmp_output.name

        try:
            # Set up multiple patches
            with (
                patch(
                    "prompt_ops.interfaces.cli.PromptMigrator",
                    return_value=mock_migrator,
                ),
                patch(
                    "prompt_ops.interfaces.cli.get_dataset_adapter_from_config",
                    return_value=mock_dataset_adapter,
                ),
                patch(
                    "prompt_ops.interfaces.cli.get_models_from_config",
                    return_value=(None, None, "test_task_model", "test_prompt_model"),
                ),
                patch(
                    "prompt_ops.interfaces.cli.get_metric",
                    return_value=MagicMock(),
                ),
                patch(
                    "prompt_ops.interfaces.cli.get_strategy",
                    return_value=MagicMock(),
                ),
                patch("prompt_ops.interfaces.cli.load_config", return_value={}),
                patch(
                    "prompt_ops.interfaces.cli.validate_min_records_in_dataset",
                    return_value=None,
                ),
            ):

                # Run the migrate command with the actual file output
                result = runner.invoke(
                    cli,
                    [
                        "migrate",
                        "--config",
                        temp_config_file,
                        "--output-dir",
                        os.path.dirname(output_path),
                    ],
                )

                # Print the output for debugging
                if result.exit_code != 0:
                    print(f"Command failed with exit code {result.exit_code}")
                    print(f"Output: {result.output}")
                    if result.exception:
                        print(f"Exception: {result.exception}")

                # Check that the command ran successfully
                assert result.exit_code == 0

                # Check that the migrator methods were called
                mock_migrator.load_dataset_with_adapter.assert_called_once()
                mock_migrator.optimize.assert_called_once()

                # Verify the migrator was properly initialized
                from prompt_ops.interfaces.cli import PromptMigrator

                PromptMigrator.assert_called_once()
        finally:
            # Clean up the temporary output file
            if os.path.exists(output_path):
                os.unlink(output_path)
