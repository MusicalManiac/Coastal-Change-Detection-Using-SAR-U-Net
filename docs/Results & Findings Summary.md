# Results & Findings Summary

Oct 23, 2026 · @Sebastian

## Overview

The U-Net reproduces its training labels almost perfectly. Against the independent Hawke's Bay Regional Council (HBRC) flood extent, it is precise but finds only about a quarter of the flooding, and it does no better than the simple threshold rule it was trained on.

| Question | Answer | Key number |
| --- | --- | --- |
| Does the U-Net learn the labels? | Yes | Test IoU 0.947 against `baseline_mask` |
| Does the encoder matter? | No | resnet18 / resnet34 / efficientnet-b2 all within 0.954 ± 0.003 IoU |
| When it says "flooded", is it right? | Yes | Precision 0.93 against HBRC |
| Does it find all the flooding? | No | Recall 0.24 (whole scene), 0.33 (test blocks) against HBRC |
| Is it better than the threshold rule? | No | IoU 0.232 vs 0.231 against HBRC |
| Why does it miss flooding? | Most missed flooding was not dark open water in the 14 Feb image | 87% of missed pixels show no change or got brighter |

The model maps water still lying on the ground when the satellite passed, and maps it accurately. It cannot map the maximum extent HBRC recorded, and neither can any model trained on a "VV drop below −3.5 dB" label.

## Setup in brief

Full details are in [Data Collection & Preprocessing Summary](Data%20Collection%20&%20Preprocessing%20Summary.md) and [How the U-Net Training Setup Works](How%20the%20U-Net%20Training%20Setup%20Works.md).

| Item | Value |
| --- | --- |
| Imagery | Sentinel-1 IW, VV + VH, relative orbit 81; pre 2023-01-21, post 2023-02-14 07:07 UTC (about 8 pm NZDT) |
| Scene | Napier / Esk Valley, 6,667 × 4,330 px at 10 m, 99.7% valid |
| Inputs | `pre_vv`, `pre_vh`, `post_vv`, `post_vh` (dB, standardised) |
| Labels (`baseline_mask`) | `post_vv − pre_vv < −3.5 dB` outside JRC permanent water; about 1.4% of pixels flooded |
| Dataset | 893 patches of 256 × 256, split by spatial block: 623 train / 141 val / 129 test |
| Model | U-Net, resnet34 encoder (24.4M parameters), BCE + Dice, one-cycle LR, 60 epochs |
| Independent reference | HBRC "Hawke's Bay Flood Observation Extents", event "NIWE Feb 2023", photo interpretation and ground survey (418 polygons) |

## 1. Training results (`unet_training.ipynb`)

- Best checkpoint at epoch 51, val IoU 0.926.
- Threshold tuned on val: 0.30 (val IoU 0.927). The IoU curve is flat between 0.20 and 0.50, so the choice hardly matters.

Test set (threshold 0.30), scored against `baseline_mask`:

| Map | IoU | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| U-Net (resnet34) | 0.947 | 0.971 | 0.974 | 0.973 |
| Rule without JRC mask | 0.570 | 0.570 | 1.000 | — |
| Rule with JRC mask | 1.000 | 1.000 | 1.000 | — (the labels themselves) |

**How to read this:** the score measures how well the U-Net rebuilds the labelling rule. It isn't flood-mapping accuracy. The rule without the JRC mask loses precision only because it flags permanent water, which the model learned to leave out without being given the JRC layer.

## 2. Encoder comparison (`encoder_comparison.ipynb`)

Three encoders, three seeds each, otherwise identical setup. Gabrielle test set, mean ± std over seeds:

| Model | IoU | Precision | Recall |
| --- | --- | --- | --- |
| resnet18 | 0.954 ± 0.002 | 0.975 ± 0.001 | 0.978 ± 0.002 |
| resnet34 | 0.952 ± 0.002 | 0.977 ± 0.001 | 0.974 ± 0.001 |
| efficientnet-b2 | 0.956 ± 0.001 | 0.976 ± 0.001 | 0.979 ± 0.001 |
| Rule (VV change < −3.5 dB) | 0.570 | 0.570 | 1.000 |
| Otsu threshold on `post_vv` (−16.33 dB) | 0.050 | 0.051 | 0.840 |

