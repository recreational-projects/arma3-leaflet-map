"""Load GeoJSON features from source `grad-meh` data."""

from __future__ import annotations

import gzip
import logging
from typing import TYPE_CHECKING

import msgspec
from arma3_offline_map_lib import geojson

from src import features_config
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Collection, Container, Mapping
    from pathlib import Path

    from arma3_offline_map_lib.geojson import Feature


_LOGGER = logging.getLogger(__name__)


def load_root_features(
    *, path: Path, world_name: str
) -> dict[str, dict[str, list[Feature]]]:
    """Load features from the root 'geojson' directory."""
    multipolygons = _load_features_from_dir(
        path=path,
        include=features_config.MULTIPOLYGON_FEATURES,
        kind="multipolygon",
        world_name=world_name,
    )
    polygons = _load_features_from_dir(
        path=path,
        include=features_config.POLYGON_FEATURES,
        kind="polygon",
        world_name=world_name,
    )
    points = _load_features_from_dir(
        path=path,
        include=features_config.MARKER_FEATURES,
        kind="point",
        world_name=world_name,
        limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
    )
    lines = _load_features_from_dir(
        path=path,
        include=features_config.POLY_LINE_FEATURES,
        kind="non-road/bridge line",
        world_name=world_name,
    )

    all_root_feature_kinds = [
        _get_feature_descriptor(fp) for fp in _geojson_gz_files_in_dir(path)
    ]
    ignored_root_feature_kinds = (
        all_root_feature_kinds
        - multipolygons.keys()
        - polygons.keys()
        - points.keys()
        - lines.keys()
    )
    if ignored_root_feature_kinds:
        log_msg = (
            f"[{world_name}] ignored root features: "
            f"{format_iterable_of_str(ignored_root_feature_kinds)}"
        )
        _LOGGER.warning(log_msg)

    return {
        "multipolygons": multipolygons,
        "polygons": polygons,
        "points": points,
        "lines": lines,
    }


def load_roads_and_bridges(
    *, path: Path, world_name: str
) -> dict[str, dict[str, list[geojson.Feature]]]:
    """Load roads and bridges from the 'geojson/roads' directory."""
    if not path.is_dir():
        log_msg = f"[{world_name}] no 'roads' source dir."
        _LOGGER.warning(log_msg)
        return {}

    roads = {}
    bridges = {}
    for fp in _geojson_gz_files_in_dir(path):
        kind = _get_feature_descriptor(fp)
        if kind in features_config.BRIDGE_ROADS:
            bridges[kind] = _load_features_from_file(path=fp, world_name=world_name)

        elif kind not in features_config.IGNORED_ROADS:
            roads[kind] = _load_features_from_file(path=fp, world_name=world_name)

    return {"roads": roads, "bridges": bridges}


def load_locations(*, path: Path, world_name: str) -> dict[str, list[geojson.Feature]]:
    """Load roads and bridges from the 'geojson/locations' directory."""
    if not path.is_dir():
        log_msg = f"[{world_name}] no 'locations' source dir."
        _LOGGER.warning(log_msg)
        return {}

    all_location_kinds = [
        _get_feature_descriptor(fp) for fp in _geojson_gz_files_in_dir(path)
    ]
    locations = _load_features_from_dir(
        path=path,
        exclude=features_config.IGNORED_LOCATIONS,
        kind="location",
        world_name=world_name,
    )
    ignored_locations = all_location_kinds - locations.keys()
    if ignored_locations:
        log_msg = (
            f"[{world_name}] ignored locations: "
            f"{format_iterable_of_str(ignored_locations)}"
        )
        _LOGGER.warning(log_msg)

    return locations


def _load_features_from_dir(
    *,
    path: Path,
    include: Container[str] | None = None,
    exclude: Container[str] | None = None,
    limit: int | None = None,
    kind: str,
    world_name: str,
) -> dict[str, list[geojson.Feature]]:
    """
    Load features from `.geojson.gz` files in a directory.

    Returns:
         `dict`. Keys are `FILENAME_STEM` for each relevant
         `path/{FILENAME_STEM}.geojson.gz`.

    """
    dir_features = {}
    if include and exclude:
        err_msg = "`include` and `exclude` cannot both be used."
        raise RuntimeError(err_msg)

    candidate_fps = _geojson_gz_files_in_dir(path)
    if include:
        filepaths = [
            fp for fp in candidate_fps if _get_feature_descriptor(fp) in include
        ]
    elif exclude:
        filepaths = [
            fp for fp in candidate_fps if _get_feature_descriptor(fp) not in exclude
        ]
    else:
        filepaths = candidate_fps

    for fp in filepaths:
        features = _load_features_from_file(path=fp, limit=limit, world_name=world_name)
        feature_descriptor = _get_feature_descriptor(fp)
        if features:
            dir_features[feature_descriptor] = features

    if not dir_features:
        log_msg = f"[{world_name}] no {kind} features."
        _LOGGER.warning(log_msg)
    else:
        log_msg = (
            f"[{world_name}] loaded {kind} features: "
            f"{_summarise_features(dir_features)}"
        )
        _LOGGER.debug(log_msg)

    return dir_features


def _geojson_gz_files_in_dir(path: Path) -> list[Path]:
    """Return a list of `.geojson.gz` files in a directory."""
    return [p for p in list(path.iterdir()) if p.suffixes == [".geojson", ".gz"]]


def _load_features_from_file(
    *, path: Path, limit: int | None = None, world_name: str
) -> list[geojson.Feature]:
    """
    Return features from a `.geojson.gz` file.

    NB: grad_meh source files are gzipped JSON arrays of GeoJSON features, not GeoJSON
    compliant files.
    """
    with gzip.open(path, "rt", encoding="utf-8") as file:
        features = msgspec.json.decode(file.read(), type=list[geojson.Feature])
        # Can't return set as Feature is not hashable

    feature_kind = _get_feature_descriptor(path)
    if not features:
        log_msg = f"[{world_name}] no valid features in `{path.name}`."
        _LOGGER.warning(log_msg)
        return []

    if limit and len(features) > limit:
        log_msg = (
            f"[{world_name}] "
            f"too many '{feature_kind}' features ({len(features)} > {limit}) "
            f"- data ignored."
        )

        _LOGGER.warning(log_msg)
        return []

    return features


def _get_feature_descriptor(path: Path) -> str:
    """Return the feature descriptor for a `.geojson.gz` file."""
    return path.stem.removesuffix(".geojson")


def _summarise_features(features: Mapping[str, Collection[geojson.Feature]]) -> str:
    """Return a string summarizing features data."""
    if not features:
        return "None"

    texts = [
        f"{len(features)} {feature_kind}" for feature_kind, features in features.items()
    ]
    return format_iterable_of_str(texts)
