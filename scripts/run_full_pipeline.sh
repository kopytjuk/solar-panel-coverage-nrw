#!/bin/zsh

# ---- CONFIGURATION START ----
TILES=("329_5622_1" "329_5623_1" "329_5624_1" "330_5622_1" "330_5623_1" "330_5624_1" "331_5622_1" "331_5623_1" "331_5624_1")


MAIN_REPO_FOLDER=$(pwd)
SOLAR_PANEL_DETECTOR_REPO_FOLDER="/Users/kopytjuk/Code/Solar-Panel-Detector"

OUTPUT_MAIN_FOLDER=/Users/kopytjuk/Data/roof-analysis/Vettweiß/

# ---- CONFIGURATION END ----

for TILE in "${TILES[@]}"; do

    echo "### Processing tile $TILE ###"

    TILE_RESULT_FOLDER="$OUTPUT_MAIN_FOLDER/$TILE"

    echo "Creating the output folder: $TILE_RESULT_FOLDER"
    mkdir -p $TILE_RESULT_FOLDER

    pyenv local 3.12

    if [[ -n "$VIRTUAL_ENV" && -f "$VIRTUAL_ENV/bin/poetry" ]]; then
        echo "Poetry environment active! Deactivating the current poetry environment."
        deactivate
    fi

    echo "----- Extract the bulding information in the tile -----"

    poetry run building-selector $TILE $TILE_RESULT_FOLDER \
        || { echo "building-selector failed for tile $TILE. Skipping to next tile."; rm -rf $TILE_RESULT_FOLDER; continue; }

    echo "----- Determine the energy yield -----"

    poetry run energy-extractor "$TILE_RESULT_FOLDER/buildings_general_info.gpkg" "$TILE_RESULT_FOLDER/energy_yield.csv" \
        || { echo "energy-extractor failed for tile $TILE. Skipping to next tile."; rm -rf $TILE_RESULT_FOLDER; continue; }

    echo "----- Crop the images for the solar panel detector -----"

    IMAGE_OUTPUT_FOLDER="$TILE_RESULT_FOLDER/aerial-images"
    mkdir -p $IMAGE_OUTPUT_FOLDER
    poetry run image-cropper "$TILE_RESULT_FOLDER/buildings_general_info.gpkg" $IMAGE_OUTPUT_FOLDER

    echo "----- Detect the solar panels from images -----"

    cd $SOLAR_PANEL_DETECTOR_REPO_FOLDER

    source .venv/bin/activate

    cd $SOLAR_PANEL_DETECTOR_REPO_FOLDER/src

    python detect_cli.py $IMAGE_OUTPUT_FOLDER "$TILE_RESULT_FOLDER/solar_panel_detections.csv"

    deactivate

    # TODO: combine all the data
    cd $MAIN_REPO_FOLDER

    poetry run combine-results $TILE_RESULT_FOLDER "$TILE_RESULT_FOLDER/final.gpkg"

    echo "Done with tile $TILE!"
done

echo "All tiles processed!"