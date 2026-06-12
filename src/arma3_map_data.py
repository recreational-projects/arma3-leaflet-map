"""`Arma3MapData` class."""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

import msgspec
from arma3_offline_map_lib import geojson

from src import features_config
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Container
    from pathlib import Path


_LOGGER = logging.getLogger(__name__)


def _load_features_from_dir(
    *,
    path: Path,
    include: Container[str] | None = None,
    exclude: Container[str] | None = None,
    limit: int | None = None,
    kind: str,
) -> dict[str, list[geojson.Feature]]:
    """
    Load features from `.geojson.gz` files in a directory.

    Returns:
         `dict`. Keys are `FILENAME_STEM` for each relevant
         `path/{FILENAME_STEM}.geojson.gz`.

    """
    features: dict[str, list[geojson.Feature]] = {}
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
        features_list = _load_features_from_file(path=fp, limit=limit)
        feature_descriptor = _get_feature_descriptor(fp)
        if features_list:
            features[feature_descriptor] = features_list

    if not features:
        log_msg = f"- No {kind} features."
        _LOGGER.warning(log_msg)
    else:
        log_msg = f"- Loaded {kind} features: {_summarise_features(features)}"
        _LOGGER.debug(log_msg)

    return features


def _geojson_gz_files_in_dir(path: Path) -> list[Path]:
    """Return a list of `.geojson.gz` files in a directory."""
    return [p for p in list(path.iterdir()) if p.suffixes == [".geojson", ".gz"]]


def _load_features_from_file(
    *, path: Path, limit: int | None = None
) -> list[geojson.Feature]:
    """
    Load features from a `.geojson.gz` file.

    NB: grad_meh source files are gzipped JSON arrays of GeoJSON features, not GeoJSON
    compliant files.
    """
    with gzip.open(path, "rt", encoding="utf-8") as file:
        features = msgspec.json.decode(file.read(), type=list[geojson.Feature])

    feature_descriptor = _get_feature_descriptor(path)
    if not features:
        log_msg = f"- No valid features in `{path.name}`."
        _LOGGER.warning(log_msg)
        return []

    if limit and len(features) > limit:
        log_msg = (
            f"- Too many '{feature_descriptor}' features "
            f"({len(features)} > {limit}) - data ignored."
        )
        _LOGGER.warning(log_msg)
        return []

    return features


def _get_feature_descriptor(path: Path) -> str:
    """Return the feature descriptor for a `.geojson.gz` file."""
    return path.stem.removesuffix(".geojson")


def _summarise_features(features: dict[str, list[geojson.Feature]]) -> str:
    """Return a string summarizing features data."""
    if not features:
        return "None"

    texts = [
        f"{len(features)} {feature_kind}" for feature_kind, features in features.items()
    ]
    return format_iterable_of_str(texts)


@dataclass(kw_only=True, frozen=True)
class Arma3MapData:
    """Container for GeoJSON data assembled from data source."""

    map_name: str
    world_size: int
    preview_image_filepath: Path | None
    multipolygon_features: dict[str, list[geojson.Feature]] = field(
        default_factory=dict
    )
    polygon_features: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    point_features: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    line_features: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    roads: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    locations: dict[str, list[geojson.Feature]] = field(default_factory=dict)

    @classmethod
    def from_data(cls, path: Path) -> Self | None:
        """Compile from source GeoJSON."""
        if not path.is_dir():
            log_msg = f"Can't find '{path}'; skipping.[/]"
            _LOGGER.error(log_msg, extra={"markup": True})
            return None

        log_msg = f"[bold]Loading data from '{path}'...[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        metadata_ = json.loads((path / "meta.json").read_text())
        preview_image_filepath_ = path / "preview.png"
        if not preview_image_filepath_.is_file():
            log_msg = f"Couldn't find preview image '{preview_image_filepath_}'."
            _LOGGER.warning(log_msg)
            preview_image_filepath_ = None

        geojson_dirpath_ = path / "geojson"
        all_feature_descriptors = [
            _get_feature_descriptor(fp)
            for fp in _geojson_gz_files_in_dir(geojson_dirpath_)
        ]
        multipolygons = _load_features_from_dir(
            path=geojson_dirpath_,
            include=features_config.MULTIPOLYGON_FEATURES,
            kind="multipolygon",
        )
        polygons = _load_features_from_dir(
            path=geojson_dirpath_,
            include=features_config.POLYGON_FEATURES,
            kind="polygon",
        )
        points = _load_features_from_dir(
            path=geojson_dirpath_,
            include=features_config.MARKER_FEATURES,
            limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
            kind="point",
        )
        non_road_lines = _load_features_from_dir(
            path=geojson_dirpath_,
            include=features_config.POLY_LINE_FEATURES,
            kind="non-road line",
        )
        ignored_feature_descriptors = (
            all_feature_descriptors
            - multipolygons.keys()
            - polygons.keys()
            - points.keys()
            - non_road_lines.keys()
        )
        if ignored_feature_descriptors:
            log_msg = (
                f"- Ignored features: "
                f"{format_iterable_of_str(ignored_feature_descriptors)}"
            )
            _LOGGER.warning(log_msg)

        locations_path = geojson_dirpath_ / "locations"
        all_location_kinds = [
            _get_feature_descriptor(fp)
            for fp in _geojson_gz_files_in_dir(locations_path)
        ]
        locations = _load_features_from_dir(
            path=locations_path,
            exclude=features_config.IGNORED_LOCATIONS,
            kind="location",
        )
        ignored_locations = all_location_kinds - locations.keys()
        if ignored_locations:
            log_msg = (
                f"- Ignored locations: {format_iterable_of_str(ignored_locations)}"
            )
            _LOGGER.warning(log_msg)

        roads_path = geojson_dirpath_ / "roads"
        if not roads_path.is_dir():
            roads = {}
            log_msg = "- No roads source data."
            _LOGGER.warning(log_msg)
        else:
            all_roads = [
                _get_feature_descriptor(fp)
                for fp in _geojson_gz_files_in_dir(roads_path)
            ]
            roads = _load_features_from_dir(
                path=roads_path, exclude=features_config.IGNORED_ROADS, kind="road"
            )
            ignored_roads = all_roads - roads.keys()
            if ignored_roads:
                log_msg = f"- Ignored roads: {format_iterable_of_str(ignored_roads)}"
                _LOGGER.warning(log_msg)

        return cls(
            map_name=metadata_["worldName"],
            world_size=metadata_["worldSize"],
            preview_image_filepath=preview_image_filepath_,
            multipolygon_features=multipolygons,
            polygon_features=polygons,
            point_features=points,
            line_features=non_road_lines,
            roads=roads,
            locations=locations,
        )
