import numpy as np
from PIL import Image

from segmentation_benchmark.benchmark import SegmentationBenchmark


def test_segmentation_benchmark(tmp_path):
    # Create test directories
    pred_dir = tmp_path / "pred"
    gt_dir = tmp_path / "gt"
    pred_dir.mkdir()
    gt_dir.mkdir()

    # Create test images
    pred_img = np.zeros((100, 100), dtype=np.uint8)
    pred_img[25:75, 25:75] = 255

    gt_img = np.zeros((100, 100), dtype=np.uint8)
    gt_img[30:80, 30:80] = 255

    Image.fromarray(pred_img).save(pred_dir / "test.png")
    Image.fromarray(gt_img).save(gt_dir / "test.png")

    # Run benchmark
    benchmark = SegmentationBenchmark(pred_dir, gt_dir)
    results = benchmark.calculate_metrics()

    assert len(results) == 1
    assert "filename" in results.columns
    assert "iou" in results.columns
    assert "dice" in results.columns
    assert results.iloc[0]["filename"] == "test.png"
    assert 0 < results.iloc[0]["iou"] < 1
    assert 0 < results.iloc[0]["dice"] < 1
