"""TO DO."""

import json
import logging
from pathlib import Path

import folium

from src import features_styles
from src.arma3_map_data import Arma3MapData
from src.geo_json import feature as geo_json
from src.plot_coordinate import PlotCoordinate

_LOGGER = logging.getLogger(__name__)


def _create_feature_group(
    *, feature_kind: str, features: list[geo_json.Feature]
) -> folium.FeatureGroup:
    """Return a new empty `folium.FeatureGroup`."""
    return folium.FeatureGroup(name=f"{feature_kind} ({len(features)})")


def _marker_group(
    *,
    feature_kind: str,
    features: list[geo_json.Feature],
    name_prefix: str = "",
    icon_name: str = "",
    icon_color: str = "red",
) -> folium.FeatureGroup:
    """Return a group of markers as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(feature_kind=feature_kind, features=features)
    for f in features:
        geometry = f.geometry
        if not isinstance(geometry, geo_json.Point):
            err_msg = "Unexpected non-`Point`."
            raise TypeError(err_msg)

        coordinates = geometry.coordinates
        plot_coord = PlotCoordinate.from_position(coordinates)
        popup_text = f"•&nbsp;feature_kind: '{feature_kind}'<br>"
        tooltip_text = f"{name_prefix}-{feature_kind}"

        if f.properties:
            name = f.properties.get("name")
            if name:
                popup_text += f"•&nbsp;name: '{name}'<br>"
                tooltip_text += f": '{name}'"

        popup_text += (
            f"•&nbsp;coordinates: ({coordinates[0]:.1f}, {coordinates[1]:.1f})"
        )
        marker_icon = folium.Icon(prefix="fa", icon=icon_name, color=icon_color)
        folium.Marker(
            location=plot_coord.xy,
            popup=popup_text,
            tooltip=tooltip_text,
            icon=marker_icon,
        ).add_to(feature_group)

    return feature_group


def _line_group(
    *,
    feature_kind: str,
    features: list[geo_json.Feature],
    color: str,
    weight: float,
    dash_array: str,
) -> folium.FeatureGroup:
    """Return a group of lines as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(feature_kind=feature_kind, features=features)
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
            color=color,
            weight=weight,
            dash_array=dash_array,
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
    *, feature_kind: str, features: list[geo_json.Feature], fill_color: str
) -> folium.FeatureGroup:
    """Return a group of polygons as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(feature_kind=feature_kind, features=features)
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
                    fill_color=fill_color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(feature_group)  # may be unnecessary to use?

    return feature_group


def _multipolygon_group(
    *, feature_kind: str, features: list[geo_json.Feature], fill_color: str
) -> folium.FeatureGroup:
    """Return a group of multipolygons as a `folium.FeatureGroup`."""
    feature_group = _create_feature_group(feature_kind=feature_kind, features=features)
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
                    fill_color=fill_color,
                    fill=True,
                    stroke=False,
                    fill_opacity=1,
                    tooltip=feature_kind,
                ).add_to(feature_group)  # may be unnecessary to use?

    return feature_group


def _image_overlay(
    image_path: Path, map_size: int
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
    *,
    map_: folium.Map,
    feature_multi_series: dict[str, list[geo_json.Feature]],
    name_prefix: str = "",
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
        icon_color = features_styles.ICON_COLORS.get(feature_kind, "gray")
        icon_name = features_styles.ICONS.get(feature_kind, "")

        if not icon_name:
            log_msg = f"- No icon for point feature kind '{feature_kind}'."
            _LOGGER.error(log_msg)
            icon_color = "red"

        _marker_group(
            feature_kind=feature_kind,
            features=features,
            name_prefix=name_prefix,
            icon_name=icon_name,
            icon_color=icon_color,
        ).add_to(map_)


def _plot_lines_multi_series(
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
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
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
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
    *, map_: folium.Map, feature_multi_series: dict[str, list[geo_json.Feature]]
) -> None:
    """TO DO."""
    for feature_kind, features in feature_multi_series.items():
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


def plot_map(data_path: Path, plot_path: Path) -> None:
    """Plot Folium map from grad_meh output, and save."""
    map_name = data_path.stem
    metadata_filepath = data_path / "meta.json"
    if not metadata_filepath.is_file():
        log_msg = f"[bold]Map '{map_name}': no metadata, skipping.[/]"
        _LOGGER.error(log_msg, extra={"markup": True})
        return

    metadata = json.loads(metadata_filepath.read_text())
    preview_image_filepath = data_path / "preview.png"
    geojson_dirpath = data_path / "geojson"
    save_filepath = plot_path / f"{map_name}.html"
    log_msg = f"[bold]Map '{map_name}' loading...[/]"
    _LOGGER.info(log_msg, extra={"markup": True})

    map_data = Arma3MapData.from_geo_json(geojson_dirpath)
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

    _plot_multipolygons_multi_series(
        map_=map_, feature_multi_series=map_data.multipolygons
    )
    _plot_polygons_multi_series(map_=map_, feature_multi_series=map_data.polygons)
    _plot_markers_multi_series(map_=map_, feature_multi_series=map_data.points)
    _plot_markers_multi_series(map_=map_, feature_multi_series=map_data.locations)
    _plot_lines_multi_series(map_=map_, feature_multi_series=map_data.roads)
    _plot_lines_multi_series(map_=map_, feature_multi_series=map_data.non_road_lines)
    folium.LayerControl().add_to(map_)

    log_msg = f"Saving map '{save_filepath}'... "
    _LOGGER.info(log_msg)

    map_.save(save_filepath)
    log_msg = "...done."
    _LOGGER.info(log_msg)
