#!/bin/zsh

# ---- CONFIGURATION START ----
# TILES=("318_5653_1")
TILES=("318_5652_1" "318_5653_1" "318_5654_1" "319_5652_1" "319_5653_1" "319_5654_1" "320_5652_1" "320_5653_1" "320_5654_1")

SEGMENTATION_THRESHOLD=0.8

MAIN_REPO_FOLDER=$(pwd)
SOLAR_PANEL_DETECTOR_REPO_FOLDER="/Users/kopytjuk/Code/solar-panel-segmentation"

OUTPUT_MAIN_FOLDER=/Users/kopytjuk/Data/roof-analysis/Titz/


# to allow deletions in ZSH
setopt localoptions rmstarsilent


# ---- CONFIGURATION END ----

for TILE in "${TILES[@]}"; do

    echo "### Processing tile $TILE ###"

    TILE_RESULT_FOLDER="$OUTPUT_MAIN_FOLDER/$TILE"

    # Delete all contents within the folder
    rm -rf "$TILE_RESULT_FOLDER/*"

    echo "Creating the output folder: $TILE_RESULT_FOLDER"
    mkdir -p $TILE_RESULT_FOLDER

    if [[ -n "$VIRTUAL_ENV" && -f "$VIRTUAL_ENV/bin/poetry" ]]; then
        echo "Poetry environment active! Deactivating the current poetry environment."
        deactivate
    fi

    echo "----- Extract the bulding information in the tile -----"

    poetry run building-selector $TILE $TILE_RESULT_FOLDER \
        || { echo "building-selector failed for tile $TILE. Skipping to next tile."; rm -rf $TILE_RESULT_FOLDER; continue; }


    echo "----- Crop the images for the solar panel detector -----"

    IMAGES_AND_MASKS_PARENT_FOLDER="$TILE_RESULT_FOLDER/aerial-images/"

    CROPPED_IMAGES_FOLDER="$IMAGES_AND_MASKS_PARENT_FOLDER/raw/"
    mkdir -p $CROPPED_IMAGES_FOLDER
    poetry run image-cropper "$TILE_RESULT_FOLDER/buildings_general_info.gpkg" $CROPPED_IMAGES_FOLDER \
        || { echo "Image-cropping failed for tile $TILE. Skipping to next tile."; rm -rf $TILE_RESULT_FOLDER; continue; }

    echo "----- Detect solar panels from images -----"

    cd $SOLAR_PANEL_DETECTOR_REPO_FOLDER

    # create segmentation masks
    SEGMENTATION_MASK_FOLDER="$IMAGES_AND_MASKS_PARENT_FOLDER/masks/"
    poetry run python run.py segment_new_data $IMAGES_AND_MASKS_PARENT_FOLDER $SEGMENTATION_MASK_FOLDER

    # go back
    cd $MAIN_REPO_FOLDER

    echo "----- Determine the energy yield -----"
    poetry run energy-extractor "$TILE_RESULT_FOLDER/buildings_general_info.gpkg" $CROPPED_IMAGES_FOLDER $SEGMENTATION_MASK_FOLDER \
        "$TILE_RESULT_FOLDER/energy_yield.csv" --segmentation-threshold $SEGMENTATION_THRESHOLD

    
    echo "----- Combine information -----"
    poetry run combine-results $TILE_RESULT_FOLDER "$TILE_RESULT_FOLDER/final.gpkg"

    echo "Done with tile $TILE!"

done

echo "All tiles processed!"