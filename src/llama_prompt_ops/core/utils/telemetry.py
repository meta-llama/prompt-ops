# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
Telemetry module for tracking and displaying optimization process information.

This module provides classes and utilities for collecting and displaying
key information about the optimization process before it begins.
"""

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from .logging import get_logger


@dataclass
class PreOptimizationSummary:
    """
    Container for pre-optimization summary information.

    This class collects and formats key information about the optimization
    process that will be displayed to users before optimization begins.
    """

    task_model: str
    proposer_model: str
    metric_name: str
    train_size: int
    val_size: int
    mipro_params: Dict[str, Any]
    guidance: Optional[str] = None
    baseline_score: Optional[float] = None

    def to_pretty(self) -> str:
        """
        Format the summary as a human-readable string.

        Returns:
            A formatted string suitable for console display
        """
        pad = " " * 4
        lines = [
            "=== Pre-Optimization Summary ===",
            f"{pad}Task Model       : {self.task_model}",
            f"{pad}Proposer Model   : {self.proposer_model}",
            f"{pad}Metric           : {self.metric_name}",
            f"{pad}Train / Val size : {self.train_size} / {self.val_size}",
            f"{pad}MIPRO Params     : {json.dumps(self.mipro_params, separators=(',', ':'))}",
        ]

        if self.guidance:
            # Truncate guidance for readability
            guidance_display = self.guidance[:120]
            if len(self.guidance) > 120:
                guidance_display += "..."
            lines.append(f"{pad}Guidance         : {guidance_display}")

        if self.baseline_score is not None:
            lines.append(f"{pad}Baseline score   : {self.baseline_score:.4f}")

        return "\n".join(lines)

    def to_json(self) -> str:
        """
        Convert the summary to JSON format.

        Returns:
            JSON string representation of the summary
        """
        return json.dumps(asdict(self), indent=2)

    def log(self) -> None:
        """
        Log the summary using the configured logger.

        This method outputs the formatted summary at INFO level.
        """
        logger = get_logger()
        logger.progress(self.to_pretty())
