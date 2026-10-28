# Region 2 MIDWEST: SUMMARY (chat 8 desk, Oct 27 2026)
Files: KPC_MW_<ST>_desk.md (IN IL MO WI MN IA ND SD). OH and MI key check at the bottom. Read only. Grades A/B/C as in the Southeast book; I could not query polygons.

| State | Parks / no outline | Verdict | Main reason |
|---|---|---|---|
| IN | 229 / 22 | GAPS | one key layer; 13 lake State Recreation Areas not found |
| IL | 219 / 15 | READY | 8 name suspects; Shelbyville units |
| MO | 561 / 17 | READY | add trail lines (Long Trails, Trail Routes) |
| WI | 348 / 22 | READY after one add | State Trail Segments (A) |
| MN | 294 / 36 | READY after one add | State Trails Minnesota (A) covers 16 trails; Lake Superior MPAs uncovered |
| IA | 181 / 7 | READY | |
| ND | 155 / 53 | GAPS | 36 State Historic Sites have no polygons; State Forests layer is from 2011 |
| SD | 120 / 11 | READY | no access layer |

## Top adds for chat 2
1. WI State Trail Segments: dnrmaps.wi.gov PR_STATE_TRAILS_NETWORK_PLAN_WTM_Ext/MapServer/0 (A)
2. MN State Trails Minnesota: enterprise.gisdata.mn.gov …/trans_state_trails_minnesota/FeatureServer/0 (A)
3. MO Trail Routes + Long Trails: gis.dnr.mo.gov SPHS_trails_public layers 3, 7 (A)
4. ND State Forests: NDGISHUB_State_Forest FeatureServer (A, old data)
5. MO Wild Areas (layer 13) and MN DNR WMA public layer
6. IN: find a second DNR layer for State Recreation Areas / trails
7. Corps project-land boundaries (IA, IL, MO, SD, IN) for rule 14

## Name mismatches (look missing, only named differently)
IN: Prophetstown Fen, Westercamp, Bryan Woods, J.E. Roush Lake, Spencer County SF. IL: Beall Woods, Donnelley/DePue, Kishwaukee River, Ray Norbut, Rauchfuss Hill, North Point Marina, Washington County, Copperhead Hollow. MO: the three SCAs, Lost Valley, Roger Pryor, Bruce Watkins, Felix Vallé. WI: eight wildlife areas, Kohler-Andrae, four SRAs, Menominee River units. MN: Whitewater, McCarthy Lake, Schueler. IA: La Soya, Teal Basins. ND: Lone Tree, Little Metigoshe. SD: three SRAs.
Common pattern: the key stores the POTA type word ("State Recreation Area", "State Fish and Wildlife Area") that the state layer drops. Ask chat 2 to strip type suffixes before matching.

## NEW grey areas (only)
| # | Question | Lean |
|---|---|---|
| MW-1 | USFWS **Wetland Management Districts** are county-wide admin districts, not land. The land is scattered Waterfowl Production Areas. Treat WMD numbers as pin-only? | Pin only. |
| MW-2 | ND's 36 **State Historic Sites** have no boundaries. | Pin only (same idea as SE-7). |
| MW-3 | Lake Superior **marine protected areas** (MN) – water-only list or park? | Water-only list (rule 9). |
| MW-4 | **Water trails** (Wapsipinicon US-11305) | River kind, line rules. |
Corps-lake state parks/FWAs in this region follow SE-1/SE-5.

## OH and MI key check (no web work)
OH: 276 parks, 3 unjoined (Fort Miamis US-3514, North Country NST, Lewis & Clark NHT): all national, fine. MI: 388 parks, 61 unjoined: 16 National Wild & Scenic Rivers (US-12786…12801), 13 State Harbors, 6 State Trails (Betsie Valley, North Central, Pere Marquette, Iron Belle…), 6 State Forests (Au Sable, Copper Country, Escanaba River, Lake Superior, Mackinaw, Pere Marquette; **the key has MI DNR parks and wildlife layers only, no state forest layer**), 4 National Recreation Areas, Flint SP US-13565 (new), Houghton-Douglass Falls US-13566. MI's earlier test is still pending on my side; add a Michigan DNR State Forest layer and the MI state trail lines before the run.
- 2026-10-27 (desk, Round 2): Michigan DNR account walked: no 6-state-forest polygon (FMUs are not them); lead 'Michigan DNR Project Boundary 2020' hub dataset. See KPC_BigHoles_desk.md R2-2.
