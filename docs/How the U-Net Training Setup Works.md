# How the U-Net Training Setup Works

Oct 8, 2026 · @Sebastian

## Overview

`models/unet_training.ipynb` trains a U-Net to mark flooded pixels in Sentinel-1 radar patches, then scores it on a held-out test set. It is Phase 4 of the project and runs after `data/data_preprocessing.ipynb`, which produces the patches it reads.

The notebook does five things in order:

1. Loads the patch dataset and the settings the preprocessing notebook recorded.
2. Builds a U-Net whose encoder starts from ImageNet weights.
3. Trains for 40 epochs, saving the model each time validation IoU improves.
4. Reloads the best saved model and scores it once on the test split.
5. Saves training curves and example predictions as images.

The last recorded run reached a test flood IoU of 0.927. Read the caveat under Evaluation before quoting that number: it measures how well the model copies a threshold rule, not how well it finds real flooding.

## Data inputs

The notebook reads 893 ready-made patches from `dataset_patches/`; it does no preprocessing of its own. Each patch is a pair of `.npy` files with the same name, one under `images/` and one under `masks/`.

|  | Image | Mask |
| --- | --- | --- |
| Shape | 4 × 256 × 256 | 256 × 256 |
| Type | float32, already normalised | uint8, 1 = flooded, 0 = not |
| Contents | `pre_vv`, `pre_vh`, `post_vv`, `post_vh` | `baseline_mask` |

The four image channels are Sentinel-1 backscatter in two polarisations (VV and VH), before and after the event. At 10 m per pixel, one patch covers 2.56 km × 2.56 km. The source scene is `CycloneGabrielle_HawkesBay_S1_Stack_v2.tif`.

### Splits

| Split | Patches | Blocks | Flooded pixels |
| --- | --- | --- | --- |
| Train | 623 | 73 | 1.47% |
| Val | 141 | 16 | 1.36% |
| Test | 129 | 15 | 1.46% |

The splits are fixed by the preprocessing notebook, not by this one. Three choices made there matter for training:

- **Splits are spatial.** The scene is cut into 512-pixel blocks and whole blocks go to one split. Patches overlap by 50%, so splitting patch by patch would put near-copies in both train and test.
- **Flooding is balanced across splits.** Block assignment was picked so each split holds a similar share of flooded pixels.
- **Normalisation uses training pixels only.** Each channel has its training mean subtracted and is divided by its training standard deviation. The values are stored in `dataset_info.json`.

The notebook reads `dataset_info.json` at start-up to get the channel names, so the model's input size follows the dataset rather than being hard-coded.

### Augmentation

Training patches are randomly flipped left-right, flipped up-down, and rotated by a multiple of 90 degrees. The same transform is applied to the image and its mask. Validation and test patches are never augmented.

## Model architecture

The model is a U-Net with a ResNet-34 encoder, built in one call to the `segmentation-models-pytorch` library (`smp.Unet`). It has 24.4 million parameters, takes a 4-channel patch, and returns one number per pixel.

&#91;embedded content: U-Net with ResNet-34 encoder · 5 steps down, 5 steps up, 4 skip connections\]

Read it down the left side and up the right. The fifth decoder step and the output layer are drawn as one box, and the full-size input has no skip connection.

A U-Net has two halves joined by skip connections:

- **Encoder (ResNet-34).** Shrinks the patch in five steps, from 256 × 256 down to 8 × 8, while building up richer features. This half learns what is in the patch.
- **Decoder.** Grows the 8 × 8 features back to 256 × 256 in five steps. This half works out where each thing is.
- **Skip connections.** At each step the decoder also receives the encoder's features from the matching resolution. They carry the fine detail that shrinking throws away, which is what keeps flood edges sharp.

Two details are specific to this setup:

- **Pre-trained encoder.** The encoder starts from ImageNet weights instead of random ones, which helps with only 623 training patches. ImageNet images have 3 channels and these patches have 4, so the library adapts the first layer to fit. The decoder starts from random weights.
- **Output is a logit, not a probability.** The model returns one raw score per pixel. Applying a sigmoid turns it into a flood probability, and a pixel is called flooded when that probability is above 0.5.

The whole network is trained; nothing is frozen.

## Training configuration

All settings are constants at the top of the notebook's configuration cell, so changing a run means editing one place.

| Setting | Value | What it controls |
| --- | --- | --- |
| `ENCODER` | `resnet34` | Which backbone the U-Net uses |
| `ENCODER_WEIGHTS` | `imagenet` | Starting weights for the encoder |
| `BATCH_SIZE` | 16 | Patches per training step |
| `EPOCHS` | 40 | Full passes over the training set |
| `LEARNING_RATE` | 1e-4 | Step size for the optimizer |
| `WEIGHT_DECAY` | 1e-4 | Regularisation strength |
| `THRESHOLD` | 0.5 | Probability above which a pixel counts as flooded |
| `NUM_WORKERS` | 2 | Background processes loading patches |
| `SEED` | 42 | Seed for Python, NumPy and PyTorch |

