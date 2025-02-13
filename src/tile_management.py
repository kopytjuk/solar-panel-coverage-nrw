import pandas as pd


class TileManager:
    # internal columns
    extent_columns = ["min_x", "min_y", "extent"]

    def __init__(self, tile_info: pd.DataFrame):
        """Initialize the TileManager

        Args:
            tile_info (pd.DataFrame): dataframe with
                columns `tile_name`, `min_x`, `min_y`, `extent`
        """
        self.tile_info = tile_info

    def get_tile_name_from_point(self, x: float, y: float) -> str:
        """Get the tile name for a given point

        Args:
            x (float): x-coordinate
            y (float): y-coordinate

        Returns:
            str: tile name
        """
        # filter tiles that contain the point
        mask = (
            (self.tile_info["min_x"] <= x)
            & (self.tile_info["min_y"] <= y)
            & ((self.tile_info["min_x"] + self.tile_info["extent"]) > x)
            & ((self.tile_info["min_y"] + self.tile_info["extent"]) > y)
        )

        tile = self.tile_info[mask]

        if tile.empty:
            raise ValueError(f"No tile found for point ({x}, {y})")

        if tile.shape[0] > 1:
            raise ValueError(f"Multiple tiles found for point ({x}, {y})")

        return tile["tile_name"].iloc[0]

    @classmethod
    def from_tile_file(cls, tile_overview_path: str) -> "TileManager":
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
            tile_info["tile_name"]
            .str.split("_", expand=True)
            .loc[:, 2:4]
            .astype(int)
            * 1000  # for km to m
        )
        tile_extent.columns = cls.extent_columns
        tile_info = pd.concat([tile_info, tile_extent], axis=1)

        tile_info = tile_info[["tile_name"] + cls.extent_columns]

        return cls(tile_info)

    @classmethod
    def from_html_extraction_result(cls, fp: str):
        """Read tile information from the HTML extraction result file created by
        the `scripts/extract_html_table.py` script.

        E.g. `Strahlungsenergie-NRW-KWh-Yr-Shd-50cm-V23_32280_5648_4.tif` -> 280, 5648, 4
        Note, that the leading 32 in 32280 should be separated with "_", probably
        an error in the naming of the data.

        Args:
            fp (str): file path
        """
        tile_info = pd.read_csv(fp, sep=",")
        tile_info["tile_name"] = tile_info["File"]

        extent_list = list()

        for name in tile_info["tile_name"]:
            # remove file ending
            name = name.split(".")[0]

            name_split = name.split("_")

            first_part = name_split[1]
            min_x = int(first_part.replace("32", "")) * 1000
            min_y = int(name_split[2]) * 1000
            extent = int(name_split[3]) * 1000

            extent_list.append(
                {"min_x": min_x, "min_y": min_y, "extent": extent}
            )

        extent_df = pd.DataFrame(extent_list)
        tile_info = pd.concat([tile_info, extent_df], axis=1)
        tile_info = tile_info[["tile_name"] + cls.extent_columns]

        return cls(tile_info)


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
