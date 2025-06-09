from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from utils.logging import get_library_logger

logger = get_library_logger(__name__)


class SegmentationBenchmark:
    """Class for evaluating segmentation performance between prediction and ground truth masks."""

    def __init__(self, pred_folder: str | Path, gt_folder: str | Path, threshold: float = 0.5):
        """Initialize with prediction and ground truth folders.

        Args:
            pred_folder: Folder containing prediction masks
            gt_folder: Folder containing ground truth masks
        """
        self.pred_folder = Path(pred_folder)
        self.gt_folder = Path(gt_folder)

        self._threshold = threshold

        # Verify folders exist
        if not self.pred_folder.exists():
            raise ValueError(f"Prediction folder does not exist: {self.pred_folder}")
        if not self.gt_folder.exists():
            raise ValueError(f"Ground truth folder does not exist: {self.gt_folder}")

    def _load_image(self, path: Path, image_size: tuple[int, int] | None = None) -> np.ndarray:
        """Load image and convert to binary mask."""
        img = Image.open(path)
        if image_size:
            img = img.resize(image_size)
        return np.array(img) > self._threshold

    def calculate_metrics(self) -> pd.DataFrame:
        """Calculate IoU and Dice metrics for each image pair.

        Returns:
            DataFrame with columns: filename, iou, dice
        """
        results = []

        # Get all images in prediction folder
        pred_files = list(self.pred_folder.glob("*.png"))
        pred_files.extend(self.pred_folder.glob("*.bmp"))
        pred_files.extend(self.pred_folder.glob("*.tif"))

        logger.debug(f"Found {len(pred_files)} prediction files in {self.pred_folder}")

        for pred_path in pred_files:
            # Find ground truth file by matching base name (stem)
            gt_candidates = list(self.gt_folder.glob(f"{pred_path.stem}.*"))
            if not gt_candidates:
                logger.debug(f"Ground truth file does not exist for {pred_path.name}, skipping")
                continue
            gt_path = gt_candidates[0]

            # Load images
            pred_mask = self._load_image(pred_path)
            gt_mask = self._load_image(gt_path, image_size=pred_mask.shape[:2])

            results.append(self._calculate_single_pair(pred_mask, gt_mask, pred_path.name))

        return pd.DataFrame(results)

    def _calculate_single_pair(
        self, pred_mask: np.ndarray, gt_mask: np.ndarray, filename: str | None = None
    ) -> dict:
        """Calculate metrics for a single prediction-ground truth pair."""
        intersection = np.logical_and(pred_mask, gt_mask).sum()
        union = np.logical_or(pred_mask, gt_mask).sum()

        iou = intersection / union if union > 0 else 0
        dice = (
            2 * intersection / (pred_mask.sum() + gt_mask.sum())
            if (pred_mask.sum() + gt_mask.sum()) > 0
            else 0
        )

        result = {"iou": float(iou), "dice": float(dice)}
        if filename is not None:
            result["filename"] = filename
        return result

    @staticmethod
    def calculate_metrics_from_lists(
        pred_masks: list, gt_masks: list, filenames: list | None = None
    ) -> pd.DataFrame:
        """Calculate IoU and Dice metrics from lists of images.

        Args:
            pred_masks: List of prediction masks as numpy arrays
            gt_masks: List of ground truth masks as numpy arrays
            filenames: Optional list of filenames for reference

        Returns:
            DataFrame with columns: [filename (optional),] iou, dice
        """
        if len(pred_masks) != len(gt_masks):
            raise ValueError("Prediction and ground truth lists must have the same length")
        if filenames is not None and len(filenames) != len(pred_masks):
            raise ValueError("Filenames list must have the same length as masks")

        results = []
        for idx, (pred, gt) in enumerate(zip(pred_masks, gt_masks)):
            pred_mask = np.array(pred) > 0
            gt_mask = np.array(gt) > 0

            filename = filenames[idx] if filenames is not None else None
            results.append(
                SegmentationBenchmark._calculate_single_pair(None, pred_mask, gt_mask, filename)
            )

        return pd.DataFrame(results)
