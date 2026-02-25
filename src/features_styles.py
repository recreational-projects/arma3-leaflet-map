"""Configure feature appearance."""

from typing import Any

ICONS: dict[str, str] = {
    # feature_kind: icon name
    "bunker": "x",
    "bush": "seedling",
    "busstop": "bus-simple",
    "chapel": "place-of-worship",
    "church": "church",
    "cross": "cross",
    "fortress": "fort-awesome",
    "fountain": "shower",
    "fuelstation": "gas-pump",
    "hospital": "hospital",
    "lighthouse": "landmark",
    "mounts": "mountain",
    "powersolar": "solar-panel",
    "powerwave": "house-tsunami",
    "powerwind": "fan",
    "rock": "x",
    "ruin": "x",
    "tree": "tree",
    "quay": "anchor",
    "shipwreck": "skull-crossbones",
    "stack": "x",
    "transmitter": "tower-cell",
    "tourism": "x",
    "view-tower": "tower-observation",
    "watertower": "droplet",
    # locations:
    "airport": "plane",
    "bordercrossing": "road-barrier",
    "flatarea": "o",
    "flatareacity": "o",
    "flatareacitysmall": "o",
    "hill": "mound",
    "name": "x",
    "namecitycapital": "landmark-flag",
    "namecity": "city",
    "citycenter": "arrows-to-dot",
    "namevillage": "building",
    "namelocal": "x",
    "namemarine": "water",
    "namewaterlocal": "water",
    "rockarea": "hill-rockslide",
    "strategic": "x",
    "strongpointarea": "x",
    "vegetationbroadleaf": "leaf",
    "vegetationfir": "tree",
    "vegetationpalm": "tree",
    "vegetationvineyard": "plant-wilt",
    "viewpoint": "eye",
}

ICON_COLORS: dict[str, str] = {
    # feature_kind: color
    # water:
    "powerwave": "blue",
    "quay": "blue",
    "shipwreck": "blue",
    "namemarine": "blue",
    # buildings:
    "chapel": "purple",
    "church": "purple",
    "fortress": "purple",
    "fuelstation": "purple",
    "hospital": "purple",
    "airport": "purple",
    "bordercrossing": "purple",
    # settlements:
    "namecitycapital": "darkpurple",
    "namecity": "darkpurple",
    "citycenter": "darkpurple",
    "namevillage": "darkpurple",
    # physical:
    "hill": "beige",
    "rockarea": "beige",
    "mounts": "beige",
    "rock": "beige",
    # vegetation:
    "bush": "green",
    "vegetationbroadleaf": "green",
    "vegetationfir": "green",
    "locations-vegetationpalm": "green",
    "locations-vegetationvineyard": "green",
    "tree": "green",
    # low importance:
    "locations-namelocal": "lightgray",
}

LINE_STYLES: dict[str, dict[str, Any]] = {
    "main_road": {
        "color": "orange",
        "weight": 4,
    },
    "road": {
        "color": "yellow",
        "weight": 2,
    },
    "track": {
        "color": "white",
        "weight": 2,
    },
    "trail": {
        "color": "gray",
        "weight": 1,
        "dash_array": "4 2",
    },
    "hide": {
        "color": "red",
        "weight": 10,
        "dash_array": "0.001 20",  # dots
    },
    "powerline": {
        "color": "purple",
        "weight": 1,
    },
    "railway": {
        "color": "black",
        "weight": 2,
    },
    "highway": {
        # xcam_taunus
        "color": "red",
        "weight": 6,
    },
}

POLYGON_STYLES: dict[str, dict[str, str]] = {
    # Includes multipolygon
    "forest": {
        "fill_color": "green",
    },
    "house": {
        "fill_color": "gray",
    },
    "river": {
        "fill_color": "blue",
    },
    "runway": {
        "fill_color": "gray",
    },
}
