"""Common setup."""

import logging
from pathlib import Path

from rich.logging import RichHandler

_INPUT_DATA_RELATIVE_DIR = "../gruppe-adler/meh-data/"
_WORKING_RELATIVE_DIR = "working"
_OUTPUT_RELATIVE_DIR = "maps"
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
