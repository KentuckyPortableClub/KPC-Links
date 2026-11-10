# Amendment 2 (Nov 9 2026): for Quality to grade

Branch `prep/nov9-amendment2` (fresh from main after Links #104 / Data #57). The owner merges (squash). Nothing here signs a park by itself.

## What changed (KISS)
1. **The 19 held parks**: 18 signed (owner decisions, evidence in `data/us-key/overrides.json`); US-12471 Lone Rock still held.
2. **Saved-copy hosts**: services.arcgis.com, services1.arcgis.com, apps.fs.usda.gov are never read live; the key builds use the saved outlines.
3. **World overrides keep exact IDs** (`ids` in world overrides).
4. **Research inbox**: `data/research-inbox/*.csv|json` -> `kpc_research_inbox.py` runs ONE sure test on just those parks; results in `data/research-inbox/results/`, retry list `needs-another-look.json`. Format: `docs/research-input-format.md`. Converter: `kpc_research_from_xlsx.py` (Nov 9 workbooks and the "Solved cases" sheet).
5. **One sure test** = polygon, pin inside or within 0.5 km (hard cap: a pin over 0.5 km, or with no distance, is never SURE), the SAME core name (accents folded, generic words dropped; every name field counts, so French/English NAME_E/NAME_F match), no kind clash, not a piece, not an overlay. An extra distinctive word on one side (Deep Closure, Buckhorn Unit, North/Lower) is a person's call.
6. **WDPA / Protected Planet is never SURE.** A WDPA match is a lead: the solver looks for the same park (name, WDPA designation/agency) on the country's official layer(s) on file (`data/world-key/extra-layers.json`, `sheet-countries.json`) and runs the same sure test there. A sure match on the official layer is SURE with the official record; otherwise NEEDS PERSON with a named next step (download the official layer, or a person compares). This is a standing step in the solver.
7. **Earlier NO**: it does not stop the test; a sure match over it is `SOLUTION FOUND vs earlier NO`, never signed, on the owner's list.
8. **Point circles**: a park with only an official point gets a 100 ft circle around that point (`data/point-circles.json`, 27 parks), used only as the labelled `point-circle` 2-fer tier. Every user card says: "No official boundary on file. Using a 100 ft circle around the agency's official point (record, layer, id). The real boundary may be larger, so check before you activate." Cards: overlap finder, park popup, overlap popup, GPX/KML export, Tool Box US planner, Activation Kit, Access Finder, GPS file pin text, mapping-rep checklist. Tests: `tests/test_point_circle_notes.py`.
9. **CA-0037** Îles de l'Estuaire = Estuary Islands NWA (owner YES, `data/ca-key/overrides.json`).
10. **Cache tags**: every changed page script now loads with `?v=20261109am2` (root pages and `.claude/build/*/main.html`); version-tag tests updated.

## The owner's one short list
`data/research-inbox/brandon-list.md` (solutions over an earlier NO + agency-alias names). YES to flip, or NO.

## Rule hashes (approved Nov 9 2026, 7:52 PM CST; recorded in docs/key-rules-change.txt)
| key | main | this branch |
|---|---|---|
| us-key | 19d219f37114 | f489a836894f |
| ca-key | 22f16bc69b96 | 570b09c3cb52 |
| world-key | 10e4092cc97f | 6444287722b9 |
| fers | eb92de7a5f65 | 3dde681f1427 |

The pin cap, WDPA lead step, cache tags and text cleanup do not touch rule files; the four hashes are unchanged.

## Research runs (saved copies first, allowed live reads only)
| file | rows | SURE | SOLUTION vs earlier NO | POINT | NEEDS PERSON | REJECTED |
|---|---|---|---|---|---|---|
| Nov 9 US/CA no-ID | 1691 | 31 | 11 | 27 | 1503 | 119 |
| Denied/held (Solved cases) | 964 | 45 | 6 | 2 | 793 | 118 |
| Nov 9 world high/med | 1632 | 7 | 0 | 0 | 1611 | 14 |

World SURE went 307 -> 7: the WDPA rows and the four pins over 0.5 km (JP-1221 0.58 km, JP-1459 0.561 km, AE-0113 0.55 km, MX-0525 0.519 km) are no longer sure.

WDPA leads (298 world rows): **2 SURE through the official layer** (AE-0039 Saadiyat Marine NP, Abu Dhabi SDI; BE-0465 Champelle et Poilvache, Wallonie). **190 need a download** (no official layer on file: JP 186, CO 1, FI 1, FR 1, IT 1). **106 have an official layer that gave no sure match** (MX 23, GB 19, MK 18, AU 16, AE 7, PE 5, ID 4, NZ 4, NC 3, GU 2, DO 1, LK 1, NI 1, RW 1, VI 1): a person compares, or a fuller official layer is downloaded. Per-park list: `world-official-layers-needed.csv` (outbox).

Denied/held NEEDS PERSON reasons: no outline found 365; no same-name polygon within 0.5 km 282; robots-disallowed layer 98 (Yukon); no POTA pin 17; agency alias 15 (owner list); unreadable/saved-only layer 9; kind clash 7. The file's verdict column was not trusted.

Bilingual rule: exactly **1** park moves to sure because of French/English names: **CA-0037**.

## Hand downloads
`hand-downloads-amendment2.csv` (outbox): 145 layers, 1,045 parks (Vicmap WFS, Naturbase, Ontario forest blocks, Parks Canada NHS view, Paris espaces verts, England historic parklands, Yukon layers, robots-disallowed). World official layers needed: `world-official-layers-needed.csv`.

## Gate
`kpc_full_suite.py` run at the PR head; log in the grade packet (`gate-<sha>.log`).
