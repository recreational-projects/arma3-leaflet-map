"""
Plot a map.

NB: the source *.geojson.gz files are gzipped JSON arrays of GeoJSON features, not
GeoJSON compliant files.
"""

import logging

from _setup import OUTPUT_PATH, SOURCE_DATA_PATH, setup_logging
from src.arma3_map_data import Arma3MapData
from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.plot import check_styles, plot_map

MAP_NAME = "stratis"
LOG_LEVEL = "INFO"


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    check_styles()
    OUTPUT_PATH.mkdir(exist_ok=True)
    map_data = Arma3MapData.from_data(SOURCE_DATA_PATH / MAP_NAME)
    if map_data:
        plot_map(map_data=map_data, export_path=OUTPUT_PATH)


if __name__ == "__main__":
    main()
