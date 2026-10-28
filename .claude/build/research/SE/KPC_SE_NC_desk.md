# Southeast Source Book: NORTH CAROLINA (desk, Oct 27 2026)
Grades: A = opened and read, B = surfaced by search only, C = inference. Read only.

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / license | Do we read it? |
|---|---|---|---|---|
| Managed areas (state parks, natural areas, game lands, easements, many owners) | https://ncnhde.natureserve.org/arcgis/rest/services/NC_Public/Managed_Areas/MapServer/0 (A) | NC Natural Heritage Program (NCNHDE) | fields MA_NAME, OWNER, OWNER_TYPE (Federal / Local Government / Private / State), CATEGORY, DATA_DATE, SRC_DATE; description and copyright blank; **no public-access field, and the program warns a listing does not mean the public can use it** (A, ncnhp attribute sheet) | YES (sgnca) |
| Game lands | services1.arcgis.com/YfqBAUM5nWR3yhGP … gamelands_general; also GL_points, GLtrails_roads (trails/roads, layers Trail 0, Roads 1, Secondary Roads 2, copyright NC Wildlife Resources Commission) (A) | NCWRC | no date or license text shown | YES (sgncb) boundaries; **trail/road lines NOT read** |
| State parks | NO dedicated state-parks boundary layer found. Searches for NC DPR/OneMap returned only county/regional boundaries (A: none found). Park outlines exist inside Managed Areas (sgnca). | NC Division of Parks & Recreation | | via sgnca only |
| State forests | none found; Managed Areas includes Jordan Lake/Hofmann etc. (B) | NC Forest Service | | via sgnca |
| National forests | services1.arcgis.com/gGHDlz6USftL5Pau … NFsNC_Boundaries_view (B) | USFS | | not in NC key, covered nationally |
| State trails | NC State Trails (Mountains-to-Sea, Yadkin River, Dan River, Deep River etc.): no official line layer found | | | NO |

## 2. POTA parks with no outline in our key (34)
Covered by Managed Areas (probable, check name match): Nature preserves US-3851, 3854, 3857, 3859, 3861, 3862, 3863; Jessups Mill Pond SGL US-10511; Harmon Den WMA US-12662; Nutbush WMA US-6963; Multiple Use Areas Lake Rim US-10406, Micken's Branch US-11238; Hiwassee Dam US-10389, Chatuge Dam Trail US-10398, Apalachia US-10399, Doughton US-12414 (these are TVA/Corps/Blue Ridge Pkwy style "Recreation Parks"), fish hatcheries, state historic sites.
**Uncovered** (no official layer I know of): state trails Yadkin River US-12320, Dan River US-13002, Mountains to Sea State Trail US-8313 (trail lines), Moses H. Cone US-12119 and Julian Price US-12371 (NPS Blue Ridge Parkway: NPS boundary layer needed), Fontana TVA Dam NRA US-8005 (TVA).
Trails (AT, Trail of Tears, Overmountain Victory): national trail lines.

## 3. Trail lines and access
Access we read: Game_Land_Access, NCWRC_Boating_Access_Areas_view. **Not read:** GLtrails_roads (game-land trails/roads, A), NC State Parks trails (none found).

## 4. Tricky land (this is NC's big issue)
- **Game lands are partly "by agreement."** Wikipedia and NCWRC describe NC game lands on federal (Corps, USFS), Duke Energy, and private timber land under cooperative agreements (B). Examples: Jordan Lake and Falls Lake game lands on Corps land (B); Pisgah/Nantahala/Uwharrie/Croatan game lands = national forest land; many mountain game lands = Duke or Alcoa/TVA lands. Brandon's ruling: private land by agreement is not park land except its own POTA number. Use the Managed Areas OWNER_TYPE (Federal/Private/State) as the first hint; the game-land layer alone does not say.
- **State recreation areas on Corps lakes:** Falls Lake SRA, Jordan Lake SRA: the park is state-managed but the land is Corps. Rule 14 = layered Corps+state is a real overlap only when both have POTA numbers and the line is the same land.
- **TVA dams (Hiwassee, Chatuge, Apalachia, Fontana):** land is TVA/Duke, listed by POTA as "State/TVA parks".
- **Water-only:** the Outer Banks sounds; Cape Lookout.
- **Blue Ridge Parkway pieces** (Moses Cone, Julian Price): NPS land; NC state parks next to them (Grandfather Mountain SP) touch but do not layer.

## 5. KNOWN-GOOD layers (NC)
1. ncnhde Managed_Areas MapServer/0 (A)
2. NCWRC gamelands_general (YfqBAUM5nWR3yhGP)
3. NCWRC GL_points / Game_Land_Access (access)
4. NCWRC GLtrails_roads FeatureServer (A, trails)
5. NCWRC Boating_Access_Areas_view
6. NFsNC_Boundaries_view (gGHDlz6USftL5Pau)
7. NC OneMap park services: **ask chat 2's bot to look** (not found by me)

## 6. 2-fers to expect
Confident (B): Pisgah National Forest game land vs. Pisgah NF (same land: "same land, two park numbers"); Nantahala NF vs. Nantahala game land; Uwharrie NF vs. Uwharrie game land; Croatan NF vs. Croatan game land; Great Smoky Mountains NP vs. nothing on the NC side.
Not sure: Jordan Lake SRA vs. Jordan Lake game land (Corps owns both); Falls Lake SRA vs. Falls Lake game land; Lake James SP vs. adjacent game land; Hanging Rock SP vs. Dan River game land (agreement).
- 2026-10-27 (desk): still no official NC State Parks polygon layer found; see KPC_BigHoles_desk.md item 7.
