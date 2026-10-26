# Pipeline flowchart: notes

Notes to accompany `pipeline_flowchart.drawio.png` (a PNG that also contains the editable draw.io diagram: open it in draw.io to edit). The figure keeps box text short; this file records the method detail behind each box and the shared numbers.

## How to read the figure

- **Two lanes.** Blue = model development on Cyclone Gabrielle (Hawke's Bay). Green = testing the trained model on new events (Cyclone Idai and three NZ cyclones). The new events were never used for training.
- **Seven phases** run top to bottom: research and planning, data collection, data processing, model training, model refining, model validation, product.
- **Bold outlines** mark the two independent accuracy tests (Gabrielle vs HBRC; Idai vs WFP/HDX). The "Test patches" box is a check that the model learned the labelling rule, not an accuracy measure.

---

## Box-by-box detail

### 1. Research and planning

| Box | Detail |
|---|---|
| Literature review | Problem context (cloud cover, NZDF disaster response), SAR flood mapping, U-Net. See `docs/literature-review.md`. |
| Event and data search | Global events and NZ cyclones with suitable Sentinel-1 coverage in Google Earth Engine. A large global training dataset (Kuro Siwo) was considered first but not used: at around 700 GB it was too large to download and train on with the time and computing available. |

### 2. Data collection

| Box | Detail |
|---|---|
| Gabrielle radar | Sentinel-1 GRD, IW mode, VV + VH, relative orbit 81 (ascending). Before 21 Jan 2023, after 14 Feb 2023 07:07 UTC (about 8 pm NZDT). Area 176.60–177.10°E, 39.00–39.60°S (Napier / Esk Valley). Exported at 10 m, EPSG:32760. Orbit 81 was chosen because orbit 73 covered only about 10% of the area. (`notebooks/data_collection.ipynb`) |
| JRC water | JRC Global Surface Water v1.4, occurrence band. Pixels water more than 80% of the time = permanent water. |
| Idai radar | Sentinel-1, before 18 Feb 2019, after 20 Mar 2019, Beira, Mozambique; clipped to where both scenes overlap; EPSG:3857, 10 m. (`docs/idai_gee_export.js`) An earlier 7 → 19 Mar stack and a 14 → 19 Mar pair were side experiments, not used for the reported results. |
| NZ radar | Dovi (Wairarapa, 1 → 13 Feb 2022), Ruby (East Cape, 3 → 15 Dec 2021), Gretel (Northland, 7 → 19 Mar 2020) (`notebooks/nz_external_testing.ipynb`; results in `docs/nz-external-test-results.md`). Cyclone Hale (Hawke's Bay, 8 → 20 Jan 2023) was also exported but is not reported: its after image is about 9 days after the storm (group decision, 26 Oct). |

Full data references (APA 7): `docs/data-sources.md`.

### 3. Data processing

| Box | Detail |
|---|---|
| Speckle filter | 30 m circular focal mean, applied in Earth Engine before export. |
| Rule labels (proxy) | Flooded where post-event VV minus pre-event VV is below −3.5 dB, outside JRC permanent water. About 1.4% of pixels are flooded. These are proxy labels computed from the model's own inputs, not ground truth. |
| Patches, split, normalise | 893 patches of 256 × 256 pixels. Whole 512-pixel spatial blocks are assigned to one split so neighbouring patches cannot leak between sets: 623 train / 141 validation / 129 test (73 / 16 / 15 blocks). Each band standardised with training-set statistics (dB): pre VV −13.72 ± 5.07; pre VH −19.91 ± 6.18; post VV −12.30 ± 5.73; post VH −18.26 ± 6.93. (`notebooks/data_preprocessing.ipynb`) |
| Same pre-processing | New events get the same 30 m focal mean and are normalised with the **Gabrielle** training statistics, so the model sees inputs on the same scale as in training. |

### 4. Model training

| Box | Detail |
|---|---|
| U-Net, ResNet-34 | `segmentation_models_pytorch` U-Net with a ResNet-34 encoder pre-trained on ImageNet (24.4 M parameters). Inputs: pre VV, pre VH, post VV, post VH. Output: flood probability per pixel. Loss: binary cross-entropy + Dice. |
| Run A: 40 epochs | Best validation checkpoint at epoch 38; flood if probability > 0.5. This is the checkpoint committed in the repo (`models/checkpoints/unet_best.pt`) and used by the app. |

### 5. Model refining

| Box | Detail |
|---|---|
| Run B: 60 epochs | Same setup plus a one-cycle learning-rate schedule. Best validation checkpoint at epoch 51; threshold 0.30, tuned on the validation set (the IoU curve is flat between 0.20 and 0.50). (`notebooks/unet_training.ipynb`) |
| Encoder comparison *(not in the figure)* | ResNet-18, ResNet-34 and EfficientNet-B2, three seeds each, 60 epochs. Test IoU against rule labels: 0.952–0.956 across the three encoders. (`notebooks/encoder_comparison.ipynb`) |

### 6. Model validation

| Box | Detail |
|---|---|
| Test patches (rule check) | The 129 held-out Gabrielle test patches scored against the rule labels. Run A IoU 0.927; Run B IoU 0.947. Baselines on the same patches: the rule without the JRC water mask (IoU 0.570) and an Otsu threshold on post-event VV (IoU 0.050). Measures agreement with the rule labels, not flood-mapping accuracy. |
| HBRC | Hawke's Bay Regional Council Cyclone Gabrielle flood extent: maximum extent over 13–15 Feb 2023 from photos, video, satellite imagery, building inspections and ground contours. Independent of the radar labels. |
| Full scene vs HBRC | Whole-scene prediction with 50% overlapping tiles (blended), scored over all valid pixels. Run B: IoU 0.23, precision 0.93, recall 0.24, F1 0.38; the rule alone: IoU 0.231. (`notebooks/nzdf_flood_product.ipynb`, `docs/Results & Findings Summary.md`) **Run B only** so far: a Run A run depends on the HBRC reference file being available (see below). |
| Apply trained models | Models applied to the new events without retraining. Idai: both runs. NZ cyclones: Run A only. |
| Align map | `src/align_reference.py` puts the WFP/HDX map (about 95 m) on the exact Sentinel-1 grid. Unmapped areas are treated as not flooded. |
| WFP/HDX map | WFP satellite-detected waters for Idai: maximum extent 12–21 Mar 2019, itself derived from Sentinel-1. Includes permanent water. |
| Idai test | 203 non-overlapping tiles, metrics pooled over all valid pixels (`src/evaluate_model.py`). Run A: IoU 0.366, F1 0.535, P 0.580, R 0.497. Run B: IoU 0.353, F1 0.522, P 0.558, R 0.490. Hit / false-alarm / miss map: `src/make_idai_error_map.py`. The shared numbers use pooled metrics, not the per-patch mean (patches with no flooding score IoU 1 but precision and recall 0). |
| NZ cyclones (area only) | No reference flood maps exist, so only the share of the area flagged as flooded is reported (Run A): Dovi 0.48%, Ruby 0.31%, Gretel 4.41%. Run A only; Run B was not run on the NZ cyclones. |

### 7. Product

| Box | Detail |
|---|---|
| LINZ roads | NZ Road Centrelines (Topo, 1:50k), LINZ Data Service layer 50329. |
| Roads product | Flood polygons from the full-scene prediction (polygons under 1,000 m² dropped as speckle) overlaid on the roads: 96 road features, 16.3 km under water (Run B). Output in NZTM2000 for QGIS. |
| Streamlit app | `src/app.py`. Upload a four-band before/after GeoTIFF (pre VV, pre VH, post VV, post VH, same pre-processing) and get the flood map, probability map and flooded-area statistics. Uses the **Run A** checkpoint; threshold adjustable with a slider. A demo video was recorded. |

---

## Not shown in the figure

- **Encoder comparison:** see section 5 above.
- **Copernicus EMS EMSR348:** the first Idai reference downloaded (AOI03 Beira). The evaluation used the WFP/HDX map instead. EMSR348 is supplied as vector layers that needed more complex processing, area-of-interest selection and alignment, and one of the two planned areas (AOI16 Beira North) had no flood-delineation product. The WFP/HDX detected-water raster was easier to reproduce and align directly with the Sentinel-1 GeoTIFF. This was a practical data-processing decision, not a judgement that WFP/HDX is more accurate.
- **Tile seams:** the app, Idai test and NZ tests use non-overlapping 256-pixel tiles, which can leave a visible grid. Only the Gabrielle full-scene run blends overlapping tiles.

## Not implemented

- Sea / permanent-water mask at prediction time
- Overlapping tiles in the app and the new-event tests
- Calibrated confidence / uncertainty output
- Training labels independent of the VV-change rule
- SAR vs optical comparison under cloud

## Shared numbers (26 Oct 2026)

Pending items (update this file when they arrive):
- **HBRC with Run A:** depends on the HBRC reference file being available. If not, HBRC remains Run B only.

| Test | Run A (epoch 38, t = 0.5) | Run B (epoch 51, t = 0.30) |
|---|---|---|
| Gabrielle test patches vs rule labels | IoU 0.927 | IoU 0.947 |
| Gabrielle full scene vs HBRC | pending (needs HBRC file) | IoU 0.23, P 0.93, R 0.24, F1 0.38 |
| Idai vs WFP/HDX (pooled) | IoU 0.366, F1 0.535, P 0.580, R 0.497 | IoU 0.353, F1 0.522, P 0.558, R 0.490 |
| NZ cyclones (flagged area) | Dovi 0.48%, Ruby 0.31%, Gretel 4.41% | not run |

Update this table when the reruns are in.
