"""
Render multiple maps.

By default, only supported maps are rendered.
Edit `config.toml` so that `process_unsupported_maps = true` to override.
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

from src.arma3_map_data import Arma3MapData
from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.setup import INPUT_PATH, OUTPUT_PATH, PROCESS_UNSUPPORTED_MAPS, setup_logging
from src.supported_maps import SUPPORTED_MAPS

LOG_LEVEL = "INFO"


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    source_dirs = sorted(INPUT_PATH.iterdir())
    if PROCESS_UNSUPPORTED_MAPS:
        data_dirs = source_dirs
    else:
        data_dirs = [dir_ for dir_ in source_dirs if dir_.stem in SUPPORTED_MAPS]

    existing_plots = {fp.stem for fp in OUTPUT_PATH.iterdir()}
    dirs_to_plot = []
    for fp in data_dirs:
        if fp.stem in existing_plots:
            log_msg = f"'{fp.stem}' already plotted - skipping."
            logger.warning(log_msg)
        else:
            dirs_to_plot.append(fp)

    log_msg = f"{len(dirs_to_plot)} maps to plot."
    logger.info(log_msg)

    if dirs_to_plot:
        OUTPUT_PATH.mkdir(exist_ok=True)
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
                        map_data.render_map(OUTPUT_PATH)

                    progress.update(task, advance=1)


if __name__ == "__main__":
    main()
