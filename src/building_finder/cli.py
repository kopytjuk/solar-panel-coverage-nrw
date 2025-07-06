import logging

import click
from shapely import box

from building_finder.extract_buildings import (
    extract_buildings_from_gps_polygon,
)
from utils.logging import get_client_logger
from utils.transform import transform_utm32N_to_wgs84

logger = get_client_logger()

logging.getLogger("pyogrio").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


@click.command()
@click.argument("utm_km_x", type=click.INT)
@click.argument("utm_km_y", type=click.INT)
@click.argument("output_path", type=click.Path(exists=False))
@click.option("--extent-km", type=click.INT, default=1)
@click.option(
    "--with-address-only",
    default=True,
    is_flag=True,
    help="Filter buildings to include only those with addresses.",
)
def building_finder_cli(
    utm_km_x: int,
    utm_km_y: int,
    extent_km: int,
    output_path: str,
    with_address_only: bool,
):
    """Extract buildings with their addresses and outline geometries from OpenStreetMap.
    The area of extraction is defined by the lower left tile corner as UTM_KM_X, UTM_KM_Y (and EXTENT_KM)"""

    utm_m_x = utm_km_x * 1000
    utm_m_y = utm_km_y * 1000
    extent_m = extent_km * 1000

    bbox_extent = (utm_m_x, utm_m_y, utm_m_x + extent_m, utm_m_y + extent_m)
    bbox_extent_utm = box(*bbox_extent)

    # Transform bounding box to WGS84
    bbox_extent_wgs84 = transform_utm32N_to_wgs84(bbox_extent_utm)

    buildings_gdf = extract_buildings_from_gps_polygon(bbox_extent_wgs84, with_address_only)
    logger.info(f"Found {len(buildings_gdf)} buildings in the tile!")

    buildings_gdf.to_file(
        str(output_path),
        layer="buildings",
        driver="GPKG",
        index=True,
    )

    logger.info("Building finder complete!")


if __name__ == "__main__":
    building_finder_cli()
