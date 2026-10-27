# KENTUCKY 2-FER CHECK: VERDICTS (Research desk, chat 8, Tue Oct 27 ~12:40 AM)

Built on `KPC_KY2fer_Prep_desk.md` and chat 2's rerun (`data/fers/US-KY.json`, 196 spots; mapping.md Oct 27 5 AM comparison). **Nothing in the guide, pages or data was changed**; the guide changes only when Brandon OKs.

How to read: **KEEP** = official sources support it. **DROP** = official sources say two different owners / not Forest Service land. **NOT SURE** = the sources I could open don't settle it. Grades: **A** = official page or layer opened; **B** = surfaced, not opened; **C** = Wikipedia or other non-official. Strength is given for each verdict.

**Limit, said plainly:** this session cannot query a map service. The one test that would settle most "NOT SURE" lines is a point-in-polygon test of each spot against the Forest Service's **Basic Ownership** layer (`OWNERCLASSIFICATION = USDA FOREST SERVICE`, Daniel Boone). Only chat 2's bot can run it (section 6).

## 0. HQ RULINGS (Oct 27 4:30 AM, Brandon) AND WHAT THEY CHANGE
Rulings: (1) Daniel Boone = Forest Service-OWNED land only (Basic Ownership layer), never the proclamation line. (2) Owned by one agency, managed by another (the 7 Forest Service WMAs) = real 2-fer, KEEP. (3) Different owners side by side = touching, not a 2-fer, DROP. (4) River/trail parks: POTA item 5, public land within 100 ft of the river edge or trail line; corridor ownership does not matter; the test is whether the OTHER park's public land lies within 100 ft of that edge/line. (5) Water-route historic trails: test against the river's edge (official shoreline). (6) NOT SURE = kept out of the guide until chat 2's ownership / 100-ft test, then desk re-checks; never a "no".

