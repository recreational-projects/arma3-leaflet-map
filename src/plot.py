"""TO DO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import folium
from arma3_offline_map_lib import geojson
from folium import DivIcon

from src.features_styles import (
    LINE_STYLES,
    POINT_STYLES,
    POLYGON_STYLES,
    TEXT_STYLES,
    CircleMarkerStyle,
    CircleStyle,
    LineStyle,
    MarkerStyle,
    PolygonStyle,
)
from src.plot_coordinate import PlotCoordinate
from src.strings import format_iterable_of_str

if TYPE_CHECKING:
    from collections.abc import Sequence, Sized
    from pathlib import Path

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
    map_image_overlay = _image_overlay(
        image_path=map_data.preview_image_filepath, map_size=map_data.world_size
    )
    if map_image_overlay:
        map_image_overlay.add_to(map_)

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


def _image_overlay(
    *, image_path: Path, map_size: int
) -> folium.raster_layers.ImageOverlay | None:
    """Return image overlay."""
    if not image_path.is_file():
        log_msg = f"Couldn't find preview image '{image_path}' - ignoring."
        _LOGGER.warning(log_msg)
        return None

    max_ = PlotCoordinate.from_position((map_size, map_size))
    return folium.raster_layers.ImageOverlay(
        image=str(image_path),
        bounds=((0, 0), max_.xy),
        name="Preview satmap",
        overlay=True,
    )


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

        _multi_polygon_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _multi_polygon_group(
    *, feature_kind: str, features: list[geojson.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """Return a group of multipolygons as a `folium.FeatureGroup` of `MultiPolygon`s."""
    feature_group = _create_empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.MultiPolygon):
            err_msg = "Unexpected non-`MultiPolygon`."
            raise TypeError(err_msg)

        for multipolygon in f.geometry.coordinates:
            for polygon in multipolygon:
                _plot_coords = [
                    PlotCoordinate.from_position(coord) for coord in polygon
                ]
                folium.Polygon(
                    locations=[p.xy for p in _plot_coords],
                    fill_color=style.color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(feature_group)  # may be unnecessary to use?

    return feature_group


def _plot_polygon_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style defined for polygon feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = PolygonStyle()

        _polygon_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _polygon_group(
    *, feature_kind: str, features: list[geojson.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """Return a group of polygons as a `folium.FeatureGroup` of `folium.Polygon`s."""
    feature_group = _create_empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.Polygon):
            err_msg = "Unexpected non-`Polygon`."
            raise TypeError(err_msg)

        for polygon in f.geometry.coordinates:
            _plot_coords = [
                PlotCoordinate.from_position(position)
                for position in polygon
                if _validate_position(position)
            ]
            if _plot_coords:  # Don't plot polygon if no valid coords
                folium.Polygon(
                    locations=[p.xy for p in _plot_coords],
                    fill_color=style.color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(feature_group)  # may be unnecessary to use?

    return feature_group


def _validate_position(position: geojson.Position) -> geojson.Position | None:
    """Validate position. Only used by `_polygon_group()`."""
    if position[0] is None or position[1] is None:
        log_msg = "- Ignored coordinate containing `None` value."
        _LOGGER.warning(log_msg)
        return None

    return position


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

        _marker_group(feature_kind=feature_kind, features=features, style=style).add_to(
            map_
        )


def _marker_group(
    *,
    feature_kind: str,
    features: list[geojson.Feature],
    style: MarkerStyle | CircleMarkerStyle | CircleStyle,
) -> folium.FeatureGroup:
    """Return a group of markers as a `folium.FeatureGroup`."""
    feature_group = _create_empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.Point):
            err_msg = "Unexpected non-`Point`."
            raise TypeError(err_msg)

        _coords = f.geometry.coordinates
        _plot_coords = PlotCoordinate.from_position(_coords)
        _popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        _tooltip_text = feature_kind

        if f.properties:
            name = f.properties.get("name", "NO_NAME")
            if name:
                _popup_text += f"•&nbsp;name: '{name}'<br>"
                _tooltip_text += f": '{name}'"

        _popup_text += f"•&nbsp;coordinates: ({_coords[0]:.1f}, {_coords[1]:.1f})"
        if isinstance(style, CircleStyle):
            marker = folium.Circle(
                location=_plot_coords.xy,
                radius=style.radius,
                stroke=False,
                fill=True,
                fill_color=style.color,
                fill_opacity=style.fill_opacity,
                popup=_popup_text,
                tooltip=_tooltip_text,
            )
        elif isinstance(style, CircleMarkerStyle):
            marker = folium.CircleMarker(
                location=_plot_coords.xy,
                radius=style.radius,
                color=style.color,
                stroke=False,
                fill=True,
                fill_opacity=style.fill_opacity,
                popup=_popup_text,
                tooltip=_tooltip_text,
            )
        else:
            _marker_icon = folium.Icon(
                prefix="fa", icon=style.icon_name, color=style.color
            )
            marker = folium.Marker(
                location=_plot_coords.xy,
                popup=_popup_text,
                tooltip=_tooltip_text,
                icon=_marker_icon,
            )

        marker.add_to(feature_group)

    return feature_group


def _plot_div_icon_multi_series(
    *, map_: folium.Map, multi_series: dict[str, list[geojson.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in multi_series.items():
        style = TEXT_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style in TEXT_STYLES for '{feature_kind}'."
            _LOGGER.error(log_msg)

        _text_marker_group(feature_kind=feature_kind, features=features).add_to(map_)


def _text_marker_group(
    *,
    feature_kind: str,
    features: list[geojson.Feature],
) -> folium.FeatureGroup:
    """Return a group of markers as a `folium.FeatureGroup`."""
    feature_group = _create_empty_feature_group(
        feature_kind=feature_kind, features=features, show=True
    )
    for f in features:
        if not isinstance(f.geometry, geojson.Point):
            err_msg = "Unexpected non-`Point`."
            raise TypeError(err_msg)

        _coords = f.geometry.coordinates
        _plot_coords = PlotCoordinate.from_position(_coords)
        _popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        _tooltip_text = feature_kind
        _non_breaking_name = ""

        if f.properties:
            name = f.properties.get("name", "NO_NAME")
            if name:
                _popup_text += f"•&nbsp;name: '{name}'<br>"
                _tooltip_text += f": '{name}'"
                _non_breaking_name = name.replace(" ", "&nbsp;")

        _popup_text += f"•&nbsp;coordinates: ({_coords[0]:.1f}, {_coords[1]:.1f})"
        _html = f"{_non_breaking_name}"
        marker = folium.Marker(
            location=_plot_coords.xy,
            popup=_popup_text,
            tooltip=_tooltip_text,
            icon=DivIcon(html=_html),
        )
        marker.add_to(feature_group)

    return feature_group


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

        _poly_line_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _poly_line_group(
    *, feature_kind: str, features: list[geojson.Feature], style: LineStyle
) -> folium.FeatureGroup:
    """Return a group of lines as a `folium.FeatureGroup` of `folium.PolyLine`s."""
    feature_group = _create_empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.LineString):
            err_msg = "Unexpected non-`LineString`."
            raise TypeError(err_msg)

        _plot_coords = [
            PlotCoordinate.from_position(coord) for coord in f.geometry.coordinates
        ]
        folium.PolyLine(
            locations=[p.xy for p in _plot_coords],
            color=style.color,
            weight=style.weight,
            dash_array=style.dash_array,
            tooltip=feature_kind,
        ).add_to(feature_group)  # may be unnecessary?

    return feature_group


def _create_empty_feature_group(
    *, feature_kind: str, features: Sized, show: bool = True
) -> folium.FeatureGroup:
    """Return a new empty `folium.FeatureGroup`."""
    return folium.FeatureGroup(name=f"{feature_kind} ({len(features)})", show=show)
