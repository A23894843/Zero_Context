"""
Centralized application logging.

This is distinct from engine/logger.py's Telemetry_Logger, which writes
structured ML feature vectors (JSONL) for model training. This module
configures human-readable runtime/error/security logs with rotation,
replacing scattered print() calls throughout the codebase.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir, level=logging.INFO):
    """Configures the root logger with a rotating file handler + console output.

    Call this once, early, from each entrypoint (main.py, dashboard.py,
    engine/train_pipeline.py when run standalone).
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "zero_context.log")

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if setup_logging() is called more than once
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return root
