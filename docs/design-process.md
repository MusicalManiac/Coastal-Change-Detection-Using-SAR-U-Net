# NZDF Sentinel-1 SAR Coastal Flood Detection — Design Process Document

## 1. Project Overview & Stakeholder Need
- **Client:** New Zealand Defence Force (NZDF)
- **Problem Statement:** Operational blindness during extreme storm events due to heavy cloud cover obscuring optical satellites during search and rescue / amphibious landing missions.
- **Proposed Solution:** Automated pipeline pairing Sentinel-1 C-band SAR backscatter with a U-Net segmentation model to map flood boundaries through cloud cover.

---

## 2. Event & Data Availability Matrix

| Event Name | Region | Event Date | Pre-Event S1 Scene | Post-Event S1 Scene | Local Timestamp (NZDT) | Orbit Pass | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cyclone Gabrielle** | Hawke's Bay | Feb 14, 2023 | 2023-01-21 07:07 UTC | 2023-02-14 07:07 UTC | Feb 14, 08:07 PM NZDT | Ascending (relative orbit 81) | **PASS** (Same orbit, 100% AOI coverage, during peak flooding) |
| **Cyclone Idai** | Beira, Mozambique | Mar 14, 2019 | 2019-02-18 16:06 UTC (S1B) | 2019-03-20 16:07 UTC (S1A) | — | Same track (~16:07 UTC passes) | **Test event** (reference: WFP/HDX detected waters, 12–21 Mar 2019) |
| **Cyclone Dovi** | Wairarapa | Feb 2022 | 2022-02-01 | 2022-02-13 | Feb 14, about 06:22 AM NZDT | — | **Exploratory** (no reference map) |
| **Cyclone Ruby** | East Cape | Dec 2021 | 2021-12-03 | 2021-12-15 | Dec 16, about 06:21 AM NZDT | — | **Exploratory** (no reference map) |
| **Cyclone Gretel** | Northland | Mar 2020 | 2020-03-07 | 2020-03-19 | Mar 19, about 08:07 PM NZDT | — | **Exploratory** (no reference map) |
| **Cyclone Hale** | Hawke's Bay | Jan 2023 | 2023-01-08 17:30 UTC | 2023-01-20 17:30 UTC | Jan 21, about 06:30 AM NZDT | Same track | Exported, not reported (after image about 9 days after the storm) |

**Change from original plan (Gabrielle):** the descending pass (relative orbit 73, 1 and 13 Feb) covered only about 91% of the area of interest, so `data_collection.ipynb` uses the ascending pass on relative orbit 81 instead. Each pass is delivered as two GRD slices, which are mosaicked to cover the full area.

---

## 3. Reference (Ground-Truth) Data for Model Evaluation — Cyclone Idai, Beira

**Author:** Rata | **Date:** 5 October 2026 | **Notebook:** `notebooks/idai_reference.ipynb`

> **Update (final evaluation):** the Idai evaluation used the WFP/HDX satellite-detected waters product (`data/idai/reference/`, see `data/idai/README.md`) with the Sentinel-1 pair 18 February → 20 March 2019, instead of EMSR348. The EMSR348 work below is kept as a record of the reference data sourced and considered.

### What it is
To evaluate our U-Net flood predictions, we need an independent map of where flooding actually occurred. We use the flood delineation produced by the Copernicus Emergency Management Service (EMS) for Tropical Cyclone Idai (activation **EMSR348**). EMS analysts produced these maps from satellite imagery during the emergency response to support humanitarian operations. The data is supplied as GIS vector layers (shapefiles), including the observed flood extent, permanent water bodies (hydrography) and the mapped area boundary.

Source: https://mapping.emergency.copernicus.eu/activations/EMSR348/

### Why this dataset
- **Independent:** produced by a separate expert team, not by our model or its training data, so it is a fair test.
- **Authoritative:** an official product used in the real disaster response.
- **Matches our test event:** covers Beira, near where Cyclone Idai made landfall on 14 March 2019 (~23:30 UTC), and is openly available.

### Product choice
EMSR348 includes several products for the Beira area. We selected **AOI03 Beira – Delineation Map v1** as our main reference because it is closest in time to peak flooding.

| Product | Delivered | Use |
|---|---|---|
| AOI03 Delineation Map v1 | 16 Mar 2019 | **Main reference** |
| AOI03 Delineation Monit01 / Monit02 | 8–9 Apr 2019 | Later flood extent as water receded; possible secondary comparison |
| AOI03 Grading Map | 8 Apr 2019 | Building/infrastructure damage only – not used |
| AOI16 Beira North Grading Map | 12 Apr 2019 | Building/infrastructure damage only – not used |

**Source imagery for the main reference:**
- **Post-event image (flood mapped from this):** COSMO-SkyMed © ASI (2019), X-band SAR, acquired **16 March 2019 at 14:41 UTC**, 2.5 m resolution (~1.5 days after landfall).
- **Pre-event (baseline) image:** Sentinel-2B (optical), acquired 2 December 2018 at 07:32 UTC, 10 m resolution, ~0% cloud cover in AOI.

The post-event Sentinel-1 image used for model prediction should be as close to 16 March 2019 as possible, because flood extent changes quickly and a time gap would show up as false model errors.

### Change from original plan
The original plan included flood delineation for AOI16 Beira North. On inspection, **no flood delineation product exists for AOI16**, only a damage grading map. The comparison area is therefore **AOI03 Beira** only.

### Processing
1. Downloaded the vector packages and map PDFs directly from the EMS website in Google Colab (source URLs recorded in the notebook) and saved them to the shared Google Drive (`data/idai/reference/`).
2. Unzipped the packages and loaded the layers with `geopandas`.
3. Exported a single cleaned file, `data/idai/reference_clean/idai_beira_flood_reference.gpkg` (saved to the shared Google Drive, not in the repo), with three layers:
   - `flood` – observed flood extent (1 multi-part feature)
   - `permanent_water` – rivers, lakes and sea (14 features)
   - `aoi` – mapped area boundary (1 feature)
4. Reference layers are in **EPSG:4326** (WGS 84, latitude/longitude). They are reprojected to **UTM zone 36S (EPSG:32736)** for area calculations and for rasterising to the model's 10 m grid.

### How it will be used
- `aoi`: clip the Sentinel-1 imagery to the reference area (Nisheeth).
- `flood` and `permanent_water`: compare against the model's predicted flood map, pixel by pixel, to calculate accuracy metrics and produce a predicted-vs-reference map (Rhett). Permanent water is excluded so that rivers and sea are not counted as correctly detected flooding.

### Limitations
- **Not perfect ground truth:** the reference is an expert interpretation of satellite imagery. It is the best independent reference available, not a field survey.
- **Partial independence:** the reference was also derived from SAR imagery, so it shares some of SAR's blind spots with our model. However, it uses a different satellite and radar band (COSMO-SkyMed X-band vs Sentinel-1 C-band), a much finer resolution (2.5 m vs 10 m) and expert human interpretation, so it remains a reasonable independent benchmark.
- **Hidden water:** satellite flood mapping can miss water under vegetation or between buildings. These areas may appear as model "errors" even when the model is right, or be missed by both.
- **Single snapshot:** the reference shows one moment in time. Any difference between its image date and our Sentinel-1 date adds uncertainty.
- **Resolution mismatch:** the reference was mapped at 2.5 m but the model predicts at 10 m, so small or narrow flooded areas may be below what the model can detect.
- **Rasterisation:** the vector polygons must be converted to a pixel grid matching the model output, which may introduce small errors along flood edges.

### Open questions
- [x] Which Sentinel-1 acquisition over Beira is closest to 16 March 2019? → The evaluation used the 18 February → 20 March 2019 pair, the closest same-track pair whose footprints overlap over Beira.
- [x] Is Cyclone Idai one of the 43 Kuro Siwo training events? → No longer relevant: Kuro Siwo was not used (about 700 GB, too large to download and train on); the model was trained on Cyclone Gabrielle only.

---

## 4. Data Processing Architecture

