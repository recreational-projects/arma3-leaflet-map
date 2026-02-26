"""
TO DO.

NB: the source *.geojson.gz files are gzipped JSON arrays of GeoJSON features, not
GeoJSON compliant files.
"""

import logging
from pathlib import Path

from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from src.arma3_map_data import Arma3MapData
from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.plot import check_styles, plot_map

INPUT_DATA_RELATIVE_DIR = "../gruppe-adler/meh-data/"
OUTPUT_RELATIVE_DIR = "maps"
LOG_LEVEL = "INFO"


_LOG_FORMAT = "%(message)s"
logging.basicConfig(
    level=LOG_LEVEL,
    format=_LOG_FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)


def main() -> None:
    """Application entry point."""
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    check_styles()
    source_dirs = list(SOURCE_DATA_PATH.iterdir())
    PLOT_PATH.mkdir(exist_ok=True)
    existing_plots = [fp.stem for fp in list(PLOT_PATH.iterdir())]
    dirs_to_plot = [fp for fp in source_dirs if fp.stem not in existing_plots]

    for map_name in existing_plots:
        log_msg = f"Map '{map_name}' already plotted - skipping."
        logger.warning(log_msg)

    log_msg = f"{len(dirs_to_plot)} maps to plot."
    logger.info(log_msg)

    if dirs_to_plot:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            "maps |",
            TimeElapsedColumn(),
            "elapsed |",
            TimeRemainingColumn(),
            "remaining",
        )

        with progress:
            task = progress.add_task("Working...", total=len(dirs_to_plot))

            while not progress.finished:
                for fp in sorted(dirs_to_plot):
                    map_data = Arma3MapData.from_geo_json(fp)
                    if map_data:
                        plot_map(map_data=map_data, export_path=PLOT_PATH)

                    progress.update(task, advance=1)


if __name__ == "__main__":
    BASE_PATH = Path(__file__).resolve().parent
    SOURCE_DATA_PATH = BASE_PATH / INPUT_DATA_RELATIVE_DIR
    PLOT_PATH = BASE_PATH / OUTPUT_RELATIVE_DIR
    main()
