from urllib.parse import urlparse


def parse_blob_storage_uri(uri) -> tuple[str, str]:
    # Parse the URI
    parsed_uri = urlparse(uri)

    # Extract the path components
    path_components = parsed_uri.path.strip("/").split("/")

    # The container name is the first component
    container_name = path_components[0]

    # The blob path is the rest of the components, joined by '/'
    blob_path = "/".join(path_components[1:]) if len(path_components) > 1 else ""

    return container_name, blob_path
