"""Plotting."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import folium

from src.features_styles import (
    LINE_STYLES,
    POINT_STYLES,
    POLYGON_STYLES,
    TEXT_STYLES,
    LineStyle,
    MarkerStyle,
    PolygonStyle,
    TextStyle,
)
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
    from collections.abc import Sequence
    from pathlib import Path

    from arma3_offline_map_lib import geojson

    from src.arma3_map_data import Arma3MapData

_LOGGER = logging.getLogger(__name__)


def check_styles() -> None:
    """TO DO."""
    icon_names = [
        style.icon_name
        for style in POINT_STYLES.values()
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
    _centre = PlotCoordinate.from_position(
        (map_data.world_size / 2, map_data.world_size / 2)
    )
    map_ = folium.Map(
        location=_centre.xy,
        zoom_start=13,
        control_scale=True,  # Show a scale on the bottom of the map.
        prefer_canvas=True,  # for vector layers instead of SVG
        # crs="Simple",  # Don't use, as it seems to use pixels for plot units.
        tiles=None,
    )
    if map_data.preview_image_filepath:
        _plot_sat_map_overlay(
            map_=map_,
            image_path=map_data.preview_image_filepath,
            map_size=map_data.world_size,
        )
    _plot_multipolygon_multi_series(
        map_=map_, multi_series=map_data.multipolygon_features
    )
    _plot_polygon_multi_series(map_=map_, multi_series=map_data.polygon_features)
    _plot_marker_multi_series(map_=map_, multi_series=map_data.point_features)
    _plot_line_multi_series(map_=map_, multi_series=map_data.roads)
    _plot_line_multi_series(map_=map_, multi_series=map_data.line_features)
    _plot_div_icon_multi_series(map_=map_, multi_series=map_data.locations)
    folium.LayerControl().add_to(map_)

    save_filepath = export_path / f"{map_data.map_name}.html"
    log_msg = f"Saving '{save_filepath}'... "
    _LOGGER.info(log_msg)

    map_.save(save_filepath)
    log_msg = f"[bold]Saved map for '{map_data.map_name}'."
    _LOGGER.info(log_msg, extra={"markup": True})


def _plot_sat_map_overlay(*, map_: folium.Map, image_path: Path, map_size: int) -> None:
    """TO DO."""
    max_ = PlotCoordinate.from_position((map_size, map_size))
    map_image_overlay = folium.raster_layers.ImageOverlay(
        image=str(image_path),
        bounds=((0, 0), max_.xy),
        name="Preview satmap",
        overlay=True,
    )
    map_image_overlay.add_to(map_)


def _plot_multipolygon_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        # for forest, features is singleton
        style = POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in POLYGON_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = PolygonStyle()

        multi_polygon_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _plot_polygon_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in POLYGON_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = PolygonStyle()

        polygon_group(feature_kind=feature_kind, features=features, style=style).add_to(
            map_
        )


def _plot_marker_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = POINT_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in POINT_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = MarkerStyle()

        marker_group(feature_kind=feature_kind, features=features, style=style).add_to(
            map_
        )


def _plot_line_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = LINE_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in LINE_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = LineStyle()

        poly_line_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _plot_div_icon_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = TEXT_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in TEXT_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = TextStyle()

        text_marker_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)
