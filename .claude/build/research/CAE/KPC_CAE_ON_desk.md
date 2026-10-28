# Canada East: ONTARIO (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only. I cannot query polygons, so "covers" comes from the publisher text. CANADA RULES: federal first; WDPA never; plain Crown land is not a park; water layer = National Hydro Network (NHN).
Key: 1158 parks, 255 with no outline (85 National Historic Sites, 81 Conservation Areas, 15 Conservation Reserves, 9 Wilderness Areas, 7 National Parks, 6 Recreation Parks, 6 Management Areas).

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| Provincial parks | Provincial_Parks_AGOL FeatureServer, layer 0 (https://services3.arcgis.com/RQBDTPtsbT0jebs7/ArcGIS/rest/services/Provincial_Parks_AGOL/FeatureServer). Classes: Wilderness, Nature Reserve, Cultural Heritage, Natural Environment, Waterway, Recreational | Ontario Ministry of Environment, Conservation and Parks (copyright King's Printer for Ontario 2022) | service text says "downloaded and updated 2023-02-12", frequency "as needed"; the page states NO licence (A). The data.ontario.ca record "Provincial Park Regulated" says **Open Government Licence – Ontario**, but that record is old (validated 2013, file 2018, download needs name+email) (A) | in key ('Ontario Park') |
| Conservation reserves | "Conservation Reserve Regulated" (data.ontario.ca/dataset/conservation-reserve-land; also LIO_Open03 MapServer, ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer) | Ontario MECP / LIO | OGL-Ontario (B) | in key ('Ontario cons') |
| Federal (national parks, NWAs, MBSs) | Parks Canada layer (see Summary) + CPCAD | federal | OGL-Canada | in key ('Ontario fede', 'Parks Canada', 'cpcad') |
| Conservation authority lands | one service per authority; our key has many 'ON-<CA>' keys | 36 conservation authorities, each its own licence | varies | PARTLY. Upper Thames, Nottawasaga, Long Point still unread (Gap desk). |
| Municipal / regional | 'Ontario muni' | cities | varies | in key |
| Provincial trails | none found (Ontario Trails is a point/line inventory, not read) | | | NO |

## 2. Parks with no outline (255) and what covers each
- **85 National Historic Sites (e.g. Rideau Canal CA-4882 joined; Trent - Severn Waterway CA-4889 NOT joined; Fort Frontenac CA-5303; Rideau Hall CA-5116):** historic sites are pin-only by Brandon's ruling. Trent-Severn and Rideau are **canal/waterway lines**, see section 4.
- **Name/accent mismatch (the likeliest "missing"):** La Verendrye Provincial Park CA-0259 (key has no accent; layer name is "La Vérendrye" or "La Verendrye"): fuzzy match. Barron Canyon Conservation Reserve CA-1300 vs Barron River Provincial Park CA-1302 (joined).
- **Biosphere reserves** Frontenac Arch CA-0023, Georgian Bay Littoral CA-0027: UNESCO designations, no park boundary: pin only (C; ask Brandon, same as SE-7 heritage areas).
- **81 Conservation Areas:** need the per-authority layers; the unread authorities are the gap.
- **Barron Canyon National Geologic Trail CA-1301, Nine Mile Portage Heritage Trail CA-5506:** trail lines, no layer.
- South Point Trail (Rondeau) CA-1599: inside Rondeau Provincial Park (CA-0368), a sub-trail number.

## 3. Trails and access
Nothing official found for access points. Ontario Parks publishes park entrance points on its map (B). Trails: Bruce Trail (conservancy, private/by agreement) and Trans Canada Trail are not park land.

## 4. Tricky land (rule 14)
- **Provincial parks on First Nations land:** Ontario has co-managed and treaty-affecting parks (Algonquin CA-0138 claim area; Killarney; Sandbanks area). **Grey area CAE-1.**
- **Crown land mix:** Ontario "Crown Land Use Policy Atlas" mixes General Use Areas (plain Crown land) with parks; never read it as a park layer.
- **Rideau Canal CA-4882 (Parks Canada line) vs Rideau River Provincial Park CA-0365 vs Rideau Migratory Bird Sanctuary CA-0364:** the canal is a water corridor owned by Parks Canada, the park and the sanctuary sit on or beside it. Same land, up to three numbers.
- **Thousand Islands NP CA-0099 and Georgian Bay Islands NP CA-0026:** island parks, mostly water between islands: rule 9.
- **Point Pelee NP CA-0067 / Rondeau PP CA-0368:** Lake Erie shoreline, water test needed.

## 5. KNOWN-GOOD layers (Discovery Bot answer key)
1. Ontario Provincial_Parks_AGOL layer 0
2. Conservation Reserve Regulated (LIO_Open03 layer for conservation reserves)
3. Parks Canada "Places administered" FeatureServer (https://services2.arcgis.com/wCOMu5IS7YdSyPNx/arcgis/rest/services/vw_Places_Public_lieux_public_APCA/FeatureServer/0)
4. CPCAD MapServer layer 0 (https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer): fallback, covers everything
5. NHN water (WMS https://maps.geogratis.gc.ca/wms/hydro_network_en; GPKG on ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nhn_rhn/gpkg_en/CA/)
6. Conservation authority services (per authority)

## 6. 2-fers to expect
Confident (C, prove with polygons): Rideau Canal vs Rideau River PP vs Rideau MBS; Algonquin PP vs nearby conservation reserves on its edge; Thousand Islands NP vs adjacent provincial waterway holdings. Hard: Trent-Severn (a 386 km line), Georgian Bay Islands NP vs North Georgian Bay Shoreline CR CA-1546 (islands interleaved).
