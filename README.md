# Solar panel roof coverage

Determine the solar roof coverage in North Rhine Westphalia (NRW) using [OpenGeodata.NRW](https://www.opengeodata.nrw.de/produkte/) and OpenStreetMap.

## Setup

1. Install `pyenv` (to make use of `.python-version`)
2. Install poetry to install all requirements
3. Initialize the project `poetry install`

## Tools

### Building-Selector

Given a tile name and an output folder outputs a `gpkg` file with buildings and their GPS coordinates

```shell
building-selector 511_5701_1 results
```

### Image-Cropper

Given a `gpkg` file with buildings and their WGS84 coordinates, crop aerial images out of large aerial tiles for later solar panel detection.

```shell
image-cropper results/511_5701_1_buildings.gpkg results/images
```