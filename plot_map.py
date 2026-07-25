"""Plot a single map."""

import logging

from src.arma3_leaflet_map import Arma3LeafletMap
from src.arma3_map_data import Arma3MapData
from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.setup import INPUT_PATH, OUTPUT_PATH, setup_logging

MAP_NAME = "stratis"
LOG_LEVEL = "INFO"


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    map_data = Arma3MapData.from_data(INPUT_PATH / MAP_NAME)
    if not map_data:
        err_msg = f"Unexpected data issue with {INPUT_PATH / MAP_NAME}."
        raise RuntimeError(err_msg)

    map_ = Arma3LeafletMap(map_data)
    map_.render(OUTPUT_PATH)


if __name__ == "__main__":
    main()
