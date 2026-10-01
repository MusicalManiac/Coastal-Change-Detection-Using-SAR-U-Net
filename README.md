# Coastal Change Detection Using SAR + U-Net

Flood/inundation detection from Sentinel-1 SAR imagery, trained on global cyclone
events and tested on an unseen real-world case, for the GEOG 761 project with
[external partner context: NZ maritime geospatial reconnaissance].

## Project summary
Optical satellite imagery (Sentinel-2) is frequently unusable during extreme
weather due to cloud cover. This project uses Sentinel-1 SAR — which sees
through cloud and darkness — with a U-Net model to detect flooding, aiming to
support reconnaissance prioritisation ("where should we look first?") rather
than safety certification.

## Team & task ownership
| Person  | Focus                                                      | Docs |
|---------|--------------------------------------------------------------|------|
| Nisheeth | Global cyclone event investigation, data sufficiency, risk analysis | `docs/risk-analysis.md` |
| Rata    | Ground-truth/reference data, literature synthesis, presentation & reporting organization            | `docs/literature-review.md` |
| Seb     | NZ regional event investigation (GEE), design-process doc     | `docs/design-process.md` |
| Rhett   | Product concept, demo, extensions                             | `docs/product-concept.md` |

## Approach
- **Training data**: [Kuro Siwo](https://github.com/Orion-AI-Lab/KuroSiwo) — 43 global flood events, multi-temporal Sentinel-1 (2 pre + 1 post per event), used via their existing U-Net training pipeline rather than building one from scratch.
- **Test/validation event**: Cyclone Idai, Beira, Mozambique (March 2019) — chosen for confirmed clean pre/post Sentinel-1 coverage and independent reference data (Copernicus EMS EMSR348 delineation maps).
- **NZ case study**: Cyclone Gabrielle, Hawke's Bay (Feb 2023) — included for operational relevance and as a documented example of real-world data-availability constraints (thin pre-event baseline due to single-satellite Sentinel-1 coverage since Sentinel-1B's 2021 failure).

## Repo structure
See folder READMEs. Large data/model files are **not** stored in this repo — see `data/README.md` and `models/README.md` for the shared Drive links.

## Setup
```bash
git clone https://github.com/MusicalManiac/Coastal-Change-Detection-Using-SAR-U-Net
git clone https://github.com/Orion-AI-Lab/KuroSiwo external/KuroSiwo
cd external/KuroSiwo && pip install -r requirements.txt
```

## Status
Currently in Week 1 of 3: data pipeline and training setup.
