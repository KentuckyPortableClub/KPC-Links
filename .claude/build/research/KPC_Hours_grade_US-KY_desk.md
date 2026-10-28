# Hours / fees / permits bot, Kentucky: GRADE (chat 11, Oct 28 2026)
Run graded: data/hours/US-KY.json + review.md (the bot's own 12-park sample), ver 1. 193 parks: 34 with hours, 8 fees, 11 permits, 155 "nothing found".
The bot's own gate (data/hours/state.json): **FAIL** 9 of 38 expected rows (24%). So this batch should be marked FAILED and not queued onward.
Bar: A+B >= 90%. A = the park's own hours/fee/permit, right place, complete sentence. B = true but needs a label or is thin. C = wrong thing, a fragment, or a different place's fact shown as the park's.

## RESULT: FAIL (4 of 12 = 33%). My count agrees with the bot's own gate.

| # | park | what was shown | grade | why |
|---|---|---|---|---|
| 1 | Clarks River NWR | "office is open Mon-Fri 7:30-4:00" + refuge sunrise to sunset | B | Second line is the park's hours (good). First is OFFICE hours labelled plain "Hours" (H-R5 says own label). |
| 2 | Reelfoot NWR | "Monday - Saturday (Closed on all Federal Holidays)" | C | No times, no subject: it is probably the office; a visitor cannot use it. |
| 3 | Abraham Lincoln Birthplace NHS | "The Memorial Building closes at 4:30 pm" | C | One building's closing time shown as the park's hours (attraction hours must carry their own label). |
| 4 | Green River NWR | "Day use from legal sunrise to legal sunset" | A | Park's own page, right meaning. |
| 5 | Wolf Creek NFH | 8-4, free admission, fishing licence + trout permit | A | All official, right place (one duplicate hours line). |
| 6 | Clay WMA | "Grouse and quail seasons are open until 3 pm ... from Nov" | C | Cut at "Nov." (the fix H-R1 is not working) AND hunting-season hours shown as the park's "Hours". |
| 7 | Rockcastle River WMA | same sentence, same cut at "Nov" | C | same two reasons. |
| 8 | Salato Wildlife Refuge | "Hours and Seasonal Closings" ; "26, 2026 | Free Admission" | C | A heading kept as a hit (H-R3 says dropped) and a date-line fragment as a fee. The real line (Tue-Fri 9-4) is fine. |
| 9 | Kentucky Horse Park | 10-4, closed Mon-Thu; "FREE Entry" | C | The "FREE" line is the Man o' War Memorial only; shown as the park's fee it is misleading (the park charges admission). Hours line is fine. |
| 10 | Lincoln Homestead SP | "The park is open year-round, and classes can" ; ") at a cost of $2 per person" | C | From parks.ky.gov/field-trips: field-trip page was supposed to be skipped; sentence cut; $2 is a class price, not the park's fee. |
| 11 | Carter Caves SP | "(PERMIT REQUIRED)" / "(FREE PERMIT REQUIRED)" | C | Two fragments from a map PDF with no subject (what needs a permit?). "A hit needs a subject" is not working. |
| 12 | Bat Cave SNP | "However, the hiking trails on the portion above ground are open year round" | B | True and useful, but starts mid-thought ("However,"). |

A 2, B 2, C 8. Also: the sample is the bot's "first/most hits" set, so real quality over all 193 is not better.

## Why it fails (for chat 10)
- Recall: 155 of 193 parks "nothing found" even when the hours page read OK (Cumberland Gap basicinfo page read OK, no hours kept). NPS basicinfo / FWS visit-us pages often put hours in a table or a list the sentence reader skips.
- The H-R fixes claimed done (sentence cut at "Nov.", subject needed, headings dropped, field-trip pages skipped, hunting-season/office/attraction hours under their own labels) are NOT visible in this output. If this output pre-dates the fixes, rerun; chat 10's report says this Kentucky run IS the rerun.
- Gate list in state.json: 29 of 38 expected rows MISS (state nature preserves US-79xx, fishing lakes US-136xx, many NPS). The gate is doing its job; the bot is not ready for the long run.

## Fixes for chat 10 (sent to its inbox)
1. Do not start the long run for hours on this build (gate FAIL 24%); fix then rerun Kentucky.
2. Re-check each H-R rule on the 8 C rows above (they are the test list): Clay + Rockcastle (cut at "Nov"), Salato (heading + date fragment), Lincoln Homestead (field-trip page), Carter Caves (no subject), Reelfoot (no times), ABLI + Horse Park (attraction/memorial only).
3. Read tables and definition lists (Hours / Fees rows) on NPS, FWS, parks.ky.gov and eec.ky.gov pages, not only sentences. Target: 24% gate -> 70%.
4. A fee line must say what it is for; "FREE" for one building must not become the park's fee.
