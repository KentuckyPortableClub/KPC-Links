# 2-fers from the outline store (prep, switch OFF)

KPC owner, 2026-11-13. Status: prepared, not wired in. `kpc_fers.py` does not call it, so no 2-fer answer changes and no rules
hash moves.

## What it is

`.github/scripts/kpc_fers_store.py` lets the 2-fer bot take park outlines from the outline store (about 2 m detail, one gzip
piece per park) instead of downloading them. Owner decision "one door in": bots do not download boundaries; a park the store
does not have is held and listed, and only the store filler fetches it.

## The store it reads

Index contract `kpc-outline-store-index/3` (outline store tool full 3). Another version is refused (the area is not ready). Only the
per-area `index-<AREA>.json` is read: the combined `index.json` keeps one entry for a park that sits in two areas. Each area file
must match its sha256 and size in the index before use. A park with tracts in two area files is assembled from both. Per record:
`publishable` (trusted only with `publish_basis` verified-row or owner-confirmed), `licence_class`, `publish_basis`, `wdpa_derived`
(must be false; a scan of every text value is a second check, field names are not read), `private_reason` (kept for the owner and
the club-room tag, never shown). Test fixture: `tests/fixtures/fers-store-v3/` (synthetic squares written by the tool itself).

## The switch

`KPC_FERS_FROM_STORE` (default off). Off: `install()` does nothing and `kpc_fers.py` runs exactly as today. The Kentucky and
world runs never use the store: with the switch on they run as today (downloads included). On, for a US + Canada run:

1. **Area gate, before pass 1.** Every member state needs a readable store no older than `KPC_FERS_STORE_MAX_DAYS` (45). If one
   is missing, stale, of another format or damaged, the run stops with exit 87 before anything is read or saved; the area keeps
   its previous files.
2. **Memory gate.** From the store index's own point counts: the bot's base, a tile floor, the packed store and the unpacked
   outlines must fit `KPC_FERS_STORE_LIMIT_MB` (3000, the whole process). Otherwise exit 88 with a plain reason. Until
   `kpc_fers.py` keeps its passes lazy (switch-over), the gate counts every outline as unpacked.
3. **Outlines.** `download()` returns a `LazyOutlines` map: each park checked once (checksums, every joined record present and
   usable), kept packed, unpacked on use with a points budget (`KPC_FERS_STORE_BUDGET`, 2,000,000).
4. **Held parks** (with the reason; never half a park, never a download): not in the store, a joined record missing or with no
   usable ring, WDPA-looking text anywhere in the record or park, any damage to the index or the piece, and on a PUBLIC store
   (`KPC_FERS_STORE_KIND=public`, the default) any record not marked `publishable` ("needs the private store").
5. **No live pair vanishes.** On every save, each live row of the previous file that the run did not make again comes back as a
   row: "not sure: held: <why>" when a park of it is held, otherwise "dropped: not found again ..." for the change list.
6. **Club room only.** A row that used an outline whose record is not publishable is tagged `club_room_only`.
7. `saved_us()` keeps only the Wild and Scenic corridor records of the saved key copy (the whole national copy is about 2.4 GB
   in memory); `live_load()` reads nothing (no second door).
8. `data/fers/store-missing-<tag>.json` is written on every store run: one row per area and every held park.

## Commands (no network)

- `kpc_fers_store.py check <store_dir> <AREA> ...`: read and verify every park; points, memory, age.
- `kpc_fers_store.py fit <store_dir> <AREA> ...`: the memory gate alone (exit 88 when it will not fit).
- `kpc_fers_store.py diff --old FILE --new FILE --out STEM`: the change list a person signs before new answers are saved.
- `kpc_fers_store.py run`: only with the switch on (refuses otherwise): install, then `kpc_fers.main()`.

## Not in this module (switch-over and later)

The hook and the lazy passes in `kpc_fers.py`; moving this file into the 2-fer `RULE_FILES` (one declared rules-hash move);
the matcher "join under review" rule (`join_review()` exists, not wired; keep and tag, hold only on shared records, is the recommendation, not yet the owner's decision); `pad_closed()` and the trail-status reads, which still
go out live; the KPC-Data workflow step that fetches the store.

Tests: `tests/test_fers_store_nov13.py` (synthetic stores; no network).
