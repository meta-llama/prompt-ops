#!/usr/bin/env python
"""
Test the prompt migrator with YAML configuration support.

This script provides a configurable interface for testing the prompt migrator's 
ability to optimize prompts for various tasks. It supports configuration via 
YAML files and command-line arguments.

You need to set the OPENROUTER_API_KEY environment variable before running this script.

Usage:
    export OPENROUTER_API_KEY=your_key_here
    python test_with_config.py --config configs/joule.yaml
    python test_with_config.py --config configs/dox.yaml
    python test_with_config.py --config configs/joule.yaml --model openrouter/anthropic/claude-3-opus
    python test_with_config.py --adapter-class my_package.custom_adapters.MyCustomAdapter

Configuration:
    The script can be configured using a YAML file with the following structure:
    
    model:
      name: "openrouter/meta-llama/llama-3.3-70b-instruct"
      api_base: "https://openrouter.ai/api/v1"
      temperature: 0.0
      
    dataset:
      adapter_class: "prompt_ops.adapters.joule.JouleAdapter"  # Full import path to adapter class
      path: "path/to/dataset.json"
      train_size: 0.25
      validation_size: 0.25
      adapter_params:  # Optional adapter-specific parameters
        param1: value1
        param2: value2
      
    prompt:
      text: "Your prompt text here..."
      inputs: ["question", "context"]
      outputs: ["answer"]
      
    See example configuration files in the configs/ directory.
"""

import logging
import os
import json
import sys
import argparse
import yaml
import importlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import typing as t
from dotenv import load_dotenv

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Load environment variables from .env file
load_dotenv()

from prompt_ops.core.migrator import PromptMigrator
from prompt_ops.core.prompt_strategies import (
    LightOptimizationStrategy, OptimizationError
)
from prompt_ops.core.model_strategies import LlamaStrategy
from prompt_ops.core.metrics import DSPyMetricAdapter, StandardJSONMetric
from prompt_ops.core.datasets import DatasetAdapter, load_dataset
from prompt_ops.core.model import setup_model

# Constants
SEED = 42

# Default adapter class map for convenience
ADAPTER_CLASS_MAP = {
    "standard_json": "prompt_ops.core.datasets.ConfigurableJSONAdapter",
    "rag_json": "prompt_ops.core.datasets.RAGJSONAdapter",
}

# Default metric class map for convenience
METRIC_CLASS_MAP = {
    "similarity": "prompt_ops.core.metrics.DSPyMetricAdapter",
}

# Default strategy class map for convenience
STRATEGY_CLASS_MAP = {
    "light": "prompt_ops.core.prompt_strategies.LightOptimizationStrategy",

}


def resolve_class(class_type_or_path, class_map):
    """
    Resolve a class type to full class path.
    
    Args:
        class_type_or_path: Either a known type (e.g., 'joule', 'dox') 
                            or a full class path
        class_map: Mapping of shorthand names to full class paths
                               
    Returns:
        str: Full class path
    """
    # If it's a known type, use the mapping
    if class_type_or_path.lower() in class_map:
        return class_map[class_type_or_path.lower()]
    
    # Otherwise assume it's already a full class path
    return class_type_or_path


def resolve_adapter_class(adapter_type_or_class):
    """
    Resolve adapter type to full class path.
    
    Args:
        adapter_type_or_class: Either a known adapter type (e.g., 'joule') 
                               or a full class path
                               
    Returns:
        str: Full class path
    """
    return resolve_class(adapter_type_or_class, ADAPTER_CLASS_MAP)


