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
| US-13651 | Zim Wildlife Management Area | new park (POTA, found 2026-11-03); pin 47.2157, -92.6024 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13650 | Darwin S. Meyers Wildlife Management Area | new park (POTA, found 2026-11-03); pin 47.6364, -92.2233 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13649 | Old Koschak Farm Wildlife Management Area | new park (POTA, found 2026-11-03); pin 47.9224, -91.8297 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13648 | Altona Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.1954, -96.3255 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13647 | Badger Lake Wildlife Management Area | new park (POTA, found 2026-11-03); pin 43.9228, -95.7295 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13646 | Bohemian Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.6337, -96.4067 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13645 | Budolfson Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.0445, -95.4761 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13644 | Cedar Rock Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.6084, -95.1649 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13643 | Coon Creek Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.3361, -96.0402 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13642 | Fenmont Wildlife Management Area | new park (POTA, found 2026-11-03); pin 43.8475, -95.8295 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13641 | Green Valley Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.5043, -95.6988 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13640 | Hole-In-Mountain Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.2256, -96.3167 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13639 | Hopeful Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.2557, -96.0983 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13638 | Lake Maria Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.1721, -95.8155 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13637 | Lamberton Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.2521, -95.22 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13636 | Lyons Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.2812, -95.8878 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13635 | Phyllis Voosen Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.4953, -95.4642 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13634 | Sodus Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.2801, -95.8394 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13633 | Talcot Lake Wildlife Management Area | new park (POTA, found 2026-11-03); pin 43.8942, -95.4529 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13632 | Two Rivers Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.2796, -95.3845 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
| US-13631 | Winter Wildlife Management Area | new park (POTA, found 2026-11-03); pin 44.1451, -96.384 | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | 2026-11-03 |
