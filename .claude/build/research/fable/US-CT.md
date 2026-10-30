# Fable book: US-CT (16 rows, 4 parks)
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-CT.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-6860 | Ferry Landing SP | our doc: depdata.ct.gov parks map (statewide, does not name park) | 3 | pin until DEEP park map seen | 8 | Oct 29 |
| US-6860 | Ferry Landing SP | Oct 30 chat 8: no point-in-polygon hit at all (checked earlier this week). **Confirmed no-layer, stays a pin.** | 8 | Oct 30 |
| US-6860 | | PAD-US at pin: Marine District Headquarters (SOTH, owner OTHS/STAT, manager UNK, 7 ac, Fee, PAD id 51673) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6860 | Ferry Landing State Park | look-up 9-p2-ct (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [Protected Open Space View]; Roger Tory Peterson WMA 625 ac [Areas Open for Hunting]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6875 | The Preserve (Essex Land Trust) | our doc: DEEP page, no map; land trust owns | 3 -> 4b | land-trust parcel; take-back candidate | 8 | Oct 29 |
| US-6875 | The Preserve (Essex Land Trust) | Oct 30 chat 8: my Oct 29 land-trust note was wrong -- "Preserve State Forest" (889 ac, DEEP) is the same proper word ("Preserve") under DEEP ownership, not a land trust. **TRACE candidate.** | 8 | Oct 30 |
| US-6875 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6875 | The Preserve Essex Land Trust State Park Preserve | look-up 9-p2-ct (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [Protected Open Space View];  889 ac [DEEP Property]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-7529 | Beckley Iron Furnace SP | our doc: DEEP page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-7529 | Beckley Iron Furnace SP | Oct 30 chat 8: this park's REAL official name is "Beckley Furnace Industrial Monument" (ctparks.com / portal.ct.gov/DEEP confirmed) -- our point-in-polygon hit "[DEEP] Industrial Monument Historic Preserve" (2.9 ac) is the SAME proper designation, T-1 match. **TRACE candidate.** | 8 | Oct 30 |
| US-7529 | | PAD-US at pin: Industrial Monument Historic Preserve (SOTH, owner OTHS/STAT, manager UNK, 1 ac, Fee, PAD id 51664) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-7529 | Beckley Iron Furnace State Park | look-up 9-p2-ct (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Housatonic State Forest ? ac [Protected Open Space View]; Industrial Monument Historic Preserve ? ac [Protected Open Space View]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-7542 | Satan's Kingdom SRA | our doc: no map on DEEP page | 3 | pin (no source yet) | 8 | Oct 29 |
| US-7542 | Satan's Kingdom SRA | Oct 30 chat 8: the point-in-polygon hit "Farmington River Water Access" (12.3 ac) shares NO proper word with "Satan's Kingdom" -- it's a nearby access point on the same river, not this park, per T-1. **Confirmed no-layer, stays a pin.** | 8 | Oct 30 |
| US-7542 | | PAD-US at pin: Farmington River Water Access (SREC, owner SFW/STAT, manager UNK, 8 ac, Fee, PAD id 57476) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-7542 | Satan's Kingdom State Recreation Area | look-up 9-p2-ct (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Nepaug State Forest ? ac [Protected Open Space View]; Nepaug State Forest 1364 ac [Areas Open for Hunting]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
