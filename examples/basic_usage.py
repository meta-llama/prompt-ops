#!/usr/bin/env python
"""
Basic example of using the prompt_ops package.

This example demonstrates how to create a PromptMigrator instance and optimize a prompt.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from prompt_ops.core.migrator import PromptMigrator
from prompt_ops.core.prompt_strategies import LightOptimizationStrategy
from prompt_ops.core.model import setup_model

def main():
    """Run the basic example."""
    # Check for API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please set it with: export OPENROUTER_API_KEY=your_key_here")
        return

    # Set up a model
    model = setup_model(
        model_name="openrouter/meta-llama/llama-3-70b-instruct",
        api_base="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0.0
    )

    # Create a strategy
    strategy = LightOptimizationStrategy(
        model_name="llama-70b",
        task_model=model,
        prompt_model=model
    )

    # Create a migrator
    migrator = PromptMigrator(strategy=strategy)

    # Define a sample prompt
    prompt = {
        "text": "Answer the question based on the context.\n\nContext: {context}\nQuestion: {question}\nAnswer:",
        "inputs": ["context", "question"],
        "outputs": ["answer"]
    }

    print("Original prompt:")
    print(prompt["text"])
    print()

    # Optimize the prompt
    try:
        optimized_prompt = migrator.optimize(prompt)
        print("Optimized prompt:")
        print(optimized_prompt.signature.instructions)
    except Exception as e:
        print(f"Error optimizing prompt: {e}")

if __name__ == "__main__":
    main()
