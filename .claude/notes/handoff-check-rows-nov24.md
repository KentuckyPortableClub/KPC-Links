# Hand-off: the check rows and the matching problems (24 Nov 2026)

From: Opus (the KPC matching chat). To: the agent taking "the rest". Owner: Brandon White, KZ4CP. Plain language for him, please: he is a ham, not a web developer.

**The split (owner, 24 Nov 4:12 AM):**
- Opus takes **every park-ID problem**: New York's IDs that don't confirm their land, the ~98 parks whose saved ID is gone, ID coverage, and the Forest Service cross-state pieces.
- **You take the rest:** the own-page mistake (Maine, Iowa), the county guard rule, New Hampshire, the pin-outside list, page coverage, and the random sample.

## 1. Rules you must follow (short; the full list is KPC-Links `.claude/CLAUDE.md`)
- **NO BUILDING.** No key build, outline rebuild, map Release or 2-fer run on GitHub until Brandon lifts it. Reading, tests, PC test keys and draft PRs are fine.
- **A change that moves a key rules number goes on a branch as a draft PR.** That means any change to US / Canada / world rule files, switches, or what saved answers may do. It is merged only after Brandon's own review. The changelog line says `Reviewed: KPC owner, <date>`. Add a scope entry for each key whose number moves, and run `python3 .github/scripts/kpc_preflight.py --quick` and `kpc_key_scope_check.py` for us/ca/world.
- **RULES FIRST.** Anything that DECIDES (what counts, what is moved to check) needs a short rule sheet in `.claude/notes/mapping.md` first: what counts, what doesn't, sources, what happens when unsure, what people see, 5–10 real examples. Then grey areas go to Brandon, and only then do you build.
- **The keeper is the only bot that fetches agency servers.** Never remove the never-contact lines in `kpc_net_guard.py` / `kpc_master.py`. robots.txt always wins.
- **Ids and counts in anything public. No park names.**
- **Commits as "KPC owner" with no AI co-author lines. Emails only for real issues:** dispatch as few runs as possible and never rerun to see.
- **Write every promise as one line in `.claude/inbox/LEDGER.md`,** and mark it DONE only with proof.

