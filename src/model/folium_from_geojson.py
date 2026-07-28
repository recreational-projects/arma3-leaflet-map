"""Adapters to return Folium objects in `PlotCoordinate` terms from GeoJSON."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import folium
from arma3_offline_map_lib import geojson

from src.styles import (
    CircleMarkerStyle,
    CircleStyle,
    LineStyle,
    MarkerStyle,
    PolygonStyle,
    TextStyle,
)

from .folium import create_polygon, empty_feature_group
from .plot_coordinate import PlotCoordinate

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

_LOGGER = logging.getLogger(__name__)


def polygon_group_from_multi_polygons(
    *, feature_kind: str, features: Collection[geojson.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Polygon`s from GeoJSON features
    with `MultiPolygon` geometry.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(features), show=style.show
    )
    for feature in features:
        multipolygon_geometry = _ensure_geometry(
            geometry=feature.geometry,
            feature_kind=feature_kind,
            expected_geometry_type=geojson.MultiPolygon,
            folium_object_name="folium.Polygon",
        )
        for multipolygon in multipolygon_geometry.coordinates:
            # pyrefly: ignore [not-iterable]
            for polygon in multipolygon:
                _add_polygon(
                    # pyrefly: ignore [bad-argument-type]
                    coords=polygon,
                    feature_group=feature_group,
                    feature_kind=feature_kind,
                    style=style,
                )

    return feature_group


def polygon_group_from_house(
    *, feature_kind: str, features: Collection[geojson.Feature]
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Polygon`s from GeoJSON features
    with `Polygon` geometry.

    Specialized for 'house' features, which have color.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind,
        feature_count=len(features),
    )
    for feature in features:
        polygon_geometry = _ensure_geometry(
            geometry=feature.geometry,
            feature_kind=feature_kind,
            expected_geometry_type=geojson.Polygon,
            folium_object_name="folium.Polygon",
        )
        for polygon in polygon_geometry.coordinates:
            _add_polygon(
                # pyrefly: ignore [bad-argument-type]
                coords=polygon,
                feature_group=feature_group,
                feature_kind=feature_kind,
                style=PolygonStyle(color=f"rgb{tuple(feature.properties['color'])}"),
            )

    return feature_group


def polygon_group_from_polygons(
    *, feature_kind: str, features: Collection[geojson.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Polygon`s from GeoJSON features
    with `Polygon` geometry.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(features), show=style.show
    )
    for feature in features:
        polygon_geometry = _ensure_geometry(
            geometry=feature.geometry,
            feature_kind=feature_kind,
            expected_geometry_type=geojson.Polygon,
            folium_object_name="folium.Polygon",
        )
        for coords in polygon_geometry.coordinates:
            _add_polygon(
                # pyrefly: ignore [bad-argument-type]
                coords=coords,
                feature_group=feature_group,
                feature_kind=feature_kind,
                style=style,
            )

    return feature_group


def poly_line_group(
    *, feature_kind: str, features: Collection[geojson.Feature], style: LineStyle
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.PolyLine`s
    from GeoJSON features with `geojson.LineString` geometry.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(features), show=style.show
    )
    for feature in features:
        line_string_geometry = _ensure_geometry(
            geometry=feature.geometry,
            feature_kind=feature_kind,
            expected_geometry_type=geojson.LineString,
            folium_object_name="folium.PolyLine",
        )
        _plot_coords = [
            # pyrefly: ignore [bad-argument-type]
            PlotCoordinate.from_grad_meh_position(coord)
            for coord in line_string_geometry.coordinates
        ]
        folium.PolyLine(
            locations=[p.lat_lon for p in _plot_coords],
            color=style.color,
            weight=style.weight,
            dash_array=style.dash_array,
            tooltip=feature_kind,
        ).add_to(feature_group)  # may be unnecessary?

    return feature_group


def text_marker_group(
    *,
    feature_kind: str,
    features: Collection[geojson.Feature],
    style: TextStyle,
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Marker`s
    from GeoJSON features with `geojson.Point` geometry.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(features), show=True
    )
    for feature in features:
        point_geometry = _ensure_geometry(
            geometry=feature.geometry,
            feature_kind=feature_kind,
            expected_geometry_type=geojson.Point,
            folium_object_name="folium.Marker",
        )
        _coords = point_geometry.coordinates
        # pyrefly: ignore [bad-argument-type]
        _plot_coords = PlotCoordinate.from_grad_meh_position(_coords)
        _popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        _tooltip_text = feature_kind
        name = feature.properties.get("name")
        if name is not None:
            _popup_text += f"•&nbsp;name: '{name}'<br>"
            _tooltip_text += f": '{name}'"

        _popup_text += f"•&nbsp;coordinates: ({_coords[0]:.1f}, {_coords[1]:.1f})"
        _html_tag = f"<div style='white-space:nowrap; color: {style.color}"

        if style.font_style:
            _html_tag += f"; font-style: {style.font_style}"
        if style.font_size:
            _html_tag += f"; font-size: {style.font_size}"

        _html_tag += ";'>"
        _html = f"{_html_tag}{name}</>"
        marker = folium.Marker(
            location=_plot_coords.lat_lon,
            popup=_popup_text,
            tooltip=_tooltip_text,
            icon=folium.DivIcon(html=_html),
        )
        marker.add_to(feature_group)

    return feature_group


def marker_group(
    *,
    feature_kind: str,
    features: Collection[geojson.Feature],
    style: MarkerStyle | CircleMarkerStyle | CircleStyle,
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Marker`s
    from GeoJSON features with `geojson.Point` geometry.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(features), show=style.show
    )
    for feature in features:
        point_geometry = _ensure_geometry(
            geometry=feature.geometry,
            feature_kind=feature_kind,
            expected_geometry_type=geojson.Point,
            folium_object_name="folium.Marker",
        )
        marker = _create_point_marker(
            feature_kind=feature_kind,
            # pyrefly: ignore [bad-argument-type]
            coordinates=point_geometry.coordinates,
            properties=feature.properties,
            style=style,
        )
        marker.add_to(feature_group)

    return feature_group


def _add_polygon(
    *,
    coords: Sequence[tuple[float, float]],
    feature_group: folium.FeatureGroup,
    feature_kind: str,
    style: PolygonStyle,
) -> None:
    """
    Add a new `folium.Polygon` to a `folium.FeatureGroup`, scaling for plot.

    Params:
        coords: `Sequence` of grad_meh positions
        feature_group: the `folium.FeatureGroup` to add the polygon to
        feature_kind: the kind of feature (e.g. 'house') used for tooltips
        style: the style to use for the polygon
    """
    plot_coords_ = [
        PlotCoordinate.from_grad_meh_position(position)
        for position in coords
        if _validate_position(position)
    ]
    create_polygon(
        plot_coords=plot_coords_,
        feature_kind=feature_kind,
        style=style,
    ).add_to(feature_group)  # may be unnecessary to use?


def _validate_position(position: geojson.Position) -> geojson.Position | None:
    """Validate a `geojson.Position`. Only used for `folium.Polygon`s."""
    if position[0] is None or position[1] is None:
        log_msg = "- Ignored coordinate containing `None` value."
        _LOGGER.warning(log_msg)
        return None

    return position


def _create_point_marker(
    *,
    feature_kind: str,
    coordinates: geojson.Position,
    properties: dict[str, str],
    style: MarkerStyle | CircleMarkerStyle | CircleStyle,
) -> folium.Marker | folium.CircleMarker | folium.Circle:
    """Create a Folium point marker using the requested style."""
    plot_coordinate = PlotCoordinate.from_grad_meh_position(coordinates)
    popup_text, tooltip_text = _point_popup_and_tooltip(
        feature_kind=feature_kind,
        coordinates=coordinates,
        properties=properties,
    )

    if isinstance(style, CircleStyle):
        return folium.Circle(
            location=plot_coordinate.lat_lon,
            radius=style.radius,
            stroke=False,
            fill=True,
            fill_color=style.color,
            fill_opacity=style.fill_opacity,
            popup=popup_text,
            tooltip=tooltip_text,
        )

    if isinstance(style, CircleMarkerStyle):
        return folium.CircleMarker(
            location=plot_coordinate.lat_lon,
            radius=style.radius,
            color=style.color,
            stroke=False,
            fill=True,
            fill_opacity=style.fill_opacity,
            popup=popup_text,
            tooltip=tooltip_text,
        )

    marker_icon = folium.Icon(prefix="fa", icon=style.icon_name, color=style.color)
    return folium.Marker(
        location=plot_coordinate.lat_lon,
        popup=popup_text,
        tooltip=tooltip_text,
        icon=marker_icon,
    )


def _point_popup_and_tooltip(
    *,
    feature_kind: str,
    coordinates: geojson.Position,
    properties: dict[str, str],
) -> tuple[str, str]:
    """Build popup and tooltip text for a point feature."""
    popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
    tooltip_text = feature_kind

    if properties:
        name = properties.get("name", "NO_NAME")
        if name:
            popup_text += f"•&nbsp;name: '{name}'<br>"
            tooltip_text += f": '{name}'"

    popup_text += f"•&nbsp;coordinates: ({coordinates[0]:.1f}, {coordinates[1]:.1f})"
    return popup_text, tooltip_text


def _ensure_geometry(
    *,
    geometry: geojson.Geometry,
    feature_kind: str,
    expected_geometry_type: type,
    folium_object_name: str,
) -> geojson.MultiPolygon | geojson.Polygon | geojson.LineString | geojson.Point:
    """TODO."""
    match expected_geometry_type:
        case geojson.MultiPolygon:
            if isinstance(geometry, geojson.MultiPolygon):
                return geometry

        case geojson.Polygon:
            if isinstance(geometry, geojson.Polygon):
                return geometry

        case geojson.LineString:
            if isinstance(geometry, geojson.LineString):
                return geometry

        case geojson.Point:
            if isinstance(geometry, geojson.Point):
                return geometry

    err_msg = (
        f"Unexpected non-`{expected_geometry_type}` geometry "
        f"when plotting '{feature_kind}' as `{folium_object_name}`."
    )
    raise TypeError(err_msg)
