"""
Shared utility functions and classes for the backend API.
"""

import asyncio
import importlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from litellm import completion
from config import OPENROUTER_API_KEY, UPLOAD_DIR
from fastapi import WebSocket


def load_class_dynamically(class_path: str):
    """Import and return class from dotted path string."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_llm_completion(
    model: str,
    messages: list,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
):
    """
    Create a completion using LiteLLM for any OpenAI-compatible API.
    
    Args:
        model: Model name (e.g., "Llama-4-Maverick-17B-128E-Instruct-FP8")
        messages: List of message dicts with 'role' and 'content'
        api_key: API key for authentication (falls back to OPENROUTER_API_KEY)
        api_base: Base URL for the API endpoint (e.g., "https://api.llama.com/compat/v1")
        temperature: Sampling temperature
        **kwargs: Additional arguments passed to litellm.completion
    
    Returns:
        LiteLLM completion response
    """
    key_to_use = api_key or OPENROUTER_API_KEY
    if not key_to_use:
        raise ValueError("API key is required. Provide via parameter or set OPENROUTER_API_KEY in .env")
    
    completion_kwargs = {
        "model": model,
        "messages": messages,
        "api_key": key_to_use,
        "temperature": temperature,
        **kwargs
    }
    
    # Add api_base if provided
    if api_base:
        completion_kwargs["api_base"] = api_base
    
    print(f"🚀 LiteLLM completion - Model: {model}, API Base: {api_base or 'default'}")
    
    return completion(**completion_kwargs)


def get_uploaded_datasets():
    """Get list of uploaded datasets."""
    datasets = []
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(UPLOAD_DIR, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        # Get first few records for preview
                        preview = data[:3] if isinstance(data, list) else []
                        datasets.append(
                            {
                                "name": f"Uploaded: {filename}",
                                "filename": filename,
                                "path": filepath,
                                "preview": preview,
                                "total_records": (
                                    len(data) if isinstance(data, list) else 0
                                ),
                            }
                        )
                except Exception as e:
                    print(f"Error reading dataset {filename}: {e}")
    return datasets


def generate_unique_project_name(base_name: str, base_dir: str) -> str:
    """
    Generate a unique project name by adding incremental suffixes if the project already exists.

    Args:
        base_name: The desired project name (e.g., "qa-project-2025-09-15")
        base_dir: The directory where projects are created

    Returns:
        Unique project name (e.g., "qa-project-2025-09-15-2" if original exists)
    """
    project_path = os.path.join(base_dir, base_name)

    # If the base name doesn't exist, use it
    if not os.path.exists(project_path):
        return base_name

    # Otherwise, find the next available incremental name
    counter = 2
    while True:
        incremental_name = f"{base_name}-{counter}"
        incremental_path = os.path.join(base_dir, incremental_name)

        if not os.path.exists(incremental_path):
            return incremental_name

        counter += 1

        # Safety check to prevent infinite loop (though very unlikely)
        if counter > 1000:
            # Fallback to timestamp-based naming
            timestamp = str(int(time.time()))
            return f"{base_name}-{timestamp}"


class StreamingLogHandler(logging.Handler):
    """Custom log handler that streams log messages to WebSocket clients."""

    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
        self.formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
        self._closed = False

    def emit(self, record):
        """Send log record to WebSocket client."""
        # Skip if we've marked this handler as closed
        if self._closed:
            return

        try:
            log_entry = self.format(record)
            # Create task to send message (non-blocking) only if there's an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._send_log_safe(log_entry, record))
            except RuntimeError:
                # No event loop running, skip WebSocket logging
                pass
        except Exception as e:
            # Avoid infinite recursion by not logging this error
            pass

    async def _send_log_safe(self, log_entry: str, record):
        """Safely send log message, catching WebSocket closure errors."""
        if self._closed:
            return

        try:
            # Check if WebSocket client_state indicates it's still connected
            if hasattr(self.websocket, "client_state"):
                from starlette.websockets import WebSocketState

                if self.websocket.client_state != WebSocketState.CONNECTED:
                    self._closed = True
                    return

            await self.websocket.send_json(
                {
                    "type": "log",
                    "message": log_entry,
                    "level": record.levelname,
                    "logger": record.name,
                    "timestamp": record.created,
                }
            )
        except (RuntimeError, Exception):
            # WebSocket is closed or errored, mark as closed and stop trying to send
            self._closed = True

    def close(self):
        """Mark the handler as closed."""
        self._closed = True
        super().close()


class OptimizationManager:
    """Manages the optimization process with real-time streaming."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.log_handler = None

    async def send_status(self, message: str, phase: str = None):
        """Send status update to client."""
        await self.websocket.send_json(
            {"type": "status", "message": message, "phase": phase or "unknown"}
        )

    async def send_progress(self, phase: str, progress: float, message: str):
        """Send progress update to client."""
        await self.websocket.send_json(
            {
                "type": "progress",
                "phase": phase,
                "progress": progress,
                "message": message,
            }
        )

    async def send_result(self, result: dict):
        """Send final optimization result to client."""
        await self.websocket.send_json({"type": "complete", **result})

    async def send_error(self, error: str):
        """Send error message to client."""
        await self.websocket.send_json({"type": "error", "message": error})

    def setup_log_streaming(self):
        """Set up log handlers to capture all optimization logs."""
        self.log_handler = StreamingLogHandler(self.websocket)
        self.log_handler.setLevel(logging.INFO)

        # Add handler to multiple loggers to capture all output
        loggers_to_stream = [
            logging.getLogger(),  # Root logger
            logging.getLogger("prompt_ops"),  # llama-prompt-ops logger
            logging.getLogger("llama_prompt_ops"),  # Alternative logger name
            logging.getLogger("dspy"),  # DSPy optimization logs
            logging.getLogger("LiteLLM"),  # LiteLLM API call logs
        ]

        for logger in loggers_to_stream:
            logger.addHandler(self.log_handler)

    def cleanup_log_streaming(self):
        """Clean up log handlers."""
        if self.log_handler:
            loggers_to_cleanup = [
                logging.getLogger(),
                logging.getLogger("prompt_ops"),
                logging.getLogger("llama_prompt_ops"),
                logging.getLogger("dspy"),
                logging.getLogger("LiteLLM"),
            ]

            for logger in loggers_to_cleanup:
                try:
                    logger.removeHandler(self.log_handler)
                except ValueError:
                    # Handler not in logger, ignore
                    pass
