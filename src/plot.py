"""TO DO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import folium

from src.features_styles import (
    LINE_STYLES,
    POINT_STYLES,
    POLYGON_STYLES,
    CircleMarkerStyle,
    CircleStyle,
    LineStyle,
    MarkerStyle,
    PolygonStyle,
)
from src.geo_json import feature as geo_json
from src.plot_coordinate import PlotCoordinate

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from src.arma3_map_data import Arma3MapData

_LOGGER = logging.getLogger(__name__)


def _duplicates(seq: Sequence[Any]) -> set[Any]:
    """Return duplicate elements from `seq`."""
    seen = set()
    return {val for val in seq if (val in seen or seen.add(val))}


def check_styles() -> None:
    """TO DO."""
    icon_names = [
        style.icon_name
        for style in POINT_STYLES.values()
        if hasattr(style, "icon_name")
    ]
    duplicate_icon_names = _duplicates(icon_names)
    if duplicate_icon_names:
        log_msg = f"Non-unique icons: {duplicate_icon_names}"
        _LOGGER.warning(log_msg)


def _create_feature_group(
    *, feature_kind: str, features: list[geo_json.Feature], show: bool = True
) -> folium.FeatureGroup:
    """Return a new empty `folium.FeatureGroup`."""
    return folium.FeatureGroup(name=f"{feature_kind} ({len(features)})", show=show)


def _marker_group(
    *,
    feature_kind: str,
    features: list[geo_json.Feature],
    style: MarkerStyle | CircleMarkerStyle | CircleStyle,
) -> folium.FeatureGroup:
    """Return a group of markers as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        geometry = f.geometry
        if not isinstance(geometry, geo_json.Point):
            err_msg = "Unexpected non-`Point`."
            raise TypeError(err_msg)

        coordinates = geometry.coordinates
        plot_coord = PlotCoordinate.from_position(coordinates)
        popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        tooltip_text = feature_kind

        if f.properties:
            name = f.properties.get("name")
            if name:
                popup_text += f"•&nbsp;name: '{name}'<br>"
                tooltip_text += f": '{name}'"

        popup_text += (
            f"•&nbsp;coordinates: ({coordinates[0]:.1f}, {coordinates[1]:.1f})"
        )
        if isinstance(style, CircleStyle):
            marker = folium.Circle(
                location=plot_coord.xy,
                radius=style.radius,
                stroke=False,
                fill=True,
                fill_color=style.color,
                fill_opacity=style.fill_opacity,
                popup=popup_text,
                tooltip=tooltip_text,
            )
        elif isinstance(style, CircleMarkerStyle):
            marker = folium.CircleMarker(
                location=plot_coord.xy,
                radius=style.radius,
                color=style.color,
                stroke=False,
                fill=True,
                fill_opacity=style.fill_opacity,
                popup=popup_text,
                tooltip=tooltip_text,
            )
        else:
            marker_icon = folium.Icon(
                prefix="fa", icon=style.icon_name, color=style.color
            )
            marker = folium.Marker(
                location=plot_coord.xy,
                popup=popup_text,
                tooltip=tooltip_text,
                icon=marker_icon,
            )
        marker.add_to(feature_group)

    return feature_group


