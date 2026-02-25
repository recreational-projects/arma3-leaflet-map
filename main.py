"""
TO DO.

NB: the source *.geojson.gz files are gzipped JSON arrays of GeoJSON features, not
GeoJSON compliant files.
"""

import json
import logging
from pathlib import Path

import folium
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from src.meh.features_styles import (
    FEATURE_ICONS,
)
from src.meh.modules.features_config import (
    IGNORED_FEATURE_KIND_THRESHOLD,
    IGNORED_LOCATIONS,
    IGNORED_ROADS,
    LINE_FEATURES,
    MULTIPOLYGON_FEATURES,
    POINT_FEATURES,
    POLYGON_FEATURES,
)
from src.meh.modules.load import load_features_from_dir
from src.meh.modules.utils import duplicates
from src.meh.plot import (
    image_overlay,
    plot_lines_multi_series,
    plot_markers_multi_series,
    plot_multipolygons_multi_series,
    plot_polygons_multi_series,
)

INPUT_DATA_RELATIVE_DIR = "../../source_data/grad_meh/"
OUTPUT_RELATIVE_DIR = "../../plots"
LOG_LEVEL = "INFO"


_LOG_FORMAT = "%(message)s"
logging.basicConfig(
    level=LOG_LEVEL, format=_LOG_FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)


def main() -> None:
    log_msg = f"IGNORED_FEATURE_KIND_THRESHOLD = {IGNORED_FEATURE_KIND_THRESHOLD}"
    logging.info(log_msg)

    duplicate_icons = duplicates(list(FEATURE_ICONS.values()))
    if duplicate_icons:
        log_msg = f"Non-unique icons: {duplicate_icons}"
        logging.warning(log_msg)

    source_dirs = list(SOURCE_DATA_PATH.iterdir())
    existing_plots = [fp.stem for fp in list(PLOT_PATH.iterdir())]
    dirs_to_plot = [fp for fp in source_dirs if fp.stem not in existing_plots]

    for map_name in existing_plots:
        log_msg = f"Map '{map_name}' already plotted - skipping."
        logging.warning(log_msg)

    log_msg = f"{len(dirs_to_plot)} maps to plot."
    logging.info(log_msg)

    if dirs_to_plot:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            "maps |",
            TimeElapsedColumn(),
            "elapsed |",
            TimeRemainingColumn(),
            "remaining",
        )

        with progress:
            task = progress.add_task("Working...", total=len(dirs_to_plot))

            while not progress.finished:
                for fp in dirs_to_plot:
                    plot_map(fp, PLOT_PATH)
                    progress.update(task, advance=1)


def plot_map(data_path: Path, plot_path: Path) -> None:
    """Plot Folium map from grad_meh output, and save."""
    metadata_filepath = data_path / "meta.json"
    preview_image_filepath = data_path / "preview.png"
    geojson_dirpath = data_path / "geojson"
    map_name = data_path.stem
    save_filepath = plot_path / f"{map_name}.html"

    log_msg = f"[bold]Map '{map_name}' loading...[/]"
    logging.info(log_msg, extra={"markup": True})

    metadata = json.loads(metadata_filepath.read_text())

    map_ = folium.Map(
        location=(0, 0),
        zoom_start=12,
        control_scale=True,  # Show a scale on the bottom of the map.
        prefer_canvas=True,  # for vector layers instead of SVG
        # crs="Simple",  # Don't use, as it seems to use pixels for plot units.
        tiles=None,
    )
    map_image_overlay = image_overlay(preview_image_filepath, metadata["worldSize"])
    if map_image_overlay:
        map_image_overlay.add_to(map_)

    multipolygon_features = load_features_from_dir(
        path=geojson_dirpath,
        include=MULTIPOLYGON_FEATURES,
        kind="multipolygon",
    )
    polygon_features = load_features_from_dir(
        path=geojson_dirpath,
        include=POLYGON_FEATURES,
        kind="polygon",
    )
    point_features = load_features_from_dir(
        path=geojson_dirpath,
        include=POINT_FEATURES,
        limit=IGNORED_FEATURE_KIND_THRESHOLD,
        kind="point",
    )
    locations = load_features_from_dir(
        path=geojson_dirpath / "locations",
        exclude=IGNORED_LOCATIONS,
        kind="location",
    )
    line_features = load_features_from_dir(
        path=geojson_dirpath,
        include=LINE_FEATURES,
        kind="non-road line",
    )
    roads_path = geojson_dirpath / "roads"
    if not roads_path.exists():
        roads = {}
        log_msg = "- No roads source data."
        logging.warning(log_msg)
    else:
        roads = load_features_from_dir(
            path=roads_path,
            exclude=IGNORED_ROADS,
            kind="road",
        )

    plot_multipolygons_multi_series(
        map_=map_,
        feature_multiseries=multipolygon_features,
    )
    plot_polygons_multi_series(
        map_=map_,
        feature_multiseries=polygon_features,
    )
    plot_markers_multi_series(
        map_=map_,
        feature_multiseries=point_features,
    )
    plot_markers_multi_series(
        map_=map_,
        feature_multiseries=locations,
    )
    plot_lines_multi_series(
        map_=map_,
        feature_multiseries=line_features,
    )
    plot_lines_multi_series(
        map_=map_,
        feature_multiseries=roads,
    )
    folium.LayerControl().add_to(map_)

    log_msg = f"Saving map '{save_filepath}'... "
    logging.info(log_msg)
    map_.save(save_filepath)
    log_msg = "...done."
    logging.info(log_msg)


if __name__ == "__main__":
    log = logging.getLogger("rich")
    BASE_PATH = Path(__file__).resolve().parent
    SOURCE_DATA_PATH = BASE_PATH / INPUT_DATA_RELATIVE_DIR
    PLOT_PATH = BASE_PATH / OUTPUT_RELATIVE_DIR
    main()