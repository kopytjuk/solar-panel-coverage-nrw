import glob
import os
import uuid

import geopandas as gpd
import osmnx as ox


def get_bounding_box_from_tile_name(
    name: str,
) -> tuple[float, float, float, float]:
    """Extract the bounding box from a tile name.

    Args:
        name (str): tile name, e.g. "3dm_32_511_5701_1_nw"

    Returns:
        tuple[float, float, float, float]: extent
    """
    # extract the bounding box from the tile name
    # e.g. "3dm_32_511_5701_1_nw" -> (511, 5701, 512, 5702)
    parts = name.split("_")
    x_km, y_km = int(parts[2]), int(parts[3])
    extent_km = int(parts[4])

    x_m = x_km * 1000
    y_m = y_km * 1000
    extent_m = extent_km * 1000
    return (x_m, y_m, x_m + extent_m, y_m + extent_m)


def get_buildings_from_bbox(
    bbox: tuple[float, float, float, float],
    *,
    with_address: bool = True,
    uid_column_name: str = "building_id",
) -> gpd.GeoDataFrame:
    """Given a GPS bounding box, fetch buildings from OpenStreetMap.

    Args:
        bbox (tuple[float, float, float, float]): Box with (lon_min, lat_min, lon_max, lat_max)
        with_address (bool, optional): Whether to return only boxes with an address. Defaults to True.

    Returns:
        gpd.GeoDataFrame: buildings with WGS84 geometries, the index of the dataframe is a unique UUID4
    """
    # Fetch buildings
    # bbox_lat_lon = (bbox[1], bbox[0], bbox[3], bbox[2])  # neede for onnx
    buildings_gdf = ox.features_from_bbox(bbox, tags={"building": True})

    if "addr:street" not in buildings_gdf:
        buildings_gdf["addr:street"] = None

    if with_address:
        buildings_gdf = buildings_gdf[buildings_gdf["addr:street"].notnull()]

    buildings_gdf[uid_column_name] = buildings_gdf.apply(
        lambda _: str(uuid.uuid4()), axis=1
    )

    buildings_gdf = buildings_gdf.set_index(uid_column_name)

    return buildings_gdf


def delete_all_files_in_folder(folder_path: str):
    files = glob.glob(os.path.join(folder_path, "*"))
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"Error deleting {f}: {e}")
