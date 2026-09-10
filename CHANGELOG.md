# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## UNRELEASED - TBC

### Changed

- Dependencies: bump arma3-offline-map-lib to == 0.10.0

## [0.7.1] - 2026-07-29

### Fixed

- Territories and control points were flipped in x/y

### Changed

- Dependencies: bump arma3-offline-map-lib to == 0.7.0

## [0.7.0] - 2026-07-27

### Added

- Experimental support for plotting territories around control points
- Improvements to error and logging messages

### Changed

- Don't allow line breaks in text labels
- Require Python >=3.13
- Dependencies: bump pillow to >= 12.3.0

## [0.6.0] - 2026-07-06

### Added

- Simple title block
- 'house' layer (all buildings, hedges, some rocks) rendered in color
- Always create required working/output directories
- pre-commit
- CI: `ruff format`

### Fixed

- Preview image filepath handling

### Changed

- Improved `README.md`
- CI: use existing `uv.lock`, use pyrefly instead of ty for type checking
- Dependencies: bump arma3-offline-map-lib to == 0.6.0


## [0.5.0] - 2026-06-24

Interim release

[0.7.1]: https://github.com/recreational-projects/arma3-leaflet-map/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/recreational-projects/arma3-leaflet-map/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/recreational-projects/arma3-leaflet-map/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/recreational-projects/arma3-leaflet-map/releases/tag/v0.5.0
