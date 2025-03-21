from pathlib import Path

import click

from image_cropper.crop_images import crop_images_from_buildings
from utils.logging import get_client_logger

logger = get_client_logger()


@click.command()
@click.argument("buildings_file", type=click.Path(exists=True))
@click.argument("output_folder", type=click.Path())
def image_cropper_cli(buildings_file: str, output_folder: str):
    """Extract a square-shaped image for each of the buildings in the BUILDINGS_FILE (gpkg).

    Args:
        buildings_file (str): GeoPackage file with buildings
        output_folder (str): output folder where images shall be extracted
    """
    click.echo(f"Processing buildings from: {buildings_file}")
    click.echo(f"Saving cropped images to: {output_folder}")

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    image_data_location = "data"
    crop_images_from_buildings(buildings_file, image_data_location, output_folder)
    logger.info("Processing complete!")


if __name__ == "__main__":
    image_cropper_cli()
