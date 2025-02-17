from pathlib import Path

import click

from building_finder.extract_buildings import extract_buildings


@click.command()
@click.argument("tile_name", type=click.STRING)
@click.argument("output_location", type=click.Path(exists=True))
@click.option(
    "--image-tiles-overview-path",
    type=click.Path(exists=True),
    default="data/tile-info/dop_nw.csv",
)
@click.option(
    "--energy-tiles-overview-path",
    type=click.Path(exists=True),
    default="data/Strahlungsenergie-0.5x0.5.csv",
)
@click.option(
    "--image-data-location",
    type=click.STRING,
    default="data",
)
@click.option(
    "--energy-data-location",
    type=click.STRING,
    default="data",
)
@click.option("--keep-data", is_flag=True)
def building_finder_cli(
    tile_name,
    output_location,
    image_tiles_overview_path,
    energy_tiles_overview_path,
    image_data_location,
    energy_data_location,
    keep_data,
):
    """Command-line interface for extracting building polygons from OSM."""
    click.echo(f"Starting building extraction for tile: {tile_name}")
    click.echo(f"Output will be saved to: {output_location}")

    output_location = Path(output_location)
    extract_buildings(
        tile_name,
        output_location,
        image_tiles_overview_path,
        energy_tiles_overview_path,
        image_data_location,
        energy_data_location,
        keep_data,
    )


if __name__ == "__main__":
    building_finder_cli()
