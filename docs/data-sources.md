# Data Sources

Data used in the GEOG 761 project *Coastal Change Detection Using Sentinel-1 SAR and U-Net*. Table A is for the report's Methods section; Table B is optional supporting detail. References follow APA 7th edition.

## Table A. Data sources used in the flood-mapping pipeline

| Data | Provider | Resolution | Details | Use | Reference |
|---|---|---|---|---|---|
| Sentinel-1 SAR (GRD) | ESA Copernicus, via Google Earth Engine | 10 m | C-band radar, IW mode, VV and VH polarisation, in dB; pre-processed by Earth Engine (thermal noise removal, calibration, terrain correction); 30 m focal mean applied to reduce speckle | Model input: before/after image pairs for training (Gabrielle) and testing (Idai, Dovi, Ruby, Gretel) | Torres et al. (2012); European Union/ESA/Copernicus (n.d.); Gorelick et al. (2017) |
| JRC Global Surface Water v1.4 | EC JRC / Google, via Google Earth Engine | 30 m | How often each pixel was water, 1984–2021; pixels water more than 80% of the time treated as permanent water | Removes permanent water (sea, lakes, rivers) from the training labels | Pekel et al. (2016) |
| Satellite detected waters, Cyclone Idai | World Food Programme, via Humanitarian Data Exchange | ~95 m | Maximum flood extent mapped from Sentinel-1, 12–21 March 2019 | Independent reference map for the Idai accuracy test | World Food Programme (2019) |
| Cyclone Gabrielle flood extent | Hawke's Bay Regional Council | Vector polygons | Maximum flood extent, 13–15 February 2023, from photos, video, satellite imagery, building inspections and ground contours | Independent reference map for the Gabrielle accuracy test | Hawke's Bay Regional Council (n.d., 2025) |
| NZ Road Centrelines (Topo, 1:50k) | Toitū Te Whenua Land Information New Zealand, via LINZ Data Service | 1:50,000 vector | National road network | Identifies roads crossed by predicted flooding | Toitū Te Whenua Land Information New Zealand (n.d.) |
| Sentinel-2 optical imagery | ESA Copernicus, via Copernicus Browser | 10 m | Optical (visible light) passes over Napier, 8–22 February 2023, with cloud cover | Shows that cloud blocked the optical view near the Gabrielle flood peak (motivation) | Drusch et al. (2012); Copernicus Data Space Ecosystem (n.d.) |

*Optional row, only if the report explains the reference switch:*

| Data | Provider | Resolution | Details | Use | Reference |
|---|---|---|---|---|---|
| EMSR348 flood delineation | Copernicus Emergency Management Service | Vector polygons | Flood extent mapped during the Idai emergency, Beira (AOI03) | First Idai reference considered; replaced by the WFP/HDX map | Copernicus Emergency Management Service (2019) |

## Table B. Sentinel-1 image pairs (optional supporting detail)

| Event | Area | Before image | After image | Role |
|---|---|---|---|---|
| Cyclone Gabrielle | Napier and Esk Valley, Hawke's Bay | 21 Jan 2023 | 14 Feb 2023, 07:07 UTC (about 8 pm NZDT, near the flood peak) | Training, validation and test patches; HBRC accuracy test |
| Cyclone Idai | Beira, Mozambique | 18 Feb 2019 | 20 Mar 2019 | Independent accuracy test (WFP/HDX) |
| Cyclone Dovi | Wairarapa | 1 Feb 2022 | 13 Feb 2022 | Predicted flood extent only |
| Cyclone Ruby | East Cape | 3 Dec 2021 | 15 Dec 2021 | Predicted flood extent only |
| Cyclone Gretel | Northland | 7 Mar 2020 | 19 Mar 2020 | Predicted flood extent only |

Gabrielle uses relative orbit 81 (ascending), which covers the whole area on both dates. Dates are satellite acquisition dates (UTC).

## Notes for the report

- **Credit lines for maps and figures.** Copernicus asks for *"Contains modified Copernicus Sentinel data (2019–2023)"* (images from 2019, 2020, 2021, 2022 and 2023 are used); Earth Engine asks for *"Source: EC JRC/Google"* on maps that use the JRC water layer.
- **The Idai reference shares a sensor with the model.** The WFP/HDX map was made from Sentinel-1, which is worth a sentence in the Discussion.
- **HBRC is a maximum extent over three days; the radar is one snapshot.** This explains much of the missed flooding (Discussion).

---

## References

Copernicus Data Space Ecosystem. (n.d.). *Copernicus Browser* [Web application]. European Space Agency. https://browser.dataspace.copernicus.eu/

Copernicus Emergency Management Service. (2019). *EMSR348: Tropical Cyclone IDAI in Mozambique* [Data set]. European Commission. https://mapping.emergency.copernicus.eu/activations/EMSR348/

Drusch, M., Del Bello, U., Carlier, S., Colin, O., Fernandez, V., Gascon, F., Hoersch, B., Isola, C., Laberinti, P., Martimort, P., Meygret, A., Spoto, F., Sy, O., Marchese, F., & Bargellini, P. (2012). Sentinel-2: ESA's optical high-resolution mission for GMES operational services. *Remote Sensing of Environment, 120*, 25–36. https://doi.org/10.1016/j.rse.2011.11.026

European Union/ESA/Copernicus. (n.d.). *Sentinel-1 SAR GRD: C-band synthetic aperture radar ground range detected, log scaling* (COPERNICUS/S1_GRD) [Data set]. Google Earth Engine Data Catalog. https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD

Gorelick, N., Hancher, M., Dixon, M., Ilyushchenko, S., Thau, D., & Moore, R. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment, 202*, 18–27. https://doi.org/10.1016/j.rse.2017.06.031

Hawke's Bay Regional Council. (n.d.). *Cyclone Gabrielle flooding* [Interactive map]. https://hbrc.govt.nz/our-council/cyclone-gabrielle-response/cyclone-gabrielle-flooding

Hawke's Bay Regional Council. (2025, February 27). *Cyclone Gabrielle flood map now available*. https://hbrc.govt.nz/our-council/news/article/1802/cyclone-gabrielle-flood-map-now-available

Pekel, J.-F., Cottam, A., Gorelick, N., & Belward, A. S. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature, 540*(7633), 418–422. https://doi.org/10.1038/nature20584

Toitū Te Whenua Land Information New Zealand. (n.d.). *NZ road centrelines (Topo, 1:50k)* [Data set]. LINZ Data Service. https://data.linz.govt.nz/layer/50329-nz-road-centrelines-topo-150k/

Torres, R., Snoeij, P., Geudtner, D., Bibby, D., Davidson, M., Attema, E., Potin, P., Rommen, B., Floury, N., Brown, M., Navas Traver, I., Deghaye, P., Duesmann, B., Rosich, B., Miranda, N., Bruno, C., L'Abbate, M., Croci, R., Pietropaolo, A., . . . Rostan, F. (2012). GMES Sentinel-1 mission. *Remote Sensing of Environment, 120*, 9–24. https://doi.org/10.1016/j.rse.2011.05.028

World Food Programme. (2019). *Mozambique satellite detected waters, Cyclone Idai* [Data set]. Humanitarian Data Exchange. https://data.humdata.org/dataset/mozambique-flood-detected-waters-cyclone-idai