```
[ Sentinel-1 GRD, Google Earth Engine ] --> [ 30 m speckle smoothing, pre/post VV + VH stack ] --> [ GeoTIFF ]
  notebooks/data_collection.ipynb                                                                     |
                                                                                                      v
[ 256 x 256 patches, spatial block split, train-only normalisation ] <-- notebooks/data_preprocessing.ipynb
        |
        v
[ U-Net training & test scoring ] --> [ Full-scene inference ] --> [ Flood polygons + flooded road segments ]
  notebooks/unet_training.ipynb            notebooks/nzdf_flood_product.ipynb (GeoTIFF, GeoPackage, GeoJSON)
```

| Stage | Notebook | Runs on | Output |
| :--- | :--- | :--- | :--- |
| Data collection | `notebooks/data_collection.ipynb` | Colab | `CycloneGabrielle_HawkesBay_S1_Stack_v2.tif` on Google Drive |
| Preprocessing | `notebooks/data_preprocessing.ipynb` | Colab | `dataset_patches/` on Google Drive (copied to `data/` for training) |
| Data visualisation | `notebooks/data_visualisation.ipynb` | Local | Presentation figures in `notebooks/figures/` |
| Training, Run A (40 epochs) | `notebooks/unet_training_40epoch.ipynb` | Colab GPU | `models/checkpoints/unet_best.pt` (in the repo) |
| Training, Run B (60 epochs) | `notebooks/unet_training.ipynb` | Local GPU | `models/outputs/unet_best.pt` (not in the repo) |
| Encoder comparison | `notebooks/encoder_comparison.ipynb` | Local GPU | `models/outputs/comparison/` |
| NZDF product and HBRC validation | `notebooks/nzdf_flood_product.ipynb` | Local | `models/outputs/nzdf/` |
| Idai evaluation | `src/align_reference.py`, `src/evaluate_model.py`, `src/make_idai_error_map.py` | Local | `outputs/evaluation/` |
| NZ cyclone tests | `notebooks/nz_external_testing.ipynb` | Colab | Prediction previews and run summaries |
| Flood-mapping app | `src/app.py` (Streamlit) | Local | Interactive flood map |

---

## 5. Technical Choices & Rationales

### AI/ML Model Selection
- **Selected Method:** U-Net Convolutional Neural Network
- **Justification:** Preserves sharp boundary edge features (vital for narrow flood channels/coastal margins) and spatial convolutions naturally suppress SAR speckle noise compared to single-pixel thresholding.

### Satellite Platform
- **Selected Sensor:** Sentinel-1 C-band SAR ($\text{VV} + \text{VH}$)
- **Justification:** Active microwave sensor penetrates cloud cover, heavy rain, and operates day/night.

### Training Labels
- **Selected Method:** Pseudo-labels (`baseline_mask`): a pixel is flooded if VV backscatter dropped by more than 3.5 dB between the pre- and post-event images, excluding permanent water (JRC Global Surface Water occurrence > 80%).
- **Justification:** No pixel-level ground truth exists for Gabrielle at the Sentinel-1 acquisition time, and the rule can be computed for the whole scene.
- **Consequence:** The model's inputs include both VV images, so it can learn to rebuild the rule. High scores against these labels show the pipeline works; they do not show the model detects real flooding. Removing `vv_diff` from the inputs did not remove this leakage, because `pre_vv` and `post_vv` carry the same information.

### Dataset Design
- **Patches:** 256 × 256 pixels (2.56 km at 10 m), 50% overlap, inputs `pre_vv`, `pre_vh`, `post_vv`, `post_vh`.
- **Spatial split:** the scene is cut into 512-pixel blocks and whole blocks go to one split (train 73 blocks / 623 patches, validation 16 / 141, test 15 / 129). Splitting patch by patch would put overlapping near-copies in both train and test.
- **Flood balance:** block assignment was chosen so each split has a similar share of flooded pixels (1.47% / 1.36% / 1.46%).
- **Normalisation:** per-channel mean and standard deviation from training pixels only, stored in `dataset_info.json` and in every checkpoint.

### Training Configuration
- **Architecture:** U-Net (`segmentation-models-pytorch`) with an ImageNet-pretrained encoder, 4 input channels, 1 output.
- **Loss:** binary cross-entropy + Dice, to cope with only ~1.4% of pixels being flooded.
- **Optimiser:** AdamW, batch size 16, flip and 90° rotation augmentation. Two runs:
  - **Run A:** 40 epochs, fixed threshold 0.5 (best validation checkpoint at epoch 38).
  - **Run B:** 60 epochs with a one-cycle learning-rate schedule (peak 1e-3), threshold tuned on validation (best validation checkpoint at epoch 51, threshold 0.30).
