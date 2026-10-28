# Official documents bot, Kentucky: GRADE (chat 11, Oct 28 2026)
Run graded: data/docs/US-KY.json + review.md (ver 2). 193 parks: 184 map ok, 37 found by the bot, 55 name the park, 120 rules ok, 9 no map, 1 handover note.
Two checks: (a) the bot's own "Kentucky FINDER check" (25 parks vs hand answers) and (b) the 12-park sample table. Bar: A+B >= 90%.
A = the park's own official map/rules, right place. B = official and from the right agency but generic (page not PDF) or weaker. C = wrong thing (map or rules page for a different subject) or missed.

## RESULT: FAIL
- Finder check (25): 13 same as the hand answer (A), 4 other-but-valid official map pages (B: Clarks River, Reelfoot, Ohio River Islands, Green River NWR /map pages), 8 C (5 wrong, 3 none) => **17 of 25 = 68%**.
- 12-park sample table: A 8, B 2, C 2 => **10 of 12 = 83%**. Both under 90%. (The sample is "first 12 with a map", easiest parks.)

## The C rows
| ref | park | what went wrong |
|---|---|---|
| US-10105, 10106, 10107, 10111 | Green, Rockcastle, Big South Fork, Rock Creek Wild and Scenic Rivers | the SAME generic page, eec.ky.gov/Environmental-Protection/Water/GIS/Pages/default.aspx, for four different rivers (answers are NPS/USFS maps). Looks like a word match on "Wild"/"River"/"GIS". |
| US-10103 | Cumberland River Wilderness Area | map = the same EEC water-GIS page; **rules = eec.ky.gov ... Air-Quality-Regulations marked OK** (air quality rules for a wilderness area). |
| US-10099 | Wolf Creek National Fish Hatchery | finder check says the bot found fws.gov/library (a library page) while the sample table shows the right /map page: the two code paths disagree; and rules = fws.gov/laws-regulations (generic, marked OK). |
| US-10102 | Pine Mountain State Trail | finder check: none; the sample table shows a park page; rules parks.ky.gov/park-rules marked not OK (honest). Inconsistent. |
| US-10104 | Red River NWSR | none (answer is a USFS Box map). |
| US-10139 | Jefferson NF WMA | none (answer is a KDFWR map image). |

## Handover
- 1 note in all of Kentucky: Quiet Trails SNP, card text "May now be run by Commonwealth by Mr. and Mrs. W.G. Wigglesworth Jr. For years the: check before you go." It is a 1992 DONATION, and the sentence is cut: this would look wrong on a card. **C.**
- It MISSED the two real Kentucky handovers the truth checker found: Levi Jackson (State -> City of London, 2019) and Otter Creek SRA (KDFWR -> Meade County Fiscal Court, 2026). Needs the same signal (see the truth-checker grade for the filter rules).

## Other areas in the same run (not graded line by line, numbers only)
- **Tennessee: FAIL by numbers.** 32 of 277 parks have a map (12%); 241 say "no map link on file and none on the park page"; several are "needs browser (403)"; www.tn.gov is resting. Kentucky had hand answers to start from; Tennessee did not. Do not count TN.
- Virginia: partial (57 of 184 checked; virginiastateparks.gov resting). North Carolina 146/253 map ok. Florida 249/460: still waits on chat 2's fix (grade 6/12 earlier); I did not regrade it.
- Hosts resting after three strikes: parks.ky.gov (so Kentucky state park rules/maps may be thin), www.tn.gov, virginiastateparks.gov, wolfememorial.com, legacy.fws.gov, www5.swfwmd.state.fl.us.
- 1 bot error: US-12083 University of the Cumberlands WMA (URL with spaces).

## Fixes for chat 2 (documents bot owner; sent to its inbox)
1. Wild and Scenic Rivers + wilderness areas: do not use a state agency GIS/regulations page as the map or rules page. Map must name the river/wilderness or come from the managing federal agency (NPS/USFS); otherwise "no map" with the reason.
2. A rules page must be about visitors' rules for that unit: reject Air-Quality-Regulations, laws-regulations, "library".
3. Make the finder check and the sample table use the SAME result (Wolf Creek, Pine Mountain differ).
4. Handover: only a sentence with the park's name, a year of 2000 or later, and "transferred to / now managed by / operated by" and a new owner; never print a cut sentence on a card. Use the truth checker's real finds (Levi Jackson, Otter Creek) as the test.
5. Tennessee: not ready (12%); fix the park-page finder (state park pages on tn.gov need a browser step) before the long run counts it.
6. Florida: still open from chat 8's grade; I will regrade after your fix.
