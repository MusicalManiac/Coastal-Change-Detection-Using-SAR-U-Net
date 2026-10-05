# Data Collection & Preprocessing Summary

Oct 5, 2026 · @Sebastian

## Overview

We now have a first training dataset: 1,632 patches (256 × 256 px, 10 m) cut from a pre/post Cyclone Gabrielle Sentinel-1 pair over Hawke's Bay, split 1,142 / 245 / 245 into train / val / test.

Two notebooks in `data/` produce it:

1. `data_collection.ipynb` queries Google Earth Engine, builds a 6-band GeoTIFF and downloads it: `CycloneGabrielle_HawkesBay_S1_Stack.tif` (73 MB).
2. `data_preprocessing.ipynb` tiles that GeoTIFF into `.npy` patches under `dataset_patches/` (2.4 GB) and splits them.

Neither the GeoTIFF nor the patches are committed; both are in `.gitignore`. Each teammate regenerates them by running the notebooks.

## Data collection (`data_collection.ipynb`)

The notebook pulls one Sentinel-1 image from before Cyclone Gabrielle and one from after it, then exports both with a baseline flood mask as a single GeoTIFF.

| Setting | Value |
| --- | --- |
| Source | Earth Engine `COPERNICUS/S1_GRD` |
| Mode / pass | IW, descending, VV + VH |
| Area of interest | Bounding box 176.60–177.10°E, 39.00–39.60°S (Napier / Esk Valley) |
| Pre-event scene | 2023-02-01 17:30 UTC |
| Post-event scene | 2023-02-13 17:30 UTC |
| Speckle filter | 30 m circular focal mean |
| Output grid | EPSG:32760 (UTM 60S), 10 m, 4,330 × 6,667 px, float32 |

Processing steps:

1. Smooth VV and VH for both dates with the 30 m focal mean.
2. Compute `vv_diff` = post VV − pre VV (dB).
3. Mask out permanent water: JRC Global Surface Water occurrence > 80%.
4. Label a pixel flooded where `vv_diff` < −3.5 dB on non-permanent-water land. This is `baseline_mask`.
5. Download with `geemap.download_ee_image`, which tiles the request (252 tiles) to get around Earth Engine's 48 MB direct-download limit.

Bands in the GeoTIFF:

| Band | Name | Content |
| --- | --- | --- |
| 1 | `pre_vv` | Pre-event VV backscatter, smoothed (dB) |
| 2 | `pre_vh` | Pre-event VH backscatter, smoothed (dB) |
| 3 | `post_vv` | Post-event VV backscatter, smoothed (dB) |
| 4 | `post_vh` | Post-event VH backscatter, smoothed (dB) |
| 5 | `vv_diff` | Post VV − pre VV (dB) |
| 6 | `baseline_mask` | 1 = flooded, 0 = not (stored as float32) |

## Preprocessing (`data_preprocessing.ipynb`)

The notebook cuts the GeoTIFF into 1,632 overlapping 256 × 256 patches and splits them 70 / 15 / 15.

1. Read bands 1–5 as the input features and band 6 as the target mask.
2. Slide a 256 × 256 window with stride 128 (50% overlap) over the scene.
3. Skip any patch containing NaN or made entirely of zeros (scene edges).
4. Save each patch as float32 NumPy arrays: `dataset_patches/images/patch_NNNN.npy` with shape (5, 256, 256), and `dataset_patches/masks/patch_NNNN.npy` with shape (256, 256).
5. Split with scikit-learn `train_test_split` (`random_state=42`): 70% train, then the rest halved into validation and test.

| Split | Patches |
| --- | --- |
| Train | 1,142 |
| Validation | 245 |
| Test | 245 |

The split only produces lists of file paths in memory; nothing is moved into split folders yet, and no normalisation is applied.

## How to run it

Both notebooks run from VS Code connected to a Google Colab runtime, so all files live on the Colab VM until you copy them off.

1. Run the install cell: `pip install earthengine-api geemap geedim`. `geedim` is required by the tiled download.
2. In the init cell, replace `project='XX'` with your own Earth Engine Cloud project ID, then authenticate when prompted.
3. Run `data_collection.ipynb`. It takes a few minutes for the 252 tiles; "Connection pool is full" warnings are harmless.
4. Run `data_preprocessing.ipynb` on the same runtime.

Things that tripped us up:

- **Files vanish when the runtime resets.** The Colab disk starts empty each session.
- **`files.upload()` and `files.download()` don't work from VS Code.** They need the Colab web page. Use the Colab extension instead: right-click a local file → **Upload to Colab**, or run **Colab: Download...** from the Command Palette.
- **Check the GeoTIFF is on the runtime before preprocessing.** If you start a new runtime, upload `CycloneGabrielle_HawkesBay_S1_Stack.tif` first, or `rasterio.open` fails with "No such file or directory".
- **The old `geemap.ee_export_image` call fails.** The full stack is about 866 MB uncompressed, over Earth Engine's 48 MB direct-download limit; `download_ee_image` tiles around it.

## Known limitations and next steps

The dataset works end to end, but two issues will make U-Net scores look better than they really are. Fix those before trusting any metrics.

| Issue | Why it matters | Suggested fix |
| --- | --- | --- |
| Label is computed from an input band | `baseline_mask` is just `vv_diff` < −3.5 dB outside permanent water, and `vv_diff` is input channel 5. The model can learn the threshold rather than flooding. | Drop `vv_diff` from the inputs, or use labels from an independent source. |
| Overlapping patches split at random | With 50% overlap, neighbouring patches share pixels across train, val and test, so test scores leak training data. | Split the scene into spatial blocks first, then patch each block. |
| Labels are a threshold proxy | −3.5 dB is a heuristic; there is no ground truth yet. | Check against an independent flood extent map for Gabrielle. |
| One event, one scene pair | 1,632 patches from one place and date limits how well the model generalises. | Add more dates, tracks or events. |
| No normalisation | Inputs are raw dB values. | Standardise per channel using train-set statistics. |
| Storage and unused bands | Masks are stored as float32; `vh_diff` is computed but not exported. | Save masks as uint8; decide whether to add `vh_diff`. |
