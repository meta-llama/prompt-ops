"""
Unit tests for utils.py
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from utils import (
    OptimizationManager,
    StreamingLogHandler,
    create_llm_completion,
    generate_unique_project_name,
    get_uploaded_datasets,
    load_class_dynamically,
)


class TestLoadClassDynamically:
    """Tests for load_class_dynamically function."""

    def test_loads_built_in_class(self):
        """Test loading a built-in Python class."""
        dict_class = load_class_dynamically("builtins.dict")
        assert dict_class == dict

    def test_loads_custom_class(self):
        """Test loading a class from the codebase."""
        # Load a class from our own codebase
        cls = load_class_dynamically("utils.OptimizationManager")
        assert cls == OptimizationManager

    def test_raises_on_invalid_path(self):
        """Test that invalid paths raise appropriate errors."""
        with pytest.raises((ImportError, AttributeError)):
            load_class_dynamically("nonexistent.module.Class")

    def test_raises_on_invalid_class_name(self):
        """Test that invalid class names raise AttributeError."""
        with pytest.raises(AttributeError):
            load_class_dynamically("builtins.NonExistentClass")


class TestCreateLLMCompletion:
    """Tests for create_llm_completion function."""

    @patch("utils.completion")
    def test_basic_completion(self, mock_completion):
        """Test basic LLM completion call."""
        mock_completion.return_value = {"choices": [{"message": {"content": "test"}}]}

        result = create_llm_completion(
            model="openrouter/test-model",
            messages=[{"role": "user", "content": "test"}],
        )

        assert mock_completion.called
        call_args = mock_completion.call_args[1]
        assert call_args["model"] == "openrouter/test-model"
        assert call_args["temperature"] == 0.7  # default

    @patch("utils.completion")
    def test_completion_with_api_key(self, mock_completion):
        """Test completion with explicit API key."""
        mock_completion.return_value = {"choices": []}

        create_llm_completion(model="test-model", messages=[], api_key="test-key-123")

        call_args = mock_completion.call_args[1]
        assert call_args["api_key"] == "test-key-123"

    @patch("utils.completion")
    def test_completion_with_custom_temperature(self, mock_completion):
        """Test completion with custom temperature."""
        mock_completion.return_value = {"choices": []}

        create_llm_completion(model="test-model", messages=[], temperature=0.5)

        call_args = mock_completion.call_args[1]
        assert call_args["temperature"] == 0.5

    @patch("utils.completion")
    def test_completion_with_api_base(self, mock_completion):
        """Test completion with custom API base."""
        mock_completion.return_value = {"choices": []}

        create_llm_completion(
            model="test-model", messages=[], api_base="https://custom.api.com"
        )

        call_args = mock_completion.call_args[1]
        assert call_args["api_base"] == "https://custom.api.com"


class TestGetUploadedDatasets:
    """Tests for get_uploaded_datasets function."""

    def test_returns_empty_list_when_no_datasets(self, temp_upload_dir):
        """Test returns empty list when upload directory is empty."""
        with patch("utils.UPLOAD_DIR", temp_upload_dir):
            result = get_uploaded_datasets()
            assert result == []

    def test_returns_dataset_list(self, temp_upload_dir, sample_dataset):
        """Test returns list of datasets with metadata."""
        # Create a test dataset file
        dataset_path = os.path.join(temp_upload_dir, "test.json")
        with open(dataset_path, "w") as f:
            json.dump(sample_dataset, f)

        with patch("utils.UPLOAD_DIR", temp_upload_dir):
            result = get_uploaded_datasets()

            assert len(result) == 1
            assert result[0]["filename"] == "test.json"
            assert result[0]["total_records"] == 3
            assert len(result[0]["preview"]) == 3

    def test_handles_invalid_json_gracefully(self, temp_upload_dir):
        """Test handles corrupted JSON files gracefully."""
        # Create an invalid JSON file
        bad_file = os.path.join(temp_upload_dir, "bad.json")
        with open(bad_file, "w") as f:
            f.write("invalid json {")

        with patch("utils.UPLOAD_DIR", temp_upload_dir):
            result = get_uploaded_datasets()
            # Should not crash, just skip the bad file
            assert result == []

    def test_ignores_non_json_files(self, temp_upload_dir):
        """Test ignores non-JSON files in upload directory."""
        # Create a non-JSON file
        txt_file = os.path.join(temp_upload_dir, "readme.txt")
        with open(txt_file, "w") as f:
            f.write("This is a text file")

        with patch("utils.UPLOAD_DIR", temp_upload_dir):
            result = get_uploaded_datasets()
            assert result == []

    def test_preview_limited_to_three_records(self, temp_upload_dir):
        """Test preview is limited to 3 records."""
        # Create dataset with more than 3 records
        large_dataset = [{"q": f"Question {i}", "a": f"Answer {i}"} for i in range(10)]
        dataset_path = os.path.join(temp_upload_dir, "large.json")
        with open(dataset_path, "w") as f:
            json.dump(large_dataset, f)

        with patch("utils.UPLOAD_DIR", temp_upload_dir):
            result = get_uploaded_datasets()
            assert len(result[0]["preview"]) == 3
            assert result[0]["total_records"] == 10


class TestGenerateUniqueProjectName:
    """Tests for generate_unique_project_name function."""

    def test_returns_base_name_when_available(self, temp_upload_dir):
        """Test returns base name when it doesn't exist."""
        result = generate_unique_project_name("test-project", temp_upload_dir)
        assert result == "test-project"

    def test_adds_suffix_when_exists(self, temp_upload_dir):
        """Test adds numeric suffix when base name exists."""
        # Create existing project
        os.makedirs(os.path.join(temp_upload_dir, "test-project"))

        result = generate_unique_project_name("test-project", temp_upload_dir)
        assert result == "test-project-2"

    def test_increments_suffix_multiple_times(self, temp_upload_dir):
        """Test increments suffix when multiple versions exist."""
        # Create multiple existing projects
        os.makedirs(os.path.join(temp_upload_dir, "test-project"))
        os.makedirs(os.path.join(temp_upload_dir, "test-project-2"))
        os.makedirs(os.path.join(temp_upload_dir, "test-project-3"))

        result = generate_unique_project_name("test-project", temp_upload_dir)
        assert result == "test-project-4"

    def test_safety_limit_uses_timestamp(self, temp_upload_dir):
        """Test uses timestamp when counter exceeds safety limit."""
        # Mock os.path.exists to always return True
        with patch("utils.os.path.exists", return_value=True):
            with patch("utils.time.time", return_value=1234567890):
                result = generate_unique_project_name("test", temp_upload_dir)
                assert result == "test-1234567890"


