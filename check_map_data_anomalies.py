"""
Report map metadata anomalies.

* `worldName` != directory name
* `elevationOffset` != 0
* `gridOffsetX` != 0
* `gridOffsetY` != `worldSize`
"""

import json
import logging

from src.setup import INPUT_PATH, setup_logging
from src.supported_maps import SUPPORTED_MAPS

CHECK_UNSUPPORTED_MAPS = True
LOG_LEVEL = "WARNING"


def main() -> None:
    """Script entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")

    source_dirs = INPUT_PATH.iterdir()
    if CHECK_UNSUPPORTED_MAPS:
        data_dirs = source_dirs
    else:
        data_dirs = [dir_ for dir_ in source_dirs if dir_.stem in SUPPORTED_MAPS]

    for dir_ in sorted(data_dirs):
        log_msg = f"Checking '{dir_.stem}'..."
        logger.info(log_msg)
        metadata_filepath = dir_ / "meta.json"
        if not metadata_filepath.is_file():
            logger.error("Missing 'meta.json' - skipping.")
            continue

        metadata_ = json.loads((dir_ / "meta.json").read_text())
        worldName = metadata_["worldName"]
        worldSize = metadata_["worldSize"]
        elevationOffset = metadata_["elevationOffset"]
        gridOffsetX = metadata_["gridOffsetX"]
        gridOffsetY = metadata_["gridOffsetY"]

        if worldName != dir_.stem:
            log_msg = f"'{worldName}' doesn't match dir stem '{dir_.stem}'"
            logger.warning(log_msg)

        if elevationOffset != 0:
            log_msg = f"'{worldName}': {elevationOffset=}"
            logger.warning(log_msg)

        if gridOffsetX != 0:
            log_msg = f"'{worldName}': {gridOffsetX=}"
            logger.warning(log_msg)

        if gridOffsetY != worldSize:
            log_msg = f"'{worldName}': {gridOffsetY=}, {worldSize=}"
            logger.warning(log_msg)


if __name__ == "__main__":
    main()
