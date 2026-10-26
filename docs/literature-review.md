# Literature Review and References

Background literature for the GEOG 761 project *Coastal Change Detection Using Sentinel-1 SAR and U-Net*: the problem, the operational context, and why SAR and U-Net were chosen. Data sources are listed separately in `data-sources.md`. References follow APA 7th edition.

> Every reference below has been checked against its publisher or official page (October 2026).

---

## 1. The problem: cloud cover and rapid information during disasters

Satellite imagery is now central to disaster management because it shortens the time between impact and response, but access, legal and AI-accountability gaps remain (Brennan, 2026). Optical imagery is often blocked by cloud during the severe weather that causes flooding. Gap-filling methods that rely on historical water records struggle in extreme, unprecedented floods (Li et al., 2025).

## 2. Operational context: NZDF disaster response

NZDF responses show why a rapid, wide-area first look matters:

- **Kaikōura earthquake, 2016.** HMNZS Wellington was sent to carry out a rapid environmental assessment so landing craft and ships' boats could operate safely. It received minimal information about the impact during the 54 hours between re-tasking and arrival, and the seabed and foreshore were raised by more than four metres (Headquarters Joint Forces New Zealand, 2021, p. 25). HMNZS Canterbury offloaded 214 tonnes of aid by helicopter and carried 640 evacuees; NZDF evacuated nearly 1,000 people in total (New Zealand Defence Force [NZDF], n.d.-b). *Note: an earthquake, not a cloud-cover case; useful only as evidence that early coastal information matters.*
- **HMNZS Canterbury** accommodates up to 365 personnel and carries two 23 m, 60-tonne landing craft (NZDF, n.d.-a).
- **Cyclone Winston, Fiji, 2016.** HMNZS Wellington arrived first with 60 tonnes of aid and identified routes and anchorages; Canterbury followed with 106 tonnes and about 300 personnel, using landing craft to reach remote islands (NZDF, 2016).
- **Cyclone Gabrielle, 2023.**
  - Rissington's only connecting bridge, over the Mangaone River, was destroyed; Army engineers built a pulley system to resupply the community (NZDF, 2023a).
  - Dartmoor was cut off to the north and south; the Air Force flew in two tonnes of food (NZDF, 2023c).
  - Waipiro and Te Puia Springs were reported inaccessible and low on food and diesel. HMNZS Manawanui reached Waipiro, but surf made a supply transfer unsafe; supplies were delivered via Tokomaru Bay (NZDF, 2023b). *Do not say Waipiro was resupplied.*
- **Tonga eruption and tsunami, 2022.** HMNZS Wellington's hydrographers and divers surveyed shipping lanes, harbours and wharves so aid vessels could operate safely (NZDF, 2022). Detailed surveys like this remain necessary; a satellite product only screens where to look first.

A Navy contact (personal communication, 2026) described the current sequence: maritime patrol aircraft photograph the area first, then hydrographers make an in-person rapid assessment. Satellite imagery is used where available but is not always available. *APA 7: personal communications are cited in text only and are not in the reference list.*

## 3. Sentinel-1 SAR for flood mapping

C-band SAR does not depend on sunlight and sees through cloud. Smooth open water reflects the radar pulse away from the sensor, so flooded land appears dark. Twele et al. (2016) built a fully automated Sentinel-1 flood-mapping chain on this principle. Clement et al. (2018) mapped the 2015–16 winter floods near York, UK, by comparing pre- and post-flood Sentinel-1 images (change detection), and compared the VV and VH polarisations. Comparing before and after images is what lets new flooding be told apart from surfaces that are always dark, such as permanent water.

## 4. U-Net and deep learning for SAR flood segmentation

U-Net is an encoder–decoder network whose skip connections combine coarse context with fine spatial detail, giving pixel-level segmentation (Ronneberger et al., 2015). Nemni et al. (2020) tested fully convolutional networks, including a U-Net with a ResNet-34 encoder (the same architecture as this project), on Sentinel-1 flood mapping for UNOSAT's emergency response. The networks clearly outperformed an automated threshold method and cut the time to produce a flood map by about 80%.

## 5. Training datasets