def resolve_metric_class(metric_type_or_class):
    """
    Resolve metric type to full class path.
    
    Args:
        metric_type_or_class: Either a known metric type (e.g., 'similarity') 
                              or a full class path
                               
    Returns:
        str: Full class path
    """
    return resolve_class(metric_type_or_class, METRIC_CLASS_MAP)


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
    dataset_config = config.get("dataset", {})
    adapter_class_path = dataset_config.get("adapter_class")
    dataset_path = dataset_config.get("path")
    
    if not adapter_class_path:
        raise ValueError("Adapter class not specified in configuration")
    
    if not dataset_path:
        raise ValueError("Dataset path not specified in configuration")
    
    # Resolve adapter class path if it's a known type
    adapter_class_path = resolve_adapter_class(adapter_class_path)
    
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
    metric_config = config.get("metric", {})
    
    # Get metric class from config
    metric_class_path = metric_config.get("metric_class")
    
    # If no metric class is specified, use the type to determine the class
    if not metric_class_path:
        metric_type = metric_config.get("type", "similarity")
        if metric_type == "similarity":
            return DSPyMetricAdapter(
                model=model,
                signature_name="similarity"
            )
        elif metric_type == "custom":
            # For backward compatibility with custom metrics
            return DSPyMetricAdapter(
                model=model,
                input_mapping=metric_config.get("input_mapping", {}),
                output_fields=metric_config.get("output_fields", []),
                score_range=tuple(metric_config.get("score_range", (0, 1))),
                normalize_to=tuple(metric_config.get("normalize_to", (0, 1))),
                custom_instructions=metric_config.get("custom_instructions", "")
            )
    else:
        # Resolve metric class path
        metric_class_path = resolve_metric_class(metric_class_path)
        
        # Import the metric class dynamically
        metric_class = load_class_dynamically(metric_class_path)
        
        # Get metric parameters
        metric_params = metric_config.get("params", {})
        
        # Create and return the metric instance
        try:
            return metric_class(**metric_params)
        except Exception as e:
            raise ValueError(f"Failed to create metric instance: {str(e)}")


def check_api_key():
    """Check if the OpenRouter API key is set."""
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        print("Please set it with: export OPENROUTER_API_KEY=your_key_here")
        sys.exit(1)
    print(" OpenRouter API key is set.")


def find_config() -> Optional[str]:
    """Find configuration file in standard locations."""
    config_paths = [
        "./config.yaml",                                # Current directory
        "./configs/default.yaml",                       # Configs subdirectory
        os.path.expanduser("~/.prompt_ops.yaml"),  # User home directory
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            return path
    
    return None


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {str(e)}")
        sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Optimize prompts using configuration from YAML files and command-line arguments"
    )
    
    # Config file option
    parser.add_argument(
        "--config", 
        help="Path to YAML configuration file"
    )
    
    # Model configuration
    parser.add_argument(
        "--model", 
        help="Model name to use for optimization"
    )
    parser.add_argument(
        "--api-base", 
        help="API base URL"
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        help="Model temperature"
    )
    
    # Dataset configuration
    parser.add_argument(
        "--dataset", 
        help="Path to the dataset file"
    )
    parser.add_argument(
        "--adapter-class",
        help="Full import path to dataset adapter class"
    )
    parser.add_argument(
        "--dataset-type",
        choices=list(ADAPTER_CLASS_MAP.keys()),
        help="Type of dataset (shorthand for adapter class)"
    )
    parser.add_argument(
        "--file-format",
        choices=["json", "csv", "yaml"],
        help="Format of the dataset file. If not specified, inferred from file extension."
    )
    parser.add_argument(
        "--train-size", 
        type=float, 
        help="Proportion of data to use for training"
    )
    parser.add_argument(
        "--val-size", 
        type=float, 
        help="Proportion of data to use for validation"
    )
    
    # Prompt configuration
    parser.add_argument(
        "--prompt", 
        help="Base prompt to optimize"
    )
    parser.add_argument(
        "--prompt-file", 
        help="File containing the base prompt to optimize"
    )
    
    # Output configuration
    parser.add_argument(
        "--output-dir", 
        help="Directory to save results"
    )
    parser.add_argument(
        "--output-prefix", 
        help="Prefix for output files"
    )
    
    # Logging configuration
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    # Metric arguments
    parser.add_argument(
        "--metric-class", 
        type=str,
        help="Metric class to use"
    )
    parser.add_argument(
        "--metric-type", 
        type=str,
        choices=["similarity", "dox"],
        help="Type of metric to use (shorthand for metric-class)"
    )
    
    # List available components
    parser.add_argument(
        "--list-adapters",
        action="store_true",
        help="List available dataset adapters and exit"
    )
    parser.add_argument(
        "--list-metrics",
        action="store_true",
        help="List available metrics and exit"
    )
    
    args = parser.parse_args()
    
    # Handle information requests
    if args.list_adapters:
        print("Available dataset adapters:")
        for name, path in sorted(ADAPTER_CLASS_MAP.items()):
            print(f"  {name}: {path}")
        sys.exit(0)
        
    if args.list_metrics:
        print("Available metrics:")
        for name, path in sorted(METRIC_CLASS_MAP.items()):
            print(f"  {name}: {path}")
        sys.exit(0)
    
    return args


