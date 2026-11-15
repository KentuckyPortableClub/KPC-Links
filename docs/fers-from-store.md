# 2-fers from the outline store (wired in, switch OFF)

KPC owner, 2026-11-13; switch-over 2026-11-15. Status: `kpc_fers.main()` calls `kpc_fers_store.install()` right after the hard-end
clock is armed, only when `KPC_FERS_FROM_STORE` is on (off: nothing is imported and the run is exactly as before). This file and
`.github/fers-store-areas.json` are 2-fer rule files (fers rules d0064c860cba -> 2fe19a32e5eb, entry `2026-11-15-store-switch`).
No workflow turns the switch on yet (KPC-Store PR 2).

**Scope `none`, and a stamp only in store runs.** With the switch off no answer and no pair fingerprint changes, so an ordinary
run re-tests nothing (it reuses every saved pair answer). A store run adds the id `2026-11-15-store-switch` to the rule stamp of
every park of the areas it runs from the store (`install()` wraps `kpc_fers.rule_stamp`), so exactly those pairs are tested again,
once, on the area's first store run; later store runs reuse them as usual.

**The area list is a rule input.** `.github/fers-store-areas.json` stays in the 2-fer rules hash on purpose: `areas` and `world`
can make the bot read MORE from the store (another area, the world), not only less. So every edit of it (`areas`, `except`,
`world`) moves the fers rules hash and needs its own declared line in `docs/key-rules-change.txt` and an entry in
`.github/fers-rule-scope.json` (an `except` change usually with scope `none`: an excepted area simply runs the old path). It needs
no code change.

## Which areas (`.github/fers-store-areas.json`, KPC owner 2026-11-15)

- `"areas": "all-us-ca"`: every US state and Canadian province area the store holds (a list of area codes also works).
- `"except": []`: an area pulled back to the old path without a code change. A store run that names it leaves it out with that
  reason (it keeps its previous files; run it with the switch off). A run whose every area is excepted runs as before.
- US-KY never: the Kentucky run (REGION ky) reads Kentucky's own files (`ky_geom`, name-joined `src|NAME` ids, its own owner and
  drop rules); the store's US-KY area is keyed by layer record ids and the Kentucky name joins, so using it needs a crosswalk and a
  new Kentucky owner step: not a small change, left out on purpose.
- An area named for the run that the store does not hold (no index, another format, stale, damaged) is left out of the run with a
  plain reason (its row in `store-missing-<tag>.json`, a warning) and the run goes on for the other areas. No area left = exit 87.
  A run that names no area (STATES) is refused (exit 87): a whole-region store run could rewrite an excepted area's files. A
  broken list = exit 87. Parks filed under an area that does not use the store are held, never downloaded.
  The spot file of an area that does not use the store in this run (excepted, not held, stale; also a border area whose parks
  were only loaded as neighbours) is never rewritten by a store run: it stays as it was (counted in the report and listed by
  area code in `store-missing-<tag>.json`).
