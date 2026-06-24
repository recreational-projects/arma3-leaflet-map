"""Return Folium objects from GeoJSON."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import folium
from arma3_offline_map_lib import geojson
from folium import DivIcon, FeatureGroup

from src.plot_coordinate import PlotCoordinate
from src.styles import (
    CircleMarkerStyle,
    CircleStyle,
    LineStyle,
    MarkerStyle,
    TextStyle,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Sized

    from src.styles import PolygonStyle

_LOGGER = logging.getLogger(__name__)


def multi_polygon_group(
    *, feature_kind: str, features: Collection[geojson.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.MultiPolygon`s
    from GeoJSON features with `MultiPolygon` geometry.
    """
    feature_group = _empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.MultiPolygon):
            err_msg = (
                f"Unexpected non-`MultiPolygon` geometry "
                f"when plotting '{feature_kind}' as MultiPolygon."
            )
            raise TypeError(err_msg)

        for multipolygon in f.geometry.coordinates:
            for polygon in multipolygon:
                _plot_coords = [
                    PlotCoordinate.from_grad_meh_position(coord) for coord in polygon
                ]
                _add_polygon(plot_coords=_plot_coords, feature_group=feature_group,
                             feature_kind=feature_kind, style=style)

    return feature_group


def polygon_group(
    *, feature_kind: str, features: Collection[geojson.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Polygon`s
    from GeoJSON features with `Polygon` geometry.
    """
    feature_group = _empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.Polygon):
            err_msg = (
                f"Unexpected non-`Polygon` geometry "
                f"when plotting '{feature_kind}' as Polygon."
            )
            raise TypeError(err_msg)

        for polygon in f.geometry.coordinates:
            _plot_coords = [
                PlotCoordinate.from_grad_meh_position(position)
                for position in polygon
                if _validate_position(position)
            ]
            if _plot_coords:  # Don't plot polygon if no valid coords
                _add_polygon(plot_coords=_plot_coords, feature_group=feature_group,
                             feature_kind=feature_kind, style=style)

    return feature_group


def _add_polygon(
    *,
    plot_coords: list[PlotCoordinate],
    feature_group: FeatureGroup,
    feature_kind: str,
    style: PolygonStyle,
) -> None:
    """Add a `folium.Polygon` to a `folium.FeatureGroup`."""
    folium.Polygon(
        locations=[p.xy for p in plot_coords],
        fill_color=style.color,
        fill=True,
        fill_opacity=1,
        color=style.color,
        weight=style.weight,
        tooltip=feature_kind,
    ).add_to(feature_group)  # may be unnecessary to use?


def _validate_position(position: geojson.Position) -> geojson.Position | None:
    """Validate position. Only used by `_polygon_group()`."""
    if position[0] is None or position[1] is None:
        log_msg = "- Ignored coordinate containing `None` value."
        _LOGGER.warning(log_msg)
        return None

    return position


def marker_group(
    *,
    feature_kind: str,
    features: Collection[geojson.Feature],
    style: MarkerStyle | CircleMarkerStyle | CircleStyle,
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Marker`s
    from GeoJSON features with `Point` geometry.
    """
    feature_group = _empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.Point):
            err_msg = (
                f"Unexpected non-`Point` geometry "
                f"when plotting '{feature_kind}' as Marker."
            )
            raise TypeError(err_msg)

        _coords = f.geometry.coordinates
        _plot_coords = PlotCoordinate.from_grad_meh_position(_coords)
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


def text_marker_group(
    *,
    feature_kind: str,
    features: Collection[geojson.Feature],
    style: TextStyle,
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Marker`s
    from GeoJSON features with `Point` geometry.
    """
    feature_group = _empty_feature_group(
        feature_kind=feature_kind, features=features, show=True
    )
    for f in features:
        if not isinstance(f.geometry, geojson.Point):
            err_msg = (
                f"Unexpected non-`Point` geometry "
                f"when plotting '{feature_kind}' as text Marker."
            )
            raise TypeError(err_msg)

        _coords = f.geometry.coordinates
        _plot_coords = PlotCoordinate.from_grad_meh_position(_coords)
        _popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        _tooltip_text = feature_kind
        _non_breaking_name = ""

        if f.properties:
            name = f.properties.get("name")
            if name is not None:
                _popup_text += f"•&nbsp;name: '{name}'<br>"
                _tooltip_text += f": '{name}'"
                _non_breaking_name = name.replace(" ", "&nbsp;")

        _popup_text += f"•&nbsp;coordinates: ({_coords[0]:.1f}, {_coords[1]:.1f})"
        _html_tag = f"<div style='color: {style.color}"

        if style.font_style:
            _html_tag += f"; font-style: {style.font_style}"
        if style.font_size:
            _html_tag += f"; font-size: {style.font_size}"

        _html_tag += ";'>"
        _html = f"{_html_tag}{_non_breaking_name}</>"
        marker = folium.Marker(
            location=_plot_coords.xy,
            popup=_popup_text,
            tooltip=_tooltip_text,
            icon=DivIcon(html=_html),
        )
        marker.add_to(feature_group)

    return feature_group


def poly_line_group(
    *, feature_kind: str, features: Collection[geojson.Feature], style: LineStyle
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.PolyLine`s
    from GeoJSON features with `LineString` geometry.
    """
    feature_group = _empty_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        if not isinstance(f.geometry, geojson.LineString):
            err_msg = (
                f"Unexpected non-`LineString` geometry "
                f"when plotting '{feature_kind}' as PolyLine."
            )
            raise TypeError(err_msg)

        _plot_coords = [
            PlotCoordinate.from_grad_meh_position(coord)
            for coord in f.geometry.coordinates
        ]
        folium.PolyLine(
            locations=[p.xy for p in _plot_coords],
            color=style.color,
            weight=style.weight,
            dash_array=style.dash_array,
            tooltip=feature_kind,
        ).add_to(feature_group)  # may be unnecessary?

    return feature_group


def _empty_feature_group(
    *, feature_kind: str, features: Sized, show: bool = True
) -> folium.FeatureGroup:
    """Return a new empty `folium.FeatureGroup`."""
    return folium.FeatureGroup(name=f"{feature_kind} ({len(features)})", show=show)
