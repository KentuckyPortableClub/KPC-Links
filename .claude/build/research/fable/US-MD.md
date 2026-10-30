# Fable book: US-MD (16 rows, 5 parks)
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-MD.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-13564 | Savage Highlands SP | our doc: no map; leads: MD iMAP MD_ProtectedLands (geodata.md.gov) + DNR AIMS layers (dnr.geodata.md.gov); layer-probe 8-rg7-mdnh filed | 2 -> 3 | to check state layer | 8 | Oct 29 |
| US-13564 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-13564 | Savage Highlands State Park | look-up 9-p2-md (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): SAVAGE RIVER SF	 ? ac [DNR Owned Lands and Conserva] *name; SAVAGE RIVER SF ? ac [DNR Owned Lands and Conserva] *name. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6388 | Tawes Garden SP | our doc: map page does not name park; MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-6388 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6388 | Helen Avalynne Tawes Garden State Park | look-up 9-p2-md (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6389 | Jefferson Patterson Park & Museum SP | our doc: no map; MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-6389 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6389 | Jefferson Patterson Park and Museum State Park | look-up 9-p2-md (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): SOUTHERN MARYLAND WOODLANDS NATIONAL WILDLIFE 577173 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-7768 | Frederick City Watershed WMA | our doc: map page does not name park; lead WMABoundaries FeatureServer + MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-7768 | | PAD-US at pin: Frederick Municipal Forest (LOTH, owner CITY/LOC, manager UNK, 5186 ac, Fee, PAD id 16458) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-7768 | Frederick City Watershed Cooperative Wildlife Management Are | look-up 9-p2-md (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-7769 | Heaters Island WMA | our doc: dnr.maryland.gov/wildlife/Documents/heatersislandmap.pdf (own map PDF) + WMABoundaries layer | 3 (map found) | to trace | 8 | Oct 29 |
| US-7769 | Heaters Island WMA | the map found in the row above | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-7769 | | PAD-US at pin: ISLANDS OF THE POTOMAC Wildlife Manageme (SCA, owner SDNR/STAT, manager UNK, 322 ac, Fee, PAD id 56533) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-7769 | Heaters Island Wildlife Management Area | look-up 9-p2-md (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): ISLANDS OF THE POTOMAC WMA ? ac [DNR Owned Lands and Conserva]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