def _line_group(
    *, feature_kind: str, features: list[geo_json.Feature], style: LineStyle
) -> folium.FeatureGroup:
    """Return a group of lines as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        geometry = f.geometry
        if not isinstance(geometry, geo_json.LineString):
            err_msg = "Unexpected non-`LineString`."
            raise TypeError(err_msg)

        plot_coords = [
            PlotCoordinate.from_position(coord) for coord in geometry.coordinates
        ]
        folium.PolyLine(
            locations=[p.xy for p in plot_coords],
            color=style.color,
            weight=style.weight,
            dash_array=style.dash_array,
            tooltip=feature_kind,
        ).add_to(feature_group)  # may be unnecessary?

    return feature_group


def _validate_position(position: geo_json.Position) -> geo_json.Position | None:
    """Validate position. Only used by `_polygon_group()`."""
    if position[0] is None or position[1] is None:
        log_msg = "- Ignored coordinate containing `None` value."
        _LOGGER.warning(log_msg)
        return None

    return position


def _polygon_group(
    *, feature_kind: str, features: list[geo_json.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """Return a group of polygons as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        geometry = f.geometry
        if not isinstance(geometry, geo_json.Polygon):
            err_msg = "Unexpected non-`Polygon`."
            raise TypeError(err_msg)

        for polygon in geometry.coordinates:
            plot_coords = [
                PlotCoordinate.from_position(position)
                for position in polygon
                if _validate_position(position)
            ]
            if plot_coords:  # Don't plot polygon if no valid coords
                folium.Polygon(
                    locations=[p.xy for p in plot_coords],
                    fill_color=style.color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(feature_group)  # may be unnecessary to use?

    return feature_group


def _multipolygon_group(
    *, feature_kind: str, features: list[geo_json.Feature], style: PolygonStyle
) -> folium.FeatureGroup:
    """Return a group of multipolygons as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(
        feature_kind=feature_kind, features=features, show=style.show
    )
    for f in features:
        geometry = f.geometry
        if not isinstance(geometry, geo_json.MultiPolygon):
            err_msg = "Unexpected non-`MultiPolygon`."
            raise TypeError(err_msg)

        for multipolygon in geometry.coordinates:
            for polygon in multipolygon:
                plot_coords = [PlotCoordinate.from_position(coord) for coord in polygon]
                folium.Polygon(
                    locations=[p.xy for p in plot_coords],
                    fill_color=style.color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(feature_group)  # may be unnecessary to use?

    return feature_group


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


def _plot_markers_multi_series(
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        style = POINT_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style for point feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = MarkerStyle()

        _marker_group(feature_kind=feature_kind, features=features, style=style).add_to(
            map_
        )


def _plot_lines_multi_series(
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        style = LINE_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style defined for line feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = LineStyle()

        _line_group(
            feature_kind=feature_kind,
            features=features,
            style=style,
        ).add_to(map_)


def _plot_polygons_multi_series(
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        style = POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = f"- No style defined for polygon feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)
            style = PolygonStyle()

        _polygon_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def _plot_multipolygons_multi_series(
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        # for forest, features is singleton
        style = POLYGON_STYLES.get(feature_kind)
        if not style:
            log_msg = (
                f"- No style defined for multipolygon feature kind '{feature_kind}'."
            )
            _LOGGER.error(log_msg)
            style = PolygonStyle()

        _multipolygon_group(
            feature_kind=feature_kind, features=features, style=style
        ).add_to(map_)


def plot_map(*, map_data: Arma3MapData, export_path: Path) -> None:
    """Plot Folium map and save."""
    map_ = folium.Map(
        location=(0, 0),
        zoom_start=12,
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

    _plot_multipolygons_multi_series(
        map_=map_, feature_multi_series=map_data.multipolygons
    )
    _plot_polygons_multi_series(map_=map_, feature_multi_series=map_data.polygons)
    _plot_markers_multi_series(map_=map_, feature_multi_series=map_data.points)
    _plot_markers_multi_series(map_=map_, feature_multi_series=map_data.locations)
    _plot_lines_multi_series(map_=map_, feature_multi_series=map_data.roads)
    _plot_lines_multi_series(map_=map_, feature_multi_series=map_data.non_road_lines)
    folium.LayerControl().add_to(map_)

    save_filepath = export_path / f"{map_data.map_name}.html"
    log_msg = f"Saving '{save_filepath}'... "
    _LOGGER.info(log_msg)

    map_.save(save_filepath)
    log_msg = f"[bold]Saved map for '{map_data.map_name}'."
    _LOGGER.info(log_msg, extra={"markup": True})
