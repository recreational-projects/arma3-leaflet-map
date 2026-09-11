"""
Report map metadata anomalies as warnings (or error if noted).

- missing `meta.json` (error, skips metadata checks)
    - `worldName` != directory name
    - `elevationOffset` != 0
    - `gridOffsetX` != 0
    - `gridOffsetY` != `worldSize`
- missing `geojson/` (error, skips geojson checks)
    - has rivers
    - no locations
    - no roads
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from arma3_offline_map_lib.grad_meh.metadata import Metadata

from src.setup import INPUT_PATH, PROCESS_UNSUPPORTED_MAPS, setup_logging
from src.supported_maps import SUPPORTED_MAPS

if TYPE_CHECKING:
    from pathlib import Path

LOG_LEVEL = "INFO"
LOGGER = logging.getLogger("rich")


def main() -> None:
    """Script entry point."""
    setup_logging(LOG_LEVEL)

    source_dirs = INPUT_PATH.iterdir()
    if PROCESS_UNSUPPORTED_MAPS:
        data_dirs = source_dirs
    else:
        data_dirs = [dir_ for dir_ in source_dirs if dir_.stem in SUPPORTED_MAPS]

    for dir_ in sorted(data_dirs):
        world_name_ = _metadata_checks(dir_=dir_)
        geojson_path = dir_ / "geojson"
        _geojson_checks(dir_=geojson_path, world_name=world_name_)
        log_msg = f"[{world_name_}] checked."
        LOGGER.info(log_msg)


def _metadata_checks(dir_: Path) -> str:
    """
    Parameters
    ----------
    dir_:
        The world data directory.

    """
    metadata_filepath = dir_ / "meta.json"
    if not metadata_filepath.is_file():
        log_msg = f"[{dir_.stem}] missing 'meta.json': skipping metadata checks."
        LOGGER.error(log_msg)
        return dir_.stem

    metadata = Metadata.from_file(metadata_filepath)
    world_name_ = metadata.world_name
    elevation_offset_ = metadata.elevation_offset
    grid_offset_ = metadata.grid_offset
    size_ = metadata.world_size

    if world_name_ != dir_.stem:
        log_msg = f"[{world_name_}] doesn't match dir stem '{dir_.stem}'."
        LOGGER.warning(log_msg)

    if elevation_offset_ != 0:
        log_msg = f"[{world_name_}] {elevation_offset_=}."
        LOGGER.warning(log_msg)

    if grid_offset_.x != 0:
        log_msg = f"[{world_name_}] {grid_offset_.x=}."
        LOGGER.warning(log_msg)

    if grid_offset_.y != size_:
        log_msg = f"[{world_name_}] {grid_offset_.y=}, {size_=}."
        LOGGER.warning(log_msg)

    return world_name_


def _geojson_checks(*, dir_: Path, world_name: str) -> None:
    """
    Parameters
    ----------
    dir_:
        The world data `geojson` directory.
    world_name:
        Used for logging only.

    """
    if not dir_.is_dir():
        log_msg = f"[{world_name}] missing 'geojson/' dir."
        LOGGER.error(log_msg)
        return

    if (dir_ / "river.geojson.gz").is_file():
        log_msg = f"[{world_name}] has rivers."
        LOGGER.warning(log_msg)

    locations_path_ = dir_ / "locations"
    if not locations_path_.is_dir():
        log_msg = f"[{world_name}] no 'geojson/locations/' dir."
        LOGGER.warning(log_msg)
    elif not locations_path_.iterdir():
        log_msg = f"[{world_name}] no locations."
        LOGGER.warning(log_msg)

    roads_path_ = dir_ / "roads"
    if not roads_path_.is_dir():
        log_msg = f"[{world_name}] no 'geojson/roads/'."
        LOGGER.warning(log_msg)
    elif not roads_path_.iterdir():
        log_msg = f"[{world_name}] no roads."
        LOGGER.warning(log_msg)
    elif (roads_path_ / "hide.geojson.gz").is_file():
        log_msg = f"[{world_name}] has hidden roads."
        LOGGER.warning(log_msg)


if __name__ == "__main__":
    main()
