"""Classify input data."""

POINT_FEATURES = [
    # GeoJSON `Point`s from 'geojson' root dir, to be plotted as markers:
    "bush",
    "busstop",
    "bunker",
    "chapel",
    "church",
    "cross",
    "fortress",
    "fountain",
    "fuelstation",
    "hospital",
    "lighthouse",
    "mounts",  # extra attributes not handled yet
    "powersolar",
    "powerwave",
    "powerwind",
    "quay",
    "rock",
    "ruin",
    "shipwreck",
    "stack",
    "tourism",
    "transmitter",
    "tree",
    "view-tower",
    "watertower",
]
LINE_FEATURES = [
    # GeoJSON `LineString`s from 'geojson' root dir, to be plotted as polylines:
    "powerline",
    "railway",
]
POLYGON_FEATURES = [
    # GEOJSON `Polygon`s from 'geojson' root dir:
    "river",
    "runway",
    "house",  # extra attributes not yet handled
]
MULTIPOLYGON_FEATURES = [
    # GEOJSON `MultiPolygon`s from 'geojson' root dir, to be plotted as polygons:
    "forest",
]
IGNORED_LOCATIONS = [
    # Features from 'geojson/locations' dir that should not be loaded (yet):
    # irrelevant:
    "flatarea",
    "flatareacity",
    "flatareacitysmall",
    "strongpointarea",
    "fedroad071",  # wl_rosche: road name label
    "fedroad191",  # wl_rosche: road name label
    "fedroad493",  # wl_rosche: road name label
    "ruslandicon_p148",  # beketov: road name label
]
IGNORED_ROADS = [
    # Features from 'geojson/roads' dir that should not be loaded (yet):
    # not lines:
    "main_road-bridge",
    "road-bridge",
    "track-bridge",
]
IGNORED_FEATURE_KIND_THRESHOLD = 1000
"""NB: Used to ignore feature kinds with too many members which would
affect performance."""