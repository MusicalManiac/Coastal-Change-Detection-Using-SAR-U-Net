# Data Collection & Preprocessing Summary

Oct 7, 2026 · @Sebastian

## Overview

The training dataset is now 893 patches (256 × 256 px, 10 m, 4 input channels) from a pre/post Cyclone Gabrielle Sentinel-1 pair over Hawke's Bay, split 623 / 141 / 129 into train / val / test. About 1.4% of pixels are labelled flooded in each split.

This replaces the first version described here on 5 October (1,632 patches). That version was built from a broken export and should not be used.

Two notebooks in `data/` produce the dataset:

1. `data_collection.ipynb` queries Google Earth Engine, builds a 6-band GeoTIFF and downloads it: `CycloneGabrielle_HawkesBay_S1_Stack_v2.tif`.
2. `data_preprocessing.ipynb` tiles that GeoTIFF into normalised `.npy` patches under `dataset_patches/{train,val,test}/`.

Neither the GeoTIFF nor the patches are committed. Each teammate regenerates them by running the notebooks.

## What changed since the first version

| Problem in the first version | Fix |
| --- | --- |
| Only about 10% of the area had radar data; Napier and the Esk Valley were empty. Orbit 73 only clips the western edge. | Switched to relative orbit 81, which covers 100% of the area on both dates. |
| The flood label was nodata over almost all land, because the JRC water layer has gaps where water was never seen. | Gaps are filled as "not permanent water" before the label is computed. |
| Nodata is stored as −inf, which the NaN check missed; 1,537 of 1,632 patches contained −inf. | Preprocessing keeps only patches where every pixel is finite. |
| Overlapping patches were split at random, so test pixels also appeared in training. | Whole spatial blocks are assigned to one split; no patch crosses a block edge. |
| `vv_diff`, which the label is thresholded from, was an input channel. | Dropped from the inputs (4 channels remain). |
| No normalisation; masks stored as float32. | Channels standardised with train-set statistics; masks stored as uint8. |

## Data collection (`data_collection.ipynb`)

The notebook pulls one Sentinel-1 pass from before Cyclone Gabrielle and one from during the flooding, then exports both with a baseline flood mask as a single GeoTIFF. The export is 99.7% valid pixels in every band.

| Setting | Value |
| --- | --- |
| Source | Earth Engine `COPERNICUS/S1_GRD` |
| Mode / orbit | IW, VV + VH, relative orbit 81 (ascending) |
| Area of interest | Bounding box 176.60–177.10°E, 39.00–39.60°S (Napier / Esk Valley) |
| Pre-event pass | 2023-01-21 07:07 UTC, 2 slices combined |
| Post-event pass | 2023-02-14 07:07 UTC (about 8 pm NZ time, during peak flooding), 2 slices combined |
| Speckle filter | 30 m circular focal mean |
| Output grid | EPSG:32760 (UTM 60S), 10 m, 4,330 × 6,667 px, float32, nodata = −inf |

Processing steps:

1. Combine all slices from each pass and print each date's coverage of the area. Both are 100%; the notebook warns below 95%.
2. Smooth VV and VH for both dates with the 30 m focal mean.
3. Compute `vv_diff` = post VV − pre VV (dB).
4. Mask out permanent water: JRC Global Surface Water occurrence > 80%, with gaps in that layer treated as not water.
5. Label a pixel flooded where `vv_diff` < −3.5 dB outside permanent water. This is `baseline_mask`; about 1.4% of the scene is flooded.
6. Download with `geemap.download_ee_image`, which tiles the request to get around Earth Engine's 48 MB direct-download limit.
7. Print the percentage of valid pixels in each band as a check on the download.

A visual check of the labels shows flooding on the plains around and south of Napier and along river channels, and none in the open bay.

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

The notebook cuts the GeoTIFF into 893 normalised 256 × 256 patches and assigns them to train, val and test by spatial block, so no pixel appears in two splits.

1. Read bands 1–4 (`pre_vv`, `pre_vh`, `post_vv`, `post_vh`) as inputs and band 6 as the label. `vv_diff` is not used as an input.
2. Mark valid pixels: finite in every band (nodata is −inf).
3. Cut the scene into 512 px blocks. Inside each block, slide a 256 × 256 window with stride 128 and keep only patches where every pixel is valid.
4. Assign whole blocks to splits. The notebook tries 20,000 seeded random assignments and keeps the one whose share of patches and of flooded pixels is closest to 70 / 15 / 15.
5. Standardise each channel with the mean and standard deviation of the training pixels.
6. Save to `dataset_patches/<split>/images/patch_NNNN.npy` (float32, shape 4 × 256 × 256) and `dataset_patches/<split>/masks/patch_NNNN.npy` (uint8, shape 256 × 256).
7. Write `dataset_patches/dataset_info.json` with the settings, normalisation statistics and block assignment.

