# World W2: AUSTRALIA (desk, Oct 27 2026)
Grades: A = opened and read, B = search only, C = inference. Read only. Key = data/world-key/AU.json: 10,272 parks, 2,228 no outline, 1,433 pin outside, 1,067 to check; sources in key: CAPAD, NSW State Forest, QLD State Forest, VIC state forests, WA DBCA state forests. Australia has the best public-land data of any country we hold: **most parks are Crown land (public) and every state publishes a tenure layer**, so rule 14 can run here.

## SUMMARY (READY / GAPS)
| State | Verdict | Why |
|---|---|---|
| NSW | READY after adds | CC BY tenure layer (Crown / National Park / State Forest / Private / Indigenous) updated Oct 2025 |
| VIC | READY after adds | PLM25 (public land management), CC BY 4.0, updated quarterly |
| WA | READY | DBCA Legislated Lands and Waters, CC BY-SA 4.0, April 2026 |
| QLD | PARTLY | Protected areas of Queensland series (lot-on-plan), licence not stated; state forests in key |
| TAS | READY after add | LIST Land Tenure (Crown/private/reserved) but licence not specified |
| SA, NT, ACT | GAPS | not read; NT has a Parks and Reserves land-holdings list; ACT/SA layers not found yet |
| national | CAPAD 2024 | licence "Not specified" on data.gov.au; no ownership field confirmed |

## 1. Official layers by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| All protected areas (national parks, nature reserves, conservation parks, IPAs, private protected areas) | CAPAD 2024 terrestrial / marine, FGDB download: https://data.gov.au/data/dataset/6f980342-3a58-4a47-adb2-a178cd6748c2 | DCCEEW (states supply) | currency 30 Jun 2024; updated 24 Oct 2025; **licence "Not Specified" on the page (A)** (check the DCCEEW record: usually CC BY 4.0, C) | IN KEY |
| **NSW land tenure** (Crownland-Leasehold, Crownland-Other, Indigenous Owned, National Park, Private, State Forest, Unresolved) | https://data.nsw.gov.au/data/dataset/nsw-land-tenure ; GDB https://datasets.seed.nsw.gov.au/dataset/6884bc76-7b9d-4fcc-b3cc-a3416699dcb5/resource/d4e3fc9c-11f8-433c-8fe1-751148136635/download/nswlandtenure_dec2024_v2_seed.gdb.zip | NSW Spatial Services / SEED | updated 8 Oct 2025; **CC BY** (A) | **NO. TOP ADD (the ownership step)** |
| NSW NPWS estate / all managed land | data.nsw.gov.au "NPWS All Managed Land", "NPWS Estate" (B) | NPWS | CC BY (B) | NO |
| **VIC Public Land Management (PLM25)** | https://discover.data.vic.gov.au/dataset/public-land-management-plm25 ; WFS https://opendata.maps.vic.gov.au/geoserver/wfs ; WMS layer open-data-platform:plm25 (A) | DEECA | "last updated 24/10/2026" (A, odd future-looking date on the page), quarterly; **CC BY 4.0** | **NO. TOP ADD** (state forests, parks, reserved AND unreserved Crown land, water frontages, Commonwealth land) |
| **WA DBCA Legislated Lands and Waters (DBCA-011)** | https://data.gov.au/data/dataset/dbca-legislated-lands-and-waters ; slip service https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Property_and_Planning/MapServer/15 (B) | DBCA | 11 Apr 2026; **CC BY-SA 4.0** (A); includes national park, nature reserve, conservation park, marine park, state forest, timber reserve and **Crown reserves under the Land Administration Act** | the key has WA "state forests" only: **add the whole layer** |
| QLD protected areas | https://data.qld.gov.au/dataset/protected-areas-of-queensland-series ; ArcGIS https://services-ap1.arcgis.com/s047i49VH0D2nqIM/ArcGIS/rest/services/Protected_areas/FeatureServer ; https://gisext.qfes.qld.gov.au/arcgis/rest/services/Hosted/Protected_areas/FeatureServer/0 (B) | Dept of Environment | updated 29 Aug 2025 (source 15 Jul 2025); licence not specified on data.gov.au (A) | PARTLY (state forest only) |
| TAS LIST Land Tenure | https://data.gov.au/data/dataset/list-land-tenure ; service https://services.thelist.tas.gov.au/arcgis/rest/services/Public/OpenDataWFS/MapServer/26 (B) | Tasmanian Government (the LIST) | updated 25 Jun 2025; **licence not specified** (A) | NO |
| NT Parks and Reserves | https://data.nt.gov.au/dataset/2cceca81-af2d-4de5-85a3-a19223842602 (B) | NT Government | not read | NO |
| SA / ACT | not found | | | NO |
| Trails | Bicentennial National Trail, Larapinta, Heysen: no official line files found (World preflight item 13) | | | NO |

