# Keeper asks, the old bot fetches: how whole layers get refreshed

Owner's call, 16 Nov 2026, 9:37 PM Central: *"write a plan using keeper since it is doing the checks that when
something out of date it request it ... put that somewhere we won't forget it."*

**Status: RULED AND BUILT, NOT RUNNING (17 Nov).** The cache side is KPC-Links #247 (merged; by-hand button only, knobs default to the rulings); the keeper
side is a change file to apply in KPC-Store. All four grey areas are ruled, below. Was: PARKED, nothing built. Every layer we hold was downloaded in the last few days, so nothing is
stale and there is nothing to refresh yet. Pick this up when a real layer is actually out of date, or before
the two monthly jobs are ever switched back on.

## Built, off (Nov 17, Handoff 3)

- Cache side (KPC-Links): `.github/scripts/kpc_layer_refresh.py` reads the request file `layer-requests.json` (an asset on the
  `boundary-cache` release) and names the areas to re-read. `kpc-geo-cache.yml` and `kpc-world-cache.yml` got a `from_requests`
  box on their by-hand button; ticked, they re-read only those areas with their own fetch, pacing, `save-check` and upload. No
  request file, an unreadable one, or no row that may be served = nothing is fetched. No schedule block.
- Keeper side (KPC-Store): a change file, `docs/layer-refresh-keeper-change.md`, for the owner to apply. Not applied.
- The four rulings (RULED 17 Nov) default in both cache workflows; a repo variable overrides: `KPC_LR_STALE_DAYS` (R-LR1), `KPC_LR_DYING` (R-LR2), `KPC_LR_CHANGED_READ`
  (R-LR3), `KPC_LR_WHO` (R-LR4). Unset = nothing extra; with R-LR3 unset every changed-layer row is held, so the wire serves
  nothing until the owner rules. What each value does: the top of `kpc_layer_refresh.py`.
- The save unit is the area file (US-XX, W-XX, CA-ALL): a request for one layer re-reads its whole area once. A re-read of only
  the requested layer inside an area needs a change to the key scripts (rules hash) and is not built.

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

## RULED by Brandon, 17 Nov 2026, 4:30 AM Central

All four grey areas are closed. These are the rules now; the knobs in KPC-Links #247 get set to match.

- **R-LR1. How stale is too stale.** A layer that gives us a change DATE we can read (`lastEditDate`, or
  `Last-Modified`) is trusted: no timer, it is re-pulled only when that date moves. A layer that gives us no
  date is re-pulled **every 6 months** to be safe. Knob `KPC_LR_STALE_DAYS` = 180, applied to dateless layers
  only.
  - HQ's reading, say so if it is wrong: an **ETag is not a date**. It says *that* a layer changed, not *when*.
    So a layer with an ETag but no date still gets the 6-month pull. On the first walk 14 of 14 layers gave an
    ETag but only 6 of 14 gave a `lastEditDate` and 6 a `Last-Modified`, so this is the common case, and it is
    the safe side: at most 2 pulls a year for those, against 12 a year for all 589 under the old blind monthly.
- **R-LR2. A layer that is dying.** Before a service goes dark we take **one full-detail copy** and archive it.
  The ~110 m saved copy is not good enough to be the permanent record. Knob `KPC_LR_DYING` = on.
- **R-LR3. Changed layer: whole or part?** Re-read the **whole layer** for now. Reading only the changed
  records means editing the key scripts, which sit inside the rules hash. Brandon: *do it properly later* -
  so it goes on notes/ideas.md, not into this build. Knob `KPC_LR_CHANGED_READ` = whole.
- **R-LR4. Who may ask.** The keeper's own walk, **and a chat or a report may flag a layer as stale** and add a
  request row. Knob `KPC_LR_WHO` = keeper + chat. The row carries who asked (`by`), so a hand-added row is
  always told apart from the keeper's own.

**Q2, also ruled: the keeper removes its own served rows.** Not the cache bot (that would mean giving a public
bot write access to a private file) and not by hand. The keeper drops a row once the area's saved copy on the
release is newer than the row's date. This is a change to the keeper, so it goes in the KPC-Store change file
with the rest.

**Q1, the remaining blocker:** the public request file reaches the KPC-Links release through the keeper, using
the secret `KPC_LINKS_DISPLAY_TOKEN` in KPC-Store. Brandon has a fine-grained token and added KPC-Links to it on
17 Nov; it still has to be pasted into KPC-Store's Actions secrets under that name. Until it is, the cache bot
finds no request file and fetches nothing. The same missing-secret finding blocks `KPC_DATA_WRITE_TOKEN` and
with it the public shelf (ledger 45).

## Before the crons are ever switched back on

`kpc-geo-cache.yml` fires on the 3rd and `kpc-world-cache.yml` on the 4th. Until this is wired, those two will
re-download layers that are days old. Either switch the schedules off and keep the by-hand button, or wire
step 1 and 2 first. Switching a download off decides nothing, so it needs no rule sheet.

KPC owner, 2026-11-16
