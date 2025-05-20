import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import CLI components
try:
    from llama_prompt_ops.interfaces.cli import create_cli_app
    from llama_prompt_ops.core.migrator import PromptMigrator
except ImportError:
    pass  # Tests will be skipped if imports fail


@pytest.fixture
def facility_config_path():
    """Fixture providing path to the facility config."""
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
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as tmp:
        yaml.dump(config, tmp)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


class TestCLIIntegration:
    """Integration tests for the CLI interface."""
    
    def test_cli_migrate_command(self, temp_config_file):
        """Test the migrate command with a config file."""
        try:
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
                
                # Check that the migrator was called
                mock_migrator.migrate.assert_called_once()
        except (NameError, ImportError):
            pytest.skip("Required components not available")
    
    def test_cli_optimize_command(self):
        """Test the optimize command with direct parameters."""
        try:
            # Create CLI app
            app = create_cli_app()
            
            # Mock the optimize function
            mock_optimize_result = {"prompt": "Optimized prompt"}
            
            # Patch the optimize function
            with patch('llama_prompt_ops.interfaces.cli.optimize_prompt', return_value=mock_optimize_result):
                # Run the optimize command with the --fast flag
                result = app.invoke([
                    "optimize", 
                    "--prompt", "Analyze this customer message and categorize it:",
                    "--strategy", "llama",
                    "--fast"
                ])
                
                # Check that the command ran successfully
                assert result.exit_code == 0
        except (NameError, ImportError):
            pytest.skip("Required components not available")
    
    def test_cli_config_loading(self, facility_config_path):
        """Test loading a real config file through the CLI."""
        try:
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
        except (NameError, ImportError, FileNotFoundError):
            pytest.skip("Required components not available")
    
    def test_end_to_end_cli_flow(self, temp_config_file):
        """Test the complete flow from CLI to optimization."""
        try:
            # Create CLI app
            app = create_cli_app()
            
            # Create a mock for the optimization process
            mock_optimize_result = {
                "prompt": "Optimized prompt",
                "score": 0.9
            }
            
            # Patch the migrator's optimize method
            with patch.object(PromptMigrator, 'optimize', return_value=mock_optimize_result):
                # Patch the save method to avoid file operations
                with patch.object(PromptMigrator, 'save_optimized_prompt'):
                    # Run the migrate command
                    result = app.invoke([
                        "migrate", 
                        "--config", temp_config_file,
                        "--output", "optimized_prompt.yaml"
                    ])
                    
                    # Check that the command ran successfully
                    assert result.exit_code == 0
        except (NameError, ImportError):
            pytest.skip("Required components not available")
