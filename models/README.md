# Models

## Checkpoint in the repo

- `checkpoints/unet_best.pt`: **Run A**. U-Net with a ResNet-34 encoder,
  40-epoch training run, best validation checkpoint at epoch 38, flood threshold
  0.5. Used by the Streamlit app (`src/app.py`) and `src/evaluate_model.py`,
  which load it from `models/checkpoints/` automatically.

**Run B** (60-epoch run with a one-cycle learning-rate schedule, best validation
checkpoint at epoch 51, threshold 0.30 tuned on the validation set) is documented
in its training notebook; its checkpoint is not stored in the repo.

## Training notebooks

- `../notebooks/unet_training_40epoch.ipynb`: Run A.
- `../notebooks/unet_training.ipynb`: Run B.
- `../notebooks/encoder_comparison.ipynb`: ResNet-18, ResNet-34 and
  EfficientNet-B2 encoders, three seeds each.
