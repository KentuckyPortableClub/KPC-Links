# Jobs for the owner's outside agent (20 Nov 2026, 7:10 AM Central)

From Fable (the reviewer). The owner asked for you to take more of the key problems, not only the size check. You are the ONE owner of each job below; no other chat starts them. Read `HANDOFF-20-Nov.md` in this folder first for the rules and the state of things.

## WHO HAS WHICH JOB (Fable, 20 Nov 8:50 AM; read this first)

Two outside agents picked up this list at the same time. That stops here. One owner per job:

| Agent | Its jobs | Stop work on |
|---|---|---|
| **The agent that opened pull request #306** | Job 1 (the size check, #306), job 3b (hold the Army Corps layer), job 8 (the wiring check, done) | Jobs 3 to 7 |
| **The agent that opened pull request #305** | Job 3 (licences, done), job 4 (the rule sheet), job 5 (#305), job 6 (done), job 7 (the test gate) | Job 1: its own size-check draft was never pushed and is dropped |

**Update 9:25 AM:** job 5 is DONE (#305 merged; #307 is a duplicate of one of its nine and is to be CLOSED, not merged). Job 7 is DONE (#309 merged): the agent that opened #305 stops job 7. Job 13 is dropped. The agent that opened #306 now has: job 1 (#306, see the review in REPAIRS), 3b, 11, 12. The agent that opened #305 now has: job 4 (the sample numbers), 9, 10.

Job 2 is done (Fable, on main). If you find work of yours that overlaps the other agent's, stop and say so instead of finishing it. Hand each job back when it is finished, not in one bundle at the end.

## The rules for every job

1. **No build, no Release, no 2-fer run, no fetch from an agency server.** Work from saved files.
2. **Look first.** Name the existing tool you read and why it was not enough. Fix or switch on what is there.
3. **One draft pull request per job.** A change that moves a rules fingerprint needs its changelog line and a scope entry, and merges only after Fable's read.
4. **Numbers from real parks.** Say what each test ran on: invented parks or real saved data.
5. **One job at a time,** in the order below. Run the full test gate once per job, at the end.
6. **You have no KPC-Store access, by the owner's rule.** Anything there is Opus's.
7. **The graded sample is private.** The owner can hand you `KPC-sample-19-Nov-pass1-answers.zip`. Use it to count; never put a sampled park's name or number in a public file, test or pull request. Counts only.

## Job 1. The size check (you have this)

Spec: `REPAIRS.md`, "SIZE CHECK, the real cause". In short: one missing file (`data/acres.json`) keeps three size tools dead; hold must be reachable from the switch file; use the measured outline; limit 0.33 to 3 times the official size (holds 91 parks today, list given to the owner). Before the file appears, read what `kpc_join_check.py` does with it.

## Job 2. DONE by Fable, 20 Nov 7:40 AM. Do NOT start it. (A fault in the fill step)

Fixed on main and proved on the real release files: see `REPAIRS.md`, "FIXED: the fill step". What follows is the old text.

Found by Opus today. `kpc_master_fill.py`, about line 282: the national Army Corps download of 11 Nov is recorded once in `raw-manifest.json`, so every state's piece of it counts as "already applied". Yet no saved copy holds a single `sgide` row. Four hand files (AL, AR, CA, NE) are skipped because of it.
- Fix the check so "applied" means the copy really holds the rows.
- One test with a made-up manifest, and one count on the real files: how many hand files does the fault skip today?
- Do not run the fill for real. The Army Corps layer also has a licence question (job 3).

## Job 3. Licence readings for five layers (research, no code)

The fill step refuses 19 parks with "no licence or terms recorded", and the store and KPC-Links disagree on a sixth layer.

| Layer id | What it is | Parks waiting |
|---|---|---|
| `dcnps` | National Park Service units in DC | 4 |
| `sggaf` | a Georgia state layer | 6 |
| `dnrsf` | Michigan DNR state forests | 6 |
| `usaceproj` | Army Corps projects (Mississippi) | 3 |
| `sgide` | Army Corps recreation areas (national) | DONE by Fable 20 Nov: the Corps' page says "No License Provided / Request permission to use". The owner decides. Do not redo |

For each: find the agency's own terms of use or licence statement for that data, give the address, the date read and the exact sentence that allows or forbids republishing. Put the five readings in one table for the owner. He accepts or refuses each; only then does anyone write a licence row or his acceptance in `data/outlines/hand/owner-licence-acceptance.json`. Do not write those files yourself.

## Job 3b. Hold the Army Corps layer until the owner has permission (small; before the build)

The Corps' page for this layer says "No License Provided / Request permission to use" (read by Fable, 20 Nov). The owner pointed at that line (7:41 AM): we do not have permission. KPC-Links' licence gate passes the layer anyway, and since the fill-step fix (efe36340) the next fill would merge it into 22 more public saved copies.
- Make the gate refuse `sgide` (address `.../usace_recreation_areas/FeatureServer/0`) with the reason "no licence on the agency's page; permission not yet given", the same way it refuses a layer with no terms recorded. Use the existing licence table or gate; do not write a second one.
- One test: a hand file of that layer is refused at the fill; another layer's is not.
- Count from the release files, change nothing: which public saved copies already hold `sgide` rows (Fable counted 13 states on 20 Nov: IL IN KS MS ND OH OK OR SD TN TX WA WV). Taking them out changes public files, so that waits for the owner's word.
- It comes back with one line when the owner records permission.

## Job 4. Where the wrong joins really come from (the biggest one)

Counted by Fable today on the 300-park sample, by the kind of layer each record came from:

| Layer kind | Wrong records | Of |
|---|---|---|
| The national PAD-US layer and other national layers | 16 | 586 (2.7%) |
| State layers marked "owned" | 8 | 1,596 (0.5%) |
| State layers marked "compilation" | 5 | 838 (0.6%) |

Across all keys today: 25,612 joined records on 10,353 parks come from the national layers.

So the national layer joined by name is the largest source of wrong land, about five times the rate of state layers. An earlier guess, that "boundary line" layers were the main cause, is NOT what these counts show: they are a few small layers (`sgmnb`, `mid`, and New York's `sgnyc`), real but minor.

The job:
1. On the sample, find what separates the wrong national-layer joins from the right ones, using fields the saved copies already hold (designation type, manager, owner, acres, distance from the pin). Look at the builder's existing kind test and agency test before proposing anything.
2. Write a one-page rule sheet: what counts, what does not, what happens when unsure, 5 to 10 real cases with the names removed.
3. Give two numbers for the rule on the sample: wrong records it catches, right records it would take away.
4. Stop there. The owner rules on the sheet; only then is anything built.

## Job 5. Plain wrong cases, fixed by a saved "no" with evidence

- Nevada US-2635 (a state park joined to the 321,709-acre recreation area record `fsod68`).
- The 8 rows and the 12 disagreements listed in pull request #296.

Each needs: who decided, the official source, what it shows, the date. Follow `.claude/notes/key-quality.md` on saved answers by evidence. The release guard already refuses Nevada until US-2635 is done.

## Job 6. One list per switch that goes on at the build

From saved files only: for D5 (leased land never joined by name) and the piece rule, the parks that would change if the switch were on. One file each. Hold-on-error and saved-answers-say change no park.

## Job 7. Make the test gate honest

Main's gate is red and `tests/known-fail-main.txt` is from 7 Nov, so "no new failures" leans on an old list. For each test failing on main today: is the test wrong, or the code? Fix the test or list it with a one-line reason and today's date. No rule file.

## Job 8. The wiring check: files a bot reads that no bot delivers

Fable scanned 481 bot files in both repos: 29 files are read by some bot, exist nowhere on main, and have no clear writer. The list is in `REPAIRS.md` under "Wiring check". Two are confirmed dead: `data/acres.json` (job 1) and `data/status/quality/verdicts.json` (the Release refuses every state without it and nothing writes it).

For each of the others: read the code and say which it is: a writer the scan missed, a file a person fills in, a tool nobody uses any more, or a dead link. For a dead link, one line: who should write it, or which reader should be retired. Build no new bot; the owner decides on each.

## THE REVIEWS' MAIN FINDINGS THAT HAD NO OWNER (added 20 Nov 9:05 AM; owner: "very little of that fixes the main issues found in 3 reports")

He is right: jobs 1 to 8 covered 4 of the 16 open findings (R1 to R16 in `REPAIRS.md`, each with the report and finding number). These four are the code fixes the reports asked for that nobody had. Draft pull requests, no build, one owner each, after your current job.

### Job 9 (the agent that opened #305). The builder still saves a state after an error (R6; Claude review F10 and F14)
#295 fixed ONE of five places where the US key builder carries on after an error. Fix the other four the same way (behind the existing switch `KPC_HOLD_ON_PASS_ERROR`, or say in one line each why a place must not hold). Also: where a rule's data file is missing, the builder treats it as "no rule" and carries on; make a missing rule file stop that state. One test per place.

### Job 10 (the agent that opened #305). Saved answers that go wrong quietly (R4; Grok F7, Claude F5)
(a) A saved "no" names a record id; after a layer refresh renumbers the record, the "no" no longer applies and the record joins again (Arkansas US-1080). Make a "no" follow the record by its fingerprint, the way a saved join already does. (b) 15 parks hold one record under both join and no: list them and fix each saved answer with its evidence (the list is `S6b-297-join-and-no.csv` from the outside review). Count on today's saved keys how many answers each fix touches.

### Job 11 (the agent that opened #306). The drop guard only sees a lost outline (R7; Claude F7, Grok F4)
`kpc_key_drop_guard.py` counts a park as lost only when it goes from joined to nothing. It misses a park whose records were swapped for others, one that gained land it should not have, and one that quietly shrank. Add those three as REPORT lines first (no hold), with the count each would give between the released key and today's key. O9 on the checklist is the same report: this job closes it.

### Job 12 (the agent that opened #306). Two side paths to public files skip the gates (R11; Grok F17)
Read finding F17 in `KPC-pipeline-review-2026-11-19.md` (the keeper's asks, and the display copy that is switched off). For each path: either it goes through the same gate as a Release, or it is switched off in code so a GitHub switch alone cannot open it. One test each.

### Job 13. DROPPED by the owner, 20 Nov 9:06 AM. Do NOT do it. #305 is merged. (Was: the second pass on #305's nine saved "no" answers)
The club's rule (key-quality.md section 15): a saved answer merges only after a second pass, by someone who did not write it, agrees. #305 was written by the other agent, so this one is yours. For each of the nine parks (US-2635, US-3933, US-5154, US-7461, US-7462, US-7578, US-7581, US-9202, US-12233): open the official pages named in its `evidence`, read them yourself, and say AGREE or DISAGREE with one line of what the page shows. Do not read the first agent's reasoning before you have your own answer. Hand back one table. No code.

NOT given to you, and why: R8 (outlines rebuilt from the key) happens only at the one build; R2 (rules switched off) go on at the build with the lists of job 6; R3 (#296) waits for the owner's answer on short names; R9 (old 2-fer rows) is the owner's call; R12 to R14 are in the private store (Opus); R16 (cost) is the owner's bot list, already acted on.

## What Fable does

Reads each draft and the rule sheet, checks your numbers against the repo, and says pass or not yet in one reply. Fable did not write these, so the read is independent.
