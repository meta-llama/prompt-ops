# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Utility functions for extracting values from different object types.
"""

from typing import Any


def extract_value(obj: Any, key: str, default: Any = None) -> Any:
    """
    Extract a value from an object, handling different object types.

    This utility function provides a consistent way to extract values from:
    - DSPy Example objects (via outputs attribute)
    - Objects with direct attributes
    - Dictionary-like objects
    - Prediction objects (with text attribute)
    - Any object with string representation

    Args:
        obj: The object to extract from (can be a DSPy Example, dict, object, etc.)
        key: The key or attribute name to extract
        default: Default value if the key doesn't exist

    Returns:
        The extracted value or the default

    Examples:
        >>> # Extract from DSPy Example
        >>> example = dspy.Example(outputs={"answer": "42"})
        >>> extract_value(example, "answer")  # Returns "42"

        >>> # Extract from dictionary
        >>> data = {"answer": "42"}
        >>> extract_value(data, "answer")  # Returns "42"

        >>> # Extract from object with attribute
        >>> class Response:
        ...     answer = "42"
        >>> extract_value(Response(), "answer")  # Returns "42"
    """
    # Check for outputs attribute (DSPy Example objects)
    if hasattr(obj, "outputs") and hasattr(obj.outputs, "get"):
        value = obj.outputs.get(key)
        if value is not None:
            return value

    # Direct attribute access
    if hasattr(obj, key):
        return getattr(obj, key)

    # Dictionary access
    if isinstance(obj, dict) and key in obj:
        return obj[key]

    # Text attribute (Prediction objects)
    if hasattr(obj, "text"):
        return obj.text

    # Fallback to string representation
    if hasattr(obj, "__str__") and not isinstance(obj, (str, bytes, bytearray)):
        return str(obj)

    return default
