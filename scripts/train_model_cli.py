"""Trains a PV segmentation model."""

import json
import shutil
from pathlib import Path

import click

from segmentation_model.training import train_model
from utils.logging import get_client_logger

logger = get_client_logger(level="INFO")


@click.command()
@click.argument("root_dir", type=click.Path(exists=True))
@click.argument("output_folder", type=click.Path())
@click.option("--batch-size", "-b", default=8, help="Batch size for training")
@click.option("--num-workers", "-w", default=4, help="Number of data loader workers")
@click.option(
    "--num-samples", "-ns", default=None, help="Number of total samples to use", type=click.INT
)
@click.option("--epochs", "-e", default=10, help="Number of training epochs")
@click.option("--learning-rate", "-lr", default=1e-3, help="Learning rate", type=click.FLOAT)
@click.option(
    "--patience",
    "-pt",
    default=10,
    help="Number of epochs to run without improvement before stopping the training",
    type=click.INT,
)
@click.option(
    "--train-encoder/--freeze-encoder", default=False, help="Whether to train the encoder"
)
@click.option(
    "--use-augmentation",
    "-au",
    help="Whether to apply image augmentation on top of the training data",
    default=False,
    is_flag=True,
    type=click.BOOL,
)
def train_model_cli(
    root_dir: str,
    output_folder: str,
    batch_size: int,
    num_workers: int,
    epochs: int,
    learning_rate: float,
    patience: int,
    train_encoder: bool,
    use_augmentation: bool,
    num_samples: int | None = None,
):
    """Train a segmentation model CLI wrapper."""

    output_folder = Path(output_folder)
    checkpoint_path = output_folder / "_checkpoints"
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    model, test_metrics = train_model(
        root_dir=Path(root_dir),
        output_dir=checkpoint_path,
        batch_size=batch_size,
        num_workers=num_workers,
        patience=patience,
        epochs=epochs,
        learning_rate=learning_rate,
        train_encoder=train_encoder,
        num_samples=num_samples,  # Not used in this function
        use_augmentation=use_augmentation,
    )

    # remove checkpoints folder
    shutil.rmtree(str(checkpoint_path))

    model_path = output_folder / "stored_model"
    model_path.mkdir(parents=True, exist_ok=True)

    model.save_model(model_path)

    # store metrics
    test_metrics_as_json = json.dumps(test_metrics, indent=4)
    (output_folder / "test_metrics.json").write_text(test_metrics_as_json)


if __name__ == "__main__":
    train_model_cli()