| Split | Patches | Blocks | Flooded pixels |
| --- | --- | --- | --- |
| Train | 623 | 73 | 1.47% |
| Validation | 141 | 16 | 1.36% |
| Test | 129 | 15 | 1.46% |

Normalisation statistics (training pixels, dB). Apply the same values to any new scene at inference time.

| Channel | Mean | Std |
| --- | --- | --- |
| `pre_vv` | −13.72 | 5.07 |
| `pre_vh` | −19.91 | 6.18 |
| `post_vv` | −12.30 | 5.73 |
| `post_vh` | −18.26 | 6.93 |

## How to run it

Both notebooks run from VS Code connected to a Google Colab runtime, so all files live on the Colab VM until you copy them off.

1. Run the install cell: `pip install earthengine-api geemap geedim`. `geedim` is required by the tiled download.
2. In the init cell, set `project=` to your own Earth Engine Cloud project ID, then authenticate when prompted.
3. Run `data_collection.ipynb`. Before the download, check both "AOI coverage" lines are 95% or higher with no warning. After it, check every band is about 99.7% valid.
4. Run `data_preprocessing.ipynb` on the same runtime. Check the three splits have similar "% flooded pixels".

Things that tripped us up:

- **Files vanish when the runtime resets.** The Colab disk starts empty each session, so the GeoTIFF and patches must be regenerated or re-uploaded.
- **`files.upload()` and `files.download()` don't work from VS Code.** They need the Colab web page. Use the Colab extension instead: right-click a local file → **Upload to Colab**, or run **Colab: Download...** from the Command Palette.
- **The extension can't download files over about 500 MB.** It fails with "Cannot create a string longer than 0x1fffffe8 characters". Split the file on Colab with `split -b 200m`, download the parts, and join them locally with `cat`.
- **Trust the "AOI coverage" lines, not the pass-listing table.** The extra cell that lists every pass by orbit overstates coverage unless its `unmask(0)` is changed to `unmask(0, False)`.
- **Not every orbit covers the area.** Orbit 73 looked fine by date but only covers about 10% of it. If you change the area or dates, re-check coverage first.
- **`ee_export_image` fails on this stack.** It is over Earth Engine's 48 MB direct-download limit; `download_ee_image` tiles around it.

## Known limitations and next steps

The split and normalisation problems are fixed, but the labels are still derived from the inputs. Until that changes, a high U-Net score does not show the model detects real flooding.

| Issue | Why it matters | Suggested fix |
| --- | --- | --- |
| Label is computed from an input band | `baseline_mask` is a −3.5 dB threshold on post VV − pre VV, and both are inputs. Dropping `vv_diff` from the inputs does not stop the model rebuilding it, so it can learn the threshold rather than flooding. | Use flood labels from an independent source. |
| Labels are a threshold proxy | −3.5 dB is a heuristic; there is no ground truth yet. | Check against an independent flood extent map for Gabrielle. |
| One event, one scene pair | 893 patches from one place and date limits how well the model generalises. | Add more dates, tracks or events. |
| `vh_diff` not exported | The VH change is computed in the collection notebook but not saved. | Decide whether the model needs it; it can also be rebuilt from the VH inputs. |
| Class imbalance | Only about 1.4% of pixels are flooded, so predicting "no flood" everywhere scores about 98.6% accuracy. | Use Dice or focal loss, or class weights. Report flood IoU, precision and recall, not accuracy. |
| Flooding continues past the southern edge | The scene cuts off flooded land south of Napier, and flooded pixels are what the dataset is shortest of. | Move the southern boundary from 39.60°S to about 39.75°S and re-export. |
| Open-sea patches | About a fifth of the scene is open bay, which adds many patches with no flooding. | Drop patches that are entirely permanent water. |
| 24-day gap before the event | The pre-event image is from 21 January, so some backscatter change may come from land or soil-moisture change rather than flooding. | If labels look noisy, compare with orbit 175 or 8, which have 12-day pairs but a post-event image a week after the peak. |
