"""
Command-line interface for the prompt migrator.

This module provides a CLI for using the prompt migrator functionality,
including commands for optimizing individual prompts, batch processing,
and optimization using YAML configuration files.
"""

import importlib
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import click

from ..core.prompt_strategies import BaseStrategy, LightOptimizationStrategy
from ..core.model_strategies import LlamaStrategy
from ..core.migrator import PromptMigrator
from ..core.model import setup_model
from ..core.metrics import DSPyMetricAdapter, StandardJSONMetric
from ..core.datasets import DatasetAdapter, load_dataset


@click.group()
def cli():
    """
    Prompt Migrator - A tool for migrating and optimizing prompts for Llama models.
    """
    pass


@cli.command(name="optimize")
@click.option(
    "--prompt",
    required=True,
    help="The prompt text to optimize"
)
@click.option(
    "--strategy",
    type=click.Choice(["base", "light", "heavy"], case_sensitive=False),
    default="light",
    show_default=True,
    help="The optimization strategy to apply"
)
@click.option(
    "--model",
    default="llama-3",
    show_default=True,
    help="Target model name"
)
def optimize_prompt(prompt: str, strategy: str, model: str):
    """
    Optimize a single prompt for Llama models.
    """
    # Map strategy name to class
    strategy_map = {
        "base": BaseStrategy,
        "light": LightOptimizationStrategy,
    }
    
    # Create strategy instance
    strategy_class = strategy_map[strategy.lower()]
    strategy_instance = strategy_class(model_name=model)
    
    # Create migrator and optimize
    from ..core.migrator import PromptMigrator
    migrator = PromptMigrator(strategy=strategy_instance)
    
    # Optimize the prompt
    optimized = migrator.optimize({"text": prompt})
    
    # Display results
    click.echo("\nOriginal prompt:")
    click.echo(f"{prompt}\n")
    click.echo("Optimized prompt:")
    click.echo(f"{optimized}\n")





# Helper functions for optimize-with-config command
def resolve_class(class_type_or_path, class_map):
    """
    Resolve a class type to full class path.
    
    Args:
        class_type_or_path: Either a known type or a full class path
        class_map: Mapping of shorthand names to full class paths
                               
    Returns:
        str: Full class path
    """
    # If it's a known type, use the mapping
    if class_type_or_path.lower() in class_map:
        return class_map[class_type_or_path.lower()]
    
    # Otherwise assume it's already a full class path
    return class_type_or_path


def load_class_dynamically(class_path):
    """
    Dynamically import and return a class from its path.
    
    Args:
        class_path: Full import path to the class
        
    Returns:
        The class object
        
    Raises:
        ValueError: If the class cannot be imported
    """
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ValueError(f"Failed to import class {class_path}: {str(e)}")


def get_dataset_adapter(config):
    """
    Create adapter from configuration.
    
    Args:
        config: The configuration dictionary
        
    Returns:
        DatasetAdapter: Instantiated adapter
        
    Raises:
        ValueError: If adapter configuration is invalid
    """
    # Default adapter class map for convenience
    ADAPTER_CLASS_MAP = {
        "standard_json": "prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "rag_json": "prompt_ops.core.datasets.RAGJSONAdapter",
    }
    
    dataset_config = config.get("dataset", {})
    adapter_class_path = dataset_config.get("adapter_class")
    dataset_path = dataset_config.get("path")
    
    if not adapter_class_path:
        raise ValueError("Adapter class not specified in configuration")
    
    if not dataset_path:
        raise ValueError("Dataset path not specified in configuration")
    
    # Resolve adapter class path if it's a known type
    adapter_class_path = resolve_class(adapter_class_path, ADAPTER_CLASS_MAP)
    
    try:
        # Import the class dynamically
        adapter_class = load_class_dynamically(adapter_class_path)
        
        # Get file format if specified
        file_format = dataset_config.get("file_format")
        
        # Get adapter-specific parameters
        adapter_params = dataset_config.get("adapter_params", {})
        
        # Create and return the adapter instance
        return adapter_class(dataset_path=dataset_path, file_format=file_format, **adapter_params)
    except ValueError as e:
        raise ValueError(f"Failed to load adapter: {str(e)}")


def get_metric(config, model):
    """
    Create metric from configuration.
    
    Args:
        config: The configuration dictionary
        model: The model to use for the metric
        
    Returns:
        A metric instance
    """
    # Default metric class map for convenience
    METRIC_CLASS_MAP = {
        "similarity": "prompt_ops.core.metrics.DSPyMetricAdapter",
        "standard_json": "prompt_ops.core.metrics.StandardJSONMetric",
    }
    
    metric_config = config.get("metric", {})
    metric_class_path = metric_config.get("class")
    
    if not metric_class_path:
        # Default to DSPyMetricAdapter with similarity signature
        return DSPyMetricAdapter(model=model, signature_name="similarity")
    
    # Resolve metric class path if it's a known type
    metric_class_path = resolve_class(metric_class_path, METRIC_CLASS_MAP)
    
    try:
        # Import the class dynamically
        metric_class = load_class_dynamically(metric_class_path)
        
        # Get metric-specific parameters
        metric_params = metric_config.get("params", {})
        
        # Create and return the metric instance
        if metric_class == DSPyMetricAdapter:
            # DSPyMetricAdapter requires the model parameter
            return metric_class(model=model, **metric_params)
        else:
            # Other metric classes may not need the model
            return metric_class(**metric_params)
    except ValueError as e:
        raise ValueError(f"Failed to load metric: {str(e)}")


