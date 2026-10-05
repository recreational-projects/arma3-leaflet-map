"""
Report map metadata anomalies as warnings (or error if noted).

- missing `meta.json` (error, skips metadata checks)
    - `worldName` != directory name
    - `elevationOffset` != 0
    - `gridOffsetX` != 0
    - `gridOffsetY` != `worldSize`
- missing `geojson/` (error, skips geojson checks)
    - has rivers
    - unhandled features
    - no locations; unhandled locations
    - no roads/bridges; unhandled roads/bridges
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from arma3_offline_map_lib.grad_meh.geojson import geojson_gz_files_in_dir
from arma3_offline_map_lib.grad_meh.metadata import Metadata

from src import features_config, styles
from src.setup import INPUT_PATH, setup_logging

if TYPE_CHECKING:
    from pathlib import Path

LOG_LEVEL = "INFO"
LOGGER = logging.getLogger("rich")


def main() -> None:
    """Script entry point."""
    setup_logging(LOG_LEVEL)
    source_dirs = [p for p in INPUT_PATH.iterdir() if p.is_dir()]
    for world_dir in sorted(source_dirs):
        world_name_ = _metadata_checks(world_dir)
        _geojson_checks(geojson_dir=world_dir / "geojson", world_name=world_name_)
        log_msg = f"[{world_name_}] checked."
        LOGGER.info(log_msg)

    log_msg = f"Data for {len(source_dirs)} maps checked."
    LOGGER.info(log_msg)
    LOGGER.info(log_msg)


def _metadata_checks(world_dir: Path) -> str:
    """
    Parameters
    ----------
    world_dir:
        The world data directory.

    """
    metadata_filepath = world_dir / "meta.json"
    if not metadata_filepath.is_file():
        log_msg = f"[{world_dir.stem}] missing 'meta.json': skipping metadata checks."
        LOGGER.error(log_msg)
        return world_dir.stem

    metadata = Metadata.from_file(metadata_filepath)
    world_name_ = metadata.world_name
    elevation_offset_ = metadata.elevation_offset
    grid_offset_ = metadata.grid_offset
    size_ = metadata.world_size

    if world_name_ != world_dir.stem:
        log_msg = f"[{world_name_}] doesn't match dir stem '{world_dir.stem}'."
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


def _geojson_checks(*, geojson_dir: Path, world_name: str) -> None:
    """
    Parameters
    ----------
    geojson_dir:
        The world data `geojson` directory.
    world_name:
        Used for logging only.

    """
    if not geojson_dir.is_dir():
        log_msg = f"[{world_name}] missing 'geojson/' dir."
        LOGGER.error(log_msg)
        return

    if (geojson_dir / "river.geojson.gz").is_file():
        log_msg = f"[{world_name}] has rivers."
        LOGGER.warning(log_msg)

    _features_checks(geojson_dir, world_name=world_name)
    _locations_checks(geojson_dir / "locations", world_name=world_name)
    _roads_checks(geojson_dir / "roads", world_name=world_name)


def _features_checks(geojson_dir: Path, *, world_name: str) -> None:
    """
    Parameters
    ----------
    geojson_dir:
        The world data `geojson/` directory.
    world_name:
        Used for logging only.

    """
    feature_kinds = _extract_kinds(geojson_dir)
    unhandled_kinds = (
        feature_kinds
        - styles.POINT_STYLES.keys()
        - styles.LINE_STYLES.keys()
        - styles.POLYGON_STYLES.keys()
        - {"house"}  # TODO: special case
    )
    if unhandled_kinds:
        log_msg = f"[{world_name}] has unhandled feature kinds: {unhandled_kinds}"
        LOGGER.error(log_msg)


def _locations_checks(locations_dir: Path, *, world_name: str) -> None:
    """
    Parameters
    ----------
    locations_dir:
        The world data `geojson/locations` directory.
    world_name:
        Used for logging only.

    """
    if not locations_dir.is_dir():
        log_msg = f"[{world_name}] no locations (no 'geojson/locations/' dir)."
        LOGGER.warning(log_msg)
        return

    if not locations_dir.iterdir():
        log_msg = f"[{world_name}] no locations ('geojson/locations' is empty)."
        LOGGER.warning(log_msg)
        return

    location_kinds = _extract_kinds(locations_dir)
    unhandled_kinds = (
        location_kinds - features_config.IGNORED_LOCATIONS - styles.TEXT_STYLES.keys()
    )
    if unhandled_kinds:
        log_msg = f"[{world_name}] has unhandled location kinds: {unhandled_kinds}"
        LOGGER.error(log_msg)


def _roads_checks(roads_dir: Path, *, world_name: str) -> None:
    """
    Parameters
    ----------
    roads_dir:
        The world data `geojson/roads` directory.
    world_name:
        Used for logging only.

    """
    if not roads_dir.is_dir():
        log_msg = f"[{world_name}] no roads (no 'geojson/roads' dir)."
        LOGGER.warning(log_msg)
        return

    if not roads_dir.iterdir():
        log_msg = f"[{world_name}] no roads ('geojson/roads' is empty)."
        LOGGER.warning(log_msg)
        return

    road_kinds = _extract_kinds(roads_dir)
    if "hide" in road_kinds:
        log_msg = f"[{world_name}] has hidden roads."
        LOGGER.warning(log_msg)

    unhandled_kinds = (
        road_kinds - styles.ROAD_STYLES.keys() - styles.BRIDGE_STYLES.keys()
    )
    if unhandled_kinds:
        log_msg = f"[{world_name}] has unhandled road kinds: {unhandled_kinds}"
        LOGGER.error(log_msg)


def _extract_kinds(directory: Path) -> set[str]:
    """Extract feature kind names from geojson.gz files in the given directory."""
    return {
        fp.stem.removesuffix(".geojson") for fp in geojson_gz_files_in_dir(directory)
    }


if __name__ == "__main__":
    main()
