# Canada East: SUMMARY (chat 8 desk, Oct 27 2026)
Six files here (ON QC NB NS PE NL). Read only; nothing changed. Grades: A opened, B search only, C inference. I could not query polygons.

## READY / GAPS
| Prov | Parks / no outline | Verdict | Main reason |
|---|---|---|---|
| ON | 1158 / 255 | READY after fuzzy match | provincial parks + conservation reserves covered; conservation authorities partly unread; 85 NHS pin-only |
| QC | 839 / 398 | GAPS (regional parks) | one excellent provincial register (CC-BY 4.0, updated 2026), but 143 regional + 87 recreation parks are municipal |
| NB | 562 / 256 | READY (small gaps) | GeoNB provincial parks (OGL-NB); portage-route "parks" are lines |
| NS | 489 / 168 | GAPS | Protected Areas System has only "selected" provincial parks; 38 beach/roadside parks uncovered |
| PE | 53 / 36 | GAPS | no open provincial park polygons found; CPCAD fallback |
| NL | 134 / 67 | GAPS + LICENCE | provincial file is a 2016 zip with **no redistribution allowed** |

## Top adds for chat 2
1. **CPCAD** (https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer, layer 0): federal, "freely available", licence not stated on the page (A); use as fallback for PE, NL, NS provincial parks.
2. **QC Aires_protegees** (geo.environnement.gouv.qc.ca …/Biodiversite/Aires_protegees/MapServer): already in key, CC-BY 4.0, refreshed 2026-03; check the key points at the current version.
3. **QC municipal parks**: Montréal grands parcs (CC-BY 4.0); search Québec City, Laval, Longueuil in Données Québec.
4. **Parks Canada places** (services2.arcgis.com/wCOMu5IS7YdSyPNx …/vw_Places_Public_lieux_public_APCA/FeatureServer/0): national parks, reserves, marine areas only (no NHS); licence ca-ogl-lgo; says "not for defining boundaries".
5. **NS Protected Areas System** (data.novascotia.ca ticv-5du5, GeoJSON export).
6. **ON conservation authorities**: finish Upper Thames, Nottawasaga, Long Point.
7. **NHN water** (OGL-Canada, 1:50,000, modified 2022-11): WMS https://maps.geogratis.gc.ca/wms/hydro_network_en; GPKG https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nhn_rhn/gpkg_en/CA/. Gives lakes, rivers, canals, islands for the shoreline tests.
8. **NB Protected Natural Areas** (find the GeoNB service).

## Name mismatches (look missing, probably just named differently)
- **La Verendrye Provincial Park (ON, CA-0259)**: key has no accent; the Québec Réserve faunique La Vérendrye (CA-1027) is a different park across the border. Do not join across provinces.
- **Mount Royal Regional Park (CA-0511)** = "Parc du Mont-Royal"; **Parc Angrignon (CA-0962)**: English suffix words in the key, French names in the dataset.
- Frontenac: QC Frontenac NP (CA-0496) is not Ontario's Frontenac PP (CA-0219).
- NB/NS "X Recreation Park", "X Nature Reserve": suffix words in key, not in layer.
- Rule for chat 2: match inside the **same province**, drop accents and the English type word, then try the French form.

## NEW grey areas for Brandon (not in SE/MW/NE/SC2/MTN/PAC lists)
| # | Question | My lean |
|---|---|---|
| CAE-1 | Ontario provincial parks inside First Nations treaty/claim areas (Algonquin CA-0138, Killarney CA-0252): count as normal parks? | Yes, the park is where the designation legally applies; note nothing. |
| CAE-2 | Québec "réserves naturelles en milieu privé" (private land, servitude) e.g. Lac-du-Portage CA-2095, Portageur CA-2210: parks? | Not park land except own number; usually fails "public + open" (NOT SURE). |
| CAE-3 | Québec nature reserves under Indigenous co-management. | Same as normal; flag source. |
| CAE-4 | Portage routes and canal lines (Beaubassin Portage CA-6446, Petitcodiac–Washademoak CA-6492, Meductic-Eel River CA-6499, Trent-Severn CA-4889, Rideau Canal CA-4882): line rules? | Line parks, lines = 100 ft; Trent-Severn and Rideau also need NHN water. |
| CAE-5 | Kejimkujik NP + Seaside Adjunct (CA-0042, CA-0043), co-managed with Mi'kmaq. | Normal park. |
| CAE-6 | Torngat Mountains / Mealy Mountains (Nunatsiavut / Innu). | Normal park. |
| CAE-7 | **Redistribution:** NL provincial file forbids copying to third parties; PE may be licensed. Do we read it and publish only our derived outlines, or skip it? | Skip it; use CPCAD. |
| CAE-8 | Municipal "Recreation Parks" with POTA numbers (NB North Head Park CA-0776). Brandon's rule says city parks never; do numbered ones count? | Keep out unless Brandon rules otherwise. |

## What is solid, what is not
Solid (A): QC register fields/licence/dates, Parks Canada places licence, NHN licence and links, NB parks licence, NL file terms, NS PAS description, ON park service description. Not solid: CPCAD licence (not stated), ON licence on the AGOL service, NS licence terms, PE (no layer found), most 2-fer predictions (B/C).
- 2026-10-27 (desk, Round 4): QC/ON/NB/NS holes sorted (never / pin / mismatch / real layer); about 190 of 1,077 need a layer: ON conservation-authority lands (~87), NS provincial parks (38), NB nature preserves (~25). See KPC_BigHoles_desk.md 'ROUND 4'.
