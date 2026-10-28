# Campground info bot, Kentucky: GRADE (chat 11, Oct 28 2026)
Run graded: data/campinfo/US-KY.json + review.md. 109 campground records: 58 read OK, 42 wait on the RIDB key (Brandon secret), 9 "not official host" (all Land Between the Lakes), booking link on 58, elevation on 86, SITE COUNT on only 7.
No gate result in state.json (this bot shows none). Bar: A+B >= 90%.
A = every fact shown is right and sourced. B = nothing wrong shown but thin, or one soft fact (overstated, generic link). C = a wrong fact, or a fix chat 10 reported as done that still fails.

## RESULT: FAIL
- My RANDOM 10 (seed 5, 2 waiting-on-RIDB records excluded): A 0, B 5, C 5 = **50%**.
- The bot's own sample ("the records with the most facts", NOT random): about 8 of 10 distinct records A/B, but it lists Twin Knobs and Zilpo twice. Best case, not typical.
- Answer-key check in review.md (67 hand-checked camps): 44 fields agree, 16 DIFFER, 164 left blank (recall about 20%, accuracy of what it fills about 73%).

## Random 10
| record | grade | why |
|---|---|---|
| Lake Barkley Campground | B | only a booking link (a lodge/cottage reservation page, not clearly camping); key has sites 79, electric. |
| Self-service lakeside campgrounds (10) (Land Between the Lakes) | C | still "page not on an official host: landbetweenthelakes.us"; chat 10 said LBL was added with proofs. All 6 LBL records (Hillman Ferry, Energy Lake, Wranglers, Piney, Fenton, self-service) are empty. |
| Barren River Lake SRP Campground | B | same generic lodge booking link only. |
| West Kentucky WMA designated camping | C | **rv_max_ft = 451** comes from "Elevation: maximum 451 feet"; rules.fires text is a deer-hunt rule. |
| Paintsville Lake Campground | B | booking link only. |
| Yellowbank WMA primitive campground | C | booking.url = the Heritage Lands Conservation Fund page (not a booking page); **rv_max_ft = 872** is elevation; season "Nov. 1 through Dec. 31" is the rabbit/quail HUNTING season, not a camping season. |
| Mammoth Cave Campground | C | phone (270) 758-2180 is the "Park footer Contact Info" number (key: 758-2424); showers/restrooms are read from the headings "Shower Types"/"Toilet Types" in a page menu, not from a statement. |
| Higginson-Henry WMA designated camping | C | **rv_max_ft = 675** is elevation; hunting season as camping season. |
| Fort Boonesborough Campground | B | booking link only; key has 163 sites, electric, dump station. |
| Twin Knobs Campground | B | mostly right (fees, check-in, dump station), but hookups.sewer/water = true from "RV sites range from electric-only to full hookups": should be "some", not true (the 'some sites' fix C-6). |

## Defects found (counts are Kentucky, all 109 records)
1. **Elevation read as RV length**: 4 records have rv_max_ft quoted from "Elevation: ... maximum N feet" (451, 675, 872, 980 range). Wrong data that a camper would trust.
2. **Hunting season read as camping season**: WMA "season" values come from hunting sentences.
3. **Negation fix is only partly working**: Koomer Ridge is now right (electric False, dump station False, "no hookups"), but Bandy Creek sewer = True with the quoted line "There are no sewer hook-ups at individual trailer sites."
4. **Footer/office phones**: 8 records still take the "Park footer Contact Info" phone (Bandy Creek, Bear Creek, Blue Heron, Alum Ford, Houchin Ferry, Mammoth Cave...). One district-office number is shared by 5 campgrounds ((423) 569-9778 and (859) 428-7706 each x5). Holly Bay line lists "859-428-7706; 606-864-4163" and only the first was kept ("all phones on a line kept" not working).
5. **Duplicates not merged**: Twin Knobs x3, Zilpo x2, Koomer Ridge x2 (one waiting on RIDB), Mammoth Cave x2. 
6. **Headings read as facts**: showers/restrooms "yes" from menu words.
7. **Recall is low**: sites known for 7 of 109, fees for 16. KY State Parks campgrounds (parks.ky.gov) give only a booking link: the page text is not being read for sites, hookups, dump station.
8. **Hand key vs bot**: the 4 "electric DIFFER bot False vs key True" are probably KEY errors (Koomer Ridge says "no hookups"); chat 8 already told Brandon (see chat 10 NEEDS BRANDON). Clear Creek, White Sulphur Horse Camp, Great Meadows: still need a look at the agency words.

## Fixes for chat 10 (sent to its inbox)
1. rv_max_ft only from "length"/"RV up to N ft"/"max RV" words, never "elevation"; test: West KY, Yellowbank, Higginson-Henry must have no rv_max_ft.
2. season only from "open/season of use/camping season" lines, not hunting lines (reject "hunt", "quail", "deer", "turkey").
3. Negation: "There are no X" in the same sentence = False even if X appears after "no ... at individual ..."; add Bandy Creek sewer to the negtest.
4. Drop every phone whose source line says "footer", "Contact Us", "Mailing Address"; keep all phones on a line, label them (office / campground); a number shared by 4+ campgrounds is a district number, say so.
5. Merge duplicates by name + 300 m BEFORE writing (Twin Knobs, Zilpo, Koomer Ridge, Mammoth Cave).
6. Never take a fact from a heading or menu (a word followed by a colon-less list: "Shower Types", "Toilet Types").
7. LBL host: make landbetweenthelakes.us an official host (it is the Forest Service's LBL site); rerun the 6 LBL records.
8. Read state-park page text for sites/hookups/dump/fees (parks.ky.gov): Barren River, Carter Caves, Fort Boonesborough, Lake Barkley, Paintsville have only a booking link.
9. Add a gate: 10 known answers (Koomer Ridge no hookups; Bandy Creek no sewer; West KY no rv_max_ft; Twin Knobs sewer "some"; Mammoth Cave phone not the footer).
