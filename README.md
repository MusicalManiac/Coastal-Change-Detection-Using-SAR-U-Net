# Coastal Change Detection Using Sentinel-1 SAR and U-Net

A Streamlit demonstration and evaluation pipeline for detecting flood-related
change in Sentinel-1 Synthetic Aperture Radar (SAR) imagery. The project was
developed for the GEOG 761 project and is intended for reconnaissance
prioritisation, not safety certification or official flood mapping.

Sentinel-1 SAR is useful during storms because it can acquire imagery through
cloud and at night. The model receives a pre-event and post-event SAR pair and
predicts a pixel-level flood/change mask.

## What was actually used

### Training data

The model was trained on one Sentinel-1 pair from Hawke's Bay, New Zealand,
associated with Cyclone Gabrielle:

- pre-event pass: 21 January 2023;
- post-event pass: 14 February 2023;
- area: Napier and the Esk Valley;
- sensor: Sentinel-1 GRD, IW mode, VV and VH polarization;
- preprocessing: 30 m circular focal mean and training-set normalization.

The source scene was converted into 893 spatially separated 256 x 256 patches:

| Split | Patches | Spatial blocks |
| --- | ---: | ---: |
| Training | 623 | 73 |
| Validation | 141 | 16 |
| Test | 129 | 15 |

The training label is a SAR-derived heuristic: pixels where post-event VV
decreased by more than 3.5 dB relative to pre-event VV, excluding permanent
water. It is therefore a proxy label rather than independently surveyed
ground truth. The reported training/test scores measure how well the U-Net
reproduces this rule; they do not by themselves prove real-world flood
accuracy.

The trained checkpoint is:

```text
models/checkpoints/unet_best.pt
```

It uses a U-Net with a ResNet-34 encoder and four input channels:

```text
pre_vv, pre_vh, post_vv, post_vh
```

The committed checkpoint is **Run A**: a 40-epoch training run, best validation
checkpoint at epoch 38, flood threshold 0.5. A second training run, **Run B**
(60 epochs with a one-cycle learning-rate schedule, best epoch 51, threshold
0.30 tuned on validation), is documented in `notebooks/unet_training.ipynb`;
its checkpoint is not stored in the repo. See [models/README.md](models/README.md).

### Evaluation data

Three evaluation workflows are included:

1. **Cyclone Idai, Beira, Mozambique**  
   Sentinel-1 data from 18 February 2019 (pre-event) and 20 March 2019
   (post-event), with an independent WFP/HDX detected-water reference
   product. The reference is aligned to the Sentinel-1 grid before metrics
   are calculated. This is the main quantitative external evaluation.

2. **Cyclone Gabrielle against the Hawke's Bay Regional Council flood extent**  
   The full Gabrielle scene is compared with HBRC's mapped maximum flood
   extent (13–15 February 2023) in `notebooks/nzdf_flood_product.ipynb`,
   which also produces the road-impact analysis. The HBRC layer itself is not
   stored in the repo.

3. **Other New Zealand cyclones (Dovi, Ruby, Gretel)**  
   Prediction-only tests with no independent reference maps, so only the
   predicted flooded area is reported. Notebook:
   `notebooks/nz_external_testing.ipynb`; results write-up:
   `docs/nz-external-test-results.md`.