- **Model selection:** checkpoint with the best validation IoU; the probability threshold is then tuned on validation (not test) and stored in the checkpoint.

---

## 6. Model Results — Cyclone Gabrielle (pseudo-labels)

All scores are flood-class metrics on the held-out **test blocks**, measured against the threshold labels. They show how closely each method reproduces the labelling rule.

**Run A** (`unet_training_40epoch.ipynb`, ResNet-34, best epoch 38, threshold 0.5): test IoU **0.927**, precision 0.955, recall 0.969, F1 0.962.

**Run B** (`unet_training.ipynb`, ResNet-34, best epoch 51, threshold 0.30): test IoU **0.947**, precision 0.971, recall 0.974, F1 0.973.

**Encoder comparison** (`encoder_comparison.ipynb`, same setup, 3 seeds each, mean ± std):

| Method | IoU | Precision | Recall |
| :--- | :--- | :--- | :--- |
| U-Net, EfficientNet-B2 | 0.956 ± 0.001 | 0.976 ± 0.001 | 0.979 ± 0.001 |
| U-Net, ResNet-18 | 0.954 ± 0.002 | 0.975 ± 0.001 | 0.978 ± 0.002 |
| U-Net, ResNet-34 | 0.952 ± 0.002 | 0.977 ± 0.001 | 0.974 ± 0.001 |
| Rule: VV drop > 3.5 dB (no permanent-water mask) | 0.570 | 0.570 | 1.000 |
| Otsu threshold on `post_vv` | 0.050 | 0.051 | 0.840 |

**Interpretation:**
- The three encoders are within about two standard deviations of each other, so none is clearly better on these labels.
- The U-Nets beat the plain rule mainly by also learning to leave out permanent water, which the labels exclude but the inputs do not mark.
- Otsu scores low because it also marks the sea and rivers.
- Independent evaluations: Gabrielle against the HBRC flood extent (`notebooks/nzdf_flood_product.ipynb`, Section 7) and Idai against the WFP/HDX map (`src/evaluate_model.py`, Section 3). Shared numbers: `docs/figures/pipeline_flowchart_notes.md`.

---

## 7. NZDF Decision Product & External Validation

**Notebook:** `notebooks/nzdf_flood_product.ipynb`

1. **Full-scene inference:** predicts the whole 6667 × 4330 pixel Hawke's Bay scene with overlapping, blended 256-pixel windows. Outputs a flood probability GeoTIFF and a binary flood GeoTIFF (1 = flooded, 0 = dry, 255 = nodata).
2. **Vectorisation & road overlay:** converts the flood map to polygons (dropping those under 1,000 m²) and intersects them with LINZ *NZ Road Centrelines (Topo, 1:50k)*. The result is the length and share of each road under water. Outputs are a GeoPackage in NZTM2000 (EPSG:2193) for QGIS, plus GeoJSON copies.
3. **External validation:** scores both the U-Net and the threshold rule against an independent flood extent, over the whole scene and over the test blocks only. The U-Net adds value only if it beats the rule.

**Reference data for Gabrielle:** no LINZ or Civil Defence flood boundary download was found. The closest official source is the Hawke's Bay Regional Council [Cyclone Gabrielle flooding map](https://hbrc.govt.nz/our-council/cyclone-gabrielle-response/cyclone-gabrielle-flooding), published February 2025. It has no public download; the GIS layer must be requested from HBRC (Engineering.Enquiries@hbrc.govt.nz).

**Limitations of the HBRC map as ground truth:**
- **Maximum extent, not a snapshot:** compiled from photos, video, satellite images, building inspections and ground contours over 13–15 February. Water that had drained or not yet arrived at the 14 Feb 07:07 UTC acquisition will count as model misses.
- **Mapped area:** flooding outside the area HBRC mapped would count as false positives unless a mapped-area boundary is supplied.
- **Method:** manually digitised, not derived from radar. This makes it more independent than the pseudo-labels, but its edges are less precise.

