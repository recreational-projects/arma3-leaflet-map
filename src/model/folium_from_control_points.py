"""
Adapters to return Folium objects in `PlotCoordinate` terms
from`TerritoryControlPoint`s.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import folium

from .folium import empty_feature_group
from .plot_coordinate import PlotCoordinate

if TYPE_CHECKING:
    from collections.abc import Collection

    from src.styles import TextStyle

    from .arma3_leaflet_map import TerritoryControlPoint


def text_marker_group(
    *,
    feature_kind: str,
    control_points: Collection[TerritoryControlPoint],
    style: TextStyle,
) -> folium.FeatureGroup:
    """
    Return `folium.FeatureGroup` of `folium.Marker`s
    from `TerritoryControlPoint`s.
    """
    feature_group = empty_feature_group(
        feature_kind=feature_kind, feature_count=len(control_points), show=True
    )
    for control_point in control_points:
        plot_coords = PlotCoordinate.from_a3_position(control_point.position)
        html_tag_ = f"<div style='white-space:nowrap; color: {style.color}"
        if style.font_style:
            html_tag_ += f"; font-style: {style.font_style}"
        if style.font_size:
            html_tag_ += f"; font-size: {style.font_size}"

        html_tag_ += ";'>"
        name_ = control_point.name.replace("_", " ").capitalize()
        _html = f"{html_tag_}{name_}</>"
        marker = folium.Marker(
            location=plot_coords.xy,
            icon=folium.DivIcon(html=_html),
        )
        marker.add_to(feature_group)

    return feature_group
