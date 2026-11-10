# Amendment 2 (Nov 9 2026): for Quality to grade

Branch `prep/nov9-amendment2` (fresh from main after Links #104 / Data #57). Brandon merges. Nothing here signs a park by itself.

## What changed (KISS, t958u)
1. **The 19 held parks**: 18 signed (`decided_by: Brandon t927u+t938u`, evidence in `data/us-key/overrides.json`); US-12471 Lone Rock still held.
2. **Saved-copy hosts** (t939u, "4 saved copies"): services.arcgis.com, services1.arcgis.com, apps.fs.usda.gov are never read live; the key builds use the saved outlines.
3. **World overrides keep exact IDs** (`ids` in world overrides).
4. **Research inbox** (t943u/t942u): `data/research-inbox/*.csv|json` -> `kpc_research_inbox.py` runs ONE sure test on just those parks; results in `data/research-inbox/results/`, retry list `needs-another-look.json`. Format: `docs/research-input-format.md`. Converter: `kpc_research_from_xlsx.py` (Nov 9 workbooks and the t955u "Solved cases" sheet).
5. **One sure test** = polygon, pin inside or within 0.5 km, the SAME core name (accents folded, generic words dropped; every name field on the record counts, so French/English NAME_E/NAME_F match, t957u), no kind clash, not a piece, not an overlay. Tightened after the spot check below: an extra distinctive word on one side (Deep Closure, Buckhorn Unit, North/Lower) is a person's call.
6. **Earlier NO** (t956u): it does not stop the test; a sure match over it is `SOLUTION FOUND vs earlier NO`, never signed, on Brandon's list.
7. **Point circles** (t949u/t950u/t953u/t954u): a park with only an official point gets a 100 ft circle around that point (`data/point-circles.json`, 27 parks), used only as the labelled `point-circle` 2-fer tier. Every user card says: "No official boundary on file. Using a 100 ft circle around the agency's official point (record, layer, id). The real boundary may be larger, so check before you activate." Cards: overlap finder list card + badge, park popup, overlap popup, GPX/KML export; Tool Box US planner grade line; Activation Kit; Access Finder; GPS file pin text; mapping-rep checklist. Tests: `tests/test_point_circle_notes.py`.
8. **CA-0037** Îles de l'Estuaire = Estuary Islands NWA (Brandon t957u YES, `data/ca-key/overrides.json`).

## Brandon's one short list
`data/research-inbox/brandon-list.md` (solutions over an earlier NO + agency-alias names). Say YES to flip, or NO.

## Rule hashes: PENDING Brandon's OK by name
| key | main | this branch |
|---|---|---|
| us-key | 19d219f37114 | f489a836894f |
| ca-key | 22f16bc69b96 | 570b09c3cb52 |
| world-key | 10e4092cc97f | 6444287722b9 |
| fers | eb92de7a5f65 | 3dde681f1427 |

## Research runs (saved copies first, allowed live reads only)
| file | rows | SURE | SOLUTION vs earlier NO | POINT | NEEDS PERSON | REJECTED |
|---|---|---|---|---|---|---|
| Nov 9 US/CA no-ID | 1691 | 31 | 11 | 27 | 1503 | 119 |
| t955u denied/held (Solved cases) | 964 | 45 | 6 | 2 | 793 | 118 |
| Nov 9 world high/med | 1632 | 307 | 0 | 0 | 1311 | 14 |

t955u NEEDS PERSON reasons: no outline found by the research 365; no polygon with the same name within 0.5 km of the pin 282 (most of the file's "LIKELY" rows: the pin is km away); robots-disallowed layer 98 (Yukon 33 rows / 27+ campgrounds); no POTA pin 17; agency alias 15 (Brandon list); unreadable/saved-only layer 9; kind clash 7. REJECTED: 112 already have a saved ID since the merge, 5 layers give only points/lines. The file's verdict column was not trusted (its 126 SOLVED -> 38 SURE, 1 solution-vs-NO, 43 already saved, 44 a person's call).

Bilingual rule: exactly **1** park moves to sure because of French/English names: **CA-0037** (now Brandon's YES). Quebec and the other French-named rows are held for other reasons (no polygon at the pin, unreadable layers).

## Spot check (live, allowed hosts, full-detail geometry)
18 SURE rows sampled: 17 polygon + name + pin within 0.5 km confirmed; JP-1221 Ueno at 0.62 km on the full-detail line (edge case, check). An earlier sample found 4 bad loose-name matches (Funk Island Deep Closure, Siloam Springs Buckhorn Unit, Garrett Lake State Forest vs Fishing Lake, Aniakchak Preserve vs Wild & Scenic River); the test was tightened and all four are no longer sure.

## Hand downloads
`hand-downloads-amendment2.csv` (outbox): 145 layers, 1,045 parks; top: Vicmap WFS, Naturbase, Ontario forest blocks, Parks Canada NHS view, Paris espaces verts, England historic parklands, Yukon GY_ParksProtectedAreas/0 and GY_CultureHeritage/0 (robots-disallowed).
