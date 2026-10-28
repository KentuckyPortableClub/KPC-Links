# World W5: POLAND (PL) (desk, Oct 27 2026)
Grades: A = opened and read, B = search result only, C = inference. Read only; nothing here queried a polygon. Builds on KPC_2fer_Preflight_World_desk.md (W-1 to W-8 not repeated). WDPA never; EEA Natura 2000 fine. Counts are from data/world-key/<CC>.json.
Key: 2,982 parks, 115 no outline, 176 to check, 402 pin outside. Sources in key: EEA Natura 2000, EEA nationally designated areas, Silesia ORSIP complexes (copy, licence not stated). Last run: all rows saved-only because GDOŚ refused GitHub (403).
## 1. Official layers
- **GDOŚ** (General Directorate for Environmental Protection) protected forms: the national geoportal lists only an **ATOM download** for protected areas http://mapy.geoportal.gov.pl/wss/service/ATOM/httpauth/atom/PS (A; licence: the geoportal page names none; terms are on its Regulamin page). Also a GDOŚ metadata catalogue (bankdanych.gdos.gov.pl, B) and a **MPP FormyOchronyPrzyrody** ArcGIS service on powietrze.gios.gov.pl (https://powietrze.gios.gov.pl/arcgis/rest/services/MPP/FormyOchronyPrzyrody/MapServer, B: listed, not opened) which may avoid the 403 problem.
- EEA layers: fine, already live.
## 2. Public / owned land: YES, THE BEST IN CONTINENTAL EUROPE
**Lasy Państwowe (State Forests) Forest Data Bank (BDL)** publishes forest boundaries by ownership:
- WMS by form of ownership: https://mapserver.bdl.lasy.gov.pl/ArcGIS/services/WMS_BDL_kat_wlasnosci/MapServer/WMSServer (A: layers split into State Forests land and other forms of ownership)
- WFS: https://wfs.bdl.lasy.gov.pl/geoserver/BDL/ows (RDLP, forest districts, forest ranges, subareas); OGC API Features https://ogcapi.bdl.lasy.gov.pl ; WMTS by ownership (A, same page)
- **Licence/terms: not stated on the pages I read (A).** Contact the BDL operator or read the portal Regulamin.
- State Forests land is the state's land and, by the Forest Act, **open to the public** for walking (with exceptions: nature reserves, forest closures). So Polish national forests are agency land → rule 14 can run, as in the US.
## 3. No outline (115)
- **Nature and Landscape Complex 246 (213 none):** Cieszanów PL-0095, Głogi PL-0116: Zespół przyrodniczo-krajobrazowy, a regional designation; layers by RDOŚ/voivodeship (the gov.pl "RDOŚ Dane i metadane" pages list services per region) — not in EEA.
- **Ecological Site 25 (all none):** Uroczysko Kowadza PL-0997, Góra Hugona PL-1300 (użytek ekologiczny): small, municipal-level; per-region data.
- Natural Monument 5 (Aleja Drzew w Ceranowie PL-0300, Pomnik Przyrody PL-0397): single trees: pin only.
- Protected Landscape Area 362 (29 none): Poleski PL-0047, Chełmski PL-0078: whole-line parks (W-2).
## 4. Sea / lake: Baltic (Słowiński, Woliński parks coast), Masurian lakes (Mamry), Wigry: water-only.
## 5. NEW grey areas
| # | Question | My lean |
|---|---|---|
| W5-1 | **State Forests (Lasy Państwowe) land inside a national park or reserve** (Białowieża PL-0002, Lasy Naturalne Puszczy Białowieskiej PL-0008): the forest district is the owner but access is restricted in the reserve core. | Same land, two park numbers; add closure line. |
| W5-2 | **"Forest closures" (zakazy wstępu)** published on BDL (zakazywstepu.bdl.lasy.gov.pl): temporary bans. | Optional closures source; do not claim open. |
## 6. Known-good: GDOŚ ATOM / FormyOchronyPrzyrody; EEA; BDL ownership WMS + WFS. **2-fers (C):** Białowieża NP PL-0002 vs Lasy Naturalne Puszczy Białowieskiej Nature Reserve PL-0008 (same forest, layered); Biebrzański NP PL-0194 vs Natura 2000 sites; Bory Tucholskie NP PL-0005 vs its Natura 2000 site.
## 7. READY / NOT READY: **READY after one licence check** for pairs on State Forests land; missing: BDL licence, GDOŚ live copy (the 403 was GitHub-specific), regional complexes layer.
