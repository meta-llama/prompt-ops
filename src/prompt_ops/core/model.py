# abstract class (to generalize the interface i.e. predict etc)
"""
Model abstraction module for prompt migrator.

This module provides a standardized way to create and configure models from
different providers (DSPy, TextGrad, etc.) for use with the prompt migrator.
It leverages LiteLLM's unified interface for accessing various LLM providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

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


class ModelAdapter(ABC):
    """
    Base adapter class for different model providers.
    
    This abstract class defines the interface that all model adapters must implement.
    """
    
    @abstractmethod
    def get_model(self, **kwargs) -> Any:
        """
        Get a model instance from the provider.
        
        Args:
            **kwargs: Provider-specific configuration options
            
        Returns:
            A model instance from the provider
        """
        pass
    
    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        Configure the model provider with global settings.
        
        Args:
            **kwargs: Provider-specific configuration options
        """
        pass


class DSPyModelAdapter(ModelAdapter):
    """
    Adapter for DSPy models.
    """
    
    def __init__(self):
        """Initialize the DSPy model adapter."""
        if not DSPY_AVAILABLE:
            raise ImportError("DSPy is not installed. Install it with `pip install dspy-ai`")
    
    def get_model(self, **kwargs) -> Any:
        """
        Get a DSPy LM instance.
        
        Args:
            model: The model identifier (e.g., "openai/gpt-4o-mini" or "anthropic/claude-3-opus-20240229")
            api_base: The API base URL (optional)
            api_key: The API key (optional)
            max_tokens: Maximum number of tokens to generate (default: 2048)
            temperature: Sampling temperature (default: 0.0)
            cache: Whether to cache responses (default: False)
            **kwargs: Additional arguments to pass to dspy.LM
            
        Returns:
            A dspy.LM instance
        """
        model = dspy.LM(
            model=kwargs.get("model"),
            api_base=kwargs.get("api_base"),
            api_key=kwargs.get("api_key"),
            max_tokens=kwargs.get("max_tokens", 48000),
            temperature=kwargs.get("temperature", 0.0),
            cache=kwargs.get("cache", False),
            **{k: v for k, v in kwargs.items() if k not in ["model", "api_base", "api_key", "max_tokens", "temperature", "cache"]}
        )
        
        return model
    
    def configure(self, model=None, **kwargs) -> None:
        """
        Configure DSPy with a default model.
        
        Args:
            model: The model to set as default
            **kwargs: Additional configuration options
        """
        if model:
            dspy.configure(lm=model)


class TextGradModelAdapter(ModelAdapter):
    """
    Adapter for TextGrad models.
    """
    
    def __init__(self):
        """Initialize the TextGrad model adapter."""
        if not TEXTGRAD_AVAILABLE:
            raise ImportError("TextGrad is not installed. Install it with `pip install textgrad`")
    
    def get_model(self, **kwargs) -> Any:
        """
        Get a TextGrad engine instance.
        
        Args:
            engine_name: The engine name (e.g., "openrouter/meta-llama/llama-3.3-70b-instruct")
            api_base: The API base URL (optional)
            api_key: The API key (optional)
            **kwargs: Additional arguments to pass to tg.get_engine
            
        Returns:
            A TextGrad engine instance
        """
        engine_kwargs = {}
        
        # Add API base and key if provided
        if "api_base" in kwargs:
            engine_kwargs["api_base"] = kwargs.pop("api_base")
        
        if "api_key" in kwargs:
            engine_kwargs["api_key"] = kwargs.pop("api_key")
        
        # Get the engine name
        engine_name = kwargs.pop("engine_name", None)
        
        # Fall back to "model" if engine_name is not provided
        if not engine_name and "model" in kwargs:
            engine_name = kwargs.pop("model")
        
        # Add remaining kwargs
        engine_kwargs.update(kwargs)
        
        # Get the engine
        return tg.get_engine(engine_name=engine_name, **engine_kwargs)
    
    def configure(self, **kwargs) -> None:
        """
        Configure TextGrad with global settings.
        
        Args:
            **kwargs: Configuration options
        """
        # TextGrad doesn't have a global configuration method like DSPy
        pass


def setup_model(model_name=None, adapter_type="dspy", **kwargs):
    """
    Set up a model using the specified adapter.
    
    This function provides a unified interface for creating models from different providers.
    It supports both simple model identifiers (e.g., "openai/gpt-4o-mini") and custom configurations.
    
    Args:
        model_name: The model identifier (e.g., "openai/gpt-4o-mini", "anthropic/claude-3-opus-20240229")
        adapter_type: The adapter type to use ("dspy" or "textgrad")
        **kwargs: Additional adapter-specific configuration options
        
    Returns:
        A model instance from the specified adapter
        
    Raises:
        ValueError: If the adapter type is not supported
        ImportError: If the required library is not installed
        
    Examples:
        # Simple usage with known providers
        model = setup_model("openai/gpt-4o-mini")
        
        # Custom configuration for vLLM
        model = setup_model(
            model_name="vllm_llama_8b",
            api_base="http://localhost:8000/v1",
            api_key="fake-key"
        )
        
        # Using with TextGrad
        model = setup_model(
            model_name="openrouter/meta-llama/llama-3.3-70b-instruct",
            adapter_type="textgrad"
        )
    """
    # Create settings dictionary with model name
    settings = {}
    if model_name:
        settings["model"] = model_name
    
    # Update with additional kwargs
    settings.update(kwargs)
    
    # Create adapter based on type
    if adapter_type.lower() == "dspy":
        adapter = DSPyModelAdapter()
        model = adapter.get_model(**settings)
        adapter.configure(model=model)
        print(f" Using model with DSPy: {settings.get('model', 'custom configuration')}")
    elif adapter_type.lower() == "textgrad":
        adapter = TextGradModelAdapter()
        # TextGrad uses engine_name instead of model
        if "model" in settings:
            settings["engine_name"] = settings.pop("model")
        model = adapter.get_model(**settings)
        print(f" Using model with TextGrad: {settings.get('engine_name', 'custom configuration')}")
    else:
        raise ValueError(f"Unsupported adapter type: {adapter_type}")
    
    return model


def get_model_adapter(adapter_type):
    """
    Get a model adapter instance by type.
    
    Args:
        adapter_type: The adapter type ("dspy" or "textgrad")
        
    Returns:
        A ModelAdapter instance
        
    Raises:
        ValueError: If the adapter type is not supported
    """
    if adapter_type.lower() == "dspy":
        return DSPyModelAdapter()
    elif adapter_type.lower() == "textgrad":
        return TextGradModelAdapter()
    else:
        raise ValueError(f"Unsupported adapter type: {adapter_type}")
        

# For backward compatibility
setup_openrouter_model = setup_model