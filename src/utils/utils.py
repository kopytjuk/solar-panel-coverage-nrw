import geopandas as gpd
import osmnx as ox


def get_buildings_from_bbox(
    bbox: tuple[float, float, float, float],
    *,
    with_address: bool = True,
    uid_column_name: str = "building_id",
) -> gpd.GeoDataFrame:
    """Given a GPS bounding box, fetch buildings from OpenStreetMap and return
    them as a GeoDataFrame.

    Args:
        bbox (tuple[float, float, float, float]): Box with
            (lon_min, lat_min, lon_max, lat_max)
        with_address (bool, optional): Whether to return only boxes
            with an address. Defaults to True.

    Returns:
        gpd.GeoDataFrame: buildings with WGS84 geometries, the index of the
            dataframe is a unique UUID4
    """
    # Fetch buildings from OpenStreetMap
    buildings_gdf = ox.features_from_bbox(bbox, tags={"building": True})

    # ways only
    buildings_gdf = buildings_gdf.loc["way", :]
    buildings_gdf["way_id"] = buildings_gdf.index
    buildings_gdf.reset_index(drop=True, inplace=True)

    if "addr:street" not in buildings_gdf:
        buildings_gdf["addr:street"] = None

    if with_address:
        buildings_gdf = buildings_gdf[buildings_gdf["addr:street"].notnull()]

    # UUID4
    # buildings_gdf[uid_column_name] = buildings_gdf.apply(lambda _: str(uuid.uuid4()), axis=1)

    buildings_gdf[uid_column_name] = buildings_gdf["way_id"]

    buildings_gdf = buildings_gdf.set_index(uid_column_name)

    return buildings_gdf