**Final status after the rulings** (this table overrides any wording below that differs):
| Item | Status | Note |
|---|---|---|
| Redbird, Beaver Creek, Cane Creek, Mill Creek, Pioneer Weapons, Twin Knobs, Zilpo x Daniel Boone (the 7 Forest Service WMAs) | **KEEP** | KDFWR says Forest Service owns; managed by KDFWR |
| Burchell-Beech, Cumberland Falls, Natural Bridge, Big South Fork, W.H. Martin SNA x Daniel Boone; University of the Cumberlands, Cumberland Forest, Boone Forestlands WMAs x Daniel Boone | **DROP** (different owners, touching) | Big South Fork is NPS-owned; the others state or private |
| Sunny Brook, Hoskins, Rockcastle River WMA x Daniel Boone | **NOT SURE, out of the guide** | Needs the ownership test; KDFWR pages state no owner |
| Wild rivers (Red River, Rockcastle, Rock Creek, Cumberland, Big South Fork, Little South Fork, Bad Branch, Green, Martin's Fork) x Daniel Boone | **NOT SURE, likely KEEP where the overlap is Forest Service land** | AREA test (Brandon 4:34 AM): corridor polygon vs Forest Service-owned DBNF land, a patch at least 50 yards across on Forest Service-owned land. The bot found large overlaps with fee land already (Red River 704 ac, Rockcastle 2,717 ac, Rock Creek 2,595-2,866 ac, Cumberland River 290-958 ac) but they come from the "saved outline" pass only; the Basic Ownership test is still to run |
| Cumberland River wild river x Cumberland Falls | **NOT SURE, likely KEEP** | Area test: the corridor polygon against the falls park, on a state-owned tract (the park is state land). The Daniel Boone member of the old 3-fer fails at the falls (state land) but the corridor x DBNF part may hold on Forest Service land |
| Pioneer Weapons x Sheltowee Trace | **NOT SURE, likely KEEP** | Pioneer Weapons is Forest Service land; the Forest Service trail line inside it, within 100 ft of the line. Needs the Forest Service trail line |
| Big South Fork wild river x Sheltowee Trace | **NOT SURE** | Wild river = area (corridor); Sheltowee = line, so: is the corridor's public land within 100 ft of the trail line? Geometry |
| W.H. Martin SNA x Rockcastle wild river | **NOT SURE** | Area x area: does the preserve overlap the corridor polygon by 50 yards on state-owned land? Martin is owned by the Office of Kentucky Nature Preserves |
| Sinking Creek x Daniel Boone | **NOT SURE** | Owner not found |
| Pine Mountain State Trail (5 pairs) | **NOT SURE** | It is a state park with land (bot tested its ~197-acre state tract; Nature Preserves lists ~2,606 units), so it is an AREA park only where a boundary exists; the guide used the trail line. No official line or full boundary found. Stays out until HQ/chat 2 settle which |
| Water-route Trail of Tears and Lewis & Clark pairs | **NOT SURE, testable** | Test the other park's public shore land within 100 ft of the official shoreline. Needs chat 2 to confirm its river-route files cover the Kentucky Ohio River stretch |
| Land-route Trail of Tears segments / Lewis & Clark auto route | **NOT SURE, out of the guide** | NPS lines are approximate (1:100,000) |
| Cumberland Gap NHP x Wilson Cumberland Trail SP (TN) | **NOT SURE; outside Kentucky guide** | |

**Doubts left (for HQ):**
1. **Shoreline source.** For the water-route trails and the big rivers I need an official river-edge line (Kentucky's own hydrography or USGS National Hydrography). I have not opened one. Chat 2 should say which shoreline file the test will use. On the Ohio, the Kentucky state line is the north bank, so the Kentucky shore is Kentucky land.
2. **Wild rivers are area parks now.** The 9 polygons in `ky-wild-rivers.geojson` (state Wild Rivers, each with its Office of Kentucky Nature Preserves page, type "Wild River (State)") are tested like any area. They carry ACCESS "Restricted", so the spot must be on Forest Service-owned land or a state-owned tract. The geojson has no source line (chat 2 is to note where it came from). The 100-ft shoreline question now applies only to the water-route historic trails and Sheltowee Trace.
3. **State-owned tract source.** Forest Service parcels pass by the Basic Ownership layer; state-owned tracts along a corridor need a state ownership source (Office of Kentucky Nature Preserves tract list, `ky-lands-seen.json`, or the state parcel data).
4. **Sunny Brook and Hoskins** owners (KDFWR gives none).
5. **Pine Mountain** has no official line.
6. **The 40 matched pairs and 56 bot candidates outside Daniel Boone** were not opened pair by pair (section 7).

## 0b. Checked against the whole-world rules (mapping.md "2-FER RULES FOR THE WHOLE WORLD", Oct 27 4:32 AM)
All verdicts above fit rules 1, 3, 4, 5 and 7: the 7 Forest Service WMAs are "agency-land + layering" (KEEP), the side-by-side state/NPS/private pairs are "touching" (DROP), NOT SURE stays out and is never a "no".
**Tension resolved (Brandon 4:34 AM, "wilderness rivers are not trails, it is an overlap"):** a river or trail park WITH an official corridor boundary (the 9 Kentucky Wild Rivers in `ky-wild-rivers.geojson`, US wild and scenic river corridors) is an **AREA park**: test the corridor polygon against the other park like any 2-fer (50-yard patch, public and open land). The corridors are mixed ownership and tagged "Restricted", so the spot must sit on **Forest Service-owned land** (Basic Ownership) or a **state-owned tract**. The 100-ft rule is only for parks that are **just a line** (historic/scenic trail center lines, water trails, Sheltowee Trace).

## 1. The four WMAs (HQ question c)
| WMA | Verdict | Why (official source) | Strength |
|---|---|---|---|
| **Redbird** (US-10159) x Daniel Boone | **KEEP as a real 2-fer** (Forest Service land managed by KDFWR) | KDFWR's own Redbird page: "The U.S. Forest Service owns Redbird WMA, which is within the Daniel Boone National Forest" (https://app.fw.ky.gov/kfwis/destinations/Redbird_WMA.htm, A). Chat 2's scrape of KDFWR's Public Lands Search says the same ("Owned by U.S. Forest Service", Kdfwr_id=35, `data/ky-wma-owners.json`). Forest Service page says "cooperatively managed with KDFWR" (https://www.fs.usda.gov/r08/danielboone/recreation/redbird-wildlife-management-area, A). | Strong. The bot's idea that it is "not on Forest Service fee land" is **contradicted** |
| **Burchell-Beech Creek** (US-3799) x Daniel Boone | **DROP** | KDFWR's WMA map and Public Lands Search both say "Owned by Kentucky Department of Fish and Wildlife Resources" (https://fw.ky.gov/More/Documents/Burchell-BeechCreekWMA_ALL.pdf, A; Kdfwr_id=18). State land, 1,241 acres, Clay County. The map's "Daniel Boone National Forest" header and "Forest Service Road" legend only describe the setting. | Strong |
| **Sunny Brook** (US-10168) x Daniel Boone | **NOT SURE** | KDFWR's page has no owner line (Kdfwr_id=9707, empty in `ky-wma-owners.json`). Map places it near Morehead (Triplett Creek, US 60) with a "Daniel Boone National Forest" label (https://fw.ky.gov/More/Documents/SunnybrookWMAall.pdf, A). KDFWR's hunting guide notes planned stream-restoration work, which suggests a mitigation purchase, only a hint. | Weak. Keep out of the guide until the ownership test is run |
| **Hoskins** (US-10138) x Daniel Boone | **NOT SURE** | KDFWR page has no owner line (Kdfwr_id=9711). Its contact is the same Southeast-region number as Boone Forestlands (private land managed by KDFWR); I could not open its map. | Weak. Keep out until tested |

So of the four: one real (Redbird), one no (Burchell-Beech), two open.

## 2. Daniel Boone pairs from the owner scrape (supports the bot's land test)
KDFWR's own pages say the **Forest Service owns**: Beaver Creek, Cane Creek, Mill Creek, Pioneer Weapons, Redbird, Twin Knobs Campground, Zilpo Campground (`data/ky-wma-owners.json`, each with a KDFWR link). The DBNF's own recreation pages call Cane Creek and Mill Creek "cooperatively managed" (A). These agree with the bot's candidates (Beaver Creek x DBNF 17,521 ac; Mill Creek 12,864; Pioneer 7,703; Cane Creek 6,647; Twin Knobs 690; Zilpo 222). **KEEP** all seven as "Forest Service land managed by KDFWR", strength strong for ownership; the exact overlap shape still comes from the ownership layer.

Not Forest Service, so **DROP** against DBNF fee land: **University of the Cumberlands WMA** (owned by the university per the news report https://www.wymt.com/2025/01/02/agreement-reached-open-new-wildlife-management-area-southern-ky, C; KDFWR page has no owner line), **Cumberland Forest WMA** (owned by C. F. Ataya LLC), **Boone Forestlands WMA** (private, Boone Forestlands LLC, https://fw.ky.gov/More/Documents/BooneForestlandsWMA_ALL.pdf, A). **Rockcastle River WMA** (US-10160, 4.6-acre sliver with DBNF): KDFWR page has no owner line, **NOT SURE**; 4.6 acres is also under the 50-yard rule's comfort zone.

## 3. The suspect state-park pairs (HQ question 2)
| Pair | Verdict | Why | Strength |
|---|---|---|---|
| **Cumberland Falls State Resort Park x Daniel Boone** | **DROP** (map edge mismatch, not a real overlap) | The park is state land: the falls and 593 acres bought privately in 1930, park dedicated 1931 (Wikipedia, C). Wikipedia says it sits "contained entirely within" the forest, which describes the proclamation line, not Forest Service ownership. State parks = Kentucky Department of Parks. Bot already flagged 5 of its 6 spots "two owners". | Medium (no official ownership page for the park opened) |
| **Natural Bridge State Resort Park x Daniel Boone** | **DROP** | Office of Kentucky Nature Preserves page: "Owner: Kentucky Department of Parks"; land added with the state Heritage Land fund "connects the park to the forest" (https://eec.ky.gov/Nature-Preserves/Locations/Pages/Natural-Bridge.aspx, A). Touching, not overlapping. | Strong |
| **Big South Fork NRA x Daniel Boone** | **DROP** (edge mismatch between two federal lines) | KDFWR lists Big South Fork as "Owned by National Park Service". Forest Service fee land and NPS fee land cannot be the same ground. The 141-acre and 61-acre overlaps are most likely the DBNF proclamation line (which includes non-Forest-Service land) crossing the NPS boundary. | Medium. Settle with the ownership layer |
| **Cumberland River Wilderness (wild river) x Cumberland Falls x Daniel Boone** (3-fer, 10.6 acres) | **Demote to NOT SURE** | The Daniel Boone member fails for the same reason as the Falls. A wild river corridor is managed by the Office of Kentucky Nature Preserves with ownership "varies by tract" (its page says the same for Rockcastle: https://eec.ky.gov/Nature-Preserves/Locations/Pages/Rockcastle-River-Wild-River.aspx, A). Wild river x Falls alone might hold. | Weak |
| **Red River Wild River x Daniel Boone (and x Clifty)** (592 and 704 acres) | **NOT SURE** | Corridor ownership varies by tract and "about half" lies in Red River Gorge (https://eec.ky.gov/Nature-Preserves/Locations/Pages/Red-River-Wild-River.aspx, A). Clifty Wilderness is Forest Service wilderness. Needs the ownership layer. | Weak |
| **Rockcastle, Rock Creek, Cumberland and Big South Fork wild rivers x Daniel Boone** | **NOT SURE** (bot found them but dropped many on the pin rule) | Same "owner varies by tract" wording; Rockcastle corridor "lies entirely within the proclamation boundary" (A). | Weak |

## 4. Bot-only and guide-only items
| Item | Verdict | Why | Strength |
|---|---|---|---|
| **Dr. William H. Martin SNA x Daniel Boone** | **DROP** | Owned by the Office of Kentucky Nature Preserves, 458.96 acres, "adjacent to the forest" (https://eec.ky.gov/Nature-Preserves/Locations/Pages/Dr.-William-H.-Martin-WWCA.aspx, A). Adjacent, not overlapping. | Strong |
| **W.H. Martin SNA x Rockcastle wild river** | **NOT SURE** | The preserve protects the Beech Bingham Branch watershed that flows into the Rockcastle (same page). A river line near a preserve edge may be inside the 100-ft zone, but the corridor's land owner is unknown. | Weak |
| **Pioneer Weapons x Sheltowee Trace** (guide only, dropped in pass 3) | **NOT SURE, leaning KEEP** | Pioneer Weapons is Forest Service-owned (KDFWR, Kdfwr_id=36). Sheltowee Trace is a Forest Service National Recreation Trail through the forest and "several wildlife management areas" (Wikipedia, C; trail guide https://www.fs.usda.gov/Internet/FSE_DOCUMENTS/stelprdb5427184.pdf, B). Not a two-owner case: a trail on the owning agency's land. Whether the trail line passes at least 100 yards inside the WMA needs the Forest Service trail line. | Medium for ownership, none for geometry |
| **Sinking Creek SNA x Daniel Boone** (guide only) | **NOT SURE** | I could not open its Nature Preserves page. Other state natural areas next to the forest (Martin, Natural Bridge) are state-owned, which points to DROP. | Weak |
| **Big South Fork wild river x Sheltowee Trace** | **NOT SURE** | The Sheltowee passes through the Big South Fork recreation area (Wikipedia, C). Both are designations along a line, not two landowners. Geometry only. | Weak |
| **Cumberland Gap NHP x Wilson Cumberland Trail State Park (TN)** | **NOT SURE; outside the Kentucky guide** | Searches did not surface an official page on how the Cumberland Trail crosses the park. | None |

## 5. The national historic trail lines (HQ question a: "which line is the official one")
The guide's 29 Trail of Tears and Lewis & Clark pairs (rivers and trails) have trail "pins" the guide itself called "guide pins only", "not checked against the actual water line". The official lines are:
- **Trail of Tears NHT:** National Park Service, National Trails: https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/TRTE_NHT/FeatureServer (A). One layer, "Designated Alignment" line, updated 3/31/22. Its own description: "approximate designated route", digitized at 1:100,000, "identified before ground verification, so it does not always match the historic trail trace."
- **Lewis and Clark NHT:** National Park Service "Congressionally Designated Route": https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Lewis_and_Clark_National_Historic_Trail_Congressionally_Designated_Route/FeatureServer (A for the catalog entry, B for the service itself). "The official National Park Service centerline", "best approximation", data of May 2019, and the catalog page does not say the Ohio River in Kentucky is included.

**Verdict (corrected Oct 27 4:25 AM after Brandon's point that these trails are on the water):** POTA's rule (docs.pota.app/docs/rules.html, Activation Location and Access item 5, confirmed word for word): for a trail or river that is a park by itself, the activator and station must be "on public property within 30.5 meters (100 feet) from the edge of the trail or river."
- **Water-route pairs (Ohio, Tennessee, Mississippi; the trail IS the river):** the NPS line only needs to show the trail follows the river. The test is against the **river edge** (official hydrography shoreline), not the approximate NPS line: does the other park's PUBLIC land come within 100 ft of the water? So the 0.2-3 km gap chat 2 saw between the guide's pins and the NPS line is most likely pin vs line, not a wrong river. These pairs are **TESTABLE, not unconfirmed**. Still NOT SURE until (a) chat 2's data/trails or river-route files are checked to show the NPS file covers the Kentucky Ohio River stretch (the Trail of Tears layer I opened does not describe water routes; the Lewis & Clark catalog entry does not say the Kentucky stretch is included, though it starts on the Ohio at Pittsburgh), and (b) the shore strip is public land.
- **Land-route segments (Trail of Tears land routes, Lewis & Clark auto route):** the NPS lines are approximate (1:100,000, "identified before ground verification"), so the 100-ft rule cannot be confirmed from them. These stay unconfirmed, research-yourself only.
- The earlier wording ("the 29 pairs stay unconfirmed") was too broad for the water-route pairs.

**Pine Mountain State Trail (5 pairs):** the Office of Kentucky Nature Preserves lists it as owned by Kentucky State Parks, "a linear state park still under development", ~120 miles when complete, with no map link (https://eec.ky.gov/Nature-Preserves/Locations/Pages/Pine%20Mountain%20State%20Scenic%20Trail.aspx, A). No official line is published as an open layer (only an Avenza store copy of a KyGeoNet map, C). **Unconfirmed**, same treatment.

## 6. What chat 2's bot should run (the tests I cannot)
1. Download the Basic Ownership parcels for Daniel Boone (`OWNERCLASSIFICATION = USDA FOREST SERVICE`, `FORESTNAME` Daniel Boone) from https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_BasicOwnership_02/MapServer/0 and test **Sunny Brook, Hoskins, Rockcastle River WMA, Sinking Creek, the wild river corridors (Red River, Rockcastle, Rock Creek, Cumberland, Big South Fork)** and the Cumberland Falls / Big South Fork edges against it. Keep a spot only if a patch at least 50 yards across is Forest Service-owned.
2. Test **Pioneer Weapons x Sheltowee Trace** with the Forest Service's own trail layer, 100 ft either side of the line.
3. Add a "managed on Forest Service land" label for the seven Forest Service-owned WMAs so the "two owners" check exempts them (KDFWR says managed, owned by the Forest Service).
4. Leave the 29 historic-trail pairs and the 5 Pine Mountain pairs **unconfirmed** in the guide.

## 7. Not done
- I did not open both maps for the **40 matched** pairs or the **56** bot candidate pairs outside Daniel Boone (Kentucky state-park pairs, Lake Barkley / Kentucky Lake, Ohio River Islands, etc.). Those need a pair-by-pair open of both official maps from the prep file's link table.
- No Corps lease maps were opened (Lake Cumberland, Barkley, Kentucky Lake, Green River).
- Hoskins' KDFWR map and Sinking Creek's page could not be opened here.

## Sources
- https://app.fw.ky.gov/kfwis/destinations/Redbird_WMA.htm
- https://www.fs.usda.gov/r08/danielboone/recreation/redbird-wildlife-management-area
- https://fw.ky.gov/More/Documents/Burchell-BeechCreekWMA_ALL.pdf
- https://fw.ky.gov/More/Documents/SunnybrookWMAall.pdf
- https://fw.ky.gov/More/Documents/BooneForestlandsWMA_ALL.pdf
- https://www.wymt.com/2025/01/02/agreement-reached-open-new-wildlife-management-area-southern-ky
- https://eec.ky.gov/Nature-Preserves/Locations/Pages/Natural-Bridge.aspx
- https://eec.ky.gov/Nature-Preserves/Locations/Pages/Dr.-William-H.-Martin-WWCA.aspx
- https://eec.ky.gov/Nature-Preserves/Locations/Pages/Rockcastle-River-Wild-River.aspx
- https://eec.ky.gov/Nature-Preserves/Locations/Pages/Red-River-Wild-River.aspx
- https://eec.ky.gov/Nature-Preserves/Locations/Pages/Pine%20Mountain%20State%20Scenic%20Trail.aspx
- https://en.wikipedia.org/wiki/Cumberland_Falls_State_Resort_Park
- https://en.wikipedia.org/wiki/Sheltowee_Trace_Trail
- https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/TRTE_NHT/FeatureServer
- https://catalog.data.gov/dataset/lecl-lewis-and-clark-national-historic-trail-congressionally-designated-route
- https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_BasicOwnership_02/MapServer
- `data/ky-wma-owners.json` (chat 2's scrape of KDFWR Public Lands Search, Oct 26)
