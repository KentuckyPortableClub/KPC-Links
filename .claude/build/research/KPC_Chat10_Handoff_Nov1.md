# Chat 10 (bot builder) hand-off, Nov 1 2026 12:40 PM CST

First read this note, then run `python3 .claude/build/inbox_now.py 10`. Everything below is in KPC-Data unless it says KPC-Links.

## Running by itself now (check the status board first: data/status/board.json)

**Park-info engine v0.4.1**
- **Code:** `.github/scripts/draft/tools/kpc_engine/`; the big registry files are on branch `engine-registry`.
- **Workflow:** `kpc-engine.yml`, every 3 h until about Nov 2 10 UTC, then nightly at 04:07 UTC.
- **Areas:** all ~300, Kentucky first. Steering: issues labelled `engine-steer`.
- **Results:** tools-out `engine/`, plus its hand-back on intake-files (`*-engine.*`), which the readers take to the waiting room.
- **Fixed today:** tools-out saves now retry; the engine is given the full area list.
- **Check:** the board shows parks > 0, and runs move past Kentucky.

**Hard look reader** (`kpc-hardlook.yml` / `kpc_hardlook.py`)
- Every hardlook-* file → `data/waiting/questions/hardlook.json` + `pin-typos.json`. 5,534 rows read.

**Intake reader kinds**
- camping, parking, docs (+ docs-pagefix csv), convert, layers, questions, hours, acres, portals, hardlook (xlsx too).

**Tool trial** (`kpc-tool-trial.yml`: weekly Sun 05:37 UTC, or by hand)
- Tools: sitemaps, parcels, inspire, audit, watch, sameland, missedfers, pulloffs, acres, trace. The tracer = 769 Hard Look parcel parks.

**Other new bots**

| Bot | Schedule / note |
|---|---|
| picture tracer (`kpc-picture-trace.yml`) | weekly; its input was fixed today |
| camp layers | weekly, Sat |
| GPS packs (branch gps-packs) | nightly |
| cell coverage (`kpc-cell.yml`) | monthly |
| collector + GIS finders (portals) | every 2 h |

**Waiting room**
- `grade-queue.md` lists only new / changed rows.
- Trusted kinds: 3 chat-11 YES in a row = the bot releases itself, with a 1-in-10 sample.
- G-4 applies to keys + 2-fers only.
- The verdict is read from its first words.
- GENS = 1.

## Waiting on others

**Chat 11**
- The KEY YES on the Nov 1 US + CA key build: 320 YES parks wait for it.
- Grading: engine, hard look, picture tracer and tool outputs.

**Chat 2**
- data/fers storage: gzip the area files; move expected-* / review-all to fers-storage.
- The G-4 lines.
- The T7 / T8 compare.

**Chat 8:** Pennyrile.

**Brandon:** two trail asks (see the last section).

## Next for chat 10

1. **STORAGE STEP 2** (Brandon GO; HQ item of Nov 1 12:10 PM). Earliest: Mon Nov 2 evening, after step 1 has been green for a day.
   1. Make the backup: `git bundle create`, attach it to a GitHub release, run `git bundle verify`.
   2. Disable every scheduled workflow, and list them in the report.
   3. Make an orphan commit of today's files and force-push it to main.
   4. Re-enable the workflows and run the waiting room + the collector once.
   5. HQ tells every chat to take a fresh clone.

   Report the before / after sizes: 640 MB now.
2. **New-refs posting** (chat 5's Nov 1 12:50 AM item): a to_post list; post only when the ref is in the live list; a DRY proving run first.
3. **Engine switch-over,** each kind after chat 11 passes it, in this order: docs → parking → camping → outlines (after Nov 6) → KY hours / closures last.
4. **Nightly world + Canada + KY key rebuilds** from a touched.json (KPC-Links `KPC_10_Next3_Specs.md` part 3), after the Nov 1-3 monthly runs.
5. **Two smaller jobs:**
   - Retire HQ's stop-gap `kpc-outside-tools.yml`.
   - Feed the hours / fees workbooks + the blocked rows into the outside-KY trial. The trial ends Nov 7; report to chat 11.

## Rulings made Oct 31 - Nov 1 (in notes/mapping.md + RULES-NOW)

- **R-G12:** a pin within 150 m of a named official record = a candidate.
- **R-G13:** a POTA pin typo confirmed by an official point = use the outline. The pin never moves; the typo is listed.
- **W-10:** WDPA is a last-resort APPROXIMATE source: no stored shapes, no downloads, credit shown.

**Still open for Brandon:**
- A named trail piece, tied to the trail by a system / route field or by the agency's page.
- KyGovMaps trail lines, allowed when the managing agency publishes none.
