from enum import StrEnum

import pandas as pd
import requests
from bs4 import BeautifulSoup


class DatasetType(StrEnum):
    AERIAL_IMAGE = "aerial_image"
    ENERGY_YIELD_50CM = "energy_yield_50cm"
    ENERGY_YIELD_100CM = "energy_yield_100cm"


# lookup for base urls for the different datasets
DOWNLOAD_BASE_URL = {
    DatasetType.AERIAL_IMAGE: "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/akt/dop/dop_jp2_f10/",
    DatasetType.ENERGY_YIELD_50CM: "https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/strahlungsenergie_50cm/",
    DatasetType.ENERGY_YIELD_100CM: "https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/strahlungsenergie_1m/",
}

FILE_EXTENSIONS = {
    DatasetType.AERIAL_IMAGE: "jp2",
    DatasetType.ENERGY_YIELD_50CM: "tif",
    DatasetType.ENERGY_YIELD_100CM: "tif",
}


def parse_download_links(
    url: str, dataset_type: DatasetType = DatasetType.AERIAL_IMAGE
) -> pd.DataFrame:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features="xml")

    files = list()
    for file_tag in soup.find_all("file"):
        file_name = file_tag.get("name")
        size_bytes = file_tag.get("size")
        file = {
            "name": file_name,
            "size": int(size_bytes),
        }
        files.append(file)
    # Create a DataFrame from the list of files
    df = pd.DataFrame(files)

    # add url
    df["url"] = df["name"].apply(lambda x: DOWNLOAD_BASE_URL[dataset_type] + f"{x}")

    return df
