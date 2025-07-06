import shapely
from shapely.geometry import box

from utils import (
    get_bounding_box_from_tile_name,
    get_buildings_from_bbox,
    transform_utm32N_to_wgs84,
    transform_wgs84_to_utm32N,
)
from utils.logging import get_library_logger

logger = get_library_logger(__name__)


def extract_buildings(tile_name: str, with_address: bool = False):
    # Get bounding box from tile name
    bbox_extent = get_bounding_box_from_tile_name(tile_name)
    bbox_extent_utm = box(*bbox_extent)

    # Transform bounding box to WGS84
    bbox_extent_wgs84 = transform_utm32N_to_wgs84(bbox_extent_utm)

    return extract_buildings_from_gps_polygon(bbox_extent_wgs84, with_address)


def extract_buildings_from_gps_polygon(gps_polygon: shapely.Polygon, with_address: bool = False):
    # Retrieve buildings from OSM within the bounding box
    buildings_from_bbox = get_buildings_from_bbox(gps_polygon.bounds, with_address=with_address)

    logger.debug(f"Found {len(buildings_from_bbox)} buildings in the polygon!")

    # filter for buildings in the polygon
    buildings_from_bbox = buildings_from_bbox[buildings_from_bbox.within(gps_polygon)]

    # Compute the area for all geometries and store it in a column (m² in UTM32N)
    area_arr = [transform_wgs84_to_utm32N(geom).area for geom in buildings_from_bbox.geometry]
    buildings_from_bbox["area"] = area_arr

    if len(buildings_from_bbox) == 0:
        return

    return buildings_from_bbox
