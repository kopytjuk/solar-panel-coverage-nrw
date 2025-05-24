from building_finder.extract_buildings import extract_buildings


def test_extract_buildings():
    # Test the extract_buildings function with a local file system
    tile_name = "318_5653_1"

    buildings_gdf = extract_buildings(tile_name, with_address=True)

    assert len(buildings_gdf) > 10
