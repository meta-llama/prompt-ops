# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Strategy implementations for prompt optimization.

This module contains the base strategy class and various specialized
optimization strategies for migrating prompts to Llama models.
"""

import json
import logging
import os
import sys
import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

import dspy
from typing_extensions import Literal

from .evaluation import create_evaluator
from .model import LiteLLMModelAdapter
from .utils import map_auto_mode_to_dspy


class OptimizationError(Exception):
    """Exception raised when prompt optimization fails."""

    pass


class BaseStrategy(ABC):
    """
    Base class for prompt optimization strategies.

    This class defines the interface for optimization strategies and provides
    common functionality.
    """

    def __init__(
        self,
        model_name: str = "llama-3",
        metric: Optional[Callable] = None,
        num_threads: int = 18,
        model_family: str = None,
    ):
        """
        Initialize the strategy.

        Args:
            model_name: Name of the model to optimize for
            metric: Metric to use for evaluation
            num_threads: Number of threads to use for parallel processing
            model_family: Model family to optimize for (e.g., "llama")
                         If None, will be inferred from model_name
        """
        self.model_name = model_name
        self.metric = metric
        self.num_threads = num_threads
        self.trainset = None
        self.valset = None

        # Set model family if provided, otherwise leave as None (model-agnostic)
        self.model_family = model_family

    @abstractmethod
    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """
        Execute the optimization strategy on the given prompt data.

        Args:
            prompt_data: Dictionary containing prompt information
                - text: The prompt text to optimize
                - inputs: List of input field names
                - outputs: List of output field names

        Returns:
            The optimized prompt text
        """
        text = prompt_data.get("text", "")
        # Default behavior: no changes
        return text


class BasicOptimizationStrategy(BaseStrategy):
    """
    A strategy that runs a basic optimization pass using DSPy's MIPROv2.
    based on this paper: https://arxiv.org/pdf/2406.11695

    This strategy applies a basic optimization to the prompt using DSPy's
    MIPROv2 optimizer with the 'basic' auto mode, which focuses on format
    and style adjustments without extensive restructuring.

    This strategy can be model-aware, incorporating model-specific tips and
    formatting preferences into the optimization process.
    """

    def __init__(
        self,
        model_name: str = "llama-3",
        num_threads: int = 18,
        metric: Optional[Callable] = None,
        model_family: str = None,
        # MIPROv2 specific parameters
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 5,
        auto: Optional[Literal["basic", "intermediate", "advanced"]] = "basic",
        num_candidates: int = 10,
        max_errors: int = 10,
        seed: int = 9,
        init_temperature: float = 0.5,
        verbose: bool = False,
        track_stats: bool = True,
        log_dir: Optional[str] = None,
        metric_threshold: Optional[float] = None,
        # Compile method parameters
        num_trials: Optional[int] = None,
        minibatch: bool = True,
        minibatch_size: int = 25,
        minibatch_full_eval_steps: int = 10,
        program_aware_proposer: bool = True,
        data_aware_proposer: bool = True,
        view_data_batch_size: int = 10,
        tip_aware_proposer: bool = True,
        fewshot_aware_proposer: bool = True,
        requires_permission_to_run: bool = False,
        # Baseline computation settings
        compute_baseline: bool = True,
        # Model name parameters for display
        task_model_name: Optional[str] = None,
        prompt_model_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the basic optimization strategy with MIPROv2 parameters.

        Args:
            model_name: Target Llama model name
            num_threads: Number of threads for optimization
            metric: Evaluation metric function

            # MIPROv2 constructor parameters
            max_bootstrapped_demos: Maximum number of bootstrapped demos to generate
            max_labeled_demos: Maximum number of labeled demos to include
            auto: Optimization mode ('basic', 'intermediate', 'advanced')
                 These values are mapped to DSPy's expected values ('light', 'medium', 'heavy')
            num_candidates: Number of candidate instructions to generate
            max_errors: Maximum number of errors to tolerate during evaluation
            seed: Random seed for reproducibility
            init_temperature: Initial temperature for sampling
            verbose: Whether to print verbose output
            track_stats: Whether to track statistics
            log_dir: Directory to save logs
            metric_threshold: Threshold for early stopping based on metric

            # MIPROv2 compile method parameters
            num_trials: Number of optimization trials (if None, determined by auto mode)
            minibatch: Whether to use minibatching for evaluation
            minibatch_size: Size of minibatches for evaluation
            minibatch_full_eval_steps: How often to evaluate on the full validation set
            program_aware_proposer: Whether to use program-aware instruction proposals
            data_aware_proposer: Whether to use data-aware instruction proposals
            view_data_batch_size: Number of examples to show to the proposer
            tip_aware_proposer: Whether to use tip-aware instruction proposals
            fewshot_aware_proposer: Whether to use few-shot aware instruction proposals
            requires_permission_to_run: Whether to require user permission to run

            # Baseline computation parameters
            compute_baseline: Whether to compute baseline score before optimization

            # Model name parameters for display
            task_model_name: Name of the task model
            prompt_model_name: Name of the prompt model

            **kwargs: Additional configuration parameters
        """
        super().__init__(model_name, metric, num_threads, model_family)

        # Store task and prompt models
        self.task_model = kwargs.get("task_model")
        self.prompt_model = kwargs.get("prompt_model")

        # Training and validation data
        self.trainset = kwargs.get("trainset", [])
        self.valset = kwargs.get("valset", [])
        self.testset = kwargs.get("testset", [])

        # MIPROv2 constructor parameters
        self.max_bootstrapped_demos = max_bootstrapped_demos
        self.max_labeled_demos = max_labeled_demos
        self.auto = auto
        self.num_candidates = num_candidates
        self.max_errors = max_errors
        self.seed = seed
        self.init_temperature = init_temperature
        self.verbose = verbose
        self.track_stats = track_stats
        self.log_dir = log_dir
        self.metric_threshold = metric_threshold

        # MIPROv2 compile method parameters
        self.num_trials = num_trials
        self.minibatch = minibatch
        self.minibatch_size = minibatch_size
        self.minibatch_full_eval_steps = minibatch_full_eval_steps
        self.program_aware_proposer = program_aware_proposer
        self.data_aware_proposer = data_aware_proposer
        self.view_data_batch_size = view_data_batch_size
        self.tip_aware_proposer = tip_aware_proposer
        self.fewshot_aware_proposer = fewshot_aware_proposer
        self.requires_permission_to_run = requires_permission_to_run

        # Baseline computation settings
        self.compute_baseline = compute_baseline

        # Model name parameters for display
        self.task_model_name = task_model_name
        self.prompt_model_name = prompt_model_name

    def _get_model_name(self, model) -> str:
        """
        Get a human-readable name for a model using stored names.

        Args:
            model: The model object to get the name for

        Returns:
            A string representation of the model name
        """
        if model is None:
            return "None"

        # Use stored model names if available
        if model is self.task_model and self.task_model_name:
            return self.task_model_name
        if model is self.prompt_model and self.prompt_model_name:
            return self.prompt_model_name

        # Fallback to legacy introspection for backward compatibility
        if hasattr(model, "model_name"):
            return str(model.model_name)
        if hasattr(model, "model"):
            return str(model.model)
        if hasattr(model, "_model") and hasattr(model._model, "model"):
            return str(model._model.model)

        # Final fallback
        return str(model)

    def _create_signature(self, prompt_data: Dict[str, Any], instructions: str):
        """
        Create a DSPy signature with explicit field definitions.

        Args:
            prompt_data: Dictionary containing inputs and outputs field definitions
            instructions: The instruction text for the signature

        Returns:
            DSPy signature class
        """
        # Create a signature class dynamically with proper field definitions
        input_fields = {}
        output_fields = {}

        # Define input and output fields based on prompt_data
        for field in prompt_data.get("inputs", ["question"]):
            input_fields[field] = dspy.InputField(desc="${" + field + "}")
        for field in prompt_data.get("outputs", ["answer"]):
            output_fields[field] = dspy.OutputField(desc="${" + field + "}")

        # Create the signature class with proper field definitions
        DynamicSignature = type(
            "DynamicSignature",
            (dspy.Signature,),
            {
                **input_fields,
                **output_fields,
                "__doc__": instructions,  # Store the instructions as the docstring
            },
        )

        return DynamicSignature

    def _compute_baseline_score(self, prompt_data: Dict[str, Any]) -> Optional[float]:
        """
        Compute baseline score using the original prompt before optimization.
        Uses testset to avoid data leakage and evaluation.py for consistency.

        Args:
            prompt_data: Dictionary containing the prompt text and metadata

        Returns:
            Baseline score as float, or None if computation fails or is not possible
        """
        if not self.metric or not self.testset:
            logging.debug("Skipping baseline computation: missing metric or test set")
            return None

        if not self.compute_baseline:
            logging.debug("Baseline computation disabled")
            return None

        try:
            start_time = time.time()

            # Use consistent signature creation with original prompt
            baseline_signature = self._create_signature(
                prompt_data, prompt_data["text"]
            )
            baseline_program = dspy.Predict(baseline_signature)

            print(
                f"\nComputing baseline score on {len(self.testset)} test examples using {self.num_threads} threads..."
            )

            evaluator = create_evaluator(
                metric=self.metric,
                devset=self.testset,
                num_threads=self.num_threads,  # Use the strategy's num_threads setting
                display_progress=True,
                display_table=False,
            )

            score = evaluator.evaluate(baseline_program)
            duration = time.time() - start_time

            print(f"Baseline Score: {score:.3f} in {duration:.2f}s\n")
            return float(score)

        except Exception as e:
            logging.warning(f"Baseline evaluation failed: {e}")
            return None

    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """
        Apply basic optimization to the prompt using DSPy's MIPROv2.

        Args:
            prompt_data: Dictionary containing the prompt text and metadata

        Returns:
            The optimized DSPy program object, which contains the optimized prompt
            accessible via optimized_program.predict.signature.instructions
        """
        text = prompt_data["text"]

        if "dspy" not in globals() or not self.trainset:
            return f"[Optimized for {self.model_name}] {text}"

        # Display pre-optimization summary using utility function
        from .utils.summary_utils import create_and_display_summary

        create_and_display_summary(self, prompt_data)

        try:
            # Create signature using consistent helper method
            signature = self._create_signature(prompt_data, text)

            # Create program instance with the signature
            program = dspy.Predict(signature)

            # Map our naming convention to DSPy's expected values
            dspy_auto_mode = map_auto_mode_to_dspy(self.auto)

            # Extract the underlying DSPy model if we have model adapters
            task_model = self.task_model
            prompt_model = self.prompt_model

            # Handle DSPyModelAdapter instances
            if hasattr(task_model, "_model"):
                task_model = task_model._model

            if hasattr(prompt_model, "_model"):
                prompt_model = prompt_model._model

            # Configure the optimizer with all parameters
            optimizer = dspy.MIPROv2(
                metric=self.metric,
                prompt_model=prompt_model,
                task_model=task_model,
                max_bootstrapped_demos=self.max_bootstrapped_demos,
                max_labeled_demos=self.max_labeled_demos,
                auto=dspy_auto_mode,  # Use the mapped value
                num_candidates=self.num_candidates,
                num_threads=self.num_threads,
                max_errors=self.max_errors,
                seed=self.seed,
                init_temperature=self.init_temperature,
                verbose=self.verbose,
                track_stats=self.track_stats,
                log_dir=self.log_dir,
                metric_threshold=self.metric_threshold,
            )

            # Initialize proposer_kwargs if not already present
            optimizer.proposer_kwargs = getattr(optimizer, "proposer_kwargs", {}) or {}

            # Check if we have custom instruction tips
            if (
                hasattr(self, "proposer_kwargs")
                and self.proposer_kwargs
                and "tip" in self.proposer_kwargs
            ):
                # Use our custom instruction tips
                optimizer.proposer_kwargs["tip"] = self.proposer_kwargs["tip"]
                logging.info(
                    f"Using custom instruction tips: {self.proposer_kwargs['tip'][:50] if self.proposer_kwargs['tip'] else 'None'}"
                )

            logging.info(
                f"Optimization strategy using {self.max_labeled_demos} labeled demos, {self.max_bootstrapped_demos} bootstrapped demos with {self.num_threads} threads"
            )

            logging.info(
                f"Compiling program with {len(self.trainset)} training examples, {len(self.valset)} validation examples, and {len(self.testset)} test examples"
            )

            # Create a custom compile method that injects our tip directly
            original_propose_instructions = None
            if (
                hasattr(self, "proposer_kwargs")
                and self.proposer_kwargs
                and "tip" in self.proposer_kwargs
            ):
                # Store the original method
                from dspy.propose.grounded_proposer import GroundedProposer

                original_propose_instructions = (
                    GroundedProposer.propose_instructions_for_program
                )

                # Create a wrapper that injects our custom tip
                def custom_propose_instructions(self, *args, **kwargs):
                    logging.info(
                        "Starting custom_propose_instructions with enhanced error handling"
                    )

                    try:
                        # Log arguments for debugging
                        if len(args) >= 3:
                            trainset = args[0]
                            program = args[1]
                            demo_candidates = args[2]

                            logging.info(
                                f"Trainset size: {len(trainset) if trainset else 0}"
                            )
                            logging.info(f"Program type: {type(program)}")
                            logging.info(
                                f"Demo candidates: {'Present' if demo_candidates else 'None'}"
                            )

                            # Check for potential issues
                            if not trainset or len(trainset) == 0:
                                logging.warning(
                                    "Empty trainset provided to instruction proposer"
                                )

                            if demo_candidates is None:
                                logging.warning(
                                    "Demo candidates is None, which may cause issues"
                                )

                            # Log first training example for debugging
                            if trainset and len(trainset) > 0:
                                example = trainset[0]
                                logging.info(f"First trainset example: {example}")
                                if hasattr(example, "inputs") and hasattr(
                                    example, "outputs"
                                ):
                                    logging.info(f"Example inputs: {example.inputs}")
                                    logging.info(f"Example outputs: {example.outputs}")
                                else:
                                    logging.warning(
                                        "Example missing required 'inputs' or 'outputs' attributes"
                                    )

                        # Override the tip parameter with our custom tip
                        if "tip" in kwargs:
                            logging.info(
                                f"Using default tip parameter: {kwargs['tip'][:50] if kwargs['tip'] else 'None'}"
                            )

                        # Inject our custom tip
                        custom_tip = optimizer.proposer_kwargs.get("tip")
                        if custom_tip:
                            logging.info(f"Injecting custom tip: {custom_tip[:50]}...")
                            kwargs["tip"] = custom_tip

                        # Call the original method with enhanced error handling
                        logging.info(
                            "Calling original propose_instructions_for_program"
                        )
                        result = original_propose_instructions(self, *args, **kwargs)

                        # Log the result for debugging
                        if result is None:
                            logging.error("Instruction proposer returned None")
                            # Create a fallback result
                            if len(args) >= 2:
                                program = args[1]
                                fallback_result = {}
                                for i, pred in enumerate(program.predictors()):
                                    fallback_result[i] = [
                                        getattr(
                                            pred,
                                            "instructions",
                                            "Default instruction due to error",
                                        )
                                    ]
                                logging.info("Created fallback instructions")
                                return fallback_result
                        else:
                            logging.info(
                                f"Instruction proposer returned result with keys: {result.keys()}"
                            )

                        return result
                    except Exception as e:
                        logging.error(f"Error in custom_propose_instructions: {str(e)}")
                        logging.error(traceback.format_exc())

                        # Create a fallback result
                        if len(args) >= 2:
                            program = args[1]
                            fallback_result = {}
                            for i, pred in enumerate(program.predictors()):
                                fallback_result[i] = [
                                    getattr(
                                        pred,
                                        "instructions",
                                        "Default instruction due to error",
                                    )
                                ]
                            logging.info(
                                "Created fallback instructions after exception"
                            )
                            return fallback_result

                        # Re-raise if we can't create a fallback
                        raise

                # Apply our wrapper
                GroundedProposer.propose_instructions_for_program = (
                    custom_propose_instructions
                )

            # Try to apply our debug wrapper to the GroundedProposer class
            try:
                from prompt_ops.debug import patch_dspy_proposer

                debug_patched = patch_dspy_proposer()
                if debug_patched:
                    logging.info(
                        "Successfully applied debug wrapper to GroundedProposer"
                    )
                else:
                    logging.warning("Failed to apply debug wrapper to GroundedProposer")
            except ImportError:
                logging.warning(
                    "Debug module not available, continuing without enhanced debugging"
                )

            try:
                # Set up detailed logging for the instruction proposal phase
                logging.info("Starting DSPy optimization with enhanced debugging")
                logging.info(f"Program type: {type(program)}")
                logging.info(f"Trainset size: {len(self.trainset)}")
                logging.info(f"Valset size: {len(self.valset) if self.valset else 0}")

                # Log the first example in trainset to help debug data format issues
                if self.trainset and len(self.trainset) > 0:
                    example = self.trainset[0]
                    logging.info(f"First trainset example structure: {type(example)}")
                    if hasattr(example, "inputs") and hasattr(example, "outputs"):
                        logging.info(f"Example inputs: {example.inputs}")
                        logging.info(f"Example outputs: {example.outputs}")
                    else:
                        logging.warning(
                            "Example missing required 'inputs' or 'outputs' attributes"
                        )
                        logging.warning(
                            f"Example attributes: {dir(example) if hasattr(example, '__dict__') else 'No attributes'}"
                        )

                # Wrap the compile call in a try/except to catch specific errors
                try:
                    # Call compile with all parameters
                    logging.info("Calling optimizer.compile")
                    optimized_program = optimizer.compile(
                        program,
                        trainset=self.trainset,
                        valset=self.valset,
                        num_trials=self.num_trials,
                        minibatch=self.minibatch,
                        minibatch_size=self.minibatch_size,
                        minibatch_full_eval_steps=self.minibatch_full_eval_steps,
                        program_aware_proposer=self.program_aware_proposer,
                        data_aware_proposer=self.data_aware_proposer,
                        view_data_batch_size=self.view_data_batch_size,
                        tip_aware_proposer=self.tip_aware_proposer,
                        fewshot_aware_proposer=self.fewshot_aware_proposer,
                        requires_permission_to_run=self.requires_permission_to_run,
                        provide_traceback=True,  # Add this line
                    )
                    logging.info("Optimizer.compile completed successfully")
                except TypeError as e:
                    if "'NoneType' object is not subscriptable" in str(e):
                        logging.error(f"Error in instruction proposal phase: {str(e)}")
                        logging.error(traceback.format_exc())

                        # Detailed error analysis
                        logging.error(
                            "Detailed error analysis for 'NoneType' object is not subscriptable:"
                        )
                        logging.error(
                            "This typically occurs when the instruction proposal phase fails to generate valid instructions"
                        )
                        logging.error("Possible causes:")
                        logging.error(
                            "1. Dataset format issues - ensure each example has 'inputs' and 'outputs' fields"
                        )
                        logging.error("2. Empty or insufficient training data")
                        logging.error(
                            "3. Model API errors during instruction generation"
                        )
                        logging.error("4. Incompatible DSPy version")

                        # Create a fallback
                        logging.warning("Falling back to original prompt")
                        optimized_program = None
                    else:
                        logging.error(
                            f"Unexpected TypeError during optimization: {str(e)}"
                        )
                        logging.error(traceback.format_exc())
                        raise
                except Exception as e:
                    logging.error(f"Error during optimization: {str(e)}")
                    logging.error(traceback.format_exc())
                    raise
            finally:
                # Restore the original method if we modified it
                if original_propose_instructions:
                    GroundedProposer.propose_instructions_for_program = (
                        original_propose_instructions
                    )

            # Store model family information in the optimized program for reference
            if hasattr(self, "model_family") and optimized_program is not None:
                setattr(optimized_program, "model_family", self.model_family)

            # Check if optimization was successful
            if optimized_program is None:
                logging.warning(
                    "Optimizer returned None. Falling back to original prompt."
                )
                # Create a simple program with the original prompt as a fallback
                fallback_program = program
                # Add a marker to indicate this is a fallback
                setattr(fallback_program, "is_fallback", True)
                setattr(fallback_program, "model_family", self.model_family)
                return fallback_program

            # Log information about the optimized program
            logging.info(f"Optimized program type: {type(optimized_program)}")
            logging.info(f"Optimized program attributes: {dir(optimized_program)}")

            return optimized_program

        except Exception as e:
            logging.error(f"Error in optimization: {str(e)}")
            # Instead of creating a mock program, raise a more descriptive exception
            raise OptimizationError(f"Optimization failed: {str(e)}")


