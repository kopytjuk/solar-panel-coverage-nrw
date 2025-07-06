from pathlib import Path

import click
import torch
from PIL import Image

from segmentation_model_v2.unclassified_dataset import UnclassifiedDataset
from segmentation_model_v2.utils import determine_torch_device
from utils.logging import get_client_logger

logger = get_client_logger()


@click.command()
@click.argument("input_folder", type=click.Path(exists=True, file_okay=False))
@click.argument("output_folder", type=click.Path(file_okay=False))
@click.option(
    "--model-path",
    type=click.Path(exists=True),
    default="/Users/kopytjuk/Downloads/PV-Segmentation-deeplabv3.pt",
    help="Path to the pre-trained model file.",
)
def main_cli(input_folder, output_folder, model_path: str):
    """
    CLI tool to process images from INPUT_FOLDER and save masks to OUTPUT_FOLDER.
    """
    input_folder = Path(input_folder)

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    dataset = UnclassifiedDataset.from_folder(input_folder, resize_shape=(256, 256))
    logger.info(f"Loaded {len(dataset)} images from {input_folder}")

    batch_size = 16
    num_workers = 4
    data_loader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    logger.info(f"Data loader created with batch size {batch_size} and {num_workers} workers.")

    device = determine_torch_device()
    model = torch.load(model_path, weights_only=False, map_location=device)
    # model = model.to(device)

    for batch_idx, images in enumerate(data_loader):
        logger.info(f"Processing batch {batch_idx + 1}/{len(data_loader)}")

        logger.debug(f"Moving images to device: {device}")
        images = images.to(device)

        with torch.no_grad():
            pred_masks = model(images)["out"]
            pred_masks = torch.sigmoid(pred_masks)
            pred_masks = (pred_masks > 0.5).float()  # Binarize the masks
            pred_masks = pred_masks.cpu()

        # Assuming the model outputs masks in the same shape as input images
        for i, output in enumerate(pred_masks):
            mask = output.cpu().numpy()
            mask = (mask * 255).astype("uint8")  # Convert to uint8 for saving

            # Convert the matrix to an image
            image = Image.fromarray(mask[0, ...])

            image_path = dataset._samples_list[batch_idx * batch_size + i]

            # Save the image as a BMP file
            image_output_path = output_folder / f"{image_path.stem}.bmp"
            image.save(image_output_path)

    logger.info("Done!")


if __name__ == "__main__":
    main_cli()
