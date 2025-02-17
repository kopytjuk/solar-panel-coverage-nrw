import shutil
from pathlib import Path

from shapely.geometry import box

from utils import (
    get_bounding_box_from_tile_name,
    get_buildings_from_bbox,
    transform_utm32N_to_wgs84_geometry,
)


def extract_buildings(tile_name: str, output_location: str):
    output_location = Path(output_location)

    # Clear output location if it exists
    if output_location.exists():
        shutil.rmtree(str(output_location))
    output_location.mkdir(parents=True, exist_ok=True)

    # Get bounding box from tile name
    bbox_extent = get_bounding_box_from_tile_name(tile_name)
    bbox_extent_utm = box(*bbox_extent)

    # Transform bounding box to WGS84
    bbox_extent_wgs84 = transform_utm32N_to_wgs84_geometry(bbox_extent_utm)

    # Retrieve buildings from OSM within the bounding box
    buildings_from_bbox = get_buildings_from_bbox(bbox_extent_wgs84.bounds)

    if len(buildings_from_bbox) == 0:
        return

    # Save buildings to a geopackage
    buildings_from_bbox.to_file(
        output_location / f"{tile_name}_buildings.gpkg",
        layer="buildings",
        driver="GPKG",
        index=True,
    )
