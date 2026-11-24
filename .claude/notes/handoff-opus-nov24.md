# Hand-off from Opus, 24 Nov 2026 ~10:50 AM CT

The owner is limiting Opus's usage. You take over everything below. Plain writing, IDs only, house rules in `.claude/CLAUDE.md`.

## Where things stand (all verified on main)
- **KPC-Links main:** US **ae8e40264dda**, CA **7696c35aa512**, world 167bf55f79a8, fers 62e77c250cc5.
- **Merged today:** #366, #367, #368, #369, #370, #371, #372, #373, and KPC-Data #187 to #194.
- **PC kit:** `kpc-kit-update-2026-11-24a.zip` is in `key builder files`, and the page reader's 5 scripts are updated (all read back equal). START-HERE has NOT been run. Its report must say US ae8e40264dda / CA 7696c35aa512.
- **NO BUILDING is still in force:** no key build, outline rebuild, Release or 2-fer run.

## Job 1 (small, first): finish the acreage
1. Review and merge **KPC-Data #195** (FWS table with out-of-order columns; tests pass on 3.12 and 3.13).
2. Then dispatch ONE acreage run, with **fresh=no**:
   `gh api -X POST repos/KentuckyPortableClub/KPC-Data/actions/workflows/kpc-tool-trial.yml/dispatches -f ref=main -f 'inputs[tools]=acres' -f 'inputs[fresh]=no'`
   **NEVER fresh=yes.** It wiped the last good reads of 5 lists on saved-copy-only hosts. I repaired that on tools-out (c99be74c, the bot's own "kept" rule).
3. **Done means:** `data/park-facts-summary.txt` on KPC-Data main shows **more than 2,268** official sizes (it says 2,133 now). The FWS refuges should no longer show "no row read" in tools-out `acres/report.md`.
   - Today's gains to keep: Park Service +220 and Forest Service +110 (the intake file `acres-usfs-lar-fy2025.json`).

## Job 2 (the big one): re-check REPAIRS.md against the real code
The owner's question: "where was all that yesterday?" The open lines in `.claude/inbox/REPAIRS.md` were written 19-20 Nov and **were not re-checked since**.

For each open line (O9, O10, K2, G1-G3, F3-F5, B1/B3/B4/B6, R1-R16, Z1-Z3), check it against the code and the runs, not the notes. Mark each one:
- **DONE** + proof (commit, run, number); or
- **STILL OPEN** + what is left, in one line; or
- **OWNER'S CALL** + the one question.

Then give the owner ONE short list: what really stands between today and Z1 (the one build). Today's merges may already close some lines (auto-confirm, page names, robots, the stop list). R9 (the 2,379 old public 2-fer rows: take them down now or keep them?) is an owner question.

Read KPC-Store `docs/code-map/START-HERE.md` before building anything (LOOK BEFORE YOU BUILD).

## Owner's new ask (after the PC move)
"set up my tools to auto update rules from GitHub and push to GitHub". The idea:
- **Pull:** START-HERE does a `git pull` of the kit's `links` and `KPC-Data` copies, instead of kit zips sent by hand.
- **Push:** the PC's reports and page-reader results are pushed back to a KPC-Data side branch.

It needs a GitHub sign-in on the PC: the owner's own `gh auth login`, never a token pasted in chat. Plan it as part of the new-PC move (answer-key plan, `.claude/notes/` new-PC notes). It is not built yet.

## Open, not urgent
- **BLM map sizes as a match witness:** measured, 0 gain in NV+OR. Not built (ledger 10:35 AM). The display option (BLM acres on park pages as "agency map data") waits for the owner's GO.
- **Forest Service yearly list:** done as the intake file. Next year's needs the owner's hand download again (Box blocks bots).
- `test_kpc_matcher_nov13` (73 golden cases) and `test_match_checks_wiring_nov20` (an old changelog phrase) fail on main. This is part of R15.

Ledger lines for all of this are in `.claude/inbox/LEDGER.md` (24 Nov, Opus).
