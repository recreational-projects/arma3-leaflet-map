"""TO DO."""

import gzip
import logging
from pathlib import Path

import msgspec

from src.meh.modules.geojsonfeature import Feature as GeoJSONFeature
from src.meh.modules.utils import geojson_gz_files_in_dir, summarise_features


def load_features_from_dir(
        *,
        path: Path,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        limit: int | None = None,
        kind: str,
) -> dict[str, list[GeoJSONFeature]]:
    """
    Load features from files in a directory.

    Returns:
         `dict`. Keys are `FILENAME_STEM` for each relevant
         `path/{FILENAME_STEM}.geojson.gz`.

    """
    features: dict[str, list[GeoJSONFeature]] = {}

    if include and exclude:
        err_msg = "`include` and `exclude` cannot both be used."
        raise ValueError(err_msg)

    candidate_filepaths = geojson_gz_files_in_dir(path)

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
        raw_features = load_features_from_file(path=fp)

        if raw_features:
            if limit and len(raw_features) > limit:
                log_msg = (
                    f"- Too many '{feature_kind}' features "
                    f"({len(raw_features)}) - data ignored."
                )
                logging.warning(log_msg)
            else:
                features[feature_kind] = raw_features

    if not features:
        log_msg = f"- No {kind} features."
        logging.warning(log_msg)
    else:
        log_msg = f"- Loaded {kind} features: {summarise_features(features)}"
        logging.debug(log_msg)

    return features


def load_features_from_file(
        *,
        path: Path,
) -> list[GeoJSONFeature]:
    """
    Load features from a `.geojson.gz` file.

    NB: grad_meh source files are gzipped JSON arrays of GeoJSON features, not GeoJSON
    compliant files.
    """
    with gzip.open(path, "rt", encoding="utf-8") as file:
        features = msgspec.json.decode(file.read(), type=list[GeoJSONFeature])

    if features is None:
        log_msg = f"- No valid features in `{path.name}`."
        logging.warning(log_msg)
        return []

    return features