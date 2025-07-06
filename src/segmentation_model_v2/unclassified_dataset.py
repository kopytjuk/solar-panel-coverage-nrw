from pathlib import Path

import torch
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset


class UnclassifiedDataset(Dataset):
    def __init__(
        self,
        image_files: list[Path],
        *,
        resize_shape: tuple[int, int] = (256, 256),
    ):
        """
        Args:
            data (list): List of tuples containing image and mask paths.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        # self._root_folder = Path(root_dir)

        self._samples_list = image_files
        self._resize_shape = resize_shape

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

    def __len__(self):
        return len(self._samples_list)

    def __getitem__(self, idx) -> torch.Tensor:
        image_path = self._samples_list[idx]

        image = self.load_image(image_path, self._resize_shape)
        return image

    @classmethod
    def from_folder(
        cls, folder_path: str | Path, resize_shape: tuple[int, int] = (256, 256)
    ) -> "UnclassifiedDataset":
        """Create a dataset from a folder containing images."""
        folder_path = Path(folder_path)

        image_files = list(folder_path.rglob("*.[pjb][pnmi][gfp]*"))
        image_files = [
            f
            for f in image_files
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        ]

        return cls(image_files=image_files, resize_shape=resize_shape)
