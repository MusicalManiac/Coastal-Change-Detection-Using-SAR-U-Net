# Cyclone Hale testing

Run `hale_gee_export.js` in the Google Earth Engine Code Editor. It exports
four smoothed Sentinel-1 bands:

```text
pre_vv, pre_vh, post_vv, post_vh
```

Place the completed GeoTIFF in `data/raw/` and test it with:

```powershell
python src\evaluate_model.py `
  --stack data\raw\Hale_S1_PrePost_202301_overlap.tif `
  --checkpoint models\checkpoints\unet_best.pt `
  --output-dir outputs\evaluation\hale
```

No independent Hale flood mask is currently available. Do not calculate
accuracy metrics for Hale without an independently produced, aligned reference.
