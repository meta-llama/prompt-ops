# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Exceptions for the prompt-ops tool.

This module defines custom exceptions used throughout the prompt-ops tool.
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
