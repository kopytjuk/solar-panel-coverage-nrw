import os
from pathlib import Path

import pandas as pd
import rasterio
from tqdm import tqdm


def crop_images_from_buildings(
    buildings_gpkg_path: str, image_data_location: str, output_location: str
):
    output_location = Path(output_location)
    output_location.mkdir(parents=True, exist_ok=True)

    buildings = gpd.read_file(buildings_gpkg_path)

    image_tile_name = buildings["image_tile"].unique()[0]
    image_filepath = os.path.join(
        image_data_location, image_tile_name + ".jp2"
    )

    with rasterio.open(image_filepath) as image_file:
        affine_transform = image_file.transform

        for building_id, building_data in tqdm(
            buildings.iterrows(), total=len(buildings)
        ):
            building_polygon = building_data["geometry"]
            example_building_buffered_box = building_polygon.envelope.buffer(
                5.0
            )

            crop_window = rasterio.windows.from_bounds(
                *example_building_buffered_box.bounds,
                transform=affine_transform,
            )

            image_data = image_file.read(window=crop_window)

            image_data = image_data[:3, ...]
            image_data = np.moveaxis(image_data, 0, -1)

            plt.imsave(
                output_location / f"{building_id}.png",
                arr=image_data,
                dpi=200,
            )

    overview_data = {
        "building_id": [],
        "image_path": [],
    }

    for building_id in buildings["building_id"]:
        overview_data["building_id"].append(building_id)
        overview_data["image_path"].append(
            str(output_location / f"{building_id}.png")
        )

    overview_df = pd.DataFrame(overview_data)
    overview_df.to_csv(output_location / "overview.csv", index=False)
