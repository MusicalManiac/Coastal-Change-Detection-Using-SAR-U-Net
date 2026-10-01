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

---

## 3. Data Processing Architecture

[ Sentinel-1 GRD Data ] ---> [ Speckle Filter & Terrain Correction ] ---> [ Co-Registered Pre/Post Stack ]
|
v
[ Client Vector Outputs ] <--- [ Binary Mask Post-Processing ] <--- [ U-Net Inference Engine ]

---

## 4. Technical Choices & Rationales

### AI/ML Model Selection
- **Selected Method:** U-Net Convolutional Neural Network
- **Justification:** Preserves sharp boundary edge features (vital for narrow flood channels/coastal margins) and spatial convolutions naturally suppress SAR speckle noise compared to single-pixel thresholding.

### Satellite Platform
- **Selected Sensor:** Sentinel-1 C-band SAR ($\text{VV} + \text{VH}$)
- **Justification:** Active microwave sensor penetrates cloud cover, heavy rain, and operates day/night.

---

## 5. Team Task Log & Contributions

| Date | Contributor | Task / Component Completed | Notes / Blockers |
| :--- | :--- | :--- | :--- |
| YYYY-MM-DD | [Name] | Created initial repository structure & GEE script | Completed Task 1 & 2 setup |
| YYYY-MM-DD | [Name] | Preprocessed Sentinel-1 imagery for Cyclone Gabrielle | Calibrated to $\sigma^0$ dB |
| YYYY-MM-DD | [Name] | Established Otsu change-detection baseline | IoU baseline = X.XX |