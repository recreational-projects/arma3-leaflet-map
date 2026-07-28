"""Adapters to return Folium objects in `PlotCoordinate` terms from Shapely objects."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from arma3_offline_map_lib.position_2d import Position2D

from .folium import create_polygon, empty_feature_group
from .plot_coordinate import PlotCoordinate

if TYPE_CHECKING:
    import folium
    import shapely

    from src.styles import PolygonStyle


_LOGGER = logging.getLogger(__name__)


def polygon_group(
    *,
    feature_kind: str,
    polygons: shapely.MultiPolygon,
    style: PolygonStyle,
) -> folium.FeatureGroup:
    """Return `folium.FeatureGroup` of `folium.Polygon`s from `shapely.MultiPolygon`."""
    group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(polygons.geoms), show=style.show
    )
    for polygon in polygons.geoms:
        plot_coords_ = [
            PlotCoordinate.from_a3_position(Position2D(x=coord[0], y=coord[1]))
            for coord in polygon.exterior.coords
        ]
        create_polygon(
            plot_coords=plot_coords_,
            feature_kind=feature_kind,
            style=style,
        ).add_to(group)

    return group
