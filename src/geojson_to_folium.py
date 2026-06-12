"""Return Folium objects from GeoJSON."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import folium
from arma3_offline_map_lib import geojson
from folium import DivIcon

from src.features_styles import (
    CircleMarkerStyle,
    CircleStyle,
    LineStyle,
    MarkerStyle,
    PolygonStyle,
)
from src.plot_coordinate import PlotCoordinate

if TYPE_CHECKING:
    from collections.abc import Sized

_LOGGER = logging.getLogger(__name__)


def multi_polygon_group(
    *, feature_kind: str, features: list[geojson.Feature], style: PolygonStyle
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


def polygon_group(
    *, feature_kind: str, features: list[geojson.Feature], style: PolygonStyle
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


def marker_group(
    *,
    feature_kind: str,
    features: list[geojson.Feature],
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


def text_marker_group(
    *,
    feature_kind: str,
    features: list[geojson.Feature],
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


def poly_line_group(
    *, feature_kind: str, features: list[geojson.Feature], style: LineStyle
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


def _empty_feature_group(
    *, feature_kind: str, features: Sized, show: bool = True
) -> folium.FeatureGroup:
    """Return a new empty `folium.FeatureGroup`."""
    return folium.FeatureGroup(name=f"{feature_kind} ({len(features)})", show=show)
