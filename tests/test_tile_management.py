from io import StringIO

import pytest

from src.tile_management import TileManager

# Sample CSV data for testing
CSV_DATA = """\
Metadaten der DOP10 für die Datenabgabe
Land;Nordrhein-Westfalen
Eigentuemer;Land NRW, Bezirksregierung Koeln, Abteilung Geobasis NRW 
Stand;2025-01-23
Version Regelwerk;V4.0
Kachelname;Erfassungsmethode;Aktualitaet;Bildflugnummer;Kamera_Sensor;Bodenpixelgroesse;Spektralkanaele;Koordinatenreferenzsystem_Lage;Koordinatenreferenzsystem_Hoehe;Bezugsflaeche;Koordinatenursprung_East;Koordinatenursprung_North;Anzahl_Spalten;Anzahl_Zeilen;Farbtiefe;Standardabweichung;Dateiformat;Hintergrund;Quelldatenqualitaet;Kompression;Komprimierung;Belaubungszustand;Bemerkungen
dop10rgbi_32_478_5740_1_nw_2024;0;2024-04-06;1427/24 Paderborn;DMCIII-27532_DMCIII;10;RGBI;25832;7837;bDOM;478000;5740000;10000;10000;8;20;JPEG2000;0;1;1;GDAL_JP2ECW, 90;1;keine
dop10rgbi_32_478_5739_1_nw_2024;0;2024-04-06;1427/24 Paderborn;DMCIII-27532_DMCIII;10;RGBI;25832;7837;bDOM;478000;5739000;10000;10000;8;20;JPEG2000;0;1;1;GDAL_JP2ECW, 90;1;keine
dop10rgbi_32_384_5620_1_nw_2023;0;2023-05-04;1405/23;UCEM3-431S41091X314298-f100_UCE-M3;10;RGBI;25832;7837;bDOM;384000;5620000;10000;10000;8;20;JPEG2000;0;1;1;GDAL_JP2ECW, 90;2;keine
dop10rgbi_32_384_5619_1_nw_2023;0;2023-03-01;1404/23;DMCIII-27532_DMCIII;10;RGBI;25832;7837;bDOM;384000;5619000;10000;10000;8;20;JPEG2000;0;1;1;GDAL_JP2ECW, 90;1;keine
"""


@pytest.fixture
def tile_manager():
    # Use StringIO to simulate a file-like object containing the CSV data
    tile_overview_path = StringIO(CSV_DATA)
    return TileManager.from_tile_file(tile_overview_path)


def test_get_tile_name_from_point(tile_manager):
    # Test with a point inside a tile
    x, y = 478_500, 5739_500
    expected_tile_name = "dop10rgbi_32_478_5739_1_nw_2024"
    assert tile_manager.get_tile_name_from_point(x, y) == expected_tile_name

    # Test with a point outside of any tile
    x, y = 100_000, 1000_000
    with pytest.raises(ValueError, match="No tile found for point"):
        tile_manager.get_tile_name_from_point(x, y)
