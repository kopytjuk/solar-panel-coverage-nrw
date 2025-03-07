#!/bin/zsh

# ---- CONFIGURATION START ----
# TILES=("318_5652_1")
TILES=("318_5652_1" "318_5653_1" "318_5654_1" "319_5652_1" "319_5653_1" "319_5654_1" "320_5652_1" "320_5653_1" "320_5654_1")


MAIN_REPO_FOLDER=$(pwd)
SOLAR_PANEL_DETECTOR_REPO_FOLDER="/Users/kopytjuk/Code/solar-panel-segmentation"

OUTPUT_MAIN_FOLDER=/Users/kopytjuk/Data/roof-analysis/Titz/


poetry_activate() {
    source $(poetry env info --path)/bin/activate
}

# to allow deletions in ZSH
setopt localoptions rmstarsilent


poetry_activate

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

    echo "----- Determine the energy yield -----"

    poetry run energy-extractor "$TILE_RESULT_FOLDER/buildings_general_info.gpkg" "$TILE_RESULT_FOLDER/energy_yield.csv" \
        || { echo "energy-extractor failed for tile $TILE. Skipping to next tile."; rm -rf $TILE_RESULT_FOLDER; continue; }

    echo "----- Crop the images for the solar panel detector -----"

    IMAGES_AND_MASKS_PARENT_FOLDER="$TILE_RESULT_FOLDER/aerial-images/"

    CROPPED_IMAGES_FOLDER="$IMAGES_AND_MASKS_PARENT_FOLDER/raw/"
    mkdir -p $CROPPED_IMAGES_FOLDER
    poetry run image-cropper "$TILE_RESULT_FOLDER/buildings_general_info.gpkg" $CROPPED_IMAGES_FOLDER

    echo "----- Detect solar panels from images -----"

    cd $SOLAR_PANEL_DETECTOR_REPO_FOLDER

    poetry_activate

    # create segmentation masks
    SEGMENTATION_MASK_FOLDER="$TILE_RESULT_FOLDER/aerial-images/masks/"
    python run.py segment_new_data $IMAGES_AND_MASKS_PARENT_FOLDER $SEGMENTATION_MASK_FOLDER

    # go back
    cd $MAIN_REPO_FOLDER
    poetry_activate

    # TODO: determine the amount of installed solar panels
    
    # poetry run determine-panels $IMAGES_AND_MASKS_PARENT_FOLDER "$TILE_RESULT_FOLDER/detected-panels.csv"
    
    # combine all the data
    # poetry run combine-results $TILE_RESULT_FOLDER "$TILE_RESULT_FOLDER/final.gpkg"

    echo "Done with tile $TILE!"

    deactivate
done

echo "All tiles processed!"