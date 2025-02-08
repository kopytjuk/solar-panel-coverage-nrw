import os
import shutil
from pathlib import Path

import click
import numpy as np
import pandas as pd
import rasterio
import shapely
from matplotlib import pyplot as plt
from rasterio.features import rasterize
from tqdm import tqdm

from src.tile_management import TileManager, get_bounding_box_from_tile_name
from src.transform import UTM_EPSG, transform_utm32N_to_wgs84_geometry
from src.utils import get_buildings_from_bbox


@click.command()
@click.argument("tile_name", type=click.STRING)
@click.argument("output_location", type=click.Path(exists=True))
@click.option(
    "--image-tiles-overview-path",
    type=click.Path(exists=True),
    default="/Users/kopytjuk/Code/roof-analysis/data/tile-info/dop_nw.csv",
)
@click.option(
    "--energy-tiles-overview-path",
    type=click.Path(exists=True),
    default="/Users/kopytjuk/Code/roof-analysis/data/Strahlungsenergie-0.5x0.5.csv",
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
def extract_buildings(
    tile_name: str,
    output_location: str,
    image_tiles_overview_path: str,
    energy_tiles_overview_path: str,
    image_data_location: str,
    energy_data_location: str,
    keep_data: bool,
):
    click.echo(f"Processing tile: {tile_name}")
    click.echo(f"Saving output to: {output_location}")

    output_location = Path(output_location)

    if not keep_data:
        shutil.rmtree(str(output_location))

    image_location = output_location / "images"
    image_location.mkdir(parents=True, exist_ok=True)

    # bounding box can be extracted from the tile name
    bbox_extent = get_bounding_box_from_tile_name(tile_name)
    bbox_extent_utm = shapely.box(*bbox_extent)

    # OSM lookups work with WGS84 coordinates only
    bbox_extent_wgs84 = transform_utm32N_to_wgs84_geometry(bbox_extent_utm)

    buildings_from_bbox = get_buildings_from_bbox(bbox_extent_wgs84.bounds)

    DEBUG = True
    if DEBUG:
        N = 20
        buildings_from_bbox = buildings_from_bbox.sample(N, random_state=42)

    if len(buildings_from_bbox) == 0:
        click.echo("No buildings found in this tile")
        return

    buildings_from_bbox_utm = buildings_from_bbox.to_crs(UTM_EPSG)

    # determine the kWh per year for each building
    energy_information = extract_energy_potential(
        energy_tiles_overview_path,
        energy_data_location,
        bbox_extent_utm,
        buildings_from_bbox_utm,
    )

    buildings_from_bbox_utm = pd.concat(
        [buildings_from_bbox_utm, energy_information], axis=1
    )

    buildings_from_bbox_utm.to_file(
        output_location / "buildings.gpkg", layer="buildings", driver="GPKG"
    )
    buildings_from_bbox_utm[
        ["energy_avg", "energy_min", "energy_max", "energy_sum"]
    ].to_csv(output_location / "buildings.csv")

    tile_manager = TileManager.from_tile_file(image_tiles_overview_path)

    image_tile_name = tile_manager.get_tile_name_from_point(
        bbox_extent_utm.centroid.x, bbox_extent_utm.centroid.y
    )
    image_filename = image_tile_name + ".jp2"
    image_filepath = os.path.join(image_data_location, image_filename)

    with rasterio.open(image_filepath) as image_file:
        # transforms a UTM coordinate to pixel coordinates
        affine_transform = image_file.transform

        BUFFER_BUILDING: float = 5.0

        for building_id, building_data in tqdm(
            buildings_from_bbox_utm.iterrows(),
            total=len(buildings_from_bbox_utm),
        ):
            building_polygon = building_data["geometry"]
            building_envelope = building_polygon.envelope

            example_building_buffered_box = building_envelope.buffer(
                BUFFER_BUILDING, cap_style="flat", join_style="mitre"
            )

            if not bbox_extent_utm.contains(example_building_buffered_box):
                click.echo(
                    f"Building {building_id} is outside of the image bounds"
                )
                continue

            crop_window = rasterio.windows.from_bounds(
                *example_building_buffered_box.bounds,
                transform=affine_transform,
            )

            image_data = image_file.read(window=crop_window)

            image_data = image_data[:3, ...]
            # change (3, H, W) to (H, W, 3)
            image_data = np.moveaxis(image_data, 0, -1)

            plt.imsave(
                image_location / f"{building_id}_{int(BUFFER_BUILDING):d}.png",
                arr=image_data,
                dpi=200,
            )


def extract_energy_potential(
    energy_tiles_overview_path,
    energy_data_location,
    bbox_extent_utm,
    buildings_from_bbox_utm,
):
    tile_manager_energy = TileManager.from_html_extraction_result(
        energy_tiles_overview_path
    )
    energy_map_filename = tile_manager_energy.get_tile_name_from_point(
        bbox_extent_utm.centroid.x, bbox_extent_utm.centroid.y
    )
    energy_filepath = os.path.join(energy_data_location, energy_map_filename)

    # TODO: rewrite so that the data is only read once

    with rasterio.open(energy_filepath) as energy_file:
        # transforms a UTM coordinate to pixel coordinates
        affine_transform = energy_file.transform

        no_data_value = energy_file.profile["nodata"]

        energy_stats = []
        for building_id, building_data in tqdm(
            buildings_from_bbox_utm.iterrows(),
            total=len(buildings_from_bbox_utm),
            desc="Extracting energy potential",
        ):
            # create a mask with 1s where the building is, and 0s elsewhere
            # the mask is in pixel coordinates and has the same shape as the image
            building_mask = rasterize(
                [building_data.geometry],
                transform=affine_transform,
                out_shape=(energy_file.height, energy_file.width),
                fill=0,
                all_touched=True,
            ).astype(bool)

            # read data only from mask
            energy_data = energy_file.read(1)[building_mask]

            # if the building is not in the image, the energy_data is empty
            # and we set it to 0
            if energy_data.size == 0:
                energy_data = np.zeros((2, 2))

            energy_data[energy_data == no_data_value] = (
                0  # we assume the energy output is 0kWh for this pixel
            )

            energy_stats.append(
                {
                    "building_id": building_id,
                    "energy_max": energy_data.max(),
                    "energy_min": energy_data.min(),
                    "energy_avg": energy_data.mean(),
                    "energy_median": np.median(energy_data),
                    "energy_sum": energy_data.sum(),
                }
            )
    energy_information = pd.DataFrame(energy_stats)
    energy_information.set_index("building_id", inplace=True)
    return energy_information


if __name__ == "__main__":
    extract_buildings()
