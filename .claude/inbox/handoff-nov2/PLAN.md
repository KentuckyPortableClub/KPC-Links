# Rollout plan (Nov 2, 2026)

All times are CST. "Done" means it is live: the change is on main AND a real run (or the site) shows it working. A push alone
is not done.

## Before you start (every step, every time)

1. **Take a fresh copy.** KPC-Data's history was restarted this morning. Before every push:
   ```
   rm -rf /tmp/kpc && mkdir /tmp/kpc && cd /tmp/kpc
   git clone https://github.com/KentuckyPortableClub/KPC-Data.git
   git clone https://github.com/KentuckyPortableClub/KPC-Links.git
   ```
   Never push from an older checkout. Never force-push.
2. **Check before you apply.** Run `git apply --check <patch>` at the repo root.
   - If it passes, apply the patch.
   - If it fails, run `git apply -R --check <patch>`. If that passes, the patch is **already in**: skip it and say so.
   - If neither passes, main changed under the patch. **Stop and report it to chat 10.** Don't hand-merge.
3. **One step = one commit**, with the patch name in the message (e.g. `G7: save by overwrite everywhere`). That keeps
   every step easy to undo with `git revert`.

## Step 0: the test build (before anything goes to main)

On a fresh copy, apply the whole stack in order, without committing:
- KPC-Data: G1, G3, G4, G5, G8, G9, G11
- KPC-Links: G1, G2, G7, G8, G9, G10, G11

Then run the checks from this folder:
```
python3 -m pytest -q tests      # expects 66 passed, 1 skipped (the PDF build needs the Carlito/Caladea fonts)
```
The tests read their copies from `/workspace/fresh_nov2`. To test a newer copy, point `FRESH` in tests/test_g7plus.py at it.

Every workflow file must still load as YAML, and every `run:` block must pass `bash -n`; the tests check both.

**Success:** all green. **If not:** stop. Report the failing test to chat 10.

## The steps, in order

| # | What | Patch(es) | Who | Needs Brandon's OK? | Depends on |
|---|---|---|---|---|---|
| 1 | Watchdog restarts send the schedule's settings | G1 (both repos) | chat 10 | No | none |
| 2 | Honest User-Agent | G2 (KPC-Links) | chat 3 | No | none |
| 3 | Scrub the Google key from the documents bot + clean W-GB.json | G3 (KPC-Data) + tools/scrub_docs_keys.py | chat 2 | No | none |
| 4 | Key doctor on every release run; docstring fix | G4, G5 (KPC-Data) | chat 10 | No | none |
| 5 | Every save by overwrite (KPC-Links, ~30 workflows) | G7 | chat 10 | No (the red-or-not setting is in DECISIONS.md) | none |
| 6 | Hidden failures made loud (both repos) | G8 | chat 10 | No (notices, not red) | KPC-Links: G1, G2, G7. KPC-Data: G1, G3, G4, G5 |
| 7 | Spread the start times (both repos) | G9 | chat 10 | No | G8 is in (for a clean apply, follow the order) |
| 8 | Restarts run as the missed schedule | G11 (both repos) | chat 10 | No (posting restarts are in DECISIONS.md) | 1-7 |
| 9 | 2-fer layer / guide PDF / GPX / hours builder, all switches OFF | G10 (KPC-Links) | chat 8 merges; chat 2 runs the hours preview | Merging with the switches off: No. **Each switch: YES** | 5 (save helper) |
| 10 | Pages stop falling back to held keys | G6 (KPC-Links) | chat 3 + chat 10 | **YES** (51 world-key countries disappear until released) | none |

Do steps 1-4 one by one, checking each before the next. Steps 5-8 change many workflow files. Push each one alone, then
wait for at least one real run of 3 affected workflows before the next step.

## Success check per step ("done" = live)

1. **G1.** The next watchdog restart (the run's "Run name"/inputs page) shows the schedule's inputs. For example, helpers
   at 10:23 UTC shows `jobs=match`, and the waiting room shows `mode=release-approved`, not the dispatch defaults.
2. **G2.** The next kpc-ky-maps or link-check log shows the KPC User-Agent, not "Chrome"/"Safari".
3. **G3.** `grep -c AIza data/docs/W-GB.json` gives 0 on main (after the cleanup tool runs), and the next documents-bot run keeps it at 0.
4. **G4/G5.** Every scheduled waiting-room run has a key-doctor step and writes the resources report.
5. **G7.** In the next run of at least 3 converted workflows, the log says `saved (overwrite` and the commit is on main. A
   person's edit made in between is still there.
6. **G8.**
   - Any run with a `continue-on-error` step ends with "Report hidden failures".
   - A lost save shows `::error title=Save::`, a notice on the run page. The run stays green.
   - After 24 hours, count the new notices and report them (they are real problems that were hidden before).
7. **G9.**
   - The workflow files on main show the new crons, each with a `# G9 Nov 2: was ...` note.
   - Over the next day, the Actions list shows no two runs of one repo starting in the same minute (KPC-Data: 8 known
     pinned exceptions, all listed in reports/G9-schedule-collisions.md).
8. **G11.** The next watchdog restart's inputs include `as_schedule`, and its log takes the scheduled path. For example,
   the waiting room runs the release and the key doctor.
9. **G10.**
   - The workflow "KPC 2-fer and hours publish (off until GO)" is listed, and a hand start with the switches unset does nothing (all off).
   - With a switch on `preview`, the run's artifact holds the files and main is untouched.
   - It is "done" only after Brandon says "on" AND the site shows it: the 2-fer layer on the map, the hours on park pages,
     the new PDF/GPX downloads.
10. **G6.** A held world-key country no longer shows on the site. Released ones still do.

## Rollback

- Any step: on a fresh copy, `git revert <that step's commit>` and push.
- G7 without a revert: set the repo variable `KPC_SAVE_MODE=rebase` (the old way, still loud).
- G10: set the switch back to `off` (or delete the variable).
- G9: a revert brings back the old minutes. Nothing else depends on them.
- G11: revert G11 only; G1 still sends the inputs.
- After any revert, check that the next run behaves the old way, and post that in your inbox note.

## What to report back (each chat, in its inbox)

- Which patches went in, with their commit ids.
- The `git apply --check` result for each (passed / already in / failed).
- The run(s) you checked, with run links and times in CST.
- Anything that failed, and what you did about it (revert or not).
