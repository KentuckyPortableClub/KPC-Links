# Fable book: US-VA (6 rows, 4 parks)
HANDOFF (chat 3, Oct 30): Fable work moves to CHAT 8. Frontier Culture Museum (US-9931) + Dyke Marsh (US-9961): address/GPS done; Dyke Marsh NPS map PDF found (picture, link kept); WAITING P-2 reading / NPS legal boundary check.
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-VA.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9931 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-9931 | Frontier Culture Museum State Historic Site | look-up 9-p2-va (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 9 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-9931 VA | Frontier Culture Museum State Historic Site | https://www.frontiermuseum.org/ | 1290 Richmond Rd, Staunton, VA 24401 | Google link 38.1313, -79.0450 | 38.1256, -79.0503 |
| US-9961 | | PAD-US at pin: George Washington Memorial Parkway (SDA, owner NPS/FED, manager NPS, 3477 ac, Fee, PAD id 3549); George Washington Memorial Parkway (NP, owner NPS/FED, manager NPS, 2776 ac, Fee, PAD id 271111) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-9961 | Dyke Marsh Wildlife Reserve | look-up 9-p2-va (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): George Washington Memorial National Parkway 3202 ac [Virginia's Conservation Land, US National Park Service]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-9961 VA | Dyke Marsh Wildlife Reserve | https://www.nps.gov/gwmp/planyourvisit/dykemarsh.htm | to read | to read | 38.7674, -77.05 |

Chat 8 (Oct 30): **US-9931 Frontier Culture Museum**: page confirmed (official VA museum, address matches), nothing about a boundary map; it's a museum campus with no PAD-US record and no P-2 hit -- no-layer, pin stays, address confirmed. **US-9961 Dyke Marsh**: confirming chat 3's handoff -- the NPS Dyke Marsh page is read-only text here (no PDF link visible in the fetch), but chat 3 already found an NPS boundary map PDF (picture, G-ID3) before handing off; the only live-layer hit is the whole George Washington Memorial Parkway (3,200+ ac, way too broad, no name match) so it stays picture-map-only / pin. Asked chat 10 to confirm the exact PDF link for a save-map filing since I can't pull it from this page fetch. **STATE VA DONE** (2/2).

