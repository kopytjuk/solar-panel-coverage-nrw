import shutil
from pathlib import Path

import click
from shapely.geometry import box

from utils import (
    get_bounding_box_from_tile_name,
    get_buildings_from_bbox,
    transform_utm32N_to_wgs84_geometry,
)


@click.command()
@click.argument("tile_name", type=click.STRING)
@click.argument("output_location", type=click.Path(exists=True))
@click.option(
    "--osm-data-path",
    type=click.Path(exists=True),
    default="data/osm_buildings.geojson",
)
def extract_buildings(
    tile_name: str, output_location: str, osm_data_path: str
):
    click.echo(f"Processing tile: {tile_name}")
    click.echo(f"Saving output to: {output_location}")

    output_location = Path(output_location)

    # Clear output location if it exists
    if output_location.exists():
        shutil.rmtree(str(output_location))
    output_location.mkdir(parents=True, exist_ok=True)

    # Get bounding box from tile name
    bbox_extent = get_bounding_box_from_tile_name(tile_name)
    bbox_extent_utm = box(*bbox_extent)

    # Transform bounding box to WGS84
    bbox_extent_wgs84 = transform_utm32N_to_wgs84_geometry(bbox_extent_utm)

    # Retrieve buildings from OSM within the bounding box
    buildings_from_bbox = get_buildings_from_bbox(
        bbox_extent_wgs84.bounds, osm_data_path
    )

    if len(buildings_from_bbox) == 0:
        click.echo("No buildings found in this tile")
        return

    # Save buildings to a geopackage
    buildings_from_bbox.to_file(
        output_location / "buildings.gpkg", layer="buildings", driver="GPKG"
    )

    click.echo(
        f"Buildings extracted and saved to {output_location / 'buildings.gpkg'}"
    )


if __name__ == "__main__":
    extract_buildings()
