# Fable book: US-MN (6 rows, 4 parks)
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-MN.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-13546 | Twin Points Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13547 | Two Harbors Protected Area | our doc: DNR harbor page, no map; look-up blocked (403) | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13547 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-13547 | Two Harbors Protected Area | look-up 9-p2-mn (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 33855630 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-13548 | Knife River Marine Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13549 | McQuade Marine Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |

Chat 8 (Oct 30): look-up 8-mn-dnrunits queried MN DNR Management Units (layer 3, the statewide boundary layer) at all 4 pins (Twin Points, Two Harbors, Knife River, McQuade) -- zero features at any point, confirming none of these small-craft harbor/breakwater structures sit inside a DNR land-management polygon (no owner, no parcel). All 4 stay pins (why-not: no-layer, per R-G7 step 4b -- there is no land boundary to trace, these are water-edge structures, not parcels). **STATE MN DONE** (4/4 resolved).
