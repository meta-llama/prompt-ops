#!/usr/bin/env python
"""
Example script demonstrating Llama-specific prompt optimization.

This script shows how to use the Llama-specific optimization features
in the prompt-migrator framework, including:
1. Using Llama-optimized PromptMigrator
2. Using the LlamaStrategy
3. Applying Llama-specific tips and templates
"""

import os
import sys
import logging
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_migrator.core.migrator import PromptMigrator
from prompt_migrator.core.model_strategies import (
    ModelSpecificStrategy,
    LlamaStrategy,
    GPTStrategy,
    ClaudeStrategy,
    get_strategy_for_model
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def optimize_for_llama_model():
    """Demonstrate optimizing a prompt specifically for Llama models."""
    
    # Sample prompt data
    prompt_data = {
        "text": "Extract key information from the following document. Include the title, author, date, and main points.",
        "inputs": ["document"],
        "outputs": ["key_information"],
        "input_fields": ["document"],
        "output_fields": ["key_information", "extracted_information"],
        "examples": [
            {
                "input": "Document: The Impact of Climate Change on Global Agriculture (2023) by Dr. Jane Smith. Climate change is affecting agricultural production worldwide. Rising temperatures are altering growing seasons. Extreme weather events are damaging crops. Farmers are adapting by using drought-resistant varieties and improved irrigation.",
                "output": "Title: The Impact of Climate Change on Global Agriculture\nAuthor: Dr. Jane Smith\nDate: 2023\nMain Points:\n- Climate change affects agricultural production worldwide\n- Rising temperatures alter growing seasons\n- Extreme weather damages crops\n- Farmers adapt using drought-resistant varieties and improved irrigation"
            }
        ]
    }
    
    print(f"\n{'='*80}\nOptimizing for LLAMA models\n{'='*80}")
    
    # Create a Llama-specific strategy
    strategy = LlamaStrategy(verbose=True)
    
    # Create a PromptMigrator with the Llama strategy
    migrator = PromptMigrator(
        strategy=strategy,
        model_family="llama"
    )
    
    # Optimize the prompt
    try:
        # In a real application, you would provide actual training and validation data
        # Here we're just demonstrating the API
        result = migrator.optimize(
            prompt_data=prompt_data.copy(),
            save_to_file=True,
            file_path="optimized_prompt_llama.json",
            save_yaml=True,
            use_llama_tips=True
        )
        
        # Print the optimized prompt
        if isinstance(result, str):
            print(f"Optimized Prompt:\n{result}")
        elif hasattr(result, 'predict') and hasattr(result.predict, 'signature'):
            print(f"Optimized Prompt:\n{result.predict.signature.__doc__}")
        else:
            print(f"Optimization result: {str(result)[:200]}...")
            
    except Exception as e:
        print(f"Error optimizing for Llama: {str(e)}")

def demonstrate_llama_specific_features():
    """Demonstrate specific features of Llama-specific optimization."""
    
    # Sample prompts for different tasks
    prompts = {
        "classification": {
            "text": "Classify the sentiment of the following text as positive, negative, or neutral.",
            "inputs": ["text"],
            "outputs": ["sentiment"],
            "input_fields": ["text"],
            "output_fields": ["sentiment", "class"],
            "examples": [
                {
                    "input": "I absolutely loved the movie! The acting was superb and the plot was engaging.",
                    "output": "positive"
                },
                {
                    "input": "The service was terrible and the food was cold.",
                    "output": "negative"
                },
                {
                    "input": "The weather today is partly cloudy with a high of 75°F.",
                    "output": "neutral"
                }
            ]
        },
        "coding": {
            "text": "Write a Python function that takes a list of integers and returns the sum of all even numbers in the list.",
            "inputs": ["requirements"],
            "outputs": ["code"],
            "input_fields": ["requirements"],
            "output_fields": ["code", "implementation"],
            "examples": [
                {
                    "input": "Write a function to check if a string is a palindrome.",
                    "output": "```python\ndef is_palindrome(s):\n    # Remove non-alphanumeric characters and convert to lowercase\n    s = ''.join(c.lower() for c in s if c.isalnum())\n    # Check if the string is equal to its reverse\n    return s == s[::-1]\n```"
                }
            ]
        }
    }
    
    print(f"\n{'='*80}\nDemonstrating Llama-Specific Features\n{'='*80}")
    
    # Process each task type
    for task_name, prompt_data in prompts.items():
        print(f"\nOptimizing {task_name.upper()} task for Llama model")
        
        # Create a Llama-specific strategy with custom parameters
        llama_strategy = LlamaStrategy(
            apply_formatting=True,
            apply_templates=True,
            template_type="with_examples",
            verbose=True
        )
        
        # Create a PromptMigrator with the Llama strategy
        migrator = PromptMigrator(
            strategy=llama_strategy,
            model_family="llama"
        )
        
        # Optimize the prompt
        try:
            result = migrator.optimize(
                prompt_data=prompt_data.copy(),
                save_to_file=True,
                file_path=f"llama_{task_name}_task.json",
                save_yaml=True
            )
            
            # Print the optimized prompt
            if isinstance(result, str):
                print(f"Llama-Optimized Prompt:\n{result}")
            elif hasattr(result, 'predict') and hasattr(result.predict, 'signature'):
                print(f"Llama-Optimized Prompt:\n{result.predict.signature.__doc__}")
            else:
                print(f"Optimization result: {str(result)[:200]}...")
                
        except Exception as e:
            print(f"Error with Llama optimization for {task_name}: {str(e)}")
        
        print("-" * 50)

def demonstrate_llama_instruction_preferences():
    """Demonstrate Llama-specific instruction preferences for different task types."""
    
    print(f"\n{'='*80}\nDemonstrating Llama-specific Instruction Preferences\n{'='*80}")
    
    # Import the necessary functions
    from prompt_migrator.core.utils.llama_utils import (
        get_task_type_from_prompt,
        select_instruction_preference,
        get_model_tips
    )
    
    # Sample prompts for different tasks
    prompts = {
        "extraction": {
            "text": "Extract the following entities from the text: person names, locations, organizations, and dates.",
            "input_fields": ["text"],
            "output_fields": ["entities", "extracted_information"]
        },
        "coding": {
            "text": "Write a Python function that takes a list of integers and returns the sum of all even numbers in the list.",
            "input_fields": ["requirements"],
            "output_fields": ["code", "implementation"]
        },
        "reasoning": {
            "text": "Analyze the following logical problem and provide a step-by-step solution.",
            "input_fields": ["problem"],
            "output_fields": ["solution", "reasoning"]
        },
        "classification": {
            "text": "Classify the sentiment of the following text as positive, negative, or neutral.",
            "input_fields": ["text"],
            "output_fields": ["sentiment", "class"]
        },
        "summarization": {
            "text": "Summarize the following text in 3-5 sentences, capturing the main points.",
            "input_fields": ["text"],
            "output_fields": ["summary"]
        }
    }
    
    # Get Llama-specific tips
    llama_tips = get_model_tips("llama")
    instruction_preferences = llama_tips.get("instruction_preferences", [])
    
    if not instruction_preferences:
        print("No instruction preferences found for Llama models.")
        return
    
    # For each prompt, detect task type and select appropriate instruction preference
    for task_name, prompt_data in prompts.items():
        # Detect task type
        task_type = get_task_type_from_prompt(
            prompt_data["text"],
            prompt_data["input_fields"],
            prompt_data["output_fields"]
        )
        
        # Select instruction preference
        preference = select_instruction_preference("llama", task_type, prompt_data)
        
        # Display results
        print(f"\nPrompt: {prompt_data['text']}")
        print(f"Detected task type: {task_type}")
        print(f"Selected instruction preference: {preference[:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    # Run the examples
    optimize_for_llama_model()
    demonstrate_llama_specific_features()
    demonstrate_llama_instruction_preferences()
