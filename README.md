# arma3-leaflet-map

A proof of concept to create Arma 3 [Leaflet](https://leafletjs.com/) interactive maps
from [Gruppe Adler Map Exporter](https://github.com/gruppe-adler/grad_meh) ('grad_meh')
output.

Uses the [Folium](https://python-visualization.github.io/folium/) 
Leaflet library to produce the maps in Python.

## Prerequisites

A folder containing maps data exported with grad_meh.

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
Edit `config.toml` so that:
- `input_relative_dir` points to the folder containing
  the grad_meh maps data
- `output_relative_dir` points to the folder where the maps should be saved

### To plot a single map:
Edit `plot_map.py` so that `MAP_NAME` points to the required map, then:
```shell
uv run plot_map.py 
```

### To plot all maps in the folder
```shell
uv run plot_all_maps.py 
```

Each map can take up to around 60&nbsp;s to produce.

## Output

Each Leaflet maps is saved in `output_relative_dir` as a self-contained HTML file.
Open in a browser to view.

NB: the HTML files can be large, up to about 150&nbsp;MB.

### Screenshot (v0.5.0)

![Screenshot of Altis map](docs/screenshot_050_altis.png)

### What's included in the maps

- A simple land/sea image
- A very low-res satellite image
- Layers for roads/tracks/trails, bridges, powerlines, railways,
  rivers, runways, forests, buildings
- Icon marker layers for each kind of point feature
- Text labels for each kind of location (settlements etc.)
- NB: to keep file sizes and HTML rendering time manageable, layers are excluded
  if they would contain more than 1000 objects