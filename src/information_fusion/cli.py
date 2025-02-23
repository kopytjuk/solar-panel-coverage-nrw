from pathlib import Path

import click

from information_fusion.information_fusion import combine_information
from utils.logging import get_client_logger

logger = get_client_logger()


@click.command()
@click.argument("tile_results_folder", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path())
def merge_results_cli(tile_results_folder: str, output_file: str):
    logger.info("Merging results from %s", tile_results_folder)
    final_gdf = combine_information(tile_results_folder)

    logger.info("Saving the merged results to %s", output_file)
    final_gdf.to_file(output_file, driver="GPKG")

    logger.info("Done!")


if __name__ == "__main__":
    merge_results_cli()
