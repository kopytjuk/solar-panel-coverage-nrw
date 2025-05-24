import logging

import click

from building_finder.extract_buildings import extract_buildings, write_gdf_to
from utils.logging import get_client_logger

logger = get_client_logger()

logging.getLogger("pyogrio").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


@click.command()
@click.argument("tile_name", type=click.STRING)
@click.argument("output_location", type=click.Path(exists=False))
@click.option(
    "--with-address-only",
    default=True,
    is_flag=True,
    help="Filter buildings to include only those with addresses.",
)
def building_finder_cli(
    tile_name: str,
    output_location: str,
    with_address_only: bool,
):
    """Extract buildings with their addresses and outline geometries from OpenStreetMap.
    The area of extraction is defined by the TILE_NAME which follows the nomenclature of OpenGeodata.NRW."""

    click.echo(f"Starting building extraction for tile: {tile_name}")
    click.echo(f"Output will be saved to: {output_location}")

    buildings_gdf = extract_buildings(
        tile_name,
        with_address=with_address_only,
    )

    write_gdf_to(
        output_location,
        buildings_gdf,
        f"{tile_name}_buildings.gpkg",
    )

    logger.info("Building finder complete!")


if __name__ == "__main__":
    building_finder_cli()
