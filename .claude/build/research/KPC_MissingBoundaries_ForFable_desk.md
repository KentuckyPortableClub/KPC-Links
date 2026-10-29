# Missing boundaries: the list for Fable (NEWEST ONLY; Brandon Oct 29 1:54 PM: 'get rid of old one')
The 8:55 AM index was removed. Its detail files are still in .claude/build/research/ if anyone needs them.

## RERUN on the NEW Rule G key (chat 8, Oct 29 ~2:30 PM, grade A; replaces my 2:05 PM section, which read the stale KPC-Data copy)
Read from KPC-Links data/us-key (13,083 parks, 11,312 outlined, 120 check, 808 sites on bigger land, 858 nothing found, pin outside 4,210).
- **The 313 "pin inside a bigger area": 24 now outlined, 289 left.** Needs R-G7 step 2 (a state layer already names something): 63. Step 3 (the official park map hunt; the POTA page link is given): 224. Step 3 with no page at all: 2. Step 4 (ownership) comes only after step 3 finds no boundary line.
- **"Nothing near" 273: 7 now outlined, 266 left. "Likely" 24: 13 now outlined, 11 left.**
- **Fable list so far: nothing.** It is only what steps 2-5 cannot place, so it stays empty until chat 2 / the look-up bot run them. Pool of refs: `missing-after-key.json` (keys PIN INSIDE / NOTHING NEAR / LIKELY).
- Other no-outline parks outside these lists (about 1,000): BLM recreation areas, state trails, historic sites, wild and scenic rivers, national recreation trails. Those are Source Book / own-land work, not R-G7.
- Open key questions: chat 11 answered 26 YES / 1 NO; the rest wait.

## WORK LOG BY STATE (Brandon Oct 29 3:21 PM: everything found goes in THIS file)
One section per state, low to high (IA, MN, RI, CO, HI, ME, VA, AZ, NM, …, NV). Each chat that works a park adds ONE row under its state, never deletes others' rows:
`| park | name | source found (link / layer / our doc) | Rule G step | result: traced / owned land / pin | by chat | date |`
When every park in a state has a row, add 'STATE XX DONE' under it. What is left with 'pin' and no source = the real Fable list.

### MN
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-13547 | Two Harbors Protected Area | our doc: DNR harbor page, no map; look-up blocked (403) | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13546 | Twin Points Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13548 | Knife River Marine Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13549 | McQuade Marine Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |

### CO
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9652 | Grenada SWA | our parkinfo: POTA link = cpw.state.co.us GranadaDeadmanSWA_geo.pdf (opened 200); map-check filed | 3 (map found) | to trace | 8 | Oct 29 |
| US-10540 | Bellevue-Watson Fish Hatchery | cpw.state.co.us/hatchery/bellvue-watson (opened; page, no map); Watson Lake SWA geo PDF likely | 3 | pin until map seen | 8 | Oct 29 |

### ME
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9174 | Mahoosuc Ecological Reserve | our doc: maine.gov/dacf/mnap page, no map; BPL site 403 to bot | 3 | pin (no source yet) | 8 | Oct 29 |
| US-8287 | Capitol State Park | NRHP 89000252 nomination PDF opened (200), written boundary; POTA link is AllTrails | 3 -> 4a | to read + trace | 8 | Oct 29 |

### AZ
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-11944 | Dankworth Pond SP | AZ State Parks park map PDF (usedirect DAPO_Park Map_8-2023); map-check filed | 3 (map found) | to trace | 8 | Oct 29 |
| US-3390 | River Island SP | AZ State Parks park map PDF Park Map-RIIS (opened 200); map-check filed | 3 (map found) | to trace | 8 | Oct 29 |
| US-6071 | Little Black Mountain Petroglyph Site | BLM page (opened 200): BLM Arizona Strip site, not state land; BLM surface layer | 3 -> 4b | BLM land: trace from BLM layer | 8 | Oct 29 |

