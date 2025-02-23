# Combine all info


from pathlib import Path

import geopandas as gpd
import pandas as pd

from utils.logging import get_library_logger

logger = get_library_logger(__name__)


def combine_information(
    result_folder: Path, confidence_threshold: float = 0.8
) -> gpd.GeoDataFrame:
    """Combine all information stored in `result_folder` into
    a single GeoDataFrame.

    Args:
        result_folder (Path): folder with data from previous steps
        confidence_threshold (float, optional): confidence threshold for solar
            panel detections. Defaults to 0.8.

    Yields:
        gpd.GeoDataFrame: merged data
    """

    buildings = gpd.read_file(result_folder / "buildings_general_info.gpkg")
    logger.info("Loaded buildings_general_info.gpkg")

    energy_yield = pd.read_csv(result_folder / "energy_yield.csv")

    solar_panel_detections = pd.read_csv(result_folder / "solar_panel_detections.csv")
    logger.info("Loaded solar_panel_detections.csv")

    solar_panel_detections = solar_panel_detections.rename(
        columns=lambda x: "detections_" + x if x != "building_id" else x
    )
    logger.info("Renamed columns in solar_panel_detections")

    solar_panel_detections = solar_panel_detections[
        solar_panel_detections["detections_confidence"] > confidence_threshold
    ]
    logger.info(
        f"Filtered solar_panel_detections by confidence (threshold: {confidence_threshold:.2f})",
    )

    # Merge buildings and energy_yield dataframes
    merged_df = buildings.merge(energy_yield, on="building_id", how="left")

    # Merge the result with solar_panel_detections dataframe
    merged_df = merged_df.merge(solar_panel_detections, on="building_id", how="left")

    # Buildings, which have no detections have `NA`s in columns corresponding to detections
    # leading to a False after the `notnull()` operation
    merged_df["solar_panel_installed"] = merged_df["detections_confidence"].notnull()

    final_df = (
        merged_df.groupby("building_id")
        .agg(
            {
                "energy_sum_kWh": "min",
                "solar_panel_installed": "min",
                "detections_area_m2": "sum",
            }
        )
        .reset_index(drop=False)
    )

    # merge to get the original geometry back
    final_df = final_df.merge(buildings, on="building_id", how="left")

    # to geodataframe, to have the geometries of the buildings
    final_gdf = gpd.GeoDataFrame(final_df, geometry="geometry")
    return final_gdf
