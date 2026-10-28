# South Central Source Book: ARKANSAS (desk, Oct 27 2026)
Grades A opened/read, B search only, C inference. Read only. Key: 304 parks, 54 unjoined; sgara Natural Heritage Commission, sgarb State Parks, sgarc AGFC.

## 1. Official boundaries
| Type | Layer | Publisher | Note | Read? |
|---|---|---|---|---|
| State parks | sgarb (gis.ardot.gov hosting) | AR State Parks | | YES |
| Natural areas | sgara (gis.arkansas.gov) | ANHC | | YES |
| WMAs, fishing lakes, hatcheries | sgarc (AGFC AGOL 5bMc8SlGDYGINZr5); gisec2.agfc.com/arcgis/rest/services/APP_AGFC/MapServer/10 (layers.json key `arw`) | AGFC | | YES |
| **All public land (city, county, state parks, refuges, WMAs, wilderness, historic areas, military)** | https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Planning_Cadastre/MapServer/16 PUBLIC_LAND_BOUNDARIES_AHTD (A): polygons; fields type, source, boundary_n, verified; built by the State Highway Dept. with AGFC, State Parks, NWR, Corps input; no date | AHTD | mixes city/county parks in | **NO** |
| **Trails** | https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Environment/MapServer/22 ARKANSAS_TRAILS (A): polylines, name, surface_type, accessibility, data_source; credit Arkansas State Parks + ANHC; no date | AR State Parks / ANHC | | **NO** |

## 2. Unjoined (54)
- **15 "State Trails" that are driving routes:** Pig Trail Scenic Byway, Scenic 7 Byway, Talimena, Mount Magazine, Ozark Highlands, Sylamore, Camden Expedition, Civil War Trail, Southwest Trail, Butterfield, Saracen, Crowley's Ridge Parkway, St. Francis, Great River Road etc. → **roads, not trails**: grey area SC2-1.
- Real trails: West-Northwest State Trail US-10426, True Grit State Trail 10715, Ozark Highlands Trail 10508, Arkansas River Water Trail 13229, Upper Illinois River Water Trail 13461, Ouachita NRT 10258 → ARKANSAS_TRAILS (A) for land trails; water trails = river kind.
- State recreation/fishing lakes: Peppers Pond 12078, Sugarloaf Mountain 12093, Cherokee SRA 7522, Huckabee Lake 9169, Tates Bluff 11874, Iron Fork Reservoir 11873, Lake Wilhelmina 11870, Lake June 13556, Highway 7 Rec Area 11214, White Rock Mountain 11155, Blanchard Springs 7442, DeGray Lower Lake 7443, Nimrood Lake 7444 (Corps and USFS lakes), Muddy Creek WMA 11394, Joe Hogan SCA 12753: AGFC layer in key – **name suspects**, or on Corps/USFS land.
- 3 State Fish Hatcheries, 3 Nature Centers (AGFC nature centers 11354–11356), Rohwer Relocation Center 11233, Old State House Museum 12086, Chalk Bluff Battlefield 11165: pin-only candidates.
- Hunt Family (J.B. and Johnelle Hunt) 11951, Janet Huckabee Arkansas River Trail 11960, Mike Huckabee Delta Rivers 7525: trails.

## 3. Trails and access
Parking, facilities, gates, water access read. Add ARKANSAS_TRAILS.

## 4. Tricky land
- **Corps lakes** (DeGray, Greers Ferry, Bull Shoals, Beaver, Norfork): state parks on Corps-owned land.
- **Ouachita and Ozark-St. Francis NFs** with AGFC WMAs inside (cooperative).
- Scenic byway "trails" = roads.

## 5. KNOWN-GOOD layers
1. AHTD PUBLIC_LAND_BOUNDARIES (A)
2. AR State Parks (sgarb)
3. AGFC WMAs
4. ARKANSAS_TRAILS (A)
5. ANHC natural areas (sgara)
6. USFS Ouachita / Ozark ownership

## 6. 2-fers
Confident (C): Ouachita NF vs. each AGFC WMA wholly in the forest (cooperative on USFS land): same land. Hard: Corps lake parks vs. state parks on same lake.
