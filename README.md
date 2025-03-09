# Solar panel roof coverage

Determine the solar roof coverage in North Rhine Westphalia (NRW) using [OpenGeodata.NRW](https://www.opengeodata.nrw.de/produkte/) and OpenStreetMap.

## Setup

1. Install `pyenv` (to make use of `.python-version`)
2. Install poetry to install all requirements
3. Initialize the project `poetry install`

## Run everything at once


In a fresh shell session (not the one from VSCode), run

```
./scripts/run_full_pipeline.sh
```

## Hello world Docker

1. Build the Docker image:

```bash
docker build -t hello-world-python .
```

2. Run the Docker container:

```bash
docker run hello-world-python
```
