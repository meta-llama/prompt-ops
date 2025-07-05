import atexit
import json
import logging
import os
import time
from contextlib import contextmanager

_LOG_SINGLETON: "LoggingManager|None" = None

DEFAULT_LEVEL = os.getenv("PROMPT_OPS_LOG_LEVEL", "INFO").upper()


class LoggingManager:
    def __init__(self, level=DEFAULT_LEVEL):
        self.logger = logging.getLogger("prompt_ops")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            fmt = "%(asctime)s | %(levelname)-7s | %(message)s"
            handler.setFormatter(logging.Formatter(fmt))
            self.logger.addHandler(handler)

        # Prevent propagation to root logger to avoid duplicate messages
        # This logger is designed for progress/telemetry, not general app logging
        self.logger.propagate = False

        self.set_level(level)

        self.timings: dict[str, float] = {}
        self.metrics: list[dict] = []

        atexit.register(self._dump_timings)  # convenience during CLI runs

    def __del__(self):
        # Unregister the atexit handler to prevent issues in testing
        try:
            atexit.unregister(self._dump_timings)
        except ValueError:
            # Handler might not be registered
            pass

    # ---- configuration --------------------------------------------------
    def set_level(self, level: str):
        self.logger.setLevel(level.upper())

    # ---- phase tracking --------------------------------------------------
    def start_phase(self, name: str):
        self.timings[name] = -time.perf_counter()

    def end_phase(self, name: str):
        if name not in self.timings:
            return
        self.timings[name] += time.perf_counter()
        self.logger.info(f"[{name}] completed in {self.timings[name]:.2f}s")

    @contextmanager
    def phase(self, name):
        self.start_phase(name)
        try:
            yield
        finally:
            self.end_phase(name)

    # ---- progress + metrics ---------------------------------------------
    def progress(self, msg: str, level: str = "INFO"):
        getattr(self.logger, level.lower())(msg)

    def log_metric(self, key: str, value, step: int | None = None):
        rec = {"key": key, "value": value, "step": step, "time": time.time()}
        self.metrics.append(rec)
        self.logger.debug(f"[metric] {key}={value} step={step}")

    # ---- export ----------------------------------------------------------
    def export_json(self, path: str):
        try:
            with open(path, "w") as f:
                json.dump(
                    {"timings": self.timings, "metrics": self.metrics}, f, indent=2
                )
        except Exception as e:
            self.logger.error(f"Failed to export telemetry to {path}: {str(e)}")

    def _dump_timings(self):
        # Called at program exit for insight in CLI runs
        if not self.timings:
            return

        # Check if any handlers have closed streams
        for handler in self.logger.handlers:
            if hasattr(handler, "stream") and hasattr(handler.stream, "closed"):
                if handler.stream.closed:
                    return  # Skip logging if stream is closed

        try:
            self.logger.info("=== Timings summary ===")
            for k, v in self.timings.items():
                self.logger.info(f"{k:<25} {v:6.2f}s")
        except (ValueError, AttributeError, OSError):
            # Stream might be closed during shutdown, ignore gracefully
            pass


def get_logger() -> LoggingManager:
    global _LOG_SINGLETON
    if _LOG_SINGLETON is None:
        _LOG_SINGLETON = LoggingManager()
    return _LOG_SINGLETON
