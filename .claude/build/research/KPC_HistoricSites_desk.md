# Historic-site boundaries: national source + state agencies (desk, Oct 28 2026)

## 1. The national source: NPS National Register of Historic Places polygons
- **REST address (A, opened):** https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1 (layer 1 = "National Register of Historic Places Polygons", polygons). A test copy of the same layer sits at `.../cultural_resources/nrhpTest/MapServer/1` (B) - use nrhp_locations.
- **Publisher:** Cultural Resources GIS, National Park Service (A). Also on the federal GeoPlatform and downloadable (CSV, Shapefile, GeoJSON, KML) via https://data.amerigeoss.org/dataset/national-register-of-historic-places-polygons1 (A): source record last modified 2023-07-20, catalogue entry 2025-12-09. So a download copy EXISTS and can be saved (good backup, no outage risk).
- **Coverage:** extent worldwide (US + territories); 41 fields incl. RESNAME, NRIS_Refnum, State, County, ResType, CertDate, Is_NHL, STATUS (some rows are "Removed"), BND_TYPE, MAP_METHOD, SRC_DATE, SRC_SCALE, SRC_ACCU, EDIT_DATE (A). Max 2,000 rows per call.
- **How the shapes are made (A):** "built from the bounding UTM coordinates in each nomination". That means they are the LISTED property's boundary, often a rough box or traced from a paper nomination map; MAP_METHOD / SRC_SCALE / SRC_ACCU say how good. Not a park managers' fence line.
- **Licence:** none stated on the pages I opened (A). US federal data, normally public domain (C): confirm in the metadata.
- **No data date on the service itself** (A); use EDIT_DATE per feature.
- **Does it have POTA historic sites as polygons?** Only IF the POTA park is on the Register AND the nomination gave coordinates. Three kinds of POTA historic site:
  1. NPS units (e.g. Fort Donelson, Shiloh, Stones River, Andersonville): NPS publishes its own park boundary layer, which is better (use that); NRHP shape is a second witness.
  2. State historic sites that are on the Register (Perryville Battlefield, Fort Boonesborough, Old Fort Harrod, Etowah Indian Mounds, Fort King George): likely a polygon, but its shape is the NOMINATION boundary (may be larger or smaller than the park).
  3. Local or unlisted markers/sites: no polygon. Pin only, as the house rule says.
- **TEST NOT DONE.** My research tool cannot send query addresses to that server (blocked) and my shell has no network, so I could NOT test the 5 sites. I will not guess. BOT LOOK-UP below.

