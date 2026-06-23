"""`Arma3MapData` class."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

import folium
from arma3_offline_map_lib.dem import DEM
from arma3_offline_map_lib.point_2d import Point2D
from rich.markup import escape

from src.load_geojson import load_locations, load_roads_and_bridges, load_root_features
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

if TYPE_CHECKING:
    from pathlib import Path

    from arma3_offline_map_lib import geojson


_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class Arma3MapData:
    """Container for GeoJSON data assembled from data source."""

    world_name: str
    world_size: int
    grid_offset: Point2D
    elevation_offset: float
    preview_image_filepath: Path | None = None
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

        geojson_path = path / "geojson"
        root_features = load_root_features(path=geojson_path, world_name=world_name_)
        roads_and_bridges = load_roads_and_bridges(
            path=geojson_path / "roads", world_name=world_name_
        )
        locations_ = load_locations(
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
            map_=map_, multi_series=self.multipolygon_features
        )
        plot_polygon_multi_series(map_=map_, multi_series=self.polygon_features)
        plot_marker_multi_series(map_=map_, multi_series=self.point_features)
        plot_roads(map_=map_, multi_series=self.roads)
        plot_bridges(map_=map_, multi_series=self.bridges)
        plot_line_multi_series(map_=map_, multi_series=self.line_features)
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