**Finding:** the spread between encoders (0.004 IoU) is about the size of the seed noise. Against threshold labels, the encoder makes no meaningful difference, so the smallest one (resnet18) is the practical choice. The encoder-comparison models were not scored on Idai; the Idai evaluation of the two main runs is produced by `src/evaluate_model.py`.

**Finding:** a single threshold on post-event backscatter alone (Otsu) is useless here (IoU 0.05), because hill shadow and smooth surfaces are as dark as water. The pre-event image is what makes change detection work.

## 3. Full-scene flood product (`nzdf_flood_product.ipynb`, Steps 1–2)

| Output | Value |
| --- | --- |
| Predicted flooded area | 38.0 km² (1.32% of valid pixels) |
| Agreement with `baseline_mask`, whole scene | IoU 0.938, precision 0.967, recall 0.969 |
| Agreement with `baseline_mask`, test blocks only | IoU 0.952, precision 0.973, recall 0.977 |
| Flood polygons | 1,951 raw, 1,259 kept after dropping those under 1,000 m²; 37.7 km² |
| Roads in scene (LINZ 1:50k centrelines) | 2,006 features, 1,938 km |
| Roads cut by flooding | 96 features, 16.3 km under water |

The test-block IoU (0.952) matches the training notebook's 0.947, which confirms that sliding-window inference over the full scene reproduces training.

Longest flooded road stretches:

| Road | Length (m) | Flooded (m) | Flooded (%) |
| --- | --- | --- | --- |
| Gilligan Road | 2,259 | 1,529 | 68 |
| Swamp Road | 7,802 | 1,356 | 17 |
| Brookfields Road | 1,853 | 1,111 | 60 |
| Hawke's Bay Expressway | 4,162 | 1,093 | 26 |
| Gilbertson Road | 2,095 | 992 | 47 |
| Korokipo Road | 6,913 | 595 | 9 |
| McLeod Road | 1,080 | 469 | 43 |
| Pakowhai Road | 4,421 | 392 | 9 |
| Sisson Road | 391 | 391 | 100 |

**Visual check:** predicted flooding sits on the Heretaunga Plains south of Napier (Awatoto, Brookfields, Meeanee, Pakowhai), with thin strips along swollen river channels further north. The sea, Lake Tūtira and other permanent water are correctly excluded. The only obvious false positive is one small blob in the open bay.

## 4. External validation against HBRC (Step 3)

The scored area is all valid pixels: 2,877 km², of which the HBRC reference marks 149.2 km² as flooded.

| Map | Area | IoU | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- |
| U-Net | Whole scene | 0.232 | 0.930 | 0.237 | 0.377 |
| U-Net | Test blocks only | 0.325 | 0.933 | 0.333 | 0.491 |
| Rule (`baseline_mask`) | Whole scene | 0.231 | 0.928 | 0.236 | 0.376 |
| Rule (`baseline_mask`) | Test blocks only | 0.322 | 0.929 | 0.330 | 0.487 |

**Findings:**

1. **High precision (0.93).** About 93% of what the map flags as flooded is inside the HBRC extent. For the NZDF use case this is the property that matters most: a road shown as cut really was flooded.
2. **Low recall (0.24–0.33).** The map finds 35 km² of the 149 km² HBRC extent.
3. **No gain over the rule.** The U-Net and the rule differ by 0.001–0.003 IoU. The model inherited the rule's blind spots along with its strengths.
4. **The test-block rows score higher for both maps.** That reflects where the test blocks happen to fall, not better generalisation, because the rule shows the same jump.

## 5. Why the map misses flooding (cell 12)

Of the HBRC flood extent, 35.3 km² was detected and 113.9 km² missed. False alarms outside the reference total only 2.6 km².

VV change (post − pre) at reference flood pixels, % of pixels:

| VV change | Detected | Missed |
| --- | --- | --- |
| Strong drop (< −3.5 dB) | 97.6 | 0.7 |
| Weak drop (−3.5 to −1.5 dB) | 2.4 | 12.6 |
| Little change (±1.5 dB) | 0.0 | 42.6 |
| Brighter (> +1.5 dB) | 0.0 | 44.1 |
| **Median** | **−7.4 dB** | **+1.2 dB** |

Reference polygons in the scored area (155), by the share the map detected:

| Detected | Polygons | Reference area (km²) |
| --- | --- | --- |
| None (0%) | 109 | 2.8 |
| Little (0–25%) | 33 | 76.6 |
| Partly (25–75%) | 12 | 69.8 |
| Mostly (> 75%) | 1 | 0.0 |

