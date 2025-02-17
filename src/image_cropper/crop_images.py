from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely

from utils import TileManager, transform_wgs84_to_utm32N_geometry


def crop_images_from_buildings(
    buildings_gpkg_path: str, image_data_location: str, output_location: str
):
    output_location = Path(output_location)
    output_location.mkdir(parents=True, exist_ok=True)

    buildings = gpd.read_file(buildings_gpkg_path)
    print(buildings.head())

    manager_aerial_images = TileManager.from_tile_file(
        "data/tile-info/dop_nw.csv"
    )

    overview_data = list()

    buildings = buildings.iloc[100:110]

    for _, building in buildings.iterrows():
        building_id = building["building_id"]
        building_gps_polygon = building["geometry"]

        building_polygon = transform_wgs84_to_utm32N_geometry(
            building_gps_polygon
        )
        building_geometry_centroid = building_polygon.centroid

        tile_name = manager_aerial_images.get_tile_name_from_point(
            building_geometry_centroid.x, building_geometry_centroid.y
        )
        tile_file_path = f"{image_data_location}/{tile_name}.jp2"

        with rasterio.open(tile_file_path) as image_data:
            affine_transform_px_to_geo = image_data.transform

            building_buffered_box = building_polygon.envelope.buffer(5.0)

            crop_window = rasterio.windows.from_bounds(
                *building_buffered_box.bounds,
                transform=affine_transform_px_to_geo,
            )

            image_matrix = image_data.read(window=crop_window)

            image_matrix = image_matrix[:3, ...]
            image_matrix = np.moveaxis(image_matrix, 0, -1)

            building_image_filename = f"{building_id}.png"

            plt.imsave(
                output_location / building_image_filename,
                arr=image_matrix,
                dpi=200,
            )

            affine_transform_geo_to_px = ~affine_transform_px_to_geo

            affine_transform_for_shapely = (
                affine_transform_geo_to_px.to_shapely()
            )

            # polygon in pixel coordinates of the full tile
            building_polygon_px = shapely.affinity.affine_transform(
                building_polygon, affine_transform_for_shapely
            )

            # polygon in the pixel coordinates of the cropped image
            building_polygon_px_image = shapely.affinity.translate(
                building_polygon_px, -crop_window.col_off, -crop_window.row_off
            )

            # # uncomment for DEBUG
            # img = Image.fromarray(image_matrix)
            # d = ImageDraw.Draw(img)
            # d.polygon(
            #     xy=building_polygon_px_image.exterior.coords[:], outline="red"
            # )
            # img.show()

        overview_data.append(
            {
                "building_id": building_id,
                "image_filename": building_image_filename,
                "geometry_wkt": building_polygon.wkt,
                "geometry_px_wkt": building_polygon_px_image.wkt,
            }
        )

    overview_df = pd.DataFrame(overview_data)
    overview_df.to_csv(output_location / "overview.csv", index=False)
