"""Creates a segmentation dataset from an aerial image and a shapefile of polygon labels."""

from pathlib import Path

import click
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import transform as window_transform
from shapely import box

from building_finder.extract_buildings import extract_buildings_from_gps_polygon
from utils.logging import get_client_logger
from utils.transform import UTM_EPSG, transform_utm32N_to_wgs84, transform_wgs84_to_utm32N

logger = get_client_logger()


@click.command()
@click.argument("aerial_image", type=click.Path(exists=True))
@click.argument("labels_shapefile", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path(exists=False))
@click.option("--bbox-size", "-bs", help="Bounding box size in meters", type=click.INT, default=25)
def create_dataset(aerial_image, labels_shapefile: str, output_dir: str, bbox_size: int):
    """Process aerial image and polygon-labels shapefile to create a dataset.

    AERIAL_IMAGE: Path to the aerial image file (GeoTIFF)
    LABELS_SHAPEFILE: Path to the shapefile containing polygon labels
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_folder = output_path / "images"
    image_folder.mkdir(parents=True, exist_ok=True)

    masks_folder = output_path / "masks"
    masks_folder.mkdir(parents=True, exist_ok=True)

    click.echo("Starting.")

    labels_gdf = gpd.read_file(labels_shapefile)
    labels_utm_gdf = labels_gdf.to_crs(UTM_EPSG)

    image_edge_half = int(bbox_size) // 2

    logger.info(f"{len(labels_utm_gdf)} label polygons loaded!")

    with rasterio.open(aerial_image) as image_data:
        affine_transform_px_to_geo = image_data.transform

        image_extent_bbox = box(*image_data.bounds)
        image_extent_bbox_wgs84 = transform_utm32N_to_wgs84(image_extent_bbox)

        buildings_from_bbox = extract_buildings_from_gps_polygon(image_extent_bbox_wgs84)

        for i, (building_id, building) in enumerate(buildings_from_bbox.iterrows(), start=1):
            building_gps_polygon = building.geometry

            building_utm_polygon = transform_wgs84_to_utm32N(building_gps_polygon)
            building_centroid = building_utm_polygon.centroid

            bounding_box = box(
                building_centroid.x - image_edge_half,
                building_centroid.y - image_edge_half,
                building_centroid.x + image_edge_half,
                building_centroid.y + image_edge_half,
            )
            crop_window = rasterio.windows.from_bounds(
                *bounding_box.bounds,
                transform=affine_transform_px_to_geo,
            )

            image_matrix = image_data.read(window=crop_window)

            # CHW to HCW
            image_matrix = image_matrix.transpose(1, 2, 0)[..., :3]

            from PIL import Image

            im = Image.fromarray(image_matrix)
            im.save(image_folder / f"{building_id}.bmp")

            labels_within_bbox_gdf = labels_utm_gdf[labels_utm_gdf.intersects(bounding_box)]

            if labels_within_bbox_gdf.empty:
                label_mask = np.zeros(shape=image_matrix.shape[:2], dtype=bool)
                logger.debug(
                    f"No labels found for building {building_id} within the bounding box."
                )
            else:
                transform_cropped_px_to_geo = window_transform(
                    crop_window, affine_transform_px_to_geo
                )

                label_mask = rasterize(
                    [b.geometry for _, b in labels_within_bbox_gdf.iterrows()],
                    out_shape=image_matrix.shape[:2],
                    transform=transform_cropped_px_to_geo,
                    fill=0,
                    default_value=1,
                    dtype=np.uint8,
                ).astype(bool)

            im = Image.fromarray(label_mask)
            im.save(masks_folder / f"{building_id}.bmp")

            logger.info(f"Processed {i}/{len(buildings_from_bbox)}: {building_id}")


if __name__ == "__main__":
    create_dataset()
