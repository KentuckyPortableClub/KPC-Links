# Pacific Source Book: WASHINGTON (desk, Oct 27 2026)
Key: 536 parks, 68 unjoined (13 State Forests, 16 State Recreation Sites, 11 BLM). Layers: sgwaa State Parks (services5.arcgis.com/4LKAHwqnBooVDUlX), sgwab WDFW, sgwac DNR (natural areas), sgwad DNR Non-DNR major public lands, sgwae Ecology waterbodies.

## 1. Official boundaries
| Type | Layer | Publisher | Read? |
|---|---|---|---|
| State parks | sgwaa; ParkBoundaries FeatureServer (services5.arcgis.com/4LKAHwqnBooVDUlX, B) | WA State Parks | YES |
| WDFW lands | sgwab (geodataservices.wdfw.wa.gov) | WDFW | YES |
| DNR natural areas | sgwac (gis.dnr.wa.gov/site3) | WA DNR | YES |
| **DNR recreation sites and state forests** | https://gis.dnr.wa.gov/site2/rest/services/Recreation/DNR_Recreation_Sites/MapServer (B; also Public_Recreation FeatureServer) | WA DNR | **NO** |
| State forests (DNR "State Forest Trust" lands) | DNR managed lands: the Oct 26 gap hunt tried "WA DNR managed lands (1 park)": **I count 13 unjoined state forests, so names must differ** | WA DNR | partly |
| State trails | Spokane River Centennial Trail 3171: none as line | | NO |

## 2. Unjoined (68)
- **13 State Forests** (Ahtanum, Blanchard, Capitol, Elbe Hills-Tahoma, Green Mountain-Tahuya, Little Pend Oreille, Loomis-Loup Loup, Marckworth, Naneum Ridge, Olympic Peninsula, Raging River, Teanaway, Yacolt Burn): DNR layers, **name mismatch suspects ("Capitol State Forest" vs. "Capitol Forest")**; Little Pend Oreille is WDFW/ DNR.
- **16 State Recreation Sites** (Columbia River access sites: Big Eddy, Jonker, Olequa Crossing, Massey Bar, Woodland Bar, Three Mile, County Line, Steel Bridge, Hand, Puget Island, Deep River, Highway 4; plus Dragoon Creek, Sherry Creek, Rocky Lake, Skookum Creek, Sheep Creek, Douglas Falls, Beverly Dunes): DNR / WDFW water-access sites: **pin-size**.
- Bayview SP 3157 (name suspect); Chief Joseph SWA 6473 (WDFW); 3 State Fishing Lakes (Hog Canyon, Jump Off Joe, Horseshoe-Kitsap).
- Spokane River Centennial Trail 3171 (line).
- 11 BLM: BLM POINT PARKS. Federal: Umatilla NF, Idaho Panhandle NF, Columbia River Gorge NSA, Hanford Reach NM, Mt. St. Helens NVM, Minidoka NHS, WSRs, PCT, Pacific NW NST.

## 3. Trails and access
Parking, kiosks, hand launches, boat ramps, park entrances, parking-lot polygons, trailheads read.

## 4. Tricky land
- **DNR state forest trust lands**: public, but timber trust; recreation sites on top.
- **Parks on federal reservoirs** (Lake Chelan on BuRec/USFS; Lake Roosevelt NRA): NPS-managed on BuRec land.
- Puget Sound beaches (tidelands owned by DNR).

## 5. KNOWN-GOOD layers
1. WA State Parks boundaries (sgwaa)
2. WDFW lands (sgwab)
3. DNR natural areas + Non-DNR public lands (sgwac, sgwad)
4. DNR_Recreation_Sites (B)
5. State parks trailheads and entrances
6. USFS ownership; Hanford Reach

## 6. 2-fers
Confident (B): none. Hard: Capitol State Forest vs. Capitol Forest recreation (same DNR land).
