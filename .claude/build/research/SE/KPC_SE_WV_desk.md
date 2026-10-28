# Southeast Source Book: WEST VIRGINIA (desk, Oct 27 2026)
Grades: A opened and read, B surfaced by search only, C inference. Read only.

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / license | Read? |
|---|---|---|---|---|
| WMAs | sgwva (our key). Same data also in https://services.wvgis.wvu.edu/arcgis/rest/services/Boundaries/wv_protected_lands/MapServer (A): state WMAs, State Forests, State Parks, TNC preserves, local lands, National Forests, NPS, NWRs in one service | WV GIS Technical Center (WVU); credit WV DNR | no date, license field blank (A) | WMAs yes |
| State forests | sgwvb (services9.arcgis.com/SQbkdxLkuQJuLGtx) | WV Division of Forestry | | YES |
| State parks | sgwvc gis.transportation.wv.gov Boundaries/MapServer/10 | WV DOT GIS (data from DNR) | | YES |
| Rail trails / state trails | https://gis.transportation.wv.gov/arcgis/rest/services/Hosted/WVSRA_RailTrails/FeatureServer/0 (A): statewide inventory of 6,800+ miles of public trails, lines + points | WV GIS Tech Center with WV DOT | "Data last updated: August 2021" (A); copyright WVGISTC, WVDOT | **NO** (this covers Elk River Trail, North Bend Rail Trail, Greenbrier River Trail, and AT sections) |
| Protected lands (ref copy) | …/Boundaries/wv_protected_lands_ref/MapServer (B) | WVGISTC | | NO |

## 2. POTA parks with no outline (12)
- Trails: US-10031 Elk River Trail, US-9741 North Bend Rail Trail, US-9742 Greenbrier River Trail → **WVSRA_RailTrails** (A). AT and Lewis & Clark NHT US-4572 → national trail lines.
- US-9739 Forks of the Coal SNA, US-9915 Cedar Lakes SRA → possibly wv_protected_lands "local lands/TNC"; **uncovered unless matched** (C).
- US-12052…12056 five State Fish Hatcheries → **UNCOVERED**, no layer (small points; hatcheries are not hunting-land; treat as pin-only).

## 3. Trail lines and access
Read: West_Virginia_Parking_Areas, Public_Fishing_Access_Sites. Add: WVSRA_RailTrails lines.

## 4. Tricky land
- **WMAs inside Monongahela and George Washington NFs.** WV's WMA layer is named "WMA minus national forest" in the WVGISTC metadata (B: wvgis.wvu.edu metadata "WMA_minus_national_forest_utm83"), which means the state WMA polygons **exclude** national forest land. A WMA that is mostly USFS land (e.g. Cheat/Greenbrier-area WMAs) may show only its state part. Good for rule 14, but outlines may look smaller than the hunting map.
- **Corps lakes:** Bluestone WMA / Bluestone SP (Corps land managed by state, B), Summersville, Sutton, Burnsville lake WMAs, R.D. Bailey, Stonewall Jackson (WMA on Corps land). Expect 2-fer-looking pairs where a state park and a WMA both sit on the same Corps lake (Bluestone SP + Bluestone WMA touch/overlap).
- **Rail trails:** state rail trails (Greenbrier, North Bend) are lines; North Bend Rail Trail crosses North Bend SP.
- **Water-only:** New River Gorge National Park & Preserve lies in the river; Gauley River NRA.

## 5. KNOWN-GOOD layers (WV)
1. WVGISTC wv_protected_lands MapServer (A)
2. WV WMA layer (sgwva)
3. WV State Forests (sgwvb)
4. WV State Parks (DOT Boundaries/10)
5. WVSRA_RailTrails (A)
6. West_Virginia_Parking_Areas, Public_Fishing_Access_Sites (access)

## 6. 2-fers to expect
Confident (B): North Bend SP vs. North Bend Rail Trail (the trail runs through the park: line inside polygon, a real overlap); Bluestone SP vs. Bluestone WMA (same Corps lake; **verify polygons**, not sure); Little Beaver SP vs. nothing; New River Gorge NPP vs. Grandview/Babcock SP (adjacent, Grandview SP is inside the NPP boundary? Grandview is a state park within the park's overall area; ownership differs: expect "side by side").
Not sure: Cacapon Resort SP vs. Cacapon WMA... none known.
