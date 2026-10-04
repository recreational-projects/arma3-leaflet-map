"""Plot a single map."""

import argparse
import logging

from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.model.arma3_leaflet_map import Arma3LeafletMap
from src.model.arma3_map_data import Arma3MapData
from src.setup import INPUT_PATH, OUTPUT_PATH, setup_logging

LOG_LEVEL = "INFO"


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    parser = argparse.ArgumentParser()
    parser.add_argument("map_name")
    args = parser.parse_args()

    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    map_data_dir = INPUT_PATH / args.map_name
    if not map_data_dir.is_dir():
        err_msg = f"{map_data_dir} is not a directory."
        raise RuntimeError(err_msg)

    map_data = Arma3MapData.from_data(INPUT_PATH / args.map_name)
    if not map_data:
        err_msg = f"Unexpected data issue with {INPUT_PATH / args.map_name}."
        raise RuntimeError(err_msg)

    map_ = Arma3LeafletMap(map_data)
    map_.render(OUTPUT_PATH)


if __name__ == "__main__":
    main()
