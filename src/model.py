"""
Loads Sebastian's actual trained model: segmentation_models_pytorch Unet
with a ResNet34 encoder (see unet_training.ipynb, cell 'e52dad07').

Needs: pip install segmentation-models-pytorch
"""

import segmentation_models_pytorch as smp
import torch


def load_checkpoint(checkpoint_path, device="cpu"):
    """Loads unet_best.pt, which is a dict (not raw weights):
        model_state, encoder, in_channels, input_bands, normalisation, threshold, epoch, val_iou
    Returns (model, metadata_dict).
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)

    model = smp.Unet(
        encoder_name=checkpoint["encoder"],
        encoder_weights=None,  # we're loading trained weights, not re-downloading ImageNet
        in_channels=checkpoint["in_channels"],
        classes=1,
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()

    return model, checkpoint
