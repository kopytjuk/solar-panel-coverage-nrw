from pathlib import Path

import affine
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import rasterio.windows
import shapely
from rasterio.windows import transform as window_transform
from tqdm import tqdm

from utils import TileManager, transform_wgs84_to_utm32N
from utils.logging import get_library_logger
from utils.opengeodata_nrw import DatasetType

logger = get_library_logger(__name__)


def crop_images_from_buildings(
    buildings_gpkg_path: str, image_data_location: str, output_location: str
):
    output_location = Path(output_location)
    output_location.mkdir(parents=True, exist_ok=True)

    buildings = gpd.read_file(buildings_gpkg_path)

    manager_aerial_images = TileManager.from_html_extraction_result(
        "data/aerial_images.csv",
        data_folder=image_data_location,
        tile_type=DatasetType.AERIAL_IMAGE,
    )

    overview_data = list()

    for _, building in tqdm(buildings.iterrows(), total=len(buildings)):
        building_id = building["building_id"]
        building_gps_polygon = building["geometry"]

        building_polygon = transform_wgs84_to_utm32N(building_gps_polygon)
        building_geometry_centroid = building_polygon.centroid

        tile_name = manager_aerial_images.get_tile_name_from_point(
            building_geometry_centroid.x,
            building_geometry_centroid.y,
            with_extension=False,
        )

        if not manager_aerial_images.check_if_tile_exists(tile_name):
            logger.info(f"Downloading tile data for {tile_name}")
            manager_aerial_images.download_tile(tile_name)
            logger.info("Download complete!")

        file_extension = manager_aerial_images.file_extension
        tile_filename = f"{tile_name}.{file_extension}"

        tile_file_path = f"{image_data_location}/{tile_filename}"

        with rasterio.open(tile_file_path) as image_data:
            affine_transform_px_to_geo = image_data.transform

            # res_x, res_y = image_data.res

            bounding_box = create_squared_box_around(building_polygon, margin_around_building=5.0)

            crop_window = rasterio.windows.from_bounds(
                *bounding_box.bounds,
                transform=affine_transform_px_to_geo,
            )

            image_matrix = image_data.read(window=crop_window)

            image_matrix = image_matrix[:3, ...]
            image_matrix = np.moveaxis(image_matrix, 0, -1)

            # crop window is partly outside the image
            if image_matrix.shape[0] != image_matrix.shape[1]:
                # TODO: logic to combine data from neighboring tiles
                continue

            building_image_filename = f"{building_id}.png"

            plt.imsave(
                output_location / building_image_filename,
                arr=image_matrix,
                dpi=200,
            )

            # # uncomment for DEBUG
            # img = Image.fromarray(image_matrix)
            # d = ImageDraw.Draw(img)
            # d.polygon(
            #     xy=building_polygon_px_image.exterior.coords[:], outline="red"
            # )
            # img.show()

        # we store the transformation matrix for later use
        transform_cropped_px_to_geo = window_transform(
            crop_window, affine_transform_px_to_geo
        ).to_shapely()
        transform_cropped_px_to_geo_arr = np.array(transform_cropped_px_to_geo)

        overview_data.append(
            {
                "building_id": building_id,
                "image_filename": building_image_filename,
                "image_shape_width": image_matrix.shape[1],
                "image_shape_height": image_matrix.shape[0],
                "transform_px_to_geo": tuple(transform_cropped_px_to_geo_arr.tolist()),
            }
        )

    overview_df = pd.DataFrame(overview_data)
    overview_df.to_csv(output_location / "overview.csv", index=False)


def create_transform_for_cropped_image(
    affine_transform_px_to_geo: affine.Affine, crop_window: rasterio.windows.Window
) -> tuple[float]:
    """_summary_

    Args:
        affine_transform_px_to_geo (_type_): _description_
        crop_window (_type_): _description_

    Returns:
        tuple[float]: Shapely affine transformation format
    """

    affine_transform_px_to_geo = affine_transform_px_to_geo.to_shapely()
    transform_cropped_px_to_geo_arr = np.asarray(affine_transform_px_to_geo)

    x_offset_m = round(crop_window.col_off) * transform_cropped_px_to_geo_arr[0]
    y_offset_m = round(crop_window.row_off) * transform_cropped_px_to_geo_arr[3]
    transform_cropped_px_to_geo_arr[4] += x_offset_m
    transform_cropped_px_to_geo_arr[5] += y_offset_m
    return tuple(transform_cropped_px_to_geo_arr.tolist())


def create_squared_box_around(
    building_polygon: shapely.Polygon, margin_around_building: float = 5.0
) -> shapely.Polygon:
    """Create a squared bounding box around a building outline polygon.

    Args:
        building_polygon (shapely.Polygon): building outline
        margin_around_building (float, optional): Margin in meters. Defaults to 5.0.

    Returns:
        shapely.Polygon: squared bounding box
    """
    building_polygon_with_margin = building_polygon.buffer(margin_around_building)

    building_buffered_box = building_polygon_with_margin.envelope

    # Calculate the maximum dimension (width or height) of the rectangle
    width = building_buffered_box.bounds[2] - building_buffered_box.bounds[0]
    height = building_buffered_box.bounds[3] - building_buffered_box.bounds[1]
    max_dimension = max(width, height)

    # Determine the centroid of the original rectangle
    centroid = building_buffered_box.centroid

    half_side = max_dimension / 2
    buffered_box_square = shapely.Polygon(
        [
            (centroid.x - half_side, centroid.y - half_side),
            (centroid.x + half_side, centroid.y - half_side),
            (centroid.x + half_side, centroid.y + half_side),
            (centroid.x - half_side, centroid.y + half_side),
        ]
    )

    return buffered_box_square
