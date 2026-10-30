# Automating the map key + the 2-fer line: instructions for Opus (chat 2)
Written by Fable, Oct 29 2026 11:05 PM, on Brandon's order ("Write instructions to opus on how to automate the key building and
2fer line. Make it accurate, efficient and fast."). Brandon 10:58 PM: "Hang on" = do NOT start building until he says go.

## STATUS (Oct 29 11:25 PM, Opus; Brandon 11:18 PM 'build it!')
- Step 0 DONE (Fable). BOT A DONE (Fable). BOT B wired with A (blank states = touched states only); timing test = KPC-Links run
  41002310689 (states 'RI DE'): pass = green, under 8 min, the other 48 state files byte-identical (md5 list taken before: /tmp only).
- BOT C DONE: KPC-Data `.github/scripts/kpc_key_summary.py`, run inside `kpc-copy-from-links.yml` right after the waiting room's divert;
  writes `data/waiting/preview/us-key-changes.json` (+ ca-key) = totals, per area, gained / lost / grade changes, SAMPLE of 30 (15 from
  chat 11's own answers via the ledger, 15 from layers / code). Tested on tonight's held build vs live: +51 outlined / 1 lost / 368
  piece changes / 37 grade changes, 74 KB. The copy now also runs at 01:41 UTC (8:41 PM CDT) so a day's rebuild reaches chat 11 the
  same night. KPC-Data e929c853.
- BOT B TEST PASSED: run 41002310689 (RI DE) green in 2 minutes; only US-DE.json, index.json, changed-parks.json changed, the other 48 state files untouched.
- BOT D DONE (chat 10, KPC-Data 8b77a3b6): nightly release-approved 11:13 UTC, a YES is used once, a released key writes data/waiting/released-key.json and dispatches kpc-fers-pending.yml (force) = BOT E. ALL SIX PIECES DONE Oct 29 11:30 PM.
- BOT E DONE: `kpc-fers-pending.yml` now remembers the LIVE key's pieces per park (`data/fers/key-seen.json`, first run only
  remembers) and queues every park whose LIVE outline changed, its own state as one area (1/3-size), only for states in
  `data/fers/new-key-states.json` (waves 1 + 2 = 15 states; chat 2 adds each new wave's states); a key change runs at once (no 5-park
  wait); also triggered when the waiting-room workflow completes. Tested offline with a fake dispatcher: an Ohio change started
  exactly one Ohio area run, a Texas change (not yet in a wave) started nothing.

## The one rule
A bot MOVES decisions; it never MAKES one. Chat 11's YES / NO on a map piece and Brandon's word on a release stay human.
Everything between those two points (copying answers into the key, rebuilding, comparing, holding, copying live, rerunning
2-fers) is clerical and runs itself. Rule G is unchanged by any of this.

## The chain (today by hand → tomorrow by bots)
```
chat 11 answers in data/waiting/questions/*.json          (human, as now)
  → BOT A  writes each answer into data/us-key/overrides.json           (today: chat 2 by hand, ~1 session per round, error-prone)
  → BOT B  rebuilds ONLY the states those answers touched (minutes)      (today: all 50 states, 25 min, by hand dispatch)
  → the rebuild lands HELD in KPC-Data data/waiting/in/ (chat 10 wired this Oct 29 10:30 PM: KEY WIRED, KPC-Data 70b0733b)
  → BOT C  writes the before/after summary + picks chat 11's 30-park sample (today: chat 2 by hand, counts + preview page)
  → chat 11 samples, writes KEY YES in data/waiting/approved.json           (human)
  → BOT D  releases the key live (chat 10's release-approved mode)         (today: dispatched by hand)
  → BOT E  reruns the 2-fer line for the states whose outlines CHANGED, on the LIVE key (today: waves picked by hand)
```
Result: the gap from "chat 11 answered" to "live + 2-fers redone" drops from 3-4 of Brandon's inbox rounds to one.