## 2. No outline (2,228) and what covers each
- **State Beach 1,231 (1,226 none)**, e.g. East State Beach AU-10001, Reef Point State Beach AU-10002, Killarney State Beach AU-10003: bulk of the gap. These look like **POTA's NSW "beach" copy of a US-style label**; no layer holds them. Pin only (C). **Ask Brandon (W2-1).**
- **Reserve 2,286 (521 none):** Mudgee Park Reserve AU-10417, Kawana Forest Bushland Reserve AU-10525: council/Crown reserves: NSW tenure ("Crownland-Other") and VIC PLM25 cover state Crown reserves; council bushland = never.
- **State Forest 1,343 (491 none):** Spencer Gap SF AU-0328, Macartney SF AU-0428, McCorkill SF AU-0506: **Queensland state forests** (QLD layer in key) and NSW/VIC/TAS (Permanent Timber Production Zone Land): probably **name mismatches**: key lacks the "State Forest" suffix or the layer calls it "Spencer Gap" only.
- **National Wild and Scenic River 354 (349 none):** Murray AU-10419, Hunter AU-10424, Blackwood AU-10000: rivers: POTA uses a US label for Australian river corridors. Line/water; ask Brandon (W2-2).
- **State Heritage Area 87** (Fort Scratchley AU-10397…): pin only (historic).
- **State Trail 67:** Thorsborne AU-10041, Cooloola AU-10042: Queensland trail lines (QLD Parks trails layer not found).
- **Conservation Area 450 (69 none):** NT Conservation Area AU-10073 (Hyland Bay), 10074, 10075: NT layer unread.
- **Water Management Area 46:** Lake Baroon AU-11230, Ewen Maddock Dam AU-11231: Seqwater dam land; water + shore, public-body (Seqwater) land.
- **National Park 749 (30 none):** Willis Island AU-0002 (remote), Tunnel Creek AU-0027 and Geikie Gorge AU-0126 (WA, probably name differences with "Tunnel Creek National Park" vs layer "Windjana Gorge"); Nature Reserve 954 (43 none, unnamed WA-35598 AU-11413).

## 3. Trails and access: no official access points; Queensland and WA trails not read.

## 4. Tricky land (rule 14)
- **State forests with "timber reserve" or "Permanent Timber Production Zone" status:** public Crown land but sometimes closed for harvesting; mixed with nature reserves inside.
- **Indigenous-owned and joint-managed parks:** Kakadu, Uluru-Kata Tjuta, Booderee (Commonwealth parks leased from Traditional Owners); NSW tenure labels "Indigenous Owned". Not in CAPAD as a separate ownership field. **Grey area W2-3.**
- **Private protected areas** (Bush Heritage, Australian Wildlife Conservancy, covenants): by agreement, not public: Brandon's private-land ruling; they show in CAPAD as private.
- **Leasehold (pastoral) Crown land:** "Crownland-Leasehold" in NSW is Crown land but leased to farmers: NOT open, not a park. **A tenure layer that mixes Crown leasehold and parks needs filtering by class: only National Park, State Forest, Crown reserves for public recreation count.**
- **Marine parks:** CAPAD marine is a separate release; water-only list (rule 9).
- **Commonwealth land** (Defence ranges, airports): PLM25 shows it separately; closed.

## 5. KNOWN-GOOD layers (answer key)
1. CAPAD 2024 terrestrial (national)
2. NSW Land Tenure (CC BY) for the ownership step
3. VIC PLM25
4. WA DBCA-011 (adds Crown reserves)
5. QLD Protected areas series + State Forests
6. TAS LIST Land Tenure
7. NT Parks and Reserves land holdings
8. Water: Geoscience Australia GEODATA Topo 250K hydrography / state hydro (not searched; B)

## 6. 2-fers to expect
Confident (C, to prove with polygons): NSW national park vs adjoining state forest (side by side, tenure says National Park vs State Forest: can never be the same land); WA national park vs nature reserve inside the same DBCA layer (layered lines in one layer are rare; clear duplicates first). Hard: Blue Mountains NP vs Greater Blue Mountains WHA (no boundary rule); Kakadu NP (Commonwealth) vs Kakadu region NT Conservation Areas; Booderee NP vs Jervis Bay Marine Park (land vs water).
Note: Australian parks are almost all **Crown land**, so rule 14 passes (public land, agency owns) wherever the tenure class is National Park / State Forest / Crown reserve.

## NEW grey areas
| # | Question | My lean |
|---|---|---|
| W2-1 | "State Beach" 1,231 numbers with no layer (pin only)? | Pin only, no 2-fers (C). |
| W2-2 | "National Wild and Scenic River" Australian rivers (354): line parks? | Rivers = water-only (rule 9); lines rule 8 only if an agency line exists (none). |
| W2-3 | Commonwealth parks leased from Traditional Owners (Uluru, Kakadu, Booderee): normal parks? | Yes, designation applies; no special note. |
| W2-4 | Crown leasehold land and private covenants inside CAPAD: park land? | No (by agreement / leased); only National Park, State Forest, Crown public reserves. |
