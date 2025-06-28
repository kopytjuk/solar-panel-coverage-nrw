"""Trains a PV segmentation model."""

from pathlib import Path

import lightning as pl
import segmentation_models_pytorch as smp
import torch
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split

from segmentation_model.augmentations import train_augmentation_basic
from segmentation_model.dataset import PvSegmentationDataset
from segmentation_model.model import PvSegmentationModel
from utils.logging import get_library_logger

logger = get_library_logger(__name__)


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
    image_shape: tuple[int, int] = (256, 256),
    use_augmentation: bool = True,
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

    image_files, mask_files = list_images_and_masks_in_folder(root_dir)

    if num_samples is not None:
        logger.info(f"Using only {num_samples} samples for training.")
        image_files = image_files[:num_samples]
        mask_files = mask_files[:num_samples]

    images_train, masks_train, images_val, images_test, masks_val, masks_test = (
        split_into_train_val_test(image_files, mask_files)
    )

    if use_augmentation:
        logger.info("Using data augmentation for training!")
        training_transform = train_augmentation_basic
    else:
        training_transform = None

    # Initialize dataset
    train_dataset = PvSegmentationDataset(
        image_files=images_train,
        mask_files=masks_train,
        resize_shape=image_shape,
        transform=training_transform,
    )
    valid_dataset = PvSegmentationDataset(
        image_files=images_val, mask_files=masks_val, resize_shape=image_shape
    )
    test_dataset = PvSegmentationDataset(
        image_files=images_test, mask_files=masks_test, resize_shape=image_shape
    )
    logger.info(
        f"Train dataset size: {len(train_dataset)}, "
        f"Validation dataset size: {len(valid_dataset)}, "
        f"Test dataset size: {len(test_dataset)}"
    )

    # Create data loaders
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    valid_loader = torch.utils.data.DataLoader(
        valid_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Initialize model training
    model_manager = PvSegmentationModel(
        train_encoder=train_encoder,
        learning_rate=learning_rate,
        training_transform=training_transform,
    )

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
    trainer.fit(model_manager, train_loader, valid_loader)

    best_model_path = checkpoint_callback.best_model_path

    model_manager = PvSegmentationModel.load_from_checkpoint(best_model_path)

    valid_metrics = trainer.validate(model_manager, dataloaders=valid_loader, verbose=False)
    valid_metrics = valid_metrics[0]  # list equals the number of dataloaders
    print(valid_metrics)

    test_metrics = trainer.test(model_manager, dataloaders=test_loader, verbose=False)
    test_metrics = test_metrics[0]
    print(test_metrics)

    return model_manager, test_metrics


def split_into_train_val_test(image_files, mask_files):
    images_train, images_temp, masks_train, masks_temp = train_test_split(
        image_files, mask_files, test_size=0.4, random_state=42
    )

    # Then, split temp into val and test
    images_val, images_test, masks_val, masks_test = train_test_split(
        images_temp, masks_temp, test_size=0.5, random_state=42
    )

    return images_train, masks_train, images_val, images_test, masks_val, masks_test


def list_images_and_masks_in_folder(root_dir):
    image_folder_name = "images"
    mask_folder_name = "labels"

    image_folder = root_dir / image_folder_name
    mask_folder = root_dir / mask_folder_name
    if not image_folder.exists() or not mask_folder.exists():
        raise FileNotFoundError(f"Image or mask folder does not exist in {root_dir}")

    extension: str = "tif"
    image_files = list(image_folder.glob(f"*.{extension}"))
    mask_files = list(mask_folder.glob(f"*.{extension}"))

    images_file_names = {image_file.stem for image_file in image_files}
    mask_file_names = {mask_file.stem for mask_file in mask_files}

    valid_samples = images_file_names.intersection(mask_file_names)

    image_files = [image_file for image_file in image_files if image_file.stem in valid_samples]
    mask_files = [mask_file for mask_file in mask_files if mask_file.stem in valid_samples]

    image_files = sorted(image_files, key=lambda x: x.stem)
    mask_files = sorted(mask_files, key=lambda x: x.stem)
    return image_files, mask_files
