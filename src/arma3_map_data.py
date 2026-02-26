"""`Arma3MapData` class."""

import gzip
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import msgspec

from src import features_config
from src.geo_json import feature as geo_json

_LOGGER = logging.getLogger(__name__)


def _geojson_gz_files_in_dir(path: Path) -> list[Path]:
    """Return a list of `.geojson.gz` files in a directory."""
    return [p for p in list(path.iterdir()) if p.suffixes == [".geojson", ".gz"]]


def _get_feature_descriptor(path: Path) -> str:
    """Return the feature descriptor for a `.geojson.gz` file."""
    return path.stem.removesuffix(".geojson")


def _load_features_from_file(
    *, path: Path, limit: int | None = None
) -> list[geo_json.Feature]:
    """
    Load features from a `.geojson.gz` file.

    NB: grad_meh source files are gzipped JSON arrays of GeoJSON features, not GeoJSON
    compliant files.
    """
    with gzip.open(path, "rt", encoding="utf-8") as file:
        features = msgspec.json.decode(file.read(), type=list[geo_json.Feature])

    feature_descriptor = _get_feature_descriptor(path)
    if features is None:
        log_msg = f"- No valid features in `{path.name}`."
        _LOGGER.warning(log_msg)
        return []

    if limit and len(features) > limit:
        log_msg = (
            f"- Too many '{feature_descriptor}' features "
            f"({len(features)}) - data ignored."
        )
        _LOGGER.warning(log_msg)
        return []

    return features


def _summarise_features(features: dict[str, list[geo_json.Feature]]) -> str:
    """Return a string summarizing features data."""
    if not features:
        return "None"
    texts = [
        f"{len(features)} {feature_kind}" for feature_kind, features in features.items()
    ]
    return ", ".join(texts)


def _load_features_from_dir(
    *,
    path: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    limit: int | None = None,
    kind: str,
) -> dict[str, list[geo_json.Feature]]:
    """
    Load features from `.geojson.gz` files in a directory.

    Returns:
         `dict`. Keys are `FILENAME_STEM` for each relevant
         `path/{FILENAME_STEM}.geojson.gz`.

    """
    features: dict[str, list[geo_json.Feature]] = {}
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


@dataclass(kw_only=True, frozen=True)
class Arma3MapData:
    """Container for GeoJSON data asssembled from data source."""

    multipolygons: dict[str, list[geo_json.Feature]] = field(default_factory=dict)
    polygons: dict[str, list[geo_json.Feature]] = field(default_factory=dict)
    points: dict[str, list[geo_json.Feature]] = field(default_factory=dict)
    non_road_lines: dict[str, list[geo_json.Feature]] = field(default_factory=dict)
    roads: dict[str, list[geo_json.Feature]] = field(default_factory=dict)
    locations: dict[str, list[geo_json.Feature]] = field(default_factory=dict)

    @classmethod
    def from_geo_json(cls, path: Path) -> Self:
        """Compile plottables from source GeoJSON."""
        all_feature_descriptors = [
            _get_feature_descriptor(fp) for fp in _geojson_gz_files_in_dir(path)
        ]
        multipolygons = _load_features_from_dir(
            path=path,
            include=features_config.MULTIPOLYGON_FEATURES,
            kind="multipolygon",
        )
        polygons = _load_features_from_dir(
            path=path, include=features_config.POLYGON_FEATURES, kind="polygon"
        )
        points = _load_features_from_dir(
            path=path,
            include=features_config.POINT_FEATURES,
            limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
            kind="point",
        )
        non_road_lines = _load_features_from_dir(
            path=path, include=features_config.LINE_FEATURES, kind="non-road line"
        )
        ignored_feature_descriptors = (
            all_feature_descriptors
            - multipolygons.keys()
            - polygons.keys()
            - points.keys()
            - non_road_lines.keys()
        )
        if ignored_feature_descriptors:
            log_msg = f"Ignored features: {ignored_feature_descriptors}"
            _LOGGER.warning(log_msg)

        locations_path = path / "locations"
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
            log_msg = f"Ignored locations: {ignored_locations}"
            _LOGGER.warning(log_msg)

        roads_path = path / "roads"
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
                log_msg = f"Ignored roads: {ignored_roads}"
                _LOGGER.warning(log_msg)

        return cls(
            multipolygons=multipolygons,
            polygons=polygons,
            points=points,
            non_road_lines=non_road_lines,
            roads=roads,
            locations=locations,
        )
