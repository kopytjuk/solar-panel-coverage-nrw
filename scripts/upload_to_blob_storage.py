from pathlib import Path

from azure.storage.blob import BlobServiceClient

from utils.tile_management import DatasetType, TileManager

# Azure Blob Storage configuration
AZURE_CONNECTION_STRING = "your_connection_string"
AZURE_CONTAINER_NAME = "your_container_name"


def upload_to_azure(blob_service_client, local_file_path, blob_name):
    blob_client = blob_service_client.get_blob_client(
        container=AZURE_CONTAINER_NAME, blob=blob_name
    )
    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"Uploaded {local_file_path} to {blob_name}")


def main():
    # Initialize TileManager
    tile_overview_path = "path_to_your_tile_overview.csv"
    data_folder = "path_to_your_local_data_folder"
    tile_manager = TileManager.from_tile_file(
        tile_overview_path, data_folder, DatasetType.AERIAL_IMAGE
    )

    # List of tile names to download
    tile_names = ["tile_name_1", "tile_name_2", "tile_name_3"]

    BlobServiceClient()

    # Initialize Azure Blob Service Client
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

    for tile_name in tile_names:
        # Download tile
        tile_manager.download_tile(tile_name, overwrite=True)
        local_file_path = Path(data_folder) / f"{tile_name}.{tile_manager.file_extension}"

        # Upload to Azure Blob Storage
        upload_to_azure(
            blob_service_client, local_file_path, f"{tile_name}.{tile_manager.file_extension}"
        )


if __name__ == "__main__":
    main()
