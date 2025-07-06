from ast import literal_eval as make_tuple
from pathlib import Path

import click
import geopandas as gpd
import numpy as np
import pandas as pd
from affine import Affine
from PIL import Image
from rasterio.features import rasterize
from tqdm import tqdm

from utils.logging import get_client_logger
from utils.transform import transform_wgs84_to_utm32N

logger = get_client_logger()


@click.command()
@click.argument("buildings_file", type=click.Path(exists=True))
@click.argument(
    "cropped_images_folder", type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
@click.argument(
    "segmentation_folder", type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
@click.argument("result_file", type=click.Path(exists=False))
def energy_extractor_cli(
    buildings_file: str,
    cropped_images_folder: str,
    segmentation_folder: str,
    result_file: str,
):
    """
    WIP
    """

    buildings = gpd.read_file(buildings_file)

    cropped_images_folder = Path(cropped_images_folder)

    cropped_images_overview = pd.read_csv(cropped_images_folder / "overview.csv")
    cropped_images_overview = cropped_images_overview.set_index("building_id")  # for faster lookup

    segmentation_folder = Path(segmentation_folder)

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

        cropped_image_size = (
            crop_image_info["image_shape_width"],
            crop_image_info["image_shape_height"],
        )
        pixel_width_meter = cropped_transform_px_to_geo[0]

        building_polygon_utm = transform_wgs84_to_utm32N(building_wgs84_polygon)

        building_mask = rasterize(
            [building_polygon_utm],
            out_shape=cropped_image_size,
            transform=transform_shapely_order_to_affine(cropped_transform_px_to_geo),
            fill=0,
            default_value=1,
            dtype=np.uint8,
        ).astype(bool)

        solar_panel_segmentation_bitmap = Image.open(segmentation_folder / f"{building_id}.bmp")

        # we reshape it in order to overlay with other bitmaps
        solar_panel_segmentation_bitmap = solar_panel_segmentation_bitmap.resize(
            cropped_image_size
        )
        solar_panel_segmentation_mask = (
            np.array(solar_panel_segmentation_bitmap, copy=True) / 255.0
        ).astype(bool)

        # keep only pixel within the building
        solar_panel_segmentation_mask_in_building = building_mask & solar_panel_segmentation_mask

        building_area = building_polygon_utm.area

        pixel_area_m2 = pixel_width_meter**2
        solar_panel_area_px = solar_panel_segmentation_mask_in_building.sum() * pixel_area_m2

        energy_stats.append(
            {
                "building_id": building_id,
                "building_area_m2": building_area,
                "solar_panel_area_m2": solar_panel_area_px,
            }
        )

    energy_stats_df = pd.DataFrame(energy_stats)
    energy_stats_df.to_csv(result_file, index=False)


def transform_shapely_order_to_affine(shapely_transform: tuple[float]) -> Affine:
    # shapely (a,b,d,e,xoff,yoff) order
    return Affine(
        shapely_transform[0],
        shapely_transform[1],
        shapely_transform[4],
        shapely_transform[2],
        shapely_transform[3],
        shapely_transform[5],
    )


if __name__ == "__main__":
    energy_extractor_cli()