### CT
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-6860 | Ferry Landing SP | our doc: depdata.ct.gov parks map (statewide, does not name park) | 3 | pin until DEEP park map seen | 8 | Oct 29 |
| US-6875 | The Preserve (Essex Land Trust) | our doc: DEEP page, no map; land trust owns | 3 -> 4b | land-trust parcel; take-back candidate | 8 | Oct 29 |
| US-7529 | Beckley Iron Furnace SP | our doc: DEEP page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-7542 | Satan's Kingdom SRA | our doc: no map on DEEP page | 3 | pin (no source yet) | 8 | Oct 29 |

### MO
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-5715 | Roger Pryor Pioneer Backcountry SP | our doc: park page, no working map; mostateparks trail map PDFs | 3 | pin until map seen | 8 | Oct 29 |
| US-5716 | Bruce R. Watkins Cultural Heritage Center SP | our doc: no map | 3 -> 4b | Jackson County parcel | 8 | Oct 29 |
| US-10575 | Walnut Woods CA | MDC news (opened): donated to City of Liberty Parks & Rec; our doc: no map | 4b | owner = City of Liberty: Clay County parcel | 8 | Oct 29 |
| US-10576 | Rush Creek CA | MDC news (opened): donated to City of Liberty Parks & Rec | 4b | owner = City of Liberty: Clay County parcel | 8 | Oct 29 |

### SC
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9229 | Wild Turkey WMA | SCDNR WMA map PDF wmamap5 (opened 200; WMA unconfirmed); SCDNR ManagedLand/116 page; map-check filed | 3 | to confirm which WMA the PDF is | 8 | Oct 29 |
| US-9759 | May Forest SP | our doc: park page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13016 | Pine Island SP | our doc: park page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13198 | Black River SP | our doc: park page, no map | 3 | pin (no source yet) | 8 | Oct 29 |

### LA
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2365 | Jimmie Davis SP | our doc: no map on file; web search: no Louisiana state-parks open-data layer found (LDOTD layers only) | 3 | pin (no source yet) | 8 | Oct 29 |
| US-2373 | Poverty Point Reservoir SP | our doc: no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-10354 | Forts Randolph & Buhlow SHS | our doc: no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-10447 | Audubon SHS | our doc: only a brochure-request page | 3 | pin (no source yet) | 8 | Oct 29 |
| US-2374 | Saint Bernard SP | our doc: no map | 3 | pin (no source yet) | 8 | Oct 29 |

### MD
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-13564 | Savage Highlands SP | our doc: no map; leads: MD iMAP MD_ProtectedLands (geodata.md.gov) + DNR AIMS layers (dnr.geodata.md.gov); layer-probe 8-rg7-mdnh filed | 2 -> 3 | to check state layer | 8 | Oct 29 |
| US-7768 | Frederick City Watershed WMA | our doc: map page does not name park; lead WMABoundaries FeatureServer + MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-7769 | Heaters Island WMA | our doc: dnr.maryland.gov/wildlife/Documents/heatersislandmap.pdf (own map PDF) + WMABoundaries layer | 3 (map found) | to trace | 8 | Oct 29 |
| US-6388 | Tawes Garden SP | our doc: map page does not name park; MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-6389 | Jefferson Patterson Park & Museum SP | our doc: no map; MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |

### NH
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2642 | Androscoggin Wayside SP | our doc: shared 51-park file dropped; leads: NHDOT_BOUNDARIES_Parks_Forest MapServer, GRANIT consnh conservation lands | 2 | to check state layer | 8 | Oct 29 |
| US-2654 | Gardner Memorial Wayside SP | same | 2 | to check state layer | 8 | Oct 29 |
| US-2685 | Winslow SP | our doc: nhstateparks.org Mt-Kearsarge map PDF (own map) + consnh | 3 (map found) | to trace | 8 | Oct 29 |
| US-8024 | Taylor Saw Mill SHS | our doc: dropped shared file; consnh | 2 | to check state layer | 8 | Oct 29 |
| US-4931 | Max Israel State Forest | NH Div. of Forests and Lands "State Reservation Maps" page (nhdfl.dncr.nh.gov/land-management/state-reservation-maps); consnh | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4936 | Nash Stream Forest State Forest | same | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4980 | White Farm State Forest | same | 3 | page to read (bot filed) | 8 | Oct 29 |
