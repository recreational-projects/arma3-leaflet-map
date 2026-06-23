"""`Arma3MapData` class."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

import folium
from arma3_offline_map_lib.dem import DEM
from arma3_offline_map_lib.geojson import (
    geojson_gz_files_in_dir,
    load_features_from_file,
)
from arma3_offline_map_lib.position_2d import Position2D
from rich.markup import escape

from src import features_config
from src.plot import (
    embed_land_image,
    embed_sat_map_overlay,
    plot_bridges,
    plot_div_icon_multi_series,
    plot_grid,
    plot_line_multi_series,
    plot_marker_multi_series,
    plot_multipolygon_multi_series,
    plot_polygon_multi_series,
    plot_roads,
    render_land_image,
)
from src.plot_coordinate import PlotCoordinate
from src.setup import WORKING_PATH
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
        multipolygons_ = load_features_from_dir(
            path=path,
            include=features_config.MULTIPOLYGON_FEATURES,
            kind="multipolygon",
            world_name=world_name,
        )
        polygons_ = load_features_from_dir(
            path=path,
            include=features_config.POLYGON_FEATURES,
            kind="polygon",
            world_name=world_name,
        )
        points_ = load_features_from_dir(
            path=path,
            include=features_config.MARKER_FEATURES,
            limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
            kind="point",
            world_name=world_name,
        )
        lines_ = load_features_from_dir(
            path=path,
            include=features_config.POLY_LINE_FEATURES,
            kind="non-road/bridge line",
            world_name=world_name,
        )

        all_root_feature_kinds = [
            _get_feature_descriptor(fp) for fp in geojson_gz_files_in_dir(path)
        ]
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

    world_name: str
    world_size: int
    grid_offset: Position2D
    elevation_offset: float
    preview_image_filepath: Path | None = None
    root_features: _RootFeatures
    """Features from 'geojson' root folder."""
    roads: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    bridges: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    locations: dict[str, list[geojson.Feature]] = field(default_factory=dict)
    dem: DEM
    """Digital Elevation Model."""

    @classmethod
    def from_data(cls, path: Path) -> Self | None:
        """Compile from source GeoJSON."""
        if not path.is_dir():
            log_msg = f"Can't find '{path}'; skipping."
            _LOGGER.error(log_msg)
            return None

        log_text = escape(f"[{path.stem}] loading data...")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        metadata_path = path / "meta.json"
        if not metadata_path.is_file():
            log_msg = f"[{path.stem}] can't find 'meta.json'; skipping."
            _LOGGER.error(log_msg)
            return None

        metadata_ = json.loads((path / "meta.json").read_text())
        world_name_ = metadata_["worldName"]

        preview_image_filepath_ = path / "preview.png"
        if not preview_image_filepath_.is_file():
            log_msg = (
                f"[{world_name_}] "
                f"couldn't find preview image '{preview_image_filepath_}'."
            )
            _LOGGER.warning(log_msg)
            preview_image_filepath_ = None

        geojson_path = path / "geojson"
        root_features_ = _RootFeatures.load(path=geojson_path, world_name=world_name_)
        roads_and_bridges = _load_roads_and_bridges(
            path=geojson_path / "roads", world_name=world_name_
        )
        locations_ = _load_locations(
            path=geojson_path / "locations", world_name=world_name_
        )
        dem_ = DEM.from_esri_ascii_raster_gz(path / "dem.asc.gz")
        log_msg = f"[{world_name_}] DEM loaded."
        _LOGGER.info(log_msg)

        log_text = escape(f"[{path.stem}] ...done.")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})
        return cls(
            world_name=world_name_,
            world_size=metadata_["worldSize"],
            grid_offset=Position2D(metadata_["gridOffsetX"], metadata_["gridOffsetY"]),
            elevation_offset=metadata_["elevationOffset"],
            preview_image_filepath=preview_image_filepath_,
            root_features=root_features_,
            roads=roads_and_bridges["roads"],
            bridges=roads_and_bridges["bridges"],
            locations=locations_,
            dem=dem_,
        )

    def render_map(self, export_path: Path) -> None:
        """Plot Folium map and save."""
        log_text = escape(f"[{self.world_name}] rendering map...")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        _center = PlotCoordinate.from_grad_meh_position(
            (self.world_size / 2, self.world_size / 2)
        )
        map_ = folium.Map(
            location=_center.xy,
            zoom_start=13,
            control_scale=True,  # Show a scale on the bottom of the map.
            prefer_canvas=True,  # for vector layers instead of SVG
            # crs="Simple",  # Don't use, as it seems to use pixels for plot units.
            tiles=None,
        )
        if self.preview_image_filepath:
            embed_sat_map_overlay(
                map_=map_, path=self.preview_image_filepath, map_size=self.world_size
            )
        land_image_filepath_ = WORKING_PATH / f"{self.world_name}.png"
        render_land_image(path=land_image_filepath_, dem=self.dem)
        embed_land_image(map_=map_, path=land_image_filepath_, map_size=self.world_size)
        log_msg = f"[{self.world_name}] land/sea image rendered and embedded."
        _LOGGER.info(log_msg)

        plot_multipolygon_multi_series(
            map_=map_, multi_series=self.root_features.multipolygons
        )
        plot_polygon_multi_series(map_=map_, multi_series=self.root_features.polygons)
        plot_marker_multi_series(map_=map_, multi_series=self.root_features.points)
        plot_roads(map_=map_, multi_series=self.roads)
        plot_bridges(map_=map_, multi_series=self.bridges)
        plot_line_multi_series(map_=map_, multi_series=self.root_features.lines)
        plot_div_icon_multi_series(map_=map_, multi_series=self.locations)
        plot_grid(map_=map_, map_size=self.world_size)
        folium.LayerControl().add_to(map_)

        log_text = escape(f"[{self.world_name}] ...done.")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        save_filepath = export_path / f"{self.world_name}.html"
        log_text = escape(f"[{self.world_name}] saving...")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        map_.save(save_filepath)
        log_text = escape(f"[{self.world_name}] ...done.")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})


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

    all_location_kinds = [
        _get_feature_descriptor(fp) for fp in geojson_gz_files_in_dir(path)
    ]
    locations = load_features_from_dir(
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


def load_features_from_dir(
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
