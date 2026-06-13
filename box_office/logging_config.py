"""Modest logging setup + a 5%-step progress helper."""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    fmt = "%(asctime)s %(levelname)-5s %(name)s | %(message)s"
    logging.basicConfig(level=level, format=fmt)


def log_progress(logger: logging.Logger, label: str, done: int, total: int,
                 step_pct: int = 5) -> None:
    """Log done/total only when crossing each step_pct boundary."""
    if total <= 0:
        return
    step = max(1, total * step_pct // 100)
    if done == total or done % step == 0:
        logger.info("%s %d/%d (%d%%)", label, done, total, done * 100 // total)
