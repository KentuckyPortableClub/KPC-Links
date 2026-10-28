# World W9: NORWAY (NO) (desk, Oct 27 2026)
Grades: A = opened and read, B = search result only, C = inference. Read only; nothing here queried a polygon. Builds on KPC_2fer_Preflight_World_desk.md (W-1 to W-8 not repeated). WDPA never; EEA Natura 2000 fine. Counts are from data/world-key/<CC>.json.
Key: 3,337 parks, 236 no outline, 57 to check, 514 pin outside; sources: EEA Natura 2000 (Norway has none) + CDDA only.
## 1. Official layers
- **Naturvernområder** (Miljødirektoratet): https://data.norge.no/en/datasets/65392b86-0c24-4ee1-824e-78c2a421f342/naturvernomrader (A). **NLOD 2.0 (open)**; GML/GeoJSON/GDB downloads, REST https://kart.miljodirektoratet.no/arcgis/rest/services/vern/mapserver, WMS https://kart.miljodirektoratet.no/arcgis/services/vern/mapserver/WMSServer, Atom https://nedlasting.miljodirektoratet.no/miljodata/ATOM/Datasett/Vern.xml . Updated 16 Feb 2026 (A). Covers all protected areas incl. Svalbard, with regulation links. **Better than the EEA copy; not in key. TOP ADD.**
## 2. Public / owned land: YES, SMALL
- **Statlig sikra friluftslivsområder** (state-secured outdoor recreation areas): https://data.norge.no/en/datasets/8aa2cc6d-af4e-3d9b-812c-966a4d50c2ab/friluftslivsomrader-statlig-sikra (A): NLOD 2.0, last modified Jan 2021, "continuously updated"; REST https://kart.miljodirektoratet.no/arcgis/rest/services/friluftsliv_statlig_sikra/mapserver ; the state buys, or holds a servitude, or a registered restriction: **three kinds, ownership not stated, so only some are state-owned**.
- **Statskog** (state forest company, ~ a third of Norway) and statsallmenning (B): no open polygon layer found; Statskog has a public map.
- Right to roam (allemannsretten) is NOT public land (W-3).
## 3. No outline (236)
- **National Recreation Area 159 (all none):** Hell Beach NO-1666, Heiområdet NO-2530: friluftsområder (matches "statlig sikra" layer: probably joinable).
- **Park 39 (all none):** Gausel Fritidsgård NO-2070, Frognerparken NO-2514: city parks = never.
- **National Military Park 14:** Fredriksten festning NO-2532, Kvalvik fort NO-2560: fortress sites: historic = never.
- National Wildlife Area 104 (15 none): Andelven, Nessa og Risa NO-2605, Landavatnet NO-2673; Nature Reserve 2,673 (12 none): Århanemyra NO-0015.
## 4. Sea / lake: marine protected areas, fjords, Svalbard seas: water-only; Rondane, Jotunheimen mountain lakes.
## 5. NEW grey areas
| # | Question | My lean |
|---|---|---|
| W9-1 | **Svalbard and Jan Mayen** protected areas (in Naturvernområder): park numbers there? | Include if numbered; very remote, no road. |
| W9-2 | **Statlig sikra** with servitude only: public use by law but private owner. | Count as public (use right is public), mark "by agreement". |
## 6. Known-good: Naturvernområder (NLOD); Statlig sikra friluftsliv; kartlagte friluftsområder. **2-fers (C):** Jotunheimen NO-0913 vs adjacent landscape-protection areas; Dovre NO-0289 vs Dovrefjell-Sunndalsfjella NO-0290 (older and newer national park: same land, two park numbers, check).
## 7. READY after adds (Naturvernområder replaces the EEA copy). Ownership: only the state-secured layer; the rest NOT SURE.
