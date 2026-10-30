# Fable book, Canada: INDEX (split by HQ Oct 30 7:35 AM; Brandon 7:31 AM 'do it all')

The work log now lives in ONE FILE PER STATE / PROVINCE: `.claude/build/research/fable/CA-XX.md` (read and write only your state's file). Rules unchanged: one row per park, updated in place; 'STATE XX DONE' goes at the END of that state's file (BOT F reads it there). The Agency Atlas (`.claude/build/research/agency-atlas/CA-XX.md`) is read FIRST.

| file | rows | parks |
|---|---|---|
| fable/CA-NU.md | 15 | 14 |
| fable/CA-PE.md | 43 | 35 |
| fable/CA-NT.md | 53 | 51 |
| fable/CA-NL.md | 69 | 67 |
| fable/CA-AB.md | 83 | 66 |
| fable/CA-MB.md | 92 | 89 |
| fable/CA-YT.md | 93 | 85 |
| fable/CA-SK.md | 127 | 110 |
| fable/CA-BC.md | 147 | 129 |
| fable/CA-NS.md | 191 | 167 |
| fable/CA-NB.md | 259 | 243 |
| fable/CA-ON.md | 319 | 248 |
| fable/CA-QC.md | 471 | 407 |

---
## Everything else from the old single file (rerun numbers, why-not tags, county lists, notes) is kept below unchanged

# Missing boundaries, CANADA: the list for Fable (chat 2, Oct 29 3:45 PM; Brandon 3:40 PM "Start Canada version of fable list")

Read from KPC-Links data/ca-key (the current Canada key): 5,899 parks, 4,188 outlined. Same R-G7 steps as the US list (notes/mapping.md); everything STAGED (freeze). Fable gets ONLY what steps 2-5 cannot place.

- **PIN INSIDE a bigger area with another name: 362** (R-G7 steps 2-5). **CHECK by hand: 53** (candidates listed). **NOTHING NEAR: 1296** (find the official layer first: Source Book / chat 9).
- Pool of refs: `missing-after-key-canada.json` (keys PIN INSIDE / CHECK / NOTHING NEAR).

## By province (biggest first)

| province | pin inside | check | nothing near |
|---|---|---|---|
| QC | 34 | 14 | 359 |
| ON | 26 | 13 | 209 |
| NB | 202 | 3 | 38 |
| NS | 9 | 4 | 154 |
| BC | 13 | 15 | 101 |
| SK | 29 | 2 | 79 |
| MB | 5 | 0 | 84 |
| YT | 9 | 0 | 76 |
| NL | 1 | 0 | 66 |
| AB | 21 | 2 | 43 |
| NT | 4 | 0 | 47 |
| PE | 7 | 0 | 28 |
| NU | 2 | 0 | 12 |

## PIN INSIDE (first 60, biggest provinces first)

| park | name | type | the bigger area / candidate | acres |
|---|---|---|---|---|

## CHECK (first 60, biggest provinces first)

| park | name | type | the bigger area / candidate | acres |
|---|---|---|---|---|

## NOTHING NEAR by park type (where to hunt layers)

- National Historic Site: 392
- Regional Park: 156
- Recreation Park: 132
- Conservation Area: 74
- Park: 71
- Historic Site: 70
- Recreation Site: 66
- National Heritage Site: 59
- Provincial Park: 54
- Nature Reserve: 46
- Territorial Park: 38
- National Park: 12
- Biosphere Reserve: 11
- Natural Area: 10
- Conservation Reserve: 10

## WORK LOG BY PROVINCE (everything found goes in THIS file)

ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.

### GIS hunter, Oct 30 2026 (chat 10; candidate rows only: pin inside an official record; chat 11 answers YES / NO in KPC-Data data/waiting/questions/gis-hunter.json; leads + 'nothing' rows stay in KPC-Data data/gis-hunter/CA-XX.json)

| ref | park | step | what was found | result | date | by |
|---|---|---|---|---|---|---|
(138 candidate rows. Note for chat 11: 'name match' can be ONE shared word, e.g. Castle Falls Natural Area vs Alberta's 'Castle' record of 62,396 ac: check the size too.)


## RULES + LAYERS TO START (Fable, Oct 29 7:05 PM)
Rule Sheet G applies unchanged; Canada reading rules R-GC1..R-GC8 and the starter layer list (✓ wired / ◯ to probe) are in notes/mapping.md under 'RULE SHEET G, CANADA'. Order: layer probing + wiring now (prep); R-G7 hand tracing after the US book is through the Opus + Fable passes (Brandon 5:28 PM).


### chat 9 Canada P-2 rows, Oct 29 19:34 (HQ 7:05 PM; PREP only, no tracing; 9 of 51 requests answered so far)
`| park | name | source found | Rule G step | result | by chat | date |`

**AB** (66 parks)

**BC** (129 parks)

**MB** (89 parks)


### chat 9 Canada P-2 rows (batch 19:50; PREP only, no tracing)
`| park | name | source found | Rule G step | result | by chat | date |`

**NB** (243 parks)

**NL** (67 parks)

**NS** (47 parks)

**NT** (51 parks)

**NU** (14 parks)

**PE** (35 parks)

## GIS LAYERS WE PULLED (Brandon Oct 29 8:17 PM: 'make sure there are places for them to leave what GIS layers we pulled'; EVERY agent adds one row per layer it probes, wires or finds dead; never delete others' rows)
`| province / federal | layer name (agency) | URL (REST / WFS / download) | name field(s) EN / FR | licence line | status: wired ✓ / probed OK / probed DEAD / private (dropped) / to probe | which parks it covers (count or refs) | by chat | date |`
| BC | Local and Regional Greenspaces (BC Map Hub) | https://maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_basemapping/MapServer/39 | (see chat 9 lp1) | BC open licence | wired ✓ (staged) | regional + municipal parks | 2 / 9 | Oct 29 |
| MB | Manitoba Provincial Forests v6 (Manitoba Maps) | https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Provincial_Forests___Version_6/FeatureServer | (see chat 9 lp1) | OpenMB licence | wired ✓ (staged) | provincial forests | 2 / 9 | Oct 29 |
| AB | Land Use Management: Public Land Recreation Area (layer 14, 64 recs, PLREC_NAME), Public Land Use Zone (layer 11, 61, PLUZ_NAME), Rocky Mountains Forest Reserve (layer 19) (Government of Alberta) | https://geospatial.alberta.ca/titan/rest/services/boundary/land_use_management/MapServer | PLREC_NAME / PLUZ_NAME / ROCKYMTN_NAME (EN only) | 'Copyright Government of Alberta' (credit class; terms line to confirm) | probed OK (polygons) | Alberta recreation areas / land-use zones (names only; Calgary / Edmonton municipal parks still to find) | 9 | Oct 29 |
| BC | Recreation Sites, Reserves + Interpretive Forests, details + closures (Recreation Sites and Trails BC) | https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/RecSitesReservesInterpForests_DetailsClosures_publicView/FeatureServer | (to read) | 'Copyright Province of British Columbia' | queued for the intake bot (KPC-Data data/intake/queue.json); may be points | BC recreation sites | 9 | Oct 29 |
| BC | Local and Regional Greenspaces: facts (BC Map Hub) | https://maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_basemapping/MapServer/39 | PARK_NAME EN only (+ PARK_TYPE, REGIONAL_DISTRICT, MUNICIPALITY, WEBSITE_URL) | service shows no licence line; (c) Government of British Columbia; catalogue https://catalogue.data.gov.bc.ca/dataset/6a2fea1b-0cc4-4fc2-8017-eaf755d516da | probed OK: POLYGON, 9,682 records | regional + municipal parks (BC Park 66 / Regional 6 / Recreation 8 nothing-near) | 9 | Oct 29 |
| MB | Manitoba Provincial Forests v6: facts | https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Provincial_Forests___Version_6/FeatureServer/1 | PROV_FOREST_NAME / NOM_FORET_PROV | Manitoba Open Data Licence | probed OK: POLYGON, 57 records | provincial forests | 9 | Oct 29 |
| federal | Parks Canada org services root (services2.arcgis.com/wCOMu5IS7YdSyPNx/arcgis/rest/services) | https://services2.arcgis.com/wCOMu5IS7YdSyPNx/arcgis/rest/services | n/a | n/a | to probe: a FOLDER root gave no layer list; need the exact service URLs | NHS 392 (Parks Canada places are points) | 9 | Oct 29 |
| YT | GeoYukon folder root | https://mapservices.gov.yk.ca/arcgis/rest/services/GeoYukon | n/a | n/a | to probe: root gave no layers; GY_ParksProtectedAreas layers 0 / 3 already in the key | YT recreation sites 26 + recreation parks 16 + historic sites 12 | 9 | Oct 29 |
| NT | GNWT folder root | https://www.apps.geomatics.gov.nt.ca/arcgis/rest/services/GNWT | n/a | n/a | to probe: root gave no layers (Environment_LCC/MapServer/195 already in the key) | NT 47 nothing-near | 9 | Oct 29 |
| all | GIS hunter step A, Oct 30: every Canada key layer (data/ca-key/layers.json) + CPCAD + Parks Canada, one multipoint query per 120 pins | (see data/gis-hunter/CA-XX.json) | layer's name field | as in the key | probed OK (used) | 13 provinces / 1,711 open parks: 138 candidates | 10 | Oct 30 |
(the 15 layers already in the key are listed in notes/mapping.md 'CANADA MAP LAYERS TO START' (✓); add a row here when you touch one)
| federal | National Parks and National Park Reserves of Canada: Legislative Boundaries (NRCan CLSS Administrative Boundaries, layer 1; layer 0 = Aboriginal Lands, not parks) | https://proxyinternet.nrcan-rncan.gc.ca/arcgis/rest/services/CLSS-SATC/CLSS_Administrative_Boundaries/MapServer/1 | adminAreaNameEng (EN; FR to check) | no licence line in service | probed OK (polygons) | national parks + reserves (legal lines) | 9 | Oct 30 |
| SK | Planning MapServer layer 3 Migratory Bird Sanctuary / layer 2 National Wildlife Area (Gov of Saskatchewan; ECCC sites in SK only) | https://gis.saskatchewan.ca/arcgis/rest/services/Planning/MapServer/3 (and /2) | PUBLICNM, PLACE_NAME, AREA_HA, MGMT_JUR | no licence line in service | probed OK (polygons, SK only) | SK MBS + NWA | 9 | Oct 30 |
| BC | TANTALIS Management Areas (Spatial), layer 8 (Gov of BC; Wildlife Management Areas sit here) | https://delivery.maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_tantalis/MapServer/8 | MANAGEMENT_AREA_NAME (EN) | 'built for a specific purpose and may change'; (c) Government of British Columbia | probed OK (polygons); check type field for WMA | BC WMAs | 9 | Oct 30 |
| BC | Wildlife Management Units, layer 23 (hunting units) | https://delivery.maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_wildlife_management/MapServer/23 | WILDLIFE_MGMT_UNIT_ID | (c) Gov of BC | DROPPED: hunting units, not parks | none | 9 | Oct 30 |
| NL | GeoAtlas Land_Use MapServer: layer 4 Canadian Protected Conserved Areas (NAME_E), layer 0 Protected Areas Plan 2020 (NAME_E, plan not final) | https://dnrmaps.gov.nl.ca/arcgis/rest/services/GeoAtlas/Land_Use/MapServer | NAME_E | none shown | probed OK (polygons); layer 4 probe filed (CA-LP3) | NL parks + reserves | 9 | Oct 30 |
| NL | Provincial parks + natural areas shapefile / KMZ downloads (TCAR + ECCC GIS Data pages) | https://www.gov.nl.ca/tcar/parks/gis-data/ ; https://www.gov.nl.ca/eccc/natural-areas/gis-data/ | (download only) | disclaimer on page | found, DOWNLOAD only (no REST) | NL parks, natural areas | 9 | Oct 30 |
| QC | Couche des territoires récréatifs du Québec (MRNF): REST | https://servicescarto.mrnf.gouv.qc.ca/pes/rest/services/Territoire/TRQ_WMS/MapServer | (CA-LP3 probe filed) | Données Québec | to read | ZEC / réserves fauniques / pourvoiries? | 9 | Oct 30 |
| QC | Territoires fauniques structurés (TFS) | https://www.donneesquebec.ca/recherche/dataset/territoires-fauniques-structures | GDB / GeoJSON / SQLite downloads, no REST found | Données Québec | found, DOWNLOAD only | ZEC + réserves fauniques | 9 | Oct 30 |
| PE | PEI_NRN (road network) | https://gis.princeedwardisland.ca/server/rest/services/Hosted/PEI_NRN/FeatureServer | roads | n/a | DROPPED: roads, not parks. No official PEI parks layer found yet | none | 9 | Oct 30 |
| ON | LG_ConservationAuthority_Boundary_OpenData (Leeds & Grenville) | https://services3.arcgis.com/KQcdsE7S72bcD7R8/ArcGIS/rest/services/LG_ConservationAuthority_Boundary_OpenData/FeatureServer | LEGAL_NAME | county open data terms | DROPPED: authority boundaries, not parks; per-authority park layers still to find | none | 9 | Oct 30 |
| NS | Halifax parks (HRM Open Data hub) | https://data-hrm.hub.arcgis.com/pages/open-data-catalogue | n/a | HRM open data | catalogue page loads as script; need the dataset link (next) | HRM parks | 9 | Oct 30 |

## WHY-NOT TAGS (R-G10 / R-GC8; chat 2 fills from data/ca-key/why-not.json after the Canada Rule G rebuild)
One line per province: tag → count → refs (no-layer / picture-map-only / private / name-mismatch / needs-parcel / pin-doubt).

## ADDRESSES (chat 8 + chat 3; same rules as the US: official page only, note when the address / GPS is an office, not the park)
`| park | name | address | GPS | official page | is it the park? (yes / office / town) | by chat | date |`

## NOTES FROM AGENTS (anything that does not fit a row: a province's quirks, a dead host, a naming pattern, a question for Fable)
`- <date> <chat>: <one or two lines>`

### chat 9 Canada P-2 rows (batch 20:44; PREP only, no tracing)
`| park | name | source found | Rule G step | result | by chat | date |`

**NS** (120 parks)

**ON** (248 parks)

**QC** (407 parks)

**SK** (110 parks)

**YT** (85 parks)

