"""Configure feature appearance."""

import logging
from dataclasses import dataclass

ICON_COLORS = {
    "green",
    "gray",
    "cadetblue",
    "darkpurple",
    "pink",
    "lightred",
    "darkgreen",
    "lightblue",
    "darkred",
    "purple",
    "blue",
    "orange",
    "black",
    "beige",
    "red",
    "lightgreen",
    "darkblue",
    "lightgray",
    "white",
}
_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class BaseStyle:
    """Define style."""

    color: str = "red"  # prominent default to highlight missing styles
    show: bool = True


@dataclass(kw_only=True, frozen=True)
class MarkerStyle(BaseStyle):
    """Define style for point feature. Creates a `folium.Marker`."""

    icon_name: str = ""
    """From https://fontawesome.com/search?q=tower&ip=classic&ic=free-collection"""

    def __post_init__(self) -> None:
        if self.color not in ICON_COLORS:
            err_msg = f"Invalid color for icon: {self.color}"
            raise RuntimeError(err_msg)


@dataclass(kw_only=True, frozen=True)
class CircleMarkerStyle(BaseStyle):
    """Define style for point feature. Creates a `folium.CircleMarker`."""

    radius: float = 7
    """Pixel, i.e. does not vary with zoom."""
    fill_opacity: float = 0.5


@dataclass(kw_only=True, frozen=True)
class CircleStyle(BaseStyle):
    """Define style for point feature. Creates a `folium.Circle`."""

    radius: float = 7
    """Meters."""
    fill_opacity: float = 0.5


@dataclass(kw_only=True, frozen=True)
class LineStyle(BaseStyle):
    """Define style for line features."""

    weight: float = 4
    dash_array: str = ""


@dataclass(kw_only=True, frozen=True)
class PolygonStyle(BaseStyle):
    """Define style for (multi)polygon features."""


POINT_STYLES: dict[str, MarkerStyle | CircleMarkerStyle | CircleStyle] = {
    # power infra:
    "powerwave": MarkerStyle(color="purple", icon_name="house-tsunami"),
    "powersolar": MarkerStyle(color="purple", icon_name="solar-panel"),
    "powerwind": MarkerStyle(color="purple", icon_name="fan"),
    # buildings:
    "airport": MarkerStyle(color="gray", icon_name="plane"),
    "bordercrossing": MarkerStyle(color="gray", icon_name="road-barrier"),
    "bunker": MarkerStyle(color="gray", icon_name="warehouse"),
    "chapel": MarkerStyle(color="gray", icon_name="place-of-worship"),
    "church": MarkerStyle(color="gray", icon_name="church"),
    "cross": MarkerStyle(color="gray", icon_name="cross"),
    "fortress": MarkerStyle(color="gray", icon_name="fort-awesome"),
    "fountain": MarkerStyle(color="gray", icon_name="shower"),
    "fuelstation": MarkerStyle(color="gray", icon_name="gas-pump"),
    "hospital": MarkerStyle(color="gray", icon_name="hospital"),
    "lighthouse": MarkerStyle(color="gray", icon_name="landmark"),
    "quay": MarkerStyle(color="gray", icon_name="anchor"),
    "ruin": MarkerStyle(color="gray"),
    "stack": MarkerStyle(color="gray"),
    "transmitter": MarkerStyle(color="gray", icon_name="tower-cell"),
    "view-tower": MarkerStyle(color="gray", icon_name="tower-observation"),
    "watertower": MarkerStyle(color="gray", icon_name="droplet"),
    "busstop": MarkerStyle(color="gray", icon_name="bus-simple"),
    # settlements:
    "namecitycapital": MarkerStyle(color="darkpurple", icon_name="landmark-flag"),
    "namecity": MarkerStyle(color="darkpurple", icon_name="city"),
    "citycenter": MarkerStyle(color="darkpurple", icon_name="arrows-to-dot"),
    "namevillage": MarkerStyle(color="darkpurple", icon_name="building"),
    # physical:
    "hill": MarkerStyle(color="beige", icon_name="mound"),
    "rockarea": MarkerStyle(color="beige", icon_name="hill-rockslide"),
    # vegetation:
    "vegetationbroadleaf": MarkerStyle(color="green", icon_name="leaf"),
    "vegetationfir": MarkerStyle(color="green", icon_name="tree"),
    "vegetationpalm": MarkerStyle(color="green", icon_name="tree"),
    "vegetationvineyard": MarkerStyle(color="green", icon_name="plant-wilt"),
    "tree": CircleStyle(color="green", radius=2, show=False),
    "bush": CircleStyle(color="lightgreen", radius=1.5, show=False),
    # other:
    "tourism": MarkerStyle(),
    "viewpoint": MarkerStyle(icon_name="eye"),
    "shipwreck": MarkerStyle(color="blue", icon_name="skull-crossbones"),
    # minor place labels:
    "namemarine": CircleMarkerStyle(color="cyan"),
    "namewaterlocal": CircleMarkerStyle(color="dodgerblue"),
    "namelocal": CircleMarkerStyle(color="orange"),
    # other plotted as CircleMarker:
    "mounts": CircleMarkerStyle(color="beige", radius=7, show=False),
    "rock": CircleMarkerStyle(color="black", radius=3, show=False),
}

LINE_STYLES: dict[str, LineStyle] = {
    "main_road": LineStyle(color="orange", weight=4),
    "road": LineStyle(color="yellow", weight=2),
    "track": LineStyle(color="white", weight=2),
    "trail": LineStyle(color="gray", weight=1, dash_array="4 2"),
    "hide": LineStyle(color="red", weight=10, dash_array="0.001 20"),  # dots
    "powerline": LineStyle(color="purple", weight=1),
    "railway": LineStyle(color="black", weight=2),
    "highway": LineStyle(color="red", weight=6),  # xcam_taunus
}


POLYGON_STYLES: dict[str, PolygonStyle] = {
    "forest": PolygonStyle(color="green", show=False),
    "house": PolygonStyle(color="gray"),
    "river": PolygonStyle(color="blue"),
    "runway": PolygonStyle(color="gray"),
}
