# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Utility modules for prompt optimization.
"""
import logging

# --- Enhanced Optimizer Logging Setup ---
# Get the dedicated optimizer trace logger
optimizer_trace_logger = logging.getLogger("llama_prompt_ops.optimizer_trace")

# Set default logging level for this logger during development.
# This will be controlled by optimizer_log_level from config/CLI later.
if not optimizer_trace_logger.handlers: # Avoid adding handlers multiple times
    optimizer_trace_logger.setLevel(logging.DEBUG)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    
    # Optional: Create a formatter and set it for the handler
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    optimizer_trace_logger.addHandler(console_handler)
    
    # Prevent the logger from propagating messages to the root logger if it's not desired
    # optimizer_trace_logger.propagate = False 
# --- End Enhanced Optimizer Logging Setup ---


from .strategy_utils import map_auto_mode_to_dspy
from .format_utils import convert_json_to_yaml, json_to_yaml_file
# It's good practice to also export the logger if it's intended to be used by other modules directly via this __init__
# However, modules can also get it by name: logging.getLogger("llama_prompt_ops.optimizer_trace")
# For now, not adding to __all__ unless explicitly needed.

__all__ = [
    'map_auto_mode_to_dspy',
    'convert_json_to_yaml',
    'json_to_yaml_file',
    # 'optimizer_trace_logger', # Uncomment if direct import from utils is desired
]
