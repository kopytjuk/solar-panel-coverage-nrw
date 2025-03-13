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
@click.option("-st", "--segmentation-threshold", default=0.8, type=click.FLOAT)
@click.option("-e", "--efficiency_panel", default=0.21, type=click.FLOAT)
def energy_extractor_cli(
    buildings_file: str,
    cropped_images_folder: str,
    segmentation_result_folder: str,
    result_file: str,
    segmentation_threshold: float,
    efficiency_panel: float,
):
    """
    Extract soloar energy yields for each building in BUILDINGS_FILE. The tool relies
    on solar radiant bitmaps and solar panel segmentation results.

    Args:
        buildings_file (str): buildings with geometries
        cropped_images_folder (str): folder with cropped images (input to segm. model)
        segmentation_result_folder (str): segmentation model output folder
        result_file (str): output location of this tool
        segmentation_threshold (float): threshold for a segmentation result of a pixel,
            above which a solar panel installation is assumed
        efficiency_panel (float): assumed efficiency of the solar panel
    """

    energy_data_location = "data"
    energy_info = extract_energy_from_buildings(
        buildings_file,
        cropped_images_folder,
        segmentation_result_folder,
        energy_data_location,
        segmentation_threshold=segmentation_threshold,
        efficiency=efficiency_panel,
    )
    energy_info.to_csv(result_file)

    logger.info("Processing complete!")


if __name__ == "__main__":
    energy_extractor_cli()
