"""TO DO."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.meh.modules.geojsonfeature import Feature as GeoJSONFeature


def geojson_gz_files_in_dir(path: Path) -> list[Path]:
    """Return all `*.geojson.gz` files in `path`."""
    return [p for p in list(path.iterdir()) if p.suffixes == [".geojson", ".gz"]]


def duplicates(seq: Sequence[Any]) -> set[Any]:
    """Return duplicate elements from `seq`."""
    seen = set()
    return {val for val in seq if (val in seen or seen.add(val))}


def summarise_features(features: dict[str, list[GeoJSONFeature]]) -> str:
    """Return a string summarizing features data."""
    if not features:
        return "None"
    texts = [
        f"{len(features)} {feature_kind}" for feature_kind, features in features.items()
    ]
    return ", ".join(texts)