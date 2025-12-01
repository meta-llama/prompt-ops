# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Model abstraction module for prompt-ops.

This module provides a standardized way to create and configure models from
different providers (DSPy, TextGrad, etc.) for use with the prompt-ops tool.
It leverages LiteLLM's unified interface for accessing various LLM providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from .utils.logging import get_logger

try:
    import dspy

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

try:
    import textgrad as tg

    TEXTGRAD_AVAILABLE = True
except ImportError:
    TEXTGRAD_AVAILABLE = False

try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class ModelAdapter(ABC):
    """
    Base adapter class for different model providers.

    This abstract class defines a common interface for all LLM interactions,
    regardless of the underlying implementation (DSPy, TextGrad, etc.).
    """

    @abstractmethod
    def __init__(self, model_name: str = None, **kwargs):
        """
        Initialize the model adapter with configuration parameters.

        Args:
            model_name: The name/identifier of the model to use
            **kwargs: Additional model-specific configuration parameters
        """
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a prompt using the underlying model.

        Args:
            prompt: The input prompt text
            **kwargs: Generation parameters (temperature, max_tokens, etc.)

        Returns:
            The generated text response
        """
        pass

    @abstractmethod
    def generate_with_chat_format(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """
        Generate text using a chat format with multiple messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Generation parameters (temperature, max_tokens, etc.)

        Returns:
            The generated text response
        """
        pass

    def generate_batch(
        self, prompts: List[str], max_threads: int = 1, **kwargs
    ) -> List[str]:
        """
        Generate responses for multiple prompts, optionally in parallel.

        This method is useful for optimizers that need to evaluate multiple
        candidates simultaneously (e.g., PDO duels, batch evaluation).

        Args:
            prompts: List of input prompts
            max_threads: Maximum number of threads for parallel execution
            **kwargs: Generation parameters (temperature, max_tokens, etc.)

        Returns:
            List of generated responses in same order as input prompts
        """
        if max_threads <= 1:
            # Sequential execution
            return [self.generate(prompt, **kwargs) for prompt in prompts]

        # Parallel execution
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [
                executor.submit(self.generate, prompt, **kwargs) for prompt in prompts
            ]
            return [future.result() for future in futures]


class DSPyModelAdapter(ModelAdapter):
    """
    Adapter for DSPy models.
    """

    def __init__(
        self,
        model_name: str = None,
        api_base: str = None,
        api_key: str = None,
        max_tokens: int = 48000,
        temperature: float = 0.0,
        cache: bool = False,
        **kwargs,
    ):
        """
        Initialize the DSPy model adapter with configuration parameters.

        Args:
            model_name: The model identifier (e.g., "openai/gpt-4o-mini")
            api_base: The API base URL
            api_key: The API key
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            cache: Whether to cache responses
            **kwargs: Additional arguments to pass to dspy.LM
        """
        if not DSPY_AVAILABLE:
            raise ImportError(
                "DSPy is not installed. Install it with `pip install dspy-ai`"
            )

        # Store all initialization parameters for reference
        self.kwargs = {
            "model": model_name,
            "api_base": api_base,
            "api_key": api_key,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "cache": cache,
            **kwargs,
        }

        # Create the DSPy model
        self._model = dspy.LM(
            model=model_name,
            api_base=api_base,
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
            cache=cache,
            **kwargs,
        )

        # Configure DSPy to use this model as default
        # This is critical for DSPy's optimizers to work properly
        dspy.configure(lm=self._model)

        # Ensure the model is globally accessible for DSPy
        # This is needed for some DSPy components that don't explicitly take a model parameter
        if hasattr(dspy, "settings"):
            dspy.settings.lm = self._model

        # Set the global LM in the DSPy module for backward compatibility
        # Some DSPy components access this directly
        if hasattr(dspy, "LM"):
            dspy.LM.lm = self._model

        # For DSPy's teleprompt module which is used by MIPROv2
        if hasattr(dspy, "teleprompt"):
            if hasattr(dspy.teleprompt, "lm"):
                dspy.teleprompt.lm = self._model

    def generate(
        self, prompt: str, temperature: float = None, max_tokens: int = None, **kwargs
    ) -> str:
        """
        Generate text from a prompt using the underlying DSPy model.

        Args:
            prompt: The input prompt text
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            **kwargs: Additional generation parameters

        Returns:
            The generated text response
        """
        # Create a temporary configuration with override parameters if provided
        temp_config = {}
        if temperature is not None:
            temp_config["temperature"] = temperature
        if max_tokens is not None:
            temp_config["max_tokens"] = max_tokens

        # Use the model to generate a completion
        if temp_config:
            with dspy.settings(**temp_config):
                response = self._model(prompt)
        else:
            response = self._model(prompt)

        return response

    def generate_with_chat_format(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> str:
        """
        Generate text using a chat format with multiple messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            **kwargs: Additional generation parameters

        Returns:
            The generated text response
        """
        # Format the messages into a single prompt
        formatted_prompt = ""
        for message in messages:
            role = message.get("role", "user").lower()
            content = message.get("content", "")

            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"

        formatted_prompt += "Assistant: "

        # Generate the response using the formatted prompt
        return self.generate(
            formatted_prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


class TextGradModelAdapter(ModelAdapter):
    """
    Adapter for TextGrad models.
    """

    def __init__(
        self,
        model_name: str = None,
        api_base: str = None,
        api_key: str = None,
        **kwargs,
    ):
        """
        Initialize the TextGrad model adapter with configuration parameters.

        Args:
            model_name: The model identifier with provider prefix (e.g., "openrouter/meta-llama/llama-3.3-70b-instruct")
            api_base: The API base URL
            api_key: The API key
            **kwargs: Additional arguments to pass to tg.get_engine
        """
        if not TEXTGRAD_AVAILABLE:
            raise ImportError(
                "TextGrad is not installed. Install it with `pip install textgrad`"
            )

        # Store all initialization parameters for reference
        self.kwargs = {
            "engine_name": model_name,
            "api_base": api_base,
            "api_key": api_key,
            **kwargs,
        }

        # Prepare engine kwargs
        engine_kwargs = {}

        # Add API base and key if provided
        if api_base:
            engine_kwargs["api_base"] = api_base

        if api_key:
            engine_kwargs["api_key"] = api_key

        # Add remaining kwargs
        engine_kwargs.update(kwargs)

        # Get the engine
        self._model = tg.get_engine(engine_name=model_name, **engine_kwargs)

    def generate(
        self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024, **kwargs
    ) -> str:
        """
        Generate text from a prompt using the underlying TextGrad model.

        Args:
            prompt: The input prompt text
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters

        Returns:
            The generated text response
        """
        # TextGrad uses a different API for generation
        response = self._model.complete(
            prompt=prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

        return response.text

    def generate_with_chat_format(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ) -> str:
        """
        Generate text using a chat format with multiple messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters

        Returns:
            The generated text response
        """
        # TextGrad has native support for chat format
        chat_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            chat_messages.append({"role": role, "content": content})

        response = self._model.chat_complete(
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return response.text


class LiteLLMModelAdapter(ModelAdapter):
    """
    Lightweight adapter using LiteLLM for simple text generation.

    Provides a clean "prompt in, string out" interface without
    framework overhead. Ideal for optimization strategies that
    don't need DSPy's advanced features.
    """

    def __init__(
        self,
        model_name: str = None,
        api_base: str = None,
        api_key: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        **kwargs,
    ):
        """
        Initialize the LiteLLM model adapter with configuration parameters.

        Args:
            model_name: The model identifier with provider prefix (e.g., "openrouter/meta-llama/llama-3.3-70b-instruct")
                       LiteLLM auto-detects the provider and uses the appropriate API key from environment
            api_base: The API base URL (optional, LiteLLM uses provider defaults)
            api_key: The API key (optional, LiteLLM reads from provider-specific env vars like OPENROUTER_API_KEY)
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional arguments to pass to litellm.completion
        """
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "LiteLLM is not installed. Install it with `pip install litellm`"
            )

        # Store configuration
        self.model_name = model_name
        self.api_base = api_base
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.kwargs = kwargs

    def generate(
        self, prompt: str, temperature: float = None, max_tokens: int = None, **kwargs
    ) -> str:
        """
        Generate text from a prompt using LiteLLM.

        Args:
            prompt: The input prompt text
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            **kwargs: Additional generation parameters

        Returns:
            The generated text response
        """
        # Use override values or defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        # Prepare LiteLLM call
        messages = [{"role": "user", "content": prompt}]

        # Filter out DSPy-specific parameters that LiteLLM doesn't understand
        filtered_kwargs = {
            k: v
            for k, v in self.kwargs.items()
            if k not in ["cache", "model"]  # Remove DSPy-specific params
        }

        # Prepare kwargs for litellm
        litellm_kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
            **filtered_kwargs,
            **kwargs,
        }

        # Add API base if specified
        if self.api_base:
            litellm_kwargs["api_base"] = self.api_base

        try:
            response = litellm.completion(**litellm_kwargs)

            # Extract text from response
            return response.choices[0].message.content

        except Exception as e:
            # Convert to our standard error types if needed
            raise e

    def generate_with_chat_format(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> str:
        """
        Generate text using a chat format with multiple messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            **kwargs: Additional generation parameters

        Returns:
            The generated text response
        """
        # Use override values or defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        # Filter out DSPy-specific parameters that LiteLLM doesn't understand
        filtered_kwargs = {
            k: v
            for k, v in self.kwargs.items()
            if k not in ["cache", "model"]  # Remove DSPy-specific params
        }

        # Prepare kwargs for litellm
        litellm_kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
            **filtered_kwargs,
            **kwargs,
        }

        # Add API base if specified
        if self.api_base:
            litellm_kwargs["api_base"] = self.api_base

        try:
            response = litellm.completion(**litellm_kwargs)

            # Extract text from response
            return response.choices[0].message.content

        except Exception as e:
            # Convert to our standard error types if needed
            raise e


def setup_model(model_name=None, adapter_type="dspy", **kwargs):
    """
    Set up a model adapter using the specified adapter type.

    This function provides a unified interface for creating model adapters from different providers.
    It supports both simple model identifiers (e.g., "openai/gpt-4o-mini") and custom configurations.

    Args:
        model_name: The model identifier (e.g., "openai/gpt-4o-mini", "anthropic/claude-3-opus-20240229")
        adapter_type: The adapter type to use ("dspy", "textgrad", or "litellm")
        **kwargs: Additional adapter-specific configuration options

    Returns:
        A ModelAdapter instance that provides a unified interface to the underlying model

    Raises:
        ValueError: If the adapter type is not supported
        ImportError: If the required library is not installed

    Examples:
        # Simple usage with known providers
        adapter = setup_model("openai/gpt-4o-mini")
        response = adapter.generate("Tell me about AI")

        # Custom configuration for vLLM
        adapter = setup_model(
            model_name="vllm_llama_8b",
            api_base="http://localhost:8000/v1",
            api_key="fake-key"
        )

        # Using with TextGrad and chat format
        adapter = setup_model(
            model_name="openrouter/meta-llama/llama-3.3-70b-instruct",
            adapter_type="textgrad"
        )
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about AI"}
        ]
        response = adapter.generate_with_chat_format(messages)
    """
    # Create adapter based on type
    logger = get_logger()
    if adapter_type.lower() == "dspy":
        # For DSPy, rename model_name to match the expected parameter
        if model_name and "model_name" not in kwargs:
            kwargs["model_name"] = model_name
        adapter = DSPyModelAdapter(**kwargs)
        logger.progress(
            f" Using model with DSPy: {kwargs.get('model_name', 'custom configuration')}"
        )
    elif adapter_type.lower() == "textgrad":
        # For TextGrad, use model_name directly
        if model_name and "model_name" not in kwargs:
            kwargs["model_name"] = model_name
        adapter = TextGradModelAdapter(**kwargs)
        logger.progress(
            f" Using model with TextGrad: {kwargs.get('model_name', 'custom configuration')}"
        )
    elif adapter_type.lower() == "litellm":
        # For LiteLLM, use model_name directly
        if model_name and "model_name" not in kwargs:
            kwargs["model_name"] = model_name
        adapter = LiteLLMModelAdapter(**kwargs)
        logger.progress(
            f" Using model with LiteLLM: {kwargs.get('model_name', 'custom configuration')}"
        )
    else:
        raise ValueError(f"Unsupported adapter type: {adapter_type}")

    return adapter


def get_model_adapter(adapter_type, **kwargs):
    """
    Get a model adapter instance by type.

    Args:
        adapter_type: The adapter type ("dspy", "textgrad", or "litellm")
        **kwargs: Configuration parameters for the adapter

    Returns:
        A ModelAdapter instance

    Raises:
        ValueError: If the adapter type is not supported
    """
    return setup_model(adapter_type=adapter_type, **kwargs)
