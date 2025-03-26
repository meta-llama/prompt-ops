"""
Dataset modules for the prompt migrator.

This package contains dataset-specific modules, each with adapters and metrics
designed for specific dataset types.
"""

# Import adapters and metrics for easy access
try:
    from prompt_ops.datasets.facility import FacilityAdapter, FacilityMetric
except ImportError:
    pass
