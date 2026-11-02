# Inbox: chat 10 (HQ automation), Nov 2, 2026

You carry most of the rollout: steps 1, 4, 5, 6, 7, 8 of PLAN.md, and you review the others' steps.

## Before every push

- Take a FRESH clone; KPC-Data history was restarted this morning. Never push from an old checkout. Never force-push.
- Run `git apply --check <patch>` first.
  - If it passes, apply the patch.
  - If `git apply -R --check` passes instead, the patch is already in. Skip it and say so.
  - If neither passes, stop and tell chat 10.
- One patch, one commit, with the patch name in the message.
- Patches are in this folder under `patches/`. Paths below are relative to this folder (`H=/workspace/kpc_handoff_nov2`).

## Do, in this order

0. **Test build.** Apply the full stack to a fresh clone and run `python3 -m pytest -q $H/tests`. Expect 66 passed and
   1 skipped. If anything else happens, stop.
1. **G1** (both repos, the same file in each):
   ```
   cd KPC-Data  && git apply --check $H/patches/G1-KPC-Data-watchdog-restart-inputs.patch  && git apply $H/patches/G1-KPC-Data-watchdog-restart-inputs.patch  && git commit -am "G1: watchdog restarts send the schedule's inputs" && git push
   cd KPC-Links && git apply --check $H/patches/G1-KPC-Links-watchdog-restart-inputs.patch && git apply $H/patches/G1-KPC-Links-watchdog-restart-inputs.patch && git commit -am "G1: watchdog restarts send the schedule's inputs" && git push
   ```
2. **G4 + G5** (KPC-Data): `G4-KPC-Data-key-doctor-every-release-run.patch`, then `G5-KPC-Data-waiting-tidy-docstring.patch`.
   Use separate commits.
3. **G7** (KPC-Links): `G7-KPC-Links-save-by-overwrite-everywhere.patch`. This moves 34 files onto the save-by-overwrite helper.
   Wait for 3 real runs, then check that each log says `saved (overwrite`.
4. **G8** (KPC-Data, then KPC-Links): `G8-KPC-Data-loud-hidden-failures.patch`, `G8-KPC-Links-loud-hidden-failures.patch`.
   - These are large (64 and 46 files).
   - KPC-Links needs G1, G2 and G7 first. KPC-Data needs G1, G3, G4 and G5 first.
   - If chat 2 (G3) or chat 3 (G2) are not done yet, wait for them.
5. **G9** (both): `G9-KPC-Data-spread-schedules.patch`, `G9-KPC-Links-spread-schedules.patch`.
6. **G11** (both): `G11-KPC-Data-restart-as-the-missed-schedule.patch`, `G11-KPC-Links-restart-as-the-missed-schedule.patch`.
7. Help chat 3 with **G6** only after Brandon's OK (DECISIONS.md #7).

## Leads for you (not patches)

- **Held build id `f3d48d30899`** (DECISIONS.md #9).
  - Look at **kpc-boundary-check.yml** in KPC-Links. It rebuilds US key states with `kpc_us_key.py` under the us-key
    lock, with no freeze check and no build stamp.
  - Until G8, a crash there was hidden: `| tee ... || true` reports tee's status, not the script's.
  - It may be what changed the held build. Compare its run times with the stamp's time.
- The build-id stamp step in **kpc-us-key.yml** (`kpc_key_freeze.py stamp`) also hid its own failure until G8.
- Delete the branch **test-keyfix-0102** in KPC-Links by hand, but only after Brandon's OK (DECISIONS.md #16).

## Needs Brandon's OK (do not decide yourself)

- `KPC_SAVE_RED` (#8)
- posting-bot restarts (#12)
- G6 (#7)
- the branch delete (#16)

## Report back (in your inbox, times in CST)

- The commit id per patch, and the `--check` result for each.
- **G7:** links to 3 runs that say `saved (overwrite`.
- **G8:** after 24 hours, the list of new `::error` / `::warning` notices. They are real problems that were hidden before.
- **G9:** whether the Actions list shows any two runs of one repo starting in the same minute. KPC-Data has 8 known ones,
  listed in reports/G9-schedule-collisions.md.
- **G11:** one watchdog restart whose inputs show `as_schedule`.
- What you found about `f3d48d30899`.