- `"world": "off"` (default): a world run never reads the store, exactly as before. `"on"`: a world run with the switch on reads
  world areas `index-W-<CC>.json` (record keys = the world key's record ids), and only as a PRIVATE store run
  (`KPC_FERS_STORE_KIND=private`; a public one exits 89): world 2-fers are club room only. Every guard stays: WDPA-derived records
  or WDPA-looking text are held, never read; the write guard and `kpc_fers_publish.py` refuse world rows in public files; a world
  area the store does not hold is left out with its reason. World 2-fers still need their areas in `.github/fers-ready-areas.json`
  before any world pair runs (unchanged). Lines and water tiles are not read from the store for world areas.

## Keep the old row (rule R11; DEFAULT for owner question 1)

A store run downloads nothing, so the PAD-US closed-area check (rule 10) and the ownership map cannot run. A live candidate row
that the store run would turn NOT SURE only for that reason keeps its old row, tagged `kept: not checked in a store run` (with
`kept_why` and `kept_on`). "Only for that reason": the closed-area check could not run and the rest of the land check said ok
(water checked from the store tile), or the row's status is `not sure: the agency ownership map did not answer`. A row the store
run decides (water only, dropped, any other not-sure reason, the water not checked either) is never kept, and an old row that was
not a live candidate is never brought back.
**Same spot only** (grade of #201): the old row is used only when it is the same spot: the old centre lies inside the new spot's
box (or the new centre inside the old row's box), the two boxes have the same size (width and height each within a factor of 2),
AND the size agrees within 25 % both ways (the larger at most 1.25 times the smaller: acres for an area row, metres of line for a
trail / river row). A spot that moved or changed size keeps this run's NOT SURE row (with `not_kept` saying why), and since its
last row is then NOT SURE, a later store run never brings the old candidate back. The rows carry no outline checksum, so this place
+ size test is the whole rule.
Passes 1 and 2 rewrite every row before pass 3 decides it, so the good copies wait between passes in a side file OUTSIDE the data
folder (the private folder, else `KPC_FERS_LIVE_DIR`/`cache/fers`, as `store-prev/<area>.json`), never in a row: a run that stops
after pass 1 or 2, a HardStop or a crash leaves no copy in `data/fers`. The final pass empties the side file. The write guard
refuses any public file with a `store_prev` copy in a row. Saved PAD-US answers are not used yet.
**A pair that is all water in the store tile** stays `not sure: closed areas not checked` (never kept). The store run cannot call it
`water only` by itself: rule 10 is checked before the water (a permanent no-entry area on the water, a dam security zone, cannot be
the spot, and main would then say `dropped: only inside an area closed to the public`), and the closed areas are not in the store.
**Names too (a second line of defence; the REF guard is the main protection):** on a public store run the write guard also
refuses a withheld park's NAME (from the store and the POTA pin list) in any text of a public file. Both the name and the text are
folded first (case, accents, hyphens, underscores, spacing and punctuation), and the name must appear as whole words. It is NOT
looked for when (a) a park that is not withheld has the same name (a public namesake: its rows and statuses name it freely), or
(b) it is not distinctive: fewer than two words, or only common park / place words ("Park", "Lake Park", "State Park", "North
Fork Trail" ...: COMMON_NAME_WORDS). A public park whose name CONTAINS the withheld name ("Pine Ridge Forest" for a withheld
"Pine Ridge") is masked out of the text first. A row's ref-keyed `names` map is checked by ref only. What it does NOT catch:
abbreviations ("Inner Pk"), partial names ("Inner Park" for "Zx Inner Park"), other spellings or translations, names under the
rules above, and names the store and the pin list do not know. That is why every withheld park is kept out by its ref (rows,
keys, text, any case) and by its records (never read on a public run).

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
the club-room tag, never shown). Test fixtures: `tests/fixtures/fers-store-v3/` (synthetic squares written by the tool itself) and
`tests/fixtures/fers-store-v4/` (made-up format 4: area, line, pin, one water tile). Since 2026-11-15 index `/4` is read too (item 11).

## The switch

`KPC_FERS_FROM_STORE` (default off). Off: `install()` does nothing and `kpc_fers.py` runs exactly as today. The Kentucky run
never uses the store, and the world run only with `"world": "on"` (above): otherwise with the switch on they run as today
(downloads included). On, for a US + Canada run:

1. **Area gate, before pass 1.** Every member state needs a readable store no older than `KPC_FERS_STORE_MAX_DAYS` (45). One that
   is missing, stale, of another format or damaged is left out of the run with its reason and keeps its previous files (since
   2026-11-15; before, the whole run stopped); when none is left the run stops with exit 87 before anything is read or saved.
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
10. **Nothing private in a public file or log.** On a PUBLIC store run a park held or used for records that are not
    publishable (licence) or that are (or may be) WDPA-derived is never named in any public file or in the run's log: not its
    ref, name, record key or licence class. The set is filled from the store index for EVERY park of the run's areas (read or
    not); a park this run read from publishable records only may be named. Such a park is left out of the spot files (an old
    live row of it is not carried), `looked-<area>.json`, `missing-<tag>.json`, the report and `store-missing-<tag>.json`,
    which gives only an anonymous count; a printed line naming one has it replaced by `[withheld]`. A park the store held for
    another reason is listed on the Missing boundary list with the store's reason, never "no official boundary". Every file
    the bot writes goes through `save_json` -> `_save_json_raw` (the two other writers, `live_save` and `_wsave`, are off in a
    store run); the store module guards that step and its own list, and the run stops with exit 89, writing nothing, rather
    than write a `club_room_only` row (any depth), a row naming a park outside the US and Canada (any row shape), any mention
    of a secret park (any case), or the never-released build `US-42797939226` (as text or a number). The refusal prints only a
    count and the kinds of problem; the details go to the private log (`KPC_FERS_PRIVATE_LOG` on a public run, the private
    folder on a private run), nowhere else. A **private** store run writes every file into `KPC_FERS_PRIVATE_OUT` (outside
    every git work tree, else exit 89 before anything is read), sends everything the process prints to
    `<private folder>/run-log.txt` and prints counts only; under GitHub Actions (public logs) it is refused (exit 89) unless
    `KPC_FERS_PRIVATE_RUNNER=1` names a private runner. `kpc_fers_publish.py` refuses a club-room, world or never-released row.
11. **Store format 4 (store tool 3.5).** The reader takes index `kpc-outline-store-index/3` and `/4`; any other version is
    refused (fails closed). Only records whose `geometry_kind` is `area` (absent = area) make a park's outline; `pin` records
    and unknown kinds are never used. A `line` record gives a line park its line (the open path, never closed, never buffered):
    trail or river comes from the record's `boundary_rule` (`trail_100ft` / `river_100ft_from_bank`; never the park's name;
    `data/trails` only when a record has none). A `designated_corridor` river is an AREA park (its corridor polygon is its
    outline; its line is never the boundary); `line_missing`, an unsorted river class or an unknown rule = held. A line found
    on NHD by name (`source: nhd-by-name` / `line_extent`) or a river line with no known bank status is SKIPPED and counted (no 2-fer from it; listed as "river candidate: needs a look" in the private folder only).
    The four NPS water routes the store marks `too coarse for a bank test` (US-4572, US-3791, US-4567, US-4581) are treated
    exactly as on main: their `data/trails` line and today's water-route rule (a coarse route not in `data/trails` is skipped).
    A `bank_missing` water trail is still decided by the existing centre-line rule (owner ruling, 2026-11-14); a row whose
    stretch was not measured from a real bank is marked `river_bank` (an estimate) and its stretch goes on the private
    `river-bank-todo.csv` so the store fetches that tile next.
    Who drew the line, its type and its water pieces still come from `data/trails`. Counts in the run report (`outline_store`).
    **The line rule itself is exactly as on main** (`kpc_fers.py`): a station 5 m inside the other park within 25.48 m of a
    trail's line (30.48 m from the line to the park edge, i.e. 100 ft), or within 30.48 m of a US river's bank where mapped
    water covers the line, along a stretch of at least 25 m. The store spec's wording ("the old 25 m centre-line workaround is
    not the rule") is about a river without a bank: that fallback is the switch in item 13, default unchanged.
