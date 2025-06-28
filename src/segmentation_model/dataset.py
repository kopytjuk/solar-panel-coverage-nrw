from pathlib import Path

import albumentations as A
import cv2
import torch
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset


class PvSegmentationDataset(Dataset):
    def __init__(
        self,
        image_files: list[Path],
        mask_files: list[Path],
        *,
        resize_shape: tuple[int, int] = (256, 256),
        transform: A.Compose | None = None,
    ):
        """
        Args:
            data (list): List of tuples containing image and mask paths.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        # self._root_folder = Path(root_dir)

        images_file_names = {image_file.stem for image_file in image_files}
        mask_file_names = {mask_file.stem for mask_file in mask_files}

        valid_samples = images_file_names.intersection(mask_file_names)

        image_files = [
            image_file for image_file in image_files if image_file.stem in valid_samples
        ]
        mask_files = [mask_file for mask_file in mask_files if mask_file.stem in valid_samples]

        image_files = sorted(image_files, key=lambda x: x.stem)
        mask_files = sorted(mask_files, key=lambda x: x.stem)

        self._samples_list = list(zip(image_files, mask_files))
        self._resize_shape = resize_shape
        self._transform = transform

    @staticmethod
    def load_image(image_path: Path, resize_shape: tuple[int, int] = (256, 256)) -> torch.Tensor:
        """Load an image from the given path. Returns in CHW format."""

        pil_image = Image.open(image_path).convert("RGB")  # Ensure image is in RGB format
        # Convert to torch tensor (CHW format)
        transform = T.Compose(
            [
                T.Resize(resize_shape),  # Resize to a fixed size (optional)
                T.ToTensor(),  # This converts PIL Image to tensor and normalizes to [0, 1]
            ]
        )

        # Apply transform
        torch_tensor = transform(pil_image)  # Shape will be (C, H, W)
        return torch_tensor

    @staticmethod
    def load_mask(mask_path: Path, resize_shape: tuple[int, int] = (256, 256)) -> torch.Tensor:
        """Load a mask from the given path. Returns in CHW format."""
        pil_mask = Image.open(mask_path)
        # Convert to torch tensor (CHW format)
        transform = T.Compose(
            [
                T.Resize(resize_shape),  # Resize to a fixed size (optional)
                T.ToTensor(),  # This converts PIL Image to tensor and normalizes to [0, 1]
                T.Lambda(lambda x: x.long()),  # Convert to long type for masks
            ]
        )

        # Apply transform
        torch_tensor = transform(pil_mask)
        return torch_tensor

    def __len__(self):
        return len(self._samples_list)

    def __getitem__(self, idx) -> tuple[torch.Tensor, torch.Tensor]:
        image_path, mask_path = self._samples_list[idx]

        if self._transform:
            # Read image and mask (as suggested in the albumentations docs)
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = image.astype("float32")

            mask = cv2.imread(mask_path, cv2.COLOR_BGR2GRAY)
            mask = mask.astype("float32")

            image = image / 255.0  # Normalize image to [0, 1]
            mask = mask / 255.0  # Normalize mask to [0, 1]

            # Pass both image and mask
            augmented = self._transform(image=image, mask=mask)

            image, mask = augmented["image"], augmented["mask"]

            mask = torch.unsqueeze(mask, 0)  # Add channel dimension to mask

        else:
            image = self.load_image(image_path, self._resize_shape)
            mask = self.load_mask(mask_path, self._resize_shape)
        return image, mask