MMFlood provides Sentinel-1 flood delineation data across many global events (Montello et al., 2022). Kuro Siwo is a larger global, multi-temporal Sentinel-1 flood dataset and was the group's original training plan (Bountos et al., 2024). At around 700 GB it was too large to download and train on with the time and computing available, so the model was trained on a single New Zealand event instead. *Note: cite these only when explaining which datasets were considered and why the plan changed.*

---

## References

Bountos, N. I., Sdraka, M., Zavras, A., Karasante, I., Karavias, A., Herekakis, T., Thanasou, A., Michail, D., & Papoutsis, I. (2024). Kuro Siwo: 33 billion m² under the water. A global multi-temporal satellite dataset for rapid flood mapping. In *Advances in Neural Information Processing Systems 37* (pp. 38105–38121). https://doi.org/10.52202/079017-1204

Brennan, A. M. (2026, February 23). *Satellite imaging is now vital for disaster management. But there are dangerous gaps in our systems*. University of Waikato. https://www.waikato.ac.nz/news-events/news/satellite-imaging-is-now-vital-for-disaster-management/

Clement, M. A., Kilsby, C. G., & Moore, P. (2018). Multi-temporal synthetic aperture radar flood mapping using change detection. *Journal of Flood Risk Management, 11*(2), 152–168. https://doi.org/10.1111/jfr3.12303

Headquarters Joint Forces New Zealand. (2021). *Humanitarian assistance and disaster relief (HADR) aide memoire* (2nd ed.). New Zealand Defence Force. https://www.nzdf.mil.nz/assets/Uploads/DocumentLibrary/20210806-HADR-Aide-Memoire-2nd-Edition.pdf

Li, Z., Xu, S., & Weng, Q. (2025). TerrainFloodSense: Improving seamless flood mapping with cloudy satellite imagery via water occurrence and terrain data fusion. *International Journal of Applied Earth Observation and Geoinformation, 144*, Article 104855. https://doi.org/10.1016/j.jag.2025.104855

Montello, F., Arnaudo, E., & Rossi, C. (2022). MMFlood: A multimodal dataset for flood delineation from satellite imagery. *IEEE Access, 10*, 96774–96787. https://doi.org/10.1109/ACCESS.2022.3205419

Nemni, E., Bullock, J., Belabbes, S., & Bromley, L. (2020). Fully convolutional neural network for rapid flood segmentation in synthetic aperture radar imagery. *Remote Sensing, 12*(16), Article 2532. https://doi.org/10.3390/rs12162532

New Zealand Defence Force. (n.d.-a). *HMNZS Canterbury*. https://www.nzdf.mil.nz/navy/our-equipment/ships-and-watercraft/hmnzs-canterbury/

New Zealand Defence Force. (n.d.-b). *Kaikōura: A community cut off*. https://www.nzdf.mil.nz/nzdf/what-we-do/humanitarian-assistance-and-disaster-relief/a-community-cut-off/

New Zealand Defence Force. (2016, February 21). *When Winston blew into town*. https://www.nzdf.mil.nz/navy/what-we-do/humanitarian-assistance-and-disaster-relief/when-winston-blew-into-town/

New Zealand Defence Force. (2022, February 11). *NZ Navy ships to return from Tonga after roles in relief efforts*. https://www.nzdf.mil.nz/media-centre/news/nz-navy-ships-to-return-from-tonga-after-roles-in-relief-efforts/

New Zealand Defence Force. (2023a, February 19). *Army engineers fashion pulley system to help resupply town*. https://www.nzdf.mil.nz/media-centre/news/engineers-fashion-pulley-system-to-help-resupply-town/

New Zealand Defence Force. (2023b, February 17). *Navy delivers to cut-off East Coast*. https://www.nzdf.mil.nz/media-centre/news/navy-delivers-to-cut-off-west-coast/

New Zealand Defence Force. (2023c, February 28). *NZ Army proving routes and supplying communities*. https://www.nzdf.mil.nz/media-centre/news/nz-army-proving-routes-and-supplying-communities/

Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional networks for biomedical image segmentation. *Lecture Notes in Computer Science, 9351*, 234–241. https://doi.org/10.1007/978-3-319-24574-4_28

Twele, A., Cao, W., Plank, S., & Martinis, S. (2016). Sentinel-1-based flood mapping: A fully automated processing chain. *International Journal of Remote Sensing, 37*(13), 2990–3004. https://doi.org/10.1080/01431161.2016.1192304
