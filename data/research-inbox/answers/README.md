# Answers and solved ledger (Nov 11 2026)

Where the Nov 5 and Nov 11 mystery-park hand-backs are filed, so a solved park is not searched or handed out again. Read only: nothing here writes a key, an override, a pin, a 2-fer file or a workflow, and no rules hash reads these files. This folder is a sub-folder on purpose: the inbox checker reads only the batches straight in `data/research-inbox/`, never `answers/`.

## Start here

| File | What it is |
|---|---|
| `solved-ledger.csv` | One row per park (832). `solved` yes/no, why (`solved_basis`), `owner_decision`, `join_ready`, the official id for a join, the official point, how strong the match is. Built by `tools/kpc_build_solved_ledger.py ledger`. |
| `search-list.csv` | The 276 parks that are NOT solved: what a search list may hand out. Rebuilt with the ledger. |
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

**2. `owner_decision` = `pending`: research is finished but the owner has not said yes.** `owner_decision_why` says why. Pending when the Nov 5 row still asked the owner to confirm (`confirm` column), the match is a National Register listing boundary (a listing boundary is not automatically the park), or the ref is FR-14979 (official record 13 km from the pin). A released-key park never waits. A pending park is not re-researched (it is off `search-list.csv`) but it is NOT dropped from `needs-another-look.json` or `brandon-list.md`, and the inbox still judges it, so an existing hold (for example the agency-alias holds US-11820 and US-12735) stays intact. Only solved parks with no pending owner decision leave the retry list, the short list and the inbox run.

**3. `join_ready`** (solved matches only): `yes`, or `no` when an owner decision is pending or the boundary is written in law with no map file (9 parks; they need no owner yes but there is nothing to join yet, `join_note` says so).

Solved does not mean joined. `official_id`, `official_id_type` and `official_source_url` are what a join reads (match rows only; leads on other rows sit in `candidate_id`). `match_strength` carries the Nov 11 notes section 5 tiers.

## WDPA / Protected Planet

WDPA ids (the prefixed forms and the plain "WDPA" plus a number), any id whose type is WDPA, and Protected Planet web addresses are removed from every file here. The row and its other cells stay; the flag `WDPA lead removed` is added to the flags column. A WDPA lead is never a source. The test `tests/test_solved_ledger_nov11.py` fails if one comes back.