def load_config(config_path):
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load configuration from {config_path}: {str(e)}")


@cli.command(name="migrate")
@click.option(
    "--config",
    required=True,
    help="Path to the YAML configuration file"
)
@click.option(
    "--model",
    default=None,
    help="Override the model specified in the config file"
)
@click.option(
    "--output-dir",
    default="results",
    help="Directory to save optimization results"
)
@click.option(
    "--api-key-env",
    default="OPENROUTER_API_KEY",
    help="Environment variable name for the API key"
)
def migrate(config, model, output_dir, api_key_env):
    """
    Migrate and optimize prompts using a YAML configuration file.
    
    This command loads a configuration file that specifies the model,
    dataset, prompt, metric, and optimization strategy to use.
    
    Example:
        prompt-ops migrate --config configs/facility.yaml
    """
    # Check if API key is set
    api_key = os.getenv(api_key_env)
    if not api_key:
        click.echo(f"Error: {api_key_env} environment variable not set", err=True)
        click.echo(f"Please set it with: export {api_key_env}=your_key_here", err=True)
        sys.exit(1)
    
    # Load configuration
    try:
        config_dict = load_config(config)
        click.echo(f"Loaded configuration from {config}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    
    # Use config values for model setup
    model_config = config_dict.get("model", {})
    model_instance = setup_model(
        model_name=model if model else model_config.get("name", "openrouter/meta-llama/llama-3.3-70b-instruct"),
        api_base=model_config.get("api_base", "https://openrouter.ai/api/v1"),
        api_key=api_key,
        max_tokens=model_config.get("max_tokens", 2048),
        temperature=model_config.get("temperature", 0.0),
        cache=model_config.get("cache", False)
    )
    
    # Create metric based on config
    try:
        metric = get_metric(config_dict, model_instance)
        click.echo(f"Using metric: {metric.__class__.__name__}")
    except ValueError as e:
        click.echo(f"Error creating metric: {str(e)}", err=True)
        sys.exit(1)
    
    # Get dataset adapter from config
    try:
        dataset_adapter = get_dataset_adapter(config_dict)
        click.echo(f"Using dataset adapter: {dataset_adapter.__class__.__name__}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    
    # Create strategy based on config
    model_name = model_config.get("name", "").split("/")[-1]
    
    # Check if strategy is specified in config
    optimization_config = config_dict.get("optimization", {})
    strategy_type = optimization_config.get("strategy", "light")
    
    # Create appropriate strategy
    if strategy_type.lower() == "llama":
        strategy = LlamaStrategy(
            model_name=model_name,
            metric=metric,
            task_model=model_instance,
            prompt_model=model_instance,
            apply_formatting=optimization_config.get("apply_formatting", True),
            apply_templates=optimization_config.get("apply_templates", True),
            template_type=optimization_config.get("template_type", "basic")
        )
        click.echo(f"Using LlamaStrategy for model: {model_name}")
    else:  # Default to light strategy
        strategy = LightOptimizationStrategy(
            model_name=model_name,
            metric=metric,
            task_model=model_instance,
            prompt_model=model_instance
        )
        click.echo(f"Using LightOptimizationStrategy for model: {model_name}")
    
    # Create migrator
    migrator = PromptMigrator(
        strategy=strategy,
        task_model=model_instance,
        prompt_model=model_instance
    )
    
    # Load dataset with configured splits
    dataset_config = config_dict.get("dataset", {})
    trainset, valset, testset = migrator.load_dataset_with_adapter(
        dataset_adapter, 
        train_size=dataset_config.get("train_size", 0.25), 
        validation_size=dataset_config.get("validation_size", 0.25)
    )
    
    # Get prompt from config
    prompt_config = config_dict.get("prompt", {})
    prompt_text = prompt_config.get("text", "")
    prompt_inputs = prompt_config.get("inputs", ["question", "context"])
    prompt_outputs = prompt_config.get("outputs", ["answer"])
    
    # Set up output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_prefix = config_dict.get("output", {}).get("prefix", Path(config).stem)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(output_dir, f"{output_prefix}_{timestamp}.json")
    
    # Try to optimize the prompt and save it to a file
    try:
        click.echo("Starting prompt optimization...")
        optimized = migrator.optimize(
            {
                "text": prompt_text, 
                "inputs": prompt_inputs, 
                "outputs": prompt_outputs
            },
            trainset=trainset,
            valset=valset,
            testset=testset,
            save_to_file=True,
            file_path=file_path
        )
        
        click.echo("\n=== Optimization Complete ===")
        click.echo(f"Results saved to: {file_path}")
        click.echo("\nOptimized prompt:")
        click.echo("=" * 80)
        click.echo(optimized.signature.instructions)
        click.echo("=" * 80)
    except Exception as e:
        click.echo(f"\nOptimization failed: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
