# MAP DATA RULE SHEET: REVIEW (Research desk, chat 8, Tue Oct 27 ~7:40 AM)

Reviewed: "MAP DATA RULE SHEET" at the end of `.claude/notes/mapping.md` (chat 2, Oct 27 5:30 AM, with 1b BOUNDARY RULES, the HQ rulings of 6:32 AM, and the observations log). I tested it against real Kentucky cases and the files in the repo; where a point is about a data file I name it. I cannot see polygons from here, so geometry tests (pin inside, half/double size) stay with the bots.

## Verdict
The sheet is the strongest of the batch, and the Brandon rulings (B-G1, B-G2, B-G3) already close three of the hardest questions. It still has **2 rule conflicts** (A), **11 edge cases** (B) and **9 questions** for Brandon (C).

## A. RULE CONFLICTS (fix the wording before building)
**A1. B2 (who wins) contradicts B1 (agency-land).** B2 puts "the MANAGING agency's own legal or official boundary layer" first. For a national forest, the Forest Service's own boundary layer IS the proclamation line (the "Proclaimed Forest Boundaries" service describes "boundaries encompassing" National Forest System lands), while B1 says use owned land only. Read literally, B2 would pick the proclamation line. **Fix:** say in B2 that for agency-land parks the agency's OWNERSHIP layer (Basic Ownership, FWS Interest FEE, PAD-US Fee) is the "official boundary layer"; the outer line is never a candidate.
**A2. Lower levels can still beat PAD-US with the wrong thing.** B2 level 3 ("another agency's layer that names the park") ranks above PAD-US. Example: Kentucky's own "Daniel Boone National Forest (hunting allowed within Elk Units)" polygon (a state layer, https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Elk_Hunting_WGS84WM/MapServer/6) names the forest but is a hunting-unit outline, not ownership. **Fix:** level 3 counts only a layer whose purpose is boundaries of that park, not a theme layer (elk units, hunting zones, fire districts).

