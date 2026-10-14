# Data

- `raw/` contains source scene GeoTIFFs and future event input data.
- `processed/` contains generated training/validation/test patches.
- `archives/` contains downloaded dataset and output archives.

The preprocessing notebook is in [`../notebooks/data_preprocessing.ipynb`](../notebooks/data_preprocessing.ipynb).
New cyclone scenes should be stored under `raw/`, and independent reference
masks can be stored under an event folder such as `idai/`.

For a live upload in the Streamlit app, create a four-band GeoTIFF in the order
`pre-event VV`, `pre-event VH`, `post-event VV`, `post-event VH`. The optional
reference mask must be a one-band binary GeoTIFF on the identical raster grid.