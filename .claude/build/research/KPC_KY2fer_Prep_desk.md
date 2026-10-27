# KENTUCKY 2-FER CHECK: PREP (Research desk, chat 8, Mon Oct 26 ~11 PM)

Gather only, **no verdicts**. No page or data file edited. Chat 2 has not said pass 3 is done; the real check starts when it does. Grades: **A** = page/layer/PDF opened and read; **B** = surfaced by search, not opened; **C** = named from a search title only. NOT SURE where I could not settle it.

Limit: this session can open only pages that a search surfaced, so KDFWR's detail pages and the Hoskins PDF could not be opened (the tool refused them). Nothing could be test-queried.

## 1. Where the Forest Service actually OWNS land (not the proclamation line)

| Source | Link | Grade | What it shows | Use for the check |
|---|---|---|---|---|
| **Basic Ownership (USFS EDW_BasicOwnership_02)** | https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_BasicOwnership_02/MapServer (metadata: https://data.fs.usda.gov/geodata/edw/edw_resources/meta/BdyOwn_LSRS_BasicOwnership.xml) | **A** | Surface ownership parcels, merged by class. Field `OWNERCLASSIFICATION` = **USDA FOREST SERVICE** (Forest Service owns), **NON-FS** (not National Forest System land), **UNPARTITIONED RIPARIAN INTEREST** (shoreline, split unclear). Also `FORESTNAME`, `GIS_ACRES`. Published Oct 4 2026, updated weekly, content date Dec 31 2015. "Not a legal document." | **The layer to use.** Fee land = rows where OWNERCLASSIFICATION is USDA FOREST SERVICE and FORESTNAME is Daniel Boone. NON-FS inside the forest = the holes (private, state, Corps). |
| Surface Ownership (more detailed sibling) | https://data.fs.usda.gov/geodata/edw/edw_resources/meta/BdyOwn_LSRS_SurfaceOwnership.xml | B (metadata surfaced, not opened) | Same parcels, not merged; Basic's metadata says SurfaceOwnership "has more detail" | Use if Basic is too coarse for a narrow strip |
| **Proclaimed Forest Boundaries (EDW_ProclaimedForestBoundaries_01)** | https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_ProclaimedForestBoundaries_01/MapServer | **A** | "Boundaries encompassing" National Forest System lands. It does **not** say land inside is owned by the Forest Service. | This is the administrative line the guide counted. It is the one that includes private land. Do not treat as land |
| PAD-US on the Forest Service server | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_PADUS_01/MapServer/0/iteminfo | B | Protected-areas database; Basic metadata says it differs from PAD-US because agencies update on different schedules | Cross-check only |
| Kentucky elk-unit layer, DBNF polygon | https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Elk_Hunting_WGS84WM/MapServer/6 | C | A KY state layer named "Daniel Boone National Forest (hunting allowed within Elk Units)" | Probably a proclamation-style outline; not for ownership |

**DBNF official recreation maps:**
- Visitor Maps and Guides: https://fs.usda.gov/r08/danielboone/maps-guides (grade **B**: surfaced, not opened; the Redbird page links to it as the general map page). This is also the link our data uses as the "official map" for Daniel Boone, Clifty, Rockcastle WSR and Rock Creek WSR.
- Motor Vehicle Use Maps by district (Redbird, Cumberland, London, Stanton) are sold through Avenza (https://store.avenza.com/products/motor-vehicle-use-map-mvum-redbird-district-daniel-boone-national-forest-us-forest-service-r8-map.oembed, C); the Forest Service posts the free copies on the maps-guides page. These show roads, not ownership.
- Honest note: no DBNF page I opened shows a fee-land boundary. Only the Basic Ownership layer does.

## 2. The four WMAs inside the proclamation line

| WMA (POTA ref) | Owner, per official source | Manager | Acres / county | Sources and grade | Verdict-ready? |
|---|---|---|---|---|---|
| **Redbird** (US-10159) | **Forest Service owns it**, per KDFWR's own page: "The U.S. Forest Service owns Redbird WMA, which is within the Daniel Boone National Forest." | KDFWR (public lands biologist) and Forest Service, cooperatively | KDFWR page 25,529 ac; Forest Service page 24,033 ac. Clay and Leslie counties. The two agencies' acreage differs by ~1,500 | KDFWR https://app.fw.ky.gov/kfwis/destinations/Redbird_WMA.htm (**A**); Forest Service https://www.fs.usda.gov/r08/danielboone/recreation/redbird-wildlife-management-area (**A**, says "cooperatively managed with KDFWR", does not say who owns); map PDF https://fw.ky.gov/More/Documents/RedbirdWMA_ALL.pdf (C, could not open) | **Likely a real 2-fer** (FS land managed by KDFWR). But the WMA may include some non-FS parcels: check against Basic Ownership. |
| **Burchell-Beech Creek** (US-3799) | **KDFWR owns it** ("Owned by Kentucky Department of Fish and Wildlife Resources") | KDFWR | 1,241 ac, **Clay County** | KDFWR map PDF https://fw.ky.gov/More/Documents/Burchell-BeechCreekWMA_ALL.pdf (**A**). Header reads "Daniel Boone National Forest" and the legend has "Forest Service Road"; no statement that the Forest Service manages it | **Not Forest Service land.** State-owned. A 2-fer with DBNF only where the WMA map and fee land actually overlap, which owned-by-KDFWR argues against (unless the page header only names the surrounding forest) |
| **Sunny Brook** (US-10168) | **NOT SURE** | KDFWR | Acreage and county not on the map. The map's coordinates (about 38°13′N 83°22′W), "Triplett Creek", "US Highway 60" and "MSU Golf Course Road" place it **near Morehead (Rowan County)** | KDFWR map https://fw.ky.gov/More/Documents/SunnybrookWMAall.pdf (**A**: label "Daniel Boone National Forest", Forest Service Road in legend, map dated 9/3/2021). KDFWR public-lands guide https://fw.ky.gov/Hunt/Documents/HuntingGuidePublicLands.pdf (**A**: "Northeast" region, low management level; says the area "may periodically close... due to future stream restoration construction"; no owner) | Needs the ownership layer; the stream-restoration wording hints at a mitigation purchase, which is only a hint |
| **Hoskins** (US-10138) | **NOT SURE** | KDFWR | Not found. Its contact number (606) 654-2533 is the same Southeast-region number as Boone Forestlands WMA (Leslie/Harlan/Bell/Clay) | KDFWR guide https://fw.ky.gov/Hunt/Documents/HuntingGuidePublicLands.pdf (**A**: "Southeast", low level, no owner). KDFWR map https://fw.ky.gov/More/Documents/Hoskins_WMA_All.pdf (C, could not open) | **Unknown.** Next step: open the Hoskins map and KDFWR's detail page https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9711 by hand |

Useful comparison (not one of the four): **Boone Forestlands WMA** is owned by Boone Forestlands, LLC (private) and managed by KDFWR under a cooperative agreement, 31,668 ac in Bell, Clay, Harlan, Leslie (https://fw.ky.gov/More/Documents/BooneForestlandsWMA_ALL.pdf, **A**). Cane Creek WMA (US-10121) is "cooperatively managed" by the Forest Service and KDFWR, 6,677 ac, Laurel County; the page does not say who owns it (https://fs.usda.gov/r08/danielboone/recreation/cane-creek-wildlife-management-area, **A**). The word "cooperatively managed" appears on the Forest Service pages; **only Redbird's KDFWR page says the Forest Service owns**.

The bot's note on these (mapping.md Oct 26): the four WMAs sit inside the DBNF proclamation line but not on Forest Service fee land, and the guide "likely counted the proclamation line". Evidence so far: Burchell-Beech is KDFWR-owned (supports the bot); Redbird is Forest Service-owned per KDFWR (**contradicts the bot**); the other two are open.

## 3. The suspect pairs (what the official sources say about the land between)

Bot result (data/fers/US-KY.json): Cumberland Falls x DBNF and Natural Bridge x DBNF both flagged "two owners (a state park and Forest Service land cannot own the same ground: a lease or a map error)"; Big South Fork x DBNF is a "candidate (saved outline only)".

| Pair | What the official/trusted sources say | Grade |
|---|---|---|
| **Cumberland Falls State Resort Park x Daniel Boone NF** (US-1277 / US-4484) | Wikipedia: the park (1,657 ac) is "contained entirely within the Daniel Boone National Forest", operated by the KY Department of Parks. The falls plus 593 acres were bought by T. Coleman du Pont's widow in 1930, park dedicated 1931. Does not say who holds title to the rest, or whether any is leased. Park official page: https://parks.ky.gov/corbin/parks/resort/cumberland-falls-state-resort-park | A (Wikipedia, not official) / official page B |
| **Natural Bridge State Resort Park x Daniel Boone NF** (US-1286 / US-4484) | Wikipedia: park is "surrounded by" the DBNF and adjacent to the Red River Gorge Geological Area; administered by the KY Department of Parks; the original land came from the L&N Railroad (137 ac, 1926), nature-preserve part (1,200 ac) dedicated in 1981. Park official page: https://parks.ky.gov/slade/parks/resort/natural-bridge-state-resort-park | A (Wikipedia) / official page B |
| **Big South Fork NRA x Daniel Boone NF** (US-0686 / US-4484) | NPS holds the NRA; the Wikipedia page does not describe a border with the forest (125,310 ac total, McCreary County in Kentucky). NPS boundary layer: https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer (layers 1 "NPS Tracts", 2 "NPS Boundary"; **A**). Map: https://www.nps.gov/biso/planyourvisit/maps.htm | A (layer) / the border question is NOT SURE |
| **Red River WSR x Natural Bridge** (US-10104) | Office of Kentucky Nature Preserves manages the Red River Wild River corridor; ownership "varies by tract", about half lies in DBNF's Red River Gorge Geological Area; the page does not say the Forest Service owns that part. Natural Bridge is under 10 miles from the corridor's southwest part. https://eec.ky.gov/Nature-Preserves/Locations/Pages/Red-River-Wild-River.aspx | A |

Land between them: **I could not find an official map showing the Cumberland Falls, Natural Bridge or Big South Fork boundaries against Forest Service fee land.** The answer is in the Basic Ownership layer (section 1): look at the parcels' OWNERCLASSIFICATION inside each state-park outline. If they read USDA FOREST SERVICE, it is a map or lease question; if NON-FS, no overlap on Forest Service land. The state parks' own legal boundary is not published as an open layer that I found; the only Kentucky Parks layers that surfaced were Lexington city parks and a "Park Point" copy (not the state park polygons).

## 4. EVERY pair in the old Kentucky 2-fers guide (71 spots), with each park's official links

The guide is `KPC_Kentucky_POTA_2fers_3fers_Guide.pdf` (the GPX has 71 2-fer/3-fer pins; pins repeat per spot, this list is by unique pair). Each park's web and official-map link, from `kpc-ky-data.json` (`web`, `off`), is in the table at the end of this section so the check can open both side by side. Flags mark links that are not a real official map.

### Pairs
| Type | Parks |
|---|---|
| 3-fer | Lewis and Clark National Historic Trail (US-4572) + Trail of Tears National Historic Trail (US-3791) + Ballard Wildlife Management Area (US-3793) |
| 3-fer | Lewis and Clark National Historic Trail (US-4572) + Trail of Tears National Historic Trail (US-3791) + Boatwright Wildlife Management Area (US-3797) |
| 3-fer | Lewis and Clark National Historic Trail (US-4572) + Trail of Tears National Historic Trail (US-3791) + Big Rivers Wildlife Management Area (US-3796) |
| 3-fer | Lewis and Clark National Historic Trail (US-4572) + Trail of Tears National Historic Trail (US-3791) + West Kentucky Wildlife Management Area (US-3837) |
| 3-fer | Pine Mountain State Trail (US-10102) + Bad Branch National Wild and Scenic River (US-10112) + Bad Branch State Nature Preserve (US-7966) |
| 3-fer | Pine Mountain State Trail (US-10102) + Jefferson National Forest Wildlife Management Area (US-10139) + George Washington & Jefferson National Forest (US-4526) |
| 3-fer | Red River National Wild and Scenic River (US-10104) + Clifty Wilderness Area (US-3801) + Daniel Boone National Forest (US-4484) |
| 3-fer | The Rockcastle National Wild and Scenic River (US-10106) + Cane Creek Wildlife Management Area (US-10121) + Daniel Boone National Forest (US-4484) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + Pioneer Weapons Wildlife Management Area (US-10158) + Daniel Boone National Forest (US-4484) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + Mill Creek Wildlife Management Area (US-10146) + Daniel Boone National Forest (US-4484) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + Cane Creek Wildlife Management Area (US-10121) + Daniel Boone National Forest (US-4484) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + Rock Creek National Wild and Scenic River (US-10111) + Daniel Boone National Forest (US-4484) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + Clifty Wilderness Area (US-3801) + Daniel Boone National Forest (US-4484) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + The Cumberland River Wilderness Area (US-10103) + Cumberland Falls State Park (US-1277) |
| 3-fer | Sheltowee Trace National Recreation Trail (US-11181) + The Cumberland River Wilderness Area (US-10103) + Daniel Boone National Forest (US-4484) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Wickliffe Mounds State Historic Site (US-3788) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Big Bone Lick State Historic Site (US-3779) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Land Between the Lakes National Recreation Area (US-3792) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Yellowbank Wildlife Management Area (US-3840) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Green River State Forest (US-7951) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + John James Audubon State Park (US-1260) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Sloughs Wildlife Management Area (US-3830) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Six Mile Island State Nature Preserve (US-7955) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Otter Creek State Recreation Area (US-8144) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Columbus Belmont State Park (US-1252) |
| 2-fer | Pine Mountain State Trail (US-10102) + Bad Branch National Wild and Scenic River (US-10112) |
| 2-fer | Pine Mountain State Trail (US-10102) + Bad Branch State Nature Preserve (US-7966) |
| 2-fer | Pine Mountain State Trail (US-10102) + Breaks Interstate State Park (US-3781) |
| 2-fer | Fort Donelson National Battlefield (US-0703) + Fort Heiman National Battlefield (US-3790) |
| 2-fer | George Washington & Jefferson National Forest (US-4526) + Jefferson National Forest Wildlife Management Area (US-10139) |
| 2-fer | Bad Branch State Nature Preserve (US-7966) + Bad Branch National Wild and Scenic River (US-10112) |
| 2-fer | Beaver Creek Wildlife Management Area (US-3794) + Daniel Boone National Forest (US-4484) |
| 2-fer | Big South Fork National Recreation Area (US-0686) + Big South Fork National Wild and Scenic River (US-10107) |
| 2-fer | Burchell-Beech Wildlife Management Area (US-3799) + Daniel Boone National Forest (US-4484) |
| 2-fer | Cane Creek Wildlife Management Area (US-10121) + Daniel Boone National Forest (US-4484) |
| 2-fer | Cane Creek Wildlife Management Area (US-10121) + The Rockcastle National Wild and Scenic River (US-10106) |
| 2-fer | Carter Caves State Park (US-1276) + Bat Cave State Nature Preserve (US-12971) |
| 2-fer | Carter Caves State Park (US-1276) + Cascade Caverns State Nature Preserve (US-12972) |
| 2-fer | Cumberland Falls State Park (US-1277) + The Cumberland River Wilderness Area (US-10103) |
| 2-fer | Daniel Boone National Forest (US-4484) + The Rockcastle National Wild and Scenic River (US-10106) |
| 2-fer | Daniel Boone National Forest (US-4484) + Rock Creek National Wild and Scenic River (US-10111) |
| 2-fer | Daniel Boone National Forest (US-4484) + The Cumberland River Wilderness Area (US-10103) |
| 2-fer | Daniel Boone National Forest (US-4484) + Clifty Wilderness Area (US-3801) |
| 2-fer | Daniel Boone National Forest (US-4484) + Red River National Wild and Scenic River (US-10104) |
| 2-fer | Hoskins Wildlife Management Area (US-10138) + Daniel Boone National Forest (US-4484) |
| 2-fer | Mammoth Cave National Park (US-0050) + The Green National Wild and Scenic River (US-10105) |
| 2-fer | Mill Creek Wildlife Management Area (US-10146) + Daniel Boone National Forest (US-4484) |
| 2-fer | Pioneer Weapons Wildlife Management Area (US-10158) + Daniel Boone National Forest (US-4484) |
| 2-fer | Red River National Wild and Scenic River (US-10104) + Clifty Wilderness Area (US-3801) |
| 2-fer | Redbird Wildlife Management Area (US-10159) + Daniel Boone National Forest (US-4484) |
| 2-fer | Rockcastle River Wildlife Management Area (US-10160) + Daniel Boone National Forest (US-4484) |
| 2-fer | Rockcastle River Wildlife Management Area (US-10160) + The Rockcastle National Wild and Scenic River (US-10106) |
| 2-fer | Sunny Brook Wildlife Management Area (US-10168) + Daniel Boone National Forest (US-4484) |
| 2-fer | Twin Knobs Campground Wildlife Management Area (US-10170) + Daniel Boone National Forest (US-4484) |
| 2-fer | Zilpo Campground Wildlife Management Area (US-10171) + Daniel Boone National Forest (US-4484) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + Sinking Creek State Natural Area (US-7970) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + Big South Fork National Recreation Area (US-0686) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + Rock Creek National Wild and Scenic River (US-10111) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + Daniel Boone National Forest (US-4484) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + Natural Bridge State Park (US-1286) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + Cumberland Falls State Park (US-1277) |
| 2-fer | Sheltowee Trace National Recreation Trail (US-11181) + The Cumberland River Wilderness Area (US-10103) |
| 3-fer | Trail of Tears National Historic Trail (US-3791) + Fort Donelson National Battlefield (US-0703) + Fort Heiman National Battlefield (US-3790) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Land Between the Lakes National Recreation Area (US-3792) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Kentucky Lake Wildlife Management Area (US-10140) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Kenlake State Park (US-1282) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Kentucky Dam Village State Park (US-1283) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Doug Travis Wildlife Management Area (US-3808) |
| 2-fer | Trail of Tears National Historic Trail (US-3791) + Livingston County Wildlife Management Area (US-3823) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Livingston County Wildlife Management Area (US-3823) |
| 2-fer | Lewis and Clark National Historic Trail (US-4572) + Ohio River Islands National Wildlife Refuge (US-0608) |

### Park links (web = park's own page, map = `off`)
| Ref | Park | Type | Web | Official map |
|---|---|---|---|---|
| US-0050 | Mammoth Cave National Park | National Park | https://www.nps.gov/maca/index.htm | https://www.nps.gov/maca/planyourvisit/maps.htm |
| US-0608 | Ohio River Islands National Wildlife Refuge | National / NPS | https://www.fws.gov/refuge/ohio-river-islands | https://www.fws.gov/refuge/ohio-river-islands/visit-us |
| US-0686 | Big South Fork National Recreation Area | National Recreation Area | https://www.nps.gov/biso/index.htm | https://www.nps.gov/biso/planyourvisit/maps.htm |
| US-0703 | Fort Donelson National Battlefield | National / NPS | https://next.pota.app/park/US-0703 | https://www.nps.gov/fodo/planyourvisit/maps.htm [web = POTA page, not official] |
| US-1252 | Columbus Belmont State Park | State Park | https://parks.ky.gov/columbus/parks/historic/columbus-belmont-state-park | https://www.kentuckytourism.com/media/docs/default-source/listing-documents/park-map5b26b649-8218-47fa-93e2-4d9b3a8b06b7.pdf?sfvrsn=c1efe6cb_2 |
| US-1260 | John James Audubon State Park | State Park | https://parks.ky.gov/henderson/parks/historic/john-james-audubon-state-park | https://www.kentuckytourism.com/media/docs/default-source/listing-documents/park-map50475013-f17e-4081-963b-98164c6a6fca.pdf?sfvrsn=f8b3bb8f_2 |
| US-1276 | Carter Caves State Park | State Park | https://parks.ky.gov/olive-hill/parks/resort/carter-caves-state-resort-park | https://Eec.ky.gov/Natural-Resources/Forestry/Documents/TygartsStateForest_ALL.pdf |
| US-1277 | Cumberland Falls State Park | State Park | https://parks.ky.gov/corbin/parks/resort/cumberland-falls-state-resort-park | https://parks.ky.gov/parks/find-a-park/cumberland-falls-state-resort-park-7786 |
| US-1282 | Kenlake State Park | State Park | https://parks.ky.gov/hardin/parks/resort/kenlake-state-resort-park | https://www.kentuckytourism.com/media/docs/default-source/listing-documents/park-map184010cd-2282-44e9-8538-2c31533d3699.pdf?sfvrsn=3adced7e_2 |
| US-1283 | Kentucky Dam Village State Park | State Park | https://parks.ky.gov/gilbertsville/parks/resort/kentucky-dam-village-state-resort-park | https://www.kentuckytourism.com/media/docs/default-source/listing-documents/park-mapa1d96cf9-4bbf-40cb-9e2c-17ae776ad27d.pdf?sfvrsn=f6a25db3_0 |
| US-1286 | Natural Bridge State Park | State Park | https://parks.ky.gov/slade/parks/resort/natural-bridge-state-resort-park | https://parks.ky.gov/explore/natural-bridge-state-resort-park-7796 |
| US-3779 | Big Bone Lick State Historic Site | Other | https://parks.ky.gov/union/parks/historic/big-bone-lick-state-historic-site | https://www.kentuckytourism.com/media/docs/default-source/listing-documents/park-map8929d877-a36c-45e6-a250-e218cc865fb7.pdf?sfvrsn=77032b6c_2 |
| US-3781 | Breaks Interstate State Park | State Park | https://www.breakspark.com/ | https://www.breakspark.com/parkmap |
| US-3788 | Wickliffe Mounds State Historic Site | Other | https://parks.ky.gov/wickliffe/parks/historic/wickliffe-mounds-state-historic-site | https://www.kentuckytourism.com/media/docs/default-source/listing-documents/park-map5a0ad43e-b0cf-4f09-8ae9-c5db00f46227.pdf?sfvrsn=b3c88011_0 |
| US-3790 | Fort Heiman National Battlefield | National / NPS | https://www.nps.gov/fodo/planyourvisit/maps.htm | https://www.nps.gov/fodo/planyourvisit/maps.htm [same as web] |
| US-3791 | Trail of Tears National Historic Trail | National / NPS | https://www.nps.gov/trte/index.htm | https://www.nps.gov/trte/planyourvisit/maps.htm |
| US-3792 | Land Between the Lakes National Recreation Area | National Recreation Area | https://landbetweenthelakes.us/ | https://www.landbetweenthelakes.us/help-center/lbl-maps/ |
| US-3793 | Ballard Wildlife Management Area | WMA | https://app.fw.ky.gov/public_lands_search/detail.aspx?Kdfwr_id=224 | https://fw.ky.gov/More/Documents/BallardWMA_All.pdf |
| US-3794 | Beaver Creek Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=39 | https://fw.ky.gov/More/Documents/BeaverCreekWMA_ALL.pdf |
| US-3796 | Big Rivers Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9203 | https://fw.ky.gov/More/Documents/BigRiversWMA_and_StateForest_all.pdf |
| US-3797 | Boatwright Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=222 | https://fw.ky.gov/More/Documents/BoatwrightWMA_All.pdf |
| US-3799 | Burchell-Beech Wildlife Management Area | WMA | https://next.pota.app/park/US-3799 | https://fw.ky.gov/More/Documents/Burchell-BeechCreekWMA_ALL.pdf [web = POTA page, not official] |
| US-3801 | Clifty Wilderness Area | River / Wilderness | https://www.fs.usda.gov/recarea/dbnf/recarea/?recid=39460 | https://www.fs.usda.gov/r08/danielboone/maps-guides [general agency maps page / shared folder] |
| US-3808 | Doug Travis Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=40 | https://fw.ky.gov/More/Documents/DougTravisWMA_ALL.pdf |
| US-3823 | Livingston County Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9117 | https://fw.ky.gov/More/Documents/LivingstonCountyWMAandStateNaturalArea_All.pdf |
| US-3830 | Sloughs Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=230 | https://fw.ky.gov/More/Documents/Sloughs_WMA_All.pdf |
| US-3837 | West Kentucky Wildlife Management Area | WMA | https://app.fw.ky.gov/public_lands_search/detail.aspx?Kdfwr_id=137 | https://fw.ky.gov/More/Documents/West_Kentucky_WMA.pdf |
| US-3840 | Yellowbank Wildlife Management Area | WMA | https://app.fw.ky.gov/public_lands_search/detail.aspx?Kdfwr_id=192 | https://fw.ky.gov/More/Documents/YellowbankWMA_ALL.pdf |
| US-4484 | Daniel Boone National Forest | National Forest | https://www.fs.usda.gov/dbnf/ | https://www.fs.usda.gov/r08/danielboone/maps-guides [general agency maps page / shared folder] |
| US-4526 | George Washington & Jefferson National Forest | National Forest | https://www.fs.usda.gov/gwj | https://www.fs.usda.gov/r08/gwj/maps-guides [general agency maps page / shared folder] |
| US-4572 | Lewis and Clark National Historic Trail | National / NPS | https://www.nps.gov/lecl/index.htm | https://www.nps.gov/lecl/planyourvisit/maps.htm |
| US-7951 | Green River State Forest | State Forest | https://eec.ky.gov/Natural-Resources/Forestry/ky-state-forests/Pages/Green-River-State-Forest.aspx | https://fw.ky.gov/More/Documents/GreenRiverStateForest_ALL.pdf |
| US-7955 | Six Mile Island State Nature Preserve | Nature Preserve | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Six-Mile-Island.aspx | NONE |
| US-7966 | Bad Branch State Nature Preserve | Nature Preserve | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Bad-Branch.aspx | https://eec.ky.gov/Nature-Preserves/Brochures/BadBranchbrochure_bw.pdf |
| US-7970 | Sinking Creek State Natural Area | Nature Preserve | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Sinking-Creek.aspx | https://eec.ky.gov/Nature-Preserves/Locations/PublishingImages/Sinking%20Creek%20-%20Sheltowee%20Trace%20Bridge%20-%20photo%20by%20Thomas%20G.%20Barnes%20from%20Kentucky,%20Naturally%20book.jpg [map link is a PHOTO, not a map] |
| US-8144 | Otter Creek State Recreation Area | Recreation Area | https://fw.ky.gov/Pages/Otter-Creek-Outdoor-Recreation-Area.aspx | https://fw.ky.gov/Documents/Otter_Creek_Brochure_Map.pdf |
| US-10102 | Pine Mountain State Trail | Trail | https://parks.ky.gov/whitesburg/parks/recreation/pine-mountain-state-scenic-trail | https://parks.ky.gov/parks/find-a-park/pine-mountain-state-scenic-trail-7826 |
| US-10103 | The Cumberland River Wilderness Area | River / Wilderness | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Cumberland-River-Wild-River.aspx | https://fw.ky.gov/Education/Documents/bluewatertrailcumberlandriver-1.pdf |
| US-10104 | Red River National Wild and Scenic River | National / NPS | https://www.fs.usda.gov/recarea/dbnf/recreation/recarea/?recid=39548 | https://usfs-public.app.box.com/s/hl7pijwfnyefzcuebgl6yialfsxae9km [general agency maps page / shared folder] |
| US-10105 | The Green National Wild and Scenic River | National / NPS | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Green-River-Wild-River.aspx | https://www.nps.gov/maca/planyourvisit/upload/Backcountry-Map-and-Guide-2014-Web.pdf |
| US-10106 | The Rockcastle National Wild and Scenic River | National / NPS | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Rockcastle-River-Wild-River.aspx | https://www.fs.usda.gov/r08/danielboone/maps-guides [general agency maps page / shared folder] |
| US-10107 | Big South Fork National Wild and Scenic River | National / NPS | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Big-South-Fork-Wild-River.aspx | https://www.nps.gov/biso/planyourvisit/maps.htm |
| US-10111 | Rock Creek National Wild and Scenic River | National / NPS | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Rock-Creek-Wild-River.aspx | https://www.fs.usda.gov/r08/danielboone/maps-guides [general agency maps page / shared folder] |
| US-10112 | Bad Branch National Wild and Scenic River | National / NPS | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Bad-Branch-Wild-River.aspx | NONE |
| US-10121 | Cane Creek Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=38 | https://fw.ky.gov/More/Documents/CaneCreekWMA_ALL.pdf |
| US-10138 | Hoskins Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9711 | https://fw.ky.gov/More/Documents/Hoskins_WMA_All.pdf |
| US-10139 | Jefferson National Forest Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9078 | https://app.fw.ky.gov/kfwis/Map_Images/JeffersonNationalForest_onlineimage.jpg [map link is a PHOTO, not a map] |
| US-10140 | Kentucky Lake Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=227 | https://fw.ky.gov/More/Documents/KentuckyLakeWMA_ALL.pdf |
| US-10146 | Mill Creek Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=37 | https://fw.ky.gov/More/Documents/MillCreekWMA_ALL.pdf |
| US-10158 | Pioneer Weapons Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=36 | https://fw.ky.gov/More/Documents/PioneerWeaponsWMA_ALL.pdf |
| US-10159 | Redbird Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=35 | https://fw.ky.gov/More/Documents/RedbirdWMA_ALL.pdf |
| US-10160 | Rockcastle River Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9217 | https://fw.ky.gov/More/Documents/RockcastleRiverWMA_ALL.pdf |
| US-10168 | Sunny Brook Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9707 | https://fw.ky.gov/More/Documents/SunnybrookWMAall.pdf |
| US-10170 | Twin Knobs Campground Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9116 | https://usfs-public.app.box.com/s/mkk3sln2dj49cc207476rpru4ahck6vp [general agency maps page / shared folder] |
| US-10171 | Zilpo Campground Wildlife Management Area | WMA | https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9094 | https://usfs-public.app.box.com/s/q18extxpqb7ota6w4c6vpl65317w2iv0 [general agency maps page / shared folder] |
| US-11181 | Sheltowee Trace National Recreation Trail | Trail | https://www.fs.usda.gov/wildflowers/regions/southern/SheltoweeTrace/index.shtml | https://www.fs.usda.gov/Internet/FSE_DOCUMENTS/stelprdb5427184.pdf |
| US-12971 | Bat Cave State Nature Preserve | Nature Preserve | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Carter-Caves.aspx | https://eec.ky.gov/Nature-Preserves/Locations/PublishingImages/Carter%20Caves%20SP%20-%20photo%20by%20Thomas%20G.%20Barnes%20from%20Kentucky,%20Naturally%20book.jpg [map link is a PHOTO, not a map] |
| US-12972 | Cascade Caverns State Nature Preserve | Nature Preserve | https://opengisdata.ky.gov/datasets/ky-knp-state-nature-preserves/explore?location=38.354945%2C-83.108279%2C14.97 | https://eec.ky.gov/Nature-Preserves/Locations/PublishingImages/Carter%20Caves%20SP%20-%20photo%20by%20Thomas%20G.%20Barnes%20from%20Kentucky,%20Naturally%20book.jpg [map link is a PHOTO, not a map] |

### Link problems the check will hit
- **Not official / not a map:** Fort Donelson and Burchell-Beech have a POTA page as `web`; Sinking Creek, Bat Cave and Cascade Caverns have a **photo** as the "map"; Cascade Caverns' web is an open-data explorer page, not a park page; Rockcastle WSR, Rock Creek WSR, Daniel Boone, Clifty and others point at the general DBNF maps page, not a boundary map; Red River and Twin Knobs/Zilpo point at a shared Box folder; Bad Branch WSR and Six Mile Island have no map.
- **Same outline for two numbers:** Fort Donelson (US-0703) and Fort Heiman (US-3790) share one outline in the data (`data/fers/same-outline-ky.json`); so does Jefferson National Forest (US-10139) with GWJ NF (US-4526). Treat as one park unless the agencies show two.
- The Trail of Tears and Lewis & Clark trails (US-3791, US-4572) are lines. Their NPS pages are the only maps; the guide says the four historic trail sites are "not on the river or trail at all".

## 5. For the real check (in order, once chat 2 says pass 3 is done)
1. Pull the Basic Ownership fee land for Daniel Boone (OWNERCLASSIFICATION = USDA FOREST SERVICE) and test the four WMAs, Cumberland Falls, Natural Bridge and Big South Fork against it.
2. Open Hoskins and Sunny Brook (KDFWR detail page by hand) for the owner.
3. For each remaining mismatch in the bot's 76-pair KY list, open both parks' links in section 4.
4. Corps lease maps (Lake Cumberland, Barkley, Kentucky Lake, Green River) are not in this prep; no Corps map was fetched.

## Sources
- https://data.fs.usda.gov/geodata/edw/edw_resources/meta/BdyOwn_LSRS_BasicOwnership.xml
- https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_BasicOwnership_02/MapServer/0/iteminfo
- https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_ProclaimedForestBoundaries_01/MapServer
- https://fs.usda.gov/r08/danielboone/maps-guides
- https://app.fw.ky.gov/kfwis/destinations/Redbird_WMA.htm
- https://www.fs.usda.gov/r08/danielboone/recreation/redbird-wildlife-management-area
- https://fw.ky.gov/More/Documents/Burchell-BeechCreekWMA_ALL.pdf
- https://fw.ky.gov/More/Documents/SunnybrookWMAall.pdf
- https://fw.ky.gov/Hunt/Documents/HuntingGuidePublicLands.pdf
- https://fw.ky.gov/More/Documents/BooneForestlandsWMA_ALL.pdf
- https://fs.usda.gov/r08/danielboone/recreation/cane-creek-wildlife-management-area
- https://en.wikipedia.org/wiki/Cumberland_Falls_State_Resort_Park
- https://en.wikipedia.org/wiki/Natural_Bridge_State_Resort_Park
- https://en.wikipedia.org/wiki/Big_South_Fork_National_River_and_Recreation_Area
- https://eec.ky.gov/Nature-Preserves/Locations/Pages/Red-River-Wild-River.aspx
- https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer
