# Fable book: US-TX (34 rows, 23 parks)
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-TX.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-10272 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10272 | Bush Family Home State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 7 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-10272 Bush Family Home | 1412 W Ohio Ave, Midland, TX 79701 | Midland | needs-parcel |
| US-10272, 10273, 10274, 10275, 10276, 12109, 6538, 6560, 6582, 6601, 6602 | Bush Family Home / Goodnight Ranch / Palmito Ranch Battlefield / Presidio la Bahia / Star of the Republic Museum / Stephen F. Austin Memorial / Barrington Plantation / French Legation / Mission Dolores / Sam Rayburn House / San Felipe de Austin State Historic Sites | THC page per site (thc.texas.gov/historic-sites/...); Star of the Republic + Barrington sit inside Washington-on-the-Brazos SHS (another record: never their outline, R-G8) | R-G7 step 3 (THC / Texas open-data state-lands layer) -> 4b (THC-owned parcel) | pages queued (3-fable-tx) | chat 3 | Oct 29 |
| US-10273 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10273 | Charles and Mary Ann Goodnight Ranch State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 7 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-10273 Goodnight Ranch | none printed | Armstrong | needs-parcel |
| US-10274 | | PAD-US at pin: Lower Rio Grande Valley National Wildlif (NWR, owner FWS/FED, manager FWS, 88266 ac, Fee, PAD id 4060); Lower Rio Grande Valley National Wildlif (NWR, owner FWS/FED, manager FWS, 89898 ac, Fee, PAD id 5015) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10274 | Palmito Ranch Battlefield State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): 0125 430 ac [Public_ConservationLands]; SOUTH TEXAS REFUGES COMPLEX 3008161 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-10274 Palmito Ranch Battlefield | 43296 Palmito Hill Rd, Brownsville, TX 78521 | Cameron | needs-parcel |
| US-10275 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10275 | Presidio la Bahia State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Goliad ? ac [Park Boundary]; ARANSAS/MATAGORDA ISLAND NATIONAL WILDLIFE RE 2306831 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-10275 Presidio la Bahia | none printed | Goliad | needs-parcel |
| US-10276 | | PAD-US at pin: Washington-on-the-Brazos State Historic  (SHCA, owner OTHS/STAT, manager OTHS, 295 ac, Fee, PAD id 261746) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10276 | Star of the Republic Museum State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): 0310 295 ac [Public_ConservationLands]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-10276 Star of the Republic Museum | 23400 Park Rd 12, Washington, TX 77880 (sits inside the Washington-on-the-Brazos site: that shape is never its outline, R-G8) | Washington | needs-parcel |
| US-12109 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12109 | Stephen F. Austin Memorial Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): TEXAS MIDCOAST REFUGES COMPLEX 2056561 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12109 Stephen F. Austin Memorial | 900 Oil Field Rd, West Columbia, TX 77486 | Brazoria | needs-parcel |
| US-6538 | | PAD-US at pin: Washington-on-the-Brazos State Historic  (SHCA, owner OTHS/STAT, manager OTHS, 295 ac, Fee, PAD id 261746) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6538 | Barrington Plantation State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): 0310 295 ac [Public_ConservationLands]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6538 Barrington Plantation | 23100 Barrington Ln, Washington, TX 77880 (same inside-Washington-on-the-Brazos note) | Washington | needs-parcel |
| US-6560 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6560 | French Legation State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 7 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6560 French Legation | 802 San Marcos St, Austin, TX 78702 | Travis | needs-parcel |
| US-6582 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6582 | Mission Dolores State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 7 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6582 Mission Dolores | 701 S Broadway St, San Augustine, TX 75972 | San Augustine | needs-parcel |
| US-6601 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6601 | Sam Rayburn House State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 7 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6601 Sam Rayburn House | 890 W State Hwy 56, Bonham, TX 75418 | Fannin | needs-parcel |
| US-6602 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6602 | San Felipe de Austin State Historic Site | look-up 9-p2-tx (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 7 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6602 San Felipe de Austin | none printed | Austin | needs-parcel |
