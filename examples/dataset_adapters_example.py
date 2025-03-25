"""
Example script demonstrating the use of dataset adapters with prompt migrator.

This script shows how to load and process different datasets using the standardized
dataset adapter approach.
"""

import logging
import os
from pathlib import Path

import dspy
from dotenv import load_dotenv

# Import adapters from the new module structure
# Create your own adapters by following the pattern in the README
from prompt_migrator.core.datasets import DatasetAdapter

from prompt_migrator.core.datasets import load_dataset
from prompt_migrator.core.migrator import PromptMigrator
from prompt_migrator.core.prompt_strategies import LightOptimizationStrategy
from prompt_migrator.core.metrics import create_metric


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()


def main():
    """Run the dataset adapters example."""
    # Check if OpenRouter API key is set
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise ValueError(
            "OPENROUTER_API_KEY environment variable not set. "
            "Please set it to run this example."
        )

    # Set up the model
    model = dspy.OpenRouter(
        model="llama-70b",
        api_key=os.environ.get("OPENROUTER_API_KEY")
    )
    
    # Create a metric for evaluation
    metric = create_metric("answer_similarity", model)
    
    # Example 1: Create a custom dataset adapter
    print("\n=== Example 1: Custom Dataset ===")
    
    # Create your own adapter by subclassing DatasetAdapter
    class CustomAdapter(DatasetAdapter):
        def adapt(self):
            # This is where you would transform your dataset
            # For this example, we'll create a simple mock dataset
            return [
                {
                    "inputs": {"question": "What is X?", "context": "X is a variable."},
                    "outputs": {"answer": "X is a variable used in mathematics."}
                },
                {
                    "inputs": {"question": "How does Y work?", "context": "Y works by process Z."},
                    "outputs": {"answer": "Y works through the Z process as described."}
                }
            ]
    
    custom_adapter = CustomAdapter()
    
    # Create migrator with strategy
    custom_migrator = PromptMigrator(
        strategy=LightOptimizationStrategy(
            model_name="llama-70b",
            metric=metric,
            task_model=model,
            prompt_model=model
        ),
        task_model=model,
        prompt_model=model
    )
    
    # Load dataset using adapter
    trainset, valset, testset = custom_migrator.load_dataset_with_adapter(
        custom_adapter, train_size=0.5, validation_size=0.25
    )
    
    print(f"Loaded custom dataset with {len(trainset)} training examples")
    
    # Example of a custom example
    if trainset:
        print("\nExample custom item:")
        example = trainset[0]
        print(f"Question: {example.question}")
        print(f"Context: {example.context}")
        print(f"Answer: {example.answer}")
        print(f"Input keys: {example._input_keys}")
        print(f"Output keys: {example._output_keys}")
    
    # Example 2: Another custom adapter for a different use case
    print("\n=== Example 2: Extraction Dataset ===")
    
    # Create another adapter for a different task
    class ExtractionAdapter(DatasetAdapter):
        def adapt(self):
            # This adapter would transform an extraction dataset
            return [
                {
                    "inputs": {"document": "The company was founded in 2020 by Jane Smith."},
                    "outputs": {"extracted_info": {"founder": "Jane Smith", "year": "2020"}}
                },
                {
                    "inputs": {"document": "Annual revenue reached $5M in Q3 2023."},
                    "outputs": {"extracted_info": {"revenue": "$5M", "period": "Q3 2023"}}
                }
            ]
    
    extraction_adapter = ExtractionAdapter()
    
    # Create migrator with strategy
    extraction_migrator = PromptMigrator(
        strategy=LightOptimizationStrategy(
            model_name="llama-70b",
            metric=metric,
            task_model=model,
            prompt_model=model
        ),
        task_model=model,
        prompt_model=model
    )
    
    # Load dataset using adapter
    trainset, valset, testset = extraction_migrator.load_dataset_with_adapter(
        extraction_adapter, train_size=0.5, validation_size=0.25
    )
    
    print(f"Loaded extraction dataset with {len(trainset)} training examples")
    
    # Example of an extraction example
    if trainset:
        print("\nExample extraction item:")
        example = trainset[0]
        print(f"Document: {example.document}")
        print(f"Extracted Info: {example.extracted_info}")
        print(f"Input keys: {example._input_keys}")
        print(f"Output keys: {example._output_keys}")


if __name__ == "__main__":
    main()
