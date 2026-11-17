# The owner's PC 2-fer runner

The club's 2-fer bot and every rule file it reads live in this repository. This folder holds the
part that does **not**: the small tool that runs them on the owner's PC, in the same order the
GitHub job does.

It was kept only on that PC until 2026-11-16. It is here now so it has a history — a copy on a
drive tells you what a file says today, not what changed or when.

| file | what it is |
|---|---|
| `kpc_pc_run.py` | the runner. Drives the club's own code; holds no copy of any rule |
| `*.bat` | the numbered steps the owner clicks |
| `HOW-TO.md`, `START-HERE.txt` | his own instructions |

**Not here, on purpose:** `pins.json` (which commit to run, and the four rules hashes it must
produce), `settings.json` (paths on his PC) and `pinned/MANIFEST.json` (the sha256 of every
shipped script). Those are his machine's settings, not club code, and `pins.json` moves whenever
a pin moves. They are in his own backup.

**This folder is a record, not the live copy.** The runner on his PC is the one that runs. Changing
this file does not change his, and changing his does not change this. Keep them together by hand,
the same way the spot relay in `tools/kpc-spot-relay.js` works.

## What the runner does that is easy to get wrong

- A **world** run lays KPC-Data's RELEASED world key over this repo's `data/world-key` before the
  passes. The released key and this repo's newest build disagreed in 85 of 93 countries, and the
  PC outline store is built from the released one.
- **"Done" comes from each pass's receipt**, not from exit codes. A run that stopped on its first
  line used to exit 0 and look finished.
- It **records which areas finished**, so a run cut short carries on next time instead of starting
  at the first area again. Progress is per request: the exact set of areas asked for, plus the
  target.
- In a store run **pass 2 does nothing** — every pass reads the same store outlines, so pass 3 does
  that test on its finer grid. The loop still runs 1, 2, 3, 5 so nothing else needed changing.