Cyclone Hale was also exported and run but is not reported; see
[Cyclone Hale](#cyclone-hale-prediction-only-testing-not-reported).

Cyclone Gabrielle is both the training source and the bundled demo example; the
HBRC comparison uses an independent reference map, but not an unseen event.

## Project structure

```text
Coastal-Change-Detection-Using-SAR-U-Net/
├── src/
│   ├── app.py                        # Streamlit flood-mapping app
│   ├── model.py                      # Checkpoint/model loading
│   ├── evaluate_model.py             # Full-scene and tiled evaluation
│   ├── align_reference.py            # Aligns a reference mask to a stack grid
│   └── make_idai_error_map.py        # Hit / false-alarm / miss map for Idai
├── notebooks/
│   ├── data_collection.ipynb         # Gabrielle Sentinel-1 export (Earth Engine)
│   ├── data_preprocessing.ipynb      # Rule labels, patches, spatial split
│   ├── data_visualisation.ipynb      # Radar imagery figures
│   ├── unet_training_40epoch.ipynb   # Run A (committed checkpoint)
│   ├── unet_training.ipynb           # Run B (60 epochs)
│   ├── encoder_comparison.ipynb      # ResNet-18 / ResNet-34 / EfficientNet-B2
│   ├── nzdf_flood_product.ipynb      # Full-scene map, roads, HBRC validation
│   ├── gabrielle_map.ipynb           # HBRC comparison map
│   ├── study_area_map.ipynb          # Study-area map
│   ├── idai_reference.ipynb          # EMSR348 reference data (Idai)
│   └── nz_external_testing.ipynb     # Dovi, Ruby, Gretel tests (Colab)
├── data/
│   ├── raw/                          # Sentinel-1 input stacks (Git LFS)
│   └── idai/                         # Idai reference products and aligned masks
├── models/
│   └── checkpoints/unet_best.pt      # Run A checkpoint (Git LFS)
├── docs/
│   ├── design-process.md             # Design decisions and task log
│   ├── literature-review.md          # Background literature (APA 7)
│   ├── data-sources.md               # Data sources and references (APA 7)
│   ├── Data Collection & Preprocessing Summary.md
│   ├── How the U-Net Training Setup Works.md
│   ├── Results & Findings Summary.md
│   ├── nz-external-test-results.md   # NZ cyclone test results
│   ├── hale_testing.md
│   ├── idai_gee_export.js            # Earth Engine export, Idai
│   ├── hale_gee_export.js            # Earth Engine export, Hale
│   └── figures/                      # Shared figures, pipeline flowchart and notes
├── requirements.txt                  # App and evaluation dependencies
├── .streamlit/config.toml            # 1 GB upload limit for large GeoTIFFs
└── README.md
```

Large files (Sentinel-1 stacks, reference rasters and the checkpoint) are stored
with Git LFS. Generated outputs are kept locally and are not in version
control: `data/processed/`, `data/archives/`, `outputs/` and `models/outputs/`.

### Side experiments and superseded files

These are kept for the record but are not used for the reported results:

- `data/raw/Idai_S1_PrePost_20190307_20190319.tif` and
  `data/idai/Idai_reference_mask.tif`: an earlier Idai stack (7 → 19 March 2019)
  and its aligned mask, superseded by the 18 February → 20 March pair.
- `docs/idai_gee_export_20190314_20190319.js`: a separate 14 → 19 March 2019
  Idai pair.
- `data/raw/Hale_S1_PrePost_202301_overlap-0000000000-0000000000.tif`,
  `docs/hale_gee_export.js` and `docs/hale_testing.md`: Cyclone Hale (see below).

## Installation and first start

The following commands are for Windows PowerShell. Run them from the project
root.

### 1. Create and activate a virtual environment

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either allow local scripts for your user or
run the interpreter directly:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` covers the Streamlit app and the evaluation scripts. The
notebooks install their own extra packages in their first cells (for example
`geopandas`, `earthengine-api`, `geemap` and `contextily`).

On macOS or Linux, create the environment with `python3 -m venv venv`, activate
it with `source venv/bin/activate`, and use `/` instead of `\` in the paths
below.

### 3. Confirm the checkpoint exists

```powershell
Get-Item models\checkpoints\unet_best.pt
```

### 4. Start the Streamlit app

```powershell
streamlit run src\app.py
```

Open the local URL shown in the terminal, normally:

```text
http://localhost:8501
```

To stop the server, press `Ctrl+C` in the terminal.

## Using the Streamlit app

The app has two input modes.

### Bundled Gabrielle demo

Enable **Use bundled Gabrielle example**. This loads the local six-band
Gabrielle stack and shows:

- pre-event VV;
- post-event VV;
- the SAR-derived training label;
- the U-Net prediction;
- flood probabilities;
- predicted flooded area;
- VV statistics.

This is a demonstration of the trained workflow, not an independent accuracy
test.

### Upload another cyclone

Leave the bundled example disabled and upload a GeoTIFF with four bands in
this exact order:

```text
1. pre-event VV
2. pre-event VH
3. post-event VV
4. post-event VH
```

The pre-event and post-event bands must use the same CRS, transform, extent,
width, and height. Values should be calibrated Sentinel-1 dB backscatter.
New stacks should use the same 30 m focal-mean preprocessing as training.

The app allows uploads up to 1 GB through
[.streamlit/config.toml](.streamlit/config.toml). Restart Streamlit after
changing this configuration.

## Cyclone Idai: quantitative evaluation

The reproducible Earth Engine export is
[docs/idai_gee_export.js](docs/idai_gee_export.js). It exports four smoothed
bands from the 18 February 2019 and 20 March 2019 scenes using the common
valid SAR region and EPSG:3857 at 10 m.

After downloading the completed GeoTIFF, place it in `data/raw/` and validate
it:

```powershell
python -c "import rasterio; p=r'data\raw\Idai_S1_PrePost_20190218_20190320_overlap.tif'; s=rasterio.open(p); print('bands:', s.count); print('size:', s.width, s.height); print('crs:', s.crs); print('resolution:', s.res); print('descriptions:', s.descriptions)"
```

Create a reference mask on the exact new stack grid:

```powershell
python src\align_reference.py `
  --reference data\idai\reference\extracted\MOZ_TotalFloodExtent12to2.tif `
  --stack data\raw\Idai_S1_PrePost_20190218_20190320_overlap.tif `
  --output data\idai\Idai_reference_mask_20190218_20190320.tif
```

Run full-scene inference and aggregate metrics across every valid,
non-overlapping 256 x 256 tile:

```powershell
python src\evaluate_model.py `
  --stack data\raw\Idai_S1_PrePost_20190218_20190320_overlap.tif `
  --reference data\idai\Idai_reference_mask_20190218_20190320.tif `
  --checkpoint models\checkpoints\unet_best.pt `
  --output-dir outputs\evaluation\idai_20190218_20190320 `
  --aggregate-patches
```

The evaluator writes a prediction GeoTIFF and a JSON metrics file. The JSON
contains:

- `metrics`: pooled full-scene metrics;
- `aggregated_metrics.macro_mean`: mean metric across valid tiles, with every
  tile weighted equally;
- `aggregated_metrics.micro_overall`: metrics after pooling all valid pixels;
- confusion-matrix counts and the number of evaluated patches.

The Idai WFP/HDX reference is a detected-water/flood-extent product compiled
over multiple dates. It does not distinguish permanent open water from newly
inundated land, and it is not perfect surveyed ground truth. Report those
limitations with the metrics.

## Cyclone Hale: prediction-only testing (not reported)

Hale was exported and run but is not reported: its post-event image
(20 January 2023) was acquired about 9 days after the storm. The workflow is
kept for reproducibility.

Run [docs/hale_gee_export.js](docs/hale_gee_export.js) in the Google Earth
Engine Code Editor. It searches for a pre/post Sentinel-1 VV+VH pair over
Hawke's Bay, applies the 30 m focal mean, and exports a four-band stack at
10 m in EPSG:2193.

After placing the downloaded file in `data/raw/`, run prediction-only
evaluation:

```powershell
python src\evaluate_model.py `
  --stack data\raw\Hale_S1_PrePost_202301_overlap-0000000000-0000000000.tif `
  --checkpoint models\checkpoints\unet_best.pt `
  --output-dir outputs\evaluation\hale
```

Do not use `--reference` or `--aggregate-patches` for Hale unless an
independent Hale reference mask becomes available. Without a reference, the
output is useful for visual inspection and prediction statistics, but it is
not an accuracy measurement.

## Reference-mask requirements

For independent metrics, the reference must be:

- one-band;
- binary or convertible to binary;
- independently produced, not derived from the model inputs using the same
  threshold rule;
- aligned to the exact input grid;
- identical in CRS, transform, width, height, and extent.

The alignment utility converts source nodata to non-flooded only when the
source product's coverage and semantics justify that treatment. Check the
source metadata before reporting metrics.

## Troubleshooting

### `streamlit run app.py` cannot find the file

The app is under `src/`. Start it from the project root with:

```powershell
streamlit run src\app.py
```

### GeoTIFF upload is rejected because it is too large

Restart Streamlit after confirming `.streamlit/config.toml` contains:

```toml
[server]
maxUploadSize = 1024
```

For large files, prefer `evaluate_model.py`, which reads directly from disk
and does not require a browser upload.

### The app reports no valid SAR pixels

The selected patch may be outside the common valid scene footprint. Use the
suggested best patch or export a tighter common-valid region from Earth
Engine. Do not silently treat large nodata areas as valid SAR observations.

### Metrics cannot be enabled

Upload an independent one-band reference mask on the exact same grid first.
Prediction probabilities and flooded-area estimates can still be viewed
without a reference, but accuracy metrics cannot be calculated responsibly.

## Limitations

- The training labels are SAR-derived threshold proxies, not independent
  surveyed flood labels.
- The model was trained on one Gabrielle scene pair, so results on Idai and
  the other New Zealand cyclones are cross-event tests with possible
  geographic and acquisition differences.
- Idai metrics depend on a multi-date detected-water reference and the valid
  overlap of the selected Sentinel-1 scenes.
- Dovi, Ruby, Gretel and Hale have no independent reference masks.
- Outputs are decision-support demonstrations and must not be used as a
  safety certification, evacuation map, or replacement for local validation.

## Further documentation

- [Design process and task log](docs/design-process.md)
- [Literature review](docs/literature-review.md)
- [Data sources](docs/data-sources.md)
- [Pipeline flowchart](docs/figures/pipeline_flowchart.drawio.png) and [flowchart notes](docs/figures/pipeline_flowchart_notes.md)
- [Data collection and preprocessing summary](docs/Data%20Collection%20%26%20Preprocessing%20Summary.md)
- [How the U-Net training setup works](docs/How%20the%20U-Net%20Training%20Setup%20Works.md)
- [Results and findings summary](docs/Results%20%26%20Findings%20Summary.md)
- [NZ cyclone test results](docs/nz-external-test-results.md)
- [Models and checkpoints](models/README.md)
- [Idai data notes](data/idai/README.md)
- [Hale testing notes](docs/hale_testing.md)
- [Figures](docs/figures/)

## Contributions

| Member | Main contributions |
| --- | --- |
| Rata Lomax | Researched the problem and the Navy's needs, including an interview with a Navy contact; built the pitch slides and speech; sourced and documented the Copernicus EMS EMSR348 reference flood data for Cyclone Idai (`notebooks/idai_reference.ipynb`); project organisation and coordination throughout (meeting notes, to-do lists and task tracking, group check-ins, contributions record, project review); designed the final presentation and slides 1–4 and 12, and integrated everyone's slides; literature review and data-sources table with verified references; pipeline flowchart and notes; repository review and documentation clean-up. |
| Sebastian Torres | Researched satellite and AI methods; searched NZ cyclone events in Earth Engine; set up the design-process document; collected and pre-processed the Gabrielle radar data and created the training labels; trained the U-Net (40- and 60-epoch runs); encoder comparison; full-scene flood product, road-impact analysis and HBRC validation; study-area and Gabrielle maps; slides 5–6. |
| Nisheeth Bhooshan Gupta | Researched project risks and wrote the pitch overview; checked global flood events and datasets; set up and coordinated the GitHub repo, including merging branches; exported and aligned the Cyclone Idai data and ran the independent Idai evaluation for both runs, including the error map; built the Streamlit flood-mapping app and demo recording; slides 7 and 10. |
| Rhett Murdoch | Researched the expected product and real NZDF operations; prepared pitch Q&A; tested the model on other NZ cyclones (Dovi, Ruby, Gretel) and wrote up the results; slides 8, 9 and 11. |

All members: weekly meetings, ideation, planning and reviewing each other's work.
