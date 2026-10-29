# Lake parks: official department maps (round LK, chat 9, Oct 29 2026)

Source: look-up bot chunks 9-lk1..4 (the 240-min probe run 40910514673 was cancelled with no results; refiled as 4 chunks, all answered). REVIEW ONLY: nothing is in a key. ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.

## What was done
For each of 557 US lake-type POTA parks: polygons within 150 m of the pin in up to 5 known state layers per state (state-gis.json: park / wildlife / land / preserve / forest), names + acres, plus the USGS lake polygon's acres at the pin. SHORE = the department polygon is more than 15% bigger than the lake (so it includes shore land).

- **FOUND** = a polygon from a state-agency boundary layer at the pin.
- **WEAK** = only a water / parcel / basemap / habitat / hunting layer hit (not a department boundary: does NOT count).
- **NOT FOUND** = the state's layers opened, nothing at the pin.
- **NO LAYER READ** = no usable layer for the state (the nationwide Regrid parcel layer returned HTTP 404 and is ignored).

A polygon at the pin is not a name match: R-G7 name rules still decide. The ArcGIS-search step (up to 3 new layers per state) added nothing that opened. Idaho: its only polygon layer is the Fish and Game hydrography (lake) layer, so 82 of 90 Idaho parks are WEAK.

## Totals: 557 parks

- FOUND 398 (of which SHORE 179), WEAK 94, NOT FOUND 47, NO LAYER READ 18

## Per state

| state | parks | FOUND | of which SHORE | WEAK | NOT FOUND | NO LAYER READ |
|---|---|---|---|---|---|---|
| AL | 18 | 17 | 2 | 0 | 1 | 0 |
| AR | 15 | 0 | 0 | 10 | 5 | 0 |
| CA | 2 | 2 | 2 | 0 | 0 | 0 |
| CO | 26 | 15 | 9 | 0 | 11 | 0 |
| CT | 1 | 1 | 0 | 0 | 0 | 0 |
| DE | 29 | 29 | 11 | 0 | 0 | 0 |
| FL | 2 | 2 | 0 | 0 | 0 | 0 |
| GA | 16 | 16 | 9 | 0 | 0 | 0 |
| IA | 18 | 18 | 12 | 0 | 0 | 0 |
| ID | 90 | 6 | 3 | 82 | 2 | 0 |
| IN | 8 | 8 | 2 | 0 | 0 | 0 |
| KS | 49 | 47 | 38 | 0 | 2 | 0 |
| LA | 6 | 5 | 0 | 0 | 1 | 0 |
| MA | 4 | 4 | 2 | 0 | 0 | 0 |
| ME | 1 | 1 | 0 | 0 | 0 | 0 |
| MI | 16 | 16 | 11 | 0 | 0 | 0 |
| MN | 12 | 8 | 1 | 0 | 4 | 0 |
| MO | 3 | 3 | 1 | 0 | 0 | 0 |
| MS | 18 | 0 | 0 | 0 | 0 | 18 |
| MT | 12 | 12 | 2 | 0 | 0 | 0 |
| NC | 2 | 2 | 1 | 0 | 0 | 0 |
| ND | 15 | 15 | 5 | 0 | 0 | 0 |
| NE | 15 | 13 | 9 | 0 | 2 | 0 |
| NJ | 6 | 6 | 3 | 0 | 0 | 0 |
| NV | 5 | 2 | 0 | 0 | 3 | 0 |
| NY | 9 | 9 | 3 | 0 | 0 | 0 |
| OK | 19 | 13 | 8 | 0 | 6 | 0 |
| OR | 6 | 5 | 2 | 0 | 1 | 0 |
| SC | 5 | 5 | 3 | 0 | 0 | 0 |
| TN | 11 | 10 | 3 | 0 | 1 | 0 |
| TX | 2 | 2 | 1 | 0 | 0 | 0 |
| UT | 6 | 3 | 1 | 0 | 3 | 0 |
| VT | 1 | 1 | 0 | 0 | 0 | 0 |
| WA | 82 | 80 | 18 | 2 | 0 | 0 |
| WV | 21 | 21 | 16 | 0 | 0 | 0 |
| WY | 6 | 1 | 1 | 0 | 5 | 0 |

## Per park

