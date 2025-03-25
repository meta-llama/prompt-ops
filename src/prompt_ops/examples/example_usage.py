"""
Example usage of the prompt migrator package.

This module demonstrates how to use the prompt migrator for
both single prompt optimization and batch processing.
"""

from prompt_ops.core.migrator import PromptMigrator
from prompt_ops.core.prompt_strategies import LightOptimizationStrategy, HeavyOptimizationStrategy
from prompt_ops.core.metrics import ExactMatchMetric, json_evaluation_metric
from prompt_ops.interfaces.csv_utils import batch_optimize_prompts


def optimize_single_prompt():
    """
    Example of optimizing a single prompt.
    """
    # Create a migrator with a light optimization strategy
    strategy = LightOptimizationStrategy(model_name="llama-3")
    migrator = PromptMigrator(strategy=strategy)
    
    # Sample prompt
    prompt = (
        "Generate a comprehensive analysis of the quarterly financial results "
        "for a tech company, including revenue growth, profit margins, and "
        "future outlook. Format the response as a business report."
    )
    
    # Optimize the prompt
    optimized = migrator.optimize({"text": prompt})
    
    # Print results
    print("\nOriginal prompt:")
    print(prompt)
    print("\nOptimized prompt:")
    print(optimized)


def batch_optimize_with_metrics():
    """
    Example of batch optimizing prompts with metrics evaluation.
    """
    # Create a heavy optimization strategy
    strategy = HeavyOptimizationStrategy(model_name="llama-3", use_examples=True)
    
    # Define metrics
    exact_match = ExactMatchMetric(case_sensitive=False, strip_whitespace=True)
    
    # Sample input and output files
    input_file = "example_prompts.csv"
    output_file = "optimized_prompts.csv"
    
    # Create a sample CSV file for demonstration
    create_sample_csv(input_file)
    
    # Run batch optimization
    batch_optimize_prompts(
        input_file_path=input_file,
        output_file_path=output_file,
        strategy=strategy,
        metrics=[exact_match, json_evaluation_metric]
    )
    
    print(f"\nCheck {output_file} for the optimized prompts and evaluation metrics.")


def create_sample_csv(filename):
    """
    Create a sample CSV file with prompts and responses.
    """
    import csv
    
    prompts = [
        {
            "prompt": "Write a function to calculate the Fibonacci sequence.",
            "response": "Here's a function to calculate the Fibonacci sequence:\n\n```python\ndef fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    elif n == 2:\n        return [0, 1]\n    \n    fib = [0, 1]\n    for i in range(2, n):\n        fib.append(fib[i-1] + fib[i-2])\n    \n    return fib\n```"
        },
        {
            "prompt": "Explain the concept of machine learning in simple terms.",
            "response": "Machine learning is like teaching a computer to learn from examples, rather than programming it with specific rules. Imagine teaching a child to recognize cats by showing them many pictures of cats, rather than listing all the features of a cat. Over time, the computer learns patterns from the data and can make predictions or decisions without being explicitly programmed for each scenario."
        },
        {
            "prompt": "Create a JSON object representing a user profile.",
            "response": "{\n  \"user\": {\n    \"id\": 12345,\n    \"name\": \"John Doe\",\n    \"email\": \"john.doe@example.com\",\n    \"age\": 30,\n    \"address\": {\n      \"street\": \"123 Main St\",\n      \"city\": \"San Francisco\",\n      \"state\": \"CA\",\n      \"zip\": \"94105\"\n    },\n    \"preferences\": {\n      \"theme\": \"dark\",\n      \"notifications\": true\n    },\n    \"roles\": [\"user\", \"admin\"]\n  }\n}"
        }
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["prompt", "response"])
        writer.writeheader()
        writer.writerows(prompts)
    
    print(f"Created sample CSV file: {filename}")


