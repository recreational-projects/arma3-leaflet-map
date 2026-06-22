"""`Arma3MapData` class."""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

import msgspec
from arma3_offline_map_lib import geojson
from arma3_offline_map_lib.dem import DEM
from arma3_offline_map_lib.point_2d import Point2D

from src import features_config
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Collection, Container, Mapping
    from pathlib import Path

    from arma3_offline_map_lib.geojson import Feature


_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class Arma3MapData:
    """Container for GeoJSON data assembled from data source."""

    world_name: str
    world_size: int
    grid_offset: Point2D
    elevation_offset: float
    preview_image_filepath: Path | None
    multipolygon_features: dict[str, list[geojson.Feature]] = field(
        default_factory=dict
    )
    polygon_features: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    point_features: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    line_features: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    roads: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    bridges: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    locations: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    dem: DEM
    """Digital Elevation Model."""

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

        geojson_path = path / "geojson"
        root_features = _load_root_features(geojson_path)
        roads_and_bridges = _load_roads_and_bridges(geojson_path / "roads")
        locations_ = _load_locations(geojson_path / "locations")
        dem_ = DEM.from_esri_ascii_raster_gz(path / "dem.asc.gz")
        _LOGGER.info("- Loaded DEM.")

        return cls(
            world_name=metadata_["worldName"],
            world_size=metadata_["worldSize"],
            grid_offset=Point2D(metadata_["gridOffsetX"], metadata_["gridOffsetY"]),
            elevation_offset=metadata_["elevationOffset"],
            preview_image_filepath=preview_image_filepath_,
            multipolygon_features=root_features["multipolygons"],
            polygon_features=root_features["polygons"],
            point_features=root_features["points"],
            line_features=root_features["lines"],
            roads=roads_and_bridges["roads"],
            bridges=roads_and_bridges["bridges"],
            locations=locations_,
            dem=dem_,
        )


def _load_root_features(geojson_path: Path) -> dict[str, dict[str, list[Feature]]]:
    """Load features from the root 'geojson' directory."""
    multipolygons = _load_features_from_dir(
        path=geojson_path,
        include=features_config.MULTIPOLYGON_FEATURES,
        kind="multipolygon",
    )
    polygons = _load_features_from_dir(
        path=geojson_path, include=features_config.POLYGON_FEATURES, kind="polygon"
    )
    points = _load_features_from_dir(
        path=geojson_path,
        include=features_config.MARKER_FEATURES,
        limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
        kind="point",
    )
    lines = _load_features_from_dir(
        path=geojson_path,
        include=features_config.POLY_LINE_FEATURES,
        kind="line",
    )

    all_root_feature_kinds = [
        _get_feature_descriptor(fp) for fp in _geojson_gz_files_in_dir(geojson_path)
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
            f"- Ignored features: {format_iterable_of_str(ignored_root_feature_kinds)}"
        )
        _LOGGER.warning(log_msg)

    return {
        "multipolygons": multipolygons,
        "polygons": polygons,
        "points": points,
        "lines": lines,
    }


def _load_locations(path: Path) -> dict[str, list[geojson.Feature]]:
    if not path.is_dir():
        log_msg = "- No 'locations' source dir."
        _LOGGER.warning(log_msg)
        return {}

    all_location_kinds = [
        _get_feature_descriptor(fp) for fp in _geojson_gz_files_in_dir(path)
    ]
    locations = _load_features_from_dir(
        path=path, exclude=features_config.IGNORED_LOCATIONS, kind="location"
    )
    ignored_locations = all_location_kinds - locations.keys()
    if ignored_locations:
        log_msg = f"- Ignored locations: {format_iterable_of_str(ignored_locations)}"
        _LOGGER.warning(log_msg)

    return locations


def _load_roads_and_bridges(path: Path) -> dict[str, dict[str, list[geojson.Feature]]]:
    """Load roads and bridges from a directory."""
    if not path.is_dir():
        log_msg = "- No 'roads' source dir."
        _LOGGER.warning(log_msg)
        return {}

    roads_and_bridges = {"roads": {}, "bridges": {}}
    for fp in _geojson_gz_files_in_dir(path):
        kind = _get_feature_descriptor(fp)
        if kind in features_config.BRIDGE_ROADS:
            roads_and_bridges["bridges"][kind] = _load_features_from_file(fp)

        elif kind not in features_config.IGNORED_ROADS:
            roads_and_bridges["roads"][kind] = _load_features_from_file(fp)

    return roads_and_bridges


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
        features = _load_features_from_file(path=fp, limit=limit)
        feature_descriptor = _get_feature_descriptor(fp)
        if features:
            dir_features[feature_descriptor] = features

    if not dir_features:
        log_msg = f"- No {kind} features."
        _LOGGER.warning(log_msg)
    else:
        log_msg = f"- Loaded {kind} features: {_summarise_features(dir_features)}"
        _LOGGER.debug(log_msg)

    return dir_features


def _geojson_gz_files_in_dir(path: Path) -> list[Path]:
    """Return a list of `.geojson.gz` files in a directory."""
    return [p for p in list(path.iterdir()) if p.suffixes == [".geojson", ".gz"]]


def _load_features_from_file(
    path: Path, *, limit: int | None = None
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
        log_msg = f"- No valid features in `{path.name}`."
        _LOGGER.warning(log_msg)
        return []

    if limit and len(features) > limit:
        log_msg = (
            f"- Too many '{feature_kind}' features "
            f"({len(features)} > {limit}) - data ignored."
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
