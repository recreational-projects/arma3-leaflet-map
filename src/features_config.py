"""Classify input data."""

from enum import Enum

IGNORED_FEATURE_KIND_THRESHOLD = 1000
"""NB: Used to ignore feature kinds with too many members which would
affect performance."""

FeatureGeometryKind = Enum(
    "FeatureGeometryKind", ["POINT", "POLY_LINE", "POLYGON", "MULTI_POLYGON"]
)

FEATURE_GEOMETRIES = {
    # Classify features from 'geojson' root dir:
    "bush": FeatureGeometryKind.POINT,
    "busstop": FeatureGeometryKind.POINT,
    "bunker": FeatureGeometryKind.POINT,
    "chapel": FeatureGeometryKind.POINT,
    "church": FeatureGeometryKind.POINT,
    "cross": FeatureGeometryKind.POINT,
    "fortress": FeatureGeometryKind.POINT,
    "fountain": FeatureGeometryKind.POINT,
    "fuelstation": FeatureGeometryKind.POINT,
    "hospital": FeatureGeometryKind.POINT,
    "lighthouse": FeatureGeometryKind.POINT,
    "mounts": FeatureGeometryKind.POINT,  # extra attributes not handled yet
    "powersolar": FeatureGeometryKind.POINT,
    "powerwave": FeatureGeometryKind.POINT,
    "powerwind": FeatureGeometryKind.POINT,
    "quay": FeatureGeometryKind.POINT,
    "rock": FeatureGeometryKind.POINT,
    # rocks not yet handled
    "ruin": FeatureGeometryKind.POINT,
    "shipwreck": FeatureGeometryKind.POINT,
    "stack": FeatureGeometryKind.POINT,
    "tourism": FeatureGeometryKind.POINT,
    "transmitter": FeatureGeometryKind.POINT,
    "tree": FeatureGeometryKind.POINT,
    "view-tower": FeatureGeometryKind.POINT,
    "watertower": FeatureGeometryKind.POINT,
    # poly lines:
    "powerline": FeatureGeometryKind.POLY_LINE,
    "railway": FeatureGeometryKind.POLY_LINE,
    # polygons:
    "river": FeatureGeometryKind.POLYGON,
    "runway": FeatureGeometryKind.POLYGON,
    "house": FeatureGeometryKind.POLYGON,  # extra attributes not handled yet
    # multi polygons:
    "forest": FeatureGeometryKind.MULTI_POLYGON,
}
IGNORED_LOCATIONS = {
    # Features from 'geojson/locations' dir that should not be loaded (yet):
    "flatarea",
    "flatareacity",
    "flatareacitysmall",
    "strongpointarea",
}
BRIDGE_ROADS = {
    # GEOJSON `Polygon`s from 'geojson/roads' dir:
    "main_road-bridge",
    "road-bridge",
    "track-bridge",
}