---

## 8. Open Questions & Next Steps

- [x] Request the Cyclone Gabrielle flood extent GIS layer from HBRC for external validation. → Obtained and used in `notebooks/nzdf_flood_product.ipynb` (the layer itself is not in the repo).
- [x] Download LINZ road centrelines for Hawke's Bay and run the road overlay. → Done (LINZ layer 50329).
- [x] Build `data/idai_patches/` so `encoder_comparison.ipynb` can score every model on Idai. → Replaced: Idai was evaluated full-scene with `src/evaluate_model.py` for Runs A and B; the encoder-comparison models were not scored on Idai.
- [x] Choose the final encoder once the Idai scores are in. → ResNet-34 kept for both runs.
- [x] Decide whether to keep the pseudo-labels or retrain on independent labels. → Pseudo-labels kept; retraining on independent labels was not done within the project.

---

## 9. Team Task Log

A summary of each member's contributions is in the main `README.md`.

| Date | Contributor | Task / Component Completed | Notes / Blockers |
| :--- | :--- | :--- | :--- |
| 2026-09-17 | Nisheeth | Created the GitHub repository | — |
| 2026-10-01 | Nisheeth | Initial project structure and README | — |
| 2026-10-01 | Sebastian | Design-process document | — |
| 2026-10-01 | Rata | EMSR348 reference-data notebook (`notebooks/idai_reference.ipynb`) | — |
| 2026-10-05 | Rata | Sourced and processed reference flood data for Cyclone Idai (Copernicus EMS EMSR348, AOI03 Beira) and documented it in Section 3; cleaned output `idai_beira_flood_reference.gpkg` on the shared Google Drive | AOI16 has no flood delineation. Need S1 scene closest to 16 Mar 2019 and confirmation Idai isn't in Kuro Siwo training set |
| 2026-10-05 | Sebastian | Preprocessing notebook: 256-pixel patches, spatial block split, train-only normalisation (`data_preprocessing.ipynb`) | Labels are the −3.5 dB rule, so scores on them measure rule-copying |
| 2026-10-08 | Nisheeth | Added Gabrielle data collection notebook (`data_collection.ipynb`): Sentinel-1 export from Google Earth Engine | Switched to ascending orbit 81 for full AOI coverage |
| 2026-10-08 | Sebastian | U-Net training notebook and setup docs (`unet_training.ipynb`, `docs/How the U-Net Training Setup Works.md`); data notebooks save to Google Drive | — |
| 2026-10-14 | Sebastian | Training runs locally; added one-cycle schedule, val-tuned threshold and rule baseline | Test IoU 0.947 (ResNet-34) against pseudo-labels |
| 2026-10-15 | Sebastian | Encoder comparison: ResNet-18 / ResNet-34 / EfficientNet-B2 × 3 seeds, with rule and Otsu baselines (`encoder_comparison.ipynb`) | No clear winner on Gabrielle; Idai patches needed |
| 2026-10-12 | Rhett | NZ external testing notebook and results write-up for Dovi, Ruby and Gretel (`testing-data` branch, merged into `main` on 26 Oct) | No reference maps, so predicted extent only |
| 2026-10-14 | Nisheeth | Streamlit app, evaluation and alignment scripts, Idai and Hale exports, Idai reference data and Run A checkpoint (`project-demo-ready` branch) | — |
| 2026-10-17 | Sebastian | NZDF product notebook (full-scene inference, flood polygons, road overlay, external validation) and data visualisation notebook for the presentation | Waiting on HBRC flood extent and LINZ roads |
| 2026-10-19 | All | Final presentation | — |
| 2026-10-24 | Sebastian | HBRC validation and road-impact analysis, study-area and Gabrielle maps, results summary; merged `seb/local-data` into `main` | — |
| 2026-10-25 | Nisheeth | Idai error map, Idai evaluation with Run B, 14 → 19 March pair export (experiment); merged `project-demo-ready` into `main` | — |
| 2026-10-26 | Rata | Literature review, data-sources table, pipeline flowchart and notes, restored the Run A training notebook, documentation clean-up and figures | — |
