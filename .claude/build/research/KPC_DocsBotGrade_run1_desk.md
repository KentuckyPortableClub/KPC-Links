# Chat 8 grades the official-documents bot, run 1 (US-MO, US-FL) (desk, Oct 28 2026)
Method: 12 parks per area PICKED AT RANDOM (seed 28) from data/docs/US-MO.json and US-FL.json, plus counts over every map the bot kept (MO 524, FL 258), plus a look at the 'runs' hints (98). Grades: A = I opened it, B = the bot's own evidence in the file agrees (name read from the PDF, name in the file name, own agency domain), C = wrong, generic, or can't be trusted. **I could not open the map links myself (they are not on this session's fetch list), so no A grades: BOT LOOK-UP row 1 below asks chat 9 to open the 8 starred ones.** Pass bar: A+B ≥ 90%.
Note: review.md's own 'first 12 parks with a map' are all federal refuges/NPS pages: a biased sample. Ask the bot to print a random 12 per agency group next time.

## RESULT: US-MO PASS (11/12 = 92%) with fixes; US-FL FAIL (6/12 = 50%)
### US-MO random 12
| Ref | Park | Grade | Why |
|---|---|---|---|
| US-11055 | Frisbee Cutoff Access | B | MDC PDF, park name read in it, stamp 2023-08 |
| US-11074 | Big Drywood Creek | B | MDC PDF, name read, no date (posted Mar 2025 only) |
| US-11371 | Bee Hollow | B | name read, 'printed 1/6/2026' (file folder says 2024-09, so the file was replaced at the same address: the printed date is the newer one) |
| US-12676 | Holly Ridge | B | name read, date unknown |
| US-11076 | Tipton Ford Access | B | name read, posted Oct 2025 |
| US-8252 | Ketcherside Mountain | B | name read |
| US-7667 | Wellsville Lake CR | B | name read; stamp 2015 vs posted 2025 = the old stamp is NOT the map date (see F5) |
| US-12581 | Blue Springs Creek | B | name read, printed 6/13/2025 |
| US-12584 | Bootleg Access | B | name read, printed 4/11/2019 (posted 2025: old map re-posted) |
| US-11129 | Long Ford Access | B | name read, posted Jul 2026 |
| US-7501 | Belcher Branch Lake | B | name read |
| US-11266 | August G. Beckmeier | C* | link is mdc.mo.gov/media/area/map/9724 labelled 'page': a PDF address read as a page, so no name or date was checked |

### US-FL random 12
| Ref | Park | Grade | Why |
|---|---|---|---|
| US-12124 | Harold A. Campbell (STA) | C | 'Map of public access locations for STAs': a map of ALL stormwater areas, names_park False = a map for a different unit |
| US-4633 | Okaloacoochee Slough SF | C | gis.myfwc.com/RecreationMap/ = FWC's statewide viewer, not this forest's map |
| US-5520 | Chassahowitzka River & Coastal Swamps | C | the file is a '2nd Draft 03-26-2024' (a draft management plan), names_park False |
| US-0244 | Key West NWR | C* | fws.gov/refuge/key-west/map = a generic template page; also the 'runs' note says 'managed by the State of Florida through a Management Agreement' (wrong for the refuge; B at best) |
| US-6299 | Dinner Island Ranch WMA | C | statewide FWC viewer again |
| US-10552 | Fox Trail SCA | B | Suwannee River WMD JPG named for the area (image: the bot cannot read it, name only from the file name) |
| US-10591 | Steinhatchee Rise SCA | B | same, JPG named for the area |
| US-8676 | Cabbage Creek SCA | B | same |
| US-8372 | Stokes Landing | B | SJRWMD PDF, name read, stamp 2023-02 |
| US-6744 | Terra Ceia Preserve | B | SWFWMD PDF, name read, stamp 2016-11 |
| US-12123 | Oak Creek, No Name Slough… | B | SFWMD JPG named for the area |
| US-3627 | Gen. James A. Van Fleet State Trail | C* | PDF with names_park False; may be the right brochure but not proven |

### The review.md first-12 samples (federal)
FL and MO first 12 are NPS 'maps.htm' pages and FWS '/map' pages: B (the agency's own map pages, date unknown). They are honest ('date unknown, checked 2026-10-28'). But 'posted July 17, 2023' on NPS rows is the PAGE's 'last updated' line, not when the map was posted: it must say 'page last updated', not 'posted' (F4).

## Over-all counts (A = measured in the JSON)
- MO: 55 maps are PDF addresses typed 'page' (so no name/date check): F1. 238 dates are 'printed on the map', 65 are PDF file stamps. 3 PDFs that do not name the park.
- FL: 50 of 258 maps are the statewide FWC viewer; 39 PDFs don't name the park; 86 are images (name can't be read); 1 'Draft' in the address; 73 parks have a blank agency; 211 no map, 234 'needs a browser' (all the Florida State Parks pages).
- 'runs' hints (98): at least 45 are cut or junk ('managed by the U.S. Fish', 'administered by the U.S. Fish', 'is managed by the Florida Fish', 'administered by Japan', 'maintained by beavers', 'managed by periodic prescribed burns', 'owned by his father-in-law', 'is administered by either a federal or state agency'). The one handover note: 'Morris State Park: donated to the state by Jim D. Morris' = history, not a handover; the card line 'May now be run by state by Jim D. Morris' is garbled.

## FIXES (for chat 2, in the order that matters)
- **F1 Read PDFs behind 'media/' addresses.** mdc.mo.gov/media/area/map/N and mostateparks.com/media/pdf/... are PDFs: look at the response type, not the address ending.
- **F2 Statewide viewers are not park maps.** gis.myfwc.com/RecreationMap/, FWC 'public lands' apps and any address with no park name in it: kind = 'viewer (statewide)', never counted as 'map ok'; the card says 'agency map viewer' only after chat 8 lists it. Same for a map of several units (the SFWMD STA map): needs names_park True for THIS park or kind 'regional map'.
- **F3 Draft, plan and brochure words.** An address or title with draft / 'plan' / 'proposed' / 'concept' / 'master plan' is not the visitor map: kind 'plan', never the main map. (HQ asked for 'a brochure vs a hunting map': a hunting map is a MAP for hunters, usable as the map; a brochure with a map inside counts only if the map page names the park.)
- **F4 Wording of dates.** 'posted' for an NPS page = 'page last updated'. Never show it as when the map was made.
- **F5 PDF stamps vs the upload date.** Wellsville: stamp 2015, posted 2025: a stamp OLDER than the folder date by more than a year is the file's creation date of a re-posted old map: show it as 'file stamp 2015', say 'this map may be old', never as the map date. A printed date equal to the day the bot fetched = generated on request = 'date unknown'. (No such case seen in the samples: rule is for safety.)
- **F6 'runs' hints: sentence splitting and sanity.** Split sentences with an abbreviation list (U.S., U. S., St., Dr., Co.); keep a hint only if what follows is an organization (agency, department, county, city, foundation, district, corporation, 'Tampa Bay Water'), not a verb or a person (burns, beavers, 'his father-in-law', 'Japan', 'local ranchers'); never show a cut sentence. Until fixed, hints stay off cards.
- **F7 Handover needs a change word.** 'donated', 'owned by', 'managed by' alone are history or boilerplate. Handover = 'transferred / now managed by / as of <year> / will be operated by / no longer' + a date or 'now'. Morris State Park would not have been flagged.
- **F8 NPS 'places' pages (Fort Caroline NM = a site of Timucuan Ecological & Historic Preserve, B/C: I could not open it):** when the park page is nps.gov/places/..., follow to the parent unit's maps page. 
- **F9 Images:** keep, label 'image: name from the file name only', grade B at most; never 'names the park' unless the bot read it.
- **F10 Random sample in review.md:** 12 per agency group, not the first 12.

## Kentucky FINDER check
Not possible yet: data/docs/US-KY.json does not exist (state.json lists US-KY in the last run's areas but only MO and FL are written). Fix A1 (tie by land) must come first anyway. I will run the 25 hand-checked Kentucky parks when the file lands.

## BOT LOOK-UP for chat 9 (8 opens)
1. Open: Beckmeier mdc.mo.gov/media/area/map/9724 (a PDF? names the park? date?); Key West NWR /map; Van Fleet State Trail PDF (names the trail?); SWFWMD 2nd Draft PDF (is it a plan or a map?); SFWMD STA PDF (confirm: one map for all STAs); Fox Trail JPG (what does it show?); nps.gov/timu maps (Fort Caroline); gis.myfwc.com/RecreationMap (does it deep-link to one WMA?).
2. Read mdc.mo.gov 'Rocky Creek 4629map.pdf': stamp 2013 vs posted 2024: is the date inside the map?

## Verdict for HQ
MO may go to a Brandon-visible sample once F1, F4, F5 and F6 are in; FL stays hidden until F2, F3, F9 are done and the FL random sample is regraded at ≥ 90% A+B. Nothing reaches a card until then (as HQ said).
