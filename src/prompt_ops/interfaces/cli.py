"""
Command-line interface for the prompt migrator.

This module provides a CLI for using the prompt migrator functionality,
including commands for optimizing individual prompts and batch processing.
"""

import importlib
import sys
from pathlib import Path
from typing import List, Optional

import click

from ..core.prompt_strategies import BaseStrategy, LightOptimizationStrategy
from ..interfaces.csv_utils import batch_optimize_prompts


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


@cli.command(name="batch-optimize")
@click.option(
    "--input-file",
    required=True,
    help="Path to the input CSV containing prompts"
)
@click.option(
    "--output-file",
    default=None,
    help="Path where the output CSV will be saved (defaults to input-file-optimized.csv)"
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
@click.option(
    "--prompt-column",
    default="prompt",
    show_default=True,
    help="Name of the column containing prompts"
)
@click.option(
    "--response-column",
    default="response",
    show_default=True,
    help="Name of the column containing responses (for evaluation)"
)
@click.option(
    "--metric-paths",
    multiple=True,
    help="Paths to custom metric functions (format: module.submodule:function_name)"
)
def batch_optimize(
    input_file: str,
    output_file: Optional[str],
    strategy: str,
    model: str,
    prompt_column: str,
    response_column: str,
    metric_paths: List[str]
):
    """
    Optimize prompts from a CSV file and save the results.
    """
    # Generate default output file if not provided
    if output_file is None:
        input_path = Path(input_file)
        stem = input_path.stem
        output_file = str(input_path.with_name(f"{stem}-optimized{input_path.suffix}"))
    
    # Map strategy name to class
    strategy_map = {
        "base": BaseStrategy,
        "light": LightOptimizationStrategy,
    }
    
    # Create strategy instance
    strategy_class = strategy_map[strategy.lower()]
    strategy_instance = strategy_class(model_name=model)
    
    # Load custom metrics if provided
    metrics = []
    for metric_path in metric_paths:
        try:
            module_path, function_name = metric_path.split(":")
            module = importlib.import_module(module_path)
            metric_func = getattr(module, function_name)
            metrics.append(metric_func)
        except (ValueError, ImportError, AttributeError) as e:
            click.echo(f"Error loading metric {metric_path}: {e}", err=True)
            sys.exit(1)
    
    # Run batch optimization
    try:
        batch_optimize_prompts(
            input_file_path=input_file,
            output_file_path=output_file,
            strategy=strategy_instance,
            metrics=metrics if metrics else None,
            prompt_column=prompt_column,
            response_column=response_column
        )
        
        click.echo(f"Successfully optimized prompts from '{input_file}' and saved to '{output_file}'")
    except Exception as e:
        click.echo(f"Error during batch optimization: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
