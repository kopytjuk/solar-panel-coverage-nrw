#!/bin/zsh

# ---- CONFIGURATION START ----
TILE="511_5701_1"
OUTPUT_RESULT_FOLDER="/Users/kopytjuk/Data/roof-analysis/$TILE"
MAIN_REPO_FOLDER=$(pwd)
SOLAR_PANEL_DETECTOR_REPO_FOLDER="/Users/kopytjuk/Code/Solar-Panel-Detector"
# ---- CONFIGURATION END ----

echo "Creating the output folder: $OUTPUT_RESULT_FOLDER"
mkdir -p $OUTPUT_RESULT_FOLDER

pyenv local 3.12

if [[ -n "$VIRTUAL_ENV" && -f "$VIRTUAL_ENV/bin/poetry" ]]; then
    echo "Poetry environment active! Deactivating the current poetry environment."
    deactivate
fi

echo "----- Extract the bulding information in the tile -----"

poetry run building-selector 511_5701_1 $OUTPUT_RESULT_FOLDER

echo "----- Determine the energy yield -----"

poetry run energy-extractor "$OUTPUT_RESULT_FOLDER/buildings_general_info.gpkg" "$OUTPUT_RESULT_FOLDER/energy_yield.csv"

echo "----- Crop the images for the solar panel detector -----"

IMAGE_OUTPUT_FOLDER="$OUTPUT_RESULT_FOLDER/aerial-images"
mkdir -p $IMAGE_OUTPUT_FOLDER
poetry run image-cropper "$OUTPUT_RESULT_FOLDER/buildings_general_info.gpkg" $IMAGE_OUTPUT_FOLDER

echo "----- Detect the solar panels from images -----"

cd $SOLAR_PANEL_DETECTOR_REPO_FOLDER

source .venv/bin/activate

cd $SOLAR_PANEL_DETECTOR_REPO_FOLDER/src

python detect_cli.py $IMAGE_OUTPUT_FOLDER "$OUTPUT_RESULT_FOLDER/solar_panel_detections.csv"

deactivate

# TODO: combine all the data
cd $MAIN_REPO_FOLDER

poetry run combine-results $OUTPUT_RESULT_FOLDER "$OUTPUT_RESULT_FOLDER/final.gpkg"

echo "Done!"