"""
This module provides functions to transform geometries between UTM zone 32N
(EPSG:25832) and WGS84 (EPSG:4326) coordinate reference systems using the
pyproj and shapely libraries.
"""

import pyproj
import shapely
from shapely import ops as shapely_ops

UTM_EPSG = "EPSG:25832"

transformer_to_4326 = pyproj.Transformer.from_crs(
    "EPSG:25832", "EPSG:4326", always_xy=True
)

transformer_to_25832 = pyproj.Transformer.from_crs(
    "EPSG:4326", "EPSG:25832", always_xy=True
)


def transform_utm32N_to_wgs84_geometry(
    geom: shapely.geometry.base.BaseGeometry,
) -> shapely.geometry.base.BaseGeometry:
    return shapely_ops.transform(transformer_to_4326.transform, geom)


def transform_wgs84_to_utm32N_geometry(
    geom: shapely.geometry.base.BaseGeometry,
) -> shapely.geometry.base.BaseGeometry:
    return shapely_ops.transform(transformer_to_25832.transform, geom)
