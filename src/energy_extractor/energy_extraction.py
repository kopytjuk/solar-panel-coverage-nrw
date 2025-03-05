import os

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from tqdm import tqdm

from utils.logging import get_library_logger
from utils.opengeodata_nrw import DatasetType
from utils.tile_management import TileManager
from utils.transform import transform_wgs84_to_utm32N

logger = get_library_logger(__name__)


def extract_energy_from_buildings(buildings_file: str, energy_data_location: str) -> pd.DataFrame:
    buildings = gpd.read_file(buildings_file)

    tile_manager_energy = TileManager.from_html_extraction_result(
        "data/Strahlungsenergie-0.5x0.5.csv",
        data_folder=energy_data_location,
        tile_type=DatasetType.ENERGY_YIELD_50CM,
    )

    energy_stats = []

    # iterate over each building and extract the energy yield
    for _, building in tqdm(buildings.iterrows(), total=len(buildings)):
        building_id = building["building_id"]
        building_gps_polygon = building["geometry"]

        building_polygon_utm = transform_wgs84_to_utm32N(building_gps_polygon)

        tile_name = tile_manager_energy.get_tile_name_from_point(
            building_polygon_utm.centroid.x,
            building_polygon_utm.centroid.y,
            with_extension=False,
        )

        if not tile_manager_energy.check_if_tile_exists(tile_name):
            logger.info(f"Downloading tile data for {tile_name}")
            tile_manager_energy.download_tile(tile_name)
            logger.info("Download complete!")

        file_extension = tile_manager_energy.file_extension
        energy_map_filename = f"{tile_name}.{file_extension}"

        energy_filepath = os.path.join(energy_data_location, energy_map_filename)

        with rasterio.open(energy_filepath) as energy_file:
            # transforms a UTM coordinate to pixel coordinates
            affine_transform = energy_file.transform

            no_data_value = energy_file.profile["nodata"]

            # create a mask with 1s where the building is, and 0s elsewhere
            # the mask is in pixel coordinates and has the same shape
            # as the image
            building_mask = rasterize(
                [building_polygon_utm],
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
                0  # we assume the energy output is 0kWh/m^2 for this pixel
            )

            # one pixel is 0.5m x 0.5m and holds the energy output in kWh/m^2
            pixel_area = 0.5 * 0.5

            # we sum up the energy output for each pixel
            total_energy_yield = energy_data.sum() * pixel_area

            energy_stats.append(
                {
                    "building_id": building_id,
                    "annual_energy_yield_kWh": total_energy_yield,
                }
            )

    energy_information = pd.DataFrame(energy_stats)
    energy_information.set_index("building_id", inplace=True)
    return energy_information
