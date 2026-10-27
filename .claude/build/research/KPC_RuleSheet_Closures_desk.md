# RULE SHEET A (ALL-STATES CLOSURES): REVIEW (Research desk, chat 8, Tue Oct 27 ~7 AM)

Reviewed: "RULE SHEET A: ALL-STATES CLOSURES" in `.claude/notes/mapping.md` (chat 2, Oct 27 5:10 AM), plus the posting sheet's closure rules (`website.md`). Nothing is built until Brandon rules. I read the sheet and tested it with real cases; I did not open every agency feed, so feed-specific points are marked.

## Verdict
Good sheet: the sources order, "a failed read never reopens a park", "never silently dropped" and "last checked" are the right instincts. It breaks on **7 edge cases** (A) and leaves **13 questions** for Brandon (B), including the 3 it lists.

## A. WHERE THE SHEET BREAKS
| # | Edge case | Why it breaks | Suggested fix |
|---|---|---|---|
| A1 | **One closure, several POTA parks on the same ground.** Example 9 says a Forest Service road closure shows "on the forest only, never on a WMA that shares the area unless the order names it". But the 7 Forest Service WMAs (Redbird, Cane Creek, Mill Creek, Pioneer Weapons...) are Forest Service-owned land (my Kentucky verdicts, KDFWR pages). A closure order on a road inside Redbird closes that ground whether or not the order says "WMA". | Rule 4 says "tie to ONE park", but under the 2-fer rules the same ground can belong to two parks (layering). | Tie a closure to every park whose OWN land contains the closed road/area (Forest Service ownership layer), not to the one the notice names. |
| A2 | **Big parks and the 40 km test.** Rule 2 drops notices "outside 40 km". 40 km from what? Yellowstone, Denali, Mojave, Everglades and long trails (Sheltowee 343 mi, Appalachian) have pins far from the closed spot. | A real closure 80 km from the pin is dropped; a similarly named park 30 km away is kept. | Use the park's outline when it has one (the closure point inside the outline or within a few km of it); the 40 km rule only when there is no outline. |
| A3 | **Vehicle-only closures.** "Road gate closed", "closed to motor vehicles", "service road closed" are very common and foot or bike access stays open. Rule 5 prints "⚠ CLOSURE FROM THE AGENCY". | Activators can walk in; the wording says no entry. | Add a fourth class: "closed to vehicles: open on foot" (agency's words), shown softer than a whole-park closure. |
| A4 | **Services closed, access open.** A federal shutdown or staffing cuts: NPS/Forest Service pages say "visitor center closed", "restrooms closed", "services limited". | Not a closure of the park; sheet 1(b) "part of a park closed (a named ... campground, day-use area...)" would show PART CLOSED for every restroom. | Closed facility (restroom, visitor center, water) = info line, not a closure; closure = entry, road, trail, campground, ramp, area. |
| A5 | **A vanishing notice.** Rule 3 says a failed read keeps the last items. A feed that reads fine but drops an item (agency resets its sheet, a site redesign) looks the same as a reopening. The posting sheet uses a two-check rule for Kentucky alerts; Sheet A has none. | A closure can silently disappear on one odd read. | Same rule for all feeds: an item is removed only after 2 good reads in a row without it, and the card then says "notice taken down, check the agency page", never "open". |
| A6 | **Same closure in two feeds.** NPS alerts API plus Recreation.gov facility status plus the park's own page. | Duplicate items; two different end dates. | Merge by park + what + overlapping dates; show the later "last checked" and both links; when dates differ, show both. |
| A7 | **Hunting-closure wording is a template.** "🦌 Closed to non-hunters" is the line for every hunting closure. KDFWR (and others) also say "closed to all public use", "hunters with draw permit only", "closed to hunters without the unit permit". | The template can be wrong for a given WMA (see the bots review G9). | Quote the agency's own sentence; use the template only when the agency's wording is the same. |

Also: **nesting and wildlife closures** (beach nesting, eagle zones, bat hibernation) are seasonal PART CLOSEDs that repeat every year; treat like item 10 (seasonal gate), do not call them standing rules. **Algae/water-quality** closures are a NOTE (example 6): agree, but add that a swim-area closure on a lake does not close the shore.

## B. GREY AREAS FOR BRANDON (its G1 to G3 first, then mine)
- **G1 (sheet): hunt-only closure and activators on a public road edge.** Under POTA you must be inside the park; a state road that runs through a WMA is usually outside the closure, but the WMA itself is closed to non-hunters. **(rec)** Show the closure, add no advice about a road edge, since nobody can tell from the data.
- **G2 (sheet): a whole-park closure hides the park from "next park"/trip suggestions, or only warns?** **(rec)** Warn and sort it last; never hide (the data may be wrong, and a person may know better).
- **G3 (sheet): how long to keep an open-ended closure.** **(rec)** 90 days is fine, then "may be out of date"; shorter (30 days) for emergency types (fire, flood), longer (a year) for named long-term closures (bridge out, dam work) when the agency page still lists them.
- **G4. Vehicle-only closures (A3):** show them, softer, as "closed to vehicles: open on foot"? **(rec)** yes.
- **G5. Facilities vs entry (A4):** a closed restroom or visitor centre is info, not a closure? **(rec)** yes.
- **G6. Several parks on one ground (A1):** show a closure on every park whose own land holds it? **(rec)** yes, once ownership data exists; until then, the named park only and the card says "may also affect nearby parks".
- **G7. Mass closures:** a hurricane, ice storm or shutdown closes dozens of parks at once. One banner per state ("many parks closed: ...") plus the per-park items, or per-park only? **(rec)** one state banner linked to the agency's page, items still on each card.
- **G8. Facebook-only closures.** Many small parks announce closures only on Facebook; the sheet bans social media. Keep the ban? **(rec)** keep it; the card says nothing rather than something unofficial. Brandon may add "closed per the park's Facebook" later as a separate, marked class.
- **G9. French or bilingual notices (later, Canada).** Canada is not in this sheet, but Quebec and New Brunswick notices are French-first. **(rec)** add before Canada starts: match park by number and place, show the agency's own words and link.
- **G10. Time of day for emergency closures.** Rule 5's "last checked <date>" is a date only. A flood closure that reopens at noon. **(rec)** emergency items show "as of <date, time>".
- **G11. State says open, federal says closed (or the reverse)** for a leased park (Lake Barkley SRP leased from the Corps; Kentucky Lake WMA on TVA land). **(rec)** show both agencies' notices separately; never reconcile.
- **G12. Does a closure void a 2-fer spot?** The 2-fer rule 10 says a permanent no-entry area cannot be a spot. Add a link so a spot inside a currently closed part is hidden until the closure ends. **(rec)** yes, the 2-fer list reads closures.
- **G13. Colorado CPW drought sheet (example 7).** HQ asked me to confirm a Google Sheet source. I could not open it. The sheet is an agency's if the agency's own site links to it and the sheet is owned by the agency's account; neither is shown in this sheet. **(rec)** NOT SURE: keep it, label the source as the agency, flag the sheet's owner for a once-only check by hand.

## C. Examples the sheet gets right
(1) California partial; (2) Missouri show flag; (3) Kentucky quota hunt; (4) Florida campground; (5) Arkansas 60 days old; (6) algae; (8) PA "Hickory": unmatched; (10) winter gate. No changes.

Sources: the sheet in `.claude/notes/mapping.md`; KDFWR owner scrape `data/ky-wma-owners.json`; the posting sheet `.claude/notes/website.md`.

## RULED (Brandon via HQ, Oct 27 8:10 AM, see mapping.md / website.md 'FINAL (HQ Oct 27 8:10 AM)')
Brandon accepted chat 8's recommendations for G1-G13 (and the 7 breaks). Partial WMA closures (G9) go in the Wednesday post quoting Fish & Wildlife's own sentence, and on the park card.
