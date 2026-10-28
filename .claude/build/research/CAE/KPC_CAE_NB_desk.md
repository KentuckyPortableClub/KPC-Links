# Canada East: NEW BRUNSWICK (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only. I cannot query polygons, so "covers" comes from the publisher text. CANADA RULES: federal first; WDPA never; plain Crown land is not a park; water layer = National Hydro Network (NHN).
Key: 562 parks, 256 with no outline (74 NHS, 58 Historic Sites, 40 Recreation Parks, 15 Nature Reserves, 10 Ecological Areas).

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| Provincial parks | GeoNB data catalogue "Provincial parks": polygons of NB provincial parks only; ESRI FGDB/layer package/shapefile download; map service geonb.snb.ca/arcgis/rest/services/GeoNB_DNR_ProvincialParks/MapServer (B) | Dept of Energy and Resource Development | updated "ad hoc"; **Open Government Licence – New Brunswick**, no restrictions (A) | in key ('NB-PP', 'New Brunswic') |
| Protected Natural Areas / ecological areas | NB DNR "Protected Natural Areas" (not opened) | ERD | OGL-NB (C) | PARTLY. Our key has 'Daly Point', 'Mary's Point' unjoined. |
| Wildlife Management Zones | 'NB WMZ' (24 numbered zones) | ERD | in key | WMZs are hunting zones, not parks (note in Gap desk) |
| Recreation parks (40) | municipal | towns | varies | NO |
| Federal | Fundy NP CA-0025, Kouchibouguac NP CA-0046, NWAs (Portage Island NWA CA-0072), Fundy Biosphere CA-0024 | Parks Canada, CWS | OGL-Canada | in key |

## 2. Parks with no outline (256)
- 74 NHS + 58 Historic Sites: pin only. Several are **portage routes** (Beaubassin / Ancient Indian Portage CA-6446, Petitcodiac – Washademoak Portage CA-6492, Meductic-Eel River Portage CA-6499, Missaguash – Baie Verte Portage CA-6579, Portage Lakes Protected Area CA-4493): old canoe/portage routes. Lines, not parks: ask Brandon (CAE-4).
- Recreation Parks: North Head Park CA-0776, Killarney Lake Park CA-5258: municipal (city parks = never per Brandon, but they hold POTA numbers; decide rule).
- Nature Reserves/ecological: Daly Point Nature Reserve CA-1231 (Bathurst/Miramichi city reserve?), Mary's Point Ramsar CA-0785 (Ramsar is a designation; the land is Shepody NWA + provincial; pin), Fundy Coastal Ecological Area CA-6477 (Protected Natural Area in ERD layer, C).

## 3. Trails and access
New Brunswick Trail (NB Trails Act, partly rail line); no layer read.

## 4. Tricky land
- **NB is mostly Crown land (~50 %) and the Crown timber licences are not parks:** the GeoNB Crown land layers mix everything. Never read "Crown land" as park.
- **Fundy Trail Provincial Park CA-6234** is a private-public partnership; boundary in the provincial parks layer (A: parks layer covers it, C).
- **Water:** Saint John River, Bay of Fundy tidal flats (huge tidal range: shoreline is a moving line). Use NHN; tidal parks (Mary's Point, Daly Point) need the high-water line. Rule 9.

## 5. KNOWN-GOOD layers
1. GeoNB DNR ProvincialParks MapServer
2. GeoNB Protected Natural Areas (find service)
3. CPCAD; Parks Canada places; NHN

## 6. 2-fers to expect
Confident (C): Fundy NP CA-0025 vs Fundy Biosphere (zone, not a boundary); Fundy Trail Provincial Park vs Fundy Coastal Ecological Area CA-6477 (adjacent, verify). Hard: Mary's Point (Shepody NWA + provincial + Ramsar).
