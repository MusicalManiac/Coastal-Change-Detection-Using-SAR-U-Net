# Cyclone Idai test data

## Reference files downloaded

These public HDX files are stored under `reference/`:

- `MOZ_floods_20190312.zip`: flood extent as of 12 March 2019.
- `MOZ_TotalFloodExtent.zip`: maximum flood extent compiled from 12–21 March 2019.

Source dataset: [WFP Mozambique satellite detected waters, Cyclone Idai](https://data.humdata.org/dataset/mozambique-flood-detected-waters-cyclone-idai).

The extracted rasters are reference products, not Sentinel-1 input stacks. They
are currently in EPSG:3857 at approximately 95 m resolution and must be
reprojected/rasterized to the exact grid of the Sentinel-1 stack before use with
`src/evaluate_model.py`.

## Find Sentinel-1 input scenes

Use Google Earth Engine to search `COPERNICUS/S1_GRD` over Beira. Filter for:

- dates before and after 14–15 March 2019;
- `instrumentMode == "IW"`;
- `resolution_m == 10`;
- `transmitterReceiverPolarisation == ["VV", "VH"]`;
- the same relative orbit and orbit pass for both dates where possible.

The collection is already radiometrically calibrated, terrain corrected, and in
decibels. Export the selected pre-event and post-event VV/VH bands to a common
10 m grid, then stack them in this order:

```text
pre-event VV, pre-event VH, post-event VV, post-event VH
```

The training pipeline also applied a 30 m circular focal mean before stacking.
That preprocessing must be reproduced for a fair cross-cyclone test.

The reproducible Earth Engine export is in
[`../../docs/idai_gee_export.js`](../../docs/idai_gee_export.js). It exports the
intersection of the pre-event footprint, post-event footprint, and Beira AOI,
rather than the former fixed rectangle. This avoids the earlier export in which
only about 0.79% of pixels had valid SAR values.

## Scenes used

The Idai test uses the Sentinel-1 pair **18 February 2019 (pre-event) →
20 March 2019 (post-event)**, exported by `docs/idai_gee_export.js` to
`data/raw/Idai_S1_PrePost_20190218_20190320_overlap.tif`.

Superseded files, kept for the record and not used for the evaluation:

- `data/raw/Idai_S1_PrePost_20190307_20190319.tif` (7 → 19 March stack) and its
  aligned mask `data/idai/Idai_reference_mask.tif`;
- `docs/idai_gee_export_20190314_20190319.js` (14 → 19 March pair, a separate
  experiment).

An earlier reference, Copernicus EMS EMSR348 (AOI03 Beira), was processed in
`notebooks/idai_reference.ipynb`; the evaluation uses the WFP/HDX product above.

The reference dataset metadata describes the 12 March product as compiled from
Copernicus and Sentinel-1, and the maximum product as using data from 12–21
March. These dates do not prove that they match any particular Sentinel-1 scene,
so record the actual image IDs and acquisition dates used for the test.

To align the maximum-extent reference to an exported Sentinel-1 stack, run:

```powershell
python src\align_reference.py `
  --reference data\idai\reference\extracted\MOZ_TotalFloodExtent12to2.tif `
  --stack data\raw\Idai_S1_PrePost_20190218_20190320_overlap.tif `
  --output data\idai\Idai_reference_mask_20190218_20190320.tif
```

The source uses value `1` for mapped flood and `255` as nodata. The alignment
converts nodata to `0` because the reference raster covers the stack extent.
This treats unmapped pixels within that extent as non-flooded.
