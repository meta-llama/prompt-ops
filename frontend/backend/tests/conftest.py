"""
Shared pytest fixtures for backend tests.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir() -> Generator[str, None, None]:
    """Create a temporary upload directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_dataset():
    """Sample dataset for testing."""
    return [
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "Who wrote Romeo and Juliet?", "answer": "William Shakespeare"},
    ]


@pytest.fixture
def sample_dataset_with_nested_fields():
    """Sample dataset with nested field structure."""
    return [
        {
            "fields": {
                "input": "Subject: Question about service\n\nHello, I have a question."
            },
            "answer": '{"category": "inquiry", "urgency": "low"}',
        },
        {
            "fields": {"input": "Subject: Urgent issue\n\nI need help immediately!"},
            "answer": '{"category": "support", "urgency": "high"}',
        },
    ]


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "dataset": "test.json",
        "datasetAdapter": "standard_json",
        "prompt": "Answer the following question concisely.",
        "metrics": "Exact Match",
        "model": "Llama 3.3 70B",
        "proposer": "Llama 3.3 70B",
        "strategy": "Basic",
        "useLlamaTips": True,
    }


@pytest.fixture
def mock_dspy_optimizer():
    """Mock DSPy optimizer for testing."""
    mock_optimizer = MagicMock()
    mock_optimizer.optimize.return_value = MagicMock(
        instruction="Optimized instruction here"
    )
    return mock_optimizer


@pytest.fixture
def mock_llm_response():
    """Mock LLM API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Enhanced prompt text"
    return mock_response


@pytest.fixture
def sample_project_config():
    """Sample project configuration YAML."""
    return """
system_prompt:
  inputs:
  - question
  outputs:
  - answer
  file: prompts/prompt.txt
dataset:
  adapter_class: prompt_ops.core.datasets.ConfigurableJSONAdapter
  path: data/dataset.json
  train_size: 0.5
  validation_size: 0.2
  input_field: question
  golden_output_field: answer
model:
  api_base: https://openrouter.ai/api/v1
  temperature: 0
  max_tokens: 4096
  task_model: openrouter/meta-llama/llama-3.1-8b-instruct
  proposer_model: openrouter/meta-llama/llama-3.1-8b-instruct
metric:
  class: prompt_ops.core.metrics.ExactMatchMetric
optimization:
  strategy: basic
"""


@pytest.fixture
def sample_wizard_data():
    """Sample wizard data for config transformation."""
    return {
        "dataset": "test.json",
        "datasetType": "qa",
        "fieldMappings": {"question": "question", "answer": "answer"},
        "prompt": "Answer the question concisely.",
        "model": "Llama 3.3 70B",
        "proposerModel": "Llama 3.3 70B",
        "metric": "Exact Match",
        "strategy": "Basic",
        "useLlamaTips": True,
    }


@pytest.fixture(autouse=True)
def reset_config_after_test():
    """Reset any global config state after each test."""
    yield
    # Cleanup code here if needed
