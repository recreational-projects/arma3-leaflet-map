"""Common setup."""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.logging import RichHandler

from src import styles
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Sequence

_LOGGER = logging.getLogger(__name__)

_BASE_PATH = Path(__file__).resolve().parent


def setup_logging(level: str) -> None:
    """Configure logging for scripts."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )


def check_styles() -> None:
    """TO DO."""
    icon_names = [
        style.icon_name
        for style in styles.POINT_STYLES.values()
        if hasattr(style, "icon_name")
    ]
    duplicate_icon_names = _duplicates(icon_names)
    if duplicate_icon_names:
        log_msg = f"Non-unique icons: {format_iterable_of_str(duplicate_icon_names)}"
        _LOGGER.warning(log_msg)


def _duplicates(seq: Sequence[Any]) -> set[Any]:
    """Return duplicate elements from `seq`."""
    seen = set()
    return {val for val in seq if (val in seen or seen.add(val))}


with (_BASE_PATH / "../config.toml").open(mode="rb") as f:
    config = tomllib.load(f)
    INPUT_PATH = _BASE_PATH / config["input_relative_dir"]
    WORKING_PATH = _BASE_PATH / config["working_relative_dir"]
    OUTPUT_PATH = _BASE_PATH / config["output_relative_dir"]
    PROCESS_UNSUPPORTED_MAPS = config["process_unsupported_maps"]

WORKING_PATH.mkdir(exist_ok=True)
OUTPUT_PATH.mkdir(exist_ok=True)
