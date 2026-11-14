# 2-fers from the outline store (prep, switch OFF)

KPC owner, 2026-11-13. Status: prepared, not wired in. Nothing runs it, so no 2-fer answer changes and no rules hash moves.

## What it is

`.github/scripts/kpc_fers_store.py` lets the 2-fer bot take park outlines from the outline store (about 2 m detail, one
gzip piece per park) instead of downloading them from agency map servers. Owner decision "one door in": bots do not download
boundaries; a park the store does not have is held and flagged, and only the store filler fetches it.

## The switch

`KPC_FERS_FROM_STORE` (default off). With it off, `install()` does nothing and `kpc_fers.py` runs exactly as today.
With it on (switch-over PR only), for one process:

- `download()` reads the store: the outline of every record the key joins, in the key's order, with the same read-time rules
  as today (use=false records left out and listed, rings of 2 points or fewer dropped, part boxes applied). A park with a
  missing record, a park not in the store, an area store that is missing or older than `KPC_FERS_STORE_MAX_DAYS` (45), or a
  WDPA-looking record is held with the reason, never downloaded. The list goes to `data/fers/store-missing-<tag>.json`.
- `saved_us()` returns nothing: the national saved key copy (measured: about 2.4 GB in memory, loaded in every pass) is not read.
- `saved_ca()` reads the store for Canadian parks.
- `live_load()` reads nothing: the bot's own saved-live copy is not a second door.
- Point circles (100 ft around the agency's official point) and picture traces are made by `kpc_fers.py` exactly as today.
- Kentucky (own files) and the world (world 2-fers wait) are refused.

Settings: `KPC_FERS_STORE_DIR` (default `store`: `index-<AREA>.json` or `index.json` plus the area files it names).

## Commands (no network)

- `kpc_fers_store.py check <store_dir> <AREA> ...`: read and verify every park; points, memory estimate, age.
- `kpc_fers_store.py diff --old <today's file> --new <store run's file> --out <stem>`: the change list a person signs
  before anything new is published (ids, names, kinds, statuses only; no shapes). Old answers stay until then.
- `kpc_fers_store.py run`: install with the switch on, then `kpc_fers.main()` (same environment as `kpc_fers.py`).

## Switch-over (a later PR, bundled with the shared matcher switch-over)

Adds the hook to `kpc_fers.py`, moves `kpc_fers_store.py` from `NOT_RULES` into the 2-fer `RULE_FILES`, rewords the held-park
text, and lets `find_spots` keep outlines packed (`LazyOutlines`). That PR moves the 2-fer rules hash once and is declared in
`docs/key-rules-change.txt` with a scope entry in `.github/fers-rule-scope.json`.

Tests: `tests/test_fers_store_nov13.py` (synthetic store; no network).
