"""
Exceptions for the prompt migrator.

This module defines custom exceptions used throughout the prompt migrator.
"""


class OptimizationError(Exception):
    """Exception raised when prompt optimization fails."""
    pass


class EvaluationError(Exception):
    """Exception raised when evaluation fails."""
    pass


class DatasetError(Exception):
    """Exception raised when there's an issue with a dataset."""
    pass
