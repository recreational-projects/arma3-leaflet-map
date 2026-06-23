"""Common setup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.logging import RichHandler

from src import styles
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Sequence

_LOGGER = logging.getLogger(__name__)

_INPUT_DATA_RELATIVE_DIR = "../../gruppe-adler/meh-data/"
_WORKING_RELATIVE_DIR = "../working"
_OUTPUT_RELATIVE_DIR = "../maps"
_BASE_PATH = Path(__file__).resolve().parent

SOURCE_DATA_PATH = _BASE_PATH / _INPUT_DATA_RELATIVE_DIR
WORKING_PATH = _BASE_PATH / _WORKING_RELATIVE_DIR
OUTPUT_PATH = _BASE_PATH / _OUTPUT_RELATIVE_DIR


def setup_logging(level: str) -> None:
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