def get_merged_config(args) -> Dict[str, Any]:
    """Merge YAML config with command-line arguments."""
    config = {}
    
    # Load from YAML if provided
    if args.config:
        config = load_config(args.config)
    else:
        # Try to find a default config
        default_config = find_config()
        if default_config:
            print(f"Using default configuration from {default_config}")
            config = load_config(default_config)
    
    # Override with command-line arguments if provided
    # Model settings
    if not "model" in config:
        config["model"] = {}
    if args.model:
        config["model"]["name"] = args.model
    if args.api_base:
        config["model"]["api_base"] = args.api_base
    if args.temperature is not None:
        config["model"]["temperature"] = args.temperature
    
    # Dataset settings
    if not "dataset" in config:
        config["dataset"] = {}
    if args.dataset:
        config["dataset"]["path"] = args.dataset
    if args.train_size is not None:
        config["dataset"]["train_size"] = args.train_size
    if args.val_size is not None:
        config["dataset"]["validation_size"] = args.val_size
    if args.file_format:
        config["dataset"]["file_format"] = args.file_format
        
    # Handle adapter class/type
    if args.adapter_class:
        config["dataset"]["adapter_class"] = args.adapter_class
    elif args.dataset_type:
        config["dataset"]["adapter_class"] = resolve_adapter_class(args.dataset_type)
        
    # Handle metric class/type
    if not "metric" in config:
        config["metric"] = {}
    if args.metric_class:
        config["metric"]["metric_class"] = args.metric_class
    elif args.metric_type:
        config["metric"]["metric_class"] = args.metric_type
    
    # Prompt settings
    if not "prompt" in config:
        config["prompt"] = {}
    if args.prompt:
        config["prompt"]["text"] = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            config["prompt"]["text"] = f.read().strip()
    
    # Output settings
    if not "output" in config:
        config["output"] = {}
    if args.output_dir:
        config["output"]["directory"] = args.output_dir
    if args.output_prefix:
        config["output"]["prefix"] = args.output_prefix
    
    # Logging settings
    if not "logging" in config:
        config["logging"] = {}
    if args.log_level:
        config["logging"]["level"] = args.log_level
    
    return config


