import re
import time

import click
import fsspec
import pandas as pd
import requests
from adlfs.spec import AzureBlobFileSystem
from azure.identity.aio import DefaultAzureCredential
from tqdm import tqdm

from utils.azure import parse_blob_storage_uri
from utils.opengeodata_nrw import parse_download_links


def download_files(links: pd.DataFrame, destination: str, polling_interval: float = 1.0):
    if "blob.core.windows" in destination:
        default_credential = DefaultAzureCredential()
        fs = AzureBlobFileSystem(
            account_name="solaryieldstorage",
            credential=default_credential,
        )
        container, path = parse_blob_storage_uri(destination)

        output_path = fs.sep.join([container, path])
        if output_path.endswith("/"):
            output_path = output_path[:-1]
    else:
        fs = fsspec.filesystem("file")
        output_path = destination
        if not fs.isdir(output_path):
            fs.mkdir(output_path, exist_ok=True, create_parents=True)

    for _, row in tqdm(links.iterrows(), "Downloading files", total=len(links)):
        file_url = row["url"]
        file_name = row["name"]

        dest_path = fs.sep.join([output_path, file_name])

        with fs.open(dest_path, "wb") as f:
            # in-memory download
            response = requests.get(file_url)
            f.write(response.content)

        time.sleep(polling_interval)


@click.command()
@click.argument("url")
@click.argument("destination")
@click.option("--filter", default=None, help="Filter for file names")
def main(url, destination: str, filter: str | None):
    """Downloads all files from the given URL to the specified destination (local or Azure Blob Storage)."""
    files_df = parse_download_links(url)

    if filter:
        regex = re.compile(filter)
        files_df = files_df[files_df["name"].str.match(regex)]

    total_size = files_df["size"].sum()
    print(f"Total size of {len(files_df)} files to download: {total_size / (1024**3):.2f} GB")

    download_files(files_df, destination)

    print("Done!")


if __name__ == "__main__":
    main()
