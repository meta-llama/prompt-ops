# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Core migrator module for prompt optimization.

This module contains the main PromptMigrator class that orchestrates the
optimization process using configurable strategies.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import dspy

from .exceptions import OptimizationError, EvaluationError
from .datasets import DatasetAdapter, load_dataset
from .prompt_strategies import BaseStrategy
from .evaluation import create_evaluator
from .utils.llama_utils import is_llama_model
from .utils import json_to_yaml_file

class PromptMigrator:
    """
    Main class for migrating and optimizing prompts.
    
    The PromptMigrator applies a strategy to transform input prompts into
    optimized versions tailored for specific model families.
    """
    
    def __init__(
        self, 
        strategy: Optional[BaseStrategy] = None, 
        task_model=None,
        prompt_model=None,
        trainset=None,
        valset=None,
        testset=None,
        model_family: str = None
    ):
        """
        Initialize the PromptMigrator with a strategy.
        
        Args:
            strategy: A strategy instance derived from BaseStrategy.
                     If None is provided, a default strategy is used.
            task_model: The model to use for the task (DSPy LM instance)
            prompt_model: The model to use for prompt optimization (DSPy LM instance)
            trainset: Training dataset for optimization
            valset: Validation dataset for optimization
            testset: Test dataset for evaluation
            model_family: The model family to optimize for (e.g., "llama", "gpt", "claude").
                         If None, will be inferred from task_model if possible.
        """
        
        if strategy is None:
            strategy = BaseStrategy()
        self.strategy = strategy
        
        # Store models and datasets
        self.task_model = task_model
        self.prompt_model = prompt_model
        self.trainset = trainset
        self.valset = valset
        self.testset = testset
        
        # Determine if we're using a Llama model
        if model_family is None and task_model is not None:
            # Try to extract model name from task_model
            if hasattr(task_model, 'model_name'):
                model_name = task_model.model_name
            else:
                model_name = str(task_model)
            
            if is_llama_model(model_name):
                self.model_family = "llama"
            else:
                logging.warning(f"Model '{model_name}' does not appear to be a Llama model. "
                              f"This library is optimized for Llama models and may not work as expected.")
                self.model_family = "llama"  # Default to Llama anyway since that's our focus
        else:
            self.model_family = model_family or "llama"
            if self.model_family != "llama":
                logging.warning(f"Model family '{self.model_family}' specified, but this library "
                              f"is optimized for Llama models and may not work as expected.")
        
        self._optimized_program = None
    
    def optimize(
        self, 
        prompt_data: Dict[str, Any], 
        trainset: List[Any] = None, 
        valset: List[Any] = None,
        testset: List[Any] = None,
        save_to_file: bool = False, 
        file_path: str = None,
        save_yaml: bool = True,
        user_prompt: str = None,
        use_llama_tips: bool = True
    ) -> Any:
        """
        Optimize a prompt using the configured strategy.
        
        Args:
            prompt_data: Dictionary containing the prompt text and metadata
            trainset: Training examples for optimization (overrides the instance trainset)
            valset: Validation examples for optimization (overrides the instance valset)
            testset: Test examples for evaluation (overrides the instance testset)
            save_to_file: Whether to save the optimized prompt to a file
            file_path: Path to save the file (optional)
            save_yaml: Whether to also save the prompt in YAML format
            user_prompt: Optional user prompt to append to the YAML file
            
        Returns:
            The optimized DSPy program
            
        Raises:
            ValueError: If prompt_data does not contain a 'text' key.
        """
        if "text" not in prompt_data:
            raise ValueError("prompt_data must contain a 'text' key.")
            
        if use_llama_tips:
            from .utils.llama_utils import get_llama_tips
            model_tips = get_llama_tips()
            
            if "model_tips" not in prompt_data:
                prompt_data["model_tips"] = model_tips

        trainset = trainset if trainset is not None else self.trainset
        valset = valset if valset is not None else self.valset
        testset = testset if testset is not None else self.testset

        if hasattr(self.strategy, 'task_model') and self.task_model:
            self.strategy.task_model = self.task_model
        
        if hasattr(self.strategy, 'prompt_model') and self.prompt_model:
            self.strategy.prompt_model = self.prompt_model
            
        if hasattr(self.strategy, 'trainset') and trainset:
            self.strategy.trainset = trainset
            
        if hasattr(self.strategy, 'valset') and valset:
            self.strategy.valset = valset

        logging.info(f"Applying {self.strategy.__class__.__name__} to optimize prompt")
        logging.info(f"Training set size: {len(trainset) if trainset else 0}")
        logging.info(f"Validation set size: {len(valset) if valset else 0}")
        
        optimized_program = self.strategy.run(prompt_data)
        
        self._optimized_program = optimized_program
        
        logging.info("Optimized prompt:")
        logging.info("-" * 40)
        logging.info(optimized_program.signature.instructions)
        logging.info("-" * 40)
        
        if "Examples:" in optimized_program.signature.instructions:
            logging.info("Examples are included in the optimized prompt")
        
        if save_to_file:
            saved_path = self.save_optimized_prompt(optimized_program, file_path, save_yaml, user_prompt)
        
        return optimized_program
   
    def load_dataset_with_adapter(
        self, 
        adapter: DatasetAdapter, 
        train_size: float = 0.25, 
        validation_size: float = 0.25
    ) -> Tuple[List[dspy.Example], List[dspy.Example], List[dspy.Example]]:
        """
        Load a dataset using an adapter.
        
        Args:
            adapter: Dataset adapter
            train_size: Fraction of data to use for training
            validation_size: Fraction of data to use for validation
            
        Returns:
            Tuple containing (trainset, valset, testset)
        """
        self.trainset, self.valset, self.testset = load_dataset(
            adapter, train_size, validation_size
        )
        
        # Update strategy with datasets if available
        if hasattr(self.strategy, 'trainset') and self.trainset:
            self.strategy.trainset = self.trainset
            
        if hasattr(self.strategy, 'valset') and self.valset:
            self.strategy.valset = self.valset
            
        return self.trainset, self.valset, self.testset

    def evaluate(
        self,
        program=None,
        examples=None,
        metric=None,
        devset=None,
        statistical=False,
        **kwargs
    ):
        """
        Evaluate a program on a set of examples.
        
        Args:
            program: The program to evaluate.
            examples: The examples to evaluate on.
            metric: Evaluation metric (defaults to the strategy's metric)
            devset: Evaluation dataset (defaults to the valset)
            statistical: Whether to use statistical evaluation
            **kwargs: Additional arguments for the evaluator
            
        Returns:
            Evaluation results
        """
        if program is None:
            program = self._optimized_program
            
        if program is None:
            raise ValueError("No program provided and no previously optimized program available")
        
        if metric is None and hasattr(self.strategy, 'metric'):
            metric = self.strategy.metric
        
        if devset is None:
            devset = self.valset
        
        evaluator = create_evaluator(
            metric=metric,
            devset=devset,
            statistical=statistical,
            **kwargs
        )
        
        if statistical:
            return evaluator.evaluate_with_statistics(program)
        return evaluator.evaluate(program)

    def save_optimized_prompt(self, program=None, file_path=None, save_yaml=False, user_prompt=None):
        """
        Save the optimized prompt to a file.

        Args:
            program: The optimized program to save.
            file_path: The path to save the file to. If None, a default path will be used.
            save_yaml: Whether to also save in YAML format.
            user_prompt: Optional user prompt to append to the YAML file.

        Returns:
            The path to the saved file.
        """
        if program is None:
            program = self._optimized_program

        if program is None:
            raise ValueError("No optimized program to save.")

        # Extract the prompt content
        if hasattr(program, "predict"):
            prompt_content = getattr(program.predict.signature, "instructions", None) or program.predict.signature.__doc__
        else:
            prompt_content = program.signature.instructions

        # Extract examples from the program
        few_shots = []
        if isinstance(program, dspy.ChainOfThought):
            if hasattr(program, "predict") and hasattr(program.predict, "demos") and program.predict.demos is not None:
                few_shots = [
                    {
                        "question": ex.question,
                        "context": ex.context if hasattr(ex, "context") else "",
                        "answer": ex.answer
                    }
                    for ex in program.predict.demos
                ]
            elif hasattr(program, "demos") and program.demos is not None:
                few_shots = [
                    {
                        "question": ex.question,
                        "context": ex.context if hasattr(ex, "context") else "",
                        "answer": ex.answer
                    }
                    for ex in program.demos
                ]
        elif hasattr(program, "demos") and program.demos is not None:
            few_shots = [
                {
                    "question": ex.question,
                    "context": ex.context if hasattr(ex, "context") else "",
                    "answer": ex.answer
                }
                for ex in program.demos
            ]

        prompt_json = {
            "prompt": prompt_content,
            "few_shots": few_shots
        }

        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate default filename with timestamp if not provided
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"optimized_prompt_{timestamp}.json"
        
        # Ensure the file is saved in the results directory
        file_path = os.path.join(results_dir, os.path.basename(file_path))
        
        # Save the JSON to the file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(prompt_json, f, indent=2, ensure_ascii=False)
            
        logging.info(f"Saved optimized prompt to {file_path}")
        
        # If save_yaml is True, also save as YAML
        if save_yaml:            
            yaml_file_path = file_path.replace(".json", ".yaml")
            
            # Use the utility function to convert JSON to YAML
            json_to_yaml_file(
                file_path, 
                yaml_file_path, 
                user_prompt=user_prompt,
                task_model=self.task_model if hasattr(self, 'task_model') else None,
                model_family=self.model_family if hasattr(self, 'model_family') else None,
                strategy=self.strategy if hasattr(self, 'strategy') else None
            )
            logging.info(f"Saved YAML prompt to {yaml_file_path}")
            
        return file_path
