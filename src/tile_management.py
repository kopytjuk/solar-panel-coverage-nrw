import pandas as pd


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


class TileManager:
    def __init__(self, tile_overview_path: str):
        tile_info = pd.read_csv(tile_overview_path, sep=";", header=5)

        tile_info = tile_info.set_index(
            "Kachelname", drop=False
        )  # for faster lookup

        self.tile_info = tile_info

    def get_file_name_for_tile(self, tile_name: str) -> str:
        """Get file name of the image of the tile

        Args:
            tile_name (str): tile name, like `478_5740_1`

        Returns:
            str: file name of the image file,
                e.g. `dop10rgbi_32_478_5740_1_nw_2024.jp2`
        """

        single_tile = self.tile_info[
            self.tile_info["Kachelname"].str.contains(tile_name)
        ]

        if single_tile.empty:
            raise ValueError(
                f"Tile {tile_name} not found in the tile overview"
            )

        single_tile = single_tile.iloc[0]

        file_name = f"{single_tile['Kachelname']}.jp2"
        return file_name

    def get_all_tiles(self) -> list[str]:
        tile_names = self.tile_info["Kachelname"].str.extract(
            r"dop10rgbi_\d+_(\d+_\d+_\d+)_"
        )[0]
        return tile_names.to_list()
