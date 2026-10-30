# Fable book: US-NH (24 rows, 9 parks)
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-NH.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2642 | Androscoggin Wayside SP | our doc: shared 51-park file dropped; leads: NHDOT_BOUNDARIES_Parks_Forest MapServer, GRANIT consnh conservation lands | 2 | to check state layer | 8 | Oct 29 |
| US-2642 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-2642 | Androscoggin Wayside State Park | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Errol Town Forest ? ac [CL: Solid]; 070850701 ? ac [Recreation Inventory: Areas]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-2654 | Gardner Memorial Wayside SP | same | 2 | to check state layer | 8 | Oct 29 |
| US-2654 | | PAD-US at pin: Gile State Forest (SRMA, owner SDNR/STAT, manager SDNR, 6759 ac, Other, PAD id 64275) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-2654 | Gardner Memorial Wayside State Park | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Gile State Forest ? ac [CL: Solid]; 131350702 ? ac [Recreation Inventory: Areas]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-2685 | Winslow SP | our doc: nhstateparks.org Mt-Kearsarge map PDF (own map) + consnh | 3 (map found) | to trace | 8 | Oct 29 |
| US-2685 | Winslow SP | the map found in the row above | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-2685 | | PAD-US at pin: Mount Kearsarge State Forest (SRMA, owner SDNR/STAT, manager SDNR, 3893 ac, Other, PAD id 64278) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-2685 | Winslow State Park | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): 131350702 ? ac [Recreation Inventory: Areas]; Kearsarge Mt State Forest ? ac [CL: Solid]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-4931 | Max Israel State Forest | NH Div. of Forests and Lands "State Reservation Maps" page (nhdfl.dncr.nh.gov/land-management/state-reservation-maps); consnh | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4931 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4931 | Max Israel State Forest | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 6 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-4936 | Nash Stream Forest State Forest | same | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4936 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4936 | Nash Stream Forest State Forest | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): SILVIO O. CONTE NATIONAL FISH AND WILDLIFE RE 7136332 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-4936 VT | Nash Stream Forest State Forest | (no owner field) | 105-033-10158  ac | needs-parcel (layer has no owner: county assessor) |
| US-4980 | White Farm State Forest | same | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4980 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4980 | White Farm State Forest | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): SILVIO O. CONTE NATIONAL FISH AND WILDLIFE RE 7136332 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-4980 VT | White Farm State Forest | (no owner field) | 249-079-10028  ac | needs-parcel (layer has no owner: county assessor) |
| US-8024 | Taylor Saw Mill SHS | our doc: dropped shared file; consnh | 2 | to check state layer | 8 | Oct 29 |
| US-8024 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-8024 | Taylor Saw Mill State Historic Site | look-up 9-p2-nh (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): 150400701 ? ac [Recreation Inventory: Areas]; Ballard State Forest ? ac [CL: Solid]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-13626 | Sugar River State Trail | new park (POTA, found 2026-10-28); pin 43.3667, -72.1791 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-10-28 |
| US-13625 | Ammonoosuc State Trail | new park (POTA, found 2026-10-28); pin 44.2128, -71.9098 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-10-28 |
