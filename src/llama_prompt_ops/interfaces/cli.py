# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Command-line interface for the llama-prompt-ops tool.

This module provides a CLI for using the prompt-ops functionality,
including commands for optimizing individual prompts, batch processing,
and optimization using YAML configuration files.
"""

import importlib
import importlib.util
import os
import sys
import yaml
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import click
from dotenv import load_dotenv

# Import template utilities
from llama_prompt_ops.templates import get_template_path, get_template_content

# Helper function for real-time output
def echo_flush(message, err=False):
    """Echo a message and flush the output buffer for real-time display."""
    click.echo(message, err=err)
    if err:
        sys.stderr.flush()
    else:
        sys.stdout.flush()

from llama_prompt_ops.core.prompt_strategies import BaseStrategy, BasicOptimizationStrategy, OptimizationError
from llama_prompt_ops.core.model_strategies import LlamaStrategy
from llama_prompt_ops.core.migrator import PromptMigrator
from llama_prompt_ops.core.model import setup_model
from llama_prompt_ops.core.metrics import DSPyMetricAdapter, StandardJSONMetric, MetricBase
from llama_prompt_ops.core.datasets import DatasetAdapter, load_dataset


@click.group()
def cli():
    """
    llama-prompt-ops - A tool for migrating and optimizing prompts for Llama models.
    """
    pass


@cli.command(name="create")
@click.argument(
    "project_name",
    required=True,
    type=str
)
@click.option(
    "--output-dir",
    default=".",
    help="Directory where the project will be created"
)
@click.option(
    "--model",
    default="openrouter/meta-llama/llama-3.3-70b-instruct",
    help="Model to use for prompt optimization"
)
@click.option(
    "--api-key-env",
    default="OPENROUTER_API_KEY",
    help="Name of the environment variable for the API key"
)
def create(project_name, output_dir, model, api_key_env):
    """Create a new prompt optimization project with all necessary files."""
    project_dir = os.path.join(output_dir, project_name)
    
    try:
        # Check if directory already exists
        if os.path.exists(project_dir):
            raise ValueError(f"Directory '{project_name}' already exists. Please choose a different name.")
        
        total_steps = 6
        
        # Step 1: Create project directory and subdirectories
        echo_flush(f"[1/{total_steps}] Creating project structure...")
        os.makedirs(project_dir)
        echo_flush(f"✓ Created project directory: {project_name}")
        
        os.makedirs(os.path.join(project_dir, "data"))
        echo_flush(f"✓ Created data directory")
        
        os.makedirs(os.path.join(project_dir, "prompts"))
        echo_flush(f"✓ Created prompts directory")
        
        # Step 2: Create config file
        echo_flush(f"\n[2/{total_steps}] Generating configuration file...")
        config = {
            "system_prompt": {
                "file": "prompts/prompt.txt",
                "inputs": ["question"],
                "outputs": ["answer"]
            },
            "dataset": {
                "path": "data/dataset.json",
                "input_field": ["fields", "input"],
                "golden_output_field": "answer"
            },
            "model": {
                "task_model": model,
                "proposer_model": model
            },
            "metric": {
                "class": "llama_prompt_ops.core.metrics.FacilityMetric",
                "strict_json": False,
                "output_field": "answer"
            },
            "optimization": {
                "strategy": "llama"
            }
        }
        
        with open(os.path.join(project_dir, "config.yaml"), "w") as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
        echo_flush(f"✓ Created config.yaml")
        
        # Step 3: Create prompt file
        echo_flush(f"\n[3/{total_steps}] Creating prompt template...")
        # Use the bundled template file
        prompt_text = get_template_content("sample_prompt.txt")
        
        with open(os.path.join(project_dir, "prompts", "prompt.txt"), "w") as f:
            f.write(prompt_text)
        echo_flush(f"✓ Created prompt.txt")
        
        # Step 4: Create sample dataset file
        echo_flush(f"\n[4/{total_steps}] Generating sample dataset...")
        # Use the helper function to get the sample dataset
        from llama_prompt_ops.templates import get_sample_dataset
        sample_data = get_sample_dataset()
        
        with open(os.path.join(project_dir, "data", "dataset.json"), "w") as f:
            json.dump(sample_data, f, indent=2)
        echo_flush(f"✓ Created dataset.json with {len(sample_data)} examples")
        
        # Step 5: Create .env file
        echo_flush(f"\n[5/{total_steps}] Setting up environment...")
        env_content = f"# API Keys\n{api_key_env}=your_api_key_here\n"
        
        with open(os.path.join(project_dir, ".env"), "w") as f:
            f.write(env_content)
        echo_flush(f"✓ Created .env file")
        
        # Step 6: Create README.md file
        echo_flush(f"\n[6/{total_steps}] Creating documentation...")
        readme_content = f"""# {project_name}

