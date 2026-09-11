"""Folium functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import folium

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.styles import PolygonStyle

    from .plot_coordinate import PlotCoordinate

_LOGGER = logging.getLogger(__name__)


def empty_feature_group(
    *, feature_kind: str, feature_count: int, show: bool = True
) -> folium.FeatureGroup:
    """Return a new empty `folium.FeatureGroup`."""
    return folium.FeatureGroup(name=f"{feature_kind} ({feature_count})", show=show)


def create_polygon(
    *,
    plot_coords: Sequence[PlotCoordinate],
    feature_kind: str,
    style: PolygonStyle,
) -> folium.Polygon:
    """
    Create a `folium.Polygon`.

    Params:
        coords: `Sequence` of `PlotCoordinate`
        feature_kind: the kind of feature (e.g. 'house') used for tooltips
        style: the style to use for the polygon
    """
    return folium.Polygon(
        locations=[p.lat_lon for p in plot_coords],
        fill_color=style.fill_color,
        fill=style.fill,
        fill_opacity=style.fill_opacity,
        color=style.color,
        weight=style.weight,
        tooltip=feature_kind,
    )
