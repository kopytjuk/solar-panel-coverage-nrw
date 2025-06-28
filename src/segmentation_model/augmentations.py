import albumentations as A

train_augmentation_basic = A.Compose(
    [
        # A.Resize(256, 256, p=0.5),
        # Horizontal/Vertical Flips
        A.SquareSymmetry(p=0.5),
        A.RandomBrightnessContrast(p=0.3),
        A.GaussNoise(std_range=(0.1, 0.2), p=0.2),
        A.MedianBlur(blur_limit=3, p=0.2),
        # --- Framework-specific steps ---
        # Convert image and mask to PyTorch tensors
        A.ToTensorV2(),
    ]
)
