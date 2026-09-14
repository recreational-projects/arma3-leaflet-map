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
    # Generic objects:
    # ref: https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#2-generic-objects
    "bunker": FeatureGeometryKind.POINT,
    "bush": FeatureGeometryKind.POINT,
    "busstop": FeatureGeometryKind.POINT,
    "chapel": FeatureGeometryKind.POINT,
    "church": FeatureGeometryKind.POINT,
    "cross": FeatureGeometryKind.POINT,
    "fortress": FeatureGeometryKind.POINT,
    "fountain": FeatureGeometryKind.POINT,
    "fuelstation": FeatureGeometryKind.POINT,
    "hospital": FeatureGeometryKind.POINT,
    "lighthouse": FeatureGeometryKind.POINT,
    "powersolar": FeatureGeometryKind.POINT,
    "powerwave": FeatureGeometryKind.POINT,
    "powerwind": FeatureGeometryKind.POINT,
    "quay": FeatureGeometryKind.POINT,
    "rock": FeatureGeometryKind.POINT,
    "ruin": FeatureGeometryKind.POINT,
    "shipwreck": FeatureGeometryKind.POINT,
    "stack": FeatureGeometryKind.POINT,
    "tourism": FeatureGeometryKind.POINT,
    "transmitter": FeatureGeometryKind.POINT,
    "tree": FeatureGeometryKind.POINT,
    "view-tower": FeatureGeometryKind.POINT,
    "watertower": FeatureGeometryKind.POINT,
    # Mounts
    # https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#13-mounts
    "mounts": FeatureGeometryKind.POINT,  # extra attributes not handled yet
    # Houses:
    # ref: https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#3-houses
    "house": FeatureGeometryKind.POLYGON,  # some extra attributes not handled yet
    # Rocks
    # ref: https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#4-rocks
    # "rocks" not yet handled
    # Forests:
    # ref: https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#5-forests
    "forest": FeatureGeometryKind.MULTI_POLYGON,
    # Railways
    # ref: https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#6-railways
    "railway": FeatureGeometryKind.POLY_LINE,
    # Power lines
    # ref: https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#7-power-lines
    "powerline": FeatureGeometryKind.POLY_LINE,
    # Runways
    # https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#8-runways
    "runway": FeatureGeometryKind.POLYGON,
    # Rivers
    # https://github.com/gruppe-adler/grad_meh/blob/master/docs/geojson_spec.md#12-rivers
    "river": FeatureGeometryKind.POLYGON,
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
