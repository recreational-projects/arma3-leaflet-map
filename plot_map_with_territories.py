"""Plot a single map with territories."""

import logging
from typing import Any

from arma3_offline_map_lib.position_2d import Position2D

from src.features_config import IGNORED_FEATURE_KIND_THRESHOLD
from src.model.arma3_leaflet_map import Arma3LeafletMap, TerritoryControlPoint
from src.model.arma3_map_data import Arma3MapData
from src.setup import INPUT_PATH, OUTPUT_PATH, setup_logging

MAP_NAME = "rhspkl"
LOG_LEVEL = "INFO"

type DictNode = dict[str, Any]
"""For hinting nodes in generic nested dicts e.g. from JSON."""

CONTROL_POINTS = {
    "airports": [
        {"name": "airport_1", "position": {"x": 7238.7769, "y": 2474.9626}},
        {"name": "airport_2", "position": {"x": 1788.1172, "y": 2918.2334}},
        {"name": "airport_3", "position": {"x": 2827.2327, "y": 5083.0859}},
        {"name": "airport_4", "position": {"x": 7004.832, "y": 4999.501}},
    ],
    "factories": [
        {"name": "factory_1", "position": {"x": 4845.8848, "y": 1577.9124}},
        {"name": "factory_2", "position": {"x": 3555.7649, "y": 3553.95}},
        {"name": "factory_3", "position": {"x": 4644.019, "y": 4409.4683}},
    ],
    "bases": [
        {"name": "milbase_1", "position": {"x": 6107.1987, "y": 6699.4858}},
        {"name": "milbase_2", "position": {"x": 5683.3477, "y": 4199.3203}},
    ],
    "outposts": [
        {"name": "outpost_1", "position": {"x": 2281.5596, "y": 6514.6226}},
        {"name": "outpost_2", "position": {"x": 5785.3486, "y": 1966.72}},
        {"name": "outpost_3", "position": {"x": 3505.5449, "y": 5255.9585}},
        {"name": "outpost_4", "position": {"x": 4076.2886, "y": 2411.5894}},
        {"name": "outpost_5", "position": {"x": 4540.084, "y": 5471.5029}},
        {"name": "outpost_6", "position": {"x": 952.07123, "y": 1458.2797}},
        {"name": "outpost_7", "position": {"x": 5430.1826, "y": 2538.4832}},
        {"name": "outpost_8", "position": {"x": 2761.0474, "y": 1780.0126}},
        {"name": "outpost_9", "position": {"x": 3668.2725, "y": 2688.5989}},
        {"name": "outpost_10", "position": {"x": 5035.3193, "y": 5100.188}},
    ],
    "waterports": [
        {"name": "seaport_1", "position": {"x": 6602.5791, "y": 665.36407}},
        {"name": "seaport_2", "position": {"x": 6372.5811, "y": 2090.0891}},
        {"name": "seaport_3", "position": {"x": 3931.3618, "y": 3271.1609}},
    ],
    "resources": [
        {"name": "resource_1", "position": {"x": 4241.0654, "y": 861.86548}},
        {"name": "resource_2", "position": {"x": 1108.3755, "y": 4097.8818}},
        {"name": "resource_3", "position": {"x": 1244.0137, "y": 7296.2559}},
        {"name": "resource_4", "position": {"x": 3796.303, "y": 6536.7378}},
    ],
}


def main() -> None:
    """Application entry point."""
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger("rich")
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logger.info(log_msg)

    map_data = Arma3MapData.from_data(INPUT_PATH / MAP_NAME)
    if not map_data:
        err_msg = f"Unexpected data issue with {INPUT_PATH / MAP_NAME}."
        raise RuntimeError(err_msg)

    cp_data = [x for xs in CONTROL_POINTS.values() for x in xs]
    map_ = Arma3LeafletMap(
        map_data, territory_control_points=control_points_from_data(cp_data)
    )
    map_.render(OUTPUT_PATH)


def control_points_from_data(cp_data: list[DictNode]) -> set[TerritoryControlPoint]:
    """Structure control points from data."""
    control_points: set[TerritoryControlPoint] = set()
    for cp in cp_data:
        name_ = cp["name"]
        position_ = Position2D(**cp["position"])
        control_points.add(TerritoryControlPoint(name=name_, position=position_))

    return control_points


if __name__ == "__main__":
    main()
