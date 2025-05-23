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
from .utils.logging_wrappers import LoggingLM # Added for LoggingLM
import sys
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
import dspy
from typing_extensions import Literal

from .utils import map_auto_mode_to_dspy

# Get the dedicated optimizer trace logger
optimizer_trace_logger = logging.getLogger("llama_prompt_ops.optimizer_trace")

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
        num_threads: int = 36,
        model_family: str = None
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
        

        if model_family is None:
            from .utils.llama_utils import is_llama_model
            if is_llama_model(model_name):
                self.model_family = "llama"
            else:
                # Default to Llama since that's our focus
                optimizer_trace_logger.warning(f"Model '{model_name}' does not appear to be a Llama model. " # Changed to optimizer_trace_logger
                                               f"This library is optimized for Llama models.")
                self.model_family = "llama"
        else:
            # If model_family is explicitly provided, use it but warn if not 'llama'
            self.model_family = model_family
            if self.model_family != "llama":
                optimizer_trace_logger.warning(f"Model family '{self.model_family}' specified, but this library " # Changed to optimizer_trace_logger
                                               f"is optimized for Llama models.")
    
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
        num_threads: int = 36,
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
        use_llama_tips: bool = True,
        requires_permission_to_run: bool = False,
        **kwargs
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
            provide_traceback: Whether to provide tracebacks for errors
            
            **kwargs: Additional configuration parameters
        """
        super().__init__(model_name, metric, num_threads, model_family)
        
        # Store task and prompt models
        self.task_model = kwargs.get('task_model')
        self.prompt_model = kwargs.get('prompt_model')
        
        # Training and validation data
        self.trainset = kwargs.get('trainset', [])
        self.valset = kwargs.get('valset', [])
        
        # Model-specific optimization settings
        self.use_llama_tips = use_llama_tips
        
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
        
        if 'dspy' not in globals() or not self.trainset:
            optimizer_trace_logger.warning("DSPy not available or trainset empty. Skipping optimization.") # Changed to optimizer_trace_logger
            return f"[Optimized for {self.model_name}] {text}"
        
        optimizer_trace_logger.info("--- Starting Pre-optimization Phase ---")
        optimizer_trace_logger.info(f"Task Model: {self.task_model}")
        optimizer_trace_logger.info(f"Proposer Model: {self.prompt_model}")
        optimizer_trace_logger.info(f"Metric: {self.metric.__class__.__name__}") # Corrected to always use class name
        baseline_score = prompt_data.get('baseline_score')
        optimizer_trace_logger.info(f"Baseline Score: {baseline_score if baseline_score is not None else 'N/A'}")
        optimizer_trace_logger.info(f"Trainset Size: {len(self.trainset) if self.trainset else 0}")
        optimizer_trace_logger.info(f"Validation Set Size: {len(self.valset) if self.valset else 0}")

        optimizer_trace_logger.debug("MIPROv2 Parameters:")
        optimizer_trace_logger.debug(f"  Auto Mode: {self.auto} (DSPy mode: {map_auto_mode_to_dspy(self.auto)})")
        optimizer_trace_logger.debug(f"  Num Candidates: {self.num_candidates}")
        optimizer_trace_logger.debug(f"  Max Bootstrapped Demos: {self.max_bootstrapped_demos}")
        optimizer_trace_logger.debug(f"  Max Labeled Demos: {self.max_labeled_demos}")
        optimizer_trace_logger.debug(f"  Num Trials: {self.num_trials if self.num_trials is not None else 'Auto-determined'}")
        optimizer_trace_logger.debug(f"  Initial Temperature: {self.init_temperature}")
        optimizer_trace_logger.debug(f"  Seed: {self.seed}")
        
        try:
            # Add model-specific tips to the prompt if enabled
            model_tips = None
            if self.use_llama_tips:
                # Check if model_tips are already in prompt_data
                if "model_tips" in prompt_data:
                    model_tips = prompt_data["model_tips"]
                else:
                    # Import here to avoid circular imports
                    from .utils.llama_utils import get_llama_tips
                    model_tips = get_llama_tips()
                    
            # Incorporate model-specific tips into the prompt if available
            if model_tips and isinstance(model_tips, dict):
                # Add model-specific formatting tips to the prompt
                if "formatting" in model_tips:
                    text += f"\n\nFormatting Tip: {model_tips['formatting']}"
                
                # Add reasoning tips for complex tasks
                if "reasoning" in model_tips and any(field in prompt_data.get('inputs', []) for field in ["context", "document", "text"]):
                    text += f"\n\nReasoning Tip: {model_tips['reasoning']}"
                
                # Add constraint tips if output format is important
                if "constraints" in model_tips:
                    text += f"\n\nOutput Requirements: {model_tips['constraints']}"
                    
            # Update the prompt text in prompt_data
            prompt_data["text"] = text
            # Create a signature class dynamically with proper field definitions
            input_fields = {}
            output_fields = {}
            
            # Define input and output fields based on prompt_data
            for field in prompt_data.get('inputs', ['question']):
                input_fields[field] = dspy.InputField(desc="${" + field + "}")
            for field in prompt_data.get('outputs', ['answer']):
                output_fields[field] = dspy.OutputField(desc="${" + field + "}")
                
            # Create the signature class with proper field definitions
            DynamicSignature = type('DynamicSignature', (dspy.Signature,), {
                **input_fields,
                **output_fields,
                '__doc__': text  # Store the instructions as the docstring
            })
            
            # Create program instance with the signature
            program = dspy.Predict(DynamicSignature)
            
            # Map our naming convention to DSPy's expected values
            dspy_auto_mode = map_auto_mode_to_dspy(self.auto)
            
            # Extract the underlying DSPy model if we have model adapters
            # And wrap the prompt_model with LoggingLM
            task_model_to_use = self.task_model
            if hasattr(task_model_to_use, '_model'): # Handle DSPyModelAdapter
                task_model_to_use = task_model_to_use._model

            prompt_model_to_use = self.prompt_model
            if hasattr(prompt_model_to_use, '_model'): # Handle DSPyModelAdapter
                prompt_model_to_use = prompt_model_to_use._model
            
            if not isinstance(prompt_model_to_use, LoggingLM): # Avoid double-wrapping
                optimizer_trace_logger.debug(f"Wrapping prompt_model ({type(prompt_model_to_use)}) with LoggingLM.")
                prompt_model_to_use = LoggingLM(wrapped_lm=prompt_model_to_use)
            else:
                optimizer_trace_logger.debug(f"prompt_model ({type(prompt_model_to_use)}) is already a LoggingLM instance.")

            # Configure the optimizer with all parameters
            # Ensure DSPy's internal verbose is False to let our logger take precedence
            optimizer = dspy.MIPROv2(
                metric=self.metric,
                prompt_model=prompt_model_to_use, # Use the wrapped model
                task_model=task_model_to_use,
                max_bootstrapped_demos=self.max_bootstrapped_demos,
                max_labeled_demos=self.max_labeled_demos,
                auto=dspy_auto_mode,  # Use the mapped value
                num_candidates=self.num_candidates,
                num_threads=self.num_threads,
                max_errors=self.max_errors,
                seed=self.seed,
                init_temperature=self.init_temperature,
                verbose=False,  # Force DSPy's verbosity off for our logger
                track_stats=self.track_stats, # Keep track_stats as per user config
                log_dir=self.log_dir, # Keep log_dir as per user config
                metric_threshold=self.metric_threshold
            )
            
            # Initialize proposer_kwargs if not already present
            optimizer.proposer_kwargs = getattr(optimizer, 'proposer_kwargs', {}) or {}
            
            # Logic for setting tip (remains largely the same, just logging changes)
            proposer_tip_to_log = "None"
            if hasattr(self, 'proposer_kwargs') and self.proposer_kwargs and 'tip' in self.proposer_kwargs:
                optimizer.proposer_kwargs['tip'] = self.proposer_kwargs['tip']
                proposer_tip_to_log = self.proposer_kwargs['tip']
                optimizer_trace_logger.debug(f"Using custom instruction tip for proposer: {proposer_tip_to_log}")
            elif model_tips:
                if 'persona' in model_tips or 'examples' in model_tips:
                    persona_tip = model_tips.get('persona', '')
                    examples_tip = model_tips.get('examples', '')
                    combined_tip = f"{persona_tip} {examples_tip}".strip()
                    if combined_tip:
                        optimizer.proposer_kwargs['tip'] = combined_tip
                        proposer_tip_to_log = combined_tip
                        optimizer_trace_logger.debug(f"Using model-specific tip for proposer: {proposer_tip_to_log}")
            if proposer_tip_to_log == "None":
                 optimizer_trace_logger.debug("No specific tip provided to instruction proposer.")


            optimizer_trace_logger.info(f"--- Starting Instruction Proposal Phase ---")
            optimizer_trace_logger.info(f"MIPROv2 using {self.max_labeled_demos} labeled demos, {self.max_bootstrapped_demos} bootstrapped demos with {self.num_threads} threads.")
            optimizer_trace_logger.info(f"Compiling program with {len(self.trainset)} training examples and {len(self.valset) if self.valset else 0} validation examples.")
            actual_num_trials = self.num_trials if self.num_trials is not None else "auto-determined based on 'auto' mode"
            optimizer_trace_logger.info(f"Number of optimization trials: {actual_num_trials}.")
            
            # Create a custom compile method that injects our tip directly (existing logic, ensure logging uses optimizer_trace_logger)
            original_propose_instructions = None
            if hasattr(self, 'proposer_kwargs') and self.proposer_kwargs and 'tip' in self.proposer_kwargs:
                from dspy.propose.grounded_proposer import GroundedProposer
                original_propose_instructions = GroundedProposer.propose_instructions_for_program
                
                def custom_propose_instructions(self_proposer, *args, **kwargs): # Renamed self to self_proposer
                    optimizer_trace_logger.debug("Starting custom_propose_instructions (tip injection wrapper)")
                    try:
                        if len(args) >= 3:
                            trainset_arg, program_arg, _ = args[0], args[1], args[2]
                            optimizer_trace_logger.debug(f"Proposer Trainset size: {len(trainset_arg) if trainset_arg else 0}, Program type: {type(program_arg)}")
                        
                        custom_tip_val = optimizer.proposer_kwargs.get('tip')
                        if custom_tip_val:
                            optimizer_trace_logger.debug(f"Injecting custom tip into proposer: {custom_tip_val[:100]}...")
                            kwargs['tip'] = custom_tip_val
                        
                        result = original_propose_instructions(self_proposer, *args, **kwargs)
                        if result is None: optimizer_trace_logger.error("Instruction proposer (custom_propose_instructions) returned None")
                        return result
                    except Exception as e_proposer:
                        optimizer_trace_logger.error(f"Error in custom_propose_instructions: {str(e_proposer)}", exc_info=True)
                        if len(args) >= 2:
                            program_arg = args[1]
                            fallback_result = {i: [getattr(pred, 'instructions', "Default instruction due to proposer error")] for i, pred in enumerate(program_arg.predictors())}
                            optimizer_trace_logger.info("Created fallback instructions after proposer exception.")
                            return fallback_result
                        raise
                GroundedProposer.propose_instructions_for_program = custom_propose_instructions
            
            # Debug patch logic (existing, ensure logging uses optimizer_trace_logger)
            try:
                from llama_prompt_ops.debug import patch_dspy_proposer
                debug_patched = patch_dspy_proposer()
                if debug_patched: optimizer_trace_logger.debug("Successfully applied debug wrapper to GroundedProposer")
                else: optimizer_trace_logger.warning("Failed to apply debug wrapper to GroundedProposer")
            except ImportError:
                optimizer_trace_logger.warning("Debug module not available, continuing without enhanced proposer debugging")
            
            optimized_program = None
            try:
                optimizer_trace_logger.info("Calling optimizer.compile...")
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
                    provide_traceback=True
                )
                optimizer_trace_logger.info("Optimizer.compile completed.")
            except TypeError as e_compile:
                if "'NoneType' object is not subscriptable" in str(e_compile):
                    optimizer_trace_logger.error(f"Error in MIPROv2 compile (likely instruction proposal phase): {str(e_compile)}", exc_info=True)
                    optimizer_trace_logger.error("This typically occurs if the instruction proposer fails. Check dataset format, data quantity, or API errors during proposal.")
                    optimized_program = None # Ensure it's None for fallback
                else:
                    optimizer_trace_logger.error(f"Unexpected TypeError during optimization: {str(e_compile)}", exc_info=True)
                    raise
            except Exception as e_compile_generic:
                optimizer_trace_logger.error(f"Generic error during optimization: {str(e_compile_generic)}", exc_info=True)
                raise
            finally:
                if original_propose_instructions:
                    GroundedProposer.propose_instructions_for_program = original_propose_instructions
                    optimizer_trace_logger.debug("Restored original GroundedProposer.propose_instructions_for_program.")
            
            optimizer_trace_logger.info("--- Starting Post-optimization Phase ---")
            if hasattr(self, 'model_family') and optimized_program is not None:
                setattr(optimized_program, 'model_family', self.model_family)
            
            if optimized_program is None:
                optimizer_trace_logger.warning("Optimizer returned None or failed. Falling back to original prompt structure.")
                fallback_program = program # program has the original/Llama-tipped prompt
                setattr(fallback_program, 'is_fallback', True)
                setattr(fallback_program, 'model_family', self.model_family)
                optimizer_trace_logger.info(f"Final selected prompt (fallback): {fallback_program.signature.instructions}")
                return fallback_program
            
            final_instructions = "Error retrieving final instructions"
            try:
                # For dspy.Predict, instructions are in program.signature.instructions
                if hasattr(optimized_program, 'signature') and hasattr(optimized_program.signature, 'instructions'):
                    final_instructions = optimized_program.signature.instructions
                # If it's a more complex program, it might be nested. This is a simple case.
                # For MultiChain, it would be program.predictors()[0].signature.instructions, etc.
            except Exception as e_instr:
                optimizer_trace_logger.error(f"Could not extract final instructions: {e_instr}")

            optimizer_trace_logger.info(f"Optimization process finished.")
            optimizer_trace_logger.info(f"Final selected prompt: {final_instructions}")
            
            # DSPy's MIPROv2 logs its own "Best score so far" and "Returning best identified program with score X"
            # The `optimizer.best_score` attribute might not always reflect the final reported score immediately
            # or in the way we expect. Relying on DSPy's own logs for this is currently more robust.
            # best_score_val = getattr(optimizer, 'best_score', 'N/A')
            # if best_score_val != 'N/A' and isinstance(best_score_val, float):
            #      best_score_val = f"{best_score_val:.4f}"
            # optimizer_trace_logger.info(f"Best score achieved (via optimizer_trace_logger): {best_score_val}")
            
            # The optimizer.history attribute did not yield easily parseable per-trial scores.
            # DSPy's own INFO logs (e.g., "Scores so far: [...]") provide this information.
            optimizer_trace_logger.debug("DSPy's internal INFO logs should show per-trial scores if global log level permits.")

            return optimized_program
            
        except Exception as e_outer:
            optimizer_trace_logger.error(f"Outer error in optimization run: {str(e_outer)}", exc_info=True)
            raise OptimizationError(f"Optimization failed: {str(e_outer)}")
