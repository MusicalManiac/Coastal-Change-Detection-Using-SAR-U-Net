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

### Evaluation data

Two unseen-event workflows are included:

1. **Cyclone Idai, Beira, Mozambique**  
   Sentinel-1 data from 18 February 2019 (pre-event) and 20 March 2019
   (post-event), with an independent WFP/HDX detected-water reference
   product. The reference is aligned to the Sentinel-1 grid before metrics
   are calculated. This is the main quantitative external evaluation.

2. **Ex-Tropical Cyclone Hale, Hawke's Bay, New Zealand**  
   A Sentinel-1 pre/post test stack is available through the Earth Engine
   export workflow. No independent Hale flood mask is currently available,
   so Hale is a prediction-only demonstration. Do not report IoU, Dice/F1,
   precision, or recall for Hale without an independent reference mask.

Cyclone Gabrielle is both the training source and the bundled demo example; it
must not be presented as an independent unseen-event test.

## Project structure

```text
Coastal-Change-Detection-Using-SAR-U-Net/
├── src/
│   ├── app.py                 # Streamlit application
│   ├── model.py               # Checkpoint/model loading
│   ├── evaluate_model.py      # Full-scene and tiled evaluation
│   └── align_reference.py     # Aligns a reference mask to a stack grid
├── data/
│   ├── raw/                   # Input Sentinel-1 GeoTIFFs
│   ├── processed/             # Training patches and derived data
│   ├── archives/              # Downloaded archives
│   └── idai/                  # Idai reference products and aligned masks
├── models/
│   ├── checkpoints/           # Trained model checkpoint
│   └── unet_training.ipynb    # Training notebook
├── notebooks/
│   ├── data_collection.ipynb  # Gabrielle Earth Engine collection
│   ├── data_preprocessing.ipynb
│   └── idai_reference.ipynb
├── docs/
├── outputs/                   # Predictions, metrics, and evaluation results
├── requirements.txt
├── .streamlit/config.toml     # 1 GB upload limit for large GeoTIFFs
└── README.md
```

Large GeoTIFFs, generated patches, checkpoints, and evaluation outputs are
normally kept locally and may be excluded from version control.

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

## Cyclone Hale: prediction-only testing

Run [docs/hale_gee_export.js](docs/hale_gee_export.js) in the Google Earth
Engine Code Editor. It searches for a pre/post Sentinel-1 VV+VH pair over
Hawke's Bay, applies the 30 m focal mean, and exports a four-band stack at
10 m in EPSG:2193.

After placing the downloaded file in `data/raw/`, run prediction-only
evaluation:

```powershell
python src\evaluate_model.py `
  --stack data\raw\Hale_S1_PrePost_202301_overlap.tif `
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
  Hale are cross-event tests with possible geographic and acquisition
  differences.
- Idai metrics depend on a multi-date detected-water reference and the valid
  overlap of the selected Sentinel-1 scenes.
- Hale currently has no independent reference mask.
- Outputs are decision-support demonstrations and must not be used as a
  safety certification, evacuation map, or replacement for local validation.

## Further documentation

- [Data collection and preprocessing summary](docs/Data%20Collection%20%26%20Preprocessing%20Summary.md)
- [How the U-Net training setup works](docs/How%20the%20U-Net%20Training%20Setup%20Works.md)
- [Idai data notes](data/idai/README.md)
- [Hale testing notes](docs/hale_testing.md)
- [Risk analysis](docs/risk-analysis.md)
