import json
import logging
import os
import time
from unittest.mock import mock_open, patch

import pytest

from llama_prompt_ops.core.utils.logging import LoggingManager, get_logger


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the logger singleton before each test."""
    # This is a bit of a hack to reset the singleton for isolated tests
    import llama_prompt_ops.core.utils.logging

    llama_prompt_ops.core.utils.logging._LOG_SINGLETON = None


def test_get_logger_singleton():
    """Test that get_logger returns a singleton instance."""
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2


def test_logging_level(caplog):
    """Test that the logging level is set correctly."""
    logger = get_logger()
    logger.set_level("DEBUG")

    with caplog.at_level(logging.DEBUG):
        logger.progress("debug message", level="DEBUG")
        logger.progress("info message", level="INFO")

    assert "debug message" in caplog.text
    assert "info message" in caplog.text

    caplog.clear()

    logger.set_level("INFO")
    with caplog.at_level(logging.INFO):
        logger.progress("debug message", level="DEBUG")
        logger.progress("info message", level="INFO")

    assert "debug message" not in caplog.text
    assert "info message" in caplog.text


def test_phase_timing():
    """Test the phase timing context manager."""
    logger = get_logger()

    with logger.phase("test_phase"):
        time.sleep(0.01)

    assert "test_phase" in logger.timings
    assert logger.timings["test_phase"] > 0


def test_log_metric():
    """Test that metrics are logged correctly."""
    logger = get_logger()
    logger.log_metric("accuracy", 0.95, step=1)

    assert len(logger.metrics) == 1
    metric = logger.metrics[0]
    assert metric["key"] == "accuracy"
    assert metric["value"] == 0.95
    assert metric["step"] == 1


@patch("atexit.register")
def test_export_json(mock_atexit_register):
    """Test exporting timings and metrics to a JSON file."""
    logger = get_logger()
    logger.start_phase("export_phase")
    time.sleep(0.01)
    logger.end_phase("export_phase")
    logger.log_metric("loss", 0.1)

    m = mock_open()
    with patch("builtins.open", m):
        logger.export_json("test_log.json")

    m.assert_called_once_with("test_log.json", "w")

    # Get the content that was written to the file
    handle = m()
    # Join all the calls to write to reconstruct the JSON string
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    data = json.loads(written_content)

    assert "timings" in data
    assert "export_phase" in data["timings"]
    assert "metrics" in data
    assert len(data["metrics"]) == 1
    assert data["metrics"][0]["key"] == "loss"
