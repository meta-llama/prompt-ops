# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Utility functions for JSON parsing and manipulation.
"""

import json
import re


def parse_json(input_string: str):
    """
    Parse JSON with fallback to extract from code blocks.

    Attempts to parse the given string as JSON. If direct parsing fails,
    it tries to extract a JSON snippet from code blocks formatted as:
        ```json
        ... JSON content ...
        ```
    or any code block delimited by triple backticks and then parses that content.

    Args:
        input_string (str): The input string which may contain JSON.

    Returns:
        The parsed JSON object.

    Raises:
        json.JSONDecodeError: If parsing fails even after attempting to extract
                             a JSON snippet from code blocks.
    """
    # Try to parse the string directly
    try:
        return json.loads(input_string)
    except json.JSONDecodeError as err:
        # Try extracting from code blocks
        patterns = [
            re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),
            re.compile(r"```(.*?)```", re.DOTALL),
        ]
        for pattern in patterns:
            match = pattern.search(input_string)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue
        # If all attempts fail, raise the original error
        raise err
