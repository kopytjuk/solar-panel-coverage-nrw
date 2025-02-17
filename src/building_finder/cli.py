from pathlib import Path

import click

from building_finder.extract_buildings import extract_buildings


@click.command()
@click.argument("tile_name", type=click.STRING)
@click.argument("output_location", type=click.Path(exists=True))
def building_finder_cli(
    tile_name: str,
    output_location: str,
):
    """Command-line interface for extracting building polygons from OSM."""
    click.echo(f"Starting building extraction for tile: {tile_name}")
    click.echo(f"Output will be saved to: {output_location}")

    output_location = Path(output_location)
    extract_buildings(
        tile_name,
        output_location,
    )


if __name__ == "__main__":
    building_finder_cli()
