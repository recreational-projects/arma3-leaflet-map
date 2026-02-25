"""Load GeoJSON features from files."""

import gzip
import logging
from pathlib import Path

import msgspec

from src.geo_json.feature import Feature as GeoJSONFeature

_LOGGER = logging.getLogger(__name__)


def _load_features_from_file(*, path: Path) -> list[GeoJSONFeature]:
    """
    Load features from a `.geojson.gz` file.

    NB: grad_meh source files are gzipped JSON arrays of GeoJSON features, not GeoJSON
    compliant files.
    """
    with gzip.open(path, "rt", encoding="utf-8") as file:
        features = msgspec.json.decode(file.read(), type=list[GeoJSONFeature])

    if features is None:
        log_msg = f"- No valid features in `{path.name}`."
        _LOGGER.warning(log_msg)
        return []

    return features


def _summarise_features(features: dict[str, list[GeoJSONFeature]]) -> str:
    """Return a string summarizing features data."""
    if not features:
        return "None"
    texts = [
        f"{len(features)} {feature_kind}" for feature_kind, features in features.items()
    ]
    return ", ".join(texts)


def load_features_from_dir(
    *,
    path: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    limit: int | None = None,
    kind: str,
) -> dict[str, list[GeoJSONFeature]]:
    """
    Load features from `.geojson.gz` files in a directory.

    Returns:
         `dict`. Keys are `FILENAME_STEM` for each relevant
         `path/{FILENAME_STEM}.geojson.gz`.

    """
    features: dict[str, list[GeoJSONFeature]] = {}

    if include and exclude:
        err_msg = "`include` and `exclude` cannot both be used."
        raise RuntimeError(err_msg)

    candidate_filepaths = [
        p for p in list(path.iterdir()) if p.suffixes == [".geojson", ".gz"]
    ]
    if include:
        filepaths = [
            fp
            for fp in candidate_filepaths
            if fp.stem.removesuffix(".geojson") in include
        ]
    elif exclude:
        filepaths = [
            fp
            for fp in candidate_filepaths
            if fp.stem.removesuffix(".geojson") not in exclude
        ]
    else:
        filepaths = candidate_filepaths

    for fp in filepaths:
        feature_kind = fp.stem.removesuffix(".geojson")
        raw_features = _load_features_from_file(path=fp)

        if raw_features:
            if limit and len(raw_features) > limit:
                log_msg = (
                    f"- Too many '{feature_kind}' features "
                    f"({len(raw_features)}) - data ignored."
                )
                _LOGGER.warning(log_msg)
            else:
                features[feature_kind] = raw_features

    if not features:
        log_msg = f"- No {kind} features."
        _LOGGER.warning(log_msg)
    else:
        log_msg = f"- Loaded {kind} features: {_summarise_features(features)}"
        _LOGGER.debug(log_msg)

    return features
