# RULE SHEET B (NEAR-MISS OUTLINE MATCHING): REVIEW (Research desk, chat 8, Tue Oct 27 ~7:20 AM)

Reviewed: "RULE SHEET B: NEAR-MISS OUTLINE MATCHING" in `.claude/notes/mapping.md` (chat 2, Oct 27 5:15 AM). Honest scope: I check names, agencies and official pages; I cannot see polygons from here, so pin-in-outline and size tests stay with the bot.

## Verdict
The rules are right where it matters (kind plus name plus official source, never OpenStreetMap alone, a person approves). It has **one internal contradiction** and **9 edge cases** the rules don't settle.

## A. A CONTRADICTION
**Example 4 breaks rule 1(a) and rule 4.** NB #5 and #6 are "joined by number" although their pins sit in zones 8 and 7, i.e. more than 1 km outside. Rule 1(a) needs the pin inside or within 1 km, rule 4 says a pin more than 1 km outside is "not listed". Either the number rule is an exception to 1(a) (then say so) or those two stay leads. **(rec)** make the number rule explicit: a numbered zone joins on name + number alone only if the park's POTA page confirms the number, and a pin outside the zone is shown as a flag, not a block.

## B. EDGE CASES
| # | Case | Problem | Fix |
|---|---|---|---|
| B1 | **Common name words.** "Mill Creek", "Big Creek", "Pine Mountain", "Bear Lake" exist in many places in one state. | Rule 1(b) "same main name word(s)" could join a similarly named area 900 m away. | Require ALL non-generic words to match, the same agency or type, and the pin inside (not just within 1 km) when the name is common; edge within 1 km needs a person. |
| B2 | **One polygon wanted by two parks.** Two POTA parks match one official area (Natural Bridge State Resort Park and its State Nature Preserve inside it; Fort Donelson and Fort Heiman). | Approving the second join makes the "same outline, two numbers" error the 2-fer rules treat as a mistake. | A polygon joins to ONE park unless the layering (park + preserve) is confirmed by two different official polygons; otherwise the second stays a lead. |
| B3 | **A piece of a bigger area (its G1, example 10).** The POTA park is Trin-Alcove, the official area is the whole Labyrinth Canyon wilderness. | Joining the whole area would make the park look bigger and create false 2-fers around it. | **(rec)** do NOT join the bigger outline. Keep the pin, list it under "Missing boundary: check the official map" (2-fer rule 12), and note "part of <area>". |
| B4 | **Combined parks (its G2).** POTA lists "Lawrencetown Beach Provincial Park" but the province's layer holds "Cole Harbour - Lawrencetown Provincial Park". | The POTA park may be one half. | **(rec)** join only when the agency's own page or POTA's park page names the combined area as the park; otherwise B3. |
| B5 | **Pin 0.5 to 1 km outside (its G3).** | POTA pins are often wrong by that much, and many parks have a trailhead pin. | **(rec)** never automatic: always a person, with the agency's park page and the road/trailhead check. |
| B6 | **Bilingual and translated names.** Canada: "Parc national du Mont-Orford" / "Mont-Orford National Park"; "Réserve" / "Reserve"; also "Lake Superior Provincial Park" / "parc provincial du Lac-Supérieur". | Rule 1(b) handles accents and Mt/Mount only. | Add a short translation table (Parc/Park, Réserve/Reserve, Lac/Lake, Mont/Mount, Rivière/River, Île/Island) before Canada runs. |
| B7 | **Renamed or retired official areas.** The agency renamed the area after POTA named it (renamed state parks, forests changed to wildlife areas); POTA retires a number. | The old name never matches; a retired POTA number may be approved. | Check POTA's retired list first; try the agency's old-name field or history page; leave the lead if the name changed after POTA's date. |
| B8 | **Override ids that change.** Overrides join by "[id or exact name]". Official layers republish and their object ids move; two layers can hold the same exact name. | A silent mis-join when the layer refreshes. | Store the layer URL + name + agency + area in the override and re-verify at each refresh (the sheet's B7 age rule in the Map data sheet). |
| B9 | **Rejected leads never come back.** Overrides 'no' is permanent. A reviewer error stays forever, and the agency may publish a better layer later. | Lost matches. | A 'no' expires after a year or when the layer changes, and keeps the reason. |

**Reviewer capacity:** "chat 8 checks each lead". How many are waiting? If it is hundreds, give an order (highest POTA activity first, parks with a 2-fer neighbour next) and a cap per run, otherwise the list stalls.

## C. GREY AREAS FOR BRANDON
Its three plus mine: **G1** piece of a bigger area (B3): keep the pin, "Missing boundary" list. **G2** combined parks (B4): join only when the agency names the combined area as the park. **G3** pin 0.5-1 km out (B5): always a person. **G4** a numbered zone whose pin is in the neighbouring zone (A): confirm with POTA's page or leave. **G5** one polygon, two parks (B2): the second stays a lead unless the layering is real. **G6** how many leads a week can a person look at (reviewer capacity)? **G7** 'no' decisions expire after a year (B9)? **G8** Canada translations (B6) before the Canada run.

## D. EXAMPLES THE SHEET GETS RIGHT
(1) Utah Jordan River, (3) Michigan GEMS, (5) Lake Superior SF vs Newberry compartment (kind only), (6) Edger Waterfowl vs a different WPA, (7) Bond Lake generic, (8) Rivière des Prairies, (9) Labrynth/Labyrinth misspelling by hand. No change.

Sources: the sheet in `.claude/notes/mapping.md`; `data/outline-leads/` and `data/fers/same-outline-ky.json` for the duplicate-polygon precedent.
