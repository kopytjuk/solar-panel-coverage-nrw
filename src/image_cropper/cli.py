from pathlib import Path

import click
import geopandas as gpd

from image_cropper.crop_images import crop_images_from_buildings
from utils.logging import get_client_logger
from utils.tile_management import TileManager

logger = get_client_logger()


@click.command()
@click.argument("buildings_file", type=click.Path(exists=True))
@click.argument("output_folder", type=click.Path())
@click.option(
    "--tile-folder",
    type=click.Path(exists=True),
    default="/Users/kopytjuk/Downloads/Heilbronn DOP20",
    help="Folder containing aerial image tiles.",
)
@click.option(
    "--output-image-format",
    type=click.Choice(["png", "jpg", "tif", "bmp"], case_sensitive=False),
    default="png",
    help="Output format for cropped images.",
)
def image_cropper_cli(
    buildings_file: str, tile_folder: str, output_folder: str, output_image_format: str
):
    """Extract a square-shaped image for each of the buildings in the BUILDINGS_FILE (gpkg).

    Args:
        buildings_file (str): GeoPackage file with buildings
        output_folder (str): output folder where images shall be extracted
    """
    click.echo(f"Processing buildings from: {buildings_file}")
    click.echo(f"Saving cropped images to: {output_folder}")

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    buildings_gdf = gpd.read_file(buildings_file)

    tile_manager = TileManager.from_folder(tile_folder, extension="tif")

    crop_images_from_buildings(
        buildings_gdf, tile_manager, output_folder, output_format=output_image_format
    )
    logger.info("Processing complete!")


if __name__ == "__main__":
    image_cropper_cli()
