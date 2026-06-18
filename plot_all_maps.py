"""
Plot multiple maps.

NB: the source *.geojson.gz files are gzipped JSON arrays of GeoJSON features, not
GeoJSON compliant files.
"""

import logging

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from _setup import OUTPUT_PATH, SOURCE_DATA_PATH, setup_logging
from src.arma3_map_data import Arma3MapData
from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.plot import check_styles, plot_map
from src.supported_maps import SUPPORTED_MAPS

LOG_LEVEL = "INFO"


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    check_styles()
    source_dirs = sorted(SOURCE_DATA_PATH.iterdir())
    OUTPUT_PATH.mkdir(exist_ok=True)
    existing_plots = sorted(fp.stem for fp in list(OUTPUT_PATH.iterdir()))
    for map_name in existing_plots:
        log_msg = f"Map '{map_name}' already plotted - skipping."
        logger.warning(log_msg)

    dirs_to_plot = [
        fp
        for fp in source_dirs
        if fp.stem in SUPPORTED_MAPS and fp.stem not in existing_plots
    ]
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
                    map_data = Arma3MapData.from_data(fp)
                    if map_data:
                        plot_map(map_data=map_data, export_path=OUTPUT_PATH)

                    progress.update(task, advance=1)


if __name__ == "__main__":
    main()
