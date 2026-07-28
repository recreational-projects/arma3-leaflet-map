"""`PlotCoordinate` class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from arma3_offline_map_lib.position_2d import Position2D

if TYPE_CHECKING:
    from arma3_offline_map_lib import geojson


_DEGREES_LATITUDE_TO_M_AT_EQUATOR = 110574
_DEGREES_LONGITUDE_TO_M_AT_EQUATOR = 111320


@dataclass(kw_only=True, frozen=True)
class PlotCoordinate:
    """Coordinate in lat/lon terms for plotting in a Folium map."""

    lon: float
    """Longitude."""
    lat: float
    """Latitude."""

    @property
    def lat_lon(self) -> tuple[float, float]:
        """Return (lat, lon) tuple as required by Folium."""
        return self.lat, self.lon

    @classmethod
    def from_grad_meh_position(cls, position: geojson.Position) -> Self:
        """
        Convert grad_meh position (GeoJSON y, x but meter units, arbitrary origin)
        to `PlotCoordinate`.

        Simple projection using equatorial degrees-to-meters ratio.

        Ignores any z.
        """
        pos_2d = Position2D.from_geojson_position(position)
        return cls(
            lon=pos_2d.x / _DEGREES_LONGITUDE_TO_M_AT_EQUATOR,
            lat=pos_2d.y / _DEGREES_LATITUDE_TO_M_AT_EQUATOR,
        )

    @classmethod
    def from_a3_position(cls, position: Position2D) -> Self:
        """
        Convert Arma 3 position (meter units, arbitrary origin)
        to `PlotCoordinate`.

        Simple projection using equatorial degrees-to-meters ratio.
        """
        return cls(
            lon=position.x / _DEGREES_LONGITUDE_TO_M_AT_EQUATOR,
            lat=position.y / _DEGREES_LATITUDE_TO_M_AT_EQUATOR,
        )
