"""TO DO."""

import logging
from pathlib import Path

import folium

from src.meh.features_styles import (
    FEATURE_ICON_COLORS,
    FEATURE_ICONS,
    FEATURE_LINE_STYLES,
    FEATURE_POLYGON_STYLES,
)
from src.meh.modules.geojsonfeature import (
    Feature as GeoJSONFeature,  # Avoid confusion with `folium.FeatureGroup`
)
from src.meh.modules.geojsonfeature import (
    LineString,
    MultiPolygon,
    Point,
    Polygon,
    Position,
)

_DEGREES_LATITUDE_TO_M = 110574
_DEGREES_LONGITUDE_TO_M = 111320


def image_overlay(
    image_path: Path, map_size: int
) -> folium.raster_layers.ImageOverlay | None:
    """Return image overlay."""
    if not image_path.is_file():
        log_msg = f"Couldn't find preview image '{image_path}' - ignoring."
        logging.warning(log_msg)
        return None

    return folium.raster_layers.ImageOverlay(
        image=str(image_path),
        bounds=((0, 0), scale_position_to_lat_long((map_size, map_size))),
        name="Preview satmap",
        overlay=True,
    )


def plot_polygons_multi_series(
    *,
    map_: folium.Map,
    feature_multiseries: dict[str, list[GeoJSONFeature]],
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multiseries.items():
        style = FEATURE_POLYGON_STYLES.get(feature_kind, {})
        fill_color = style.get("fill_color", "red")

        if not style:
            log_msg = f"- No style defined for polygon feature kind '{feature_kind}'."
            logging.error(log_msg)

        polygon_group(
            feature_kind=feature_kind,
            features=features,
            fill_color=fill_color,
        ).add_to(map_)


def polygon_group(
    *,
    feature_kind: str,
    features: list[GeoJSONFeature],
    fill_color: str,
) -> folium.FeatureGroup:
    """Return a group of polygons as a `folium.FeatureGroup`."""
    group = folium.FeatureGroup(
        name=f"{feature_kind} ({len(features)})",
    )

    for f in features:
        if not isinstance(f.geometry, Polygon):
            err_msg = "Unexpected non-`Polygon`."
            raise TypeError(err_msg)

        for polygon in f.geometry.coordinates:
            scaled_coords = [
                scale_position_to_lat_long(position)
                for position in polygon
                if validate_position(position)
            ]
            if scaled_coords:  # Don't plot polygon if no valid coords
                folium.Polygon(
                    locations=scaled_coords,
                    fill_color=fill_color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(group)  # may be unnecessary to use?

    return group


def plot_multipolygons_multi_series(
    *,
    map_: folium.Map,
    feature_multiseries: dict[str, list[GeoJSONFeature]],
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multiseries.items():
        # for forest, features is singleton
        style = FEATURE_POLYGON_STYLES.get(feature_kind, {})
        fill_color = style.get("fill_color", "red")

        if not style:
            log_msg = (
                f"- No style defined for multipolygon feature kind '{feature_kind}'."
            )
            logging.error(log_msg)

        multipolygon_group(
            feature_kind=feature_kind,
            features=features,
            fill_color=fill_color,
        ).add_to(map_)


def multipolygon_group(
    *,
    feature_kind: str,
    features: list[GeoJSONFeature],
    fill_color: str,
) -> folium.FeatureGroup:
    """Return a group of multipolygons as a `folium.FeatureGroup`."""
    group = folium.FeatureGroup(
        name=f"{feature_kind} ({len(features)})",
    )

    for f in features:
        if not isinstance(f.geometry, MultiPolygon):
            err_msg = "Unexpected non-`MultiPolygon`."
            raise TypeError(err_msg)

        for multipolygon in f.geometry.coordinates:
            for polygon in multipolygon:
                scaled_coords = [scale_position_to_lat_long(coord) for coord in polygon]

                folium.Polygon(
                    locations=scaled_coords,
                    fill_color=fill_color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(group)  # may be unnecessary to use?

    return group


def plot_lines_multi_series(
    *,
    map_: folium.Map,
    feature_multiseries: dict[str, list[GeoJSONFeature]],
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multiseries.items():
        style = FEATURE_LINE_STYLES.get(feature_kind, {})
        color = style.get("color", "red")
        dash_array = style.get("dash_array", "")
        weight = style.get("weight", 8)

        if not style:
            log_msg = f"- No style defined for line feature kind '{feature_kind}'."
            logging.error(log_msg)

        line_group(
            feature_kind=feature_kind,
            features=features,
            color=color,
            weight=weight,
            dash_array=dash_array,
        ).add_to(map_)


def line_group(
    *,
    feature_kind: str,
    features: list[GeoJSONFeature],
    color: str,
    weight: float,
    dash_array: str,
) -> folium.FeatureGroup:
    """Return a group of lines as a `folium.FeatureGroup`."""
    group = folium.FeatureGroup(
        name=f"{feature_kind} ({len(features)})",
    )

    for f in features:
        if not isinstance(f.geometry, LineString):
            err_msg = "Unexpected non-`LineString`."
            raise TypeError(err_msg)
        scaled_coords = [
            scale_position_to_lat_long(coord) for coord in f.geometry.coordinates
        ]

        folium.PolyLine(
            locations=scaled_coords,
            color=color,
            weight=weight,
            dash_array=dash_array,
            tooltip=feature_kind,
        ).add_to(group)  # may be unnecessary?

    return group


def plot_markers_multi_series(
    *,
    map_: folium.Map,
    feature_multiseries: dict[str, list[GeoJSONFeature]],
    name_prefix: str = "",
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multiseries.items():
        icon_color = FEATURE_ICON_COLORS.get(feature_kind, "gray")
        icon = FEATURE_ICONS.get(feature_kind)

        if not icon:
            log_msg = f"- No icon for point feature kind '{feature_kind}'."
            logging.error(log_msg)
            icon = ""
            icon_color = "red"

        marker_group(
            feature_kind=feature_kind,
            features=features,
            name_prefix=name_prefix,
            icon_color=icon_color,
            icon=icon,
        ).add_to(map_)


def marker_group(
    *,
    feature_kind: str,
    features: list[GeoJSONFeature],
    name_prefix: str = "",
    icon: str,
    icon_color: str,
) -> folium.FeatureGroup:
    """Return a group of markers as a `folium.FeatureGroup`."""
    marker_group_ = folium.FeatureGroup(
        name=f"{feature_kind} ({len(features)})",
    )

    for f in features:
        if not isinstance(f.geometry, Point):
            err_msg = "Unexpected non-`Point`."
            raise TypeError(err_msg)

        coordinates = f.geometry.coordinates
        scaled_coords = scale_position_to_lat_long(coordinates)
        popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        tooltip_text = f"{name_prefix}-{feature_kind}"

        if f.properties:
            name = f.properties.get("name")
            if name and name != "":
                name = f.properties["name"]
                popup_text += f"•&nbsp;name: '{name}'<br>"
                tooltip_text += f": '{name}'"

        popup_text += (
            f"•&nbsp;coordinates: ({coordinates[0]:.1f}, {coordinates[1]:.1f})"
        )

        folium.Marker(
            location=scaled_coords,
            popup=popup_text,
            tooltip=tooltip_text,
            icon=folium.Icon(
                prefix="fa",
                icon=icon,
                color=icon_color,
            ),
        ).add_to(marker_group_)

    return marker_group_


def validate_position(position: Position) -> Position | None:
    """TO DO."""
    if position[0] is None or position[1] is None:
        log_msg = "- Ignored coordinate containing `None` value."
        logging.warning(log_msg)
        return None

    return position


def scale_position_to_lat_long(position: Position) -> tuple[float, float]:
    """
    Convert x, y in metres to nominal lat, long at the equator.

    Ignore z if present.
    """
    x = position[1]
    y = position[0]
    if x is None or y is None:
        raise TypeError
    return x / _DEGREES_LATITUDE_TO_M, y / _DEGREES_LONGITUDE_TO_M
