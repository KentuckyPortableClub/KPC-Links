# Research input format (problem solver research inbox)

the owner, Nov 9 2026, 6:25 PM CST: "if the problem solver couldn't handle all that research documents you need to fix the
problem solver and design a format for a file it could read". Retry loop: the owner YES.

## Where files go
Drop a file in `data/research-inbox/` (CSV or JSON). The checker is `.github/scripts/kpc_research_inbox.py`; the problem solver runs it
with `python3 .github/scripts/kpc_problem_solver.py --inbox`. It checks **only the parks in the file**. It never rebuilds a key, never
writes an override, and never moves a POTA pin.

Files filed under `data/research-inbox/answers/` (any sub-folder) follow one rule (Nov 12): a CSV with a `pota_ref` column, or JSON rows with
`pota_ref`, is a batch and is checked like a file in the top folder (its results are `results/answers-<folders>-<name>.json`). Every other file
there (answers and list files with a `ref` column, the solved ledger, the Japan crosswalk, source lists, notes) is not a batch: each run prints
`not a batch: <file>: <reason>` and writes the list to `results/not-batches.md`, so nothing under `answers/` is skipped in silence.

## Columns (one row per park and candidate)
| column | needed | what it is | from the owner xlsx |
|---|---|---|---|
| pota_ref | yes | the POTA park, e.g. `US-3722` | pota_ref |
| park_name | yes | the POTA name | park_name |
| layer_url | yes* | the ArcGIS REST layer, ending in `/MapServer/<n>` or `/FeatureServer/<n>` | FOUND_layer_or_service_url (US/CA) or FOUND_source_url_or_layer (world) |
| record_id | yes* | the record the research found (OBJECTID or the source's own id) | FOUND_record_id |
| official_name | no | the source or record name the research read | FOUND_source_name |
| owner | no | owning or managing agency | owner_agency |
| confidence | no | the source's own confidence: high / med / low / held | confidence(high/med/low) |
| notes | no | free text (points, parcels, overlays are read by a person, not trusted) | notes |
| source | no | who made the row and when, e.g. `the owner no-ID file, Nov 9 2026` | (set by the converter) |
| pin_lat, pin_lon | no | only a fallback when KPC-Data parkinfo has no pin; never written anywhere | pota_pin_lat, pota_pin_lon |

\* A row with no layer or record id is kept as "back to Research".

Example (CSV):

```
pota_ref,park_name,layer_url,record_id,official_name,owner,confidence,notes,source,pin_lat,pin_lon
US-3722,New Echota State Historic Site,https://services6.arcgis.com/9QlSLDqa0P1cHLhu/ArcGIS/rest/services/State_Parks_Boundary/FeatureServer/0,44,New Echtoa Historic Site,Georgia DNR,high,"typo in the record name, pin 6 m",the owner recheck,,
CA-0123,Example Provincial Park,https://ws.lioservices.lrc.gov.on.ca/arcgis1071a/rest/services/LIO_OPEN_DATA/LIO_Open06/MapServer/5,812,EXAMPLE PP,Ontario MNRF,med,,Research Nov 10,,
```

JSON is the same rows: `{"rows": [{"pota_ref": "...", "park_name": "...", ...}]}`.

## What the checker does with each row (the  sure test)
1. Saved outline first (`cache/research/`), else an **allowed** live read: robots.txt checked per host (a 401/403 answer = disallow),
   hosts on `KPC_SAVED_ONLY_HOSTS` never read live, never the Grant County NM parcel server or ncnhde.natureserve.org,
   one request per host per second. Each live read is saved.
2. It reads the polygons within 0.6 km of the POTA pin on that layer and keeps one whose name fits.
3. **SURE** only if: polygon (not a point or line), pin inside or within 0.5 km, name fits (a one-letter typo or the agency's own
   name with the park's number counts), the kind of place does not clash, not an overlay (Natura 2000 / Ramsar / SSSI / UNESCO ...)
   unless the park's name says so, no person said no / none, the id is not on `blocked_ids`, and the park has no saved id yet.
4. **POINT-CONFIRMED**: no polygon fits, but a POINT record with the park's name lies within
   0.5 km of the pin. That confirms the park exists. It is never used as an outline (kept out of the keys and the 2-fers) and is
   listed separately (`point_confirmed` in needs-another-look.json) to review later for a boundary.
5. Otherwise **NEEDS PERSON** (with the reason) or **REJECTED** (with the reason).
6. **Earlier NO**: a person's earlier NO (`none: true`, a `no` record, the bad-ID block list) does not stop the test.
   A SURE (or point) match over it is **SOLUTION FOUND vs earlier NO**: never signed, it goes on the owner short list with the
   evidence and the earlier decision and its date. Otherwise the earlier NO stays.
7. Simple name helps: accents are folded and French generic words (Parc, Réserve nationale de faune, Aire protégée ...) are ignored,
   and every name field on the record counts (CPCAD NAME_E / NAME_F), so French/English names of one Canadian park match.
   An agency's other name that is not that (rule 8) and a layer with no names (pin inside the named record only) go to a person.
8. Point-circle parks: the 2-fer finder draws a 100 ft circle around the official point, and every card says
   "No official boundary on file. Using a 100 ft circle around the agency's official point (...). The real boundary may be larger,
   so check before you activate.".

the owner one short list: `data/research-inbox/brandon-list.md` (built each run).

Results: `data/research-inbox/results/<file>.json` and `.md`. SURE rows go to Quality, then are signed only under the owner rule.

## Retry loop
`data/research-inbox/needs-another-look.json` lists every park the checker could not settle (and any park Quality denies or holds:
add it with `status: needs another look` and the reason). Each entry says what it waits on: `hand-download`, `layer`, `research`
or `person`. When a layer is added or a hand download lands, run `--retry`: only those parks are checked again. A park that becomes
SURE goes to Quality; one still stuck stays on the owner short list with its reason.

## Converter
`python3 .github/scripts/kpc_research_from_xlsx.py <book.xlsx> <out.csv> --sheets US,Canada --source "..."` turns the owner no-ID
workbooks (and the "KPC held (19)" sheet style) into this format. First real input: `data/research-inbox/nov9-brandon-no-id-*.csv`.

## Answers and solved ledger (Nov 11 2026)
`data/research-inbox/answers/` holds the Nov 5 and Nov 11 mystery-park answers, the prepared lists, the sources ledger, the settled negatives and
`solved-ledger.csv` (one row per park; read `answers/README.md` first). It is a sub-folder on purpose: the checker reads only the batches straight in
`data/research-inbox/` (`inbox_files()`), so nothing under `answers/` or `results/` is ever treated as a batch.

A solved park (`released-key`, `settled-match`, `settled-no-boundary`: `classify_solved` in `kpc_research_inbox.py`) is finished research and is never on a search list
(`answers/search-list.csv`). If it has no owner decision pending it is also not read, not judged and not handed out again: the run reports it as `SOLVED` with its
official id, drops it from the retry list and leaves it off `brandon-list.md`. A solved match that still waits on an owner yes (`owner_decision` = pending: a
National Register listing boundary still held) is not re-researched but stays on the retry list and the short list with its hold intact.
The 56 Nov 5 confirms were settled (`owner_decision` = yes) on 2026-11-11. US-10274 and FR-14979 are owner no (not a match) and stay open, as do
`other`, `wrong pin`, blank, and a match that rested only on a removed WDPA lead (ZA-0085, ZA-0156, ZA-0157 stay unsolved).
Rebuild both files after new answers are filed: `python3 tools/kpc_build_solved_ledger.py ledger data/research-inbox/answers`.

WDPA / Protected Planet is a lead only. No id or address of it may sit in a tracked file; a run also scrubs any such id or address from what it writes.
`tests/test_solved_ledger_nov11.py` fails if one comes back.
