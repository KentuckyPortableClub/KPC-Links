# Jobs for the owner's outside agent, round 2 (23 Nov 2026, 1:05 PM Central)

From Opus (the matching chat). The owner asked (12:58 PM): "5,8,9,10,11 can other agent do these?" The COUNTS are yours: jobs 5, 8 and 9 below, one owner each. Jobs 10 and 11 stay with the matching chat (11 changes a key rule; 10 is new reader code for the owner's PC). Background: `.claude/notes/handoff-matching-nov23.md` ("Better ways for 5"). Rules in force: `.claude/RULES-NOW.md`.

## The rules for every job

1. **No build, no Release, no 2-fer run, no request to any agency server or park website.** Saved files only.
2. **No rule change.** If a count shows a rule should change, say so in plain words with the number; the owner rules, the matching chat builds it.
3. **Counts only in anything public.** Never a park's name or number in a file, test, PR or report: "Maryland, 11 parks, 7 of them by layer X".
4. **Look first:** use the tools that exist (below); name any you read and why it was not enough.
5. **Hand each job back when it is done** (one short report), not in one bundle. Say what each number ran on.
6. **No KPC-Store access**, by the owner's rule.

## What you read (all public)

- The website keys: KPC-Links `data/us-key/US-XX.json` (main). US rules on main: `69100a58d956` (W7 to W11, W-G11, W-G12 are in).
- The saved copies the keys read (shapes under `_r`): the **boundary-cache release** of KPC-Links (`cache/us/US-XX.json.gz`).
- The park facts: KPC-Data `data/park-facts.json.gz` (main). Use the one saved 23 Nov 12:32 PM (KPC-Data efd17011, after the 12:05 upload); say its `made` line.
- The counting tool: KPC-Links `.github/scripts/kpc_match_checks_count.py --cache DIR --facts park-facts.json.gz --keys data/us-key --out report.json` (it imports `kpc_match_checks.py`; offline, writes only --out).
- **Trap:** `import kpc_us_key` RUNS the builder. Use `python -m py_compile`, or lift one function out with `ast`.
- Python 3.12. Where to put the report: KPC-Data branch `tools-out`, `key-quality/2026-11-23/job<N>-pm.txt`; if you cannot push there, the report text in your reply is enough.

## Job 5. Pins outside the land, recounted with today's park facts

Last count (saved keys, older park facts): 2,222 parks with POTA's pin outside the joined land; 1,161 already confirmed another way (link, id, size, page name); of the 1,061 left, 679 within 500 m of the land; 382 left, 147 over 2 km, 36 over 10 km. Recount the same way with today's park facts (many more own pages, page points and addresses were read). Done when: the same five numbers, by state for the leftover, and for the leftover how many have an own page with a point, an own page with no point, no own page.

## Job 8. Canada: what the US proofs would confirm

No new rule. Point the US proofs the owner already ruled (id, link, size witness, page name, page point; `kpc_match_checks.py`) at the saved Canada keys (`data/ca-key/` or where the Canada key lives; say which) with today's park facts, as a COUNT. Done when: by province, parks joined by name alone today, and how many each proof would confirm; parks no proof reaches.

## Job 9. Wetland districts: the 6 pin-only parks

16 of the 22 wetland-district parks keep an outline (layer `fws`); 6 are pin only. The saved copies hold 897 records naming a wetland district or waterfowl production area (fws 393, padus 422, state layers 82). For the 6 (counts, no names): how many records of the saved copies sit within 5 km of each pin, which layer, whether one names the district, and whether the agency is the Fish and Wildlife Service. Done when: the 6 sorted into "a saved record fits", "records nearby but none names it", "nothing saved nearby". Nothing goes to the keeper (that is KPC-Store, not yours).

## After these

Tell the owner; the matching chat reads your reports and brings him any rule change as a draft PR.