**Findings:**

1. **The missed flooding didn't look like open water to the radar.** 87% of missed pixels show no change or got brighter, and the median change is +1.2 dB against −7.4 dB for detected flooding. Lowering the threshold could recover at most the 12.6% with a weak drop, so threshold tuning can't close the gap.
2. **The misses are mostly unfound parts of large flooded areas.** The 109 polygons missed completely cover only 2.8 km². Most of the missed area lies inside the large polygons the map partly detected.
3. **The misses have a clear pattern.** All of the Esk Valley, the Tūtaekurī and Ngaruroro river corridors upstream, and the outer edges of the plains are missed. Detected flooding is the water ponded on the low Heretaunga Plains.

**Likely explanations** (interpretation; check against aerial imagery in QGIS with the `reference_missed` layer):

- **Timing.** HBRC mapped the maximum extent over 13–15 February. The radar pass was at about 8 pm NZDT on 14 February, many hours after the river valleys peaked overnight on 13–14 February. Fast-draining valleys had largely emptied by then, while the low-lying plains still held water.
- **Wet ground and silt brighten the signal.** Saturated soil and fresh silt or debris return more radar signal than dry ground, so receded flood areas got brighter rather than darker.
- **Flooding under trees, crops and buildings.** Water under orchards and vines or between buildings can increase backscatter through double-bounce, the opposite of the signal the label rule looks for.
- **Mapping method.** Photo interpretation and ground survey include areas affected by flooding (for example silt deposits) that may not have had standing water at any single moment.

## 6. What this means for the report

**Claims the results support:**

- The pipeline works from start to finish: from Earth Engine export to a road-impact GeoPackage in NZTM2000 that opens in QGIS.
- The flood map is reliable where it flags flooding (93% precision against an independent source), so it suits rapid "which roads are cut" triage.
- The map is conservative. It shows standing water at the time of the radar pass, roughly a quarter of the recorded maximum extent.
- Against threshold labels, the deep model matches the rule. Its advantages today are practical, not accuracy: it learns to leave out permanent water without a JRC layer, gives a smooth probability map, and provides a workflow that can take better labels.

**Claims to avoid:**

- Don't present the 0.95 IoU as flood-mapping accuracy. It measures agreement with the rule that made the labels.
- Don't claim the U-Net beats the threshold approach. Against HBRC it doesn't.
- Don't read the whole-scene vs test-block difference as generalisation.

**Limitations to state:**

- The labels are circular: the model is trained on a rule it can rebuild from its own inputs.
- A single post-event image means the map is a snapshot, not a maximum extent.
- The pre-event image is 24 days earlier, so some change may come from land or soil moisture rather than flooding.
- One training event and one place. The Idai transfer test is produced by `src/evaluate_model.py`.
- The HBRC reference is itself compiled from mixed sources and is a maximum, not a snapshot. Its recall penalty is partly a timing mismatch, not model error.

**Future work the results point to:**

- Train or fine-tune on labels independent of the rule (part of the HBRC extent, or Copernicus EMS maps) and hold the rest out for testing.
- Use brightening as flood evidence for vegetated and urban areas, or add coherence or optical data.
- Use a post-event image closer to the peak (orbits 175 or 8), or several post-event dates, to estimate maximum extent.

## Where the numbers come from

| Result | Source |
| --- | --- |
| Training, threshold tuning, test set, rule baseline | `notebooks/unet_training.ipynb`, cells 6–9 |
| Encoder comparison | `notebooks/encoder_comparison.ipynb`, cell 7; `models/outputs/comparison/results.json` |
| Full-scene inference, pseudo-label check, roads | `notebooks/nzdf_flood_product.ipynb`, cells 6–13 |
| External validation | `notebooks/nzdf_flood_product.ipynb`, cell 15; `models/outputs/nzdf/external_validation.csv` |
| Miss analysis | `notebooks/nzdf_flood_product.ipynb`, cell 17; `reference_missed` layer; `reference_misses.png` |
| Maps for figures | `models/outputs/nzdf/full_scene_prediction.png`, `road_impact_map.png`, `reference_misses.png` |

The product notebook needs the full 60-epoch checkpoint (`outputs/unet_best.pt`, epoch 51, threshold 0.30). A leftover 1-epoch checkpoint gave meaningless results (659 km² "flooded", IoU 0.03), and cell 3's warning catches this.
