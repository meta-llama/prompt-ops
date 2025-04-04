"""
Debug module for DSPy's GroundedProposer to identify instruction proposal issues.

This module contains a wrapper around DSPy's GroundedProposer with enhanced logging
to help debug the 'NoneType' object is not subscriptable error.
"""

import logging
import traceback
import inspect
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_proposer")

class DebugGroundedProposer:
    """
    A wrapper around DSPy's GroundedProposer with enhanced logging.
    This class intercepts calls to the original proposer and adds detailed logging.
    """
    
    def __init__(self, original_proposer):
        """
        Initialize the debug wrapper with the original proposer.
        
        Args:
            original_proposer: The original DSPy GroundedProposer instance
        """
        self.original_proposer = original_proposer
        self.logger = logger
        
        # Wrap the propose_instructions_for_program method
        self.original_propose = original_proposer.propose_instructions_for_program
        original_proposer.propose_instructions_for_program = self.debug_propose_instructions_for_program
        
        # Wrap the propose_instruction_for_predictor method
        self.original_propose_for_predictor = original_proposer.propose_instruction_for_predictor
        original_proposer.propose_instruction_for_predictor = self.debug_propose_instruction_for_predictor
    
    def debug_propose_instructions_for_program(self, *args, **kwargs):
        """
        Wrapped version of propose_instructions_for_program with detailed logging.
        """
        self.logger.info("Starting propose_instructions_for_program with enhanced debugging")
        
        # Log the arguments
        arg_names = inspect.getfullargspec(self.original_propose).args
        if len(arg_names) > len(args):
            arg_names = arg_names[1:len(args)+1]  # Skip 'self'
        
        for i, arg_name in enumerate(arg_names):
            if arg_name == 'trainset':
                self.logger.info(f"trainset: {type(args[i])} with {len(args[i])} examples")
                if len(args[i]) > 0:
                    self.logger.info(f"First example: {args[i][0]}")
            elif arg_name == 'program':
                self.logger.info(f"program: {type(args[i])}")
                self.logger.info(f"program predictors: {[p.__class__.__name__ for p in args[i].predictors()]}")
            elif arg_name == 'demo_candidates':
                if args[i] is None:
                    self.logger.warning("demo_candidates is None")
                else:
                    self.logger.info(f"demo_candidates: {type(args[i])} with {len(args[i])} candidates")
            else:
                self.logger.info(f"{arg_name}: {args[i]}")
        
        for k, v in kwargs.items():
            self.logger.info(f"kwarg {k}: {v}")
        
        try:
            # Call the original method
            self.logger.info("Calling original propose_instructions_for_program")
            result = self.original_propose(*args, **kwargs)
            
            # Log the result
            if result is None:
                self.logger.error("Result is None!")
            else:
                self.logger.info(f"Result type: {type(result)}")
                self.logger.info(f"Result keys: {result.keys() if hasattr(result, 'keys') else 'No keys'}")
            
            return result
        except Exception as e:
            self.logger.error(f"Error in propose_instructions_for_program: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Try to identify the specific issue
            if "'NoneType' object is not subscriptable" in str(e):
                self.logger.error("Found 'NoneType' object is not subscriptable error")
                
                # Check demo_candidates
                if 'demo_candidates' in kwargs and kwargs['demo_candidates'] is None:
                    self.logger.error("demo_candidates is None, which might be causing the error")
                elif len(args) > 2 and args[2] is None:
                    self.logger.error("args[2] (demo_candidates) is None, which might be causing the error")
                
                # Check trainset
                if 'trainset' in kwargs:
                    trainset = kwargs['trainset']
                    if trainset is None:
                        self.logger.error("trainset is None")
                    elif len(trainset) == 0:
                        self.logger.error("trainset is empty")
                    else:
                        self.logger.info(f"trainset example structure: {trainset[0].__dict__ if hasattr(trainset[0], '__dict__') else trainset[0]}")
                
                # Create a fallback empty result
                self.logger.info("Creating fallback empty result")
                program = args[1] if len(args) > 1 else kwargs.get('program')
                if program:
                    result = {}
                    for i, pred in enumerate(program.predictors()):
                        result[i] = [getattr(pred, 'instructions', "")]
                    return result
            
            # Re-raise the exception
            raise
    
    def debug_propose_instruction_for_predictor(self, *args, **kwargs):
        """
        Wrapped version of propose_instruction_for_predictor with detailed logging.
        """
        self.logger.info("Starting propose_instruction_for_predictor with enhanced debugging")
        
        # Log the arguments
        arg_names = inspect.getfullargspec(self.original_propose_for_predictor).args
        if len(arg_names) > len(args):
            arg_names = arg_names[1:len(args)+1]  # Skip 'self'
        
        for i, arg_name in enumerate(arg_names):
            if arg_name == 'demo_candidates':
                if args[i] is None:
                    self.logger.warning("demo_candidates is None")
                else:
                    self.logger.info(f"demo_candidates: {type(args[i])}")
            else:
                self.logger.info(f"{arg_name}: {args[i]}")
        
        for k, v in kwargs.items():
            self.logger.info(f"kwarg {k}: {v}")
        
        try:
            # Call the original method
            self.logger.info("Calling original propose_instruction_for_predictor")
            result = self.original_propose_for_predictor(*args, **kwargs)
            
            # Log the result
            if result is None:
                self.logger.error("Result is None!")
            else:
                self.logger.info(f"Result: {result[:100]}...")
            
            return result
        except Exception as e:
            self.logger.error(f"Error in propose_instruction_for_predictor: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Create a fallback empty result
            self.logger.info("Creating fallback empty instruction")
            return "Fallback instruction due to error"


def patch_dspy_proposer():
    """
    Patch the DSPy GroundedProposer class to use our debug wrapper.
    This function should be called before using DSPy's MIPROv2 optimizer.
    """
    try:
        import dspy
        from dspy.propose.grounded_proposer import GroundedProposer
        
        # Store the original __init__ method
        original_init = GroundedProposer.__init__
        
        # Define a new __init__ method that wraps the original
        def new_init(self, *args, **kwargs):
            # Call the original __init__
            original_init(self, *args, **kwargs)
            
            # Wrap this instance with our debug wrapper
            DebugGroundedProposer(self)
        
        # Replace the __init__ method
        GroundedProposer.__init__ = new_init
        
        logger.info("Successfully patched DSPy's GroundedProposer")
        return True
    except ImportError:
        logger.error("Failed to import DSPy, cannot patch GroundedProposer")
        return False
    except Exception as e:
        logger.error(f"Error patching DSPy's GroundedProposer: {str(e)}")
        logger.error(traceback.format_exc())
        return False