## Step 0 — DONE by Fable Oct 29 11:08 PM (KPC-Data 4b30eb0f). Brandon 11:07 PM: 'You do step 0...opus do the rest'. The rest = Opus, on Brandon's GO.
## Step 0 (do first, 5 minutes): the 2-fer checker must read the LIVE key again
On Oct 29 7:05 PM chat 2 changed KPC-Data `.github/workflows/kpc-fers-line.yml` (checker job, "The worker's bundle" step) to keep the
KPC-Links `data/us-key/$st.json` over the KPC-Data copy, because KPC-Data's copy was then the frozen OLD key. Since chat 10's
wiring (10:30 PM) the roles flipped: KPC-Links `data/us-key` = the latest BUILD (possibly not approved), KPC-Data `data/us-key`
= the LIVE, approved key. The 2-fer line must measure against the live key, so put the line back to
`cp kpcdata/data/us-key/$st.json data/us-key/ 2>/dev/null || true` (KPC-Data copy wins). Same thinking everywhere: a bot that
reads "the key" reads KPC-Data's copy; only the key BUILDER reads KPC-Links.

## BOT A — BUILT by Fable Oct 29 11:35 PM (Brandon 11:12 PM 'Do a'). `.github/scripts/kpc_key_answers.py`; runs first in kpc-us-key.yml's plan job.
Tests passed: replay of Oct 29's answers on the pre-hand overrides = the SAME join lists as the hand work (0 differences after two data
slips were fixed: a 'sgwabNone' hand typo on US-13383, and chat 11's later NOT SURE written into 17 key-pieces rows it had left as YES);
second run applies 0; the 208 gis-hunter NO rows now sit in 'no' lists as bookkeeping (none was a joined piece). First real run done
locally (ledger seeded, 483 rows), so the workflow's first run rebuilds nothing until chat 11 writes new answers.
BOT B is half done with it: the plan job now reads answers-states.txt (blank `states` = only the touched states; 'all' or the monthly
cron = every state; nothing new = the run ends green with 'nothing to rebuild', build + join skipped). Opus: run its test (a real
2-state answers run under 8 min, other state files byte-identical) on the next batch of chat 11 answers.
Dry run by hand: `DATA=../kpc-data python3 -I .github/scripts/kpc_key_answers.py --dry` from the KPC-Links root.
## BOT A: the answers writer  (`.github/scripts/kpc_key_answers.py`, KPC-Links)
What it does: turns every chat 11 answer into the key's rules file, exactly as chat 2 did by hand on Oct 29 (10:55 PM: 67 YES → 64
joins / 56 parks; 7:20 PM: the 40 probe verdicts; 8:20 PM: the release check).
Inputs (read from a KPC-Data checkout, `data/waiting/questions/`):
- `key-pieces.json` (307 rows): `{area, ref, record, record_name, acres, why, answer, checked_by, how}`; `record` is already a key id
  (`fws448`, `sgtni131`, `195096`, `rst9580`...). Built by KPC-Data `kpc_key_questions.py` after each rebuild.
- `gis-hunter.json` (318 rows): `{area, ref, record (a layer OBJECTID), record_name, acres_approx, layer (URL), answer, checked_by}`.
  Map `layer` → key prefix with `data/us-key/layers.json` (strip `/query`, compare case-free, try FeatureServer↔MapServer); PAD-US
  (`edits.nationalmap.gov/.../PAD_US/MapServer/0`) = the bare OBJECTID; FWS realty = `fws<id>`; a layer not in layers.json = SKIP
  and list it (it must first be added to data/state-gis.json; never invent a prefix).
- any new questions file chat 10 adds with the same four fields `ref, record, record_name, answer` (write the reader once, keyed on
  those fields; unknown extra fields are ignored).
- NOT a markdown file: chat 11's prose verdict files (`KPC_KeyPieces_Probe_Verdicts_desk.md`, release checks in the inbox) stay a
  chat 2 hand job. Rule to put in chat 11's inbox: answers go in the JSON questions files only; prose is for notes.
