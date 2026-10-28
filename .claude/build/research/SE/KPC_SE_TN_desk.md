# Southeast Source Book: TENNESSEE (desk, Oct 27 2026)
Chat 8 research desk. Read only. Grades: A = I opened the page and read it; B = surfaced by search, not opened; C = inference/guess. I cannot query polygons, so "covers X" means the layer's published description says so.
Builds on: KPC_Gap_Layers_desk.md, KPC_OfficialMaps_States_desk.md, KPC_TrailLines_desk.md.

## 1. Official boundaries by park type
| Type | Layer (REST) | Publisher | Updated / license | Do we read it? |
|---|---|---|---|---|
| State parks | services5.arcgis.com/bPacKTm9cauMXVfn … TN_State_Parks_Boundaries and TNStatePark_boundaries | TDEC | not stated | YES (sgtna, sgtng) |
| Natural areas (SNA) | https://tdeconline.tn.gov/arcgis/rest/services/TN_Natural_Areas/MapServer (layer 0, also FeatureServer, plus a _points service) (A) | TDEC Division of Natural Areas (credit: S. Williams DNA, R. Schultz TN State Parks, T. Buchanan TDEC ISD) | no date, no license text | YES (sgtnb); sgtnh = natural areas that are not state parks |
| Wildlife/game lands | https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/TWRA/MapServer/3 "Lands" (A) | TWRA, "irregular" updates, copyright "TWRA" | no license text. Fields NAME, MANAGEMENT, CONAME, **OWNERSHIP (10 federal, 20 state, 1 private)**, **OWNCODE (16 owner codes, incl. TNC, city/county)**, ACQUIRED, HUNT | We read two TWRA layers (sgtnc Hunting_Allowed on services3 PWXNAH2YKmZY7lBq, sgtne "State_and_Fed…"). **Not read: this tnmap layer 3.** Its OWNERSHIP field is the best tool we have for rule 14 in TN. |
| State forests | services.arcgis.com/lvPBAGXeSupVUvx2 | TN Dept. of Agriculture Forestry (B) | not stated | YES (sgtnd) |
| Public lands (all agencies) | tnmap.tn.gov …/ENVIRONMENTAL/PUBLIC_LANDS/MapServer (layer 0 = TDEC lands) | state | **Service returned "not started" (error 500) when I opened it** (A) | Partly: sgtnf TDEC_Public_Lands on ArcGIS online is a copy. Re-test later. |
| State trails | No statewide TN state-trail polygon/line layer found | | | NO |

## 2. POTA parks with no outline in our key (25) and what would cover them
| Ref | Park | Covered by |
|---|---|---|
| US-3941, 6237, 6247, 6259, 6261, 6273, 6280 | Grundy Forest + six more State Natural Areas | TN_Natural_Areas layer 0 (we read it as sgtnb) – so a NAME mismatch, not a missing layer. **Ask chat 2 to check name matching.** |
| US-3950 Lauderdale Waterfowl WMA, 7565 AEDC & Woods Reservoir WMA, 7570 Beaverdam Creek WMA, 7577 Charlotte Ann Finnel Neal WMA | TWRA Lands layer 3 | name match again (TWRA names often differ: "Charlotte Ann Finnel Neal" may be listed as "Finnell"). |
| US-12775 Davy Crockett State Forest Lands (SFL), 13514 Lake Halford SFL | State forests layer (sgtnd) or TWRA | check |
| US-13364 Cherokee Trail of Tears SP (dedicated June 2026), US-13567 Clinch River Valley SP (Aug 2026) | Too new. TDEC state-park layer will add them later. Fallback: TDEC park page map. | **UNCOVERED today** (A: dedication news in tn.gov/environment/news/2026) |
| US-11181 Sheltowee Trace, 4556 AT, 4560 Natchez Trace NST, 3791 Trail of Tears NHT, 4577 Overmountain Victory NHT | National trails: NPS/USFS trail lines (already in chat 2's trail lists) | trails |
| US-0642 Natchez Trace Pkwy, US-4376 Manhattan Project NHP | NPS unit boundary (NPS_Land_Resources) | covered by NPS layer if joined; check |
| US-11357 Sellars Farm SAR, 11869 Jim Cummings Park | Sellars: state archaeological area (TN Dept. of Environment & Conservation/Historical). Jim Cummings: local park. | **UNCOVERED** (local parks = our "never" rule for council/city parks only if city-owned; check) |
| US-8313 Mountains to Sea State Trail | This is NC (listed under TN in the pack by mistake). | see NC file |

## 3. Trail lines and access
Access layers we already read: TWRA WMA_Entrances, AllAccessSites, TDEC Park_Entrances_January, Recreation Assets, Parking_Areas polygons, CleanedParkDriveTimes. Good coverage. **Gap: no official TN state-trail line layer** (grade B). Hiking trails in state parks come only from TDEC recreation assets.

## 4. Tricky land for 2-fer rules
- **Land Between the Lakes (TN/KY).** US Forest Service national recreation area, with a TWRA-run WMA inside (TWRA says LBL WMA is a cooperative hunting area; B). Rule 14: the WMA is not separate land. Expect "same land, two park numbers" or one park inside another.
- **TWRA WMAs on TVA, Corps and national forest land.** Cherokee NF / Tellico, Fort Loudoun WMA, Cheatham WMA, Old Hickory, J. Percy Priest, Normandy etc. (B: TWRA's own WMA pages describe TVA or Corps land managed by agreement). The OWNERSHIP field in layer 3 (10 = Federal) is how to detect these. Ask chat 2 to carry it into the key so rule 14 can read it.
- **Water-only:** Reelfoot Lake, TVA reservoir pools (Norris, Douglas etc. are reservoirs, not parks).
- **Parks inside a national park:** Great Smoky Mountains NP overlaps TN/NC; NP boundary vs. state lines is simple, but Foothills Parkway pieces are separate.
- **Natchez Trace Parkway / trails:** lines, not areas; line rules (100 ft).

## 5. KNOWN-GOOD layers for the Discovery Bot (TN)
1. tdeconline TN_Natural_Areas/MapServer/0 (A)
2. tnmap TWRA/MapServer/3 Lands (A)
3. TDEC TN_State_Parks_Boundaries (services5 bPacKTm9cauMXVfn)
4. TDEC TNStatePark_boundaries
5. TN Dept. of Agriculture State Forests (lvPBAGXeSupVUvx2)
6. TWRA WMA_Entrances / AllAccessSites (access)
7. TDEC Park_Entrances (access)
8. tnmap ENVIRONMENTAL/PUBLIC_LANDS (when the service restarts)

## 6. Known 2-fers to expect
Confident (grade B, same land by agency): (a) Great Smoky Mountains NP vs. any state or WMA piece inside it: none. (b) Land Between the Lakes NRA and LBL WMA if both have POTA numbers (look up the numbers in the key; I did not): **layered, expect it**. (c) Cumberland Trail State Park (TDEC) vs. Prentice Cooper WMA: they touch and partly overlap; Cumberland Trail SP corridors cross WMAs (B).
Not sure: Fort Loudoun SHA vs. Fort Loudoun WMA (TWRA-managed on TVA land; the SHA is a small separate tract); Tims Ford SP vs. Tims Ford WMA; Chickasaw SP vs. Chickasaw NWR (NO, different owners but touching).
