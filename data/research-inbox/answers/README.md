# Answers and solved ledger (Nov 11 2026)

Where the Nov 5 and Nov 11 mystery-park hand-backs are filed, so a solved park is not searched or handed out again. Read only: nothing here writes a key, an override, a pin, a 2-fer file or a workflow, and no rules hash reads these files. This folder is a sub-folder on purpose: the inbox checker reads only the batches straight in `data/research-inbox/`, never `answers/`.

## Start here

| File | What it is |
|---|---|
| `solved-ledger.csv` | One row per park (832). `solved` yes/no, why (`solved_basis`), `owner_decision`, `owner_answer` (the recorded owner-answer citation), `join_ready`, the official id for a join, the official point, how strong the match is. Built by `tools/kpc_build_solved_ledger.py ledger`. |
| `OWNER-ANSWERS-nov11.md` | The recorded owner answers of Nov 11, 2026, about 9:16 PM CT (America/Chicago). The owner accepted all 10 recommendations with the widget choice Yes, go with your answers. The source record in that file names the chat. |
| `OWNER-QUESTIONS.md` | The filed owner-question notes, now marked Answered, each citing the item in OWNER-ANSWERS-nov11.md. |
| `search-list.csv` | The parks that are NOT solved: what a search list may hand out. Rebuilt with the ledger. |
| `settled-negatives.json` / `.md` | Dead ends not to search again (and layers where a miss proves nothing). |
| `nov11/` | The Nov 11 answers (256 rows, official point columns kept) and the notes that explain them. |
| `nov5/` | The Nov 5 answers (832 rows), the held-for-owner extras (`held-for-brandon-nov5.csv`: intake flags and decided_by only), the Japan A10 crosswalk (47 parks still open; filed, no Japan join made), the Nov 5 hand-off notes. |
| `lists/` | The Nov 11 prepared lists as handed over: still open (366), solved since (178), found and waiting for a world release (288). Snapshots, not hand-out lists. |
| `sources/` | `research-sources-all.csv` (the sources ledger, 12 columns, with the Nov 11 additions appended once) and the additions file. |

## Answer words (exactly)

`match` | `no boundary exists` | `wrong pin` | `other` | blank. The `official_point_*` columns are official agency points, not corrected pins and not boundaries. No POTA pin is moved.

## What counts as solved, and what still waits on the owner

Two separate ideas, both in `classify_row` (which wraps `classify_solved`) in `.github/scripts/kpc_research_inbox.py`:

**1. `solved` (= skip_search): the research is finished, so no search list hands the park out again.** It holds when one of these is true.
1. `released-key`: the released key already grades it official (`key_location` released-US or released-CA and status official).
2. `settled-match`: the latest answer is `match` and there is a non-WDPA official id or official source url. A match that rested only on a removed WDPA lead is not solved.
3. `settled-no-boundary`: the latest answer is `no boundary exists`.

Not solved: `wrong pin`, `other`, blank, and a match with no official id or url. The latest answer is the Nov 11 answer when the park is in the Nov 11 file, else the Nov 5 answer. `search-list.csv` is exactly the parks that are not solved.

**2. `owner_decision`:** `pending`, `yes`, `no`, or blank. `owner_decision_why` says why. `owner_answer` cites the recorded owner answer in `OWNER-ANSWERS-nov11.md` (the owner accepted all 10 recommendations in chat on Nov 11, 2026, at about 9:16 PM CT, America/Chicago, widget Yes, go with your answers).

- `pending`: research is finished but the owner has not said yes. Today this is the National Register listing-boundary matches that are still held (US-11820, US-12735, US-13474, US-8142, US-3493, US-10521, US-7975). A listing boundary is not automatically the park. A pending park is not re-researched (it is off `search-list.csv`) but it is NOT dropped from `needs-another-look.json` or `brandon-list.md`, and the inbox still judges it, so an existing hold stays intact. US-11820 and US-12735 were confirmed held under item 1; US-13474 under item 6.
- `yes`: the 56 Nov 5 matches that still asked the owner to confirm, settled on 2026-11-11 (item 10). They are join ready (unless a released-key park, which never waits).
- `no`: the owner said this is not a match. US-10274 Palmito Ranch (item 7: the National Register record is the whole 6,908-acre battlefield, the bigger place; it needs the Texas Historical Commission site outline) and FR-14979 (item 2: the official record is 13 km from the pin; the live join comes off on the next world key run). These are not solved and they go on `search-list.csv`.
- Blank, with a why only: ZA-0085, ZA-0156 and ZA-0157 stay unsolved (item 10: their official ids were WDPA-derived and were removed; they need a non-WDPA official id). Recorded 2026-11-11.

A released-key park never waits. Only solved parks with no pending owner decision leave the retry list, the short list and the inbox run.

**3. `join_ready`** (solved matches only): `yes` (including the 56 Nov 5 confirms the owner settled), or `no` when an owner decision is pending or the boundary is written in law with no map file (9 parks; they need no owner yes but there is nothing to join yet, `join_note` says so).

Solved does not mean joined. `official_id`, `official_id_type` and `official_source_url` are what a join reads (match rows only; leads on other rows sit in `candidate_id`). `match_strength` carries the Nov 11 notes section 5 tiers.

## WDPA / Protected Planet

WDPA ids (the prefixed forms and the plain "WDPA" plus a number), any id whose type is WDPA, and Protected Planet web addresses are removed from every file here. The row and its other cells stay; the flag `WDPA lead removed` is added to the flags column. A WDPA lead is never a source. The test `tests/test_solved_ledger_nov11.py` fails if one comes back.
