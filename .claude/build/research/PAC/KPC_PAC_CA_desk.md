# Pacific Source Book: CALIFORNIA (desk, Oct 27 2026)
Grades A opened/read, B search only, C inference. Read only. Key: 410 parks, 34 unjoined (10 BLM point parks); sgcaa CDFW, sgcab California State Parks; USFWS.

## 1. Official boundaries
| Type | Layer | Publisher | Read? |
|---|---|---|---|
| State parks | sgcab (services2.arcgis.com Uq9r85Potqm3MfRV) | CA State Parks | YES |
| CDFW lands (wildlife areas, ecological reserves) | sgcaa; CDFW Lands Generalized ds3010, Public Access Lands ds3077 (filelib.wildlife.ca.gov, B) | CDFW | YES (sgcaa) |
| **CPAD – California Protected Areas Database** | https://gis.cnra.ca.gov/arcgis/rest/services/Boundaries/CPAD_AgencyLevel/MapServer (B), CPAD_AccessType, CPAD_AgencyClassification (B); FeatureServer services.arcgis.com/QVENGdaPbd4LUkLV/…/CPAD/FeatureServer/0 (B) | GreenInfo Network / CNRA | **NO** – the one-stop umbrella (state, county, city, federal, land trust) with an ACCESS type |
| State trails | none | | |

## 2. Unjoined (34)
- State parks: Montana de Oro SP US-1174, Van Sickle Bi-State Park 2638, La Purisima Mission SHP 3454, Tijuana Estuary Reserve 3578 (state/NERR), 3 State Beaches: **name mismatches** (State Parks layer names units like "Montaña de Oro SP", "Tijuana River..."?).
- Black Butte Lake Park US-12616 (Corps), Rainbow Basin Natural Area 11336 (BLM), Sáttítla Highlands NM 12115 (USFS), San Gabriel Mountains NM, Trona Pinnacles NNL 10400, Kesterson NWR 0198, Cesar Chavez NM 0915, Rosie the Riveter 0754, Kings River WSR 0884, 5 NHTs, PCT.
- 10 BLM SRMA/RMA (Cow Mountain, Red Hills, Panoche Hills, Stoddard Valley…): BLM POINT PARKS.

## 3. Trails and access
Park entrances and parking read. Add CPAD AccessType for rule 3 (public + open).

## 4. Tricky land
- **State parks on federal land** (Lake Perris, Folsom Lake SRA on BuRec; Castaic on DWR): leases.
- **CDFW wildlife areas with limited access** (ecological reserves are often closed to general use): public + open test.
- **Land trust and county parks** inside CPAD.
- Water: state marine reserves.

## 5. KNOWN-GOOD layers
1. CA State Parks (sgcab)
2. CDFW lands (sgcaa) + ds3077 public access
3. CPAD AccessType (A path; B content)
4. NPS/USFS/BLM boundaries
5. CA State Parks entrances/parking

## 6. 2-fers
Confident (B): Golden Gate NRA (NPS) vs. Angel Island / Mount Tamalpais SP: adjoining; Santa Monica Mountains NRA (NPS) is a patchwork with state parks (Malibu Creek SP) layered on NPS-administered area: need ownership polygons. Hard: Point Reyes NS vs. Tomales Bay SP.