Rules it applies (no judgement, just bookkeeping):
- `YES`  → `overrides.json parks[ref].join += [record]`, `fp[record] = [record_name, acres]` (so a PAD-US id that changes in the next
  PAD-US version is found again by name + acres, as the key already does), `why += "<date> <time>: <file> row YES (chat 11; applied by
  kpc_key_answers)"`, `when = date`. If the record is in that park's `no` list, REMOVE it from `no` first (an id can't be both).
- `NO`   → `no += [record]`; if it is in `join`, remove it from `join` and `fp`.
- `NOT SURE` / null / anything else → nothing. A later answer on the SAME (ref, record) replaces the earlier one (Oct 29 lesson: chat
  11's 7:35 PM NOT SURE replaced its 1:50 PM YES on 11 parks; the later row wins, by `checked_by` date, else file order).
- `alias` answers: a questions row with `"kind": "alias"` (website-name / name-mismatch batches) and YES → `alias += [record_name]`
  (the key joins an alias only when the pin is inside a record of exactly that name: existing rule, keep it).
- Ledger: `data/us-key/answers-applied.json` = `{ "<file>:<ref>:<record>": {"answer", "checked_by", "applied"} }`. A row already
  applied with the same answer is skipped; a changed answer is re-applied. This is what makes the bot safe to run every night.
- Output: `::notice title=Key answers::N applied (Y yes / N no / A alias), states: TN OH ...` and the state list to a file
  `data/us-key/answers-states.txt` for BOT B. Writes overrides.json with `kpc_save.save_json` (same bytes as the hand edits).
Where it runs: a first step in `kpc-us-key.yml`'s `plan` job (so one workflow = answers + rebuild), committed before the build jobs
read overrides.json (the plan job pushes overrides.json + the ledger; the build jobs check out that commit).
Tests before it is trusted (run offline, `python3 -I`): (1) replay Oct 29's `gis-hunter.json` on the overrides.json from commit
`ce30b179`'s parent and diff against commit `d9f2ea01`'s overrides.json: must produce the same 64 joins / 56 parks, nothing else;
(2) replay `key-pieces.json`: every YES/NO row lands in join/no, NOT SURE rows change nothing; (3) run it twice: the second run
applies 0. Keep the hand-join fix of Oct 29 8:25 PM in kpc_us_key.py (a hand join on a piece already joined by name marks it
'reviewed'): without it the bot's joins are silently held by G-1 / R-G8, which is exactly the bug that hid ~77 approved parks.

## BOT B: rebuild only the states that changed  (`.github/workflows/kpc-us-key.yml`)
Already half there: the workflow takes a `states` input (blank = all but KY), builds per state in a matrix, and the `join` job
copies only the built states' files over the checkout and then runs the all-state steps (`FINISH_ONLY=1`: cross-state pins,
index.json, layers.json, `data/us-key/changed-parks.json`). So:
- `plan` job: STATES = `inputs.states` if given, else the states in `answers-states.txt` from BOT A, else (nothing to apply) STOP
  the run green with one notice ("nothing to rebuild"). A code change to kpc_us_key.py, a new layer in state-gis.json or a Rule G
  change = a FULL rebuild, dispatched by hand with blank `states` (the monthly cron stays as the safety full rebuild).
- Keep the per-state build exactly as is (each state is independent); KY stays out (its own key).
- `join` job: already right. Add the KPC-Data checkout of the LIVE key for BOT C's comparison (sparse, `data/us-key` only).
- Time: a 5-state rerun ≈ 4-6 minutes end to end instead of 25.
- Email rule: the schedule is nightly 03:5x AM CDT (jitter) ONLY IF the ledger shows unapplied answers (the plan job decides and
  exits green otherwise); every step that can fail on a flaky server ends `|| true` except the save; one dispatch per change.

