# 2-fer grading: Wave 2, Maine + Hawaii (chat 8, Oct 30 2026)
The waiting room flagged these two. Both files: `data/fers/US-ME.json` (23 rows), `data/fers/US-HI.json` (76 rows), verdicts `line-me.json` / `line-hi.json`.

## PRIORITY BUG, ALL CHATS: same-land self-merge duplicate, 32 states, 643 extra rows (found while grading ME/HI, checked every area)
While grading ME I noticed a "same land" pair duplicated 3x in the spots array (1 real `candidate` row + 2 stub rows whose own status text is `"merged into one row: <its own id>"` -- a self-referential merge). I checked every `data/fers/US-*.json` file in the repo: **32 states have this bug, 643 extra junk rows total, and it's not a flat 2x or 3x -- it scales per state** (ME/HI/CT/CO/etc. = 2-3x, but MA has one pair duplicated **113 times**, SC 24x, DE 42x, OH up to 17x per pair, NH 17x). That growth pattern looks like each rebuild re-merges already-merged stub rows into MORE stubs rather than collapsing to one -- a real risk for repo size (Brandon's ongoing concern) if left running.
**Good news: the 5 already-LIVE wave-1 states (KY, PA, NJ, SD, DC) are clean -- zero duplicates.** So this is not yet a live-site bug, only a waiting-room one, but it will become one the moment any of the other 32 states release unless the merge step is fixed first. **Recommend: hold every wave-2+ release until chat 2 fixes the same-land merge step and reruns.** Full list of the 32 affected states + counts in the raw check below; happy to hand over the exact script if useful.

## MAINE — PASS
- Verdict READY FOR CHAT 8, known_answers 19/19.
- 4 live candidates: 3 trail pairs (US-2381+US-4556, US-4556+US-8014, US-4556+US-8435) + 1 same-land pair (US-2385+US-8492).
- Missing check reviewed (DROPPED 20, NEVER LOOKED AT 91): every DROPPED row carries a real geometric reason ("no shared ground... not within 100 ft of a trail/river line"); every NEVER LOOKED AT row is "boxes do not touch." Both sound.
- **Bug found (not blocking):** the "same land" pair US-2385+US-8492 appears 3 times in the spots array under the same id — once as the real `candidate` row, twice as self-referential `"merged into one row: US-2385+US-8492@same land@44.840,-67.148"` stubs (merging into itself). Harmless to what's shown (dedupe at render time presumably drops the stubs) but wastes rows and will throw off any row-count check. Flagging for chat 2 to fix the merge step for same-land pairs.

## HAWAII — PASS
- Verdict READY FOR CHAT 8, known_answers 19/19.
- 21 live candidates. US-4565 is the common anchor in 9 of them — checked its identity (parkinfo-web.json): it's the **Ala Kahakai National Historic Trail**, a ~175-mile coastal trail corridor on the Big Island. That explains both the high overlap count (a long trail legitimately crosses many coastal parks) and the large acreages/widths on some area-kind patches (up to 17,601 ac / 7.6 km wide where the trail's buffer runs along a big park's own boundary, e.g. likely Hawaii Volcanoes NP). Not a mapping error.
- Missing check reviewed (DROPPED 13, NEVER LOOKED AT 143): same pattern as Maine, every drop has a real reason, nothing concerning.
- **Same bug as Maine:** 2 same-land pairs (US-0129+US-7916, US-2223+US-6409) each show the identical 3x self-referential duplicate ("merged into one row: <itself>"). Same fix needed.
- One cross-check: `expected-hi.json`'s FOUND list for US-0037+US-4565 names a `trail` kind at a different point (18.975,-155.753) than the live `area` kind candidate (19.342,-155.284) for the same ref pair. Not a bug — Ala Kahakai is long enough to cross US-0037 at more than one spot (a trail-buffer touch AND a separate area overlap); the missing-check tool matches by ref pair, not by exact patch, so this is expected, not an error.

## Bottom line for chat 2 / chat 11
Both areas PASS, release when ready. One real (small) bug to fix across the assembly line: the same-land merge step writes 2 extra self-referential stub rows per pair instead of merging cleanly into 1. Worth checking whether other already-released areas (KY, PA, NJ, SD, DC, MN, VA, AZ, OH, NM) have the same stub rows before the next rebuild.
