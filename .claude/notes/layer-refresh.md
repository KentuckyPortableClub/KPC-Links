# Keeper asks, the old bot fetches: how whole layers get refreshed

Owner's call, 16 Nov 2026, 9:37 PM Central: *"write a plan using keeper since it is doing the checks that when
something out of date it request it ... put that somewhere we won't forget it."*

**Status: PARKED.** Nothing is built. Every layer we hold was downloaded in the last few days, so nothing is
stale and there is nothing to refresh yet. Pick this up when a real layer is actually out of date, or before
the two monthly jobs are ever switched back on.

## The problem

The whole-layer saved copies live on the `boundary-cache` release of KPC-Links. That is what the answer keys
read in store mode, and it is the reason a key rebuild takes minutes instead of hours.

Two jobs refill it:

| job | when | what it does |
|---|---|---|
| `kpc-geo-cache.yml` (KPC saved shapes) | 3rd of the month | re-reads every US state's layers, `GEO_CACHE_MODE: refresh` |
| `kpc-world-cache.yml` | 4th of the month | the same for world countries |

`refresh` means "always fetch, and save" — blind. It re-downloads a layer whether or not one line of it moved.
589 layers (264 US, 109 Canada, 216 world), 670 job-minutes in November, records paged 200 at a time.

Fable's own review of 22 Oct is on the workflow's first lines: *"nearly all the time is re-downloading the same
geometry."* The saved-copy release was his fix for that. The monthly cadence was never his ask — it was just a
cadence picked so the copies would not rot, and nobody checked it against how often layers really change.

## What already exists (do not rebuild it)

The keeper already does the checking, and has since it came online.

- `store/layers-seen.json` on the `store-data` branch of KPC-Store. Per layer: record count, **ETag**,
  **lastEditDate**, `last_modified`, `terms_sha`, `last_changed`, `last_checked`, host, `gone` list.
- Settings in `keeper/keeper.py` DEFAULTS: `cycle_days: 28`, `max_layers_checked_per_run: 40`,
  `catch_up_after_days: 31`.
- Runs daily for US + Canada (`kpc-store-keeper.yml`, 07:41 UTC), Thursdays for the world
  (`kpc-store-keeper-world.yml`, 05:17 UTC). The date picks the slice.
- `keeper.py` already reports `result='changed', why='edited on the server (<old> -> <new>)'`.

First 14 layers walked, 16 Nov: **14 of 14 gave an ETag**, 6 of 14 gave a lastEditDate, 6 gave Last-Modified,
2 had already been caught changing. The ETag is the one that matters — the edit-date route alone would cover
about 40% of layers, the ETag covered all 14. At 40 a day the 373 US + Canada layers are walked in about ten
days; the world at 40 a Thursday takes about six weeks.

**The gap is one wire, not a new bot: the two cache jobs never read `layers-seen.json`.**

Also already in the keeper: `keeper/gis_hunt.py` and `keeper/gis_list.py`, with `data/state-gis.json` from
KPC-Data.

## The plan

1. **Keeper writes a request, it does not fetch.** When its walk finds a layer whose ETag or lastEditDate
   moved, it adds one row to a small request file (layer address, area, what moved, the date). Nothing else
   changes about the keeper, and the keeper never starts anything itself.
2. **The old cache bot reads the request file and fetches only those layers.** Its monthly blind schedule comes
   off; it runs when there is a request to serve (and by hand).
3. **Wire the old bot, do not build a new one.** It already has the fetch code, the per-host pacing, the
   release upload, and the `save-check` guard that refuses a copy holding fewer records than the one it would
   replace. A new fetcher would have to earn all of that again.
4. **Whole layers stay out of the store repo.** The store room is for joined outlines. Raw layers are big and
   KPC-Store is private; the public `boundary-cache` release is the right shelf and it is free.
5. **A layer nobody has walked yet is not "unchanged".** Until the keeper has a first reading for a layer, that
   layer is unknown, not fresh. The request file says which.

## Not decided — the owner rules on these before anything is built

These are the grey areas. RULES FIRST: this decides what gets refreshed, so the rule sheet comes before the
code.

- **R-LR1. How stale is too stale** for a layer whose ETag never changes? Six months? A year? Never, as long as
  the ETag holds? (An ETag that never moves can mean the layer never changes — or that the server always sends
  the same one.)
- **R-LR2. A layer that is dying.** When a service is about to retire (`retired-layers.csv`), our copy becomes
  the only one left. Is the ~110 m saved copy good enough to be the permanent record, or does a layer we think
  is going away get one full-detail save first?
- **R-LR3. Changed layer: whole or part?** When a layer moved, do we re-read the whole layer or only the
  records whose own ids changed? The keeper holds a record count per layer, so a count that moved says
  something was added or removed, but not which record.
- **R-LR4. Who may ask.** Only the keeper's own walk, or may a chat or a report add a request row by hand?

## Before the crons are ever switched back on

`kpc-geo-cache.yml` fires on the 3rd and `kpc-world-cache.yml` on the 4th. Until this is wired, those two will
re-download layers that are days old. Either switch the schedules off and keep the by-hand button, or wire
step 1 and 2 first. Switching a download off decides nothing, so it needs no rule sheet.

KPC owner, 2026-11-16
