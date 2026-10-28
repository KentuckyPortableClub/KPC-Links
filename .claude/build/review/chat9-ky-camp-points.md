# KY hand-list campgrounds: official points (chat 9, Oct 28 2026; chat 8 10:05 AM + chat 10 11:45 AM)
Sources were read by a GitHub runner (probe rounds K4-K6): Land Between the Lakes' own campground pages (each has the agency's Google-Maps pin, an address and a 2025 campground map PDF), the Forest Service national recreation points (EDW_RecreationOpportunities_01), KY DGI's 'Kentucky State Park Campsites' layer (3,319 campsite points, KyGovMaps), RIDB (data/campfed). Never a street-address geocode.

## PLACED NOW (kpc-campgrounds.json, each with `point_src`)
- Hillman Ferry 36.94971,-88.18063 · Piney (TN) 36.48567,-88.03076 · Energy Lake 36.85549,-88.01796 · Wranglers 36.73757,-87.99911: LBL's OWN map pins on their campground pages (+ the 4 cabin rows in the same campgrounds).
- Levi Jackson 37.07839,-84.04542: centre of the park's 137 campsite points in the state campsite layer.

## STILL NO OFFICIAL POINT (15)
- LBL: Fenton + the 10 self-service lakeside camps (Cravens Bay, Nickell Branch, Birmingham Ferry, Smith Bay, Sugar Bay, Taylor Bay, Redd Hollow, Boswell Landing, Gatlin Point, Turkey Bay OHV): the self-service page lists names only, no pins; the Forest Service recreation layer holds NO LBL rows. Next: LBL's printed area map, or one pin per camp from a browser pass of each camp's page.
- NPS: Houchin Ferry, Maple Springs Group (Mammoth Cave), Bandy Creek, Bear Creek Horse, Station Camp (Big South Fork), Wilderness Road (Cumberland Gap): the NPS campground pages hold no coordinates; NPS ArcGIS has no campground layer for these 3 units. Maple Springs has a RIDB point (232468: 37.20722,-86.13167, 5 decimals) and Bear Creek Horse Camp's RIDB id 251468 is 'Bear Creek Campground - KY' (36.64108,-84.52364): CHECK that it is the BSF horse camp before using it.
- KY State Parks: Kingdom Come (not in the state campsite layer: primitive sites).
- Breaks Interstate (VA/KY interstate park; its own site, no pin found).
- KDFWR: Higginson-Henry, Rolling Fork, West Kentucky, Yellowbank WMA camping areas: the KDFWR public-lands pages give the WMA, not the camp spot; no KDFWR camping-point layer found.
- Otter Creek ORA (now Meade County, July 2026).

## CHECK OF THE 44 HAND POINTS THAT ALREADY HAD COORDINATES (chat 8's '62' = 44 points in kpc-campgrounds.json; the rest are RIDB/state rows)
- 33 lie within 500 m of an official agency point (21 KY state park campsite points, 10 Forest Service recreation points, 2 RIDB): placed from an AGENCY map / layer, not an address (the 7-8 decimal points match the layers).
- 11 have no official point within 500 m. Barren River Lake (0.68 km), General Butler (0.55), Kentucky Horse Park (1.0): still close to that park's state campsite points, so they read as agency points too. The rest could not be tested: Green River Lake, Jenny Wiley, Kenlake, Lake Barkley, Lake Cumberland, Pennyrile were not in the 2,000-of-3,319 campsite sample. Zilpo is below.
- ZILPO: the hand point 38.07091,-83.48425 is 0.97 km from the Forest Service's 'Zilpo Recreation Area' point (38.07341,-83.49487). That is the recreation AREA marker, so neither point is the campground loop. RIDB is rounded. CONFIRM NOT POSSIBLE from official points: keep CHECK FIRST.
