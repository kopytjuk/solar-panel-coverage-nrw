import shutil
from pathlib import Path

from shapely.geometry import box

from utils import (
    get_bounding_box_from_tile_name,
    get_buildings_from_bbox,
    transform_utm32N_to_wgs84,
    transform_wgs84_to_utm32N,
)
from utils.logging import get_library_logger

logger = get_library_logger(__name__)


def extract_buildings(tile_name: str, output_location: str, with_address: bool = False):
    output_location = Path(output_location)

    # Clear output location if it exists
    if output_location.exists():
        shutil.rmtree(str(output_location))
    output_location.mkdir(parents=True, exist_ok=True)

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

    # Compute the area for all geometries and store it in a column
    # the area computation is done in UTM32N (m²)
    area_arr = [transform_wgs84_to_utm32N(geom).area for geom in buildings_from_bbox.geometry]
    buildings_from_bbox["area"] = area_arr

    if len(buildings_from_bbox) == 0:
        return

    # Save buildings to a geopackage
    buildings_from_bbox.to_file(
        output_location / "buildings_general_info.gpkg",
        layer="buildings",
        driver="GPKG",
        index=True,
    )