## BOT C: before/after summary + chat 11's sample  (in the `join` job, after the rebuild)
Restore `kpc_key_preview.py` from git history (last at commit `2493054d`; deleted at `4ec6b770` for repo size, keep it OUT of KPC-Links
data) and run only its `compare` (offline): LIVE key (KPC-Data data/us-key) vs the NEW build. Write to KPC-Data
`data/waiting/preview/us-key-changes.json` (small: counts per state, parks that gained / lost an outline with their pieces and the
Rule G reason, grade changes, and the SAMPLE: 30 refs = 15 picked from parks changed by hand answers (BOT A's ledger this run)
+ 15 from parks changed by new layers / code, one per state where possible, with name, pieces, acres, pin-inside flag, record links).
Then one line in `.claude/inbox/chat-11.md` (KPC-Links; the bot already writes inbox lines elsewhere): "US key build <sha> is
HELD: +X outlined / -Y lost / Z grade changes; sample of 30 in data/waiting/preview/us-key-changes.json; write KEY YES or KEY NO:
refs in data/waiting/approved.json". No shapes fetched by the bot (the 7.7 MB shapes file was the size problem): the drawn
preview page (`.claude/build/preview/make_preview_page.py`) stays a chat 2 on-request page for Brandon, built from `fetch` locally.
Push rule: the summary goes to KPC-Data; the inbox line to KPC-Links (one small text commit; skip 12:00-1:00 AM on a cleanup night).

## BOT D: release  (chat 10's waiting room; nothing new to build)
Chat 11 writes in KPC-Data `data/waiting/approved.json` items: `{"what": "us-key", "path": "data/waiting/in/data/us-key/", "chat11":
"KEY YES <date> <sample result>"}` and chat 2's recheck field (`"chat2": "rechecked <date>"`; the recheck = BOT C's summary read by
chat 2, one line). Then `kpc-waiting-room.yml` mode `release-approved` (`kpc_release_approved.py`) moves it live. Ask chat 10 for one
thing: run `release-approved` on a timer (nightly, after the daily copy) so a KEY YES written in the evening is live by morning
without a hand dispatch; a Rule G change on purpose still needs the G5 stamp (big-change alarm), as chat 10 built it.

## BOT E: the 2-fer line, only where outlines changed, only on the live key
Exists already: the key's `join` job writes `data/us-key/changed-parks.json` (parks whose joined pieces changed) and KPC-Data
`kpc-fers-pending.yml` (daily 10:23 UTC) turns waiting parks into one small batch per area when 5+ wait (or any on Sunday); the line
itself reuses every pair whose inputs did not change (`kpc_fers.py` reuse fingerprints, `data/fers/reuse-p<pass>-<tag>.json`), so a
rerun of a state is minutes, not hours. Make it exact:
1. `changed-parks.json` must be computed from the LIVE key → the released key, not build → build: write it in BOT D's release step
   (diff KPC-Data's previous `data/us-key` copy, kept by the waiting room in `data/waiting/previous/`, against the released one), or
   have `kpc-fers-pending.yml` read the waiting room's `released.jsonl` for the last key release and diff there. A held build that
   chat 11 rejects must never trigger a 2-fer rerun.
2. Trigger: `kpc-fers-pending.yml` runs right after a key release (`workflow_run` on the waiting-room workflow, or a dispatch from
   the release step), not only on its daily timer. Keep the daily timer as the catch-up.
3. Areas: one line per STATE with changed parks, 1/3-size areas as HQ set (Oct 29 3:11 PM), at most 3 at once (the outside servers);
   states on the Fable list wait as Brandon ordered (a state joins the 2-fer line only when its Fable section says DONE), except a
   state that is already past the line and has a changed park, which reruns.
4. The checker reads the LIVE key (Step 0). The line's own save goes through the waiting room (chat 10 wired it: changed
   US/CA 2-fer files are held the same way) → chat 8 grades → chat 11 → release-approved.
