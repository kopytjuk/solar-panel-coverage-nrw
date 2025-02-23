from pathlib import Path
from urllib.parse import urljoin

import geopandas as gpd
import pandas as pd
import requests
import shapely

from utils.opengeodata_nrw import (
    DOWNLOAD_BASE_URL,
    FILE_EXTENSIONS,
    DatasetType,
)


class TileManager:
    # internal columns
    extent_columns = ["min_x", "min_y", "extent"]

    def __init__(
        self,
        tile_info: pd.DataFrame,
        data_folder: str | Path | None = None,
        tile_type: DatasetType | None = None,
    ):
        """Initialize the TileManager

        Args:
            tile_info (pd.DataFrame): dataframe with
                columns `tile_name`, `min_x`, `min_y`, `extent`
        """

        # extract the geometries
        tile_geometries = [
            shapely.box(
                row["min_x"],
                row["min_y"],
                row["min_x"] + row["extent"],
                row["min_y"] + row["extent"],
            )
            for _, row in tile_info.iterrows()
        ]
        tile_info = gpd.GeoDataFrame(tile_info, geometry=tile_geometries)

        self.tile_info = tile_info

        self._data_folder = Path(data_folder) if isinstance(data_folder, str) else data_folder
        self._tile_type = tile_type

    def get_tile_name_from_point(self, x: float, y: float, with_extension: bool = False) -> str:
        """Get the tile name for a given point

        Args:
            x (float): x-coordinate
            y (float): y-coordinate

        Returns:
            str: tile name
        """

        pt = shapely.Point(x, y)

        # filter tiles that contain the point
        mask = self.tile_info.geometry.intersects(pt)

        tiles = self.tile_info[mask]

        if tiles.empty:
            raise ValueError(f"No tile found for point ({x}, {y})")

        if tiles.shape[0] > 1:
            raise ValueError(f"Multiple tiles found for point ({x}, {y}), should not happen!")

        tile_name = tiles["tile_name"].iloc[0]

        extension = FILE_EXTENSIONS[self._tile_type]

        if tile_name.endswith(f".{extension}"):
            tile_name = tile_name.split(f".{extension}")[0]

        if with_extension:
            return f"{tile_name}.{extension}"
        else:
            return tile_name

    def get_tiles_intersecting(self, polygon: shapely.Polygon) -> list[str]:
        """Get the tile names that intersect with a given polygon

        Args:
            polygon (shapely.Polygon): polygon of interset (UTM32N)

        Raises:
            ValueError: in case no tiles can be found

        Returns:
            list[str]: list of tiles
        """

        # filter tiles that contain the point
        mask = self.tile_info.geometry.intersects(polygon)

        tiles = self.tile_info[mask]

        if tiles.empty:
            raise ValueError("No tile found for input polygon")

        return tiles["tile_name"].tolist()

    def check_if_tile_exists(self, tile_name: str) -> bool:
        """Check if a tile exists in the data folder

        Args:
            tile_name (str): tile name

        Returns:
            bool: True if the tile exists
        """

        file_extension = FILE_EXTENSIONS[self._tile_type]
        tile_path = self._data_folder / f"{tile_name}.{file_extension}"
        return tile_path.exists()

    def download_tile(
        self,
        tile_name: str,
        overwrite: bool = False,
    ):
        """Download a tile from a given URL

        Args:
            tile_name (str): tile name
            overwrite (bool, optional): overwrite the file if it exists.
                Defaults to False.
        """
        file_extension = FILE_EXTENSIONS[self._tile_type]
        tile_filename = f"{tile_name}.{file_extension}"
        tile_path = self._data_folder / tile_filename

        if self.check_if_tile_exists(tile_name) and not overwrite:
            print("File already exists, skipping download!")
            return

        base_url = DOWNLOAD_BASE_URL[self._tile_type]
        download_url = urljoin(base_url, tile_filename)

        download_file(download_url, str(tile_path))

    @classmethod
    def from_tile_file(
        cls,
        tile_overview_path: str,
        data_folder: str | Path | None = None,
        tile_type: DatasetType | None = None,
    ) -> "TileManager":
        """Initialize the TileManager from the official overview CSV file like
        `dop_nw.csv` or `3dm_nw.csv`

        Args:
            tile_overview_path (str): file path

        Returns:
            TileManager: tile manager instance
        """
        tile_info = pd.read_csv(tile_overview_path, sep=";", header=5)
        tile_info["tile_name"] = tile_info["Kachelname"]

        # the second, third and fourth part of the tile name are
        # the x, y and extent in km, e.g.:
        # dop10rgbi_32_478_5740_1_nw_2024 -> 478, 5740, 1
        tile_extent = (
            tile_info["tile_name"].str.split("_", expand=True).loc[:, 2:4].astype(int)
            * 1000  # for km to m
        )
        tile_extent.columns = cls.extent_columns
        tile_info = pd.concat([tile_info, tile_extent], axis=1)

        tile_info = tile_info[["tile_name"] + cls.extent_columns]

        return cls(tile_info, data_folder=data_folder, tile_type=tile_type)

    @classmethod
    def from_html_extraction_result(
        cls,
        fp: str,
        data_folder: str | Path | None = None,
        tile_type: DatasetType | None = None,
    ):
        """Read tile information from the HTML extraction result file created by
        the `scripts/extract_html_table.py` script.

        E.g.
        - `Strahlungsenergie-NRW-KWh-Yr-Shd-50cm-V23_32280_5648_4.tif` -> 280, 5648, 4
        - `dop10rgbi_32_32280_5648_4_nw_2024.tif` -> 280, 5648, 4

        Note, that the leading 32 in 32280 should be separated with "_", probably
        an error in the naming of the data.

        Args:
            fp (str): file path
        """
        tile_info = pd.read_csv(fp, sep=",")
        tile_info["tile_name"] = tile_info["File"]

        if tile_type == DatasetType.AERIAL_IMAGE:
            tile_extent = (
                tile_info["tile_name"].str.split("_", expand=True).loc[:, 2:4].astype(int)
                * 1000  # for km to m
            )
        else:
            # Extract extent for other types
            extent_list = list()
            for name in tile_info["tile_name"]:
                # remove file ending
                name = name.split(".")[0]
                name_split = name.split("_")
                first_part = name_split[1]
                min_x = int(first_part.replace("32", "")) * 1000
                min_y = int(name_split[2]) * 1000
                extent = int(name_split[3]) * 1000
                extent_list.append({"min_x": min_x, "min_y": min_y, "extent": extent})
            tile_extent = pd.DataFrame(extent_list)

        tile_extent.columns = cls.extent_columns
        tile_info = pd.concat([tile_info, tile_extent], axis=1)

        return cls(tile_info, data_folder=data_folder, tile_type=tile_type)


def get_bounding_box_from_tile_name(
    name: str,
) -> tuple[float, float, float, float]:
    """Extract the bounding box from a tile name.

    Args:
        name (str): tile name, e.g. "511_5701_1"

    Returns:
        tuple[float, float, float, float]: extent
    """
    parts = name.split("_")
    x_km, y_km = int(parts[0]), int(parts[1])
    extent_km = int(parts[2])

    x_m = x_km * 1000
    y_m = y_km * 1000
    extent_m = extent_km * 1000
    return (x_m, y_m, x_m + extent_m, y_m + extent_m)


def download_file(url: str, local_filename: str):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename
