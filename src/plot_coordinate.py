"""`PlotCoordinate` class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from arma3_offline_map_lib import geojson
    from arma3_offline_map_lib.point_2d import Point2D

_DEGREES_LATITUDE_TO_M_AT_EQUATOR = 110574
_DEGREES_LONGITUDE_TO_M_AT_EQUATOR = 111320


@dataclass(kw_only=True, frozen=True)
class PlotCoordinate:
    """Longitude, latitude."""

    x: float
    """Longitude."""
    y: float
    """Latitude."""

    @property
    def xy(self) -> tuple[float, float]:
        """Return (x, y) tuple."""
        return self.x, self.y

    @classmethod
    def from_grad_meh_position(cls, position: geojson.Position) -> Self:
        """
        Convert grad_meh position (GeoJSON y, x but meter units, arbitrary origin)
        to `PlotCoordinate` (long, lat).

        Simple projection using equatorial degrees-to-meters ratio.

        Ignores any z. Note axis order switch.
        """
        x = position[1]
        y = position[0]
        if x is None or y is None:
            raise TypeError

        return cls(
            x=x / _DEGREES_LATITUDE_TO_M_AT_EQUATOR,
            y=y / _DEGREES_LONGITUDE_TO_M_AT_EQUATOR,
        )

    @classmethod
    def from_a3_position(cls, position: Point2D) -> Self:
        """
        Convert Arma 3 `Point2D` (meter units, arbitrary origin)
        to `PlotCoordinate` (long, lat).

        Simple projection using equatorial degrees-to-meters ratio.
        """
        return cls(
            x=position.x / _DEGREES_LATITUDE_TO_M_AT_EQUATOR,
            y=position.y / _DEGREES_LONGITUDE_TO_M_AT_EQUATOR,
        )