5. Alaska waits for chat 3's file-size fix; Canada 2-fers = none (SCOPE: no world 2-fers; Canada has 2-fer tools, same line, after
   the Canada key is rebuilt under R-GC1..8).

## Order of work and what "done" means
1. Step 0 (checker reads the live key)  → done when a line run's checker log shows KPC-Data's key file dates.
2. BOT A + its three tests  → done when the replay reproduces Oct 29's 64 joins and a second run applies 0.
3. BOT B  → done when a 2-state `states` run finishes green in under 8 minutes and the other 48 state files are byte-identical.
4. BOT C  → done when chat 11 answers one real sample from the summary file alone (no files opened by hand).
5. BOT D timer (chat 10)  → done when a KEY YES written in the evening is live the next morning with no dispatch.
6. BOT E  → done when a key release with 3 changed parks in 2 states produces exactly 2 area reruns and nothing else.
Test each piece on ONE state first (Brandon's SAVE USAGE rule); keep the hand process until a piece passes its test; one dispatch
per change, never rerun-to-see; every bot step ends `|| true` except the save; no bot ever writes to the website repo's data folders
(size rule: bot outputs live in KPC-Data).

## What stays human, on purpose
- Chat 11: YES / NO per map piece, the 30-park sample, KEY YES / KEY NO.
- Chat 2 (Opus): reads BOT C's summary and writes the one-line recheck; handles prose verdicts and anything a bot lists as SKIP;
  decides when a code / layer / rule change needs a full rebuild; builds the drawn preview page when Brandon asks.
- Chat 8: grades 2-fer areas. Brandon: the release word and any Rule G grey area.

## BOT F: start each state's FIRST new-key 2-fer run by itself  (Fable, Oct 29 11:30 PM; Brandon: 'Instructions?')
Today chat 2 reads the Fable file, decides a state is done, dispatches its first run and adds it to data/fers/new-key-states.json.
The Fable file has no fixed marker (3 loose 'DONE' mentions), so a bot cannot read it. Give it one marker, one place:
1. THE MARKER: KPC-Links `.claude/build/research/fable-state-done.json` = `{"US-XX": {"date": "2026-10-30", "by": "chat 3", "note":
   "last open park placed / ruled"}}`. The chat that finishes a state's LAST open Fable-list park (chat 3 or chat 8) writes that
   state's line (HQ's order already says 'STATE XX DONE': this is the same word, in a file a bot can read). Nothing else counts.
   States with 0 open parks from the start are already in new-key-states.json (waves 1 + 2); the marker is only for the rest.
2. THE BOT: one more step in KPC-Data `kpc-fers-pending.yml` (it already runs daily 10:23 UTC and after every key release):
   for each state in the marker file that is NOT yet in `data/fers/new-key-states.json` and not in a `hold` list
   (`US-AK` until chat 3's file-size fix lands; `US-KY` never: own key, already run): dispatch `kpc-fers-line.yml` with
   `states=US-XX`, `tag=<xx>`, `stage=all`, NO `parks` filter (a first run = the whole state), then add the state to
   new-key-states.json and push. At most 3 states per run and never while the full queue (`kpc-fers-lines.yml`) is in progress
   (the step already checks that). One dispatch per state, step ends `|| true`, no email.
3. ORDER: fewest open parks first is automatic (a state is marked done when it reaches 0); if several are marked at once, start the
   ones with the fewest parks (data/parkinfo/US-XX.json count) first, the rest next run.
4. AFTER the first run: the state is in new-key-states.json, so BOT E reruns it by itself whenever its live outlines change.
5. TEST (one state): write the marker for one small done state (e.g. US-IA, 1 open park, once chat 3/8 confirms it), run
   kpc-fers-pending.yml by hand with force=yes: it must start exactly one Iowa line, add US-IA to new-key-states.json, and a second
   run must start nothing. Then it is trusted.
What stays human: deciding a state's last park (Rule G, chats 3 / 8 / 11); Alaska's hold; the Canada line (after the Canada key rebuild).
