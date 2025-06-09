from pathlib import Path

import torch
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset


class SegmentationDataset(Dataset):
    def __init__(self, root_dir: str | Path, extension: str = "tif", transform=None):
        """
        Args:
            data (list): List of tuples containing image and mask paths.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self._root_folder = Path(root_dir)

        image_folder = self._root_folder / "images"
        mask_folder = self._root_folder / "labels"
        if not image_folder.exists() or not mask_folder.exists():
            raise FileNotFoundError(f"Image or mask folder does not exist in {self._root_folder}")

        image_files = list(image_folder.glob(f"*.{extension}"))
        mask_files = list(mask_folder.glob(f"*.{extension}"))

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

        self._transform = transform

    def _load_image(self, image_path: Path) -> torch.Tensor:
        """Load an image from the given path. Returns in CHW format."""
        pil_image = Image.open(image_path)
        # Convert to torch tensor (CHW format)
        transform = T.Compose(
            [
                T.ToTensor()  # This converts PIL Image to tensor and normalizes to [0, 1]
            ]
        )

        # Apply transform
        torch_tensor = transform(pil_image)  # Shape will be (C, H, W)
        return torch_tensor

    def _load_mask(self, mask_path: Path) -> torch.Tensor:
        """Load a mask from the given path. Returns in CHW format."""
        pil_mask = Image.open(mask_path)
        # Convert to torch tensor (CHW format)
        transform = T.Compose(
            [
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
        image = self._load_image(image_path)
        mask = self._load_mask(mask_path)

        if self._transform:
            image, mask = self._transform(image, mask)

        return image, mask