12. **Water tiles** (FORMAT-4): `store/water/<source id>/<i>_<j>.json.gz` with `store/water/index.json`. The source is the one
    mapped to the run's areas (US-* = `us-nhdplus-hr`); a border tile in another source never decides. A tile must be listed in
    the index with the same sha256, its source must be publishable on a public run, and it must be in the bot's own tile form;
    otherwise it is NOT SURE, with no fall-through to another copy. A tile the store does not hold falls back to the bot's own
    last good copy (WATER_STORE), as today. Rows keep today's dated wording (the tile's date). Canadian sources are not read
    (Canada keeps today's behaviour: no bank source wired in the bot). Any error inside the land check of a store run is
    NOT SURE, never "ok".
13. **Rivers with no bank data, behind one switch** `KPC_FERS_RIVER_NO_BANK` (store runs, US rivers, passes 2-3):
    `centreline` (default) = today (25.48 m from the centre line where no water area covers it). `tiers` = PROVISIONAL (the
    owner's Nov 14 ruling): 1 bank (every point of the stretch in mapped water: today's 30.48 m from the bank, solid); 2 the
    other park reaches the river centre line (counts); 3 a park edge runs along the river within `KPC_FERS_RIVER_HALF_M`
    (150 m) for 50 m, or 4 the park lies within `KPC_FERS_RIVER_CATCH_M` (250 m) of the centre line: "river candidate: needs
    bank shape" (never a 2-fer), each written to `river-bank-todo.csv` (park ref, other park ref, lat, lon, radius m) in the PRIVATE folder only, for the bank store to fetch. Every
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

## Not in this module (later)

The lazy passes in `kpc_fers.py` (the hook and the move into the 2-fer `RULE_FILES` are done, 2026-11-15); `kpc_fers_store.py run`
now only calls `kpc_fers.main()` (the hook installs, once); the matcher "join under review" rule (`join_review()` exists, not wired; keep and tag, hold only on shared records, is the recommendation, not yet the owner's decision); PAD-US closed areas, ownership tiles and water
inside the store (until then those checks are NOT SURE in a store run); the KPC-Data workflow step that fetches the store.

Tests: `tests/test_fers_store_nov13.py` (synthetic stores; no network); `tests/test_fers_store_switch_nov15.py` (the hook off = main's
files byte for byte; on = zero sockets under an audit hook; keep the old row; exit 89; the area list; Kentucky and world) on
`tests/fixtures/fers-store-v4/` (made-up format-4 store: area, line, pin, one water tile).
