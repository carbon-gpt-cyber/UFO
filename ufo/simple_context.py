"""Minimal context container for simplified helpers."""

from __future__ import annotations

import os
from typing import Any, Dict

from ufo.module.basic import BaseSession

# String keys used by the simplified context
LOG_PATH = "LOG_PATH"
LOGGER = "LOGGER"
REQUEST_LOGGER = "REQUEST_LOGGER"
EVALUATION_LOGGER = "EVALUATION_LOGGER"
APPLICATION_PROCESS_NAME = "APPLICATION_PROCESS_NAME"
APPLICATION_ROOT_NAME = "APPLICATION_ROOT_NAME"
APPLICATION_WINDOW = "APPLICATION_WINDOW"
SUBTASK = "SUBTASK"
REQUEST = "REQUEST"


class SimpleContext(dict):
    """A thin dictionary wrapper with helper ``get``/``set`` methods."""

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key, default)

    def set(self, key: str, value: Any) -> None:
        self[key] = value

    @classmethod
    def simple(
        cls,
        process_name: str,
        app_root_name: str,
        request: str = "",
        log_dir: str | None = None,
    ) -> "SimpleContext":
        """Create a pre-populated context with optional loggers."""

        context: "SimpleContext" = cls()

        if log_dir is not None:
            logger, req_logger, eval_logger = BaseSession.setup_basic_loggers(log_dir)
            context.set(LOG_PATH, os.path.join(log_dir, ""))
            context.set(LOGGER, logger)
            context.set(REQUEST_LOGGER, req_logger)
            context.set(EVALUATION_LOGGER, eval_logger)

        context.set(APPLICATION_PROCESS_NAME, process_name)
        context.set(APPLICATION_ROOT_NAME, app_root_name)
        context.set(SUBTASK, request)

        return context
