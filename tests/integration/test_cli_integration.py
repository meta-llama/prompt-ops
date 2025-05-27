import os
import pytest
import tempfile
import yaml
from pathlib import Path

# import unittest.mock which should always be available
from unittest.mock import patch, MagicMock

# check if cli components are available
# there are legitimate scenarios where these might not be available:::
# 1. during development when only testing core functionality
# 2. in environments where only a subset of dependencies are installed
# 3. when running tests for specific components in isolation
CLI_COMPONENTS_AVAILABLE = False
try:
    from llama_prompt_ops.interfaces.cli import create_cli_app
    from llama_prompt_ops.core.migrator import PromptMigrator
    CLI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    # Record the specific import error for better diagnostics
    CLI_IMPORT_ERROR = str(e)


@pytest.fixture
def facility_config_path():
    """fixture providing path to the facility config."""
    base_dir = Path(__file__).parent.parent.parent
    return str(base_dir / "use-cases" / "facility-support-analyzer" / "facility-simple.yaml")


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config = {
        "dataset": {
            "path": "test_dataset.json",
            "input_field": ["fields", "input"],
            "golden_output_field": "answer"
        },
        "model": {
            "name": "test-model",
            "task_model": "test-model",
            "proposer_model": "test-model"
        },
        "metric": {
            "class": "llama_prompt_ops.core.metrics.FacilityMetric",
            "strict_json": False,
            "output_field": "answer"
        },
        "optimization": {
            "strategy": "llama"
        }
    }
    
    # Using delete=True allows pytest to handle cleanup automatically, The file will be deleted when the context manager exits
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=True) as tmp:
        yaml.dump(config, tmp)
        tmp.flush()  # Ensure all data is written to disk
        yield tmp.name  # Yield inside the context manager


# Define a detailed reason for skipping that explains when and why tests are skipped
def get_skip_reason():
    if not CLI_COMPONENTS_AVAILABLE:
        return f"CLI components not available: {CLI_IMPORT_ERROR if 'CLI_IMPORT_ERROR' in globals() else 'Unknown import error'}. " \
               f"These tests verify CLI functionality which is considered optional and separate from core functionality."
    return None


# Use a more explicit skipif with a function that provides detailed information
@pytest.mark.skipif(not CLI_COMPONENTS_AVAILABLE, reason=get_skip_reason())
class TestCLIIntegration:
    """Integration tests for the CLI interface."""
    
    def test_cli_migrate_command(self, temp_config_file):
        """Test the migrate command with a config file."""
        # Create CLI app
        app = create_cli_app()
        
        # Mock the PromptMigrator
        mock_migrator = MagicMock()
        mock_migrator.migrate.return_value = {"prompt": "Optimized prompt"}
        
        # Patch the PromptMigrator class
        with patch('llama_prompt_ops.interfaces.cli.PromptMigrator', return_value=mock_migrator):
            # Run the migrate command
            result = app.invoke(["migrate", "--config", temp_config_file])
            
            # Check that the command ran successfully
            assert result.exit_code == 0
            
            # Check that the migrator was called with the right arguments
            mock_migrator.migrate.assert_called_once()
            
            # Verify that PromptMigrator was initialized with the config file
            from llama_prompt_ops.interfaces.cli import PromptMigrator
            PromptMigrator.assert_called_once()
            
            # Get the config argument passed to PromptMigrator
            config_arg = PromptMigrator.call_args[1].get('config')
            assert config_arg is not None, "Config argument was not passed to PromptMigrator"
            
            # If we have access to the actual config content, we could verify it matches
            # what was loaded from temp_config_file
    
    def test_cli_config_loading(self, facility_config_path):
        """Test loading a real config file through the CLI."""
        # Create CLI app
        app = create_cli_app()
        
        # Mock the PromptMigrator
        mock_migrator = MagicMock()
        mock_migrator.migrate.return_value = {"prompt": "Optimized prompt"}
        
        # Patch the PromptMigrator class
        with patch('llama_prompt_ops.interfaces.cli.PromptMigrator', return_value=mock_migrator):
            # Run the migrate command with the real config
            result = app.invoke(["migrate", "--config", facility_config_path])
            
            # Check that the command ran successfully
            assert result.exit_code == 0
            
            # Check that the migrator was created with the config
            from llama_prompt_ops.interfaces.cli import PromptMigrator
            PromptMigrator.assert_called_once()
            
            # Verify the config argument passed to PromptMigrator
            config_arg = PromptMigrator.call_args[1].get('config')
            assert config_arg is not None, "Config argument was not passed to PromptMigrator"
            
            # Check that the migrate method was called
            mock_migrator.migrate.assert_called_once()
            
            # Verify the config file path matches what we provided
            assert facility_config_path in str(PromptMigrator.call_args), "Facility config path was not used"
    
    def test_end_to_end_cli_flow(self, temp_config_file):
        """Test the complete flow from CLI to optimization."""
        # Create CLI app
        app = create_cli_app()
        
        # Create a mock for the optimization process
        mock_optimize_result = {
            "prompt": "Optimized prompt",
            "score": 0.9
        }
        
        # Create a temporary output file path
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp_output:
            output_path = tmp_output.name
        
        try:
            # Patch the migrator's optimize method
            with patch.object(PromptMigrator, 'optimize', return_value=mock_optimize_result):
                # Run the migrate command with the actual file output
                result = app.invoke([
                    "migrate", 
                    "--config", temp_config_file,
                    "--output", output_path
                ])
                
                # Check that the command ran successfully
                assert result.exit_code == 0
                
                # Verify that the output file was created
                assert os.path.exists(output_path), "Output file was not created"
                
                # Verify file content
                with open(output_path, 'r') as f:
                    content = yaml.safe_load(f)
                    assert "prompt" in content, "Output file doesn't contain expected content"
                    assert content["prompt"] == "Optimized prompt"
        finally:
            # Clean up the temporary output file
            if os.path.exists(output_path):
                os.unlink(output_path)