def main():
    """Run the prompt optimization with configuration."""
    args = parse_arguments()
    config = get_merged_config(args)
    
    print("=== Testing Prompt Migrator with Configuration ===\n")
    
    # Set up logging
    logging_level = getattr(logging, config.get("logging", {}).get("level", "INFO"))
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    check_api_key()

    # Use config values for model setup
    model_config = config.get("model", {})
    model = setup_model(
        model_name=model_config.get("name", "openrouter/meta-llama/llama-3.3-70b-instruct"),
        api_base=model_config.get("api_base", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_tokens=model_config.get("max_tokens", 100000),
        temperature=model_config.get("temperature", 0.0),
        cache=model_config.get("cache", False)
    )
    
    # Create metric based on config
    try:
        metric = get_metric(config, model)
        print(f"Using metric: {metric.__class__.__name__}")
    except ValueError as e:
        print(f"Error creating metric: {str(e)}")
        sys.exit(1)
    
    # Get dataset adapter from config
    try:
        dataset_adapter = get_dataset_adapter(config)
        print(f"Using dataset adapter: {dataset_adapter.__class__.__name__}")
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    # Create strategy based on config
    model_name = model_config.get("name", "").split("/")[-1]
    
    # Check if strategy is specified in config
    strategy_config = config.get("strategy", {})
    strategy_type = strategy_config.get("type")
    
    # If strategy type is specified in config, use it
    if strategy_type:
        if strategy_type.lower() == "llama":
            # Get Llama-specific parameters
            apply_formatting = strategy_config.get("apply_formatting", True)
            apply_templates = strategy_config.get("apply_templates", True)
            template_type = strategy_config.get("template_type", "basic")
            
            strategy = LlamaStrategy(
                model_name=model_name,
                metric=metric,
                task_model=model,
                prompt_model=model,
                apply_formatting=apply_formatting,
                apply_templates=apply_templates,
                template_type=template_type
            )
            print(f"Using LlamaStrategy from config for model: {model_name}")
        elif strategy_type.lower() == "light":
            strategy = LightOptimizationStrategy(
                model_name=model_name,
                metric=metric,
                task_model=model,
                prompt_model=model
            )
            print(f"Using LightOptimizationStrategy from config for model: {model_name}")
        else:
            print(f"Unknown strategy type: {strategy_type}, falling back to auto-detection")
            # Fall back to auto-detection
            if "llama" in model_name.lower():
                strategy = LlamaStrategy(
                    model_name=model_name,
                    metric=metric,
                    task_model=model,
                    prompt_model=model,
                    apply_formatting=True,
                    apply_templates=True
                )
                print(f"Auto-detected LlamaStrategy for model: {model_name}")
            else:
                strategy = LightOptimizationStrategy(
                    model_name=model_name,
                    metric=metric,
                    task_model=model,
                    prompt_model=model
                )
                print(f"Auto-detected LightOptimizationStrategy for model: {model_name}")
    else:
        # Auto-detect based on model name
        if "llama" in model_name.lower():
            strategy = LlamaStrategy(
                model_name=model_name,
                metric=metric,
                task_model=model,
                prompt_model=model,
                apply_formatting=True,
                apply_templates=True
            )
            print(f"Auto-detected LlamaStrategy for model: {model_name}")
        else:
            strategy = LightOptimizationStrategy(
                model_name=model_name,
                metric=metric,
                task_model=model,
                prompt_model=model
            )
            print(f"Auto-detected LightOptimizationStrategy for model: {model_name}")
    
    # Create migrator
    migrator = PromptMigrator(
        strategy=strategy,
        task_model=model,
        prompt_model=model
    )
    
    # Load dataset with configured splits
    dataset_config = config.get("dataset", {})
    trainset, valset, testset = migrator.load_dataset_with_adapter(
        dataset_adapter, 
        train_size=dataset_config.get("train_size", 0.25), 
        validation_size=dataset_config.get("validation_size", 0.25)
    )

    # Get prompt from config
    prompt_config = config.get("prompt", {})
    prompt_text = prompt_config.get("text", "")
    prompt_inputs = prompt_config.get("inputs", ["question", "context"])
    prompt_outputs = prompt_config.get("outputs", ["answer"])

    # Set up output path
    output_config = config.get("output", {})
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_config.get("directory", "results")
    output_prefix = output_config.get("prefix", "joule_light_optimized")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(output_dir, f"{output_prefix}_{timestamp}.json")
    
    # Try to optimize the prompt and save it to a file
    try:
        # Wrap the optimization in a try/except block to catch parallelizer errors
        try:
            light_optimized = migrator.optimize(
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
            
            print("\n=== Summary ===")
            print("Light optimized prompt:")
            print("=" * 80)
            print(light_optimized.signature.instructions)
            print("=" * 80)
        except RuntimeError as re:
            if "cannot schedule new futures after shutdown" in str(re):
                print("\nEncountered a parallelizer shutdown error. This is likely due to a threading issue in DSPy.")
                print("The optimization may have partially completed. Check the output file for results.")
                print(f"Output file: {file_path}")
            else:
                raise
    except OptimizationError as e:
        print(f"\nOptimization failed: {str(e)}")
        print("No optimized prompt was generated.")
    except Exception as e:
        print(f"\nUnexpected error during optimization: {str(e)}")
        print("No optimized prompt was generated.")


if __name__ == "__main__":
    main()
