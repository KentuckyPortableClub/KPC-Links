# KPC 8: the "NO RECHECKER", a build spec for an outside coding agent
The club's Fable reviews the code afterwards, and the club's bot chat wires it.

## Why
The club matches POTA parks to official map records: "this record on this agency layer IS this park". A checker (chat 11) answers
YES / NO / NOT SURE on each match, mostly by name, kind of place and acres, without looking at the map.

On Oct 31 the checker reread 22 of its NO answers properly, opening the record page and the map. 21 stayed NO and 1 was wrong:
"Chena Wayside" vs the record "Chena River State Recreation Site", 27 acres, Alaska State Parks, which went to NOT SURE.
About 1 NO in 20 is wrong. This tool finds that 1 in 20 automatically, across about 2,700 NO answers.

**The tool never changes an answer.** It writes questions for a person.

## Input (the files are in this package; in the club's repo they live in `data/waiting/questions/`)
Four question files, each `{"about", "built", "open", "questions": [ ... ]}`. Each question has:

| field | what it is |
|---|---|
| `ref` | POTA park number, e.g. US-10464 |
| `park` | the club's park name, which can be out of date |
| `area` | US-AK, CA-AB, ZA… |
| `kind` | the kind of place |
| `layer` | ArcGIS REST layer URL, `…/MapServer/N` or `…/FeatureServer/N` |
| `record` | the record's object id on that layer |
| `record_name`, `acres_approx` / `acres` | the record's name and size |
| `record_link`, `pota_link` | links to the record and to the POTA page |
| `answer` | YES / NO / NOT SURE / null, often followed by text |
| `checked_by`, `how` | who answered and why |

Only rows whose `answer` starts with `NO` are rechecked.

| file | NO answers |
|---|---|
| `gis-hunter.json` | 362 |
| `layers.json` | 157 |
| `key-pieces.json` | 63 |
| `world-finder.json` | 2,140 (a 300-row sample is in this package) |

Order: Kentucky first, then the rest of the US and Canada, then the world.

## What it does, per NO row (batch, resume)
1. **POTA's side.** Read `https://api.pota.app/park/<ref>` for the current name, pin (lat / lon), the website POTA lists, and the location. Cache it for 30 days. Read the `<title>` of that website when it opens, as an extra name.
2. **The record.** Query the layer by object id: `/query?objectIds=<id>&outFields=*&returnGeometry=true&outSR=4326&f=geojson`.
   - **The pin test:** is POTA's pin inside the polygon? If not, how far away is it, in metres, measured in a local metric projection? For line records, use 100 ft (30.48 m) of the line.
   - **The name test:** score the park's names (POTA's current name + the website title + the club's name) against EVERY text field of the record, not just the name field.
     - Normalise first: lower case, accents and punctuation removed, runs of initials joined, type words dropped (State Park, SP, SRA, SRS, WMA, NWR, NF, SF, Wayside, Recreation Site / Area, Natural Area, Preserve, …).
     - Then a token-set ratio, gated by how many of the park's own words appear, so "Lake" cannot match "Lake Cumberland". You built the same normaliser for the map-page link extractor; reuse it.
   - **The size test:** the record's acres (from the geometry, in an equal-area projection) vs the park's acres when the input row or POTA gives them.
   - **The kind test:** compare the record's own type field (if any) with the park's kind. WMA vs State Park, a whole lake vs a recreation area on it, and a whole canal vs one section are conflicts.
3. **The neighbours.** Query the same layer for records within 2 km of the pin (envelope query, `outFields=*`). Score them the same way. If one is clearly better (pin inside, name ≥ 0.90, sane size) and is not the record already answered, report it.
4. **The verdict:**
   - **LOOK AGAIN:** the pin is inside the record (or within 100 ft of a line record), AND the name scores ≥ 0.90, or it scores 0.75 to 0.90 with acres within 3× of the park's.
   - **BETTER RECORD:** a neighbour from step 3. Give its object id, name and acres.
   - **KEEP NO:** anything else. Every one of these keeps it NO:
     - the pin is outside and more than 2 km from the record;
     - the name scores under 0.75;
     - there is a kind conflict;
     - the size is off by more than 10×.
   - **CAN'T TELL:** the layer is down, the record is gone, or it has no geometry. Give the reason; the row is retried next run.
5. **Safety cap:** if more than 15% of a batch (one input file, or one area) comes out LOOK AGAIN, stop that batch and say "too loose: check the scoring". The real rate is about 5%.

## Output
- `no_recheck/<file>.json`: one record per NO row. Fields: `ref`, `layer`, `record`, `verdict`, `why` (one plain sentence), `pin_inside`, `pin_dist_m`, `name_score`, `best_field`, `best_text`, `size_ratio`, `kind_conflict`, `better` {id, name, acres, score, pin_inside}, `read_date`.
- `no_recheck/questions.json`: ONLY the LOOK AGAIN and BETTER RECORD rows. Use the same shape as the input questions, plus `old_answer`, `evidence` (one plain line) and `suggested_record`, with `answer: null`.
- `no_recheck/report.csv` + `summary.md`: verdict counts per file and area.

## Rules (the club's house rules)
- Official layers only: the ones in the input rows. Never OpenStreetMap, Google, AllTrails or Protected Planet shapes. No API keys.
- POTA's pins are never moved or "fixed": they are only compared.
- Polite:
  - at most 1 request per second per host;
  - a User-Agent naming the club (`KPC-no-recheck (https://github.com/KentuckyPortableClub)`);
  - back off on 429 / 5xx;
  - obey robots.txt for web pages.
- One failure never stops a batch: log it as CAN'T TELL and go on.
- It must run headless on GitHub Actions:
  - `--max-minutes 50`, then stop cleanly; `--resume` carries on, so no job passes 55 minutes;
  - exit 0 normally, 3 = "not finished, run again with --resume", 2 = bad input.

## Tech
Python 3.11+, requests, shapely ≥ 2, pyproj, rapidfuzz. One file, `kpc_no_recheck.py`.
- `--files gis-hunter.json layers.json …`
- `--areas US-KY …` (optional filter)
- `--limit`, `--resume`, `--out no_recheck`, `--max-minutes`, `--offline` (cache only).

## Test (put the results in TEST_REPORT.md)
1. **Unit tests** with made-up shapes, no network:
   - pin inside / outside / near a line;
   - initials joined;
   - "Lake" does not match "Lake Cumberland";
   - a kind conflict;
   - the 15% cap.
2. **The known flip:** US-10464 Chena Wayside (in `gis-hunter.json`) must come out LOOK AGAIN or BETTER RECORD.
3. **Real runs:**
   - every NO in `gis-hunter.json` + `key-pieces.json` for US-KY, US-TN and US-AK;
   - then `layers.json` for one Canadian province;
   - then the 300-row world sample.
   - Report the verdict counts. Expect roughly 3 to 8% LOOK AGAIN + BETTER RECORD; much more means the scoring is too loose.
4. Show 10 of the flagged rows with their evidence line, so a person can judge them.

## Deliver
`kpc_no_recheck.py`, `requirements.txt`, `tests/`, `README.md`, `TEST_REPORT.md` and the sample-run outputs. **Do not wire it into anything:** the club's bot chat does that after Fable's review.