| ref | st | park | verdict | biggest department polygon at the pin |
|---|---|---|---|---|
| US-12803 | AL | Lee County State Public Fishing Lake | FOUND | Lee County Public Fishing Lake 120 ac (lake 130 ac) [PublicFishingLakes] |
| US-12963 | AL | Washington County State Public Fishing Lake | FOUND | Washington County Public Fishing Lake 80 ac (lake 80 ac) [PublicFishingLakes] |
| US-12964 | AL | Dallas County State Public Fishing Lake | FOUND | Dallas County Public Fishing Lake 88 ac [PublicFishingLakes] |
| US-12965 | AL | Dale Country State Public Fishing Lake | FOUND | Dale County Public Fishing Lake 84 ac (lake 90 ac) [PublicFishingLakes] |
| US-12966 | AL | Geneva County State Public Fishing Lake | FOUND | Geneva County Public Fishing Lake 59 ac (lake 29 ac) SHORE [PublicFishingLakes] |
| US-12967 | AL | Chambers County State Public Fishing Lake | FOUND | Chambers County Public Fishing Lake 172 ac (lake 191 ac) [PublicFishingLakes] |
| US-12968 | AL | Walker County State Public Fishing Lake | NOT FOUND |  |
| US-12969 | AL | Marion County State Public Fishing Lake | FOUND | Marion County Public Fishing Lake 39 ac (lake 39 ac) [PublicFishingLakes] |
| US-12970 | AL | Madison County Public State Fishing Lake | FOUND | Madison County Public Fishing Lake 98 ac (lake 102 ac) [PublicFishingLakes] |
| US-13317 | AL | Coffee County State Public Fishing Lake | FOUND | Coffee County Public Fishing Lake 78 ac (lake 76 ac) [PublicFishingLakes] |
| US-13318 | AL | Pike County State Public Fishing Lake | FOUND | Pike County Public Fishing Lake 44 ac (lake 40 ac) [PublicFishingLakes] |
| US-13338 | AL | Clay County State Public Fishing Lake | FOUND | Clay County Public Fishing Lakes 71 ac (lake 39 ac) SHORE [PublicFishingLakes] |
| US-13340 | AL | DeKalb County State Public Fishing Lake | FOUND | DeKalb County Public Fishing Lake 120 ac (lake 118 ac) [PublicFishingLakes] |
| US-13342 | AL | Bibb Country State Public Fishing Lake | FOUND | Bibb County Public Fishing Lake 107 ac (lake 95 ac) [PublicFishingLakes] |
| US-13343 | AL | Fayette County State Public Fishing Lake | FOUND | Fayette County Public Fishing Lake 59 ac (lake 58 ac) [PublicFishingLakes] |
| US-13344 | AL | Lamar County State Public Fishing Lake | FOUND | Lamar County Public Fishing Lake 58 ac (lake 60 ac) [PublicFishingLakes] |
| US-13345 | AL | Monroe County State Public Fishing Lake | FOUND | Monroe County Public Fishing Lake 77 ac (lake 84 ac) [PublicFishingLakes] |
| US-3714 | AL | Yates Lake Wildlife Management Area | FOUND | Forever Wild Gothard - AWF Yates Lake WM 5926 ac [WildlifeManagementAreas] |
| US-10424 | AR | Upper White Oak Lake Recreation Area State Fis | WEAK | Lower White Oak Lake 1110 ac (lake 1045 ac) [lakes] |
| US-11353 | AR | Kirk Dupps Beaver Lake Wildlife Management Are | NOT FOUND |  |
| US-11870 | AR | Lake Wilhelmina State Fishing Lake | WEAK | Wilhelmina Lake 190 ac (lake 198 ac) [lakes] |
| US-11873 | AR | Iron Fork Reservoir State Fishing Lake | WEAK | Iron Forks Lake 301 ac (lake 283 ac) [lakes] |
| US-13553 | AR | Sugar Loaf Lake State Fishing Lake | WEAK | Sugar Loaf Lake 289 ac (lake 291 ac) [lakes] |
| US-13554 | AR | Lake Atkins State Fishing Lake | WEAK | Lake Atkins 620 ac [lakes] |
| US-13556 | AR | Lake June State Fishing Lake | WEAK | June Lake - Lafayette 61 ac (lake 60 ac) [lakes] |
| US-7265 | AR | Big Lake Wildlife Management Area | NOT FOUND |  |
| US-7268 | AR | Brewer Lake Wildlife Management Area | NOT FOUND |  |
| US-7283 | AR | DeQueen Lake Wildlife Management Area | WEAK | DeQueen Lake 1678 ac (lake 1625 ac) [lakes] |
| US-7301 | AR | Lake Greeson Wildlife Management Area | WEAK | Lake Greeson 6849 ac (lake 7090 ac) [lakes] |
| US-7302 | AR | Lake Overcup Wildlife Management Area | WEAK | Lake Overcup 843 ac (lake 805 ac) [lakes] |
| US-7310 | AR | Norfolk Lake Wildlife Management Area | NOT FOUND |  |
| US-7342 | AR | Henry Gray Hurricane Lake Wildlife Management  | NOT FOUND |  |
| US-7349 | AR | Ozark Lake Wildlife Management Area | WEAK | Ozark Lake 9973 ac (lake 9421 ac) [lakes] |
| US-3408 | CA | Bethany Reservoir State Recreation Area | FOUND | STEVE THOMPSON NORTH CENTRAL VALLEY WILD 4768847 ac (lake 164 ac) SHORE [FWSApproved_Authoritative] |
| US-3558 | CA | San Luis Reservoir State Recreation Area | FOUND | San Luis Reservoir SRA 25448 ac (lake 12831 ac) SHORE [ParkBoundaries] |
| US-0190 | CO | Flagler Reservoir State Wildlife Area | NOT FOUND |  |
| US-11892 | CO | Jerry Creek Reservoirs State Wildlife Area | FOUND | Jerry Creek Reservoir SWA 864 ac [CPWAdminData] |
| US-11895 | CO | Tarryall Reservoir State Wildlife Area | FOUND | Tarryall Reservoir SWA 882 ac (lake 189 ac) SHORE [CPWAdminData] |
| US-11924 | CO | Douglas Reservoir State Wildlife Area | FOUND | Douglas Reservoir SWA 760 ac (lake 5 ac) SHORE [CPWAdminData] |
| US-1224 | CO | John Martin Reservoir State Park | FOUND | John Martin Reservoir State Park 1707 ac [CPWAdminData] |
| US-12355 | CO | Jumbo Reservoir State Wildlife Area | FOUND | Jumbo Reservoir (Julesburg) SWA 1720 ac (lake 1418 ac) SHORE [CPWAdminData] |
| US-12707 | CO | Pastorius Reservoir State Wildlife Area | FOUND | Pastorius Reservoir SWA 79 ac (lake 47 ac) SHORE [CPWAdminData] |
| US-12756 | CO | Mountain Home Reservoir State Wildlife Area | FOUND | Mountain Home Reservoir SWA 1058 ac [CPWAdminData] |
| US-13109 | CO | Narraguinnep Reservoir State Wildlife Area | FOUND | Narraguinnep Resevoir SWA 770 ac (lake 544 ac) SHORE [CPWAdminData] |
| US-13110 | CO | Skaguay Reservoir State Wildlife Area | FOUND | Skaguay Reservoir SWA 706 ac (lake 109 ac) SHORE [CPWAdminData] |
| US-8296 | CO | Karval Reservoir State Wildlife Area | FOUND | Karval Reservoir SWA 228 ac (lake 20 ac) SHORE [CPWAdminData] |
| US-9604 | CO | Alberta Park Reservoir State Wildlife Area | FOUND | Alberta Park Reservoir SWA 35 ac (lake 36 ac) [CPWAdminData] |
| US-9610 | CO | Beaver Creek Reservoir State Wildlife Area | NOT FOUND |  |
| US-9614 | CO | Big Meadows Reservoir State Wildlife Area | NOT FOUND |  |
| US-9621 | CO | Boedecker Reservoir State Wildlife Area | FOUND | Boedecker Reservoir SWA 426 ac (lake 376 ac) [CPWAdminData] |
| US-9630 | CO | Clear Creek Reservoir State Wildlife Area | FOUND | Clear Creek Reservoir SWA 687 ac (lake 2 ac) SHORE [CPWAdminData] |
| US-9642 | CO | Deweese Reservoir State Wildlife Area | NOT FOUND |  |
| US-9647 | CO | Echo Canyon Reservoir State Wildlife Area | NOT FOUND |  |
| US-9655 | CO | Holbrook Reservoir State Wildlife Area | NOT FOUND |  |
| US-9657 | CO | Horse Creek Reservoir State Wildlife Area | NOT FOUND |  |
| US-9660 | CO | Joe Moore Reservoir State Wildlife Area | NOT FOUND |  |
| US-9664 | CO | Prewitt Reservoir State Wildlife Area | FOUND | Prewitt Reservoir SWA 2739 ac (lake 78 ac) SHORE [CPWAdminData] |
| US-9671 | CO | Smith Reservoir State Wildlife Area | NOT FOUND |  |
| US-9672 | CO | Terrace Reservoir State Wildlife Area | FOUND | Terrace Reservoir SWA 254 ac [CPWAdminData] |
| US-9674 | CO | Totten Reservoir State Wildlife Area | NOT FOUND |  |
| US-9677 | CO | Williams Creek Reservoir State Wildlife Area | NOT FOUND |  |
| US-1679 | CT | Higganum Reservoir State Park | FOUND | Higganum Reservoir State Park 136 ac [Connecticut_DEEP_Property] |
| US-10667 | DE | Abbotts Pond State Fishing Lake | FOUND | Abbotts Pond 50 ac (lake 16 ac) SHORE [Environmental] |
| US-10668 | DE | Andrews State Fishing Lake | FOUND | Andrews Lake 34 ac [Environmental] |
| US-10669 | DE | Blairs Pond State Fishing Lake | FOUND | Milford Millponds 201 ac [Environmental] |
| US-10670 | DE | Chipmans Pond State Fishing Lake | FOUND | Chipmans Pond 74 ac (lake 55 ac) SHORE [Environmental] |
| US-10671 | DE | Concord Pond State Fishing Lake | FOUND | Concord Pond 88 ac [Environmental] |
| US-10672 | DE | Coursey Pond State Fishing Lake | FOUND | Coursey Pond 61 ac (lake 60 ac) [Environmental] |
| US-10673 | DE | Craigs Pond State Fishing Lake | FOUND | Craigs Pond 21 ac (lake 16 ac) SHORE [Environmental] |
| US-10674 | DE | Derby Pond State Fishing Lake | FOUND | Derby Pond 40 ac (lake 23 ac) SHORE [Environmental] |
| US-10675 | DE | Garrisons State Fishing Lake | FOUND | Garrisons Lake 86 ac [Environmental] |
| US-10676 | DE | Griffith State Fishing Lake | FOUND | Griffiths Lake and Access Site 1 ac (lake 39 ac) [Environmental] |
| US-10677 | DE | Haven State Fishing Lake | FOUND | Haven Lake 85 ac (lake 86 ac) [Environmental] |
| US-10678 | DE | Hearns Pond State Fishing Lake | FOUND | Hearns Pond 74 ac (lake 61 ac) SHORE [Environmental] |
| US-10679 | DE | Horseys Pond State Fishing Lake | FOUND | Horseys Pond 59 ac (lake 58 ac) [Environmental] |
| US-10680 | DE | Ingrams Pond State Fishing Lake | FOUND | Ingram Pond and Access Site 125 ac (lake 57 ac) SHORE [Environmental] |
| US-10681 | DE | Masseys Millpond State Fishing Lake | FOUND | Massey Mill Pond 37 ac [Environmental] |
| US-10682 | DE | McGinnis Pond State Fishing Lake | FOUND | McGinnis Pond Wildlife Area 103 ac (lake 38 ac) SHORE [Environmental] |
| US-10683 | DE | Millsboro Pond State Fishing Lake | FOUND | Millsboro Access Site 0 ac [Environmental] |
| US-10684 | DE | Moores State Fishing Lake | FOUND | Moores Lake 48 ac [Environmental] |
| US-10685 | DE | Mud Mill Pond State Fishing Lake | FOUND | Mud Mill Pond 53 ac (lake 40 ac) SHORE [Environmental] |
| US-10686 | DE | Portsville Pond State Fishing Lake | FOUND | Portsville Pond 13 ac (lake 18 ac) [Environmental] |
| US-10687 | DE | Trussum Pond State Fishing Lake | FOUND | Trap Pond State Park 898 ac [Environmental] |
| US-10688 | DE | Tubmill Pond State Fishing Lake | FOUND | Tub Mill Pond and Access Site 11 ac (lake 82 ac) [Environmental] |
| US-10689 | DE | Tussock Pond State Fishing Lake | FOUND | Tussock Pond 4 ac (lake 6 ac) [Environmental] |
| US-10690 | DE | Wagamons Pond State Fishing Lake | FOUND | Wagamons Pond 44 ac (lake 42 ac) [Environmental] |
| US-10691 | DE | Waples Pond State Fishing Lake | FOUND | Waples Pond 82 ac (lake 51 ac) SHORE [Environmental] |
| US-11809 | DE | Becks Pond State Fishing Lake | FOUND | Becks Pond 18 ac (lake 28 ac) [Environmental] |
| US-11810 | DE | Raccoon Pond State Fishing Lake | FOUND | Trap Pond State Park 1330 ac (lake 44 ac) SHORE [Environmental] |
| US-11811 | DE | Records Pond State Fishing Lake | FOUND | Records Pond 96 ac (lake 84 ac) [Environmental] |
| US-11812 | DE | Trap Pond State Fishing Lake | FOUND | Trap Pond State Park 1330 ac (lake 95 ac) SHORE [Environmental] |
| US-0245 | FL | Lake Wales Ridge Wildlife Management Area | FOUND | Lake Wales Ridge Ecosystem 1 ac (lake 2192 ac) [OpenData] |
| US-6322 | FL | Salt Lake Wildlife Management Area | FOUND | Salt Lake Wildlife Management Area 5311 ac [SJRWMD_Management_Area_viewL] |
| US-3775 | GA | Silver Lake Wildlife Management Area | FOUND | SILVER LAKE WMA 9686 ac (lake 317 ac) SHORE [WRD_WMA_Public] |
| US-7455 | GA | Lake Russell Wildlife Management Area | FOUND | LAKE RUSSELL WMA 17272 ac [WRD_WMA_Public] |
| US-7461 | GA | Ocmulgee State Fishing Lake | FOUND | OCMULGEE WMA 13473 ac [WRD_WMA_Public] |
| US-7462 | GA | Big Lazer Creek State Fishing Lake | FOUND | BIG LAZER CREEK WMA 7011 ac (lake 195 ac) SHORE [WRD_WMA_Public] |
| US-7463 | GA | Dodge County State Fishing Lake | FOUND | DODGE COUNTY PFA 443 ac (lake 101 ac) SHORE [WRD_WMA_Public] |
| US-7464 | GA | Evans County State Fishing Lake | FOUND | EVANS COUNTY PFA 366 ac (lake 65 ac) SHORE [WRD_WMA_Public] |
| US-7465 | GA | Flat Creek State Fishing Lake | FOUND | FLAT CREEK PFA 852 ac [WRD_WMA_Public] |
| US-7466 | GA | Hugh M. Gillis State Fishing Lake | FOUND | HUGH GILLIS PFA 735 ac (lake 111 ac) SHORE [WRD_WMA_Public] |
| US-7467 | GA | Marben State Fishing Lake | FOUND | CLYBEL WMA 6562 ac [WRD_WMA_Public] |
| US-7468 | GA | McDuffie State Fishing Lake | FOUND | MCDUFFIE PFA 552 ac (lake 11 ac) SHORE [WRD_WMA_Public] |
| US-7469 | GA | Paradise State Fishing Lake | FOUND | PARADISE PFA 1332 ac (lake 1 ac) SHORE [WRD_WMA_Public] |
| US-7470 | GA | Silver Lake State Fishing Lake | FOUND | SILVER LAKE WMA 9686 ac (lake 317 ac) SHORE [WRD_WMA_Public] |
| US-7899 | GA | Carter's Lake Wildlife Management Area | FOUND | CARTERS LAKE WMA 8760 ac (lake 815 ac) SHORE [WRD_WMA_Public] |
| US-7911 | GA | Lake Walter F. George Wildlife Management Area | FOUND | LAKE WALTER F. GEORGE WMA 142 ac [WRD_WMA_Public] |
| US-9786 | GA | Lake Seminole Wildlife Management Area | FOUND | LAKE SEMINOLE WMA 994 ac (lake 10501 ac) [WRD_WMA_Public] |
| US-9791 | GA | Morgan Lake Wildlife Management Area | FOUND | MORGAN LAKE WMA 1484 ac [WRD_WMA_Public] |
| US-9299 | IA | Hawthorne Lake Wildlife Management Area | FOUND | HAWTHORN WILDLIFE AREA 1793 ac [Recreation] |
| US-9301 | IA | Lake Sugema Wildlife Management Area | FOUND | LAKE SUGEMA WILDLIFE AREA 2382 ac (lake 0 ac) SHORE [Recreation] |
| US-9303 | IA | Fogle Lake Wildlife Management Area | FOUND | FOGLE LAKE 355 ac (lake 38 ac) SHORE [Recreation] |
| US-9305 | IA | Lake Shawtee Wildlife Management Area | FOUND | LAKE SHAWTEE 1160 ac [Recreation] |
| US-9307 | IA | Forney's Lake Wildlife Management Area | FOUND | FORNEY LAKE 1117 ac (lake 398 ac) SHORE [Recreation] |
| US-9310 | IA | Nobles Lake Wildlife Management Area | FOUND | NOBLES LAKE WILDLIFE AREA 230 ac (lake 31 ac) SHORE [Recreation] |
| US-9311 | IA | Keg Creek lake Wildlife Management Area | FOUND | KEG CREEK I-29 WILDLIFE AREA 102 ac (lake 55 ac) SHORE [Recreation] |
| US-9313 | IA | Round Lake Wildlife Management Area | FOUND | ROUND LAKE WILDLIFE AREA 432 ac (lake 167 ac) SHORE [Recreation] |
| US-9314 | IA | Beaver Lake Wildlife Management Area | FOUND | BEAVER LAKE WILDLIFE AREA 295 ac [Recreation] |
| US-9315 | IA | Three Mile Lake Wildlife Management Area | FOUND | THREE MILE WILDLIFE AREA 2663 ac (lake 836 ac) SHORE [Recreation] |
| US-9319 | IA | Goose Lake Wildlife Management Area | FOUND | GOOSE LAKE WILDLIFE AREA 1275 ac (lake 196 ac) SHORE [Recreation] |
| US-9322 | IA | Morse Lake Wildlife Management Area | FOUND | MORSE LAKE WILDLIFE AREA 231 ac (lake 106 ac) SHORE [Recreation] |
| US-9323 | IA | Lower Morse Lake Wildlife Management Area | FOUND | LOWER MORSE LAKE WILDLIFE AREA 303 ac [Recreation] |
| US-9324 | IA | Elm Lake Wildlife Management Area | FOUND | ELM LAKE WILDLIFE AREA 778 ac (lake 336 ac) SHORE [Recreation] |
| US-9328 | IA | Little Storm Lake Wildlife Management Area | FOUND | Storm Lake 3042 ac (lake 3108 ac) [Boundaries] |
| US-9329 | IA | Rush Lake Wildlife Management Area | FOUND | RUSH LAKE - OSCEOLA 338 ac (lake 276 ac) SHORE [Recreation] |
| US-9331 | IA | Eagle Lake Wildlife Management Area | FOUND | EAGLE LAKE NATURE AREA 109 ac [Recreation] |
| US-9349 | IA | Lost Grove Lake Wildlife Management Area | FOUND | LOST GROVE LAKE WILDLIFE AREA 1689 ac (lake 361 ac) SHORE [Recreation] |
| US-11249 | ID | Salmon Falls Creek Reservoir State Fishing Lak | WEAK | Salmon Falls Creek Reservoir 2692 ac (lake 2887 ac) [Hydrography_Public] |
| US-11250 | ID | Thorn Creek Reservoir BLM Recreation Managemen | WEAK | Thorn Creek Reservoir 117 ac (lake 117 ac) [Hydrography_Public] |
| US-11251 | ID | Magic Reservoir BLM Recreation Management Area | WEAK | Magic Reservoir 3549 ac [Hydrography_Public] |
| US-11252 | ID | GrasmereReservoir State Fishing Lake | WEAK | Grasmere Reservoir 229 ac (lake 94 ac) [Hydrography_Public] |
| US-11253 | ID | Fish Creek Reservoir BLM Recreation Management | WEAK | Fish Creek Reservoir 356 ac (lake 245 ac) [Hydrography_Public] |
| US-11256 | ID | Brownlee/Oxbow Reservoir BLM Recreation Manage | WEAK | Brownlee Reservoir 10990 ac (lake 12535 ac) [Hydrography_Public] |
| US-11257 | ID | Crane Creek Reservoir State Fishing Lake | WEAK | Crane Creek Reservoir 2286 ac [Hydrography_Public] |
| US-11258 | ID | Mormon Reservoir State Fishing Lake | WEAK | Mormon Reservoir 1574 ac (lake 1440 ac) [Hydrography_Public] |
| US-11262 | ID | Cedar Creek Reservoir State Fishing Lake | WEAK | Cedar Creek Reservoir 864 ac (lake 958 ac) [Hydrography_Public] |
| US-11308 | ID | Blackfoot Reservoir Recreation Site BLM Recrea | WEAK | Blackfoot Reservoir 16898 ac (lake 16914 ac) [Hydrography_Public] |
| US-11312 | ID | Hawkins Reservoir Recreation Site BLM Recreati | WEAK | Hawkins Reservoir 40 ac (lake 50 ac) [Hydrography_Public] |
| US-11325 | ID | Wilson Lake Reservoir State Fishing Lake | WEAK | Wilson Lake Reservoir 510 ac (lake 489 ac) [Hydrography_Public] |
| US-11341 | ID | Little Wood Reservoir BLM Recreation Managemen | WEAK | Little Wood Reservoir 515 ac (lake 578 ac) [Hydrography_Public] |
| US-11379 | ID | Paddock Valley Reservoir State Fishing Lake | WEAK | Paddock Valley Reservoir 1170 ac (lake 1182 ac) [Hydrography_Public] |
| US-11380 | ID | Mann Creek Reservoir State Fishing Lake | WEAK | Mann Creek Reservoir 274 ac [Hydrography_Public] |
| US-11381 | ID | Black Canyon Reservoir Management Area | WEAK | Black Canyon Reservoir 878 ac [Hydrography_Public] |
| US-11382 | ID | Mountain Home Reservoir State Fishing Lake | WEAK | Mountain Home Reservoir 400 ac (lake 209 ac) [Hydrography_Public] |
| US-11383 | ID | Little Camas Reservoir State Fishing Lake | WEAK | Little Camas Reservoir 969 ac (lake 1048 ac) [Hydrography_Public] |
| US-11384 | ID | Anderson Ranch Reservoir Management Area | WEAK | Anderson Ranch Reservoir 4590 ac (lake 4516 ac) [Hydrography_Public] |
| US-11385 | ID | Arrowrock Reservoir State Fishing Lake | WEAK | Arrowrock Reservoir 2999 ac (lake 2288 ac) [Hydrography_Public] |
| US-11386 | ID | Lucky Peak Reservoir State Fishing Lake | WEAK | Lucky Peak Reservoir 2788 ac (lake 2762 ac) [Hydrography_Public] |
| US-11387 | ID | Lake Cascade Reservoir Management Area | WEAK | Cascade Reservoir 27014 ac (lake 25043 ac) [Hydrography_Public] |
| US-11388 | ID | Indian Creek Reservoir State Fishing Lake | WEAK | Indian Creek Reservoir 127 ac (lake 43 ac) [Hydrography_Public] |
| US-11389 | ID | Long Tom Reservoir State Fishing Lake | NOT FOUND |  |
| US-11390 | ID | Dog Creek Reservoir State Fishing Lake | WEAK | Dog Creek Reservoir 50 ac (lake 52 ac) [Hydrography_Public] |
| US-11391 | ID | Deadwood Reservoir State Fishing Lake | WEAK | Deadwood Reservoir 2982 ac (lake 2961 ac) [Hydrography_Public] |
| US-11416 | ID | Sage Hen Reservoir State Fishing Lake | WEAK | Sage Hen Reservoir 233 ac (lake 238 ac) [Hydrography_Public] |
| US-11417 | ID | Horsethief Reservoir State Fishing Lake | WEAK | Horsethief Reservoir 255 ac (lake 248 ac) [Hydrography_Public] |
| US-11418 | ID | Brundage Reservoir State Fishing Lake | WEAK | Brundage Reservoir 216 ac [Hydrography_Public] |
| US-11419 | ID | Lost Valley Reservoir State Fishing Lake | WEAK | Lost Valley Reservoir 512 ac [Hydrography_Public] |
| US-11420 | ID | Ben Ross Reservoir State Fishing Lake | WEAK | Ben Ross Reservoir 364 ac [Hydrography_Public] |
| US-11421 | ID | Herrick Reservoir State Fishing Lake | WEAK | Herrick Reservoir 36 ac (lake 44 ac) [Hydrography_Public] |
| US-11423 | ID | Blair Trail Reservoir State Fishing Lake | WEAK | Blair Trail Reservoir 195 ac [Hydrography_Public] |
| US-11424 | ID | Bliss Reservoir State Fishing Lake | WEAK | Bliss Reservoir 299 ac (lake 287 ac) [Hydrography_Public] |
| US-11425 | ID | Stone Reservoir State Fishing Lake | WEAK | Stone Reservoir 125 ac (lake 134 ac) [Hydrography_Public] |
| US-11426 | ID | Swan Falls Reservoir State Fishing Lake | WEAK | Swan Falls Reservoir 462 ac [Hydrography_Public] |
| US-11463 | ID | Murtaugh Lake Reservoir State Fishing Lake | WEAK | Murtaugh Lake 827 ac (lake 819 ac) [Hydrography_Public] |
| US-11464 | ID | Blacks Creek Reservoir State Fishing Lake | WEAK | Blacks Creek Reservoir 108 ac (lake 25 ac) [Hydrography_Public] |
| US-11516 | ID | Ashton Reservoir State Fishing Lake | WEAK | Ashton Reservoir 379 ac (lake 287 ac) [Hydrography_Public] |
| US-11517 | ID | American Falls Reservoir State Fishing Lake | WEAK | American Falls Reservoir 55079 ac (lake 35842 ac) [Hydrography_Public] |
| US-11518 | ID | Alexander Reservoir State Fishing Lake | WEAK | Alexander Reservoir 986 ac [Hydrography_Public] |
| US-11519 | ID | Boulder Meadows Reservoir State Fishing Lake | WEAK | Boulder Meadows Reservoir 29 ac (lake 32 ac) [Hydrography_Public] |
| US-11520 | ID | Chesterfield Reservoir State Fishing Lake | WEAK | Chesterfield Reservoir 1243 ac (lake 1264 ac) [Hydrography_Public] |
| US-11521 | ID | Condie Reservoir State Fishing Lake | WEAK | Condie Reservoir 80 ac (lake 86 ac) [Hydrography_Public] |
| US-11522 | ID | Crowthers Reservoir State Fishing Lake | WEAK | Crowthers Reservoir 21 ac (lake 22 ac) [Hydrography_Public] |
| US-11523 | ID | Daniels Reservoir State Fishing Lake | WEAK | Daniels Reservoir 364 ac (lake 230 ac) [Hydrography_Public] |
| US-11524 | ID | Deep Creek Reservoir State Fishing Lake | WEAK | Deep Creek Reservoir 163 ac (lake 168 ac) [Hydrography_Public] |
| US-11525 | ID | Devils Creek Reservoir State Fishing Lake | WEAK | Devil Creek Reservoir 122 ac (lake 130 ac) [Hydrography_Public] |
| US-11526 | ID | Deyo Reservoir State Fishing Lake | WEAK | Deyo Reservoir 48 ac [Hydrography_Public] |
| US-11527 | ID | Foster Reservoir State Fishing Lake | WEAK | Foster Reservoir 131 ac [Hydrography_Public] |
| US-11528 | ID | Tripod Reservoir State Fishing Lake | WEAK | Tripod Reservoir 4 ac (lake 5 ac) [Hydrography_Public] |
| US-11529 | ID | Glendale Reservoir State Fishing Lake | WEAK | Glendale Reservoir 206 ac [Hydrography_Public] |
| US-11530 | ID | Hells Canyon Reservoir State Fishing Lake | WEAK | Hells Canyon Reservoir 2441 ac [Hydrography_Public] |
| US-11531 | ID | Island Park Reservoir State Fishing Lake | WEAK | Island Park Reservoir 7256 ac (lake 7550 ac) [Hydrography_Public] |
| US-11532 | ID | Johnson Reservoir State Fishing Lake | WEAK | Johnson Reservoir 40 ac (lake 44 ac) [Hydrography_Public] |
| US-11534 | ID | Lamont Reservoir State Fishing Lake | WEAK | Lamont Reservoir 83 ac [Hydrography_Public] |
| US-11535 | ID | Little Valley Reservoir State Fishing Lake | WEAK | Little Valley Reservoir 266 ac (lake 166 ac) [Hydrography_Public] |
| US-11536 | ID | Lower Goose Creek Reservoir State Fishing Lake | WEAK | Lower Goose Creek Reservoir 996 ac [Hydrography_Public] |
| US-11537 | ID | Lower Salmon Falls Reservoir State Fishing Lak | WEAK | Lower Salmon Falls Reservoir 873 ac [Hydrography_Public] |
| US-11538 | ID | Moose Creek Reservoir State Fishing Lake | WEAK | Moose Creek Reservoir 31 ac (lake 31 ac) [Hydrography_Public] |
| US-11539 | ID | Mosquito Flat Reservoir State Fishing Lake | WEAK | Mosquito Flat Reservoir 51 ac (lake 49 ac) [Hydrography_Public] |
| US-11540 | ID | Ririe Reservoir State Fishing Lake | WEAK | Ririe Reservoir 1429 ac (lake 1388 ac) [Hydrography_Public] |
| US-11541 | ID | Sheep Creek Reservoir State Fishing Lake | WEAK | Sheep Creek Reservoir 21 ac (lake 22 ac) [Hydrography_Public] |
| US-11542 | ID | Spring valley Reservoir State Fishing Lake | WEAK | Spring Valley Reservoir 46 ac (lake 51 ac) [Hydrography_Public] |
| US-11543 | ID | Treasureton Reservoir State Fishing Lake | WEAK | Treasureton Reservoir 148 ac (lake 151 ac) [Hydrography_Public] |
| US-11544 | ID | Twenty Four Mile Reservoir State Fishing Lake | WEAK | Twentyfour Mile Reservoir 40 ac (lake 37 ac) [Hydrography_Public] |
| US-11545 | ID | Upper Pleasant View Reservoir State Fishing La | WEAK | Upper Pleasantview Reservoir 39 ac (lake 4 ac) [Hydrography_Public] |
| US-11546 | ID | Upper Salmon Falls Reservoir State Fishing Lak | WEAK | Upper Salmon Falls Reservoir 882 ac [Hydrography_Public] |
| US-11578 | ID | Palisades Reservoir State Fishing Lake | WEAK | Palisades Reservoir 15882 ac (lake 13914 ac) [Hydrography_Public] |
| US-11579 | ID | Dworshak Reservoir State Fishing Lake | WEAK | Dworshak Reservoir 16487 ac (lake 16362 ac) [Hydrography_Public] |
| US-11948 | ID | Hornet Reservoir State Fishing Lake | WEAK | Hornet Reservoir 22 ac (lake 32 ac) [Hydrography_Public] |
| US-12112 | ID | Little Payette Lake State Fishing Lake | WEAK | Little Payette Lake 1430 ac (lake 1461 ac) [Hydrography_Public] |
| US-12174 | ID | Jim Moore Pond State Fishing Lake | WEAK | Jim Moore Pond 41 ac (lake 49 ac) [Hydrography_Public] |
| US-12222 | ID | Mackay Reservoir State Fishing Lake | WEAK | Mackay Reservoir 1130 ac (lake 1178 ac) [Hydrography_Public] |
| US-12226 | ID | Bruneau Arm Reservoir State Fishing Lake | WEAK | C. J. Strike Reservoir 6632 ac (lake 1262 ac) [Hydrography_Public] |
| US-12227 | ID | Crane Falls Lake State Fishing Lake | FOUND | CJ STRIKE WMA 11266 ac (lake 88 ac) SHORE [WildlifeManagementAreas] |
| US-12228 | ID | Cove Arm Lake State Fishing Lake | FOUND | CJ STRIKE WMA 11265 ac (lake 75 ac) SHORE [WildlifeManagementAreas] |
| US-12232 | ID | Horseshoe Bend Mill Pond State Fishing Lake | WEAK | Horseshoe Bend Mill Pond 8 ac (lake 3 ac) [Hydrography_Public] |
| US-12233 | ID | CJ Strike Reservoir State Fishing Lake | WEAK | C. J. Strike Reservoir 6629 ac (lake 6208 ac) [Hydrography_Public] |
| US-12291 | ID | Sawyers Pond State Fishing Lake | WEAK | Sawyers Pond 59 ac [Hydrography_Public] |
| US-12292 | ID | Dick Knox Pond State Fishing Lake | WEAK | Dick Knox Pond 48 ac [Hydrography_Public] |
| US-12303 | ID | Wilson Springs Pond Complex State Fishing Lake | WEAK | Wilson Springs North Pond 5 ac (lake 18 ac) [Hydrography_Public] |
| US-13094 | ID | Oneida Narrows Reservoir State Fishing Lake | WEAK | Oneida Narrows Reservoir 420 ac (lake 430 ac) [Hydrography_Public] |
| US-13158 | ID | Blackfoot Reservoir State Fishing Lake | WEAK | Blackfoot Reservoir 16896 ac (lake 16914 ac) [Hydrography_Public] |
| US-13616 | ID | Duff Pond State Fishing Lake | WEAK | Duff Lane Pond 3 ac (lake 5 ac) [Hydrography_Public] |
| US-5596 | ID | Carey Lake Wildlife Management Area | FOUND | CAREY LAKE WMA 790 ac [WildlifeManagementAreas] |
| US-5607 | ID | Market Lake Wildlife Management Area | FOUND | MARKET LAKE WMA 5977 ac [WildlifeManagementAreas] |
| US-5608 | ID | McArthur Lake Wildlife Management Area | FOUND | MCARTHUR LAKE WMA 1579 ac (lake 135 ac) SHORE [WildlifeManagementAreas] |
| US-5611 | ID | Mud Lake Wildlife Management Area | FOUND | MUD LAKE WMA 13787 ac [WildlifeManagementAreas] |
| US-7821 | ID | Magic Reservoir Airstrip State Recreation Area | NOT FOUND |  |
| US-11818 | IN | Martindale State Fishing Lake | FOUND | Martindale Public Fishing Area 24 ac (lake 15 ac) SHORE [Hosted] |
| US-11996 | IN | Adams Mill State Fishing Lake | FOUND | Adams Mill Public Fishing Area 10 ac [Hosted] |
| US-11998 | IN | Lake Wawasee State Fishing Lake | FOUND | Wawasee Public Fishing Area 12 ac (lake 3426 ac) [Hosted] |
| US-12001 | IN | Trail Creek State Fishing Lake | FOUND | Trail Creek West Branch Public Fishing A 77 ac [Hosted] |
| US-12002 | IN | Williams Dam State Fishing Lake | FOUND | Williams Dam Public Fishing Area 30 ac [Hosted] |
| US-13100 | IN | Driftwood State Fishing Lake | FOUND | Driftwood Public Fishing Area 894 ac (lake 92 ac) SHORE [Hosted] |
| US-13103 | IN | Hindostan Falls State Fishing Lake | FOUND | Hindostan Falls Public Fishing Area 117 ac [Hosted] |
| US-13104 | IN | Three Rivers State Fishing Lake | FOUND | Martinsville Public Fishing Area 17 ac [Hosted] |
| US-7384 | KS | Atchison State Fishing Lake | FOUND | Atchison State Fishing Lake And Wildlife 205 ac [protected_areas] |
| US-7385 | KS | Brown State Fishing Lake | FOUND | Brown State Fishing Lake And Wildlife Ar 196 ac (lake 66 ac) SHORE [protected_areas] |
| US-7386 | KS | Browning Oxbow State Fishing Lake | NOT FOUND |  |
| US-7387 | KS | Douglas State Fishing Lake | FOUND | Douglas State Fishing Lake And Wildlife  712 ac (lake 178 ac) SHORE [protected_areas] |
| US-7388 | KS | Geary State Fishing Lake | FOUND | Geary State Fishing Lake And Wildlife Ar 501 ac (lake 46 ac) SHORE [protected_areas] |
| US-7390 | KS | Leavenworth State Fishing Lake | FOUND | Leavenworth State Fishing Lake 304 ac (lake 152 ac) SHORE [protected_areas] |
| US-7391 | KS | Miami State Fishing Lake | FOUND | Miami SFL and Wildlife Area 176 ac (lake 111 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7392 | KS | Middle Creek State Fishing Lake | FOUND | Louisburg-Middlecreek Wildlife Managemen 603 ac (lake 272 ac) SHORE [protected_areas] |
| US-7394 | KS | Nebo State Fishing Lake | FOUND | Nebo State Lake Wildlife Area 246 ac (lake 30 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7395 | KS | Nemaha Wildlife Area State Fishing Lake | FOUND | Nemaha SFL and Wildlife Area 708 ac [KDWPT_Wildlife_Areas] |
| US-7396 | KS | Pottawatomie No 1 State Fishing Lake | FOUND | Pottawatomie State Fishing Lake No. 1 An 186 ac (lake 18 ac) SHORE [protected_areas] |
| US-7397 | KS | Pottawatomie No 2 State Fishing Lake | NOT FOUND |  |
| US-7398 | KS | Shawnee State Fishing Lake | FOUND | Shawnee State Fishing Lake 592 ac (lake 123 ac) SHORE [protected_areas] |
| US-7399 | KS | Tuttle Creek Willow State Fishing Lake | FOUND | Tuttle Creek Lake 34626 ac (lake 168 ac) SHORE [protected_areas] |
| US-7400 | KS | Washington State Fishing Lake | FOUND | Washington State Fishing Lake And Wildli 448 ac [protected_areas] |
| US-7401 | KS | Bourbon State Fishing Lake | FOUND | Bourbon SFL and Wildlife Area 247 ac (lake 93 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7402 | KS | Crawford State Fishing Lake | FOUND | Crawford State Park 482 ac (lake 146 ac) SHORE [protected_areas] |
| US-7403 | KS | Lyon State Fishing Lake | FOUND | Lyon SFL and Wildlife Area 445 ac (lake 132 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7405 | KS | Melvern River State Fishing Lake | FOUND | Melvern Lake 23456 ac [protected_areas] |
| US-7406 | KS | Mined Land State Fishing Lake | FOUND | Mined Land Wildlife Area 14648 ac (lake 4 ac) SHORE [protected_areas] |
| US-7407 | KS | Montgomery State Fishing Lake | FOUND | Montgomery State Fishing Lake 384 ac (lake 78 ac) SHORE [protected_areas] |
| US-7408 | KS | Neosho State Fishing Lake | FOUND | Neosho State Fishing Lake 228 ac [protected_areas] |
| US-7409 | KS | Osage State Fishing Lake | FOUND | Osage State Fishing Lake 509 ac (lake 132 ac) SHORE [protected_areas] |
| US-7410 | KS | Wilson State Fishing Lake | FOUND | Wilson State Fishing Lake 199 ac [protected_areas] |
| US-7411 | KS | Woodson State Fishing Lake | FOUND | Woodson Wildlife Area 2912 ac (lake 121 ac) SHORE [protected_areas] |
| US-7412 | KS | Black Kettle State Fishing Lake | FOUND | Black Kettle State Fishing Lake 28 ac (lake 7 ac) SHORE [protected_areas] |
| US-7413 | KS | Butler State Fishing Lake | FOUND | Butler State Lake Wildlife Area 361 ac [KDWPT_Wildlife_Areas] |
| US-7414 | KS | Chase State Fishing Lake | FOUND | Chase SFL and Wildlife Area 395 ac (lake 106 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7415 | KS | Cowley State Fishing Lake | FOUND | Cowley State Fishing Lake And Wildlife A 210 ac (lake 74 ac) SHORE [protected_areas] |
| US-7416 | KS | Kingman State Fishing Lake | FOUND | Byron Walker Wildlife Area 4778 ac (lake 148 ac) SHORE [protected_areas] |
| US-7417 | KS | McPherson State Fishing Lake | FOUND | McPherson State Fishing Lake 293 ac (lake 30 ac) SHORE [protected_areas] |
| US-7418 | KS | Jewell State Fishing Lake | FOUND | Jewell State Lake Wildlife Area 163 ac (lake 40 ac) SHORE [protected_areas] |
| US-7419 | KS | Logan State Fishing Lake | FOUND | Logan State Lake Wildlife Area 525 ac (lake 45 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7420 | KS | Ottawa State Fishing Lake | FOUND | Ottawa State Fishing Lake And Wildlife A 710 ac (lake 96 ac) SHORE [protected_areas] |
| US-7421 | KS | Rooks State Fishing Lake | FOUND | Rooks SFL and Wildlife Area 303 ac (lake 29 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7422 | KS | Saline State Fishing Lake | FOUND | Saline State Fishing Lake 76 ac (lake 22 ac) SHORE [protected_areas] |
| US-7423 | KS | Sheridan State Fishing Lake | FOUND | Sheridan State Fishing Lake 326 ac (lake 35 ac) SHORE [protected_areas] |
| US-7424 | KS | Sherman State Fishing Lake | FOUND | Sherman-Kansas Veteran's Wildlife Area 2615 ac (lake 18 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7425 | KS | Barber State Fishing Lake | FOUND | Barber State Fishing Lake And Wildlife A 191 ac (lake 29 ac) SHORE [protected_areas] |
| US-7426 | KS | Clark State Fishing Lake | FOUND | Clark Wildlife Area 1250 ac (lake 282 ac) SHORE [protected_areas] |
| US-7427 | KS | Concannon State Fishing Lake | FOUND | Concannon State Fishing Lake And Wildlif 798 ac (lake 51 ac) SHORE [protected_areas] |
| US-7428 | KS | Ford County State Fishing Lake | FOUND | Ford State Fishing Lake and Wildlife Are 311 ac (lake 8 ac) SHORE [protected_areas] |
| US-7429 | KS | Goodman State Fishing Lake | FOUND | Goodman State Lake and Wildlife Area 263 ac (lake 19 ac) SHORE [protected_areas] |
| US-7430 | KS | Hain State Fishing Lake | FOUND | Hain Wildlife Area 78 ac (lake 4 ac) SHORE [KDWPT_Wildlife_Areas] |
| US-7431 | KS | Hodgeman State Fishing Lake | FOUND | Hodgeman SFL and Wildlife Area 494 ac [KDWPT_Wildlife_Areas] |
| US-7432 | KS | Kiowa State Fishing Lake | FOUND | Kiowa State Fishing Lake 47 ac (lake 20 ac) SHORE [protected_areas] |
| US-7433 | KS | Meade State Fishing Lake | FOUND | Meade State Park 424 ac (lake 67 ac) SHORE [protected_areas] |
| US-7434 | KS | Scott State Fishing Lake | FOUND | Scott State Park 1082 ac (lake 110 ac) SHORE [protected_areas] |
| US-7926 | KS | Elk City Reservoir State Wildlife Area | FOUND | Elk City Lake 19429 ac [protected_areas] |
| US-2373 | LA | Poverty Point Reservoir State Park | NOT FOUND |  |
| US-4049 | LA | Big Lake Wildlife Management Area | FOUND | Big Lake WMA 19513 ac [LDWF_WMA_Refuge] |
| US-4059 | LA | Grassy Lake Wildlife Management Area | FOUND | Grassy Lake WMA 13222 ac [LDWF_WMA_Refuge] |
| US-4063 | LA | Lake Boeuf Wildlife Management Area | FOUND | Lake Boeuf WMA 804 ac (lake 56923 ac) [LDWF_WMA_Refuge] |
| US-4064 | LA | Lake Ramsey Savannah Wildlife Management Area | FOUND | Lake Ramsay Savannah WMA 832 ac [LDWF_WMA_Refuge] |
| US-4083 | LA | Soda Lake Wildlife Management Area | FOUND | Soda Lake WMA 2144 ac [LDWF_WMA_Refuge] |
| US-11396 | MA | Agawam Lake Wildlife Management Area | FOUND | Agawam Lake WMA 788 ac [MassWildlifeLands] |
| US-11470 | MA | Lake Warner Wildlife Management Area | FOUND | Lake Warner WMA 107 ac (lake 51 ac) SHORE [MassWildlifeLands] |
| US-11611 | MA | Atwood Reservoir Wildlife Management Area | FOUND | Atwood Reservoir WMA 516 ac (lake 94 ac) SHORE [AGOL] |
| US-11631 | MA | Hartley Reservoir Wildlife Management Area | FOUND | East Over Farm Conservation Area 52 ac (lake 49 ac) [AGOL] |
| US-8453 | ME | Dickwood Lake Wildlife Management Area | FOUND | Leboeuf Lot 3807 ac [Maine_Conserved_Lands_Fee] |
| US-6649 | MI | Cranberry Lake Wildlife Management Area | FOUND | Cranberry Lake Flooding State Wildlife M 262 ac (lake 85 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6660 | MI | Devils Lake Flooding Wildlife Management Area | FOUND | Devil's Lake and Devil's River Flooding  906 ac [DNRWILDLandsOPENDATA] |
| US-6662 | MI | Dog Lake Flooding Wildlife Management Area | FOUND | Dog Lake Flooding State Wildlife Managem 1653 ac (lake 192 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6677 | MI | French Farm Lake Flooding Wildlife Management  | FOUND | French Farm Flooding State Wildlife Mana 2927 ac (lake 590 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6691 | MI | Grass Lake Flooding Wildlife Management Area | FOUND | Grass Lake Flooding State Wildlife Manag 2610 ac (lake 6252 ac) [DNRWILDLandsOPENDATA] |
| US-6692 | MI | Grass Lake Marsh Flooding Wildlife Management  | FOUND | Grass Lake Marsh Flooding State Wildlife 961 ac (lake 192 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6702 | MI | Hayward Lake to North Lake Floodings Wildlife  | FOUND | Hayward Lake to North Lake Floodings Sta 3268 ac [DNRWILDLandsOPENDATA] |
| US-6707 | MI | Houghton Lake Flats North Flooding Wildlife Ma | FOUND | Houghton Lake Flats North Flooding State 840 ac (lake 2 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6708 | MI | Houghton Lake Flats South Flooding Wildlife Ma | FOUND | Houghton Lake Flats South Flooding State 981 ac (lake 10 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6709 | MI | Houghton Lake Wildlife Management Area | FOUND | Houghton Lake State Wildlife Research Ar 12071 ac [DNRWILDLandsOPENDATA] |
| US-6716 | MI | Lake LaVasseur Flooding Wildlife Management Ar | FOUND | Lake LaVasseur Flooding State Wildlife M 396 ac (lake 1772 ac) [DNRWILDLandsOPENDATA] |
| US-6723 | MI | Little Fox River Flooding / Stanley Lake Wildl | FOUND | Little Fox River / Stanley Lake Flooding 2533 ac (lake 98 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6732 | MI | Marsh Creek / Beaver Lake Flooding Wildlife Ma | FOUND | Marsh Creek / Beaver Lake Flooding State 545 ac (lake 33 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6750 | MI | O'Neal Lake Flooding Wildlife Management Area | FOUND | Wilderness State Park 12240 ac (lake 138 ac) SHORE [DNRManagementBoundariesOPEND] |
| US-6758 | MI | Pike Lake Flooding Wildlife Management Area | FOUND | Pike Lake Flooding State Wildlife Manage 133 ac (lake 82 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-6785 | MI | Sportsmans Lake/Pond Wildlife Management Area | FOUND | Sportsman's Lake State Wildlife Manageme 161 ac (lake 18 ac) SHORE [DNRWILDLandsOPENDATA] |
| US-11972 | MN | Dead Lake Wildlife Management Area | NOT FOUND |  |
| US-12380 | MN | McCarthy Lake Wildlife Management Area | FOUND | Mc Carthy Lake WMA 3240 ac [us_mn_state_dnr] |
| US-12450 | MN | Clark Lake Wildlife Management Area | FOUND | Clark Lake WMA 34 ac [us_mn_state_dnr] |
| US-12452 | MN | Bradshaw Lake Wildlife Management Area | NOT FOUND |  |
| US-12626 | MN | Indian Lake Wildlife Management Area | FOUND | Indian Lake WMA 620 ac (lake 396 ac) SHORE [us_mn_state_dnr] |
| US-12660 | MN | Severance Lake Wildlife Management Area | FOUND | Severance Lake WMA: North Unit 90 ac [us_mn_state_dnr] |
| US-12687 | MN | Ward Lake Wildlife Management Area | FOUND | Ward Lake WMA 70 ac [us_mn_state_dnr] |
| US-12693 | MN | Swan Lake Wildlife Management Area | FOUND | Swan Lake WMA: Nicollet Bay Main Unit 164 ac [us_mn_state_dnr] |
| US-12706 | MN | Marget Lake Wildlife Management Area | FOUND | Marget Lake WMA 511 ac [us_mn_state_dnr] |
| US-13354 | MN | Pelican Lake Wildlife Management Area | NOT FOUND |  |
| US-13559 | MN | Chub Lake Wildlife Management Area | NOT FOUND |  |
| US-13620 | MN | Lake Eleanor Wildlife Management Area | FOUND | Lake Eleanor WMA 72 ac (lake 167 ac) [us_mn_state_dnr] |
| US-10958 | MO | Tywappity Community Lake State Conservation Ar | FOUND | Tywappity CL 116 ac (lake 36 ac) SHORE [Discover_Nature] |
| US-6527 | MO | Thomas Hill Reservoir State Conservation Area | FOUND | Thomas Hill Reservoir CA 9296 ac [Discover_Nature] |
| US-6529 | MO | Truman Reservoir Management Lands State Park | FOUND | Truman Reservoir ML (Deepwater Creek) 5616 ac (lake 20198 ac) [Discover_Nature] |
| US-12193 | MS | Lake Claude Bennett State Fishing Lake | NO LAYER READ |  |
| US-12194 | MS | Lake Lamar Bruce State Fishing Lake | NO LAYER READ |  |
| US-12195 | MS | Elvis Presley State Fishing Lake | NO LAYER READ |  |
| US-12196 | MS | Tippah County State Fishing Lake | NO LAYER READ |  |
| US-12197 | MS | Lake Monroe State Fishing Lake | NO LAYER READ |  |
| US-12198 | MS | Neshoba County State Fishing Lake | NO LAYER READ |  |
| US-12199 | MS | Lake Tom Bailey State Fishing Lake | NO LAYER READ |  |
| US-12200 | MS | Simpson County State Fishing Lake | NO LAYER READ |  |
| US-12201 | MS | Prentiss Walker State Fishing Lake | NO LAYER READ |  |
| US-12202 | MS | Lake Bogue Homa State Fishing Lake | NO LAYER READ |  |
| US-12203 | MS | Lake Mary Crawford State Fishing Lake | NO LAYER READ |  |
| US-12204 | MS | Calling Panther State Fishing Lake | NO LAYER READ |  |
| US-12205 | MS | Lake Mike Conner State Fishing Lake | NO LAYER READ |  |
| US-12206 | MS | Lake Jeff Davis State Fishing Lake | NO LAYER READ |  |
| US-12207 | MS | Lake Walthall State Fishing Lake | NO LAYER READ |  |
| US-12208 | MS | Lake Perry State Fishing Lake | NO LAYER READ |  |
| US-7076 | MS | Sky Lake Wildlife Management Area | NO LAYER READ |  |
| US-7081 | MS | Lake George Wildlife Management Area | NO LAYER READ |  |
| US-12649 | MT | Fresno Reservoir Wildlife Management Area | FOUND | Fresno Reservoir 2672 ac (lake 82 ac) SHORE [FWPLND_WMA] |
| US-12651 | MT | Nevada Lake Wildlife Management Area | FOUND | Nevada Lake 1512 ac [FWPLND_WMA] |
| US-12849 | MT | Bynum Reservoir State Fish and Wildlife Area | FOUND | Bynum Reservoir 291 ac (lake 2819 ac) [FWPLND_FAS] |
| US-12865 | MT | Eureka Reservoir State Fish and Wildlife Area | FOUND | Eureka Reservoir 29 ac (lake 420 ac) [FWPLND_FAS] |
| US-12893 | MT | Martinsdale Reservoir State Fish and Wildlife  | FOUND | Martinsdale Reservoir 334 ac (lake 989 ac) [FWPLND_FAS] |
| US-12900 | MT | Newlan Creek Reservoir State Fish and Wildlife | FOUND | Newlan Creek Reservoir 157 ac (lake 265 ac) [FWPLND_FAS] |
| US-12901 | MT | Nilan Reservoir State Fish and Wildlife Area | FOUND | Nilan Reservoir 9 ac (lake 521 ac) [FWPLND_FAS] |
| US-12907 | MT | Pishkin Reservoir State Fish and Wildlife Area | FOUND | Pishkun Reservoir 1641 ac (lake 1519 ac) [FWPLND_FAS] |
| US-12935 | MT | Willow Creek Reservoir State Fish and Wildlife | FOUND | Willow Creek Reservoir 1395 ac (lake 1323 ac) [FWPLND_FAS] |
| US-2566 | MT | Cooney Reservoir State Park | FOUND | Cooney 349 ac (lake 769 ac) [FWPLND_STATEPARKS] |
| US-2600 | MT | Tongue River Reservoir State Park | FOUND | Tongue River Reservoir 529 ac (lake 2158 ac) [FWPLND_FWPLANDS_PARCELS] |
| US-6442 | MT | Freezeout Lake Wildlife Management Area | FOUND | Freezout Lake 11231 ac (lake 235 ac) SHORE [FWPLND_WMA] |
| US-10399 | NC | Apalachia Reservoir Recreation Park | FOUND | Tennessee Valley Authority - Apalachia L 1110 ac (lake 1064 ac) [NC_Public] |
| US-8226 | NC | Upchurch Lake State Fishing Lake | FOUND | Nicholson Creek 1020 ac (lake 256 ac) SHORE [gamelands_general] |
| US-7703 | ND | Buffalo Lake Wildlife Management Area | FOUND | Buffalo Lake 697 ac (lake 487 ac) SHORE [NDGISHUB_Wildlife_Management] |
| US-8564 | ND | Armourdale Lake Wildlife Management Area | FOUND | Armourdale Lake 25 ac (lake 84 ac) [NDGISHUB_Wildlife_Management] |
| US-8565 | ND | Arroda Lake Wildlife Management Area | FOUND | Arroda Lake 414 ac (lake 22 ac) SHORE [NDGISHUB_Wildlife_Management] |
| US-8571 | ND | Cedar Lake Wildlife Management Area | FOUND | Cedar Lake 800 ac [NDGISHUB_Wildlife_Management] |
| US-8573 | ND | Coal Lake Wildlife Management Area | FOUND | Coal Lake 789 ac (lake 16 ac) SHORE [NDGISHUB_Wildlife_Management] |
| US-8578 | ND | Erie Dam/Brewer Lake Wildlife Management Area | FOUND | Erie Dam (Brewer Lake) 1080 ac [NDGISHUB_Wildlife_Management] |
| US-8580 | ND | Harmony Lake Wildlife Management Area | FOUND | Harmony Lake 628 ac [NDGISHUB_Wildlife_Management] |
| US-8583 | ND | Horsehead Lake Wildlife Management Area | FOUND | Horsehead Lake 524 ac [NDGISHUB_Wildlife_Management] |
| US-8591 | ND | Lake Patricia Wildlife Management Area | FOUND | Lake Patricia 638 ac [NDGISHUB_Wildlife_Management] |
| US-8592 | ND | Lake Washington Wildlife Management Area | FOUND | Lake Washington 870 ac [NDGISHUB_Wildlife_Management] |
| US-8601 | ND | Rice Lake Wildlife Management Area | FOUND | Rice Lake 815 ac (lake 760 ac) [NDGISHUB_Wildlife_Management] |
| US-8604 | ND | Smishek Lake Wildlife Management Area | FOUND | Smishek Lake 194 ac (lake 0 ac) SHORE [NDGISHUB_Wildlife_Management] |
| US-8606 | ND | Swan Lake Wildlife Management Area | FOUND | Swan Lake 292 ac (lake 919 ac) [NDGISHUB_Wildlife_Management] |
| US-8607 | ND | Sweet Briar Lake Wildlife Management Area | FOUND | Sweet Briar Lake 891 ac (lake 274 ac) SHORE [NDGISHUB_Wildlife_Management] |
| US-8608 | ND | Thompson Lake Wildlife Management Area | FOUND | Thompson Lake 795 ac [NDGISHUB_Wildlife_Management] |
| US-12445 | NE | Ayr Lake Wildlife Management Area | FOUND | Ayr Lake WMA 170 ac [NPGCProperties2023_2024] |
| US-12946 | NE | Elwood Reservoir Wildlife Management Area | FOUND | Elwood Reservoir WMA 827 ac (lake 978 ac) [NPGCProperties2023_2024] |
| US-13329 | NE | Plum Creek Canyon Reservoir Wildlife Managemen | FOUND | Plum Creek Canyon 1 ac (lake 231 ac) [NPGCProperties2023_2024] |
| US-13378 | NE | Sherman Reservoir Wildlife Management Area | FOUND | Sherman Reservoir WMA 4100 ac (lake 0 ac) SHORE [NPGCProperties2023_2024] |
| US-4018 | NE | Wildwood Lake Wildlife Management Area | FOUND | Wildwood WMA 482 ac (lake 110 ac) SHORE [NPGCProperties2023_2024] |
| US-4034 | NE | Leisure Lake Wildlife Management Area | FOUND | Leisure Lake Recreation Area (NRD) 85 ac (lake 36 ac) SHORE [Conservation_Partner_Lands] |
| US-5629 | NE | Sherman Reservoir State Recreation Area | FOUND | Sherman Reservoir SRA 3470 ac (lake 2435 ac) SHORE [Park_Areas] |
| US-5630 | NE | Calamus Reservoir State Recreation Area | FOUND | Calamus Reservoir WMA 9896 ac (lake 5032 ac) SHORE [NPGCProperties2023_2024] |
| US-5631 | NE | Merritt Reservoir State Recreation Area | FOUND | Merritt Reservoir WMA 9049 ac [NPGCProperties2023_2024] |
| US-5642 | NE | Swanson Reservoir State Recreation Area | FOUND | Swanson Reservoir WMA 8010 ac (lake 4661 ac) SHORE [NPGCProperties2023_2024] |
| US-5660 | NE | Box Butte Reservoir State Recreation Area | FOUND | Box Butte Reservoir WMA 1982 ac (lake 1263 ac) SHORE [NPGCProperties2023_2024] |
| US-5664 | NE | Enders Reservoir State Recreation Area | FOUND | Enders Reservoir WMA 4328 ac (lake 1194 ac) SHORE [NPGCProperties2023_2024] |
| US-5673 | NE | Red Willow Reservoir State Recreation Area | FOUND | Red Willow Reservoir WMA 5193 ac (lake 1496 ac) SHORE [NPGCProperties2023_2024] |
| US-5675 | NE | Sutherland Reservoir State Recreation Area | NOT FOUND |  |
| US-9356 | NE | Willow Lake Wildlife Management Area | NOT FOUND |  |
| US-11990 | NJ | Harrisonville Lake Wildlife Management Area | FOUND | Harrisonville Lake Wildlife Management A 220 ac (lake 18 ac) SHORE [Open_Space__State_Owned__Gen] |
| US-12100 | NJ | Amwell Lake Wildlife Management Area | FOUND | Amwell Lake Wildlife Management Area 23 ac (lake 11 ac) SHORE [Open_Space__State_Owned__Gen] |
| US-13060 | NJ | Elmer Lake Wildlife Management Area | FOUND | Elmer Lake Wildlife Management Area 412 ac [Open_Space__State_Owned__Gen] |
| US-13148 | NJ | Baldwin Lake Wildlife Management Area | FOUND | Baldwin Lake Wildlife Management Area 48 ac (lake 14 ac) SHORE [Open_Space__State_Owned__Gen] |
| US-8043 | NJ | Makepeace Lake Wildlife Management Area | FOUND | Makepeace Lake Wildlife Management Area 11454 ac [Open_Space__State_Owned__Gen] |
| US-8057 | NJ | Union Lake Wildlife Management Area | FOUND | Union Lake Wildlife Management Area 5248 ac [Open_Space__State_Owned__Gen] |
| US-10345 | NV | Carson Lake and Pasture Wildlife Management Ar | FOUND | Carson Lake WMA 29911 ac [Wildlife_Management_Areas] |
| US-13022 | NV | Alkali Lake Wildlife Management Area | FOUND | Alkali Lake WMA 3554 ac [Wildlife_Management_Areas] |
| US-13154 | NV | Illipah Reservoir BLM Recreation Management Ar | NOT FOUND |  |
| US-13173 | NV | Wilson Reservoir BLM Recreation Management Are | NOT FOUND |  |
| US-13190 | NV | Zunino/Jiggs Reservoir BLM Recreation Manageme | NOT FOUND |  |
| US-2124 | NY | Reservoir State Park | FOUND | Reservoir 93 ac [NYS_Park_Polygons] |
| US-8103 | NY | Cayuga Lake Wildlife Management Area | FOUND | Northern Montezuma Wma 1 ac [NYS_DEC_Lands] |
| US-9037 | NY | Allegheny Reservoir Wildlife Management Area | FOUND | South Valley State Forest 3560 ac [NYS_DEC_Lands] |
| US-9041 | NY | Chautauqua Lake Wildlife Management Area | FOUND | Chautauqua Lake Fish And Wildlife Manage 35 ac (lake 0 ac) SHORE [NYS_DEC_Lands] |
| US-9043 | NY | Clear Lake Wildlife Management Area | FOUND | Clear Lake Wma 523 ac (lake 47 ac) SHORE [NYS_DEC_Lands] |
| US-9057 | NY | Silver Lake Outlet Wildlife Management Area | FOUND | Silver Lake Outlet Wma 10 ac (lake 863 ac) [NYS_DEC_Lands] |
| US-9063 | NY | Cross Lake Islands Wildlife Management Area | FOUND | Cross Lake  Islands Wma 19 ac (lake 1999 ac) [NYS_DEC_Lands] |
| US-9082 | NY | Lake Shore Marshes Wildlife Management Area | FOUND | Lake Shore Marshes Wma 779 ac [NYS_DEC_Lands] |
| US-9112 | NY | Lake Alice Wildlife Management Area | FOUND | Lake Alice Wma 1469 ac (lake 69 ac) SHORE [NYS_DEC_Lands] |
| US-10658 | OK | Lake Carl Blackwell Wildlife Management Area | NOT FOUND |  |
| US-11994 | OK | Schooler State Fishing Lake | FOUND | Schooler PFA 211 ac (lake 24 ac) SHORE [OklahomaRecreationalAreas] |
| US-12027 | OK | Altus-Lugert State Fishing Lake | NOT FOUND |  |
| US-13105 | OK | Field Station State Fishing Lake | NOT FOUND |  |
| US-7682 | OK | Lake Vanderwork State Fishing Lake | NOT FOUND |  |
| US-7684 | OK | Blue River State Fishing Lake | FOUND | Blue River Public Fishing & Hunting Area 3365 ac [OklahomaRecreationalAreas] |
| US-7685 | OK | American Horse State Fishing Lake | FOUND | American Horse Lake Public Fishing Area 437 ac (lake 89 ac) SHORE [OklahomaRecreationalAreas] |
| US-7686 | OK | Lake Elmer State Fishing Lake | FOUND | Lake Elmer Public Fishing Area 139 ac (lake 38 ac) SHORE [OklahomaRecreationalAreas] |
| US-7688 | OK | Lake Louis Burtschi State Fishing Lake | FOUND | Lake Louis Burtschi Public Fishing Area 757 ac (lake 168 ac) SHORE [OklahomaRecreationalAreas] |
| US-8119 | OK | Doc Hollis State Fishing Lake | FOUND | Sandy Sanders 36536 ac [Public_WMA_Boundaries] |
| US-8120 | OK | Evans Chambers State Fishing Lake | FOUND | Lake Evans Chambers 204 ac (lake 95 ac) SHORE [Public_WMA_Boundaries] |
| US-8123 | OK | Hall State Fishing Lake | FOUND | Hall Public Fishing Area 173 ac [OklahomaRecreationalAreas] |
| US-8126 | OK | Jap Beaver State Fishing Lake | FOUND | Lake Jap Beaver 207 ac [Public_WMA_Boundaries] |
| US-8128 | OK | Lloyd Vincent State Fishing Lake | FOUND | Ellis County 4719 ac (lake 132 ac) SHORE [Public_WMA_Boundaries] |
| US-8129 | OK | Nanih Waiya State Fishing Lake | FOUND | Nanih Waiya Public Fishing Area 200 ac [OklahomaRecreationalAreas] |
| US-8131 | OK | Ozzie Cobb State Fishing Lake | FOUND | Lake Ozzie Cobb 286 ac (lake 48 ac) SHORE [Public_WMA_Boundaries] |
| US-8134 | OK | Sardis State Fishing Lake | NOT FOUND |  |
| US-8639 | OK | Birch State Fishing Lake | NOT FOUND |  |
| US-8640 | OK | Lake Watonga State Fishing Lake | FOUND | Roman Nose State Park 841 ac (lake 36 ac) SHORE [OklahomaRecreationalAreas] |
| US-10024 | OR | Duncan Reservoir BLM Recreation Management Are | FOUND | Duncan Reservoir Campground 9 ac (lake 40 ac) [Land_ownership] |
| US-10484 | OR | Antelope Reservoir BLM Recreation Management A | NOT FOUND |  |
| US-10490 | OR | Moon Reservoir BLM Recreation Management Area | FOUND | Moon Reservoir Recreation Site 8 ac (lake 725 ac) [Land_ownership] |
| US-12845 | OR | Hult Dam & Reservoir BLM Recreation Management | FOUND | Hult Reservoir 8 ac (lake 41 ac) [Land_ownership] |
| US-12951 | OR | Prineville Reservoir State Fish and Wildlife A | FOUND | Prineville Reservoir 8758 ac (lake 2861 ac) SHORE [Land_ownership] |
| US-2849 | OR | Prineville Reservoir State Park | FOUND | Prineville Reservoir 8761 ac (lake 2861 ac) SHORE [Land_ownership] |
| US-10782 | SC | Lake John D. Long State Fishing Lake | FOUND | Lake John D Long Wildlife Lake 216 ac (lake 68 ac) SHORE [DEV_-_SCDNR_Public_Lands_Vie] |
| US-12107 | SC | Lake Cherokee State Fishing Lake | FOUND | Lake Cherokee 132 ac (lake 51 ac) SHORE [DEV_-_SCDNR_Public_Lands_Vie] |
| US-12108 | SC | Lake Thicketty State Fishing Lake | FOUND | Lake Thicketty 98 ac [DEV_-_SCDNR_Public_Lands_Vie] |
| US-9220 | SC | Clinton Reservoir Tract Wildlife Management Ar | FOUND | Unnamed Game Zone 2 12928 ac [DEV_-_SCDNR_Public_Lands_Vie] |
| US-9224 | SC | Lake Wallace Wildlife Management Area | FOUND | Lake Paul Wallace 692 ac (lake 273 ac) SHORE [DEV_-_SCDNR_Public_Lands_Vie] |
| US-12070 | TN | Garrett Lake State Fishing Lake | FOUND | Garrett Lake 278 ac [Tennessee_State_and_Federal_] |
| US-12071 | TN | Whiteville Lake State Fishing Lake | FOUND | Whiteville Lake WMA 336 ac (lake 142 ac) SHORE [Tennessee_State_and_Federal_] |
| US-12072 | TN | Bedford Lake State Fishing Lake | FOUND | Bedford Lake 310 ac (lake 50 ac) SHORE [Tennessee_State_and_Federal_] |
| US-12369 | TN | Lake Graham State Fishing Lake | FOUND | Lake Graham SFA 862 ac (lake 388 ac) SHORE [Tennessee_State_and_Federal_] |
| US-12715 | TN | Gibson County State Fishing Lake | FOUND | Gibson County Lake 272 ac (lake 512 ac) [Tennessee_State_and_Federal_] |
| US-12775 | TN | Davy Crockett State Fishing Lake | FOUND | Humboldt Hatchery 231 ac [Tennessee_State_and_Federal_] |
| US-13514 | TN | Lake Halford State Fishing Lake | NOT FOUND |  |
| US-3937 | TN | Eagle Lake Refuge Wildlife Management Area | FOUND | Eagle Lake Refuge 3514 ac [Tennessee_State_and_Federal_] |
| US-7565 | TN | AEDC and Woods Reservoir Wildlife Management A | FOUND | A.E.D.C. WMA 3260 ac [Tennessee_State_and_Federal_] |
| US-7578 | TN | Cheatham Lake Wildlife Management Area | FOUND | Cheatham Lake WMA 1376 ac [Tennessee_State_and_Federal_] |
| US-7622 | TN | Tellico Lake Wildlife Management Area | FOUND | Fort Loudoun State Historic Park 909 ac [TN_State_Parks_Boundaries] |
| US-6539 | TX | Big Lake Bottom Wildlife Management Area | FOUND | Big Lake Bottom WMA 4234 ac [WMA_Boundaries_4PublicDistri] |
| US-6542 | TX | Caddo Lake Wildlife Management Area | FOUND | Caddo Lake WMA 8445 ac (lake 5 ac) SHORE [Public_ConservationLands] |
| US-11002 | UT | Otter Creek Reservoir BLM Special Recreation M | NOT FOUND |  |
| US-11188 | UT | Lake Canyon Wildlife Management Area | FOUND | Lake Canyon WMA 7533 ac (lake 29 ac) SHORE [WMAs_WFL1] |
| US-11643 | UT | Lake Fork Wildlife Management Area | FOUND | Lake Fork WMA 2753 ac [WMAs_WFL1] |
| US-11645 | UT | Utah Lake Access - Swede's Lane Wildlife Manag | FOUND | Swedes Lane Angler Access 16 ac [WMAs_WFL1] |
| US-11761 | UT | Quail Creek Reservoir Designated Dispersed Cam | NOT FOUND |  |
| US-5914 | UT | Birch Creek Reservoir BLM Recreation Managemen | NOT FOUND |  |
| US-3117 | VT | Green River Reservoir State Park | FOUND | Green River Reservoir State Park 6110 ac [Open_Data] |
| US-12253 | WA | Winchester Reservoir State Fish and Wildlife A | FOUND | Columbia Basin 169610 ac [WP_RealEstate] |
| US-12278 | WA | Boundary Reservoir BLM Recreation Management A | FOUND |   968 ac [Public_Boundaries] |
| US-12422 | WA | Silver State Fishing Lake | FOUND | Silver Lake 5 ac (lake 446 ac) [WP_RealEstate] |
| US-12423 | WA | Williams State Fishing Lake | FOUND | Williams Lake 2 ac [WP_RealEstate] |
| US-12424 | WA | Badger State Fishing Lake | FOUND | Spokane County Lakes 4 ac [Public_Boundaries] |
| US-12425 | WA | Amber State Fishing Lake | FOUND | Columbia Plateau 3855 ac (lake 91 ac) SHORE [ParkBoundaries] |
| US-12426 | WA | Hog Canyon State Fishing Lake | FOUND |   8829 ac (lake 53 ac) SHORE [Public_Boundaries] |
| US-12427 | WA | Liberty State Fishing Lake | FOUND | Liberty Lake 1 ac [WP_RealEstate] |
| US-12428 | WA | Newman State Fishing Lake | FOUND | Newman Lake 4 ac (lake 1091 ac) [WP_RealEstate] |
| US-12429 | WA | Eloika State Fishing Lake | FOUND | Eloika Lake 2 ac (lake 630 ac) [WP_RealEstate] |
| US-12430 | WA | Deer State Fishing Lake | FOUND | Deer Lake 3 ac (lake 1146 ac) [WP_RealEstate] |
| US-12431 | WA | Sacheen State Fishing Lake | FOUND | Sacheen Lake 2 ac [WP_RealEstate] |
| US-12432 | WA | Davis State Fishing Lake | FOUND | Davis Lake 1 ac (lake 148 ac) [WP_RealEstate] |
| US-12433 | WA | Diamond State Fishing Lake | FOUND | Diamond Lake 1 ac (lake 753 ac) [WP_RealEstate] |
| US-12434 | WA | Waitts State Fishing Lake | FOUND | Waitts Lake 2 ac (lake 470 ac) [WP_RealEstate] |
| US-12435 | WA | Horseshoe State Fishing Lake | FOUND | Sherman Creek 11236 ac (lake 135 ac) SHORE [WP_RealEstate] |
| US-12466 | WA | Jump Off Joe State Fishing Lake | FOUND | Stevens County Lakes 2 ac (lake 115 ac) [Public_Boundaries] |
| US-12477 | WA | Aeneas State Fishing Lake | FOUND | Aeneas Lake 13 ac (lake 53 ac) [WP_RealEstate] |
| US-12478 | WA | Blue State Fishing Lake | FOUND | Blue Lake 25 ac (lake 119 ac) [WP_RealEstate] |
| US-12479 | WA | Jameson State Fishing Lake | FOUND | Jameson Lake 182 ac [WP_RealEstate] |
| US-12512 | WA | Kress State Fishing Lake | FOUND | Kress Lake 58 ac (lake 25 ac) SHORE [WP_RealEstate] |
| US-12942 | WA | Clear Lake State Fishing Lake | FOUND | Clear Lake 3 ac [WP_RealEstate] |
| US-12943 | WA | West Medical State Fishing Lake | FOUND | Eastern State Hospital 1279 ac [Public_Boundaries] |
| US-12955 | WA | Fishtrap State Fishing Lake | FOUND |   8832 ac (lake 191 ac) SHORE [Public_Boundaries] |
| US-12956 | WA | Forth of July State Fishing Lake | FOUND | None 644 ac (lake 2 ac) SHORE [Public_Boundaries] |
| US-13349 | WA | Bonney State Fishing Lake | FOUND | Bonney Lake 11 ac (lake 17 ac) [WP_RealEstate] |
| US-13350 | WA | Clear State Fishing Lake | FOUND | Clear Lake 3 ac (lake 156 ac) [WP_RealEstate] |
| US-13351 | WA | Tanwax State Fishing Lake | FOUND | Pierce County Lakes 1 ac (lake 174 ac) [Public_Boundaries] |
| US-13352 | WA | Lake Kapowsin State Fishing Lake | FOUND | Lake Kapowsin 14 ac (lake 496 ac) [WP_RealEstate] |
| US-13355 | WA | Mineral State Fishing Lake | FOUND | Mineral Lake 8 ac (lake 275 ac) [WP_RealEstate] |
| US-13356 | WA | American State Fishing Lake | FOUND | American Lake 4 ac (lake 1092 ac) [WP_RealEstate] |
| US-13357 | WA | Bay State Fishing Lake | FOUND | Bay Lake 3 ac (lake 128 ac) [WP_RealEstate] |
| US-13358 | WA | Jackson State Fishing Lake | FOUND | Haley 319 ac (lake 15 ac) SHORE [ParkBoundaries] |
| US-13359 | WA | Lake Cassidy State Fishing Lake | FOUND | Lake Cassidy 2 ac (lake 123 ac) [WP_RealEstate] |
| US-13360 | WA | Lake Washington State Fishing Lake | WEAK | Lake Washington 21877 ac (lake 21992 ac) [NHD] |
| US-13361 | WA | Lake Stevens State Fishing Lake | FOUND | North Cove 0 ac (lake 1003 ac) [WP_RealEstate] |
| US-13372 | WA | Moses Lake State Fishing Lake | FOUND | Columbia Basin 169329 ac (lake 6716 ac) SHORE [WP_RealEstate] |
| US-13373 | WA | Fan Lake State Fishing Lake | FOUND | Fan Lake 0 ac (lake 73 ac) [WP_RealEstate] |
| US-13374 | WA | Loon Lake State Fishing Lake | FOUND | Sherman Creek 11249 ac (lake 1093 ac) SHORE [WP_RealEstate] |
| US-13375 | WA | Rock Lake State Fishing Lake | WEAK | Rock Lake 2176 ac (lake 2190 ac) [NHD] |
| US-13376 | WA | Potholes Reservoir State Fishing Lake | FOUND | Columbia Basin 170158 ac (lake 14292 ac) SHORE [WP_RealEstate] |
| US-13382 | WA | Langlois State Fishing Lake | FOUND | Langlois Lake 15 ac (lake 40 ac) [WP_RealEstate] |
| US-13385 | WA | Harts Lake State Fishing Lake | FOUND | Harts Lake 1 ac (lake 112 ac) [WP_RealEstate] |
| US-13386 | WA | Rapjohn State Fishing Lake | FOUND | Rapjohn Lake 2 ac (lake 59 ac) [WP_RealEstate] |
| US-13387 | WA | Lake Lawrence State Fishing Lake | FOUND | None 14 ac (lake 327 ac) [Public_Boundaries] |
| US-13388 | WA | Ohop State Fishing Lake | FOUND | Pierce County Lakes 8 ac (lake 218 ac) [Public_Boundaries] |
| US-13389 | WA | Lake Whitman State Fishing Lake | FOUND | None 44 ac (lake 29 ac) SHORE [Public_Boundaries] |
| US-13390 | WA | Silver Lake State Fishing Lake | FOUND | Silver Lake 3 ac (lake 1989 ac) [WP_RealEstate] |
| US-13403 | WA | Loomis Lake State Fishing Lake | FOUND | Johns River 11960 ac (lake 150 ac) SHORE [WP_RealEstate] |
| US-13416 | WA | Black Lake State Fishing Lake | FOUND | Black Lake 1 ac (lake 574 ac) [WP_RealEstate] |
| US-13417 | WA | Munn Lake State Fishing Lake | FOUND | Munn Lake 1 ac (lake 31 ac) [WP_RealEstate] |
| US-13418 | WA | Ward Lake State Fishing Lake | FOUND | Ward Lake 2 ac (lake 66 ac) [WP_RealEstate] |
| US-13419 | WA | Chambers Lake State Fishing Lake | FOUND | THURSTON, COUNTY OF-PARKS 5 ac (lake 53 ac) [Public_Boundaries] |
| US-13420 | WA | Hicks Lake State Fishing Lake | FOUND | Hicks Lake 3 ac (lake 162 ac) [WP_RealEstate] |
| US-13421 | WA | Long Lake State Fishing Lake | FOUND | Long Lake 1 ac (lake 308 ac) [WP_RealEstate] |
| US-13422 | WA | Pattison Lake State Fishing Lake | FOUND | Pattison Lake 1 ac (lake 254 ac) [WP_RealEstate] |
| US-13423 | WA | Lake Saint Clair State Fishing Lake | FOUND | Lake Saint Clair 9 ac (lake 233 ac) [WP_RealEstate] |
| US-13424 | WA | Offutt Lake State Fishing Lake | FOUND | Offutt Lake 1 ac (lake 191 ac) [WP_RealEstate] |
| US-13425 | WA | McIntosh Lake State Fishing Lake | FOUND | McIntosh Lake 1 ac (lake 110 ac) [WP_RealEstate] |
| US-13426 | WA | Plummer Lake State Fishing Lake | FOUND | Plummer Lake 31 ac (lake 19 ac) SHORE [WP_RealEstate] |
| US-13427 | WA | Swofford Pond State Fishing Lake | FOUND | Cowlitz 13941 ac (lake 11224 ac) SHORE [WP_RealEstate] |
| US-13428 | WA | Maggie Lake State Fishing Lake | FOUND | None 367 ac (lake 22 ac) SHORE [Public_Boundaries] |
| US-13429 | WA | Cady Lake State Fishing Lake | FOUND | Cady Lake 0 ac (lake 15 ac) [WP_RealEstate] |
| US-13430 | WA | Tee Lake State Fishing Lake | FOUND | Tee Lake 2 ac (lake 47 ac) [WP_RealEstate] |
| US-13431 | WA | Haven Lake State Fishing Lake | FOUND | None 226 ac (lake 69 ac) SHORE [Public_Boundaries] |
| US-13432 | WA | Lake Wooten State Fishing Lake | FOUND | Lake Wooten 1 ac (lake 68 ac) [WP_RealEstate] |
| US-13435 | WA | Lake Margaret State Fishing Lake | FOUND | King County Lakes 1 ac (lake 53 ac) [Public_Boundaries] |
| US-13436 | WA | Lake Alice State Fishing Lake | FOUND | King County Lakes 0 ac (lake 32 ac) [Public_Boundaries] |
| US-13437 | WA | Fish Lake State Fishing Lake | FOUND | King County Lakes 6 ac (lake 15 ac) [Public_Boundaries] |
| US-13438 | WA | Spring Lake State Fishing Lake | FOUND | Spring Lake/Lake Desire County Park 376 ac (lake 66 ac) SHORE [Public_Boundaries] |
| US-13439 | WA | Bass Lake State Fishing Lake | FOUND | Bass Lake 2 ac (lake 24 ac) [WP_RealEstate] |
| US-13440 | WA | Beaver Lake State Fishing Lake | FOUND | Beaver Lake Park 82 ac (lake 71 ac) [Public_Boundaries] |
| US-13441 | WA | Lake Desire State Fishing Lake | FOUND | Lake Desire 2 ac (lake 69 ac) [WP_RealEstate] |
| US-13442 | WA | Panther State Fishing Lake | FOUND | Snohomish County Lakes 1 ac (lake 45 ac) [Public_Boundaries] |
| US-13443 | WA | Lake Morton State Fishing Lake | FOUND | Lake Morton 1 ac (lake 66 ac) [WP_RealEstate] |
| US-13444 | WA | Lake Number 12 State Fishing Lake | FOUND | Lake Number 12 0 ac (lake 93 ac) [WP_RealEstate] |
| US-13445 | WA | Lake Dollof State Fishing Lake | FOUND | King County Lakes 2 ac (lake 20 ac) [Public_Boundaries] |
| US-13446 | WA | North Lake State Fishing Lake | FOUND | North Lake 5 ac (lake 51 ac) [WP_RealEstate] |
| US-13516 | WA | Horseshoe -Kitsap- State Fishing Lake | FOUND | Kitsap County Lakes 1 ac (lake 41 ac) [Public_Boundaries] |
| US-13550 | WA | Lake Killarney State Fishing Lake | FOUND | Lake Killarney 0 ac (lake 29 ac) [WP_RealEstate] |
| US-13551 | WA | Lake Geneva State Fishing Lake | FOUND | Lake Killarney 0 ac (lake 29 ac) [WP_RealEstate] |
| US-2441 | WA | Scooteney Reservoir State Park | FOUND |   2986 ac (lake 711 ac) SHORE [Public_Boundaries] |
| US-6995 | WV | Castlemans Run Lake Wildlife Management Area | FOUND | Castlemans Run Lake Wildlife Management  840 ac (lake 19 ac) SHORE [WV_Public_Lands] |
| US-7019 | WV | Warden Lake Wildlife Management Area | FOUND | Warden Lake Wildlife Management Area 119 ac (lake 42 ac) SHORE [WildlifeManagementAreas] |
| US-7023 | WV | Burnsville Lake Wildlife Management Area | FOUND | Burnsville Lake Wildlife Management Area 13194 ac (lake 826 ac) SHORE [WildlifeManagementAreas] |
| US-7029 | WV | Stonecoal Lake Wildlife Management Area | FOUND | Stonecoal Lake Wildlife Management Area 3094 ac (lake 601 ac) SHORE [WV_Public_Lands] |
| US-7030 | WV | Stonewall Jackson Lake Wildlife Management Are | FOUND | Stonewall Jackson Lake Wildlife Manageme 18269 ac [WildlifeManagementAreas] |
| US-7031 | WV | Summersville Lake Wildlife Management Area | FOUND | Summersville Lake Wildlife Management Ar 6160 ac (lake 2834 ac) SHORE [WildlifeManagementAreas] |
| US-7034 | WV | Anawalt Lake Wildlife Management Area | FOUND | Anawalt Lake Wildlife Management Area 1793 ac (lake 2 ac) SHORE [WildlifeManagementAreas] |
| US-7035 | WV | Berwind Lake Wildlife Management Area | FOUND | Berwind Lake Wildlife Management Area 93 ac (lake 15 ac) SHORE [WildlifeManagementAreas] |
| US-7037 | WV | Bluestone Lake Wildlife Management Area | FOUND | Bluestone Lake Wildlife Management Area 17852 ac (lake 1124 ac) SHORE [WV_Public_Lands] |
| US-7038 | WV | Horse Creek Lake Wildlife Management Area | FOUND | Horse Creek Wildlife Management Area 50 ac (lake 10 ac) SHORE [WildlifeManagementAreas] |
| US-7040 | WV | Moncove Lake Wildlife Management Area | FOUND | Moncove Lake Wildlife Management Area 873 ac [WildlifeManagementAreas] |
| US-7041 | WV | Plum Orchard Lake Wildlife Management Area | FOUND | Plum Orchard Lake Wildlife Management Ar 3239 ac (lake 174 ac) SHORE [WildlifeManagementAreas] |
| US-7042 | WV | R.D. Bailey Lake Wildlife Management Area | FOUND | R.D. Bailey Lake Wildlife Management Are 17737 ac (lake 551 ac) SHORE [WildlifeManagementAreas] |
| US-7046 | WV | Beech Fork Lake Wildlife Management Area | FOUND | Beech Fork Lake Wildlife Management Area 9372 ac [WildlifeManagementAreas] |
| US-7049 | WV | East Lynn Lake Wildlife Management Area | FOUND | East Lynn Lake Wildlife Management Area 24655 ac (lake 1154 ac) SHORE [WildlifeManagementAreas] |
| US-7052 | WV | Laurel Lake Wildlife Management Area | FOUND | Laurel Lake Wildlife Management Area 12585 ac (lake 21 ac) SHORE [WildlifeManagementAreas] |
| US-7058 | WV | Conaway Run Lake Wildlife Management Area | FOUND | Conaway Run Lake Wildlife Management Are 634 ac (lake 34 ac) SHORE [WildlifeManagementAreas] |
| US-7061 | WV | OBrien Lake Wildlife Management Area | FOUND | O'Brien Lake Wildlife Management Area 1069 ac [WildlifeManagementAreas] |
| US-7063 | WV | Rollins Lake Wildlife Management Area | FOUND | Rollins Lake Wildlife Management Area 68 ac (lake 39 ac) SHORE [WildlifeManagementAreas] |
| US-7068 | WV | Woodrum Lake Wildlife Management Area | FOUND | Woodrum Lake Wildlife Management Area 1653 ac [WildlifeManagementAreas] |
| US-9914 | WV | Elk Fork Lake Wildlife Management Area | FOUND | Elk Fork Lake Wildlife Management Area 1413 ac (lake 206 ac) SHORE [WildlifeManagementAreas] |
| US-10888 | WY | Shirley Basin Reservoir BLM Special Recreation | NOT FOUND |  |
| US-10891 | WY | Teton Reservoir BLM Recreation Management Area | NOT FOUND |  |
| US-12718 | WY | Kortes Reservoir/Miracle Mile BOR Recreation S | NOT FOUND |  |
| US-12720 | WY | Ralston Reservoir BOR & State Fish and Wildlif | NOT FOUND |  |
| US-12722 | WY | Wheatland Reservoir #3 BLM Recreation Manageme | NOT FOUND |  |
| US-6113 | WY | Grayrocks Reservoir State Recreation Area | FOUND | Grayrocks Reservoir 5536 ac (lake 3600 ac) SHORE [PAA_Boundaries] |
