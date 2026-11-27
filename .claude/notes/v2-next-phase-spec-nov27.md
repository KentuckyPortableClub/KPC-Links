# v2 NEXT PHASE: the owner's 3-item plan (27 Nov 2026). NOT BUILT YET. Do not forget it.

The owner, 8:25 AM: "lets not forget about that cause it makes my life easier and helps agents from forgetting something".
WHEN: after the fresh PC v2 build of 27 Nov is graded and #393 / KPC-Store #39, #40 / KPC-Data #202, #203 are settled (the
grader's call, 5:47 AM). ORDER: 1, then 2, then 3. Each line below says what already exists, so nothing is built twice.

## 1. Freeze the matcher: no overrides after v2 runs
- The plan: once the build passes and #393 merges, `.github/scripts/kpc_us_key_v2.py` is frozen. No table that patches finished
  keys. Every fix is an INPUT (`.github/us-key-v2-rules.json` or the park facts) and must still pass today's layers, the proof
  (agency id, or name + pin / size) and the gate. A per-park exception may only point to an agency id or say "stay pin only";
  if that record is gone or fails the gate, the park drops back to pin only by itself.
- Exists already: the repair method (rule sheet section 8); the mutation tests that notice a removed rule; `other_spellings`
  (27 Nov) is built this way; there is NO override table anywhere.
- Fable's notes: "frozen" = no change for one park. A real fault with a test is still fixed (27 Nov: the Alaska hang).
  To build: one test that fails if the matcher file changes without a line in a short change list.
- STATUS: not started. Nothing to build until #393 merges.

## 2. Problem solver: reads `v2-pin-only.csv`, never edits a key
- The plan: one tool, after v2, that takes each pin-only park by its reason and says what would fix it: a spelling or id row to
  propose, a layer missing from the store, the exact blocker (pin distance, no size on file, easement), two candidates side by
  side, a pair of parks sharing a record, or "confirmed pin only, do not chase again". Output: one small table of proposals.
  Approved rows go into the park facts or the rule table for the next run.
- Exists already: `v2-pin-only.csv` and `pin-only-all.csv` (every pin-only park with its reason), `v2-id-other-names.csv`, the
  state prep tool (ids, name styles), the try-a-rule workbench. Build on these.
- The OLD problem solver in GitHub (owner 8:26 AM: "not sure if it is a good starting point"): `kpc_problem_solver.py` (7 Nov,
  1,521 lines), `kpc_solver_final_pass.py` (24 Nov), KPC-Data `kpc_pile_solver.py`. Looked at 27 Nov: built for v1. It reads v1
  keys, v1 holds and the old saved-outline cache, and its fixes are `overrides.json` join rows, the after-the-fact patch item 1
  forbids. So NOT the base. TAKE FROM IT: its checks (a sliver outline, land in another state than POTA lists, the ways a pin
  looks wrong: one digit off, one coordinate off, a rounded pin), the final pass's guards (never another park's land, a
  kind-of-land guard, a part never takes the whole), its plain verdict words, and its real examples as test cases (Windy Gap
  US-9678, Little Pee Dee US-3917, Cedar Mesa US-11748, Owyhee River US-13039). Rewrite them to read today's layer files.
- Fix first, or it sorts parks wrong:
  a. The reason list. v2's own list (rule sheet section 6): `no_record_with_this_name`, `name_but_no_pin_or_size_proof`,
     `two_records_fit`, `record_shared_with_another_park`, `water_only`, `office_only`, `layer_not_complete`,
     `record_layer_not_in_store`. The plan's `park_has_no_pin` is not a v2 reason; `layer_not_complete` is missing from the plan.
  b. Reasons must be true (a trail park whose pin is too far says "name but no pin or size proof": add a plain reason for it).
  c. "What sits under the pin" only SUGGESTS. v2's proof still decides. Pins are the weakest evidence we have.
  d. No yes / no list to the owner park by park (his rule of 25 Nov). A row v2's own proof can settle goes in without asking;
     only a short list for a rep is for people.
- STATUS: not started.

## 3. Control panel: four boxes, one small file
- The plan: v2 and the problem solver write ONE `v2-panel.json`; the page only shows it. Four boxes: Inputs (store layers
  whole / missing, hand downloads, park-facts date), v2 keys (confirmed vs pin only per area, gate pass / fail, share all /
  part / none), Problem solver (the pin-only buckets and waiting proposals), Health (storage, last run time CT). The same four
  on the PC with one button per step: layers, facts, build, problem solver. It replaces the old v1 clutter on `kpc-control.html`.
- Exists already: `V2-BUILD-SUMMARY.txt` and `summary.csv` (per area: outlined, pin only, gates, licence counts since 27 Nov),
  `STORE-ROOM-STATUS.txt` + `status.csv`, `PAGE-READER-STATUS.txt`, `park-facts-summary.txt`, and `V2-FRONT-DOOR.bat`
  (lists the four steps and starts the one picked; not yet run by the owner).
- Fable's notes: a web page cannot start programs on the PC: the buttons stay `.bat` files, the page shows results. The four
  steps leave out the page reader, which feeds the facts: make it five, or show it under Inputs. Counts only for private
  layers on the website; nothing new goes public without the owner's GO (the hold rule).
- STATUS: not started. Last of the three: it changes no key.
