"""
Partial implementation of GeoJSON spec.

Derived from https://jcristharif.com/msgspec/examples/geojson.html.
"""

from typing import Any

import msgspec

Position = tuple[float | None, float | None]
# allow None as it exists in source data (esseker house)


class Point(msgspec.Struct, tag=True):
    """Point Geometry type."""

    coordinates: Position


class LineString(msgspec.Struct, tag=True):
    """LineString Geometry type."""

    coordinates: list[Position]


class Polygon(msgspec.Struct, tag=True):
    """Polygon Geometry type."""

    coordinates: list[list[Position]]


class MultiPolygon(msgspec.Struct, tag=True):
    """MultiPolygon Geometry type."""

    coordinates: list[list[list[Position]]]


Geometry = (
        Point
        #     | MultiPoint
        | LineString
        #     | MultiLineString
        | Polygon
        | MultiPolygon
    #     | GeometryCollection
)


class Feature(msgspec.Struct, tag=True):
    """Feature class."""

    geometry: Geometry | None = None
    properties: dict[str, Any] | None = None  # additional dict type params
    id: str | int | None = None