A prompt optimization project created with llama-prompt-ops.

## Getting Started

1. Set your API key in the `.env` file:
   ```
   {api_key_env}=your_api_key_here
   ```

2. Run the optimization:
   ```bash
   cd {project_name}
   llama-prompt-ops migrate
   ```

## Project Structure

- `config.yaml`: Configuration file for the project
- `prompts/prompt.txt`: The prompt template to optimize
- `data/dataset.json`: Sample dataset for training and evaluation
- `.env`: Environment variables including API keys
"""
        
        with open(os.path.join(project_dir, "README.md"), "w") as f:
            f.write(readme_content)
        echo_flush(f"✓ Created README.md")
        
        # Final summary
        echo_flush(f"\n✨ Done! Project '{project_name}' created successfully!")
        echo_flush("\nTo get started:")
        echo_flush(f"1. cd {project_name}")
        echo_flush(f"2. Edit the .env file to add your {api_key_env}")
        echo_flush(f"   You can get an API key at: https://openrouter.ai/")
        echo_flush("3. Run: llama-prompt-ops migrate")
        
    except Exception as e:
        echo_flush(f"Error creating project: {str(e)}", err=True)
        # Clean up if something went wrong
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        sys.exit(1)


# Helper functions for optimize-with-config command
def resolve_class(class_type_or_path, class_map):
    """
    Resolve a class type to full class path or file path.
    
    Args:
        class_type_or_path: Either a known type, a full class path, or a file path
        class_map: Mapping of shorthand names to full class paths
                               
    Returns:
        str: Full class path or file path
    """
    # If it's a known type, use the mapping
    if class_type_or_path.lower() in class_map:
        return class_map[class_type_or_path.lower()]
    
    # If it's a file path, make sure it's absolute
    if class_type_or_path.endswith('.py') and not os.path.isabs(class_type_or_path):
        # Convert to absolute path
        return os.path.abspath(class_type_or_path)
    
    # Otherwise assume it's already a full class path or absolute file path
    return class_type_or_path


def load_class_dynamically(class_path):
    """
    Dynamically import and return a class from its path.
    
    Args:
        class_path: Either a full import path to the class (e.g., 'module.submodule.ClassName')
                   or a file path (e.g., '/path/to/file.py') that contains a suitable class
        
    Returns:
        The class object
        
    Raises:
        ValueError: If the class cannot be imported or detected
    """
    # Check if this is a file path (ends with .py)
    if class_path.endswith('.py'):
        file_path = class_path
        
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
            
        # Get the module name from the file path
        module_name = os.path.basename(file_path)
        if module_name.endswith('.py'):
            module_name = module_name[:-3]
            
        # Add the directory to sys.path temporarily
        dir_path = os.path.dirname(os.path.abspath(file_path))
        original_sys_path = sys.path.copy()
        sys.path.insert(0, dir_path)
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all classes in the module that inherit from our base classes
            candidates = []
            for name, obj in vars(module).items():
                if not isinstance(obj, type): 
                    continue
                    
                # Check if it's a subclass of one of our base classes
                if (issubclass(obj, DatasetAdapter) and obj != DatasetAdapter) or \
                   (issubclass(obj, MetricBase) and obj != MetricBase):
                    candidates.append((name, obj))
            
            # If we found exactly one candidate, use it
            if len(candidates) == 1:
                return candidates[0][1]
            elif len(candidates) > 1:
                # If multiple candidates, prefer ones with names that match the file
                file_base_name = module_name.replace('_', '').lower()
                for name, cls in candidates:
                    if file_base_name in name.lower():
                        return cls
                
                # If still ambiguous, raise an error with suggestions
                class_list = ', '.join(name for name, _ in candidates)
                raise ValueError(f"Multiple candidate classes found in {file_path}. "
                               f"Please specify one using a full import path. "
                               f"Available classes: {class_list}")
            else:
                raise ValueError(f"No suitable classes found in {file_path}. "
                               f"The file should contain a class that inherits from "
                               f"DatasetAdapter or MetricBase.")
        finally:
            # Restore the original sys.path
            sys.path = original_sys_path
    else:
        # import paths implementation
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
        "standard_json": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "rag_json": "llama_prompt_ops.core.datasets.RAGJSONAdapter",
    }
    
    dataset_config = config.get("dataset", {})
    adapter_class_path = dataset_config.get("adapter_class", "standard_json")
    dataset_path = dataset_config.get("path")
    
    if not dataset_path:
        raise ValueError("Dataset path not specified in configuration")
    
    # Resolve adapter class path if it's a known type
    adapter_class_path = resolve_class(adapter_class_path, ADAPTER_CLASS_MAP)
    
    # Import the class dynamically
    adapter_class = load_class_dynamically(adapter_class_path)
    
    # Get file format if specified
    file_format = dataset_config.get("file_format")
    
    # Extract all parameters except known non-parameter keys
    adapter_params = {k: v for k, v in dataset_config.items() 
                     if k not in ["adapter_class", "path", "file_format", 
                                  "train_size", "validation_size", "seed", "shuffle"]}
    
    # Create and return the adapter instance
    return adapter_class(dataset_path=dataset_path, file_format=file_format, **adapter_params)


def get_dataset_adapter_from_config(config_dict, config_path):
    """
    Create a dataset adapter from configuration, handling relative paths.
    
    Args:
        config_dict: The full configuration dictionary
        config_path: Path to the configuration file (used for resolving relative paths)
        
    Returns:
        A configured dataset adapter instance
    """
    # Handle relative dataset paths
    dataset_config = config_dict.get("dataset", {})
    if "path" in dataset_config and not os.path.isabs(dataset_config["path"]):
        # Make dataset path relative to the config file location
        config_dir = os.path.dirname(os.path.abspath(config_path))
        dataset_config["path"] = os.path.join(config_dir, dataset_config["path"])
        click.echo(f"Resolved relative dataset path to: {dataset_config['path']}")
    
    # Get the adapter using the existing helper function
    return get_dataset_adapter(config_dict)


def get_models_from_config(config_dict, override_model_name=None, api_key=None):
    """
    Create model adapter instances from configuration.
    
    Args:
        config_dict: The full configuration dictionary
        override_model_name: Optional model name to override the ones in config
        api_key: API key to use for the models
        
    Returns:
        A tuple of (task_model, proposer_model) adapter instances
    """
    model_config = config_dict.get("model", {})
    adapter_type = model_config.get("adapter_type", "dspy")
    api_base = model_config.get("api_base", "https://openrouter.ai/api/v1")
    max_tokens = model_config.get("max_tokens", 2048)
    temperature = model_config.get("temperature", 0.0)
    cache = model_config.get("cache", False)
    
    # If override_model_name is provided, use it for both models
    if override_model_name:
        task_model_name = proposer_model_name = override_model_name
    else:
        # Check for task_model and proposer_model in config
        # Fall back to 'name' if either is not specified
        default_model = model_config.get("name", "openrouter/meta-llama/llama-3.3-70b-instruct")
        task_model_name = model_config.get("task_model", default_model)
        proposer_model_name = model_config.get("proposer_model", default_model)
    
    # Create task model
    task_model = setup_model(
        model_name=task_model_name,
        adapter_type=adapter_type,
        api_base=api_base,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        cache=cache
    )
    
    # If task and proposer models are the same, reuse the instance
    if task_model_name == proposer_model_name:
        click.echo(f"Using the same model for task and proposer: {task_model_name}")
        proposer_model = task_model
    else:
        click.echo(f"Using different models - Task: {task_model_name}, Proposer: {proposer_model_name}")
        proposer_model = setup_model(
            model_name=proposer_model_name,
            adapter_type=adapter_type,
            api_base=api_base,
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
            cache=cache
        )
    
    return task_model, proposer_model


def get_model_from_config(config_dict, override_model_name=None, api_key=None):
    """
    Create a model adapter instance from configuration (legacy function).
    
    Args:
        config_dict: The full configuration dictionary
        override_model_name: Optional model name to override the one in config
        api_key: API key to use for the model
        
    Returns:
        A configured model adapter instance
    """
    model_config = config_dict.get("model", {})
    adapter_type = model_config.get("adapter_type", "dspy")
    
    return setup_model(
        model_name=override_model_name if override_model_name else model_config.get("name", "openrouter/meta-llama/llama-3.3-70b-instruct"),
        adapter_type=adapter_type,
        api_base=model_config.get("api_base", "https://openrouter.ai/api/v1"),
        api_key=api_key,
        max_tokens=model_config.get("max_tokens", 2048),
        temperature=model_config.get("temperature", 0.0),
        cache=model_config.get("cache", False)
    )


def get_strategy(strategy_config, model_name_with_path, metric, task_model, prompt_model):
    """
    Create a prompt optimization strategy based on configuration.
    
    Args:
        strategy_config: Strategy configuration dictionary
        model_name_with_path: Full model name including provider path
        metric: Metric instance to use for optimization
        task_model: Model adapter instance for task execution
        prompt_model: Model adapter instance for prompt optimization
        
    Returns:
        A strategy instance appropriate for the model and configuration
    """
    # Extract just the model name without provider path
    model_name = model_name_with_path.split("/")[-1]
    
    # Check if strategy is specified in config
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
                task_model=task_model,
                prompt_model=prompt_model,
                apply_formatting=apply_formatting,
                apply_templates=apply_templates,
                template_type=template_type
            )
            click.echo(f"Using LlamaStrategy from config for model: {model_name}")
            return strategy
            
        elif strategy_type.lower() == "basic":
            strategy = BasicOptimizationStrategy(
                model_name=model_name,
                metric=metric,
                task_model=task_model,
                prompt_model=prompt_model
            )
            click.echo(f"Using BasicOptimizationStrategy from config for model: {model_name}")
            return strategy
            
        else:
            click.echo(f"Unknown strategy type: {strategy_type}, falling back to auto-detection")
            # Fall through to auto-detection
    
    # Auto-detect based on model name
    if "llama" in model_name.lower():
        strategy = LlamaStrategy(
            model_name=model_name,
            metric=metric,
            task_model=task_model,
            prompt_model=prompt_model,
            apply_formatting=True,
            apply_templates=True
        )
        click.echo(f"Auto-detected LlamaStrategy for model: {model_name}")
    else:
        strategy = BasicOptimizationStrategy(
            model_name=model_name,
            metric=metric,
            task_model=task_model,
            prompt_model=prompt_model
        )
        click.echo(f"Auto-detected BasicOptimizationStrategy for model: {model_name}")
    
    return strategy


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
        "similarity": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
        "standard_json": "llama_prompt_ops.core.metrics.StandardJSONMetric",
    }
    
    metric_config = config.get("metric", {})
    
    # Get metric class from config - check both 'class' and 'metric_class' for compatibility
    metric_class_path = metric_config.get("class")
    
    # If no metric class is specified, use the type to determine the class
    if not metric_class_path:
        metric_type = metric_config.get("type", "similarity")
        if metric_type == "similarity":
            click.echo("Using similarity metric")
            return DSPyMetricAdapter(
                model=model,
                signature_name="similarity"
            )
        elif metric_type == "custom":
            # For backward compatibility with custom metrics
            click.echo("Using custom metric configuration")
            return DSPyMetricAdapter(
                model=model,
                input_mapping=metric_config.get("input_mapping", {}),
                output_fields=metric_config.get("output_fields", []),
                score_range=tuple(metric_config.get("score_range", (0, 1))),
                normalize_to=tuple(metric_config.get("normalize_to", (0, 1))),
                custom_instructions=metric_config.get("custom_instructions", "")
            )
        elif metric_type.lower() in METRIC_CLASS_MAP:
            # If type is a known shorthand (like 'standard_json'), resolve it
            metric_class_path = metric_type
    
    # If we have a class path at this point, resolve and instantiate it
    if metric_class_path:
        # Resolve metric class path if it's a known type
        metric_class_path = resolve_class(metric_class_path, METRIC_CLASS_MAP)
        
        try:
            # Import the metric class dynamically
            metric_class = load_class_dynamically(metric_class_path)
            
            # Extract all parameters except known non-parameter keys
            metric_params = {k: v for k, v in metric_config.items() 
                            if k not in ["metric_class", "type", "class"]}
            
            # Create and return the metric instance
            if metric_class == DSPyMetricAdapter:
                # DSPyMetricAdapter requires the model parameter
                return metric_class(model=model, **metric_params)
            else:
                return metric_class(**metric_params)
        except Exception as e:
            raise ValueError(f"Failed to create metric instance: {str(e)}")
    
    # If we get here, we couldn't determine the metric type
    raise ValueError(f"Could not determine metric type from config: {metric_config}")


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
    default="config.yaml",
    help="Path to the YAML configuration file (defaults to config.yaml)"
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
    "--save-yaml/--no-save-yaml",
    default=True,
    help="Whether to save results in YAML format in addition to JSON"
)
@click.option(
    "--api-key-env",
    default="OPENROUTER_API_KEY",
    help="Environment variable name for the API key"
)
@click.option(
    "--dotenv-path",
    default=".env",
    help="Path to the .env file containing API keys"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="INFO",
    help="Set the logging level")
def migrate(config, model, output_dir, save_yaml, api_key_env, dotenv_path, log_level):
    """
    Migrate and optimize prompts using a YAML configuration file.
    
    This command loads a configuration file that specifies the model,
    dataset, prompt, metric, and optimization strategy to use.
    
    Example:
        prompt-ops migrate --config configs/facility.yaml
    """
    # Set up logging
    numeric_level = getattr(logging, log_level.upper())
    logging.basicConfig(level=numeric_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Load environment variables from .env file if it exists
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        click.echo(f"Loaded environment variables from {dotenv_path}")
    
    # Check if API key is set
    api_key = os.getenv(api_key_env)
    if not api_key:
        click.echo(f"Error: {api_key_env} environment variable not set", err=True)
        click.echo(f"Please set it with: export {api_key_env}=your_key_here or add it to your .env file", err=True)
        sys.exit(1)
    
    # Load configuration
    try:
        config_dict = load_config(config)
        click.echo(f"Loaded configuration from {config}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    
    # Set up models from config
    task_model, prompt_model = get_models_from_config(config_dict, model, api_key)
    
    # Create metric based on config - use task_model for metric
    try:
        metric = get_metric(config_dict, task_model)
        click.echo(f"Using metric: {metric.__class__.__name__}")
    except ValueError as e:
        click.echo(f"Error creating metric: {str(e)}", err=True)
        sys.exit(1)
    
    # Get dataset adapter from config
    try:
        dataset_adapter = get_dataset_adapter_from_config(config_dict, config)
        click.echo(f"Using dataset adapter: {dataset_adapter.__class__.__name__}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    
    # Create strategy based on config
    strategy = get_strategy(
        config_dict.get("strategy", {}),
        config_dict.get("model", {}).get("name", ""),
        metric,
        task_model,
        prompt_model
    )
    
    # Create migrator
    migrator = PromptMigrator(
        strategy=strategy,
        task_model=task_model,
        prompt_model=prompt_model
    )
    
    # Load dataset with configured splits
    dataset_config = config_dict.get("dataset", {})
    trainset, valset, testset = migrator.load_dataset_with_adapter(
        dataset_adapter, 
        train_size=dataset_config.get("train_size", 0.25), 
        validation_size=dataset_config.get("validation_size", 0.25)
    )
    
    # Get prompt from config (support both 'system_prompt' and legacy 'prompt' keys)
    prompt_config = config_dict.get("system_prompt", config_dict.get("prompt", {}))
    prompt_file = prompt_config.get("file", None)
    prompt_text = prompt_config.get("text", "")
    
    # Load prompt text from file if specified and text is not provided
    if prompt_file and not prompt_text:
        # Handle relative paths - relative to the config file location
        config_dir = os.path.dirname(os.path.abspath(config))
        if not os.path.isabs(prompt_file):
            prompt_file = os.path.join(config_dir, prompt_file)
            
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r') as f:
                    prompt_text = f.read()
                click.echo(f"Loaded prompt from file: {prompt_file}")
            except Exception as e:
                click.echo(f"Error loading prompt file: {str(e)}", err=True)
                sys.exit(1)
        else:
            click.echo(f"Warning: Prompt file not found: {prompt_file}", err=True)
            click.echo("Using empty prompt text instead.")
    
    prompt_inputs = prompt_config.get("inputs", ["question", "context"])
    prompt_outputs = prompt_config.get("outputs", ["answer"])
    
    # Log which config key was used
    if "system_prompt" in config_dict:
        click.echo("Using 'system_prompt' from config")
    elif "prompt" in config_dict:
        click.echo("Using legacy 'prompt' key from config")
    
    # Set up output path
    output_config = config_dict.get("output", {})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Handle relative output directory path - relative to current working directory
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)
    
    # Use the specified prefix from config, or fall back to the config file name
    if "prefix" in output_config:
        output_prefix = output_config.get("prefix")
        click.echo(f"Using output prefix from config: {output_prefix}")
    else:
        output_prefix = Path(config).stem
        click.echo(f"Using config filename as output prefix: {output_prefix}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    json_file_path = os.path.join(output_dir, f"{output_prefix}_{timestamp}.json")
    yaml_file_path = os.path.join(output_dir, f"{output_prefix}_{timestamp}.yaml")
    
    # Try to optimize the prompt and save it to a file
    try:
        # Wrap the optimization in a try/except block to catch parallelizer errors
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
                file_path=json_file_path
            )
                        
            click.echo("\n=== Optimization Complete ===")
            click.echo(f"Results saved to: {json_file_path}")
            if save_yaml:
                click.echo(f"Results also saved to: {yaml_file_path}")
            click.echo("\nOptimized prompt:")
            click.echo("=" * 80)
            click.echo(optimized.signature.instructions)
            click.echo("=" * 80)
        except RuntimeError as re:
            if "cannot schedule new futures after shutdown" in str(re):
                click.echo("\nEncountered a parallelizer shutdown error. This is likely due to a threading issue in DSPy.")
                click.echo("The optimization may have partially completed. Check the output files for results.")
                click.echo(f"JSON output file: {json_file_path}")
                if save_yaml:
                    click.echo(f"YAML output file: {yaml_file_path}")
            else:
                raise
    except OptimizationError as e:
        click.echo(f"\nOptimization failed: {str(e)}", err=True)
        click.echo("No optimized prompt was generated.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nUnexpected error during optimization: {str(e)}", err=True)
        click.echo("No optimized prompt was generated.")
        sys.exit(1)


if __name__ == "__main__":
    cli()