### Loss

The loss is binary cross-entropy plus Dice loss, added with equal weight. Both are computed from the raw logits.

- **Binary cross-entropy** scores every pixel on its own. It gives a steady training signal but is dominated by the 98.6% of pixels that are not flooded.
- **Dice loss** scores the overlap between predicted and true flood areas. It ignores the easy background pixels, so it keeps the model from predicting "not flooded" everywhere.

### Optimizer

The optimizer is AdamW with a fixed learning rate. There is no learning-rate schedule and no early stopping; every run does all 40 epochs.

On a GPU the forward pass uses mixed precision, which is faster and uses less memory. The loss is still computed in full precision.

### What happens each epoch

1. One pass over the training set with augmentation, updating the weights.
2. One pass over the validation set with no weight updates.
3. If validation IoU beat the previous best, the model is saved to `unet_best.pt`, overwriting the last save.
4. One line is printed with train loss and IoU, and validation loss, IoU, precision and recall.

The saved model is therefore the best one by validation IoU, not the one from the final epoch.

### Metrics

All four metrics describe the flooded class only. Accuracy is not reported, because a model that never predicts flooding would already score about 98.6%.

| Metric | Question it answers |
| --- | --- |
| IoU | Of all pixels that are flooded in the prediction or the label, what share is flooded in both? |
| Precision | Of the pixels predicted flooded, what share really are? |
| Recall | Of the truly flooded pixels, what share did the model find? |
| F1 | A single score balancing precision and recall |

Pixel counts are added up over the whole split before the metrics are calculated. This avoids the distortion of averaging per-batch scores when many batches contain almost no flooding.

## Evaluation and outputs

The test set is scored once, after training, using the best saved model rather than the final one. In the last recorded run that was the model from epoch 38, with a validation IoU of 0.897.

| Test metric | Value |
| --- | --- |
| Flood IoU | 0.927 |
| Precision | 0.955 |
| Recall | 0.969 |
| F1 | 0.962 |

Validation IoU climbed from 0.045 at epoch 1 to 0.897 at epoch 38. Validation loss was still falling at epoch 40, so a longer run might improve on this.

### What the score does and does not show

A high IoU here shows the U-Net can reproduce the labelling rule, not that it detects real flooding.

The labels (`baseline_mask`) are not hand-drawn or surveyed. They come from a rule: a pixel is flooded if its VV backscatter dropped by more than 3.5 dB between the before and after images. The model is given both of those images as input, so it can work the rule out for itself.

Proving the model finds real floods needs labels made independently of the radar inputs. Until then, treat these numbers as a check that the training pipeline works.

### Files the notebook saves

| File | Contents |
| --- | --- |
| `unet_best.pt` | Best model weights, plus the encoder name, channel names, normalisation values, threshold, epoch and validation IoU |
| `training_curves.png` | Loss and flood IoU per epoch, train against validation |
| `test_predictions.png` | The 4 most-flooded test patches: after-event VV image, label, and prediction side by side |

The checkpoint carries the normalisation values on purpose. Anyone running the model on a new scene must normalise it with these same values, and can read them straight from the file.

## How to run it

The notebook is written for Google Colab and runs top to bottom with no manual steps between cells.

1. Open `models/unet_training.ipynb` in Colab and switch to a GPU runtime (Runtime > Change runtime type > GPU).
2. Get `dataset_patches/` onto the runtime. Either run `data/data_preprocessing.ipynb` in the same session or upload the folder. It must contain `train/`, `val/`, `test/` and `dataset_info.json`.
3. Run all cells. The first one installs `segmentation-models-pytorch`.
4. Download `unet_best.pt` and the two PNGs when it finishes.

### Things to watch out for

- **Outputs live on the Colab disk.** They are lost when the runtime resets, and none of them are in the repository. Download them before closing the session.
- **It runs on CPU, but slowly.** The notebook picks the GPU automatically when one is available and prints which device it is using.
- **A missing dataset fails early.** If a split folder is empty, the notebook stops with a message telling you to run the preprocessing notebook first.
- **The `HF_TOKEN` warning is harmless.** The pre-trained weights download from the Hugging Face Hub without a token.
- **Re-running preprocessing replaces the dataset.** It deletes `dataset_patches/` and rebuilds it. With the same seed and source file the splits come out the same.
- **Changing the input channels needs no edit here.** The channel count is read from `dataset_info.json`, so the change is made in the preprocessing notebook.
