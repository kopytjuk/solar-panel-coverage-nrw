"""Trains a PV segmentation model."""

import json
import shutil
from pathlib import Path

import click
import lightning as pl
import segmentation_models_pytorch as smp
import torch
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from torch.utils.data import random_split

from segmentation_model.dataset import PvSegmentationDataset
from segmentation_model.model import PvSegmentationModel


def train_model(
    root_dir: Path,
    output_dir: Path,
    batch_size: int = 8,
    num_workers: int = 4,
    patience: int = 5,
    num_samples: int | None = None,
    epochs: int = 10,
    learning_rate: float = 1e-3,
    train_encoder: bool = False,
    train_val_proportion: tuple[float, float, float] = (0.7, 0.2),
) -> smp.base.SegmentationModel:
    """Train a segmentation model.

    Args:
        root_dir: Path to the dataset directory
        batch_size: Batch size for training
        num_workers: Number of data loader workers
        epochs: Number of training epochs
        learning_rate: Learning rate
        train_encoder: Whether to train the encoder

    Returns:
        Trained Lightning trainer instance
    """
    # Initialize dataset
    if num_samples is None:
        num_samples = "full"
    full_dataset = PvSegmentationDataset(root_dir=root_dir, mode=num_samples)

    train_proportion, val_proportion = train_val_proportion
    total_size = len(full_dataset)
    train_size = int(train_proportion * total_size)
    val_size = int(val_proportion * total_size)
    test_size = total_size - train_size - val_size

    # Create the splits
    train_dataset, valid_dataset, test_dataset = random_split(
        full_dataset,
        [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(42),  # Set seed for reproducibility
    )

    # Create data loaders
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    valid_loader = torch.utils.data.DataLoader(
        valid_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Initialize model
    model = PvSegmentationModel(train_encoder=train_encoder, learning_rate=learning_rate)

    # TODO: implement model checkpointing
    metric_for_training_stop = "valid_loss"
    early_stopping_callback = EarlyStopping(
        monitor=metric_for_training_stop, mode="min", patience=patience
    )

    checkpoint_callback = ModelCheckpoint(
        monitor=metric_for_training_stop,
        dirpath=output_dir,
        filename="checkpoint-{epoch:02d}-{" + metric_for_training_stop + ":.2f}",
    )

    # Initialize Lightning trainer
    trainer = pl.Trainer(
        max_epochs=epochs,
        log_every_n_steps=1,
        callbacks=[early_stopping_callback, checkpoint_callback],
    )

    # Train the model
    trainer.fit(model, train_loader, valid_loader)

    best_model_path = checkpoint_callback.best_model_path

    model = PvSegmentationModel.load_from_checkpoint(best_model_path)

    valid_metrics = trainer.validate(model, dataloaders=valid_loader, verbose=False)
    valid_metrics = valid_metrics[0]  # list equals the number of dataloaders
    print(valid_metrics)

    test_metrics = trainer.test(model, dataloaders=test_loader, verbose=False)
    test_metrics = test_metrics[0]
    print(test_metrics)

    return model, test_metrics


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
def train_model_cli(
    root_dir: str,
    output_folder: str,
    batch_size: int,
    num_workers: int,
    epochs: int,
    learning_rate: float,
    patience: int,
    train_encoder: bool,
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