class PDOStrategy(BaseStrategy):
    """
    PDO (Prompt Duel Optimizer) strategy using dueling bandits.

    This strategy uses Thompson sampling and dueling bandits to optimize
    prompts through head-to-head competitions, with multiple ranking systems
    and prompt evolution techniques.
    """

    def __init__(
        self,
        model_name: str = "llama-3",
        metric: Optional[Callable] = None,
        num_threads: int = 18,
        model_family: str = None,
        # PDO-specific parameters
        total_rounds: int = 100,
        num_duels_per_round: int = 3,
        num_eval_examples_per_duel: int = 50,
        num_initial_instructions: int = 2,
        use_labels: bool = True,
        thompson_alpha: float = 2.0,
        num_top_prompts_to_combine: int = 3,
        num_new_prompts_to_generate: int = 1,
        max_new_prompts_to_generate: int = 50,
        num_to_prune_each_round: int = 1,
        gen_new_prompt_round_frequency: int = 1,
        max_concurrent_threads: int = 8,
        # Model parameters
        task_model: Optional[Any] = None,
        prompt_model: Optional[Any] = None,
        task_model_name: Optional[str] = None,
        prompt_model_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize PDO strategy.

        Args:
            model_name: Target model name
            metric: Evaluation metric function
            num_threads: Number of threads for optimization (used for compatibility)
            model_family: Model family (e.g., "llama")
            total_rounds: Number of optimization rounds
            num_duels_per_round: Number of duels per round
            num_eval_examples_per_duel: Examples per duel
            num_initial_instructions: Initial instruction pool size
            use_labels: Whether to use supervised learning
            thompson_alpha: Thompson sampling alpha parameter
            num_top_prompts_to_combine: Top prompts for combination
            num_new_prompts_to_generate: New prompts per round
            max_new_prompts_to_generate: Maximum total new prompts
            num_to_prune_each_round: Prompts to prune per round
            gen_new_prompt_round_frequency: Frequency of prompt generation
            max_concurrent_threads: Max threads for parallel execution
            task_model: ModelAdapter for task execution
            prompt_model: ModelAdapter for evaluation/judging
            task_model_name: Name of task model (for display)
            prompt_model_name: Name of prompt model (for display)
            **kwargs: Additional parameters
        """
        super().__init__(model_name, metric, num_threads, model_family)

        # Create or store models - PDO uses LiteLLMModelAdapter for lightweight text generation
        if task_model is None:
            # Extract model configuration from kwargs
            model_config = {
                "model_name": task_model_name or model_name,
                "api_key": kwargs.get("api_key"),
                "api_base": kwargs.get("api_base"),
                "temperature": kwargs.get("temperature", 0.0),
                "max_tokens": kwargs.get("max_tokens", 4096),
            }
            # Remove None values
            model_config = {k: v for k, v in model_config.items() if v is not None}
            self.task_model = LiteLLMModelAdapter(**model_config)
        else:
            self.task_model = task_model

        if prompt_model is None:
            # Extract model configuration from kwargs
            model_config = {
                "model_name": prompt_model_name or model_name,
                "api_key": kwargs.get("api_key"),
                "api_base": kwargs.get("api_base"),
                "temperature": kwargs.get("temperature", 0.0),
                "max_tokens": kwargs.get("max_tokens", 4096),
            }
            # Remove None values
            model_config = {k: v for k, v in model_config.items() if v is not None}
            self.prompt_model = LiteLLMModelAdapter(**model_config)
        else:
            self.prompt_model = prompt_model

        # Store model names for display
        self.task_model_name = task_model_name or model_name
        self.prompt_model_name = prompt_model_name or model_name

        # PDO configuration (add user ranking_method; default copeland)
        self.pdo_config = {
            "total_rounds": total_rounds,
            "num_duels_per_round": num_duels_per_round,
            "num_eval_examples_per_duel": num_eval_examples_per_duel,
            "num_initial_instructions": num_initial_instructions,
            "use_labels": use_labels,
            "thompson_alpha": thompson_alpha,
            "num_top_prompts_to_combine": num_top_prompts_to_combine,
            "num_new_prompts_to_generate": num_new_prompts_to_generate,
            "num_to_prune_each_round": num_to_prune_each_round,
            "gen_new_prompt_round_frequency": gen_new_prompt_round_frequency,
            "max_concurrent_threads": max_concurrent_threads,
            # Allow YAML to set answer choices via optimization.answer_choices
            "answer_choices": kwargs.get("answer_choices", ["Yes", "No"]),
            # Shared ranking method for mutation and final selection
            "ranking_method": kwargs.get("ranking_method", "copeland"),
            # Task type and judge requirement (for open-ended tasks)
            "task_type": kwargs.get("task_type", "close_ended"),
            "judge_requirement": kwargs.get("judge_requirement"),
        }

        # Training and validation data (will be set by migrator)
        self.trainset = kwargs.get("trainset", [])
        self.valset = kwargs.get("valset", [])
        self.testset = kwargs.get("testset", [])

    def run(self, prompt_data: Dict[str, Any]) -> Any:
        """
        Execute PDO optimization using dueling bandits.

        Args:
            prompt_data: Dictionary containing prompt information
                - text: The prompt text to optimize
                - inputs: List of input field names
                - outputs: List of output field names

        Returns:
            DSPy program with optimized prompt for consistency with other strategies
        """
        if not self.task_model or not self.prompt_model:
            raise ValueError("Both task_model and prompt_model are required for PDO")

        # Display pre-optimization summary
        try:
            from .utils.summary_utils import create_and_display_summary

            create_and_display_summary(self, prompt_data)
        except Exception as e:
            logging.warning(f"Failed to create summary: {e}")
            print("Starting PDO optimization (summary creation failed)...")

        try:
            # Import PDO engine
            from .pdo.optimization_engine import PDOEngine

            # Debug: Print PDO config before engine creation
            print(f"Debug: PDO config: {self.pdo_config}")
            print(f"Debug: Task model type: {type(self.task_model)}")
            print(f"Debug: Prompt model type: {type(self.prompt_model)}")

            # Create PDO engine
            engine = PDOEngine(
                task_model=self.task_model,
                judge_model=self.prompt_model,  # Use prompt model for judging
                metric=self.metric,
                **self.pdo_config,
            )

            # Prepare examples and labels
            examples = []
            labels = []

            for example in self.trainset:
                # Extract input text
                input_text = ""
                for field in prompt_data.get("inputs", ["question"]):
                    if hasattr(example, field):
                        input_text += f"{getattr(example, field)}\n"
                examples.append(input_text.strip())

                # Extract expected output
                expected_output = ""
                for field in prompt_data.get("outputs", ["answer"]):
                    if hasattr(example, field):
                        expected_output = getattr(example, field)
                        break
                labels.append(expected_output)

            # Run PDO optimization
            print(
                f"Starting PDO optimization with {len(examples)} training examples..."
            )
            print(f"Task model: {self.task_model_name or 'Unknown'}")
            print(f"Judge model: {self.prompt_model_name or 'Unknown'}")

            best_instruction, metadata = engine.optimize(
                base_instruction=prompt_data["text"],
                examples=examples,
                labels=labels if self.pdo_config["use_labels"] else None,
            )

            # Create DSPy program with optimized instruction for consistency
            optimized_program = self._create_dspy_program(prompt_data, best_instruction)

            # Store PDO metadata
            optimized_program.pdo_metadata = metadata
            optimized_program.model_family = self.model_family

            print(f"✅ PDO optimization completed successfully!")
            print(
                f"Generated {metadata['total_instructions_generated']} total instructions"
            )
            print(f"Conducted {metadata['total_duels_conducted']} total duels")

            return optimized_program

        except Exception as e:
            logging.error(f"PDO optimization failed: {str(e)}")
            raise OptimizationError(f"PDO optimization failed: {str(e)}")

    def _create_dspy_program(self, prompt_data: Dict[str, Any], instruction: str):
        """Create DSPy program with optimized instruction."""
        # Create signature using consistent helper method
        signature = self._create_signature(prompt_data, instruction)

        # Create program instance with the signature
        program = dspy.Predict(signature)

        return program

    def _create_signature(self, prompt_data: Dict[str, Any], instructions: str):
        """Create DSPy signature with explicit field definitions."""
        # Create a signature class dynamically with proper field definitions
        input_fields = {}
        output_fields = {}

        # Define input and output fields based on prompt_data
        for field in prompt_data.get("inputs", ["question"]):
            input_fields[field] = dspy.InputField(desc="${" + field + "}")
        for field in prompt_data.get("outputs", ["answer"]):
            output_fields[field] = dspy.OutputField(desc="${" + field + "}")

        # Create the signature class with proper field definitions
        DynamicSignature = type(
            "DynamicSignature",
            (dspy.Signature,),
            {
                **input_fields,
                **output_fields,
                "__doc__": instructions,  # Store the instructions as the docstring
            },
        )

        return DynamicSignature