def test_basic_functionality():
    """
    A simple test to verify that the prompt migrator is working correctly.
    This test doesn't require DSPy and uses only the basic functionality.
    """
    print("\n=== Testing Basic Functionality ===")
    
    # Create strategies with different configurations
    light_strategy = LightOptimizationStrategy(model_name="llama-3")
    heavy_strategy = HeavyOptimizationStrategy(model_name="llama-3", use_examples=True)
    
    # Create migrators
    light_migrator = PromptMigrator(strategy=light_strategy)
    heavy_migrator = PromptMigrator(strategy=heavy_strategy)
    
    # Sample prompt
    prompt = (
        "You are a helpful AI assistant. Answer the following question: \n"
        "What is the capital of France?"
    )
    
    # Optimize with different strategies
    light_optimized = light_migrator.optimize({"text": prompt})
    heavy_optimized = heavy_migrator.optimize({"text": prompt})
    
    # Print results
    print("\nOriginal prompt:")
    print(prompt)
    print("\nLight optimized prompt:")
    print(light_optimized)
    print("\nHeavy optimized prompt:")
    print(heavy_optimized)
    
    # Verify that the optimization worked
    if light_optimized != prompt and heavy_optimized != prompt:
        print("\nBasic functionality test passed! The strategies are modifying the prompts.")
    else:
        print("\nBasic functionality test failed! The strategies are not modifying the prompts.")
    
    return light_optimized, heavy_optimized


