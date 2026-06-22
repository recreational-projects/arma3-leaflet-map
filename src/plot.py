"""Plotting."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import folium
from arma3_offline_map_lib.point_2d import Point2D
from PIL import Image, ImageOps

from _setup import WORKING_PATH
from src import styles
from src.geojson_to_folium import (
    marker_group,
    multi_polygon_group,
    poly_line_group,
    polygon_group,
    text_marker_group,
)
from src.plot_coordinate import PlotCoordinate
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence
    from pathlib import Path

    from arma3_offline_map_lib import geojson
    from arma3_offline_map_lib.dem import DEM

    from src.arma3_map_data import Arma3MapData


_LOGGER = logging.getLogger(__name__)


def check_styles() -> None:
    """TO DO."""
    icon_names = [
        style.icon_name
        for style in styles.POINT_STYLES.values()
        if hasattr(style, "icon_name")
    ]
    duplicate_icon_names = _duplicates(icon_names)
    if duplicate_icon_names:
        log_msg = f"Non-unique icons: {format_iterable_of_str(duplicate_icon_names)}"
        _LOGGER.warning(log_msg)


def _duplicates(seq: Sequence[Any]) -> set[Any]:
    """Return duplicate elements from `seq`."""
    seen = set()
    return {val for val in seq if (val in seen or seen.add(val))}


def plot_map(*, map_data: Arma3MapData, export_path: Path) -> None:
    """Plot Folium map and save."""
    _center = PlotCoordinate.from_grad_meh_position(
        (map_data.world_size / 2, map_data.world_size / 2)
    )
    map_ = folium.Map(
        location=_center.xy,
        zoom_start=13,
        control_scale=True,  # Show a scale on the bottom of the map.
        prefer_canvas=True,  # for vector layers instead of SVG
        # crs="Simple",  # Don't use, as it seems to use pixels for plot units.
        tiles=None,
    )
    if map_data.preview_image_filepath:
        _embed_sat_map_overlay(
            map_=map_,
            path=map_data.preview_image_filepath,
            map_size=map_data.world_size,
        )
    land_image_filepath_ = WORKING_PATH / f"{map_data.world_name}.png"
    _render_land_image(path=land_image_filepath_, dem=map_data.dem)
    _embed_land_image(
        map_=map_, path=land_image_filepath_, map_size=map_data.world_size
    )
    _plot_multipolygon_multi_series(
        map_=map_, multi_series=map_data.multipolygon_features
    )
    _plot_polygon_multi_series(map_=map_, multi_series=map_data.polygon_features)
    _plot_marker_multi_series(map_=map_, multi_series=map_data.point_features)
    _plot_roads(map_=map_, multi_series=map_data.roads)
    _plot_bridges(map_=map_, multi_series=map_data.bridges)
    _plot_line_multi_series(map_=map_, multi_series=map_data.line_features)
    _plot_div_icon_multi_series(map_=map_, multi_series=map_data.locations)
    _plot_grid(map_=map_, map_size=map_data.world_size)
    folium.LayerControl().add_to(map_)

    save_filepath = export_path / f"{map_data.world_name}.html"
    log_msg = f"Saving '{save_filepath}'... "
    _LOGGER.info(log_msg)

    map_.save(save_filepath)
    log_msg = f"[bold]Saved map for '{map_data.world_name}'."
    _LOGGER.info(log_msg, extra={"markup": True})


def _embed_sat_map_overlay(*, map_: folium.Map, path: Path, map_size: int) -> None:
    """Embed the satellite map in the map as an overlay."""
    max_ = PlotCoordinate.from_grad_meh_position((map_size, map_size))
    map_image_overlay = folium.raster_layers.ImageOverlay(
        image=str(path),
        bounds=((0, 0), max_.xy),
        name="Preview satmap",
        overlay=True,
        show=False,
    )
    map_image_overlay.add_to(map_)


def _render_land_image(*, path: Path, dem: DEM) -> None:
    """
    Render the land/sea boolean array to an image file to be embedded later.

    This appears to be much faster than directly embedding the array.
    Recoloring is easier too.
    """
    _LOGGER.info("- Rendering land image...")
    onebit_im = Image.fromarray(dem.land)
    grayscale_im = onebit_im.convert(mode="L")
    color_im = ImageOps.colorize(
        grayscale_im, black=styles.SEA_COLOR, white=styles.LAND_COLOR
    )
    WORKING_PATH.mkdir(exist_ok=True)
    color_im.save(path)
    _LOGGER.info("  ...saved...")


def _embed_land_image(*, map_: folium.Map, path: Path, map_size: int) -> None:
    """
    Embed the land/sea image in the map as a base layer.

    Note the image is same resolution as heightmap and is not smoothed.
    """
    max_ = PlotCoordinate.from_grad_meh_position((map_size, map_size))
    map_image_overlay = folium.raster_layers.ImageOverlay(
        image=str(path),
        bounds=((0, 0), max_.xy),
        name="Land/sea image",
        overlay=False,
    )
    map_image_overlay.add_to(map_)
    _LOGGER.info("  ...embedded.")


def _plot_multipolygon_multi_series(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        # for forest, features is singleton
        style = styles.POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in POLYGON_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = styles.PolygonStyle()

        multi_polygon_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _plot_polygon_multi_series(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = styles.POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in POLYGON_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = styles.PolygonStyle()

        polygon_group(feature_kind=feature_kind, features=features, style=style).add_to(
            map_
        )


def _plot_marker_multi_series(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = styles.POINT_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in POINT_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = styles.MarkerStyle()

        marker_group(feature_kind=feature_kind, features=features, style=style).add_to(
            map_
        )


def _plot_roads(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """
    Plot all road features in style order (minor -> major).

    If any road kinds don't have a style, they are plotted last with a default style.
    """
    remaining_road_kinds = set(multi_series.keys())
    for feature_kind, style in styles.ROAD_STYLES.items():
        features = multi_series.get(feature_kind)
        if features:
            group = poly_line_group(
                feature_kind=feature_kind, features=features, style=style
            )
            group.add_to(map_)

        remaining_road_kinds.discard(feature_kind)

    for feature_kind in remaining_road_kinds:
        log_msg = f"- No style in ROAD_STYLES for '{feature_kind}'."
        _LOGGER.error(log_msg)
        features = multi_series.get(feature_kind)
        if features:
            group = poly_line_group(
                feature_kind=feature_kind, features=features, style=styles.LineStyle()
            )
            group.add_to(map_)


def _plot_bridges(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """
    Plot all bridge features in style order (minor -> major).

    If any bridge kinds don't have a style, they are plotted last with a default style.
    """
    remaining_bridge_kinds = set(multi_series.keys())
    for feature_kind, style in styles.BRIDGE_STYLES.items():
        features = multi_series.get(feature_kind)
        if features:
            group = polygon_group(
                feature_kind=feature_kind, features=features, style=style
            )
            group.add_to(map_)

        remaining_bridge_kinds.discard(feature_kind)

    for feature_kind in remaining_bridge_kinds:
        log_msg = f"- No style in BRIDGE_STYLES for '{feature_kind}'."
        _LOGGER.error(log_msg)
        features = multi_series.get(feature_kind)
        if features:
            group = polygon_group(
                feature_kind=feature_kind,
                features=features,
                style=styles.PolygonStyle(),
            )
            group.add_to(map_)


def _plot_line_multi_series(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = styles.LINE_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in LINE_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = styles.LineStyle()

        poly_line_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _plot_div_icon_multi_series(
    *, map_: folium.Map, multi_series: Mapping[str, Collection[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = styles.TEXT_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in TEXT_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = styles.TextStyle()

        text_marker_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _plot_grid(map_: folium.Map, map_size: int) -> None:
    """Plot 1 km grid."""
    label_indent = 100.0
    for i in range((map_size // 1000) + 1):
        distance = 1000 * i
        h_line = folium.vector_layers.PolyLine(
            locations=[
                PlotCoordinate.from_grad_meh_position((0, distance)).xy,
                PlotCoordinate.from_grad_meh_position((map_size, distance)).xy,
            ],
            color=styles.GRID_STYLE.color,
            weight=styles.GRID_STYLE.weight,
            opacity=styles.GRID_STYLE.opacity,
        )
        h_line.add_to(map_)
        _add_text_marker(
            map_=map_,
            a3_position=Point2D(float(distance), label_indent),
            text=f"{i:02}",
        )
        v_line = folium.vector_layers.PolyLine(
            locations=[
                PlotCoordinate.from_grad_meh_position((distance, 0)).xy,
                PlotCoordinate.from_grad_meh_position((distance, map_size)).xy,
            ],
            color=styles.GRID_STYLE.color,
            weight=styles.GRID_STYLE.weight,
            opacity=styles.GRID_STYLE.opacity,
        )
        v_line.add_to(map_)
        _add_text_marker(
            map_=map_,
            a3_position=Point2D(label_indent, float(distance)),
            text=f"{i:02}",
        )


def _add_text_marker(*, map_: folium.Map, a3_position: Point2D, text: str) -> None:
    pos_ = PlotCoordinate.from_a3_position(a3_position)
    marker = folium.Marker(
        location=pos_.xy,
        icon=folium.DivIcon(html=f'<div style="font-size: 1rem">{text}</div>'),
    ).add_to(map_)
    marker.add_to(map_)
