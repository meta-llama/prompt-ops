# Backend Test Suite

Comprehensive test suite for the prompt-ops backend API.

## Quick Start

```bash
# Install all dependencies (including tests)
cd frontend/backend
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
```

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests
│   ├── test_utils.py          # Utility functions
│   ├── test_config_transformer.py
│   ├── test_routes_datasets.py
│   └── test_routes_projects.py
├── integration/                # Integration tests
│   ├── test_optimization_workflow.py
│   └── test_websocket_optimization.py
└── fixtures/                   # Test data files
```

## Coverage

Test coverage is configured in `pytest.ini`. Reports are generated in:
- **Terminal**: Shows missing lines
- **HTML**: `htmlcov/index.html` (open in browser)
- **JSON**: `coverage.json` (for CI/CD)

View HTML coverage report:
```bash
pytest --cov
open htmlcov/index.html  # macOS
```

## Running Specific Tests

```bash
# Single test file
pytest tests/unit/test_utils.py

# Single test class
pytest tests/unit/test_utils.py::TestLoadClassDynamically

# Single test function
pytest tests/unit/test_utils.py::TestLoadClassDynamically::test_loads_built_in_class

# Tests matching pattern
pytest -k "websocket"
pytest -k "dataset"
```

## Test Options

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run in parallel (with pytest-xdist)
pytest -n auto

# Generate XML report (for CI/CD)
pytest --junitxml=test-results.xml
```

## Writing New Tests

### Unit Test Template

```python
"""Unit tests for new_module.py"""

import pytest
from new_module import function_to_test

class TestNewFeature:
    """Tests for new feature."""

    def test_basic_functionality(self):
        """Test basic use case."""
        result = function_to_test("input")
        assert result == "expected"

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test("invalid")
```

### Integration Test Template

```python
"""Integration tests for new workflow."""

import pytest
from unittest.mock import patch, Mock

class TestNewWorkflow:
    """Integration tests for new workflow."""

    def test_end_to_end(self, client, sample_dataset):
        """Test complete workflow."""
        response = client.post("/api/new-endpoint", json={...})
        assert response.status_code == 200
```

## Fixtures

Common fixtures available (defined in `conftest.py`):

- `client`: FastAPI test client
- `temp_upload_dir`: Temporary directory for file uploads
- `sample_dataset`: Sample QA dataset
- `sample_dataset_with_nested_fields`: Dataset with nested structure
- `sample_config`: Sample configuration dict
- `sample_wizard_data`: Sample wizard/onboarding data
- `mock_dspy_optimizer`: Mocked DSPy optimizer
- `mock_llm_response`: Mocked LLM API response

## Coverage Goals

Target coverage by module:
- **Utils**: 90%+
- **Config Transformer**: 85%+
- **Route Handlers**: 80%+
- **Integration Workflows**: 75%+
- **Overall**: 80%+

## CI/CD Integration

GitHub Actions workflow (`.github/workflows/backend-tests.yml`):

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install -r tests/requirements-test.txt
      - run: pytest --cov --junitxml=test-results.xml
      - uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests Fail with Import Errors

Ensure you're in the backend directory and dependencies are installed:
```bash
cd frontend/backend
pip install -r requirements.txt
```

### WebSocket Tests Timeout

WebSocket tests can be flaky. Increase timeout or skip:
```bash
pytest -m "not websocket"  # Skip WebSocket tests
pytest --timeout=10        # Increase timeout
```

### Coverage Report Not Generated

Ensure pytest-cov is installed:
```bash
pip install pytest-cov
pytest --cov=. tests/
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External Services**: Don't make real API calls
3. **Use Fixtures**: Reuse common test data
4. **Descriptive Names**: Test names should explain what they test
5. **Test Edge Cases**: Not just happy paths
6. **Keep Tests Fast**: Unit tests should run in milliseconds
7. **Document Complex Tests**: Add comments for complex logic

## Related Documentation

- [Backend README](../README.md)
- [API Documentation](../docs/api.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
