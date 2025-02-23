import click

from energy_extractor.energy_extraction import extract_energy_from_buildings
from utils.logging import get_client_logger

logger = get_client_logger()


@click.command()
@click.argument("buildings_file", type=click.Path(exists=True))
@click.argument("result_file", type=click.Path(exists=False))
def energy_extractor_cli(buildings_file: str, result_file: str):
    energy_data_location = "data"
    energy_info = extract_energy_from_buildings(buildings_file, energy_data_location)
    energy_info.to_csv(result_file)

    logger.info("Processing complete!")


if __name__ == "__main__":
    energy_extractor_cli()
