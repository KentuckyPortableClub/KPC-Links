# Fable book: US-NY (28 rows, 9 parks)
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-NY.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2001 | Adirondack Park | our doc: dec.ny.gov adkmaponly.pdf (the Blue Line map); DEC lands layers DECLANDS_ADK | 3 / GREY G-NY1 | see grey area | 8 | Oct 29 |
| US-2001 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-2001 | Adirondack State Park | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-2081 | Iona Island WMA | NY DEC layers: gisservices.dec.ny.gov dil_land_activities MapServer/2 "Wildlife Management Areas" and reference MapServer/2 "DEC Lands"; our doc: map page does not name park | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-2081 | Iona Island Wildlife Management Area | potamap lead (its PAD-US copy holds the pin): 'Iona Island State Park' owner SPR / manager SPR | R-G2 / R-G8 | R-G8: another kind of place (state PARK vs WMA): CHECK | 2 | Oct 29 |
| US-2081 | | PAD-US at pin: Bear Mountain State Park (SP, owner SPR/STAT, manager SPR, 5477 ac, Fee, PAD id 237450) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-2081 | Iona Island Wildlife Management Area | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Bear Mountain 5228 ac [NYS_Park_Polygon]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-2081 Iona Island | NO | WMA vs state park are different designations |
| US-2151 | Thompsons Lake SP | our doc: no map; OPRHP park (parks.ny.gov); state park boundary layer not yet found (only OPRHP regions) | 2 | pin (no source yet) | 8 | Oct 29 |
| US-2151 | | PAD-US at pin: John Boyd Thacher State Park (SP, owner SPR/STAT, manager SPR, 2477 ac, Fee, PAD id 237529) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-2151 | Thompsons Lake State Park | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): John Boyd Thacher 228 ac [NYS_Park_Polygon]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-8070 | Catskill Park | our doc: no working map; DEC Lands layer | 3 / GREY G-NY1 | see grey area | 8 | Oct 29 |
| US-8070 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-8070 | Catskill State Park | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-8082 | Jamaica Bay "State" Wildlife Area | our doc: nps.gov/gate maps page (Gateway NRA is NPS land, not state); NPS boundary | 3 -> 4b | NPS land: use NPS Gateway boundary | 8 | Oct 29 |
| US-8082 | | PAD-US at pin: Gateway National Recreation Area (NRA, owner NPS/FED, manager NPS, 18548 ac, Fee, PAD id 3501) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-8082 | Jamaica Bay State Wildlife Area | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-8084 | Breezy Point Tip "State" Rec Area | our doc: same NPS Gateway maps page | 3 -> 4b | NPS land | 8 | Oct 29 |
| US-8084 | | PAD-US at pin: Gateway National Recreation Area (NRA, owner NPS/FED, manager NPS, 18548 ac, Fee, PAD id 3501) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-8084 | Breezy Point Tip State Recreation Area | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-8088 | Miller Field "State" Rec Area | our doc: same NPS Gateway maps page | 3 -> 4b | NPS land | 8 | Oct 29 |
| US-8088 | | PAD-US at pin: Gateway National Recreation Area (NRA, owner NPS/FED, manager NPS, 18548 ac, Fee, PAD id 3501) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-8088 | Miller Field State Recreation Area | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-8103 | Cayuga Lake WMA | our parkinfo: POTA link = dec.ny.gov cayugamap.pdf (own map); DEC WMA layer | 3 (map found) / 2 | to trace | 8 | Oct 29 |
| US-8103 | Cayuga Lake WMA | the map found in the row above | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-8103 | Cayuga Lake Wildlife Management Area | potamap lead (its PAD-US copy holds the pin): 'Cayuga-Seneca Canal' owner OTHS / manager OTHS | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-8103 | | PAD-US at pin: Cayuga-Seneca Canal (SREC, owner OTHS/STAT, manager OTHS, 1234 ac, Fee, PAD id 232523) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-8103 | Cayuga Lake Wildlife Management Area | look-up 9-p2-ny (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): MONTEZUMA NATIONAL WILDLIFE REFUGE 23517 ac [FWSApproved];  1 ac [NYS DEC Lands]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
