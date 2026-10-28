# Canada East: QUÉBEC (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only. I cannot query polygons, so "covers" comes from the publisher text. CANADA RULES: federal first; WDPA never; plain Crown land is not a park; water layer = National Hydro Network (NHN).
Key: 839 parks, 398 with no outline (143 Regional Parks, 87 Recreation Parks, 76 NHS, 43 Nature Reserves, 20 Historic Sites).

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| **All provincial protected areas** (national parks, marine park, humanized landscape, nature reserves on private land, ecological reserves, biodiversity reserves, aquatic reserves, national wildlife reserves, wildlife refuges, biological refuges, migratory bird refuges, exceptional forest ecosystems, voluntary conservation natural environments, plus OECMs) | Esri REST https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer ; WMS …/services/Biodiversite/Aires_protegees/MapServer/WMSServer ; SHP/FGDB/GPKG on donneesquebec.ca/recherche/dataset/aires-protegees-au-quebec (A) | Ministère de l'Environnement, Lutte contre les changements climatiques, Faune et Parcs | metadata modified 2026-09-23, data files 2026-03-31, first released 2018 (A); **CC-BY 4.0** | in key (the 'Québec …' keys) |
| Regional / municipal parks (Montréal grands parcs, Québec City, Laval…) | Données Québec "vmtl-grands-parcs…" (~15 parks, CC-BY 4.0, Gap desk); no provincial list of "parcs régionaux" found | cities / MRCs | varies | PARTLY |
| SÉPAQ parks (national parks, réserves fauniques) | the same register; SÉPAQ publishes no separate open layer (B) | | | |
| ZECs and pourvoiries | MFFP "Territoires fauniques" on Données Québec (B, not opened) | MFFP | CC-BY 4.0 (B) | NO. **Hunting/fishing territories on Crown land: NOT parks unless a POTA number says so.** |
| Trails (Route verte, Sentiers) | none official | | | NO |

## 2. Parks with no outline (398)
- **Regional Parks (143)** are the main hole: Mount Royal Regional Park CA-0511 and Parc Angrignon CA-0962 are in the Montréal dataset (name: "Parc du Mont-Royal", "Parc Angrignon" — **French/English mismatch**: our key says "Mount Royal Regional Park"). Match by French name with accents removed. Most others (Parc-nature de …, parcs régionaux of MRCs) have no provincial layer: UNCOVERED.
- **Recreation Parks (87):** municipal; same.
- **76 NHS + 20 Historic Sites:** pin only (Château Frontenac CA-1945 etc.).
- **43 Nature Reserves:** most are in the register ("réserve naturelle en milieu privé", **private land with a conservation servitude**: see section 4). The ones listed as "Zec …" or "Lac-du-Portage" (CA-2095), "Portageur" (CA-2210) in our key may be name mismatches.
- Boisé de Marly Forest Reserve, Morgan Arboretum: municipal/university: UNCOVERED.

## 3. Trails and access
None official. Parc national entrances come from SÉPAQ pages (B).

## 4. Tricky land (rule 14)
- **Réserves naturelles en milieu privé:** private land protected by agreement but often closed to the public. Matches Brandon's ruling: not park land except its own number, and rule 3 (public + open) usually fails. **Grey area CAE-2.**
- **La Vérendrye:** Réserve faunique La Vérendrye CA-1027 (QC, joined) vs La Verendrye Provincial Park CA-0259 (ON, NONE): different provinces; the accent mismatch is on the Ontario side. Do not join across the border.
- **Mingan CA-0056, Saguenay-St. Lawrence Marine Park CA-0086:** water/islands, rule 9. Saguenay marine park overlaps Fjord-du-Saguenay NP CA-0495 on the shore (provincial + federal): likely "same land, two numbers" at the fjord mouth (C).
- **Nature reserves of indigenous or co-management status** (Atikamekw, Innu territories): **grey area CAE-3.**

## 5. KNOWN-GOOD layers
1. Aires_protegees MapServer (all designations)
2. Données Québec Montréal grands parcs
3. Parks Canada places FeatureServer; CPCAD
4. NHN (federal) — Québec also has "Réseau hydrographique" (BDTQ) but I did not open it (B)

## 6. 2-fers to expect
Confident (C): Saguenay-St. Lawrence MP vs Fjord-du-Saguenay NP; Forillon NP CA-0022 vs Réserve de biodiversité on the Gaspé edge. Hard: Mont-Tremblant NP CA-0509 vs ZEC and pourvoirie neighbours (not parks); Frontenac NP CA-0496 vs the Quebec "Parc régional" belts. **Name pitfall:** QC Frontenac NP (CA-0496) is not Ontario's Frontenac PP (CA-0219).
