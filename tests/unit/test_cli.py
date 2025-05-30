import pytest
from click.testing import CliRunner


def test_cli_help():
    """Test that the CLI help command works."""
    try:
        from llama_prompt_ops.interfaces.cli import cli
    except ImportError:
        pytest.skip("CLI module not found, skipping test")

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    # Just check that it runs without crashing
    assert "Usage:" in result.output


def test_cli_commands_exist():
    """Test that the expected commands exist in the CLI."""
    try:
        from llama_prompt_ops.interfaces.cli import cli
    except ImportError:
        pytest.skip("CLI module not found, skipping test")

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    # Check for common commands that should be in the help output
    help_text = result.output

    command_candidates = ["migrate", "create"]
    found_commands = [cmd for cmd in command_candidates if cmd in help_text]

    assert len(found_commands) == len(
        command_candidates
    ), f"Expected all commands {command_candidates} to be present, but only found {found_commands}"