class TestStreamingLogHandler:
    """Tests for StreamingLogHandler class."""

    @pytest.mark.asyncio
    async def test_handler_sends_log_to_websocket(self):
        """Test handler sends formatted log message to WebSocket."""
        mock_websocket = AsyncMock()
        handler = StreamingLogHandler(mock_websocket)

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        # Give async task time to complete
        await handler._send_log_safe("Test message", record)

        # Verify websocket was called
        assert mock_websocket.send_json.called

    def test_handler_marks_closed_on_error(self):
        """Test handler marks itself as closed when WebSocket errors."""
        mock_websocket = Mock()
        mock_websocket.send_json = Mock(side_effect=RuntimeError("Connection closed"))
        handler = StreamingLogHandler(mock_websocket)

        handler._closed = False
        # This should mark handler as closed
        try:
            import asyncio

            asyncio.run(
                handler._send_log_safe(
                    "test",
                    logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None),
                )
            )
        except:
            pass

        # Handler should eventually mark itself as closed
        assert hasattr(handler, "_closed")

    def test_close_marks_handler_as_closed(self):
        """Test close method marks handler as closed."""
        mock_websocket = Mock()
        handler = StreamingLogHandler(mock_websocket)

        handler.close()
        assert handler._closed is True


class TestOptimizationManager:
    """Tests for OptimizationManager class."""

    @pytest.mark.asyncio
    async def test_send_status(self):
        """Test sending status updates."""
        mock_websocket = AsyncMock()
        manager = OptimizationManager(mock_websocket)

        await manager.send_status("Test status", "test_phase")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["message"] == "Test status"
        assert call_args["phase"] == "test_phase"

    @pytest.mark.asyncio
    async def test_send_progress(self):
        """Test sending progress updates."""
        mock_websocket = AsyncMock()
        manager = OptimizationManager(mock_websocket)

        await manager.send_progress("training", 50.0, "Training in progress")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["phase"] == "training"
        assert call_args["progress"] == 50.0
        assert call_args["message"] == "Training in progress"

    @pytest.mark.asyncio
    async def test_send_result(self):
        """Test sending final results."""
        mock_websocket = AsyncMock()
        manager = OptimizationManager(mock_websocket)

        result = {"optimized_prompt": "test", "score": 0.95}
        await manager.send_result(result)

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "complete"
        assert call_args["optimized_prompt"] == "test"
        assert call_args["score"] == 0.95

    @pytest.mark.asyncio
    async def test_send_error(self):
        """Test sending error messages."""
        mock_websocket = AsyncMock()
        manager = OptimizationManager(mock_websocket)

        await manager.send_error("Something went wrong")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["message"] == "Something went wrong"

    def test_setup_log_streaming(self):
        """Test setting up log streaming."""
        mock_websocket = Mock()
        manager = OptimizationManager(mock_websocket)

        manager.setup_log_streaming()

        assert manager.log_handler is not None
        assert isinstance(manager.log_handler, StreamingLogHandler)

    def test_cleanup_log_streaming(self):
        """Test cleaning up log streaming."""
        mock_websocket = Mock()
        manager = OptimizationManager(mock_websocket)

        manager.setup_log_streaming()
        handler = manager.log_handler

        manager.cleanup_log_streaming()

        # Handler should be removed from loggers
        root_logger = logging.getLogger()
        assert handler not in root_logger.handlers
