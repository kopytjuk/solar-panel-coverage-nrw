from typing import Literal

import lightning as pl
import segmentation_models_pytorch as smp
import torch
from torch.optim import lr_scheduler

type StageType = Literal["train", "valid", "test"]


class PvSegmentationModel(pl.LightningModule):
    """Photovoltaic segmentation model based on Unet++ architecture from
    `segmentation_models_pytorch` library."""

    def __init__(
        self,
        encoder_name: str = "resnet34",
        in_channels: int = 3,
        out_classes: int = 1,
        train_encoder: bool = False,
        learning_rate: float = 2e-4,
        **kwargs,
    ):
        super().__init__()
        self.model = smp.UnetPlusPlus(
            encoder_name=encoder_name,
            encoder_weights="imagenet",
            in_channels=in_channels,
            classes=out_classes,
            encoder_freeze=True,
            **kwargs,
        )
        # preprocessing parameteres for image
        params = smp.encoders.get_preprocessing_params(encoder_name)
        self.register_buffer("std", torch.tensor(params["std"]).view(1, 3, 1, 1))
        self.register_buffer("mean", torch.tensor(params["mean"]).view(1, 3, 1, 1))

        # we do not train the encoder by default
        if not train_encoder:
            for param in self.model.encoder.parameters():
                param.requires_grad = False

        # for image segmentation dice loss could be the best first choice
        self.loss_fn = smp.losses.DiceLoss(smp.losses.BINARY_MODE, from_logits=True)

        # initialize step metics
        self.training_step_outputs = []
        self.validation_step_outputs = []
        self.test_step_outputs = []

        # training parameters
        self._learning_rate = learning_rate

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        """Forward pass of the model

        Args:
            image (torch.Tensor): input image(s) in B x C x H x W format.

        Returns:
            torch.Tensor: output segmentation mask in B x 1 x H x W format.
                0...1 probability for a pixel to belong to a solar panel.
        """
        # B x C x H x W
        # normalize wrt. encoder weights here
        image = (image - self.mean) / self.std
        mask = self.model(image)
        return mask

    def training_step(self, batch, batch_idx):
        train_loss_info = self.shared_step(batch, "train")
        # append the metics of each step to the
        self.training_step_outputs.append(train_loss_info)
        return train_loss_info

    def on_train_epoch_end(self):
        self.shared_epoch_end(self.training_step_outputs, "train")
        # empty set output list
        self.training_step_outputs.clear()
        return

    def validation_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx):
        valid_loss_info = self.shared_step(batch, "valid")
        self.validation_step_outputs.append(valid_loss_info)
        return valid_loss_info

    def on_validation_epoch_end(self):
        self.shared_epoch_end(self.validation_step_outputs, "valid")
        self.validation_step_outputs.clear()
        return

    def test_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx):
        test_loss_info = self.shared_step(batch, "test")
        self.test_step_outputs.append(test_loss_info)
        return test_loss_info

    def on_test_epoch_end(self):
        self.shared_epoch_end(self.test_step_outputs, "test")
        # empty set output list
        self.test_step_outputs.clear()
        return

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self._learning_rate)

        T_max = 1000
        scheduler = lr_scheduler.CosineAnnealingLR(optimizer, T_max=T_max, eta_min=1e-5)
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",
                "frequency": 1,
            },
        }

    def shared_step(self, batch: tuple, stage: StageType) -> dict:
        images = batch[0]
        masks = batch[1]

        # Shape of the image should be (batch_size, num_channels, height, width)
        # if you work with grayscale images, expand channels dim to have [batch_size, 1, height, width]
        assert images.ndim == 4, (
            "Images should have 4 dimensions: (batch_size, num_channels, height, width)"
        )
        assert masks.ndim == 4, (
            "Masks should have 4 dimensions: (batch_size, num_classes, height, width)"
        )
        # Check that image dimensions are divisible by 32,
        # encoder and decoder connected by `skip connections` and usually encoder have 5 stages of
        # downsampling by factor 2 (2 ^ 5 = 32); e.g. if we have image with shape 65x65 we will have
        # following shapes of features in encoder and decoder: 84, 42, 21, 10, 5 -> 5, 10, 20, 40, 80
        # and we will get an error trying to concat these features
        h, w = images.shape[2:]
        assert h % 32 == 0 and w % 32 == 0

        # Check that mask values in between 0 and 1, NOT 0 and 255 for binary segmentation
        assert images.max() <= 1.0 and images.min() >= 0, (
            "Image values should be in [0, 1] range. "
        )
        assert masks.max() <= 1.0 and masks.min() >= 0, (
            "Mask values should be in [0, 1] range for binary segmentation. "
        )

        logits_mask = self.forward(images)

        # Predicted mask contains logits, and loss_fn param `from_logits` is set to True
        loss = self.loss_fn(logits_mask, masks)

        # Lets compute metrics for some threshold
        # first convert mask values to probabilities, then
        # apply thresholding
        prob_mask = logits_mask.sigmoid()
        pred_mask = (prob_mask > 0.5).float()

        # We will compute IoU metric by two ways
        #   1. dataset-wise
        #   2. image-wise
        # but for now we just compute true positive, false positive, false negative and
        # true negative 'pixels' for each image and class
        # these values will be aggregated in the end of an epoch
        tp, fp, fn, tn = smp.metrics.get_stats(pred_mask.long(), masks.long(), mode="binary")
        return {
            "loss": loss,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

    def shared_epoch_end(self, outputs, stage: StageType):
        # aggregate step metics
        tp = torch.cat([x["tp"] for x in outputs])
        fp = torch.cat([x["fp"] for x in outputs])
        fn = torch.cat([x["fn"] for x in outputs])
        tn = torch.cat([x["tn"] for x in outputs])

        # per image IoU means that we first calculate IoU score for each image
        # and then compute mean over these scores
        per_image_iou = smp.metrics.iou_score(tp, fp, fn, tn, reduction="micro-imagewise")

        # dataset IoU means that we aggregate intersection and union over whole dataset
        # and then compute IoU score. The difference between dataset_iou and per_image_iou scores
        # in this particular case will not be much, however for dataset
        # with "empty" images (images without target class) a large gap could be observed.
        # Empty images influence a lot on per_image_iou and much less on dataset_iou.
        dataset_iou = smp.metrics.iou_score(tp, fp, fn, tn, reduction="micro")

        # total loss
        loss_list = [x["loss"] for x in outputs]
        epoch_loss = sum(loss_list) / len(loss_list)

        metrics = {
            f"{stage}_per_image_iou": per_image_iou,
            f"{stage}_dataset_iou": dataset_iou,
            f"{stage}_loss": epoch_loss,
        }

        self.log_dict(metrics, prog_bar=True)

    def save_model(self, file_path: str):
        """
        Save the model to the specified path.
        """
        self.model.save_pretrained(file_path)

    def load_model(self, file_path: str):
        """
        Load the model from the specified path.
        """
        self.model = smp.from_pretrained(file_path)
