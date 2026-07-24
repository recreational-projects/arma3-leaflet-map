"""`Arma3MapData` class."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from arma3_offline_map_lib.dem import DEM
from arma3_offline_map_lib.geojson import (
    geojson_gz_files_in_dir,
    load_features_from_file,
)
from arma3_offline_map_lib.metadata import Metadata
from rich.markup import escape

from src import features_config
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Collection, Container, Mapping
    from pathlib import Path

    from arma3_offline_map_lib import geojson


_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class _RootFeatures:
    """Container for GeoJSON data assembled from data source."""

    multipolygons: dict[str, list[geojson.Feature]]
    polygons: dict[str, list[geojson.Feature]]
    points: dict[str, list[geojson.Feature]]
    lines: dict[str, list[geojson.Feature]]

    @classmethod
    def load(cls, *, path: Path, world_name: str) -> Self:
        """Load features from the root 'geojson' directory."""
        multipolygons_ = _load_features_from_dir(
            path=path,
            include=features_config.MULTIPOLYGON_FEATURES,
            kind="multipolygon",
            world_name=world_name,
        )
        polygons_ = _load_features_from_dir(
            path=path,
            include=features_config.POLYGON_FEATURES,
            kind="polygon",
            world_name=world_name,
        )
        points_ = _load_features_from_dir(
            path=path,
            include=features_config.MARKER_FEATURES,
            limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
            kind="point",
            world_name=world_name,
        )
        lines_ = _load_features_from_dir(
            path=path,
            include=features_config.POLY_LINE_FEATURES,
            kind="non-road/bridge line",
            world_name=world_name,
        )

        all_root_feature_kinds = {
            _get_feature_descriptor(fp) for fp in geojson_gz_files_in_dir(path)
        }
        ignored_root_feature_kinds = (
            all_root_feature_kinds
            - multipolygons_.keys()
            - polygons_.keys()
            - points_.keys()
            - lines_.keys()
        )
        if ignored_root_feature_kinds:
            log_msg = (
                f"[{world_name}] ignored root features: "
                f"{format_iterable_of_str(ignored_root_feature_kinds)}"
            )
            _LOGGER.warning(log_msg)

        return cls(
            multipolygons=multipolygons_,
            polygons=polygons_,
            points=points_,
            lines=lines_,
        )


@dataclass(kw_only=True, frozen=True)
class Arma3MapData:
    """Container for GeoJSON data assembled from data source."""

    metadata: Metadata
    """Info from 'meta.json'."""
    dem: DEM
    """Digital Elevation Model."""
    root_features: _RootFeatures
    """Features from 'geojson' root folder."""
    roads: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    bridges: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    locations: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    preview_image_filepath: Path | None = None

    @classmethod
    def from_data(cls, path: Path) -> Self | None:
        """Compile from source GeoJSON."""
        if not path.is_dir():
            log_msg = f"Can't find '{path}'; skipping."
            _LOGGER.error(log_msg)
            return None

        metadata_path = path / "meta.json"
        if not metadata_path.is_file():
            log_msg = f"[{path.stem}] can't find {metadata_path}; skipping."
            _LOGGER.error(log_msg)
            return None

        log_text = escape(f"[{path.stem}] loading data...")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        metadata_ = Metadata.from_file(metadata_path)
        name_ = metadata_.world_name

        preview_image_filepath_ = path / "preview.png"
        if not preview_image_filepath_.is_file():
            log_msg = (
                f"[{name_}] couldn't find preview image '{preview_image_filepath_}'."
            )
            _LOGGER.warning(log_msg)
            preview_image_filepath_ = None

        dem_ = DEM.from_esri_ascii_raster_gz(path / "dem.asc.gz")
        log_msg = f"[{name_}] DEM loaded."
        _LOGGER.info(log_msg)
        geojson_path_ = path / "geojson"
        roads_and_bridges_ = _load_roads_and_bridges(
            path=geojson_path_ / "roads", world_name=name_
        )
        data = cls(
            metadata=metadata_,
            root_features=_RootFeatures.load(path=geojson_path_, world_name=name_),
            dem=dem_,
            roads=roads_and_bridges_["roads"],
            bridges=roads_and_bridges_["bridges"],
            locations=_load_locations(
                path=geojson_path_ / "locations", world_name=name_
            ),
            preview_image_filepath=preview_image_filepath_,
        )
        log_text_ = escape(f"[{path.stem}] ...done.")
        log_msg_ = f"[bold]{log_text_}[/]"
        _LOGGER.info(log_msg_, extra={"markup": True})
        return data


def _load_roads_and_bridges(
    *, path: Path, world_name: str
) -> dict[str, dict[str, list[geojson.Feature]]]:
    """Load roads and bridges from the 'geojson/roads' directory."""
    if not path.is_dir():
        log_msg = f"[{world_name}] no 'roads' source dir."
        _LOGGER.error(log_msg)
        return {"roads": {}, "bridges": {}}

    roads = {}
    bridges = {}
    for fp in geojson_gz_files_in_dir(path):
        kind = _get_feature_descriptor(fp)
        if kind in features_config.BRIDGE_ROADS:
            bridges[kind] = _load_features_from_file(path=fp, world_name=world_name)

        elif kind not in features_config.IGNORED_ROADS:
            roads[kind] = _load_features_from_file(path=fp, world_name=world_name)

    return {"roads": roads, "bridges": bridges}


def _load_locations(*, path: Path, world_name: str) -> dict[str, list[geojson.Feature]]:
    """Load roads and bridges from the 'geojson/locations' directory."""
    if not path.is_dir():
        log_msg = f"[{world_name}] no 'locations' source dir."
        _LOGGER.warning(log_msg)
        return {}

    all_location_kinds = {
        _get_feature_descriptor(fp) for fp in geojson_gz_files_in_dir(path)
    }
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

    candidate_fps = geojson_gz_files_in_dir(path)
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


def _load_features_from_file(
    *, path: Path, limit: int | None = None, world_name: str
) -> list[geojson.Feature]:
    """
    Return features from a `.geojson.gz` file.

    NB: grad_meh source files are gzipped JSON arrays of GeoJSON features, not GeoJSON
    compliant files.
    """
    features = load_features_from_file(path)
    if not features:
        log_msg = f"[{world_name}] no valid features in `{path.name}`."
        _LOGGER.warning(log_msg)
        return []

    feature_kind_ = _get_feature_descriptor(path)
    if limit and len(features) > limit:
        log_msg = (
            f"[{world_name}] "
            f"too many '{feature_kind_}' features ({len(features)} > {limit}) "
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