### BOT LOOK-UP (new rows)
Query `.../nrhp_locations/MapServer/1/query?where=RESNAME LIKE '%<word>%' AND State='<ST>'&outFields=RESNAME,State,STATUS,ResType,Is_NHL,MAP_METHOD,SRC_SCALE,SRC_ACCU,EDIT_DATE&returnGeometry=true&outSR=4326&f=geojson` for these 5 real POTA historic sites and report: found? STATUS? polygon area in acres vs the park's published acres? does the POTA pin fall inside?
1. Perryville Battlefield State Historic Site (KY) - word 'Perryville'
2. Fort Boonesborough State Historic Site (KY) - 'Boonesborough'
3. Old Fort Harrod State Historic Site (KY) - 'Harrod'
4. Etowah Indian Mounds State Historic Site (GA, US-3715) - 'Etowah'
5. Stones River National Battlefield (TN, US-0708) - 'Stones River' (compare with NPS's own boundary)
Rule for the bot (Brandon Oct 28 12:30 AM: 'if it a park and we have boundary use it'): a historic site is outlined when an official layer we read has a SURE match (same place by name + pin inside + size in the right range); never hunted for; otherwise pin only. Markers = pin only. The NRHP polygon is a nomination boundary, so size will often differ: expect many "pin only".

## 2. State historic-site agencies: do they publish site boundaries? (one line each)
Filled in as I go through each state's official-maps file.
- KY (Kentucky State Parks, historic sites): publishes site PARK MAPS as PDFs on kentuckytourism.com (Perryville trail map, Fort Boonesborough park + campground map, Old Fort Harrod park + fort map; all in data/ky-official-maps.json); no boundary layer found. Kentucky Heritage Council = NRHP listings (B).
- TN: state has its own NRHP boundaries layer: https://tnmap.tn.gov/arcgis/rest/services/HISTORICAL/NATIONAL_REGISTER_TN/MapServer/2 "National Register of Historic Places Boundaries" (B, search result; not opened). TN state historic sites (TN State Parks): brochures only (B).
- GA (state historic sites under Georgia State Parks): trail/site map PDFs on gastateparks.org, no boundary layer seen (A for maps, C for no layer).
- AL, FL, MS, NC, SC, VA, WV: not yet looked at for this question; will add a line as each region is done.

## 3. All the official boundary sources found (Oct 28, for Brandon: "find historic site boundaries")
Best first. A = opened; B = search result only.
| # | Source | Address | What it is | Date / licence |
|---|---|---|---|---|
| 1 | **NPS park boundaries** (for the National Historic Sites, Battlefields, Military Parks: Shiloh, Stones River, Fort Donelson, Andersonville, Cumberland Gap...) | https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer : layer 2 nps_boundary (legislated unit boundaries), 1 nps_tracts, 0 centroids (A) | NPS Land Resources Division. "Not for engineering or legal use"; NPS may not own every parcel inside. Download from NPS IRMA. | No date shown; no licence named (federal) |
| 2 | **NPS National Register polygons** | https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1 (A) | nomination boundaries, all states; see section 1 | no date, no licence named; download copy dated 2023-07-20 |
| 3 | **North Carolina HPO** | https://www.hpo.nc.gov/gis-maps-and-data (A): shapefile `NCHPO_NR_SL_DOE_Boundaries` (about 27 MB, NR districts + individually listed + study list + eligible) and daily web map HPOWEB | state boundaries for NC historic districts/sites | updated MONTHLY, file name carries date (2026-10-02); no licence stated, ask the HPO GIS analyst |
| 4 | **Tennessee** | https://tnmap.tn.gov/arcgis/rest/services/HISTORICAL/NATIONAL_REGISTER_TN/MapServer/2 "National Register of Historic Places Boundaries", polygons (A); fields REFNUM, Resource_Name, County, Listed_Date, NHL_Date, FILENET link | state copy of NR boundaries | no description, no date, no copyright text |
| 5 | **Kentucky** | https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_National_Register_Landmarks_WGS84WM/MapServer (A, credits NPS, DGI, Ky Heritage Council) - geometry type not stated, probably points (C); Lexington-Fayette only: https://services1.arcgis.com/Mg7DLdfYcSWIaDnu/ArcGIS/rest/services/National_Register_Property/FeatureServer/0 polygons (A, last edit 2021-01-18, LFUCG) + National_Register_District; Louisville Jefferson County: gis.lojic.org .../OpenDataDevelopment/MapServer/8 (B) | Statewide KY = landmarks (check type); only two counties have polygons | LFUCG 2021 |
| 6 | **Delaware** | enterprise.firstmaptest.delaware.gov/arcgis/rest/services/Society/DE_HistoricPlaces/MapServer/0 and /1 (B) | state historic places | not opened |
| 7 | State historic-site agencies (Ohio History Connection, Georgia, Alabama, Virginia, etc.) | no boundary layer found in this pass | they publish site maps, not boundaries | - |

### What this means for Kentucky POTA historic sites
- Perryville Battlefield, Fort Boonesborough, Old Fort Harrod (state historic sites): the NPS NRHP layer (row 2) is the only statewide polygon source; Kentucky's own layer is landmarks only (probably points). Fort Boonesborough and Old Fort Harrod are listed properties (C): expect a polygon if they are in NRIS with coordinates. TEST STILL TO RUN by a bot (list above).
- Federal sites in KY (Mill Springs Battlefield NM, Abraham Lincoln Birthplace NHP, Cumberland Gap NHP): NPS boundary layer (row 1) is the right source.
- Brandon's rule applies: use the polygon only when the match is sure; otherwise pin.
