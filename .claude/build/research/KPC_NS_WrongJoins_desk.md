# Nova Scotia "same land" wrong joins: SOLVED (chat 8, Oct 29 ~12:05 PM)
Grade A: I read `ca-key/CA-NS.json`, `fers/CA-NS.json` and POTA pins in `canada.json` and counted every row.

## The cause (Canada's own, not the US multipart bug)
The Nova Scotia provincial outlines are named in the key by a **short label: "Nova Scotia :34"** = first words of the layer name + the record number. Nova Scotia has TWO provincial layers whose names start the same ("Nova Scotia protected areas (NS Environment)" and "Nova Scotia parks and protected areas"), so **record 34 in one layer and record 34 in the other get the same label**. The 2-fer line says "both park numbers are joined to the same outline" when two parks list the same label, so any two parks that happen to hit the same record NUMBER in different layers look like "same land".

Proof, three rows:
| Pair | Pins | Shared label | What it really is |
|---|---|---|---|
| Cape Breton Highlands NP (CA-0013) + Lake Midway PP (CA-0922) | 486 km apart | `Nova Scotia :34` | #34 in the protected-areas layer is the NP; #34 in the parks layer is Lake Midway |
| Cape Smokey PP (CA-0456) + Bowers Meadows WA (CA-1734) | 515 km | `Nova Scotia :662` | #662 in "parks and protected areas" = Cape Smokey; #662 in "protected areas" = Bowers Meadows |
| Tusket River WA (CA-1900) + Mabou PP (CA-6600) | 423 km | label collision | same |
Others in the same list: Barrachois PP + Quinns Meadow NR (481), Petersfield PP + Sissiboo River WA (480), Cabots Landing PP + Lake Rossignol WA (466), The Islands PP + Middle River WA (445), Humes River WA + Roseway River WA (420), Jim Campbells Barren + Ponhook Lake NR (399), Bonnet Lake Barrens + Tiddville NR (391).

## Numbers
- 161 live 'same land' rows in CA-NS. **144 are this bug** (pins more than 30 km apart; every one shares an id label only, never the full key). 11 more share the label within 30 km. **6 are right.**
- 183 of 1,011 provincial labels in NS are reused by two layers. The same labels exist in other provinces: **NB 34 of 342, ON 8, MB 2, SK 2, AB 1, YT 1.** That is the whole NB (17) and MB (8) held list.
- CPCAD numbers (22138, 21986...) are not affected: they are numeric and unique in one database.

## Why it matters beyond 2-fers
The same label picks a park's OUTLINE. A park whose chosen record is a colliding label may have been given the OTHER layer's polygon. The outline join for any park with a `Nova Scotia :N` / `New Brunswick :N` label as its only/best match should be re-read. Quick test: its outline's centre must be within the pin's neighbourhood (pin inside or within 5 km); Cape Smokey would fail it by 515 km.

## Rule that separates them (R-CA1)
1. A provincial record's key = **layer id + record number** (full layer name or the layer's number), never the short label.
2. 'Same land, two park numbers' needs: same full key (or same CPCAD number) AND each pin inside or within 5 km of that outline AND the two pins within 30 km of each other. Anything failing the pin test is a wrong join, not a 2-fer.
3. Chat 2's pins-over-30-km check already caught 144 of them; keep it, it is the right safety net.

## Three NS pairs that must stay (real same land)
- Port L'Hebert PP (CA-0935) + Port L'Hebert Nature Reserve (CA-1824) (5 km; shared CPCAD numbers 22138/22139) and + Port Hebert MBS (CA-1822) (2 km).
- Shelburne Heritage River WA (CA-1843) + Shelburne River National Heritage River (CA-6136) (2 km).
- North River Protected Area (CA-0470) + North River Wilderness Area (CA-1809) (1 km), Chimney Corner PA (CA-0899) + Chimney Corner NR (CA-1741) (5 km), Chignecto NWA (CA-0016) + Amherst Point BS (CA-1718) (1 km).
(Tusket River WA CA-1900 + Tusket River Ecological Area CA-1901, 3 km, shares an id only: probably real; check once the key uses full keys. Ship Harbour Long Lake WA + White Lake WA, 10 km, shares only `Nova Scotia :217`: probably a collision too.)

## Fix, who
- Chat 2 (Canada key): build provincial record keys from the full layer name; rebuild NS, NB, ON, MB, SK, AB, YT; rerun the line for caatl; re-read outlines for parks whose join used a collided label.
- I regrade NS, NB and MB after the rerun.
