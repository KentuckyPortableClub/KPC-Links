# Hand-off: the better matcher + full layer files (25 Nov 2026, ~9:10 AM CT)

Read this first in a new matching chat. Plain words. Owner: KPC owner. Nothing is merged; nothing is built (NO BUILDING stays).

## Where things stand
- **KPC-Links #380** (branch `prep/better-matcher-nov25`, head a0b1a4b2, draft): the better matcher. US rules deb61cc4084c -> **0d015ade5a34**,
  changelog line says NOT YET APPROVED. The other builder graded rounds 1-7; round 8 (+ the gap fix a0b1a4b2) is not graded yet.
- **KPC-Store #38** (branch `prep/layer-records-nov25`, head 8f1bf6d, draft): `engine/kpc_layer_records.py` + `LAYER-RECORDS.bat`
  (every record of every layer the keys join, US + Canada; world ON HOLD), G4 in `kpc_outline_store.all_parks`, Catskill allowed (read only).
  The other builder cannot see KPC-Store (no access): the owner reviews it.
- **KPC-Data #199**: revert of the US-4501 acres edit. Graded MERGE-READY; the owner merges when he likes.

## The rules now (owner's words 25 Nov)
- 6:20 / 6:28 AM: match by proof from fresh data: agency (unit) id, then shared ground (80% / 50%; piece 90% with a shared name),
  then real name + size within 10%; never a row number; unproven = POTA pin + "code to fix", no hand-offs to the reps.
- 7:18 AM: today's store records are the FRESH source; old saved copies are hints only.
- 8:21 / 8:48 AM ("simplest path"): the PC downloads every WHOLE layer the keys join; those **full layer files**
  (`results\store\<area>.layer-records.json.gz`, with a per-layer manifest: source count, saved count, complete) are the only fresh
  source. The park-by-park store is no longer the source of truth. A key build for an area **stops and lists the gap** if any joined
  layer is not complete. US + Canada now; world on hold.
- 9:07 AM: allow the NY Catskill boundary (US:sgnyd): read for matching only, never published (DEC terms forbid redistribution).
- Switches KPC_SAME_LAND, KPC_PROVEN_ONLY, KPC_STORE_FRESH: on for MN and NY only. Kentucky later (its own handling).

## Owner's PC (all byte-checked)
- Key test kit: `D:\KPC GITHUB TOOL and MOre\key builder files` (START-HERE.bat adds every kpc-kit-update zip once). Latest: **25n**
  (rules 0d015ade5a34). Reports: `reports\test-<date-time>\REPORT.txt` + lists (pin-only-parks.csv, saved-answers-moved.csv,
  rows-kept-but-listed.csv, layers-not-complete.csv, layers-not-in-store.csv, saved-answers-no-fingerprint.csv).
- Store tool: `D:\KPC GITHUB TOOL and MOre\Tools\KPC-TOOLS-NOV14\1-STORE-TOOL\kpc-outline-store-full` (engine with G4; old copy kept as
  `kpc_outline_store.before-g4.py`; `kpc_layer_records.py`, `LAYER-RECORDS.bat`; verified-layers.csv has the Catskill row).
- MN + NY whole layers downloaded 8:47 AM: MN all 10 layers complete (fws 1,768 of 1,768); NY complete except sgnyc (107 records, none
  with a polygon or id: not joined) and sgnyd (Catskill: allowed at 9:07, to download).

## What the owner is doing now
1. LAYER-RECORDS.bat -> 1 (MN + NY) -> Y (downloads only Catskill).
2. START-HERE.bat -> report must say US 0d015ade5a34 -> `MN NY`.
Expected: MN builds (all joined layers complete); NY builds once Catskill is complete. Read the new `reports\test-...` folder.

## Next jobs, in order
1. Read the MN + NY test: pin-only parks and why, saved answers moved, rows listed, gaps. Send counts to the owner (copy-paste block
   for the reviewer; the owner prefers paste-ready messages over zips).
2. One grade of #380 round 8 (+ a0b1a4b2) by the other builder; the owner reviews #38.
3. Open items the grader or owner raised: S2 (confirmed parks keep all their name rows: owner's call), the "kept by name and official
   size" count (0 so far: report says why), the GitHub boundary-rebuild workflow needs the layer files before it may run (it would HOLD).
4. Then, only on the owner's word: LAYER-RECORDS for every US + Canada area (choice 2, many hours), switches on for more states,
   the owner's quoted OK on the rules line (marks APPROVED), merge.

## House rules that bit today
- Never push to main (branch + draft PR; author KPC owner, message ends "KPC owner, <date>", no trailers).
- Touched tests only, Python 3.12. Rule changes need the owner's quoted OK; data/** only with his OK for that exact edit.
- The device bridge sometimes delivers an OLD copy: stage it back and compare md5 every time; resend under a new output folder name.
- A PC run started before a kit lands uses the older kit: check the rules line at the top of REPORT.txt.
