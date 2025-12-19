"""
Test the /api/models/test-connection endpoint to verify proper API key handling.
"""

import os

# Import the app
import sys
from unittest.mock import MagicMock, patch

import litellm
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from main import app

client = TestClient(app)


class TestConnectionEndpoint:
    """Test the test-connection endpoint with various API key scenarios."""

    def test_with_valid_custom_key(self):
        """Test connection with a valid custom API key."""
        # Mock the acompletion to simulate a successful call
        with patch("main.acompletion") as mock_completion:
            mock_response = MagicMock()
            mock_response.model = "meta-llama/llama-3.1-8b-instruct"
            mock_response.id = "test-id-123"
            mock_completion.return_value = mock_response

            response = client.post(
                "/api/models/test-connection",
                json={
                    "provider_id": "openrouter",
                    "model_name": "meta-llama/llama-3.1-8b-instruct",
                    "api_base": "https://openrouter.ai/api/v1",
                    "api_key": "sk-or-v1-valid-key-here",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "successful" in data["message"].lower()

            # Verify the mock was called with the custom key
            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert call_kwargs["api_key"] == "sk-or-v1-valid-key-here"

    def test_with_invalid_custom_key(self):
        """Test connection with an invalid custom API key - should fail."""
        # Mock the acompletion to raise an AuthenticationError
        with patch("main.acompletion") as mock_completion:
            mock_completion.side_effect = litellm.exceptions.AuthenticationError(
                message="Invalid API key",
                llm_provider="openrouter",
                model="meta-llama/llama-3.1-8b-instruct",
            )

            response = client.post(
                "/api/models/test-connection",
                json={
                    "provider_id": "openrouter",
                    "model_name": "meta-llama/llama-3.1-8b-instruct",
                    "api_base": "https://openrouter.ai/api/v1",
                    "api_key": "invalid-key",
                },
            )

            assert response.status_code == 200  # Endpoint returns 200 but success=False
            data = response.json()
            assert data["success"] is False
            assert (
                "authentication" in data["message"].lower()
                or "failed" in data["message"].lower()
            )

    def test_with_empty_key_and_env_var(self):
        """Test connection with empty key but valid env var - should use env var."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-env-key"}):
            with patch("main.acompletion") as mock_completion:
                mock_response = MagicMock()
                mock_response.model = "meta-llama/llama-3.1-8b-instruct"
                mock_response.id = "test-id-456"
                mock_completion.return_value = mock_response

                response = client.post(
                    "/api/models/test-connection",
                    json={
                        "provider_id": "openrouter",
                        "model_name": "meta-llama/llama-3.1-8b-instruct",
                        "api_base": "https://openrouter.ai/api/v1",
                        "api_key": "",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

                # Verify the mock was called with the env var key
                mock_completion.assert_called_once()
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["api_key"] == "sk-or-v1-env-key"

    def test_with_no_key_and_no_env_var(self):
        """Test connection with no key and no env var - should fail."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure OPENROUTER_API_KEY is not in environment
            if "OPENROUTER_API_KEY" in os.environ:
                del os.environ["OPENROUTER_API_KEY"]

            response = client.post(
                "/api/models/test-connection",
                json={
                    "provider_id": "openrouter",
                    "model_name": "meta-llama/llama-3.1-8b-instruct",
                    "api_base": "https://openrouter.ai/api/v1",
                    "api_key": "",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert (
                "authentication required" in data["message"].lower()
                or "api key" in data["message"].lower()
            )

    def test_actual_invalid_key_behavior(self):
        """
        Test what actually happens when we pass an invalid key to acompletion.
        This test does NOT mock - it makes a real call to verify LiteLLM behavior.
        """
        # Skip this test in CI or if we don't want to make real API calls
        pytest.skip("Skipping real API call test - enable manually to debug")

        response = client.post(
            "/api/models/test-connection",
            json={
                "provider_id": "openrouter",
                "model_name": "meta-llama/llama-3.1-8b-instruct",
                "api_base": "https://openrouter.ai/api/v1",
                "api_key": "aaaa",  # Invalid 4-char key
            },
        )

        print(f"\nReal API call response: {response.json()}")
        data = response.json()

        # With an invalid key, this SHOULD fail
        assert data["success"] is False, "Invalid API key should fail authentication"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])
