"""TO DO."""

import json
import logging
from pathlib import Path

import folium

from src import features_config, features_styles
from src.geo_json.feature import Feature as GeoJSONFeature

# Avoid confusion with `folium.FeatureGroup`
from src.geo_json.feature import (
    LineString,
    MultiPolygon,
    Point,
    Polygon,
    Position,
)
from src.geo_json.load import load_features_from_dir

_LOGGER = logging.getLogger(__name__)
_DEGREES_LATITUDE_TO_M = 110574
_DEGREES_LONGITUDE_TO_M = 111320


def _marker_group(
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
        scaled_coords = _scale_position_to_lat_long(coordinates)
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


def _line_group(
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
            _scale_position_to_lat_long(coord) for coord in f.geometry.coordinates
        ]

        folium.PolyLine(
            locations=scaled_coords,
            color=color,
            weight=weight,
            dash_array=dash_array,
            tooltip=feature_kind,
        ).add_to(group)  # may be unnecessary?

    return group


def _validate_position(position: Position) -> Position | None:
    """Validate position. Only used by `_polygon_group()`."""
    if position[0] is None or position[1] is None:
        log_msg = "- Ignored coordinate containing `None` value."
        _LOGGER.warning(log_msg)
        return None

    return position


def _polygon_group(
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
                _scale_position_to_lat_long(position)
                for position in polygon
                if _validate_position(position)
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


def _multipolygon_group(
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
                scaled_coords = [
                    _scale_position_to_lat_long(coord) for coord in polygon
                ]

                folium.Polygon(
                    locations=scaled_coords,
                    fill_color=fill_color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(group)  # may be unnecessary to use?

    return group


def _image_overlay(
    image_path: Path, map_size: int
) -> folium.raster_layers.ImageOverlay | None:
    """Return image overlay."""
    if not image_path.is_file():
        log_msg = f"Couldn't find preview image '{image_path}' - ignoring."
        _LOGGER.warning(log_msg)
        return None

    return folium.raster_layers.ImageOverlay(
        image=str(image_path),
        bounds=((0, 0), _scale_position_to_lat_long((map_size, map_size))),
        name="Preview satmap",
        overlay=True,
    )


def _plot_markers_multi_series(
    *,
    map_: folium.Map,
    feature_multi_series: dict[str, list[GeoJSONFeature]],
    name_prefix: str = "",
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        icon_color = features_styles.ICON_COLORS.get(feature_kind, "gray")
        icon = features_styles.ICONS.get(feature_kind)

        if not icon:
            log_msg = f"- No icon for point feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)
            icon = ""
            icon_color = "red"

        _marker_group(
            feature_kind=feature_kind,
            features=features,
            name_prefix=name_prefix,
            icon=icon,
            icon_color=icon_color,
        ).add_to(map_)


def _plot_lines_multi_series(
    *,
    map_: folium.Map,
    feature_multiseries: dict[str, list[GeoJSONFeature]],
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multiseries.items():
        style = features_styles.LINE_STYLES.get(feature_kind, {})
        color = style.get("color", "red")
        dash_array = style.get("dash_array", "")
        weight = style.get("weight", 8)

        if not style:
            log_msg = f"- No style defined for line feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)

        _line_group(
            feature_kind=feature_kind,
            features=features,
            color=color,
            weight=weight,
            dash_array=dash_array,
        ).add_to(map_)


def _plot_polygons_multi_series(
    *,
    map_: folium.Map,
    feature_multi_series: dict[str, list[GeoJSONFeature]],
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        style = features_styles.POLYGON_STYLES.get(feature_kind, {})
        fill_color = style.get("fill_color", "red")

        if not style:
            log_msg = f"- No style defined for polygon feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)

        _polygon_group(
            feature_kind=feature_kind, features=features, fill_color=fill_color
        ).add_to(map_)


def _plot_multipolygons_multi_series(
    *,
    map_: folium.Map,
    feature_multiseries: dict[str, list[GeoJSONFeature]],
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multiseries.items():
        # for forest, features is singleton
        style = features_styles.POLYGON_STYLES.get(feature_kind, {})
        fill_color = style.get("fill_color", "red")

        if not style:
            log_msg = (
                f"- No style defined for multipolygon feature kind '{feature_kind}'."
            )
            _LOGGER.error(log_msg)

        _multipolygon_group(
            feature_kind=feature_kind, features=features, fill_color=fill_color
        ).add_to(map_)


def _scale_position_to_lat_long(position: Position) -> tuple[float, float]:
    """
    Convert x, y in metres to nominal lat, long at the equator.

    Ignore z if present.
    """
    x = position[1]
    y = position[0]
    if x is None or y is None:
        raise TypeError
    return x / _DEGREES_LATITUDE_TO_M, y / _DEGREES_LONGITUDE_TO_M


def plot_map(data_path: Path, plot_path: Path) -> None:
    """Plot Folium map from grad_meh output, and save."""
    map_name = data_path.stem
    metadata_filepath = data_path / "meta.json"
    if not metadata_filepath.is_file():
        log_msg = f"[bold]Map '{map_name}': no metadata, skipping.[/]"
        _LOGGER.error(log_msg, extra={"markup": True})
        return

    preview_image_filepath = data_path / "preview.png"
    geojson_dirpath = data_path / "geojson"
    save_filepath = plot_path / f"{map_name}.html"
    log_msg = f"[bold]Map '{map_name}' loading...[/]"
    _LOGGER.info(log_msg, extra={"markup": True})

    metadata = json.loads(metadata_filepath.read_text())

    map_ = folium.Map(
        location=(0, 0),
        zoom_start=12,
        control_scale=True,  # Show a scale on the bottom of the map.
        prefer_canvas=True,  # for vector layers instead of SVG
        # crs="Simple",  # Don't use, as it seems to use pixels for plot units.
        tiles=None,
    )
    map_image_overlay = _image_overlay(preview_image_filepath, metadata["worldSize"])
    if map_image_overlay:
        map_image_overlay.add_to(map_)

    multipolygon_features = load_features_from_dir(
        path=geojson_dirpath,
        include=features_config.MULTIPOLYGON_FEATURES,
        kind="multipolygon",
    )
    polygon_features = load_features_from_dir(
        path=geojson_dirpath,
        include=features_config.POLYGON_FEATURES,
        kind="polygon",
    )
    point_features = load_features_from_dir(
        path=geojson_dirpath,
        include=features_config.POINT_FEATURES,
        limit=features_config.IGNORED_FEATURE_KIND_THRESHOLD,
        kind="point",
    )
    locations = load_features_from_dir(
        path=geojson_dirpath / "locations",
        exclude=features_config.IGNORED_LOCATIONS,
        kind="location",
    )
    line_features = load_features_from_dir(
        path=geojson_dirpath,
        include=features_config.LINE_FEATURES,
        kind="non-road line",
    )
    roads_path = geojson_dirpath / "roads"
    if not roads_path.exists():
        roads = {}
        log_msg = "- No roads source data."
        _LOGGER.warning(log_msg)
    else:
        roads = load_features_from_dir(
            path=roads_path,
            exclude=features_config.IGNORED_ROADS,
            kind="road",
        )

    _plot_multipolygons_multi_series(
        map_=map_, feature_multiseries=multipolygon_features
    )
    _plot_polygons_multi_series(map_=map_, feature_multi_series=polygon_features)
    _plot_markers_multi_series(map_=map_, feature_multi_series=point_features)
    _plot_markers_multi_series(map_=map_, feature_multi_series=locations)
    _plot_lines_multi_series(map_=map_, feature_multiseries=line_features)
    _plot_lines_multi_series(map_=map_, feature_multiseries=roads)
    folium.LayerControl().add_to(map_)

    log_msg = f"Saving map '{save_filepath}'... "
    _LOGGER.info(log_msg)

    map_.save(save_filepath)
    log_msg = "...done."
    _LOGGER.info(log_msg)