def test_dspy_integration(use_real_models=False):
    """
    Test the DSPy integration for prompt optimization.
    This test requires DSPy to be installed.
    
    Args:
        use_real_models (bool): If True, use real OpenRouter models. Requires OPENROUTER_API_KEY env var.
    """
    try:
        try:
            import dspy
            import os
            print("\n=== Testing DSPy Integration ===")
        except ImportError:
            print("\n=== Skipping DSPy Integration Test ===")
            print("DSPy is not installed. To test DSPy integration, install DSPy with:")
            print("pip install dspy-ai")
            return None
        
        class GeographyExample:
            """
            Example for geography questions.
            """
            def __init__(self, question, answer):
                self.question = question
                self.answer = answer
                
            # Add a to_dict method for compatibility
            def to_dict(self):
                return {"question": self.question, "answer": self.answer}
        
        dataset = [
            GeographyExample("What is the capital of France?", "Paris"),
            GeographyExample("What is the capital of Japan?", "Tokyo"),
            GeographyExample("What is the capital of Italy?", "Rome"),
            GeographyExample("What is the capital of Germany?", "Berlin"),
            GeographyExample("What is the capital of Spain?", "Madrid"),
            GeographyExample("What is the capital of Australia?", "Canberra")
        ]
        
        # Split the dataset
        trainset = dataset[:4]  # Use more examples for training
        valset = dataset[4:]   # Keep some for validation
        
        # Define a proper metric function
        def geography_metric(gold, pred, trace=False):
            """
            Metric for evaluating geography question answering.
            """
            if hasattr(gold, 'answer') and hasattr(pred, 'answer'):
                if trace:
                    print(f"Gold: {gold.answer}, Pred: {pred.answer}")
                return 1.0 if gold.answer.lower() == pred.answer.lower() else 0.0
            return 0.0  # Default score if attributes are missing
        
        # Configure language models
        if use_real_models and os.getenv("OPENROUTER_API_KEY"):
            print("Using OpenRouter models for testing...")
            
            # OpenRouter model configuration
            openrouter_settings = {
                "model": "openrouter/openai/gpt-4o",
                "api_base": "https://openrouter.ai/api/v1",
                "api_key": os.getenv("OPENROUTER_API_KEY"),
            }
            
            task_model = dspy.OpenAI(
                model=openrouter_settings["model"],
                api_base=openrouter_settings["api_base"],
                api_key=openrouter_settings["api_key"],
                max_tokens=1000,
                temperature=0.0,
                cache=True  # Enable caching to avoid repeated API calls
            )
            
            prompt_model = task_model
            
            dspy.configure(lm=task_model)
            
            print(f"Using OpenRouter model: {openrouter_settings['model']}")
        else:
            if not use_real_models:
                print("Using mock models for testing (use_real_models=False)...")
            elif not os.getenv("OPENROUTER_API_KEY"):
                print("OPENROUTER_API_KEY environment variable not set. Using mock models...")
                print("To use real models, set the OPENROUTER_API_KEY environment variable:")
                print("export OPENROUTER_API_KEY=your_key_here")
            
            # Create a custom mock LM class for testing
            class CustomMockLM:
                def __init__(self):
                    self.model_name = "custom-mock-model"
                
                def __call__(self, prompt, **kwargs):
                    # Simple mock response
                    return "This is a mock response from the custom LM."
                
                # Add required methods for DSPy compatibility
                def basic_request(self, prompt, **kwargs):
                    return {"response": self.__call__(prompt)}
            
            # Use our custom mock models when real models aren't available
            task_model = CustomMockLM()
            prompt_model = CustomMockLM()
            
            # Configure DSPy to use the mock model
            try:
                dspy.configure(lm=task_model)
            except Exception as e:
                print(f"Warning: Could not configure DSPy with mock model: {str(e)}")
        
        # Create a strategy with appropriate configuration
        strategy = LightOptimizationStrategy(
            model_name="gpt-4o" if use_real_models else "mock-model",
            num_threads=2,  # More threads for real optimization
            max_labeled_demos=3,
            metric=geography_metric
        )
        
        # Create a migrator with the strategy and dataset
        migrator = PromptMigrator(
            strategy=strategy,
            metrics=[geography_metric],
            task_model=task_model,
            prompt_model=prompt_model,
            trainset=trainset,
            valset=valset
        )
        
        # Sample prompt to optimize
        prompt = (
            "You are a helpful AI assistant. Answer the following question about geography: \n"
            "What is the capital of Canada?"
        )
        
        # Optimize the prompt
        print("\nOptimizing prompt with DSPy integration...")
        optimized = migrator.optimize({
            "text": prompt, 
            "inputs": ["question"], 
            "outputs": ["answer"]
        })
        
        # Print results
        print("\nOriginal prompt:")
        print(prompt)
        print("\nOptimized prompt:")
        print(optimized)
        
        # Check if optimization worked
        if optimized != prompt:
            if use_real_models and "[Optimized for gpt-4o]" not in optimized:
                print("\n✅ Full DSPy integration test passed! The prompt was optimized using DSPy.")
            else:
                print("\n✅ Basic DSPy integration test passed!")
                if not use_real_models:
                    print("Note: This test used mock models. For full optimization, run with use_real_models=True")
        else:
            print("\n❌ DSPy integration test failed! The prompt was not modified.")
            
        return optimized
        
    except Exception as e:
        print(f"\n⚠️ DSPy integration test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def setup_openrouter_api_key():
    """
    Helper function to set up the OpenRouter API key.
    Returns True if the key was set up successfully, False otherwise.
    """
    import os
    
    # Check if the API key is already set
    if os.getenv("OPENROUTER_API_KEY"):
        print("OpenRouter API key is already set.")
        return True
    
    # Ask the user for their API key
    print("\nTo use real models, you need to set up your OpenRouter API key.")
    print("You can get an API key from https://openrouter.ai/keys")
    api_key = input("Enter your OpenRouter API key (press Enter to skip): ").strip()
    
    if not api_key:
        print("Skipping real model testing.")
        return False
    
    # Set the API key in the environment
    os.environ["OPENROUTER_API_KEY"] = api_key
    print("OpenRouter API key set successfully!")
    return True


def main():
    """
    Main function to run the examples.
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the prompt migrator package.")
    parser.add_argument("--real-models", action="store_true", help="Use real models for testing (requires OpenRouter API key)")
    parser.add_argument("--skip-basic", action="store_true", help="Skip basic functionality tests")
    parser.add_argument("--skip-batch", action="store_true", help="Skip batch processing tests")
    args = parser.parse_args()
    
    # Set up API key if using real models
    use_real_models = False
    if args.real_models:
        use_real_models = setup_openrouter_api_key()
    
    # Run the tests
    if not args.skip_basic:
        print("=== Example 1: Testing Basic Functionality ===")
        test_basic_functionality()
    
    print("\n=== Example 2: Testing DSPy Integration ===")
    test_dspy_integration(use_real_models=use_real_models)
    
    if not args.skip_basic:
        print("\n=== Example 3: Optimizing a Single Prompt ===")
        optimize_single_prompt()
    
    if not args.skip_batch:
        print("\n=== Example 4: Batch Optimizing Prompts with Metrics ===")
        batch_optimize_with_metrics()


if __name__ == "__main__":
    main()
