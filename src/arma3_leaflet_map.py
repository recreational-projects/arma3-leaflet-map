"""Plotting."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import folium
from arma3_offline_map_lib.position_2d import Position2D
from PIL import Image, ImageOps
from rich.markup import escape

from src import styles
from src.geojson_to_folium import (
    house_group,
    marker_group,
    multi_polygon_group,
    poly_line_group,
    polygon_group,
    text_marker_group,
)
from src.plot_coordinate import PlotCoordinate
from src.setup import WORKING_PATH

if TYPE_CHECKING:
    from pathlib import Path

    from src.arma3_map_data import Arma3MapData


_LOGGER = logging.getLogger(__name__)


@dataclass
class Arma3LeafletMap:
    """TODO."""

    data: Arma3MapData
    folium_map: folium.Map = field(init=False)

    def __post_init__(self) -> None:
        size_ = self.data.metadata.world_size
        center_ = PlotCoordinate.from_grad_meh_position((size_ / 2, size_ / 2))
        self.folium_map = folium.Map(
            location=center_.xy,
            zoom_start=13,
            control_scale=True,  # Show a scale on the bottom of the map.
            prefer_canvas=True,  # for vector layers instead of SVG
            # crs="Simple",  # Don't use, as it seems to use pixels for plot units.
            tiles=None,
        )

    def render(self, export_path: Path) -> None:
        """Plot Folium map and save."""
        name_ = self.data.metadata.world_name
        log_text = escape(f"[{name_}] rendering map...")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        if self.data.preview_image_filepath:
            self._embed_sat_map_overlay(self.data.preview_image_filepath)

        land_image_filepath_ = WORKING_PATH / f"{name_}.png"
        self._render_land_image(land_image_filepath_)
        self._embed_land_image(land_image_filepath_)
        log_msg = f"[{name_}] land/sea image rendered and embedded."
        _LOGGER.info(log_msg)

        self._plot_multipolygons()
        self._plot_polygons()
        self._plot_markers()
        self._plot_roads()
        self._plot_bridges()
        self._plot_non_road_lines()
        self._plot_text_labels()
        self._plot_grid()
        folium.LayerControl().add_to(self.folium_map)
        self._add_title(
            text=f"{self.data.metadata.display_name} "
            f"('{self.data.metadata.world_name}'). "
            f"Author: {self.data.metadata.author}",
        )

        log_text = escape(f"[{name_}] ...done.")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        save_filepath = export_path / f"{name_}.html"
        log_text = escape(f"[{name_}] saving...")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

        self.folium_map.save(save_filepath)
        log_text = escape(f"[{name_}] ...done.")
        log_msg = f"[bold]{log_text}[/]"
        _LOGGER.info(log_msg, extra={"markup": True})

    def _embed_sat_map_overlay(self, path: Path) -> None:
        """Embed the satellite image in the map as an overlay."""
        size_ = self.data.metadata.world_size
        max_ = PlotCoordinate.from_grad_meh_position((size_, size_))
        map_image_overlay = folium.raster_layers.ImageOverlay(
            image=str(path),
            bounds=((0, 0), max_.xy),
            name="Preview satmap",
            overlay=True,
            show=False,
        )
        map_image_overlay.add_to(self.folium_map)

    def _render_land_image(self, path: Path) -> None:
        """
        Render the land/sea boolean array to an image file to be embedded later.

        This appears to be much faster than directly embedding the array.
        Recoloring is easier too.
        """
        onebit_im = Image.fromarray(self.data.dem.land)
        grayscale_im = onebit_im.convert(mode="L")
        color_im = ImageOps.colorize(
            grayscale_im, black=styles.WATER_COLOR, white=styles.LAND_COLOR
        )
        color_im.save(path)

    def _embed_land_image(self, path: Path) -> None:
        """
        Embed the land/sea image in the map as a base layer.

        The image is the same resolution as the heightmap and is not smoothed.
        """
        size_ = self.data.metadata.world_size
        max_ = PlotCoordinate.from_grad_meh_position((size_, size_))
        map_image_overlay = folium.raster_layers.ImageOverlay(
            image=str(path),
            bounds=((0, 0), max_.xy),
            name="Land/sea image",
            overlay=False,
        )
        map_image_overlay.add_to(self.folium_map)

    def _plot_multipolygons(self) -> None:
        """Add all series of multipolygon features to the map."""
        for feature_kind, features in self.data.root_features.multipolygons.items():
            # for forest, features is singleton
            style = styles.POLYGON_STYLES.get(feature_kind)
            if not style:
                log_msg = f"- No style in POLYGON_STYLES for '{feature_kind}'."
                _LOGGER.error(log_msg)
                style = styles.PolygonStyle()

            multi_polygon_group(
                feature_kind=feature_kind, features=features, style=style
            ).add_to(self.folium_map)

    def _plot_polygons(self) -> None:
        """
        Add all series of polygon features to the map.

        Handles 'house' separately.
        """
        for feature_kind, features in self.data.root_features.polygons.items():
            if feature_kind == "house":
                group = house_group(feature_kind=feature_kind, features=features)
            else:
                style = styles.POLYGON_STYLES.get(feature_kind)
                if not style:
                    log_msg = f"- No style in POLYGON_STYLES for '{feature_kind}'."
                    _LOGGER.error(log_msg)
                    style = styles.PolygonStyle()

                group = polygon_group(
                    feature_kind=feature_kind, features=features, style=style
                )

            group.add_to(self.folium_map)

    def _plot_markers(self) -> None:
        """Add all series of marker features to the map."""
        for feature_kind, features in self.data.root_features.points.items():
            style = styles.POINT_STYLES.get(feature_kind)
            if not style:
                log_msg = f"- No style in POINT_STYLES for '{feature_kind}'."
                _LOGGER.error(log_msg)
                style = styles.MarkerStyle()

            marker_group(
                feature_kind=feature_kind, features=features, style=style
            ).add_to(self.folium_map)

    def _plot_roads(self) -> None:
        """
        Add all series of road features to the map in style order (minor -> major).

        Road kinds that don't have a style are plotted last with a default style.
        """
        multi_series_ = self.data.roads
        remaining_road_kinds = set(multi_series_.keys())
        for feature_kind, style in styles.ROAD_STYLES.items():
            features = multi_series_.get(feature_kind)
            if features:
                group = poly_line_group(
                    feature_kind=feature_kind, features=features, style=style
                )
                group.add_to(self.folium_map)

            remaining_road_kinds.discard(feature_kind)

        for feature_kind in remaining_road_kinds:
            log_msg = f"- No style in ROAD_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            features = multi_series_.get(feature_kind)
            if features:
                group = poly_line_group(
                    feature_kind=feature_kind,
                    features=features,
                    style=styles.LineStyle(),
                )
                group.add_to(self.folium_map)

    def _plot_bridges(self) -> None:
        """
        Add all bridge feature series to the map in style order (minor -> major).

        Bridge kinds that don't have a style are plotted last with a default style.
        """
        multi_series_ = self.data.bridges
        remaining_bridge_kinds = set(multi_series_.keys())
        for feature_kind, style in styles.BRIDGE_STYLES.items():
            features = multi_series_.get(feature_kind)
            if features:
                group = polygon_group(
                    feature_kind=feature_kind, features=features, style=style
                )
                group.add_to(self.folium_map)

            remaining_bridge_kinds.discard(feature_kind)

        for feature_kind in remaining_bridge_kinds:
            log_msg = f"- No style in BRIDGE_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            features = multi_series_.get(feature_kind)
            if features:
                group = polygon_group(
                    feature_kind=feature_kind,
                    features=features,
                    style=styles.PolygonStyle(),
                )
                group.add_to(self.folium_map)

    def _plot_non_road_lines(self) -> None:
        """Add all series of (non-road) line features to the map."""
        for feature_kind, features in self.data.root_features.lines.items():
            style = styles.LINE_STYLES.get(feature_kind)
            if not style:
                log_msg = f"- No style in LINE_STYLES for '{feature_kind}'."
                _LOGGER.error(log_msg)
                style = styles.LineStyle()

            poly_line_group(
                feature_kind=feature_kind, features=features, style=style
            ).add_to(self.folium_map)

    def _plot_text_labels(self) -> None:
        """Add all series of text labels to the map."""
        for feature_kind, features in self.data.locations.items():
            style = styles.TEXT_STYLES.get(feature_kind)
            if not style:
                log_msg = f"- No style in TEXT_STYLES for '{feature_kind}'."
                _LOGGER.error(log_msg)
                style = styles.TextStyle()

            text_marker_group(
                feature_kind=feature_kind, features=features, style=style
            ).add_to(self.folium_map)

    def _plot_grid(self) -> None:
        """Plot 1 km grid."""
        map_size_ = self.data.metadata.world_size
        for i in range((map_size_ // 1000) + 1):
            distance = 1000 * i
            h_line = folium.vector_layers.PolyLine(
                locations=[
                    PlotCoordinate.from_grad_meh_position((0, distance)).xy,
                    PlotCoordinate.from_grad_meh_position((map_size_, distance)).xy,
                ],
                color=styles.GRID_STYLE.color,
                weight=styles.GRID_STYLE.weight,
                opacity=styles.GRID_STYLE.opacity,
            )
            h_line.add_to(self.folium_map)
            label_indent_ = 100.0
            self._add_text_marker(
                a3_position=Position2D(distance, label_indent_),
                text=f"{i:02}",
            )
            v_line = folium.vector_layers.PolyLine(
                locations=[
                    PlotCoordinate.from_grad_meh_position((distance, 0)).xy,
                    PlotCoordinate.from_grad_meh_position((distance, map_size_)).xy,
                ],
                color=styles.GRID_STYLE.color,
                weight=styles.GRID_STYLE.weight,
                opacity=styles.GRID_STYLE.opacity,
            )
            v_line.add_to(self.folium_map)
            self._add_text_marker(
                a3_position=Position2D(label_indent_, distance),
                text=f"{i:02}",
            )

    def _add_text_marker(self, *, a3_position: Position2D, text: str) -> None:
        pos_ = PlotCoordinate.from_a3_position(a3_position)
        marker = folium.Marker(
            location=pos_.xy,
            icon=folium.DivIcon(html=f'<div style="font-size: 1rem">{text}</div>'),
        )
        marker.add_to(self.folium_map)

    def _add_title(self, *, text: str) -> None:
        """Add a title to the map."""
        html_ = f"<h1>{text}</h1>"
        root_ = self.folium_map.get_root()
        if not getattr(root_, "html", None):
            err_msg = "No HTML element in map root."
            raise RuntimeError(err_msg)

        root_.html.add_child(folium.Element(html_))
