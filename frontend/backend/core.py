"""
Shared core imports and availability checks for the backend.

This module centralizes the prompt-ops import logic to avoid duplication
across multiple backend modules.
"""

import logging

logger = logging.getLogger(__name__)

# Check for prompt-ops availability
try:
    from prompt_ops.core.datasets import ConfigurableJSONAdapter
    from prompt_ops.core.metrics import DSPyMetricAdapter
    from prompt_ops.core.migrator import PromptMigrator
    from prompt_ops.core.model import setup_model
    from prompt_ops.core.prompt_strategies import BasicOptimizationStrategy

    PROMPT_OPS_AVAILABLE = True
    logger.info("✓ prompt_ops core modules loaded successfully")
except ImportError as e:
    # Set all to None when not available
    ConfigurableJSONAdapter = None
    DSPyMetricAdapter = None
    PromptMigrator = None
    setup_model = None
    BasicOptimizationStrategy = None

    PROMPT_OPS_AVAILABLE = False
    logger.warning(f"⚠ Could not import prompt_ops: {e}")
    logger.warning("Some features may not work without prompt_ops installed")

__all__ = [
    "PROMPT_OPS_AVAILABLE",
    "ConfigurableJSONAdapter",
    "DSPyMetricAdapter",
    "PromptMigrator",
    "setup_model",
    "BasicOptimizationStrategy",
]
