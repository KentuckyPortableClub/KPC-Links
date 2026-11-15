# 2-fers from the store: follow-ups (not in PR #184)

KPC owner, 2026-11-14. Scope frozen; these are left for later PRs.

1. `kpc-gps.js` `readFers()` has no status filter: per the review it turns rows that are "merged into one row" or "dropped"
   into "Possible 2-fer spot" waypoints (US-2667 + US-4512 would give three). Small separate PR: keep only rows whose status
   starts with "candidate" (and the merged patches only as children of their row). Not re-checked here.
2. The "about" text of `data/fers/missing-<tag>.json` in `kpc_fers.py` still says "(or only an approximate one)" and
   "members first"; approximate parks are tested, not listed, and the list is not sorted. Fix in the switch-over PR (that PR
   moves the 2-fer rules hash anyway). The new R12 text keeps "members first" (the owner's words); drop it or sort the list.
   Nov 14: the about text is corrected in prep/nov14-full-100ft (the R12 words are not touched); item 1 in prep/nov14-ky-key-and-gps-fix.
3. The branch is behind main (main's us-key and world-key rules hashes moved since the branch base): rebase is the manager's
   call; the "newest changelog hash" tests must be run again after it.
4. River tiers (`KPC_FERS_RIVER_NO_BANK=tiers`) stay provisional and off; no more work on them until the owner rules.
5. Canadian water sources (bc-fwa, ab-hydro, on-ohn) are not read from the store: Canada keeps today's behaviour until a
   bank source is wired in the bot.
6. PAD-US closed areas and ownership tiles are not in the store: in a store run those checks are NOT SURE.
7. The switch-over itself: the hook in `kpc_fers.py`, lazy passes, this module into the 2-fer `RULE_FILES` (fers rules hash
   cef323de4c9a moves then), the KPC-Data workflow step, a private runner for private-store runs.
   Nov 15: the hook and the RULE_FILES move are done (fers d0064c860cba -> d71d343a2272, prep/nov15-fers-store-hook), with the area
   list .github/fers-store-areas.json and the keep-the-old-row rule (R11). Still open: lazy passes, the KPC-Store workflow (PR 2),
   the KPC-Data monthly-run skip of store areas (PR 4: it must also read the except list), a private runner for private runs.
8. World store areas (wired, off): the store's world builder must write index-W-<CC>.json with record keys equal to the world
   key's record ids; world lines and water are not read from the store; world areas need fers-ready-areas.json first.
9. Kentucky from the store: needs a crosswalk from Kentucky's name-joined ids (src|NAME) to the store's US-KY records and a
   Kentucky owner step on store records (ky_owner reads the id prefix); not started.
