"""Report map metadata anomalies."""

import logging

from arma3_offline_map_lib.grad_meh.metadata import Metadata

from src.setup import INPUT_PATH, PROCESS_UNSUPPORTED_MAPS, setup_logging
from src.supported_maps import SUPPORTED_MAPS

LOG_LEVEL = "WARNING"


def main() -> None:
    """Script entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")

    source_dirs = INPUT_PATH.iterdir()
    if PROCESS_UNSUPPORTED_MAPS:
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

        metadata = Metadata.from_file(metadata_filepath)
        world_name_ = metadata.world_name
        elevation_offset_ = metadata.elevation_offset
        grid_offset_ = metadata.grid_offset
        world_size_ = metadata.world_size

        if world_name_ != dir_.stem:
            log_msg = f"'{world_name_}' doesn't match dir stem '{dir_.stem}'"
            logger.warning(log_msg)

        if elevation_offset_ != 0:
            log_msg = (
                f"'{world_name_}': non-zero `elevationOffset` ({elevation_offset_})"
            )
            logger.warning(log_msg)

        if grid_offset_.x != 0:
            log_msg = f"'{world_name_}': non-zero `gridOffsetX` ({grid_offset_.x})"
            logger.warning(log_msg)

        if grid_offset_.y != world_size_:
            log_msg = (
                f"'{world_name_}': "
                f"`gridOffsetY` ({grid_offset_.y}) != `worldSize` ({world_size_})"
            )
            logger.warning(log_msg)

        if not (dir_ / "preview.png").is_file():
            log_msg = f"'{world_name_}': missing preview image."
            logger.warning(log_msg)

        if (dir_ / "geojson" / "roads" / "hide.geojson.gz").is_file():
            log_msg = f"'{world_name_}': has hidden roads"
            logger.warning(log_msg)

        if (dir_ / "geojson" / "river.geojson.gz").is_file():
            log_msg = f"'{world_name_}': has river"
            logger.warning(log_msg)


if __name__ == "__main__":
    main()
