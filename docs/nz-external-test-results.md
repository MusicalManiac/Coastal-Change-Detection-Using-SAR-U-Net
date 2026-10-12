# NZ external testing results: Dovi, Ruby and Gretel

Prepared 12 October 2026 from the three `prediction_preview.png` images and three `run_info.json` files supplied in `Testing1.zip`.

## What we tested

We applied the model trained on Cyclone Gabrielle to before-and-after radar images for three other events. We loaded the saved model rather than training a new model for each event.

All runs used the same epoch-38 checkpoint, the same four input channels (`pre_vv`, `pre_vh`, `post_vv`, `post_vh`), and the original training normalisation statistics. A pixel was classified as flooded when its model score was greater than **0.5**.

This demonstrates that the model can run on new event imagery. It does **not yet establish whether it detects flooding accurately** in those events.

## Images used

Dates below are satellite acquisition dates in UTC, not necessarily the time of maximum flooding.

| Event | Area examined | Before image | After image |
|---|---|---|---|
| Dovi | Wairarapa | 1 February 2022 | 13 February 2022 |
| Ruby | East Cape | 3 December 2021 | 15 December 2021 |
| Gretel | Northland | 7 March 2020 | 19 March 2020 |

The Dovi after image was acquired at approximately **6:22 am on 14 February NZDT**. The Ruby after image was acquired at approximately **6:21 am on 16 December NZDT**. Gretel's after images were acquired at approximately **8:07 pm on 19 March NZDT**.

Gretel is an exploratory image test: this work has not established a corresponding observed NZ flood reference.

## Where the numbers came from

Each event's `run_info.json` contains:

- `valid_pixels`: the number of pixels with usable data in all four radar inputs.
- `predicted_flood_pixels`: the number of those pixels classified as flooded by the model.

These counts were recorded during prediction, not estimated from the preview images. Invalid pixels are excluded. **Valid pixels include land and sea**; the notebook does not explicitly exclude permanent water or the sea from its predictions or these totals.

Each output pixel covers **10 m × 10 m = 100 m²** on the projected output grid. Therefore:

```text
Percentage predicted flooded = predicted_flood_pixels / valid_pixels × 100

Area predicted flooded (km²) = predicted_flood_pixels × 100 / 1,000,000

Total usable area (km²) = valid_pixels × 100 / 1,000,000
```

For Dovi:

```text
394,191 / 81,764,314 × 100 = 0.4821%, rounded to 0.48%

394,191 × 100 / 1,000,000 = 39.4191 km², rounded to 39.4 km²

81,764,314 × 100 / 1,000,000 = 8,176.4314 km²
```

The areas are sums of output pixel areas. They describe the model's classifications, not independently measured inundation.

## Results

| Event | Valid pixels | Pixels predicted flooded | Total usable area | Percentage predicted flooded | Area predicted flooded |
|---|---:|---:|---:|---:|---:|
| Dovi | 81,764,314 | 394,191 | 8,176.4 km² | 0.48% | 39.4 km² |
| Ruby | 31,404,587 | 96,845 | 3,140.5 km² | 0.31% | 9.7 km² |
| Gretel | 223,360,679 | 9,853,504 | 22,336.1 km² | 4.41% | 985.4 km² |

The total usable area across the three runs is **33,653.0 km²**, including land and sea. This is the sum of the analysed areas, not a flood-area total.

## What the percentages mean

**0.48% for Dovi means the model marked 0.48% of the usable image area as flooded. It does not mean the model was 0.48% accurate.** The same distinction applies to Ruby and Gretel.

There is no expected percentage that demonstrates good performance. A small predicted area could mean limited flooding, missed flooding, or both. A large predicted area could mean extensive flooding, false alarms, or both.

The regions have different sizes and different proportions of sea. These percentages cannot establish which cyclone caused worse flooding.

To understand whether the model is doing its job, we must check **where it predicted flooding**, not just how much area it labelled.

## How to read the previews

The external-testing previews have three columns:

| Column | What it shows |
|---|---|
| Left | Post-event VV radar image in decibels. Dark areas are not automatically floods. |
| Middle | Model score from 0 to 1. Purple indicates low scores; yellow indicates high scores. |
| Right | Final prediction: blue represents pixels classified as flooded, and pale areas represent predicted non-flood pixels. Invalid areas may be blank. |

**The middle column is a model output, not a reference label or “mark scheme”.** This differs from the earlier training figure, whose middle column showed the automatic Gabrielle label.

A model score of 0.9 is not established as a 90% real-world chance of flooding. The scores have not been calibrated against independent observations.

### Dovi

The preview shows predictions concentrated along a river-like corridor and adjacent areas. These are locations worth checking against independent observations. The preview alone cannot distinguish new floodwater from ordinary river water or other causes of radar change.

### Ruby

The preview shows comparatively sparse predictions, with several concentrated groups near the lower part of the image. We need geographic overlays and closer inspection to identify the affected places and determine whether these predictions correspond to actual inundation.

### Gretel

The preview shows many predicted-flood pixels on the apparent sea side of the coastline, particularly in the upper part of the image. This is visual evidence of **apparent false positives over ordinary water**. It is not a conclusion drawn from the 4.41% figure alone.

A coastline/permanent-water overlay is needed to confirm exactly which predicted pixels are offshore or normal water. The 985.4 km² prediction should not be reported as confirmed Gretel flooding.

## What these results establish—and what they do not

| Question | Current answer |
|---|---|
| Can the saved model process imagery from these additional events? | Yes; all three runs produced predictions and metadata. |
| Was the same model and decision threshold used? | Yes, according to the saved run metadata. |
| Do we know how accurate the predictions are? | No; independent reference labels were unavailable in all three runs. |
| Are there visible reasons to question the predictions? | Yes; Gretel appears to include sea/permanent-water false positives. |
| Can we calculate independent IoU, precision, recall or F1 from these files? | No; prediction counts alone do not identify correct detections, false alarms or missed floods. |

The earlier Gabrielle **IoU of 0.927** was agreement with labels generated by a radar darkness-change rule. It is not an accuracy score for Dovi, Ruby or Gretel, and it does not independently establish real flood-detection accuracy.

## What we need to do next

1. Overlay the predicted masks on a geographic map with coastline, rivers and place names.
2. Define exclusions for sea and permanent water, then recompute land-only summaries. This improves the evaluation domain but does not itself prove accuracy.
3. Inspect before-and-after imagery at selected predicted locations, including areas where the model may have missed flooding.
4. Obtain independent observed flood references and record their observation times and analysed coverage. Unknown areas must not automatically be labelled dry.
5. Compare both the model and the original darkness-change rule against the same eligible reference pixels. Measure correct detections, false alarms and missed floods, then calculate IoU, precision, recall and F1.

The inference notebook uses nonoverlapping 256×256 windows. Tile-boundary effects are another limitation to inspect when reviewing the full-resolution maps.

## Practical significance

The intended use is to highlight **places to inspect after a storm**, for example areas near coastal access roads or relief landing locations. A verified geographic flood map could support reconnaissance prioritisation.

At present, these maps are **unverified predictions**. Their percentages describe how much the model flagged; they do not establish that the model works properly or justify operational decisions by themselves.

## Suggested wording for the project report

> The Gabrielle-trained model was applied to additional Sentinel-1 image pairs for Dovi, Ruby and Gretel without retraining. It classified 0.48%, 0.31% and 4.41% of the respective valid image areas as flooded. These summaries include land and sea and represent predicted rather than observed inundation. Gretel's preview shows apparent false positives over ordinary water. Independent accuracy remains unestablished because time-matched reference flood labels were not available.
