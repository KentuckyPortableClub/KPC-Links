# PARK OVERLAP FINDER DISPLAY SHEET (Sheet A): REVIEW (Research desk, chat 8, Tue Oct 27)

Reviewed: Sheet A, `.claude/notes/logger-lounge-digi.md` "RULE SHEETS" (chat 3). Checked against the 2-fer rules 1-14 (mapping.md), the two notices in CLAUDE.md, and `data/fers/US-KY.json` as it is today.

## Verdict
Good sheet: it never says "confirmed", has a "could not load" rule, and keeps NOT SURE out. I found **4 breaks**, **9 edge cases** and answers for A1-A10 plus **8 new grey areas**.

## A. BREAKS
**A-1. The main list is EMPTY today.** The sheet needs `status 'candidate'` with `passes [1,1,1]`. In `data/fers/US-KY.json` (156 spots) 136 are "pass 2" (1,1,0), 18 are "dropped in pass 2", and only 2 are (1,1,1), both "same land, two park numbers" (GREY A2). So at launch the page shows nothing or only the A2 cases. **Fix:** the page and the PREVIEW must say "Kentucky is being checked: no results yet", never an empty table that reads as "no overlaps". Rule 4 already bans a "NO"; add this exact empty-state wording.
**A-2. "Marked reviewed" has no home.** Rule 1 requires "reviewed (chat 8 check + Brandon's OK, recorded by HQ)" but no field or file holds it. **Fix:** a `reviewed: {by, date, go}` field per pair in the data (or a `data/fers/reviewed-<ST>.json`), written only by HQ; the page ignores any pair without it. A bot rerun must NOT clear it unless the patch geometry changed (then it returns to unreviewed).
**A-3. Example 6b contradicts rule 2.** "Two owners" patches are hidden until rule 14, but the row says "up to 13 places". The count must be of the SHOWN patches only, or a visitor learns hidden ones exist. **Fix:** count shown patches only.
**A-4. The tag "POSSIBLE 2-FER" next to rule "never 'is a 2-fer'/'shared'".** "2-fer" in CLAUDE.md means overlapping POTA parks only, so the tag is allowed, but on a TRAIL-LINE row (example f) the pair is not an area overlap. **Fix:** line-park rows read "POSSIBLE TRAIL OVERLAP (within 100 ft of the trail line)". Also the 3-fer tag must say "POSSIBLE 3-FER".

## B. EDGE CASES
1. **The 3-fer plus its pairs (A6).** Showing the three pair rows next to the 3-fer repeats one patch four times. Show ONE 3-fer row, with its pairs as a small line inside it ("also counts for: A+B, A+C, B+C"), not as separate rows. (Rule 11: they share one patch.)
2. **Stale row after a rerun.** A pair reviewed on Oct 27 whose outline changes on Nov 20 still says "Last checked Oct 27". The row must show BOTH "checked" and "maps dated" (it does) and drop to unreviewed on a geometry change (A-2).
3. **Retired POTA number.** A listed pair loses a park number. The nightly refresh must remove the row the same day (rule 13); the page must not rely on the old file.
4. **Park renamed.** Names come from the data, numbers from POTA; if they disagree, show the number and the POTA name.
5. **Closure note vs "closest spot".** The pin "Closest spot to public access" may sit inside a closed area. Rule 10 says a permanent no-entry area cannot be the spot; the page must carry that test to the pin, not only the patch.
6. **Directions button.** DIRECTIONS to the access pin sends a driver to a point that is public road edge, not the patch. Label it "Directions to the closest public access (not to the overlap)".
7. **Location sorting privacy.** "Nearest patch first" uses the visitor's location. State that it is used only in the browser and never saved or sent.
8. **Water-only list (public).** Public gets the Water-only list but the VERY TIGHT list is members-only: a 30-yard land patch hides while a water patch of any size shows. Fine, but water rows need the same size floor (under 25 yards = nowhere).
9. **Missing-boundary list (members).** These pairs have no boundary by definition, so they show NO map patch; the grey "?" pin needs a different popup (no "where our maps suggest").

## C. ANSWERS TO A1-A10 (recommendations for Brandon)
- **A1 show "saved outline only"?** No (agree). It means not checked against today's maps.
- **A2 "same land, two park numbers" (Fort Donelson/Heiman; Jefferson NF WMA/GW&J NF).** Show in the main list ONLY if the ownership step (rule 14) says LAYERED; label "Two park numbers on the same land: check how POTA counts it". Until then hidden. (They are the only two (1,1,1) rows today, so this decides whether anything shows at launch.)
- **A3** One row per pair with N pins (agree), biggest first.
- **A4 sort.** State, then 3-fers, then biggest patch (agree).
- **A5 first release.** Kentucky only: the only state through the rules and the reviews.
- **A6** One 3-fer row with its pairs inside it (see B1), not four rows.
- **A7 trail pairs.** Up to 3 pins, nearest a public road first, and "N stretches" in the text (agree).
- **A8 tag.** "POSSIBLE 2-FER" is allowed (CLAUDE.md defines 2-fer as overlapping POTA parks) but keep "Possible"; use the trail wording for line parks (A-4).
- **A9 no public road within a mile.** Show with the walk warning, but members only until a person has looked at one; a "walk a mile" row on the public page invites trespass. 
- **A10 "how we checked".** Members see passes, sources and owner check; chat 8's notes stay private.

## D. NEW GREY AREAS (for Brandon)
- **FD-1.** The empty state wording (A-1). Rec: "We are still checking Kentucky's parks. Nothing is listed yet. This does not mean there are no overlaps."
- **FD-2.** Where the "reviewed" record lives (A-2). Rec: a field HQ owns; a changed outline clears it.
- **FD-3.** Count only shown patches (A-3). Rec: yes.
- **FD-4.** 3-fer with pairs inside one row (B1). Rec: yes.
- **FD-5.** Trail-line row wording (A-4). Rec: "POSSIBLE TRAIL OVERLAP: within 100 ft of the trail line".
- **FD-6.** Is the visitor's location used and stored? Rec: browser only, never sent or kept; say so.
- **FD-7.** Does a "closest access" pin inside a closure get dropped? Rec: yes, pick the next one or say "no open access found".
- **FD-8.** Share/print: do copied links and PDF rows keep the SHORT notice? Rec: yes, every exported row (sheet already says PDF rows).

## E. NOT CHECKED
The page code (not built); how `maps` links look for each pair (I checked the Kentucky ones earlier in `KPC_KY2fer_Prep_desk.md`); real behaviour on a phone.

Sources: the sheet in `logger-lounge-digi.md`; `data/fers/US-KY.json`; mapping.md rules 1-14; CLAUDE.md notices.
