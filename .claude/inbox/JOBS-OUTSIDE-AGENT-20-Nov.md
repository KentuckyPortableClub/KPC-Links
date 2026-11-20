# Jobs for the owner's outside agent (20 Nov 2026, 7:10 AM Central)

From Fable (the reviewer). The owner asked for you to take more of the key problems, not only the size check. You are the ONE owner of each job below; no other chat starts them. Read `HANDOFF-20-Nov.md` in this folder first for the rules and the state of things.

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

## Job 2. A fault in the fill step (small)

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
| `sgide` | Army Corps recreation areas (national) | 6; the store says not publishable, KPC-Links' gate passes it |

For each: find the agency's own terms of use or licence statement for that data, give the address, the date read and the exact sentence that allows or forbids republishing. Put the five readings in one table for the owner. He accepts or refuses each; only then does anyone write a licence row or his acceptance in `data/outlines/hand/owner-licence-acceptance.json`. Do not write those files yourself.

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

## What Fable does

Reads each draft and the rule sheet, checks your numbers against the repo, and says pass or not yet in one reply. Fable did not write these, so the read is independent.
