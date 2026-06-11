# arma3-leaflet-map

A proof of concept to create [Leaflet](https://leafletjs.com/) interactive maps
from Arma 3 maps. Uses [Folium](https://python-visualization.github.io/folium/)
to produce the maps in Python.

## Prerequisites

A folder containing maps data exported with
[Gruppe Adler Map Exporter](https://github.com/gruppe-adler/grad_meh) ('grad_meh').

This document assumes `uv` is installed, but not required.

## Installation

Clone the repo, e.g.:

```shell
git clone https://github.com/recreational-projects/arma3-leaflet-map
```
Create a Python environment and install the dependencies, e.g:
```shell
uv pip install .
```

## Usage
- Edit `_setup.py` so that:
  - `INPUT_DATA_RELATIVE_DIR` points to the folder containing
    the grad_meh maps data
  - `OUTPUT_RELATIVE_DIR` points to the folder where the maps should be saved
- To plot a single map:
  - Edit `plot_map.py` so that `MAP_NAME` points to the required map
  - Run `plot_map.py`
- To plot all maps:
  - Run `plot_all_maps.py`
- Each HTML file represents a single Arma 3 map; open in a browser
- NB: the HTML files can be large, between 10 MB and 150 MB

## Screenshot (v0.1.0)

![Screenshot of Altis map](docs/screenshot.png)

## What's included in the maps

- A very low-res satellite image
- Icon marker layers for each kind of point feature and location
- Layers for almost all other features: roads/tracks/trails, powerlines, railways,
  rivers, runways, forests, buildings 
- However, to keep file sizes and HTML rendering time manageable, layers are excluded
  if they would contain more than 1000 objects