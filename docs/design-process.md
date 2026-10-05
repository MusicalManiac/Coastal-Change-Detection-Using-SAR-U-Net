# NZDF Sentinel-1 SAR Coastal Flood Detection — Design Process Document

## 1. Project Overview & Stakeholder Need
- **Client:** New Zealand Defence Force (NZDF)
- **Problem Statement:** Operational blindness during extreme storm events due to heavy cloud cover obscuring optical satellites during search and rescue / amphibious landing missions.
- **Proposed Solution:** Automated pipeline pairing Sentinel-1 C-band SAR backscatter with a U-Net segmentation model to map flood boundaries through cloud cover.

---

## 2. Event & Data Availability Matrix

| Event Name | Region | Event Date | Pre-Event S1 Scene | Post-Event S1 Scene | Local Timestamp (NZDT) | Orbit Pass | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cyclone Gabrielle** | Hawke's Bay | Feb 14, 2023 | 2023-02-01 17:30 UTC | 2023-02-13 17:30 UTC | Feb 14, 06:30 AM NZDT | Descending | **PASS** (Matched orbit, peak landfall) |
| **Cyclone Idai** | Beira, Mozambique | Mar 14, 2019 | TBC (Nisheeth) | TBC – closest to 2019-03-16 14:41 UTC | — | TBC | **Test event** (EMS reference: EMSR348 AOI03) |

---

## 3. Reference (Ground-Truth) Data for Model Evaluation — Cyclone Idai, Beira

**Author:** Rata | **Date:** 5 October 2026 | **Notebook:** `notebooks/01_reference_data.ipynb`

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
3. Exported a single cleaned file, `data/idai/reference_clean/idai_beira_flood_reference.gpkg`, with three layers:
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
- [ ] Which Sentinel-1 acquisition over Beira is closest to 16 March 2019? (Nisheeth)
- [ ] Is Cyclone Idai one of the 43 Kuro Siwo training events? If so, it cannot be used as a fair test event. (Sebastian / Nisheeth)

---

## 4. Data Processing Architecture

[ Sentinel-1 GRD Data ] ---> [ Speckle Filter & Terrain Correction ] ---> [ Co-Registered Pre/Post Stack ]
|
v
[ Client Vector Outputs ] <--- [ Binary Mask Post-Processing ] <--- [ U-Net Inference Engine ]

---

## 5. Technical Choices & Rationales

### AI/ML Model Selection
- **Selected Method:** U-Net Convolutional Neural Network
- **Justification:** Preserves sharp boundary edge features (vital for narrow flood channels/coastal margins) and spatial convolutions naturally suppress SAR speckle noise compared to single-pixel thresholding.

### Satellite Platform
- **Selected Sensor:** Sentinel-1 C-band SAR ($\text{VV} + \text{VH}$)
- **Justification:** Active microwave sensor penetrates cloud cover, heavy rain, and operates day/night.

---

## 6. Team Task Log & Contributions

| Date | Contributor | Task / Component Completed | Notes / Blockers |
| :--- | :--- | :--- | :--- |
| YYYY-MM-DD | [Name] | Created initial repository structure & GEE script | Completed Task 1 & 2 setup |
| YYYY-MM-DD | [Name] | Preprocessed Sentinel-1 imagery for Cyclone Gabrielle | Calibrated to $\sigma^0$ dB |
| YYYY-MM-DD | [Name] | Established Otsu change-detection baseline | IoU baseline = X.XX |
| 2026-10-05 | Rata | Sourced and processed reference flood data for Cyclone Idai (Copernicus EMS EMSR348, AOI03 Beira); notebook `01_reference_data.ipynb`, cleaned output `idai_beira_flood_reference.gpkg` | AOI16 has no flood delineation. Need S1 scene closest to 16 Mar 2019 and confirmation Idai isn't in Kuro Siwo training set |
