"""Configure feature appearance."""

import logging
from dataclasses import dataclass

LAND_COLOR_RGB = (230, 230, 230)  # light gray
WATER_COLOR_RGB = (183, 203, 230)  # light blue
"""Used for land/sea image as well as feature styles."""

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
    """HTML format."""
    show: bool = True


@dataclass(kw_only=True, frozen=True)
class MarkerStyle(BaseStyle):
    """Define style for point feature. Creates a `folium.Marker`."""

    show: bool = False
    icon_name: str = ""
    """From https://fontawesome.com/search?q=tower&ip=classic&ic=free-collection"""

    def __post_init__(self) -> None:
        if self.color not in ICON_COLORS:
            err_msg = f"Invalid color for icon: {self.color}"
            raise RuntimeError(err_msg)


@dataclass(kw_only=True, frozen=True)
class CircleMarkerStyle(BaseStyle):
    """Define style for point feature. Creates a `folium.CircleMarker`."""

    show: bool = False
    radius: float = 7
    """Pixel, i.e. does not vary with zoom."""
    fill_opacity: float = 0.5


@dataclass(kw_only=True, frozen=True)
class CircleStyle(BaseStyle):
    """Define style for point feature. Creates a `folium.Circle`."""

    show: bool = False
    radius: float = 7
    """Meters."""
    fill_opacity: float = 0.5


@dataclass(kw_only=True, frozen=True)
class LineStyle(BaseStyle):
    """Define style for line features."""

    weight: float = 4
    opacity: float = 1
    dash_array: str = ""


@dataclass(kw_only=True, frozen=True)
class PolygonStyle(BaseStyle):
    """Define style for (multi)polygon features."""

    weight: float = 1
    fill: bool = True  # NB: overridden if `fill_color` is set
    fill_color: str | None = None
    fill_opacity: float = 1


@dataclass(kw_only=True, frozen=True)
class TextStyle(BaseStyle):
    """Define style for text features."""

    font_size: str | None = None
    font_style: str | None = None


GRID_STYLE = LineStyle(color="black", weight=1, opacity=0.25)
POINT_STYLES: dict[str, MarkerStyle | CircleMarkerStyle | CircleStyle] = {
    # power infra:
    "powerwave": MarkerStyle(color="purple", icon_name="house-tsunami"),
    "powersolar": MarkerStyle(color="purple", icon_name="solar-panel"),
    "powerwind": MarkerStyle(color="purple", icon_name="fan"),
    # buildings:
    # "bordercrossing": MarkerStyle(color="gray", icon_name="road-barrier"),
    "bunker": MarkerStyle(color="gray", icon_name="warehouse"),
    "chapel": MarkerStyle(color="gray", icon_name="place-of-worship"),
    "church": MarkerStyle(color="gray", icon_name="church"),
    "cross": MarkerStyle(color="gray", icon_name="cross"),
    # "fortress": MarkerStyle(color="gray", icon_name="fort-awesome"),
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
    # physical:
    # "hill": MarkerStyle(color="beige", icon_name="mound"),
    # vegetation:
    "tree": CircleStyle(color="green", radius=2),
    "bush": CircleStyle(color="lightgreen", radius=1.5),
    # other:
    "tourism": MarkerStyle(),
    "shipwreck": MarkerStyle(color="blue", icon_name="skull-crossbones"),
    # other plotted as CircleMarker:
    "mounts": CircleMarkerStyle(color="beige", radius=7),
    "rock": CircleMarkerStyle(color="black", radius=3),
}
TEXT_STYLES = {
    "namecitycapital": TextStyle(color="black", font_size="1.5rem"),
    "namecity": TextStyle(color="black", font_size="1.25rem"),
    "namevillage": TextStyle(color="black"),
    "namelocal": TextStyle(color="dimgray", font_style="oblique"),
    "namemarine": TextStyle(color="blue"),
    # "namewaterlocal": TextStyle(color="blue", font_style="oblique"),
    "airport": TextStyle(color="dimgray"),
    "hill": TextStyle(color="dimgray"),  # not always named
    "rockarea": TextStyle(color="dimgray"),  # not always named?
    "citycenter": TextStyle(),  # not named?
    "vegetationbroadleaf": TextStyle(color="green"),
    "vegetationvineyard": TextStyle(color="green"),
    "vegetationfir": TextStyle(color="green"),
    # "vegetationpalm": TextStyle(color="green"),
    "viewpoint": TextStyle(color="red"),
}
LINE_STYLES: dict[str, LineStyle] = {
    "powerline": LineStyle(color="purple", weight=1),
    "railway": LineStyle(color="black", weight=1),
}
_TRAIL_COLOR = "gray"
_TRACK_COLOR = "white"
_ROAD_COLOR = "yellow"
_MAIN_ROAD_COLOR = "orange"

ROAD_STYLES: dict[str, LineStyle] = {
    # "hide": LineStyle(color="red", weight=10, dash_array="0.001 20"), # dots
    "trail": LineStyle(color=_TRAIL_COLOR, weight=1, dash_array="4 2"),
    "track": LineStyle(color="white", weight=2),
    "road": LineStyle(color="yellow", weight=2),
    "main_road": LineStyle(color="orange", weight=4),
}
"""For roads, dict order determines plot order."""

BRIDGE_STYLES: dict[str, PolygonStyle] = {
    "trail-bridge": PolygonStyle(color=_TRAIL_COLOR, fill_color=_TRAIL_COLOR),
    "track-bridge": PolygonStyle(color=_TRACK_COLOR, fill_color=_TRACK_COLOR),
    "road-bridge": PolygonStyle(color=_ROAD_COLOR, fill_color=_ROAD_COLOR),
    "main_road-bridge": PolygonStyle(
        color=_MAIN_ROAD_COLOR, fill_color=_MAIN_ROAD_COLOR
    ),
}
"""For bridges, dict order determines plot order."""

POLYGON_STYLES: dict[str, PolygonStyle] = {
    "forest": PolygonStyle(color="green", fill_color="green", show=False),
    "river": PolygonStyle(
        color=f"rgb{WATER_COLOR_RGB}", fill_color=f"rgb{WATER_COLOR_RGB}"
    ),
    "runway": PolygonStyle(color="gray", fill_color="gray"),
}
"""'house' layer uses default `PolygonStyle` with color retrieved from GeoJSON."""

TERRITORY_STYLE = PolygonStyle(color="red", fill=False, weight=0.5)
CONTROL_POINT_STYLE = TextStyle(color="red")
