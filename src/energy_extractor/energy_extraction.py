import os
from ast import literal_eval as make_tuple
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from PIL import Image
from rasterio.features import rasterize
from rasterio.windows import transform as window_transform
from tqdm import tqdm

from utils.logging import get_library_logger
from utils.opengeodata_nrw import DatasetType
from utils.tile_management import TileManager
from utils.transform import transform_wgs84_to_utm32N

logger = get_library_logger(__name__)


@dataclass
class CroppedImageExtent:
    width: int
    height: int
    trafo_px_to_geo: tuple[float]

    def to_utm_bounds(self) -> shapely.Polygon:
        image_bounds = shapely.box(0, 0, self.width, self.height)
        return shapely.affinity.affine_transform(image_bounds, self.trafo_px_to_geo)


def extract_energy_from_buildings(
    buildings_file: str,
    cropped_images_folder: str,
    segmentation_output_folder: str,
    energy_data_location: str,
    *,
    segmentation_threshold: float,
) -> pd.DataFrame:
    buildings = gpd.read_file(buildings_file)

    cropped_images_folder = Path(cropped_images_folder)

    cropped_images_overview = pd.read_csv(cropped_images_folder / "overview.csv")
    cropped_images_overview = cropped_images_overview.set_index("building_id")  # for faster lookup

    segmentation_output_folder = Path(segmentation_output_folder)

    tile_manager_energy = TileManager.from_html_extraction_result(
        "data/Strahlungsenergie-0.5x0.5.csv",
        data_folder=energy_data_location,
        tile_type=DatasetType.ENERGY_YIELD_50CM,
    )

    # for collecting results
    energy_stats = []

    # iterate over each building and extract the energy yield
    for _, building in tqdm(buildings.iterrows(), total=len(buildings)):
        building_id = building["building_id"]
        building_wgs84_polygon = building["geometry"]

        # skipped, in case image cropping did not work
        if building_id not in cropped_images_overview.index:
            continue

        crop_image_info = cropped_images_overview.loc[building_id]
        cropped_transform_px_to_geo = make_tuple(crop_image_info["transform_px_to_geo"])
        cie = CroppedImageExtent(
            crop_image_info["image_shape_width"],
            crop_image_info["image_shape_height"],
            cropped_transform_px_to_geo,
        )
        cropped_image_extent_utm = cie.to_utm_bounds()

        building_polygon_utm = transform_wgs84_to_utm32N(building_wgs84_polygon)

        tile_name = tile_manager_energy.get_tile_name_from_point(
            building_polygon_utm.centroid.x,
            building_polygon_utm.centroid.y,
            with_extension=False,
        )

        if not tile_manager_energy.check_if_tile_exists(tile_name):
            logger.info(f"Downloading tile data for {tile_name}")
            tile_manager_energy.download_tile(tile_name)
            logger.info("Download complete!")

        # assemble the energy tile file name
        file_extension = tile_manager_energy.file_extension
        energy_map_filename = f"{tile_name}.{file_extension}"
        energy_filepath = os.path.join(energy_data_location, energy_map_filename)

        with rasterio.open(energy_filepath) as energy_file:
            # transforms a UTM coordinate to pixel coordinates
            transform_px_to_geo_energy = energy_file.transform

            no_data_value = energy_file.profile["nodata"]

            crop_window = rasterio.windows.from_bounds(
                *cropped_image_extent_utm.bounds,
                transform=transform_px_to_geo_energy,
            )

            energy_cropped_area = energy_file.read(window=crop_window)
            energy_cropped_area = energy_cropped_area[0, ...]

            energy_cropped_area[energy_cropped_area == no_data_value] = (
                0  # we assume the energy output is 0kWh/m^2 for this pixel
            )

            energy_cropped_area_trafo = window_transform(crop_window, transform_px_to_geo_energy)

            building_mask_for_energy = rasterize(
                [building_polygon_utm],
                out_shape=energy_cropped_area.shape,
                transform=energy_cropped_area_trafo,
                fill=0,
                default_value=1,
                dtype=np.uint8,
            )

            energy_building = np.where(
                building_mask_for_energy.astype(bool),
                energy_cropped_area,
                np.zeros_like(energy_cropped_area),
            )

            solar_panel_segmentation_image = Image.open(
                segmentation_output_folder / f"{building_id}.bmp"
            )
            # we reshape it in order to overlay with other bitmaps
            solar_panel_segmentation_image = solar_panel_segmentation_image.resize(
                energy_cropped_area.shape
            )
            solar_panel_segmentation_arr = np.array(solar_panel_segmentation_image, copy=True)
            solar_panel_segmentation_arr = solar_panel_segmentation_arr / 255

            solar_panel_existence_mask = solar_panel_segmentation_arr > segmentation_threshold

            # keep only pixel within the building
            solar_panel_existence_mask = np.where(
                building_mask_for_energy.astype(bool),
                solar_panel_existence_mask,
                np.zeros_like(solar_panel_existence_mask),
            )

            energy_yield_solar = np.where(
                solar_panel_existence_mask,
                energy_building,
                np.zeros_like(energy_building),
            )

            area_pixel = 0.5 * 0.5  # in m2, depends on the energy file
            actual_energy_yield = energy_yield_solar.sum() * area_pixel
            potential_energy_yield = energy_building.sum() * area_pixel

            energy_stats.append(
                {
                    "building_id": building_id,
                    "actual_energy_yield_kWh": actual_energy_yield,
                    "potential_energy_yield_kWh": potential_energy_yield,
                }
            )

    energy_information = pd.DataFrame(energy_stats)
    energy_information.set_index("building_id", inplace=True)
    return energy_information