## B. EDGE CASES
| # | Case | Problem | Fix |
|---|---|---|---|
| B1 | **Owned-land parcels are dated.** The Forest Service Basic Ownership metadata is published Oct 4 2026 and refreshed weekly, but its content date is Dec 31, 2015, and it says positions "come mainly from on-screen digitizing or GPS" and differ from PAD-US because agencies update on different schedules. Land added since (for example the roughly 700 acres added to Daniel Boone, https://www.tpl.org/media-room/over-700-acres-added-daniel-boone-national-forest-ky) may show as "not agency land". | Am I in the Park would say "this spot is not <agency> land" on land that is. | The B1 message must say "our map shows this is not <agency> land; the agency's own map is newer than ours may be: check it" and the observations log lists parcels PAD-US shows as federal fee but Basic Ownership does not. |
| B2 | **Public roads through owned land.** County, state and federal-aid roads inside a national forest are often NOT Forest Service parcels (the road is an easement or another owner). People activate from the road edge all the time. | Under B1 they are "outside" and the 2-fer / Am I in the Park messages say move away. | Gray area G-M1 below. |
| B3 | **Swiss-cheese outlines near the edge.** Owned-land outlines have thousands of tiny holes and private inholdings; GPS error is 5 to 10 m. | Am I in the Park flips between "in" and "not" every few steps near an inholding. | Treat a spot within 15 m of a hole or edge as "near the edge: check the agency map" (not a hard yes/no). |
| B4 | **Water inside agency-land parks (B6).** B6 says water inside an official outline is park. For a Corps or TVA lake that is true where the agency owns the bed in fee, but the lake bed or the river (Ohio River) is often state-owned or covered by flowage easements. | "On the water inside <park> (boat or kayak)" may be false for part of it. | State the source: water counts as park only inside the agency's FEE outline (PAD-US Fee/ownership layer); everything else says "water near <park>, check the agency map". |
| B5 | **Half/double test is too coarse.** B3 only triggers on half or double. A 100-acre WMA that grows 60%, or a refuge that gains 20,000 acres in a day, both pass silently. | Real changes slip in without a person. | Trigger on either 25% change, or any change over a set number of acres (say 500), or a polygon count change, or when it moves off the old one. |
| B6 | **"Confirmed" must mean something (B7).** "Anything not confirmed for 12 months shows ... last confirmed <date>". If a bot re-reads a layer the agency itself has not edited in 8 years, is that a confirmation? | Stale outlines look fresh. | "Confirmed" = the agency's own layer shows an edit date within the window, or a second source of the same date range agrees; reading an old layer again only updates "last read". |
| B7 | **Official links by domain (section 5).** "Official ... links (.gov/.mil/.us)" would reject official links that are not on those domains. In the repo, 36 Kentucky park map links are on kentuckytourism.com (the state's tourism site), 3 are Forest Service files on box.com (usfs-public.app.box.com), Breaks Interstate Park is on breakspark.com (an interstate compact park), and others are on .org/.edu sites (visitblackacre.org, whitehall.eku.edu). All are the agency's real map. | A domain test throws out good links or lets bad ones through. | Replace the TLD test by a per-agency allow list (the agency's own domains plus the hosts it links from its own site); anything else stays "group_site". |
| B8 | **Concessioner camps (its G3).** Campgrounds on RIDB run by a concessioner appear in Recreation.gov as the agency's facility. | They are the agency's land and listing. | List them as the park's camp, labelled "run by a concessioner" with the booking link, since the agency lists them. |
| B9 | **Camps and the closure list.** A campground closed (Sheet A) still shows on the camp list with its booking link. | A person books a closed camp. | The camp row reads the park's closure items and shows "closed per the agency" (same item). |
| B10 | **Hours and fees scraped from pages.** A park page redesign can leave an old value or a blank. "not given: check the park page" is right, but a silently changed layout can return a wrong number. | Wrong fee shown with "from the agency, <date>". | Keep the page's own text with the number; flag any hour/fee that changes by more than a set amount for a person, as the Kentucky watcher already does. |
| B11 | **Fee-free days.** NPS publishes fee-free days (Veterans Day, MLK Day and others); the sheet shows entrance fee types only. | The fee may be zero on a day. | Optional later: list the NPS fee-free dates as a note. |

## C. GREY AREAS FOR BRANDON
Its three, then mine:
- **G1 (sheet): LOW-confidence outlines.** **(rec)** show them dashed with "low confidence: check the official map", and **never feed them to the 2-fer bot** (put those parks in "Missing boundary", 2-fer rule 12).
- **G2 (sheet): an agency map link and a different PAD-US outline.** **(rec)** show the official layer (or PAD-US) outline with the agency map link beside it; if the PDF clearly differs, log an observation and let chat 8 look.
- **G3 (sheet): concessioner camps.** **(rec)** see B8.
- **G-M1. Public roads inside agency land (B2).** Is a public road that crosses a national forest or refuge part of the park for Am I in the Park and 2-fers? **(rec)** if the agency's own map or page treats the road as inside the forest (the forest's roads, owned by the Forest Service), yes; a county or state highway (not Forest Service-owned) is not park land.
- **G-M2. Water (B4).** Count water only inside the agency's FEE outline? **(rec)** yes.
- **G-M3. Border tolerance (B3).** A 15 m "near the edge" message? **(rec)** yes.
- **G-M4. Domain test (B7).** Per-agency allow list instead of .gov/.mil/.us? **(rec)** yes.
- **G-M5. Size-change trigger (B5).** 25% or 500 acres? **(rec)** yes, and any polygon-count change.
- **G-M6. What "confirmed" means (B6).** **(rec)** an agency edit date or a second source; a re-read alone is "last read".

## D. WHAT IS ALREADY SETTLED BY BRANDON (record)
B-G1 (outer line only a faint dashed label, shaded owned land is the park); B-G2 (private land by agreement is not park land except land with its own POTA number, for that number only, never toward another park; this settles my grey case 2 about the private Kentucky WMAs: they can never make a 2-fer, and they stay DROP); B-G3 (hand-checked match stays, chat 8 confirms a new line). **My 2-fer grey-areas list** `KPC_2fer_GreyAreas_desk.md` row 2 (private/university WMAs) is therefore **RULED** by B-G2.

## E. NOT CHECKED
Whether the Forest Service Basic Ownership layer includes road parcels (I could not query it); the actual share of Daniel Boone owned land that is roads or inholdings; the half/double thresholds against real changes.

Sources: the sheet in `.claude/notes/mapping.md`; https://data.fs.usda.gov/geodata/edw/edw_resources/meta/BdyOwn_LSRS_BasicOwnership.xml; https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_ProclaimedForestBoundaries_01/MapServer; https://www.tpl.org/media-room/over-700-acres-added-daniel-boone-national-forest-ky; link domains from `kpc-ky-data.json`.

## F. BRANDON'S RULING (Oct 27 6:45 AM: "Yes to all")
Read as: every recommendation (rec) in this file is accepted, including the answers to the sheet's own grey areas and my new ones. Where a rec depends on a later step (for example the ownership step in rule 14), the rec stands as written. HQ records the final sheet; the owning chat builds nothing until HQ says so.
