"""Plot a single map."""

import logging

from src.arma3_map_data import Arma3MapData
from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.setup import OUTPUT_PATH, SOURCE_DATA_PATH, setup_logging

MAP_NAME = "stratis"
LOG_LEVEL = "INFO"


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    OUTPUT_PATH.mkdir(exist_ok=True)
    map_data = Arma3MapData.from_data(SOURCE_DATA_PATH / MAP_NAME)
    if map_data:
        map_data.render_map(OUTPUT_PATH)


if __name__ == "__main__":
    main()
