# Fable book: US-HI (6 rows, 4 parks)
HANDOFF (chat 3, Oct 30): Fable work moves to CHAT 8. Artillery District (US-10923): P-2 no polygon at pin; NRHP 64000142 record + map found; WAITING NRHP map read / parcel. Address/GPS table in the desk file.
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-HI.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-10923 | | PAD-US at pin: Fort De Russy (MIL, owner DESG/DESG, manager DOD, 73 ac, Proclamation, PAD id 288) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10923 | Artillery District of Honolulu Historic Site | look-up 9-p2-hi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-10923 HI | Artillery District of Honolulu Historic Site | https://npgallery.nps.gov/AssetDetail/NRIS/64000142 | to read | to read | 21.279, -157.834 |
| US-10925 | | PAD-US at pin: Kaala Natural Area Reserve (SCA, owner SDNR/STAT, manager SDNR, 1087 ac, Fee, PAD id 195288) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10925 | HI State Game Reserve | look-up 9-p2-hi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): KAALA NATURAL AREA RESERVE 1086 ac [Reserves] *name. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-10925 HI | HI State Game Reserve | https://dlnr.hawaii.gov/forestry/frs/reserves/oahu/ | to read | to read | 21.5168, -158.144 |

Chat 8 (Oct 30): **US-10923 Artillery District of Honolulu**: look-up read the NRHP record (64000142) -- it's a Thematic Resource nomination (multiple scattered artillery batteries across Honolulu, not one contiguous site), PDF only, no live GIS. no-layer, pin stays; the NRHP PDF link kept for reference, not traced (G-ID3 would apply anyway if it held a sketch map, and a TR likely covers several non-contiguous sites so a single boundary wouldn't fit it regardless). **US-10925 HI State Game Reserve**: the dlnr.hawaii.gov URL is dead (404); no shared proper word with the Kaala NAR hit either way. The park's own name reads as a generic category label rather than a specific site name, which is unusual -- flagging for chat 2 to double check POTA's own park detail page for this one rather than treating the *name flag as real. no-layer, pin stays for now. **STATE HI DONE** (2/2).

