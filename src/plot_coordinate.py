"""`PlotCoordinate` class."""

from dataclasses import dataclass
from typing import Self

from src.geo_json import feature as geo_json

_DEGREES_LATITUDE_TO_M = 110574
_DEGREES_LONGITUDE_TO_M = 111320


@dataclass(kw_only=True, frozen=True)
class PlotCoordinate:
    """Nominal lat, long at the equator."""

    x: float
    y: float

    @property
    def xy(self) -> tuple[float, float]:
        """Return (x, y) tuple."""
        return self.x, self.y

    @classmethod
    def from_position(cls, position: geo_json.Position) -> Self:
        """Ignores any z. Note axis order switch."""
        x = position[1]
        y = position[0]
        if x is None or y is None:
            raise TypeError

        return cls(x=x / _DEGREES_LATITUDE_TO_M, y=y / _DEGREES_LONGITUDE_TO_M)
