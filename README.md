# Solar panel energy yield

Determine the solar panel energy yield in North Rhine Westphalia (NRW) using [OpenGeodata.NRW](https://www.opengeodata.nrw.de/produkte/) and OpenStreetMap.

![actual-energy-yield-extraction](docs/actual-energy-yield-extraction.png)

## Overview

The approach is described in my [blog post](https://kopytjuk.github.io/posts/solar-panel-analysis/).

![methodology](docs/methodology.png)

This project contains multiple command line tools (in order of execution):

1. `building-selector --help`
2. `image-cropper --help`
3. Solar panel segmentation (deep-learning based) is located in https://github.com/kopytjuk/solar-panel-segmentation
4. `energy-extractor --help`
5. `combine-results --help`


## Setup

The setup assumes that [pyenv](https://github.com/pyenv/pyenv) is installed and 
poetry is configured to use the currently active python version:

```
poetry config virtualenvs.prefer-active-python true
```

I.e. a virtual environment setup will use the python executable which it finds via `which python`.

Note that `.python-version`

### This repository

```shell
uv sync
# and run a single tool
uv run building-selector --help
```

### Segmentation model

In a separate terminal

```bash
cd ...  # your folder where you store your projects
git clone https://github.com/kopytjuk/solar-panel-segmentation

cd solar-panel-segmentation
poetry install
```

## Run everything at once


In a fresh shell session (not the one from VSCode), run

```
./scripts/run_full_pipeline.sh
```
