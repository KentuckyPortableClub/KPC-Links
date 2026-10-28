# World W4: GERMANY (DE) (desk, Oct 27 2026)
Grades: A = opened and read, B = search result only, C = inference. Read only; nothing here queried a polygon. Builds on KPC_2fer_Preflight_World_desk.md (W-1 to W-8 not repeated). WDPA never; EEA Natura 2000 fine. Counts are from data/world-key/<CC>.json.
Key: 1,265 parks, 286 no outline, 296 to check, 679 pin outside the outline, 683 saved-only outlines. Sources in key: BfN (national parks, nature parks, nature reserves, biosphere reserves, national natural monuments, FFH, bird protection areas, landscape protection areas).
## 1. Official layers
- **BfN Schutzgebiete** (Bundesamt für Naturschutz) on geodienste.bfn.de (WFS, e.g. https://geodienste.bfn.de/ogc/wfs/...): in key, all 8 types. Licence not read (B); BfN data is normally "Datenlizenz Deutschland" or CC BY (C): chat 2 to confirm one line.
- State portals hold the **authoritative** versions (Länder run nature conservation): e.g. NRW "Kartenlayer Naturparke NRW" (open.nrw, B). Not in key.
## 2. Public / owned land: PARTIAL, by state only
- **No national ownership layer.** Forest ownership is in Länder files and the federal Bundeswaldinventur (statistics, not polygons) (B).
- NRW **Staatswald** parcel layer (Landeseigener Forstbetrieb, 118,000 ha, 13% of NRW forest): https://test.ckan.open.nrw.de/km/dataset/747eced9-9b1b-41ec-b25c-b3f3ca3ed5a1 (A): updated 11 Aug 2025; **no licence named, and a "non_open" flag says true while access is "no limitations"**: contradictory, so ask Wald und Holz NRW before use. No service URL listed.
- Berlin Forsten administrative units (gdi.berlin.de, B): city-state forest = public land.
- BImA (federal real estate agency) holds Bundesforst and military land (B): no open polygon layer found.
- Verdict: **NOT SURE for all pairs** except where a Land publishes state forest AND state parks (NRW, Berlin) → pilot there.
## 3. No outline (286)
- **Recreation Park 182 (162 none):** Stadtpark Speckenbuettel DE-0141, Bürgerpark mit Stadtwald Bremen DE-0142: city parks = never.
- **National Historic Trail 61 (all none), National Recreation Trail 37 (35 none):** Toteiskesselweg DE-0543, Via Nova DE-0590, Saale Horizontale DE-0389, Ith-Hils-Weg DE-0529: hiking trails (lines, no official national layer).
- **Provincial/National Recreation Area 64:** Öjendorfer Park DE-0137 (Hamburg), Tempelhofer Feld DE-0169 (Berlin, former airfield, public body land), Südsee Braunschweig DE-0124, Schönramer Filz DE-0273: lake/leisure areas and bogs; Tempelhofer Feld is one of few where a Land owns it.
- Name pattern: POTA English type words ("Nature Park") appended to German names (Bayerischer Wald Nature Park DE-0011): join worked for most.
## 4. Sea / lake: Wadden Sea National Parks, Lake Constance (Bodensee), Müritz: water-only parts; Südsee Braunschweig is an artificial lake.
## 5. NEW grey areas
| # | Question | My lean |
|---|---|---|
| W4-1 | Germany's **Landschaftsschutzgebiete (LSG)** are huge, mostly private farmland, and BfN has them as a layer; include any pair with an LSG? | NOT SURE kept out unless the other park is state forest (W-2). |
| W4-2 | **Naturparke** (Nature Parks) in the key as parks: whole-line over villages. Same as W-2. | Same. |
## 6. Known-good: BfN 8 layers; NRW Staatswald (after licence check); Berlin Forsten; Tempelhofer Feld polygon. **2-fers I am confident of (C):** Bayerischer Wald National Park DE-0012 inside Bayerischer Wald Nature Park DE-0011 (layered, but the nature park is whole-line private land: NOT SURE per W-2, stated for the Finder's members list only); Eifel National Park DE-0045 vs Hohes Venn-Eifel Nature Park DE-0039 (adjacent, layered where the park lies inside).
## 7. READY / NOT READY: **NOT READY for public pairs** (no ownership layer); READY for members-only "possible" list from BfN. Missing: Länder forest layers (start NRW + Berlin + Bavaria Staatsforsten), licence line for BfN.
