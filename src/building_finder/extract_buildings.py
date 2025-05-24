import io
import os
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from shapely.geometry import box

from utils import (
    get_bounding_box_from_tile_name,
    get_buildings_from_bbox,
    transform_utm32N_to_wgs84,
    transform_wgs84_to_utm32N,
)
from utils.azure import parse_blob_storage_uri
from utils.logging import get_library_logger

logger = get_library_logger(__name__)


def extract_buildings(tile_name: str, with_address: bool = False):
    # Get bounding box from tile name
    bbox_extent = get_bounding_box_from_tile_name(tile_name)
    bbox_extent_utm = box(*bbox_extent)

    # Transform bounding box to WGS84
    bbox_extent_wgs84 = transform_utm32N_to_wgs84(bbox_extent_utm)

    # Retrieve buildings from OSM within the bounding box
    buildings_from_bbox = get_buildings_from_bbox(
        bbox_extent_wgs84.bounds, with_address=with_address
    )

    logger.info(f"Found {len(buildings_from_bbox)} buildings in the bounding box!")

    # Compute the area for all geometries and store it in a column (m² in UTM32N)
    area_arr = [transform_wgs84_to_utm32N(geom).area for geom in buildings_from_bbox.geometry]
    buildings_from_bbox["area"] = area_arr

    if len(buildings_from_bbox) == 0:
        return

    return buildings_from_bbox


def write_gdf_to(output_location, buildings_from_bbox, file_name):
    is_remote = "://" in output_location
    logger.info(f"The output remote storage: {is_remote}")
    if is_remote:
        storage_acc, container_name, path = parse_blob_storage_uri(output_location)
        # assuming user did a `az login`
        default_credential = DefaultAzureCredential()

        blob_storage_url = f"https://{storage_acc}.blob.core.windows.net"
        service_client = BlobServiceClient(blob_storage_url, credential=default_credential)

        # Upload the file
        blob_client = service_client.get_blob_client(
            container=container_name, blob=os.path.join(path, file_name)
        )
        bytestream = io.BytesIO()
        buildings_from_bbox.to_file(bytestream, layer="buildings", driver="GPKG", index=True)
        bytestream.seek(0)

        blob_client.upload_blob(bytestream, overwrite=True)
        logger.info("Writing to Azure Blob Storage completed successfully.")
    else:
        output_location = Path(output_location)
        output_location.mkdir(parents=True, exist_ok=True)

        output_path = output_location / file_name
        buildings_from_bbox.to_file(
            str(output_path),
            layer="buildings",
            driver="GPKG",
            index=True,
        )
