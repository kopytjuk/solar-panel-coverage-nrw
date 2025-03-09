import click

from energy_extractor.energy_extraction import extract_energy_from_buildings
from utils.logging import get_client_logger

logger = get_client_logger()


@click.command()
@click.argument("buildings_file", type=click.Path(exists=True))
@click.argument(
    "cropped_images_folder", type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
@click.argument(
    "segmentation_result_folder", type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
@click.argument("result_file", type=click.Path(exists=False))
def energy_extractor_cli(
    buildings_file: str,
    cropped_images_folder: str,
    segmentation_result_folder: str,
    result_file: str,
):
    energy_data_location = "data"
    energy_info = extract_energy_from_buildings(
        buildings_file, cropped_images_folder, segmentation_result_folder, energy_data_location
    )
    energy_info.to_csv(result_file)

    logger.info("Processing complete!")


if __name__ == "__main__":
    energy_extractor_cli()
