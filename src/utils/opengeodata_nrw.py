from enum import StrEnum


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
