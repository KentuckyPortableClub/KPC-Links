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
9. **No network at all (the store is the only door).** `pad_closed()` (the live PAD-US closed-area read inside the decide step)
   asks for nothing. An area spot whose closed-area check could not run is NOT SURE ("closed areas not checked"), never
   confirmed, until the store carries the closed areas. Every fetch of `kpc_fers.py`, `kpc_owned.py` and the answer cache is
   refused before it is sent (live water: saved tiles only, else NOT SURE; ownership tiles; trail status; layer dates; bundle
   answers), and the process's sockets are shut.
10. **The write guard (fail rather than leak).** Every file the bot writes goes through `save_json` -> `_save_json_raw` (the two
    other writers, `live_save` and `_wsave`, are turned off in a store run); the store module guards that step and its own
    store-missing list. The run stops with exit 89, writing nothing, rather than put any of these into a public file: a row
    marked `club_room_only` (with or without its shape, width, centre or area), any mention of a park whose outline came from
    records that are not publishable, a 2-fer row with a park outside the US and Canada, or the never-released build
    `US-42797939226` (any file). A **private** store run (`KPC_FERS_STORE_KIND=private`) writes every file into
    `KPC_FERS_PRIVATE_OUT`, which must be set and outside every git work tree (else exit 89 before anything is read): all its
    files are club room only. On a public store no unpublishable or WDPA-derived record is read at all (the park is held).
    `kpc_fers_publish.py` (the only path from 2-fer data to the public site) also refuses a club-room, world or blocked row.

11. **Store format 4 (store tool 3.5).** The reader takes index `kpc-outline-store-index/3` and `/4`; any other version is
    refused (fails closed). Only records whose `geometry_kind` is `area` (absent = area) make a park's outline. `line` records
    give a line park its line (the open path, exactly as stored: never closed, never buffered into an area) and the bot tests it
    with today's line rule, unchanged: 100 ft, i.e. 25.48 m from a centre line with the station 5 m inside the other park, or
    30.48 m from a US river's bank where a water area covers the line, along a stretch of at least 25 m. What the rule needs to
    know about the park (trail or river, who drew it, NHT type, which pieces are water) still comes from `data/trails`. A line
    park whose line the store lacks is held. A park with area records is tested as an area (its line records are not used).
    `pin` records and unknown kinds are never used. The counts go into the run report (`outline_store`) and the store-missing
    list: records left out, line parks read, live pairs on the 100-ft line rule.
12. **Water tiles from the store first** (`store/water/<AREA>/<i>_<jt>.json.gz`, the bot's own WATER_STORE tile form), then the
    bot's last good copy as today, else NOT SURE (never "no water"). Rows keep today's dated wording.
13. **Rivers with no bank data, behind one switch** `KPC_FERS_RIVER_NO_BANK` (store runs, US rivers, passes 2-3):
    `centreline` (default) = today (25.48 m from the centre line where no water area covers it). `tiers` = PROVISIONAL (the
    owner's Nov 14 ruling): 1 bank (every point of the stretch in mapped water: today's 30.48 m from the bank, solid); 2 the
    other park reaches the river centre line (counts); 3 a park edge runs along the river within `KPC_FERS_RIVER_HALF_M`
    (150 m) for 50 m, or 4 the park lies within `KPC_FERS_RIVER_CATCH_M` (250 m) of the centre line: "river candidate: needs
    bank shape" (never a 2-fer), each listed in the store-missing list's `river_bank_todo` for the bank store to fetch. Every
    river row says which tier decided it (`river_tier`). Canada and trails unchanged. The switch lives in this module (not a
    rule file), so no rules hash moves now; making it the rule in `kpc_fers.py`, or the switch-over moving this file into the
    2-fer `RULE_FILES`, moves the 2-fer (`fers`) rules hash cef323de4c9a.

## Output paths (traced 2026-11-14)

`kpc_fers.py` writes, all under `OUT` (`data/fers`; the private folder on a private store run) and all through the guarded
step: the spot files `<area>.json`, `reuse-p<pass>-<tag>.json`, `report*.json`, `looked-<area>.json` (park boxes),
`missing-<tag>.json`, `wdpa-internal-<tag>.json`, `same-outline*.json`, `ky-outline-drift.json` (Kentucky only). Direct writers:
`live_save()` (`saved-live-<area>.json.gz`) and `_wsave()` (water tiles), both off in a store run. `kpc_save` writes, at exit, `data/status/<bot>.json`
(changed file paths and dates); a private store run keeps its private files out of it. The answer cache writes only fetched answers (none in a store run). KPC-Data is a public repo, so every
file the workflow commits there is public.

## Commands (no network)

- `kpc_fers_store.py check <store_dir> <AREA> ...`: read and verify every park; points, memory, age.
- `kpc_fers_store.py fit <store_dir> <AREA> ...`: the memory gate alone (exit 88 when it will not fit).
- `kpc_fers_store.py diff --old FILE --new FILE --out STEM`: the change list a person signs before new answers are saved.
- `kpc_fers_store.py run`: only with the switch on (refuses otherwise): install, then `kpc_fers.main()`.

## Not in this module (switch-over and later)

The hook and the lazy passes in `kpc_fers.py`; moving this file into the 2-fer `RULE_FILES` (one declared rules-hash move);
the matcher "join under review" rule (`join_review()` exists, not wired; keep and tag, hold only on shared records, is the recommendation, not yet the owner's decision); PAD-US closed areas, ownership tiles and water
inside the store (until then those checks are NOT SURE in a store run); the KPC-Data workflow step that fetches the store.

Tests: `tests/test_fers_store_nov13.py` (synthetic stores; no network).
