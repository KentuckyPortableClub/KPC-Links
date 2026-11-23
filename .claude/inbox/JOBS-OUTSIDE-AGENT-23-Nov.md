# Jobs for the owner's outside agent (23 Nov 2026, 8:25 AM Central)

From Opus (the matching chat). The owner asked (8:18 AM): "Job 4 etc can outside agent do that research?" These three are yours, ONE owner each; no other chat starts them. They are COUNTS on saved files: nothing is built, fetched or changed. Background, numbers and the job table: `.claude/notes/handoff-matching-nov23.md`. Rules in force: `.claude/RULES-NOW.md` (rule sheet W is the matching sheet).

## The rules for every job

1. **No build, no Release, no 2-fer run, no request to any agency server or park website.** Saved files only.
2. **No rule change.** If a count shows a rule should change, say so in plain words with the number; the owner rules, the matching chat builds it.
3. **Counts only in anything public.** Never a park's name or number in a file, test, PR or report: "Maryland, 11 parks, 7 of them by layer X".
4. **Look first:** use the tools that exist (below); name any you read and why it was not enough.
5. **Hand each job back when it is done** (one short report), not in one bundle. Say what each number ran on.
6. **No KPC-Store access**, by the owner's rule.

## What you read (all public)

- The website keys: KPC-Links `data/us-key/US-XX.json` (main). US rules on main: `c6f3a95b1018` (W7, W-G11, W-G12 are in).
- The saved copies the keys read (shapes under `_r`): the **boundary-cache release** of KPC-Links (`cache/us/US-XX.json.gz`).
- The park facts: KPC-Data `data/park-facts.json.gz` (main). A newer one comes after the owner's upload today; say which one you used (its `made` line).
- The counting tool: KPC-Links `.github/scripts/kpc_match_checks_count.py --cache DIR --facts park-facts.json.gz --keys data/us-key --out report.json` (it imports `kpc_match_checks.py`; offline, writes only --out).
- **Trap:** `import kpc_us_key` RUNS the builder. Use `python -m py_compile`, or lift one function out with `ast`.
- Python 3.12. Where to put the report: KPC-Data branch `tools-out`, `key-quality/2026-11-23/job<N>.txt`; if you cannot push there, the report text in your reply is enough.

## Job 4. The place rows, broken down

538 parks (about 1,900 check rows) go to the check list for PLACE, and nobody has split them. Count, by state: which place test sent each row there (the reason words `kpc_match_checks.py` writes: pin outside the joined land, far from the pin, another county than the page names (W6), and so on), how many parks and rows each, and how many of those parks are already confirmed another way (id, link, size, page name). Then say which one or two causes hold most of the rows. Done when: one table (state x cause, parks and rows) plus a three-line summary.

## Job 6. Maryland: 11 parks whose outline is under a third of the agency's size

These 11 drop to a pin under the size check. For each, count only: which witness gave the agency's figure (park facts `size` witness: same_record, other_layer, agency_document, hand_copy, unknown), how the outline's acres were measured (`ac`, `ac_how`), and which layers the outline came from. The question to answer: is the outline really too small (missing land), or is the agency figure the wrong number (another unit, a total for many parks)? Done when: the 11 sorted into those two groups (and "can't tell"), counts only, with the witness kinds.

## Job 7. Saved answers that no longer find their record (323 + 64)

From the 22 Nov PC test: 323 saved answers find no record (Michigan 76, Wisconsin 74, Utah 57, the rest spread), and 64 find two that fit (Wisconsin). **Read `.claude/notes/key-quality.md` on saved answers first** (what a saved answer may do; grade only with its section 9 tools, never against the saved answers themselves). Count, by state: why each one misses: the record's id changed in the newer saved copy, the layer is missing from the saved copies, the record was split or merged, or the name changed. For the 64: what tells the two records apart (county, size, layer). Done when: a table by state and cause, and for each cause the fix in one plain sentence (no fix built).

## After these

Tell the owner; the matching chat reads your reports. Jobs 5, 8, 9 (pins outside the land, Canada, wetland districts) and 11 ("near a town") wait for today's upload and stay with the matching chat.
