# Canada West: SUMMARY (chat 8 desk, Oct 27 2026)
Seven files here (MB SK AB BC YT NT NU). Read only. A = opened, B = search only, C = inference. Same rules as Canada East (federal first, no WDPA, Crown land is not a park, NHN for water).

## READY / GAPS
| Prov | Parks / no outline | Verdict | Main reason |
|---|---|---|---|
| AB | 459 / 67 | READY | one complete provincial layer (OGL-Alberta, modified 2026-08-19); watch Kananaskis PLUZ |
| BC | 1254 / 129 | READY for provincial, GAPS municipal | TANTALIS layer is daily, OGL-BC; Metro Vancouver/Burnaby/Victoria parks still need local layers |
| SK | 411 / 110 | READY after one check | ParksAsLegislated has separate recreation-site layer; confirm our key holds it |
| MB | 308 / 89 | GAPS | provincial parks layer is "current to 2017", no licence stated |
| YT | 112 / 85 | READY (campgrounds pin-only) | surveyed polygons (OGL-Yukon, 2023) |
| NT | 68 / 53 | GAPS | territorial parks record is a tourism map (points); no NT park polygons in key |
| NU | 48 / 14 | READY enough | federal parks joined; CPCAD for the rest |

## Top adds for chat 2
1. **AB** parks_protected_areas_alberta MapServer / FeatureServer/0 (https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/MapServer): confirm it is the layer behind our 'Alberta Park' key.
2. **BC** TA_PARK_ECORES_PA_SVW (WMS https://openmaps.gov.bc.ca/geo/pub/WHSE_TANTALIS.TA_PARK_ECORES_PA_SVW/ows): daily, OGL-BC.
3. **SK** ParksAsLegislated layers 0, 1 (recreation sites), 2, 3 (https://gis.saskatchewan.ca/arcgis/rest/services/ParksAsLegislated/MapServer): 44 unjoined recreation sites likely sit in layer 1.
4. **YT** Parks_and_Protected_Areas_Polygon_Surveyed (OGL-Yukon).
5. **MB** Manitoba_Parks FeatureServer/0: find a newer copy or confirm date and licence.
6. **NT** find a polygon layer (NWT_Hunting sanctuaries and Environment_LCC are the leads; both mix land uses).
7. **CPCAD** (https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0) as the fallback for MB, NT, NU.
8. **NHN** (https://maps.geogratis.gc.ca/wms/hydro_network_en; GPKG https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nhn_rhn/gpkg_en/CA/): the water layer; BC also has its Freshwater Atlas.
9. **BC municipal**: Burnaby, Metro Vancouver, CRD (leads in Gap desk).

## Name mismatches
- Same park name in two provinces: **Duck Mountain PP** (MB CA-0538, SK CA-0596), **Cypress Hills** (SK CA-0592, AB CA-0642), **Elk Island** (AB NP CA-0020 vs MB provincial CA-0540). Match inside the same province only.
- **Garibaldi Park Recreation Park (BC CA-3537)** vs **Garibaldi Provincial Park (CA-0723)**: same park, two numbers.
- **Ethelbert (Duck Mountain) WMA (MB CA-2410)**: WMA layer likely uses a different name.
- Tombstone: TP (CA-4636) and NHPA (CA-4635) are separate designations.
- Rule: join within the province, strip the type words, try both layers before calling a park missing.

## NEW grey areas for Brandon
| # | Question | My lean |
|---|---|---|
| CAW-1 | Parks co-managed with, or inside land of, Indigenous governments (Gwaii Haanas CA-0032, Thaidene Nene CA-0098, Kluane CA-0044, Ivvavik CA-0039, Vuntut CA-0106, every Nunavut park): normal parks? | Yes, where the designation legally applies; note nothing special. |
| CAW-2 | Cypress Hills Interprovincial Park (SK CA-0592) and AB Cypress Hills PP (CA-0642): one park, two numbers? | Treat as "same land, two park numbers" only if the polygons touch; else side by side. |
| CAW-3 | Alberta same-name trio (Bow Valley PP CA-0636, Provincial Recreation Area CA-2949, Wildland PP CA-2950) and Kootenay Plains ER CA-3057 + PRA CA-5533. | Layered at the same site: "same land, two park numbers". |
| CAW-4 | Territorial roadside campgrounds (YT recreation sites, NT/NU territorial parks): points, not polygons. | Pin only; no 2-fer test. |
| CAW-5 | Crown-land recreation sites (BC Recreation Sites and Trails, AB PLUZ, SK recreation sites with numbers): park or Crown land? | Only if the layer is a legislated park/site (SK yes, BC rec sites no, AB PLUZ no). |
| CAW-6 | Municipal parks with POTA numbers (Burnaby, Metro Vancouver "Parks"). Same question as CAE-8. | Keep out unless Brandon rules otherwise. |

## What is solid, what is not
Solid (A): AB layer text, licence and dates; BC TANTALIS record (dates, licence, WMS); SK ParksAsLegislated layer list; YT surveyed record; MB layer note; NT territorial parks record; NHN record. Not solid: SK licence; MB licence and currency; the NT polygons (maybe none); NU layer source; every 2-fer prediction (B/C).