## 2. Where things are now
- **Main rules numbers (#364 merged 23 Nov 9:06 PM):** US `5b55c6fad54a`, Canada `2668aab8c1c1`, world `167bf55f79a8`.
- **The PC test run** these numbers come from: 23 Nov 10:15 PM on Brandon's PC (kit 23k; park facts made 24 Nov from pack 2026-11-23-2122).
- **This pack holds it:** `pc-test-2026-11-23-2215/REPORT.txt`, the per-state logs, `cross-state-report.txt`, and **`keys/US-XX.json` = every state's key as built on the PC.** These keys are the check-list file the investigation was missing.
- **What a key file holds, per park:**
  - `m` = joined rows `[record id, record name, acres, how]`
  - `c` = **check rows** `[record id, record name, acres, why]`
  - `match.status` = confirmed / outlined / pin
  - `bk` = `[best record, km from the pin, kind, source]`
  - The website's keys for comparison are KPC-Links `data/us-key/US-XX.json` (built 19 Nov, no `match` field).
- **Counts in this pack:** 16,853 check rows.
  - By kind: trail 5,762, D (designation and compilation copies) 5,414, place 1,186, contest 1,105, far same name 816, agency 439, size 297, Q (approximate saved answers) 256, county 183, page 164, map 90.
  - Biggest states: WI 6,341, MA 2,715, TX 1,795, VA 943, NH 653.
- **Tools:**
  - The offline counter: KPC-Links `.github/scripts/kpc_match_checks_count.py`.
  - The match rules: `kpc_match_checks.py` (`pass_state`, the W6 county rule, the W-G6 town rule and its guard).
  - Park facts: KPC-Data `.github/scripts/draft/tools/kpc_park_facts/` and the reader `kpc_park_pages*.py`.
- **The PC flow after a reader fix:**
  1. Brandon runs `2e-REREAD-KEPT-PAGES` on the PC (asks no website).
  2. Then `5-MAKE-UPLOAD-PACK`.
  3. The pack goes on KPC-Data `intake-files/pc-upload/` and `kpc-pc-upload.yml` is dispatched; park facts then rebuild on their own.
  4. `park-facts.json.gz` is copied to `key builder files`.
  5. He runs `START-HERE`.
  - PC script copies must be read back byte-equal.

## 3. Your jobs, in order
1. **Maine / Iowa: the search or list page counted as a park's own page.** Plain fix, KPC-Data reader, no rules number moves.
   - 30 Maine parks got the state's park SEARCH page as their own page, and that page was tagged with one county (Aroostook). The W6 county rule then moved their real land to check: **120 "county" check rows in Maine** (website: 0), and 24 pins are over 150 km from that county. Iowa has a smaller version: 7 parks on a DNR list page.
   - Fix: a search, list or index page is never a park's own page, and a county comes from a page only when the page names that park.
   - Test with invented data, rerun from the kept pages (2e), and expect about +119 rows back and about +20 outlines in Maine.
2. **County guard (W6), a rule change: Brandon's OK, rule sheet first, then a draft PR.**
   - Like the town guard (W-G6 GUARD in `mapping.md`): if the park's own POTA pin is outside the named county, never take away the land the pin sits in.
   - Count it on the PC keys before and after.
3. **New Hampshire: explained, no fix expected.** Of its +297 extra check rows, **+302 are "check (D#): a compilation copy; the managing agency's own record is joined"** (582 against 280 on the website). They are duplicate records of land already joined, so no land is lost (measured 23 Nov). There are also +27 "place" rows. Please confirm this with a per-park look and write it down; change nothing unless you find lost land.
4. **Pin outside the joined land (2,295 of 11,553 joined parks, 19.9%).**
   - Worst states: NY 130/828, MA 118/408, CO 111/265, WA 100/478, AR 97/257.
   - Build the problem-solver list (counts by state and kind; trailhead pins are usually fine), **leaving out Maine until job 1 is done.**
   - Report only, then Brandon decides. The PC report's new line "outlined only with the pin over 5 km off" gives the part with no proof at all.
5. **Real park pages for the weakest states: ID, PA, DE, MI** (confirmed 24%, 33%, 24%, 15%).
   - Pages only; IDs are Opus's.
   - The own-page finder (`kpc_park_pages_find.py`, FIND_RULE L) runs on the PC (`2f-FIND-OWN-PAGES`).
   - Look for agency list pages, moved sites and sitemaps the finder doesn't know yet, and add them as finder rules with tests.
6. **The outside random sample: 50 parks, not 300,** and only after jobs 1–2 are in and a fresh PC test is done.

## 4. Opus's jobs (so you don't do them twice)
- **New York:** 92% of its parks have a good ID, but the IDs don't confirm the land joined by name (829 outlines).
- **The ~98 parks whose saved ID is gone.**
- **ID coverage** (link IDs, agency IDs) for ID / PA / DE / MI.
- **The cross-state pieces from the Forest Service.** 9 lists were not asked, because robots.txt on apps.fs.usda.gov reset the connection, and the script fails closed. The other 21 records were added on the PC.

## 5. Working together
- **Who owns which code:**
  - You own the reader and finder in KPC-Data, and the county rule section of `kpc_match_checks.py`.
  - Opus owns the ID paths (`kpc_link_ids`, the ID ties in `kpc_match_checks.py`, the saved answers).
  - If you both need `kpc_match_checks.py`, the second PR rebases and recomputes its rules number and scope entries. The changelog's top line must name the right "from" numbers.
- **PC runs:** one combined PC run after both of your fixes, not one per fix (Brandon: "stop rerun and rerun").
- **The keeper** is back on (KPC-Store), but its first run has not happened yet: the 07:41 UTC timer had not fired by 10:13 UTC. Read `reports/LATEST.md` on `store-data` after it runs. It may name parks rejected by the new halved-outline gate.

## 6. Anything else
- **Don't** treat the 19 Nov website keys as truth. Compare against this PC test, the agency's own data and the park facts.
- **Before saying any rule "works",** show the per-park before/after on the PC keys: same / better / worse. Zero worse is the bar.
