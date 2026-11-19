# Key quality: how we build accurate keys and grade them hard (Fable, 18 Nov 2026) - for Opus

Read this before any key grade, any rebuild sign-off, and any change to the saved answers (overrides.json).
Companion to `matching-plan.md` (how the matcher works). This file is how we KNOW it works.

Brandon, 18 Nov: "My hand check answers were not mine and not trustworthy" (5:16 AM). "We need accurate keys, we can not
trust old information" (5:26 AM). "Leave Opus notes on how to make sure we are producing great accurate keys and our grading
is hard and helps improve the system to produce the best keys we can" (5:30 AM).

## The seven rules of the grade (short form)
1. **Grade the key, not the files that feed it.** A finding counts only when it is seen in the built key (the park's `m` rows).
2. **The yardstick is never the thing being graded.** Answers the key obeys cannot also be the answer sheet.
3. **A name is one witness.** A grade that only compares names repeats the matcher's own evidence. It verifies nothing.
4. **No evidence = UNSURE.** A verdict cites what it saw (official page, acreage, unit code, map). Otherwise it is not a verdict.
5. **Four numbers, never one**: wrong land, too big, missing pieces, coverage. Each by park and by activations, with its range.
6. **Every WRONG gets a cause and a test.** Fix the rule or the data that made it, never just the row.
7. **Reproduce before you report.** One real example checked end to end in the key before Brandon hears a number.

## 0. What went wrong on 18 Nov (do not repeat)
- **The grade was circular.** The scorecard grades the rules against overrides.json, and the key obeys overrides.json.
  "Today FOUND 100%, WRONG 0" is true by construction. Rules were being tuned to reproduce answers nobody had verified.
- **Most "hand-checked" answers are one bulk import.** 5,038 parks have answers (4,774 join, 738 no). 3,307 parks carry the
  same reason, "layers row YES ... (chat N; applied by kpc_key_answers)"; 4,093 are dated November. A bot applied a list.
- **Opus's check judged the raw file, not the key.** It looked up each saved id in today's layer. Layers renumber their rows:
  288 of 3,677 saved ids now sit on a different name (OH 163 mostly restyled names, OK 55, MN 46, ME 11). The engine already
  handles that (`saved_row_ok` + re-find by saved name + acres). Example: US-4780 Badoura, saved `sgmnb56`, key uses `sgmnb10`
  "Badoura". **So "40 Minnesota forests saved one row off, a bad import" was FALSE.** Brandon was told it. Corrected same day.
- **Of Sonnet's 79 "wrong joins" only 25 are in the published key.** The other 54 were already re-found or dropped.
- **The grader was led and under-fed.** It saw the pre-sort class and a names-agree column (anchoring). 580 rows had no
  shape. It was told to "keep lookups light" and made 1 web lookup in 1,640 rows. Its RIGHT meant "the names look alike".
- **A "fact" was wrong.** US-4236 Upper Mississippi River NWR: the truth file says 1,238 official acres (the refuge is far
  bigger), so the grader called the refuge's own records wrong. Witnesses have error rates too.
- **A number went out without its range.** 1 wrong in 120 was reported as "about 30 of 3,385". The honest range is 1 to 150.
- **The same test states every time** (OH AR MD, sometimes MI TN). MA and MN are too slow for the box, so rules are never
  graded there. A rule that only ever sees Ohio is tuned to Ohio.

### What that check really found in the published key (work list, not proof of the rest)
- **25 wrong join rows live** (22 parks). 21 rows are tagged `reviewed-approx` ("the closest official land; bigger or a
  different shape"): US-3483 3484 3485 3486 3489 3490 (Nebraska waterfowl areas on county-wide records, three parks on one
  7,011-acre record), US-12127 12128 (one 47,574-acre record), US-5461 (627,317-acre fund record), US-4179 (Mt Etna = all of
  Salamonie Lake), US-4560 (trail joined to the parkway), US-12664 12725 13178 13269 13486 13570 5574 7399 9442.
  4 rows tagged `reviewed`: US-4208 (8,533 acres against 1,070 official), US-6162 (ACEC 1,795 acres against a 40-acre
  tracksite: arguable), US-4236 (grader error, see above: NOT wrong).
- **57 disputed blocks ("never use").** 48 are on parks that have an official outline anyway. 9 are on parks left as pin or
  approximate, so the block may cost an outline: US-0655 10744 1080 1660 2545 4028 6834 7475 9166. Sixteen of the disputed
  blocks come from the "Nov 2 map audit" (pattern "OFF bigger"): that is two weak graders disagreeing. Check the official map.
- Everything else is **unverified, not known wrong**.

### The bigger risk nobody has graded
Published US key (before today's rebuild; recount after): 13,118 park rows = 11,290 official, 403 approximate, 1,425 pin.
Join rows by method: **name 120,575**, reviewed 12,904, words 4,430, same 877, official 311, reviewed-approx 271, alias 88,
NPS 8. The saved answers are under a tenth of the key. **The name rule makes almost all of it and has only been graded on
"rows that changed".** 1,257 parks rest on one name-only record. 506 records are joined to 2 or more parks (9 to 3 or more).
With the answers hidden, the rules join 820 EXTRA records on 212 of 246 reviewed parks in OH AR MD (79% of their joins there).
Nobody knows whether those extras are real pieces or other people's land. That is where the grading effort goes first.

## 1. The rule sheet for the grade (RULES FIRST format)
**(1) What counts as RIGHT.** The outline is land where the park's designation legally applies, from an official layer, and
nothing else. House rule already in force: an outline goes on only with a SURE official match (pin inside + name + similar
size), else pin only. The grade enforces that rule. It adds no rule to POTA and never questions whether a park is a park.

**(2) What is WRONG, worst first.** People act on this, so the costs are not equal:
1. WRONG LAND: another park's or nobody's land shown as this park. People would activate off the park.
2. TOO BIG: a whole forest, lake property or county record for a small park. Makes false "you are in the park" and false 2-fers.
3. MISSING PIECES: real park land left off. People are told they are outside. Costs us a 2-fer, misleads less.
4. PIN ONLY: honest. Never trade 1 or 2 for less of 4.

**(3) The witnesses, best first.** Count how many independent ones agree. A name is only one.
1. Agency id / unit code (NPS unit code, refuge code, forest id). Strongest: it does not use the name.
2. The park's own official page or map (the website field in parkinfo).
3. Size: union of the pieces against the official acreage (data/truth). Check the acreage is sane first (US-4236).
4. POTA's pin inside or near the outline. Pins can be wrong (no pin, 0,0, impossible): a flag, not a verdict.
5. Designation field of the record agrees with the park's type (State Park vs State Forest vs Wildlife Area).
6. Manager of the record agrees with the park's website host (key-agency-table.json).
7. A second official layer shows the same land under the same name.
8. Name.
VERIFIED = witness 1 or 2, or the name plus at least two of 3-7. Name alone = one witness = "check".

**(4) When unsure.** UNSURE, with the reason. The park goes to pin only or stays as it is, and onto the second-look list,
busiest first. Never RIGHT by default, never deleted by default.

**(5) What Brandon sees.** One phone page per country: the four numbers with ranges, by park and by activations; flags
open / fixed / explained; the worst 20 with a map link; what changed since the last build and why. Plain words.

**(6) Hard examples (keep them as permanent test cases).** Mt Etna / Salamonie Lake (small park, whole lake property).
Nebraska waterfowl areas on county records (one record, three parks). Red Gulch tracksite 40 acres vs ACEC 1,795.
Natchez Trace trail vs parkway. Tuttle Creek Willow SFL vs Tuttle Creek SP. Acadia Cliffs SWA vs the nature preserve.
Tillamook SF vs the fund record. DeGray Lake Resort SP blocked from its own name. Ohio WA / SF / NP taking State Park records.
North Country Trail line replaced by a Park Service piece. Tennessee's compilation layer (D7 cost 56 parks). Badoura
(row numbers moved, the key re-found it: RIGHT). Upper Mississippi River NWR (bad official acreage). Lawrence Woods US-9420.

## 2. Three graders, each independent of the key
**A. Fact checks: every park, every build, no answer sheet.** A script (`kpc_key_factcheck.py`, not a rule file: it joins
nothing) run by the key workflow, output on KPC-Data branch `tools-out`. Per park: witnesses that agree, and flags:
- pin outside and more than 1 km from every piece
- union acreage under 0.5x or over 2x the official acreage (union of the shapes, never the sum of rows)
- one record on 2+ parks (unless a recorded "same land, two park numbers")
- a record over 5x the rest of the park, or one piece far from all the others
- record's designation or manager disagrees with the park's type or website
- the record's name is another POTA park's exact name in that state
- the outline changed over 10% since the last build with no rule or layer change to explain it
- a layer the keeper reports short or stale under this park
A flag never adds or removes an outline. It sorts the park into the sample below and onto the second-look list.

**B. Random samples: this is the only way to state a rate.** Unit = a park (what people see). Draw by method (`how`:
name / words / same / alias / reviewed / reviewed-approx), weighted by activations, across ALL states (MA and MN included:
sampling a built key needs no local build). Rule of three: to say "under 1% wrong" needs 300 parks checked with none wrong
(or about 500 with one). 100 per method is triage, not a certificate. Always give the range, never just the middle.
Keep a second, TARGETED sample (flagged parks, one-witness parks, extras, parks changed since last build) to find bugs.
Never work out a rate from the targeted sample.

**C. A sealed gold set, built fresh with evidence.** About 400 parks, verified against the official source, each row with
its link, what was seen, who, when. Mix: every agency type, big and small, trails and rivers, each state family (PAD-US
only, state layer, compilation layer, BLM-heavy west), plus the hard examples above. Split in two: TUNE (rules may be
developed against it) and SEALED (only scores a finished build; nobody reads its misses while writing rules). A sealed row
that someone looked at to write a rule moves to TUNE and is replaced. This is what stops the 18 Nov circle happening again.
The old scorecard stays as a change detector only ("did this switch move anything"), on rotating states, hidden run only,
with `reviewed-approx` rows taken out of its answer sheet.

## 3. How to brief a grader (Sonnet packets)
- **Blind**: no pre-sort class, no old verdict, no method label, no "names agree" column.
- **A line-up, not a yes/no**: the park, then its joined records mixed with the nearest look-alike records that were NOT
  joined. "Which of these are this park's land?" That measures wrong land and missing pieces at once and stops rubber-stamping.
- **Evidence in the packet**: pin, each record's name, designation, manager, acres, km from pin, union acres, official acres
  and its source link, the park's page. A row without a shape or a source goes in as "needs lookup", not as a name match.
- **Lookups are the job**: every verdict cites the official page, map or number it used. No citation = UNSURE.
- **Planted rows**: 10% known answers (right and wrong, from the gold TUNE half). A grader that misses planted wrongs does
  not count; rerun with a better packet.
- **Two graders on a 10% overlap**; report how often they agree. Disagreements go to the second-look list, not to a coin flip.
- Packets of 300 rows or fewer. Sonnet grades; Opus adjudicates disagreements; Brandon rules on grey areas only.

## 4. Every WRONG improves the system
Each confirmed WRONG gets one cause code: A bad saved answer / B rule joined too much (which rule) / C rule missed (which
test) / D data (short, stale or renumbered layer) / E POTA pin or name / F grader or "official" number was wrong.
Count by code per build: the biggest code is the next job. Then:
1. the case becomes a permanent test with the real names and acres;
2. the fix is a rule or data fix, judged on TUNE;
3. it lands only if SEALED does not get worse, fact-check flags do not rise in ANY state, and no saved hard case flips;
4. rule files change only through the scope / hash / changelog steps with Brandon's APPROVED.
Before any number goes to Brandon: open one real example in the built key and confirm it is what the number says.

## 5. Saved answers from now on ("we can not trust old information")
Do not delete them all and do not trust them. Each one keeps its power only on today's evidence:
- **Class A** the rules-only build joins the same record (two paths agree): nothing to do, the rules carry it.
- **Class B** the rules do not find it, but the saved fingerprint still fits and it is VERIFIED by section 1 (3): keep,
  stamped with the evidence and today's date.
- **Class C** fails a fact, has no evidence, or is `reviewed-approx`: loses its power, the park follows the rules-only
  result, and the row goes to the second-look list busiest first for an official-source check.
- **Blocks ("never use")** stay in force (they only remove), except the 9 above, which get checked first.
- **New answers** must carry: who checked, the official source, what was seen, the date, and the record's fingerprint
  (name, acres, layer, read date). A bulk list without those is refused by a test. A fingerprint that no longer fits sends
  the answer back to "check"; ids alone are never trusted (rows get renumbered).
- When answers lose power some parks drop to pin and the drop guard holds those states. The report lists every dropped
  park with its reason, so Brandon can release a held state knowingly (KPC_DROP_OK is his word, not ours).

## 6. Order of work (written before the tools existed; steps 1-2 are DONE, the live order is section 11)
1. Read this morning's whole-US run (44284543226) and the `key-held` files. Do not grade it against overrides.json.
2. Build the fact check (A) and run it on all US states and Canada. This needs no ruling.
3. Class every saved answer A / B / C from the built keys (scorecard hidden lists + the fact check). Report counts by state.
4. First random samples (B): the `name` method and the EXTRA records, 300 parks each, all states, packets per section 3.
5. Class C and the 9 blocks: official-source check, busiest first.
6. Start the gold set (C) from the verified rows of steps 4 and 5; add the hard examples.
7. Fix by cause code, rebuild only the states touched, repeat 2-5 until the numbers meet Brandon's targets. Then Canada.
Files from the 18 Nov check: KPC-Data branch `tools-out`, folder `key-quality/2026-11-18/`.

## Brandon's rulings, 18 Nov 5:48 AM ("Yes to 1-3 ... 4 ... they should be verified too ... trust nothing, they are not my answer")
- **Q1 YES: `reviewed-approx` outlines drop to pin only until verified** (271 rows, 106 parks). A key rule change: do it
  through scope / hash / changelog, "APPROVED, decided_by KPC owner, 2026-11-18". Check no 2-fer tool still reads them
  (data/fers-approx-outlines.json).
- **Q2 YES: "excellent" in numbers.** Wrong land under 1% of parks with an outline (300 sampled, none wrong); none wrong in
  the 25 busiest parks of each state; no park over 2x its official acreage unexplained; every flag fixed or explained.
  Coverage is reported, never a target. This is the sign-off bar for US and Canada.
- **Q3 YES: the 28 "Brandon signed" rows are checked like every other old answer.**
- **Q4 Kentucky's answers are NOT his either: verify them too.** KY is 193 parks (data/ky-answer-key.json + ky-key-no.json,
  built by kpc_ky_key.js): check EVERY park against the official map, no sampling. Kentucky is home and in full scope.
- Standing: **trust nothing that has no evidence behind it.** Nothing in any key is "his answer" unless a row says he
  checked it himself, with the date.

## 7. More checks that cost little (Fable, 18 Nov 5:50 AM; Brandon: "this is maybe the most important part of the process")
- **The 2-fer run is a too-big alarm.** Count overlaps per park before any 2-fer is shown. A small park that "overlaps" many
  others, or two parks with nearly the same outline (and no "same land, two park numbers" record), is a key error first.
- **The size witness needs its own check.** US-4236's "1,238 acres" was read off a page sentence about a different refuge
  (Driftless Area). Rules: the sentence must name THIS park; prefer the agency's own yearly acreage tables by unit (Park
  Service acreage reports, Fish & Wildlife annual lands report, Forest Service land areas report: research desk finds
  them, a bot reads them once a year); a size from one page only is "weak" and cannot fail a park by itself.
- **Whole-state totals.** Per agency per state: how many of its units have an outline, and total acres, against the
  agency's own count. Catches a short or half-read layer that park-by-park checks miss.
- **The approximate grade is three things.** 403 parks: 230 from the `words` rule alone, 71 from `name`, 102 with
  `reviewed-approx` (Q1). Sample `words` FIRST: it is the loosest rule. A method that fails Q2 sends its parks to pin.
- **Who writes a rule never grades it.** Opus builds, Sonnet grades blind, Fable settles disputes and re-checks 5% of
  Sonnet's verdicts. A grade from the same model and the same evidence as the build is not a second opinion.
- **PROPOSALS, each needs Brandon's GO (not built):**
  (a) an accuracy gate in the key workflow, like the drop guard: a state's key is held when a saved hard case flips or
  its flags rise, with the held copy kept for reading;
  (b) a phone page in the Club Room, one park per screen: our outline beside the agency's own map link, three buttons
  (Right / Wrong / Not sure), saved with name + date. Brandon's and members' own eyes on parks they know are the only
  witness that is truly independent of every layer. Those rows go in the gold set as checked by a person.

## 8. Who does what
- **Fable (only):** builds the measuring tools once (the fact check; the grader packet: blind line-up, planted answers,
  evidence); picks the gold-set parks and the TUNE / SEALED split; settles every dispute; reads the first cause-code
  results and writes the fix plan; reviews rule-file changes before they land.
- **Opus:** wires and runs it all, classes the answers A / B / C, makes the rule and data fixes, rebuilds, reports.
- **Sonnet:** the volume grading, from Fable's packet, with sources.
- **Bots:** the fact check on every build, acreage tables, layer health (keeper). Nothing repeating is done by hand.

## 9. THE TOOLS (built by Fable 18 Nov; Brandon 5:55 AM: "do 1-3 go so we start right")
Both live in KPC-Links `.github/scripts`, standard library only, NOT rule files (in kpc_key_freeze.NOT_RULES; the rules
hashes did not move). Tests: `tests/test_key_factcheck_nov18.py`, `tests/test_key_grade_nov18.py` (the 18 Nov hard cases).
- **`kpc_key_factcheck.py run --keys data/us-key --cache <shapes> --parkinfo <KPC-Data>/data/parkinfo --truth
  <KPC-Data>/data/truth --out DIR [--areas ..] [--prev-keys DIR]`**: every park of a BUILT key: witnesses, flags, class
  (verified / two / one / none / flagged / pin). All 56 US areas take 5 minutes. Each key row is PROVEN in the shapes
  (the key's own `saved_row_ok`, then layer + name + acres) before any shape test. `--prev-keys` adds CHURN.
- **`kpc_key_grade.py`**: `sample` (seeded: random by method or class / busiest 25 per area / targeted / pin / gold mix),
  `packet` (blind line-ups, look-alikes and neighbours mixed in, known answers planted, the answer key written to
  `<out>-keys`, NEVER beside the packet), `score` (plants, two-grader merge, exact ranges, findings.csv with an empty
  cause column, disputes.csv, `--gold FILE` adds settled parks), `gold` (scores a finished build; SEALED = numbers only;
  `--show-sealed` reveals misses and moves them to TUNE for good).
- **`.github/key-grade-plants.json`**: 9 known answers (the Nebraska county records, the lake property, the trail on the
  state park, the wilderness on the national park, the state-wide fund record ...). Add a case only with its reason.
- **How a grade runs:** fact check, then sample, then packet, then TWO Sonnet graders who get the packet folder only,
  then score with `--gold`, then conflicts to Fable (`--adjudicated FILE`), then a cause code on every finding.
- **Known limits (say them when reporting):** wetland-district tracts (ids `fws..`, read live at build) and trail lines
  are not in the saved shapes: no shape test (389 parks, soft flag NOT_IN_READ). Canada and Kentucky need a loader
  (Kentucky's key has `tracts`, not `m` rows). Only 634 parks have a usable official size. The `agency` witness is
  learned from the key itself (weak). A SIZE flag is a question: Washington Crossing's "14 acres" and Bitterroot's
  "743,000" were both bad page reads.
- **Files of 18 Nov:** KPC-Data branch `tools-out`, `key-quality/2026-11-18/` (fact check of every state, the held-state
  comparison, the pilot packets + answers + scores, the samples with their seeds, `gold-us.json`).

## 10. FIRST RESULTS (the US key as saved 18 Nov 5:44 AM: 33 states rebuilt, 17 still on the older key)
**Fact check, all US:** 13,118 park rows, 11,715 with an outline. **Verified by facts 8,304 (70%)**, two witnesses 2,185,
one 634, none 43, **flagged 549 (4%)**. By activations: 87% verified, 2.4% flagged, 2.7% one or none.
Hard flags: SHARED 278, PIN_FAR 225, SIZE_BIG 55, OTHER_PARK 44, BIG_PIECE 36.
Witnesses seen: pin 10,652, name 10,451, agency 6,952, second layer 5,505, designation 3,320, **size 488**, code 375.
**The size leg of "pin + name + size" exists for 4% of parks.** That is the biggest hole in verifying anything.

| weakest method on the park | parks | verified | two | one / none | flagged |
|---|---|---|---|---|---|
| reviewed-approx | 106 | 14% | 22% | 16% | **47%** |
| words | 786 | 60% | 25% | 8% | 5% |
| name | 9,763 | 74% | 17% | 4% | 4% |
| same (full name, far from pin) | 22 | 13% | 40% | 36% | 9% |
| alias | 55 | 20% | 47% | 32% | 0% |
| reviewed only (the outline rests on a saved answer) | 610 | 27% | 40% | 23% | 7% |
| official line / NPS code | 373 | 100% | | | |

- The saved answers: 610 parks rest on them alone. 165 are verified by facts (Class B: keep, stamp). 149 have one
  witness or none and 48 are flagged (Class C: second look, busiest first). 248 have two witnesses (look after C).
- Weakest states (one / none): ID 33%, DE 32%, WY 28%, NV 22%, UT 13%. Most flagged: CO 13%, NV 12%, AR 12%, IN 11%.
- The 33 rebuilt states carry 3.3% flagged parks (247 of 7,530); the 17 held states, still on the old key, 7.2%.

**The 17 held states, old key against this morning's would-be key (fact check on both):** outlines 4,185 to 4,143,
verified 2,610 to 2,670, **flagged 300 to 190** (115 cleared, 5 new), SHARED 190 to 76. Of the 44 outlines lost, 25 were
already flagged, 18 had one or two witnesses, and **ONE was verified: US-4393 Gold Butte National Monument (NV, 151
activations).** The contest gave the 178,990-acre 'Gold Butte' record to the herd management area (right: it is the herd
area) and then sent the monument's OWN records (`nca21295` from the national-monument layer, `sgnvf4422`) to "check" as
"a bare name with no type word". A record's LAYER says what kind it is. Nevada stays held until that is fixed.
**Were the 44 lost outlines right? (blind line-ups of the OLD outlines, two graders, both passed the planted answers.)**
28 decided, 16 unsure. **15 old outlines were wrong (7 wrong land, 8 too big): dropping them is a correction.**
**13 were right (8) or right but incomplete (5): losing them is a step back.** Why the would-be key dropped the 13:
- "a bare name with no type word" (contest): US-6077 Red Cliffs NCA, US-3852 Buxton Woods, and Gold Butte. Same cause:
  the record's LAYER names its kind.
- "the record fits more than one of these parks" (contest): US-11142 + US-12277 West Foster Creek (two park numbers for
  the same land: the rule says SHOW both with that label), US-7348 Longview Saline.
- "fits US-n better" (contest): US-5685 Lieber SRA lost a record that carries its exact full name.
- "a heritage area is drawn around other people's land" (D3): US-12830 Old Ruby State Park, a 7-acre STATE site. The
  three NATIONAL heritage areas dropped by the same line (US-7884, US-7139, US-7893) are the rule working as ruled.
- "a designation line only for the park that IS that designation" (D3): US-10475 Pat's Cabin, US-11322 Beech Creek.
- "only a lake surface matched" (D4): US-9167 Lake Hinkle.
By state: DE, FL and WY lost only outlines both graders call wrong or too big. MT and VA lost none (their official
count fell for another reason: look before releasing). AK, AR, GA, IN, NC, NV, OK, OR, UT, WA each lose at least one
right outline; ID and RI are unsure. Releasing a held state is Brandon's word (KPC_DROP_OK).
In the 33 saved states no outline was lost by this morning's save (checked against the commit before it).

**Pilot grade (47 parks from the gold mix, two blind graders each; a work list, NOT a rate):** right 35, missing pieces
7, wrong land 3, too big 1, unsure 1. By fact class: verified 18 parks = 0 wrong land (3 missing pieces); two / one
18 parks = 2 wrong land; flagged 7 = 1 wrong land, 1 too big. The classes sort the risk the right way.
- WRONG LAND: **US-3933 Cheatham WMA** joined 'Cheatham Lake WMA' by name, and US-7578 Cheatham Lake WMA joined
  'Cheatham WMA': the name matcher drops a last word like "Lake" (`variants()` strips park / forest / pond / lake /
  reservoir / complex / memorial / reserve), which makes two different parks one name. **US-9268 Mount Irish Wilderness**
  joined 'Mount Irish' (15,075 acres, an ACEC layer record, 6.4 km from the pin) by name: a bare name from a layer of
  another kind. US-13486 Bellamy River WMA East joined the West lot (`reviewed-approx`).
- TOO BIG: US-4179 Mt Etna (`reviewed-approx`). Q1 removes both `reviewed-approx` cases.
- MISSING PIECES: US-10003 'Phillip P. Schneider' (the park is 'Phillip W.'), US-2786 'Grand Lake State Park (Honey
  Creek Area)', US-7075 four Muscadine units, US-6359 a second McClellan-Kerr record, US-5932 Jordan River OHV,
  US-4153 Kaskaskia (pin only, its record exists), US-7080 Sunflower WMA = Delta National Forest land (settled by
  Fable from the agency page: "about 60,000 acres located in Delta National Forest").
- The graders: both got the planted answers right. In 342 candidates they never split YES against NO; 10 times one was
  unsure. **But only half (A) and a third (B) of their verdicts cite a page: nps.gov, fs.usda.gov, fws.gov and many
  state sites would not open for them.** One cited map did not show what the grader said it showed (Hanging Bog).
  So: the EVIDENCE must come in the packet, fetched by a bot with the open internet, and 5% of citations get re-opened.
- Gold set so far: 61 parks (49 TUNE, 12 SEALED). Every finding of the pilot and of the held-state packet was read by
  Fable, so those are TUNE. The sealed half grows only from parks nobody has looked at one by one.

## 11. THE FIX PLAN, in order (each rule change goes through section 13)
1. **Q1, approved: `reviewed-approx` to pin only** (106 parks, 47% flagged; 2 of the 4 wrong outlines of the pilot).
2. **The contest and D3, five misses found in the held states** (section 10; causes B + C). Fix, rebuild the 17 held
   states, fact-check old against new again, re-grade what is still lost:
   (a) a bare name takes its kind from its LAYER (Gold Butte, Red Cliffs, Buxton Woods; and Mount Irish, where an
   ACEC-layer record was joined to a wilderness); (b) two park numbers for the same land both keep the record, labelled;
   (c) a record with the park's exact full name is never handed to another park; (d) the heritage line is for NATIONAL
   heritage areas, not a 7-acre state site; (e) the designation line for a park that IS that study area (Pat's Cabin).
3. **The dropped-last-word variant must not merge two parks** (cause B): when another park of the state owns the longer
   name ('Cheatham Lake WMA'), `variants()` may not strip that word, in either direction. OTHER_PARK and SHARED find
   the list: 44 + 278 parks.
4. **Class the saved answers A / B / C from the fact check** (section 5): the 610 answer-only parks first.
5. **Missing pieces** (cause C, lower cost, do after 1-4): a one-letter or one-initial slip with the pin inside and the
   same agency; 'Park (Unit Area)' records; a second record of the same layer + name; units named after the park. Each
   needs its own rule line and park list. Land under another designation (Sunflower on Delta NF) is NOT a rule: it is
   a saved answer with its evidence (Class B).
6. **The size witness** (a bot, yearly): unit acreage from the agencies' own tables; the page-read sizes stay "weak".
7. **The evidence bot** (a bot): for every park in a packet, fetch the park's official page with the open internet
   (kpc_lookup / the detective) and print its unit name, acreage sentence and map link IN the packet. Then re-run the
   random samples: 300 parks by method (`name`, `words`, `reviewed`), every state, for the first real rates.
8. **The busiest 25 per state** (Q2): 1,250 line-ups, after 7.
9. **Kentucky, every park** (Q4): the Kentucky key needs a small loader first.
10. **Canada**: the same five steps once its shapes load.
11. **Then the shelved 2-fer fixes** (Brandon 18 Nov 1:48 PM: "dont let us forget about that"): open
    `.claude/notes/fers-fix-later.md` (ledger 78): the ten bugs first, then his seven questions. Whoever reports the
    US key sign-off to Brandon names this as the next job in the same message.
Before each sign-off: fact check old against new (as for the held states above), the gold score, and the SEALED number
recorded before `--show-sealed`.

## 12. TWO JOBS FOR OPUS (Brandon 18 Nov 5:55 AM: "The 2 ideas yes, save that for Opus, give them instructions")
Both DECIDE something for people, so RULES FIRST applies: these are the rule sheets. Chat 8 tries to break them, Brandon
rules on the grey areas, then Opus builds. Fable reviews before either goes live.

### A. The accuracy gate on the key bots (build this one first)
1. **What holds a state's key** (the would-be key against main's, same shapes, same script): (a) a park that is
   verified by facts on main has NO outline in the would-be key (Gold Butte); (b) a gold-set park turns wrong land or
   too big (`kpc_key_grade.py gold`); (c) a NEW hard flag on one of the state's 25 busiest parks; (d) hard-flagged
   parks rise by more than 2 and by more than 10%.
2. **What does not:** soft flags; flags that fell; a park dropping to pin that was flagged or had under two witnesses
   (that is the drop guard's count, and often a correction); a state the owner names in the variable KPC_GATE_OK.
3. **Sources:** the fact check of both keys and the gold file. Never the saved answers.
4. **Unsure:** if the fact check cannot run (no shapes, a crash) it is a warning, never red, and the key saves as today.
5. **What people see:** one notice per held state with the park numbers and the reason; the would-be file goes on the
   `key-held` release like the drop guard's. No issue comment unless a busiest-25 park is involved (email rule).
   A SEALED gold miss is reported as "a sealed case failed", never by park number.
6. **Examples:** Gold Butte loses a verified outline: HELD. Q1 sends 106 approximate parks to pin: flags fall, PASSES.
   A rule lets wildlife areas take state park records: OTHER_PARK up by 12: HELD. A layer comes in short and parks go
   to pin: the drop guard's case, not the gate's. A new POTA park with a far pin, not busy: PASSES with a notice. The
   fact check crashes: warning, saved as before.
- **Build notes:** a small `kpc_key_gate.py` (not a rule file) + one step in kpc-us-key.yml after the drop guard, reusing
  the held-copies step. Variable `KPC_ACCURACY_GATE` = `report` (default: it only SAYS what it would hold) / `on` / `off`.
  Two runs in `report`, read them with Brandon, then `on` with his word. The same step saves each run's fact check on
  tools-out, so every build gets its report card for free. Then Canada and world keys.
- **Grey areas for Brandon:** G-G1 the numbers in 1 (d); G-G2 does the gate replace the drop guard's 0% limit for parks
  that were flagged (today those "losses" hold 16 states that look better)?

### B. The phone page "Is this outline right?" (Club Room only)
1. **What counts:** one park per screen. A member compares OUR outline with THE AGENCY'S OWN MAP and answers Looks right
   / Something is wrong (too big, too small, wrong place, a piece missing + a short note) / Not sure. The buttons unlock
   only after the official map link was opened. The answer is saved with the call sign and the date.
2. **What does not:** an answer without the official map opened; a park with no official map on file (the screen then
   only asks "do you know where the agency's map is?" and that goes to the map leads); guests.
3. **Sources, best first:** the agency map link we hold (ky-official-maps.json, the documents bot's map links, then the
   park's website). Never our map or POTA's map as the thing to compare with.
4. **Unsure:** "Not sure" is a full answer. One member's answer is ONE witness ("a person looked"): it never changes a
   key by itself. Two members who disagree go to the second-look list. A "wrong" on a busy park goes to the top of it.
5. **What people see:** the short notice line "Maps and park info are a planning aid, not a guarantee ..." with the
   About our information link. No 2-fer talk on the page (so no 2-fer notice). Members only, noindex, linked from the
   Club Room only, not in the menu. Nothing about it is posted without Brandon's GO.
6. **Examples:** Brandon checks a Kentucky park he knows: "Looks right" becomes a gold row "checked by a person, KZ4CP,
   date, map link". A member says Mt Etna is too big: top of the second-look list. A park with no map link: only the
   "where is the map" question. Two members disagree: second look. A trail park: the line and its 100-foot band are
   shown and the question is about the line. A pin-only park: "we have no outline yet", only the map question.
- **Build notes:** page through assemble.py (header / footer placeholders), member lock, noindex re-added, 390 px, test
  that one page only. The queue (which park next) comes from the fact check: Kentucky first, then the member's state,
  flagged and weak parks first, busiest first; one small JSON a bot writes. Answers go the SAME way Map Rep's do
  (read notes/website.md + the Map Rep part of mapping.md first; no new back end), through the waiting room, and a
  bot turns approved answers into gold rows. Practice text never uses a real call sign. Add the page to kpc-search.js
  (members only) when it ships.
- **Grey areas for Brandon:** G-P1 how many members must agree before a park counts as "checked by people" (Fable: two,
  or Brandon alone); G-P2 may members check parks outside their own state; G-P3 is the call sign shown to other members.

## 13. FABLE REVIEWS KEY RULE CHANGES (Brandon 18 Nov 5:55 AM: "leave Opus a note you have to review their rule changes")
Any change that moves a key rules hash (US, Canada, world, Kentucky, 2-fer rule files; switches; what the saved answers
may do) goes on a BRANCH as a draft PR. It is merged only after Brandon has taken it to a Fable chat ("review PR n")
and the changelog line carries "Reviewed: Fable, <date>". The PR brings:
1. the rule line in plain words and Brandon's ruling behind it (date + his words). No made-up rules for POTA.
2. the findings it fixes, by park number and cause code (findings.csv), and the park list of every outline it changes;
3. the fact check old against new on EVERY area (flags, classes, verified outlines lost), not three test states;
4. the gold score old against new: TUNE by park, SEALED as numbers only;
5. the new test with the real names and acres; the scope entry, the new hash and the changelog line.
Fable checks: does it fix the cause or only the row; does anything verified get worse anywhere; is a hard case flipped;
was it tuned on the parks it is graded on. A NO comes back with the reason and the smallest change that would pass.
Wording, notes, tests and tools that decide no join need no review.

## 14. FABLE'S FIRST REVIEW: #270 (Q1) and #271 (contest + D3), 18 Nov 1:50 PM: both NOT YET
The changes asked for are in a comment on each PR. Standing lessons for every later rule PR:
- **A rule about saved answers acts on the ROWS that rest on the answer, never on the override's flag.** Q1 as first built
  emptied whole parks: it took an NPS unit code join (Bluestone), an official tract (Gran Quivira) and a park's own
  exact-name records (Walton WMA) with it. An answer that loses its power cannot erase what the rules joined alone.
- **This chat box has no shapely: an offline key has no union acreage** (`ac` = rows added up; SIZE_BIG 187 offline
  against 55 published). Size flags and the size witness of an offline build are not usable. Use the deltas of outlines,
  records, SHARED, OTHER_PARK, PIN_FAR, and always add old = the PUBLISHED key. The run's own keys get the full check.
- **The fact check never reads a label the key wrote itself** (`same_land`): that is the key grading itself. SHARED stays
  a question until a person or a gold row records the pair.
- **Count the claim before it goes to Brandon.** "All 13 right outlines are back" was 9 of 13 (Lake Hinkle is D4 and was
  never in the five fixes; three national heritage areas are pins by ruling). Corrected to him the same day.
- **Found on the way (findings, cause B, not yet fixed):** a bracket word that tells two parks apart is dropped by the
  contest's same-name test (Horseshoe Canyon (South) US-5846 holds North's record in the published key);
  `LAYER_TYPE['wild']` typed the federal wilderness layers as wildlife; Acadia Cliffs SWA US-9442 holds nature-preserve
  records by name.
- **Lake Hinkle US-9167** (old outline graded right, lost to D4): a saved answer with evidence (section 11 step 5), not a rule.
- **Q1 READING, RULED (Brandon 18 Nov 1:45 PM: "Go with what you think is best right now you see more information then I can"):**
  Q1 removes only the rows tagged `reviewed-approx` (271 rows). 89 parks have nothing else and go to pin. The other 23
  (13 with rows the rules joined alone, 10 with the mark but no approximate row) keep what the rules joined alone and
  are graded like any other park. Fable chose it; Brandon may still say "all to pin".
- **Round 2 (18 Nov evening): #271's content passes; #270 has one hole.** A guard may not hang on a mark that is only set when
  rows were found: four parks whose approximate records were not in the read (Jordan Craters, Lake Abert, Devil's Rock
  Garden, Split Rock) got their old `reviewed-approx` rows back through keep-last-good. Count the tag in the finished key: 0.
- **Canada's 70 approximate rows wait for step 10** (no loader, no fact check: nothing changes that cannot be measured).
- **Held states:** with both PRs none of the 17 is estimated over the drop guard's 3%, so all would save; 33 of the 44
  lost outlines stay pins there (13 graded wrong, 16 unsure, 4 graded right). Brandon hears that before the run.

## 15. LAST LOOK + THE OUTSIDE AGENT (Fable, 19 Nov 4:30 AM)
**#270 PASSES, stamped `Reviewed: Fable, 2026-11-19`** (merge = Brandon's word). **#271 NOT YET: (b) comes out** (comment on the PR).
- **"Same land, two park numbers" is never decided by name.** (b) touched four pairs and one was wrong: Seven Sisters
  US-12918 is a 7.8-acre fishing access site beside the 1,554-acre WMA US-12646. A pair is same land only when a person
  recorded it with evidence (a saved join on both parks). West Foster Creek, Longview Saline and Hobbs come back that way.
- **The outside agent works** (Brandon's, open internet): second-look 01 = 194 answers, its planted case right, two thirds of
  the decided answers on an official page. Results: KPC-Data tools-out `key-quality/2026-11-18/second-look-01/RESULT.md`.
  One agent is ONE grader: nothing joins the gold set and no saved answer is written until a second, separate pass
  (briefed to prove the outline wrong) agrees. Opus's local gold copy with the 13 parks is not pushed.
- **BEFORE THE NEXT US KEY RUN, in this order:** (1) merge #270; (2) #271 without (b), Fable, merge; (3) a small draft PR
  for the NPS unit code: no Preserve record on a park that is not a preserve, nor the other way (Denali NP US-0022 takes the
  1.3-million-acre Denali National Preserve; it goes live when Alaska is released); (4) EVIDENCE BATCH 01, saved answers each
  with who checked, the official page, what it showed, the date and the record fingerprint, Fable reads the list first:
  back as Class B = Cardigan Mountain SP, Milner HRA, Acton RS, Whiting SCA, Topsy RMA, Henderson Swamp, Coffeepot Lake,
  Lake Hinkle SRA, Bear Gulch (the park IS the 350-acre ACEC); same land on both = West Foster Creek, Longview Saline, Hobbs;
  (5) then the run, and the fact check of the run's own keys before sign-off.
- **Findings for the work list (cause B, not fixed):** a person's join for one park protects the record on the other park
  too (`_keep` in the contest caller: US-12918 holds the WMA's sgmtb8672); Tillamook SF's real boundary is not in our layers.
- **OUTSIDE-AGENT JOBS, Opus prepares each as a kit (instruction page, packet, answer sheet, planted cases; the answer key
  never leaves tools-out):**
  A. Second pass on second-look 01: a fresh agent session, briefed to prove each YES wrong, letters reshuffled, three new plants.
  B. Park and preserve list: every NPS unit that is a park or monument AND a preserve; POTA's number for each part, the
     official acres of each part (NPS acreage report), and which boundary record is which.
  C. Official acreage tables (step 6): NPS, Fish & Wildlife and Forest Service yearly lists as CSV: unit, code, acres, source link.
  D. Missing official boundary layers: Tillamook SF (Oregon Dept of Forestry), Maidstone SP (Vermont FPR), Florida state
     park boundaries; the map service address and layer for each (state open-data portal first).
  E. Later: Kentucky's 193 parks, the official map link for each (step 9).

## 16. ALL THREE STAMPED + THE TRACERS (Fable, 19 Nov 5 AM)
**#270, #271, #276 carry `Reviewed: Fable, 2026-11-19`.** Merge in that order (Brandon's word), retargeting each to main as the
one below it lands. Then ONE US key run, then the fact check of the run's own keys before sign-off.

**THE TRACERS (bots that draw an outline from an official picture map; Brandon 19 Nov 4:49 AM: "when you think it is best have
opus turn the tracers back on ... get them ready to run"). A traced line that is wrong is WRONG LAND, the worst outcome; a pin
is honest. So they come back in three steps, and nothing traced goes on the map before Brandon rules on R-G9.**
- **T1, NOW, in dry run (needs no clean key): the accuracy test against known parks (ledger 91).** Opus runs it; this is its spec.
  1. Parks: 30, drawn by a seeded random pick (never by hand) from parks that have BOTH an official picture map and an outline
     the fact check calls verified. Ten small (under 100 acres), ten middle, ten large; at least five agencies.
  2. Blind: the tracer gets the picture map and the pin, never the official outline or its acres.
  3. For every park report: traced acres / official acres; the share of the official outline the trace covers; the share of the
     trace that lies outside the official outline; how far the traced line is from the official line (middle and worst tenth,
     in feet); and plain failures (no trace, the wrong feature traced, the map had no boundary).
  4. Sum up with the grade's own words: of 30, how many would be WRONG LAND (most of the trace outside), TOO BIG (over 1.25
     times), MISSING PIECES (under 0.8 covered), GOOD; ranges, not single numbers. Files on tools-out; no map, no key touched.
- **T2, after the US key run is signed off:** the keeper's list of pin parks (data/keeper-asks/latest.json, ledger 92-93) is
  fresh then. A real trace run, results on the branch only.
- **T3, Brandon rules R-G9 with T1's numbers in hand:** is a traced line shown at all; how good must it be (a bar from T1, per
  size class); the label ("drawn from the official map, approximate") and the notice; what a traced park may NOT do (no 2-fer
  from a traced line, proposed). Fable writes that rule sheet from T1's report; chat 8 tries to break it; then Brandon.

## 17. OPUS'S ORDER OF WORK FROM HERE (Fable, 19 Nov 5:20 AM; Brandon: "ready for him to merge anything you're done with")
1. **Merge the three stamped PRs**: #270, then #271 (retarget to main first), then #276 (retarget first). Plain merge
   commits, NOT squash (they are stacked). After each: the rules-hash check on main must pass. No key run yet.
2. **Evidence batch 01 as a draft PR; Fable reads the list before it merges.** Kit A's second pass agrees with the first
   (290 of 315 records, all planted cases right), so: back as saved answers with evidence = Cardigan Mountain SP, Milner HRA,
   Acton RS, Whiting SCA, Topsy RMA, Henderson Swamp, Coffeepot Lake, Lake Hinkle SRA, Bear Gulch (only the records BOTH
   passes call YES); same land on both parks = Hobbs (both passes), West Foster Creek and Longview Saline (the two graders of
   18 Nov, held-states packet). Every answer carries who checked, the official page, what it showed, the date, the record
   fingerprint. Nothing the passes disagree on, nothing UNSURE.
3. **Gold set:** the parks where both passes agree on an official page may join it (score the two answer files together
   with --gold; the tool splits TUNE / SEALED). The copy made from one pass alone stays unused.
4. **Tracer test T1** (section 16), dry run: any time, it waits on nothing.
5. **After 1 and 2 are merged: ONE US key run, all states.** Start it, end the turn, no polling.
6. **Fact check that run's own keys against the published key** (the runner has shapely, so the size flags count) and report
   state by state before any sign-off. Held states are Brandon's word.
7. **Then section 11 step 3**, one draft PR: the dropped-last-word variant (Cheatham WMA / Cheatham Lake WMA), and with it the
   contest finding that a person's join for one park protects the record on the other park too (Seven Sisters US-12918).
8. Then steps 4 onward as written in section 11. Kits B and C feed step 6 and the park / preserve answers.

## 18. NOTE FOR FABLE (Opus, 19 Nov 5:45 AM; Brandon: "leave a note for Fable about what he needs to look at")
1. **Merged:** #270 had already been squash-merged at 04:20 (account KentuckyPortableClub, before section 17 started). Opus
   moved #271 and #276 onto main without the Q1 commits and squash-merged them (b4323b92, 73920d00). Main's US rules =
   7c6e01e1bc2b; rules-hash check PASS; the Q1, held-states, contest and park/preserve tests PASS on main.
2. **A US key run comes BEFORE evidence batch 01:** the scheduled backup start (11:46 UTC = 5:46 AM CST) sees RULES CHANGED and
   rebuilds every state on 7c6e01e1bc2b. Opus did not stop it (no workflow edits, no dispatch). So the nine evidence parks
   stay pins until a small run after #277 merges. Step 6 = fact check that run's keys against the published key before any
   sign-off; held states are Brandon's word.
3. **#277 evidence batch 01 (draft, for you to read):** 13 saved answers (9 Class B + Hobbs x2 + West Foster Creek x2), only
   records both passes call YES, each with who / source / what it showed / date / fingerprint; approx mark off. Longview
   Saline left OUT (its graders cited the packet only). Acton: sgnmc10988 dropped (not in either packet).
4. **Gold set (step 3) NOT done:** the two passes are different packets (different letters, keys); the scorer takes one key.
   Your call how to add them (a merged answer file per record id, or a third packet).
5. **Kit B (park and preserve, outside agent) finding:** the NAME matcher (not the unit code) gives the preserve to the park on
   five park-only POTA numbers: Wrangell-St. Elias NP (Preserve 4.3M ac), Katmai NP (328,054), Lake Clark NP (1.25M), Gates of
   the Arctic NP (945,247), Craters of the Moon NM (411,913). POTA has no preserve number for these. Ruling needed: does a park
   number cover its preserve when POTA has none? Denali was ruled wrong land. Great Sand Dunes is right (US-8295 = preserve).
   Tallgrass Prairie (33 ac vs 10,893) and Timucuan (16,646 vs 46,263) records are far under official: second look.
6. **Tracer T1:** not started (waits for your go via Brandon; it needs no key).

## 19. FABLE'S CATCH-UP (19 Nov 6 AM; Brandon: "catch up on all that only fable needs to do")
1. **#277 evidence batch 01: APPROVED** (comment on the PR). Checked by Fable: all 47 joins YES in both passes, every fingerprint
   matches the shape cache, the no-acres records measured from their shapes (Wells Wildlife Area sgwad2223 = 1,061 ac = the unit;
   Lake Hinkle 977; Cardigan 5,889 + 13 + 30 vs official 5,655), and a test build of the 8 states: exactly the 13 parks change,
   11 pins become outlines, nothing else moves. Merge it when no key run is in flight. NO small run of its own: its 8 states
   are all held by the drop guard, so the release run (item 7e) rebuilds them with it.
   Follow-ups for the step 3 PR: the builder copies `same_land` from a saved answer onto the key (only when both parks name each
   other) so the 'same land, two park numbers' label shows; Lake Hinkle's outline is the lake surface (water-only, 2-fer rule 9).
2. **THE KEY RUNS ARE RED ON PURPOSE (read once, 19 Nov 6 AM):** the drop guard's limit is 0: a state that loses ONE official
   outline is held ("set KPC_DROP_OK for one run"), its would-be files go to the release `key-held`, data/outlines is not saved and
   the master check goes red. The merged rules lose outlines on purpose (Q1 pins, D3, park / preserve), so the run on 7c6e01e1bc2b
   holds most states. Nothing is wrong with the bot; nothing reaches the map until Brandon says yes per state.
3. **FACT CHECK OF THAT RUN (section 17 step 6), how. Look once when Brandon says go; no polling.**
   a. Take the held would-be files from the release `key-held` (asset download through `gh api`) and the saved states from main.
      Make sure they come from the run on rules 7c6e01e1bc2b (the 10:10 UTC run was still on the old rules).
   b. Fact check OLD = the published key as it was before the run, NEW = that run's files, the same inputs on both sides. These
      were built on the runner, so SIZE_BIG and BIG_PIECE count this time.
   c. Hold it against the FORECAST = the offline builds (work/npsfull against work/main). A lost outline or a new hard flag that
      the forecast does not have goes on a STOP list for Fable; the state stays held.
   d. One table for Brandon: state | outlines old -> new | lost as planned (Q1 / D3 / park-preserve / contest) | lost and NOT
      explained | new hard flags. A state passes when the last two are empty. Score the gold set on the new files (TUNE misses
      listed, SEALED as a count only, never --show-sealed).
   e. Brandon's yes per state, then KPC_DROP_OK for those states and ONE run. Opus never releases a state on its own.
4. **RULING R-PP1, park and preserve (Fable, Brandon may overrule): a park number does NOT cover the national preserve beside it
   unless POTA's own name for that number says so ("... and Preserve").** Why: a preserve is its own legal designation; POTA numbers
   preserves on their own where it wants them (Glacier Bay US-0029, Aniakchak US-0003, Great Sand Dunes US-8295); land with no
   POTA number never counts; and the smaller outline is the cheaper mistake (missing pieces, not too big). Already so for the unit
   code (#276, Denali). Now also for the NAME join: Wrangell-St. Elias US-0069, Katmai US-0044, Lake Clark US-0048, Gates of the
   Arctic US-0026, Craters of the Moon NM US-0665 lose the preserve record; it goes on the check list with a plain line. Draft PR
   for Fable, scope AK + ID. Second look after it: Craters of the Moon (the monument also has BLM-run land), Tallgrass Prairie,
   Timucuan.
5. **GOLD SET: done.** Pass 1 moved onto packet 01b's letters by record id, both passes scored together as two graders: 14 parks
   joined, TUNE ONLY (the rule writers have read them and most are saved answers now). Gold = 77 parks, TUNE 65 / SEALED 12; files on
   tools-out `key-quality/2026-11-19/gold-second-look/`. The SEALED half is too small to grade a release: **KIT D** = a seeded
   RANDOM sample of 60 parks from the released key (`kpc_key_grade.py sample`), two outside-agent passes, hash split left alone.
6. **TRACER T1 TEST MODE: YES, with these conditions.** A switch on the tracer, off by default; with it on the bot reads a fixed
   list, skips the "park already has official records" check and writes ONLY to a throwaway branch `trace-test` on KPC-Data (never
   `picture-maps`, the hold file or the waiting room). The list: a seeded draw of 60 fact-verified parks from the published key,
   walked in order, first 10 small / 10 middle / 10 large for which the finder itself finds an official picture map; every skipped
   park and why is a result (the map find rate). The tracer never sees the official outline; a separate measuring script does
   (section 16 T1 points 3-4). ONE run by hand, steps that cannot fail (no emails), no comments. Picture maps of parks that have
   GIS are test material only: the branch is deleted once the report is on tools-out. Fable reads the report and writes the R-G9
   sheet (T3).
7. **KIT C (official acres: NPS, FWS, USFS): use it AFTER the release, not in this fact check** (old and new must be measured with
   the same inputs). Then it becomes a size witness: an outline passes between 0.8 x the smaller figure (federal) and 1.25 x the
   larger (gross); outside that it is flagged. Draft PR, Fable reviews.
8. **OPUS'S ORDER NOW:** (a) item 3 a-d, table to Brandon; (b) merge #277; (c) R-PP1 draft PR; (d) T1 test run; (d2) item 9, the layers + the hand-off zip; then Fable reads
   (c), the table and the T1 report; (e) Brandon's yes -> KPC_DROP_OK -> ONE release run (Q1, held states, NPS, #277, R-PP1
   together); (f) kit D; (g) section 11 step 3 PR (dropped last word, the `_keep` finding, the same_land label).
9. **MISSING LAYERS + HAND-OFF (Brandon 19 Nov 5:58 AM: "we was missing layers ... older pr was going to have keeper fetch what
   we was missing, confirm we got them, then hand download list ... give me hand off to have external agent help ... all
   resources are on the table"). For Opus, one pass, read the files once:**
   a. CONFIRM: what the keeper asked for and what came in (ledger 93 + the 18 Nov HQ line: KPC-Store keeper 9aae1032,
      `layer-requests.json`, the SHORT layer counts, KPC-Data `data/keeper-asks/latest.json`), plus the master check's suspect
      baselines (CO sgcoa, OR sgorf, WA sgorf: "expected 200, the file held more" = a read cut off at 200). Tell Brandon three
      numbers and the names: asked, arrived, still short.
   b. HAND-DOWNLOAD LIST: every layer no bot can read (blocked host, login, download-only file) and every park whose true
      boundary is in no layer we hold (Tillamook SF US-5461, Tallgrass Prairie, Timucuan, Craters of the Moon's BLM land,
      Longview Saline). One row each: state, agency, layer, official page, the file to get, busiest parks first, and who can get
      it: BOT / PC / AGENT. Files land on KPC-Data branch `intake-files`.
   c. ONE ZIP for the outside agent (no keys in it, as before): job 1 = find the official GIS source for each row of the list
      (research order: open-data portal, agency maps page, then web search; return the layer address or the file, the date and
      the licence line); job 2 = second look 02 (the parks named in b plus Osage WMA, Acadia Cliffs, Diamond HMA: official page,
      official acres, where the official outline lives); job 3 = the busiest 100 pin-only parks: is there an official GIS layer
      or only a picture map. Kit D (random sample, item 5) follows after the release.
   d. BRANDON'S PC: it is on home internet with a real browser, so it can download the layers that block the bots (as with the
      KDFWR file for Salato) straight from the list's PC rows. His 2-fer tool and the full PC run wait for the released keys
      (running them on today's keys wastes the run); HQ's open line (pins.json + store tool update) comes first.
10. **R-PP1 STANDS, the outside agent confirms (Brandon 19 Nov 6:04 AM: "use your judgment or maybe outside agent confirm pota
   official page weblinks are for preserve or not").** POTA's own list numbers park and preserve apart in three Park Service
   units: Glacier Bay NP US-12607 + Preserve US-0029, Aniakchak NM US-0902 + Preserve US-0003, Great Sand Dunes NP US-0033 +
   Preserve US-8295. So a preserve is its own park to POTA; where it has no number it is not a POTA park yet. Job 4 in the
   hand-off zip (item 9c): for US-0069, US-0044, US-0048, US-0026, US-0665 open POTA's own park page and report its name, its
   website link, and whether POTA lists that preserve under any other number or name. If POTA's page says the number covers the
   preserve, the ruling flips for that park (a saved answer with the page as evidence). The R-PP1 draft PR does not wait for it.
11. **SAVE USAGE ON THIS JOB (Brandon 19 Nov 6:07 AM: "plan stays its course but areas where we can optimize usage lets do it").**
   - ONE Fable session per block, not per item: Opus finishes item 8 a to d2 first, then Fable reads the PR, the table and the
     T1 report in one sitting.
   - ONE release run for everything (Q1, held states, NPS, #277, R-PP1). No small runs, no reruns to look.
   - Fact check the RUNNER'S files; no 50-state builds in chat. A review rebuilds only the states in the PR's scope.
   - The forecast is saved outside the chat (tools-out `key-quality/2026-11-19/forecast/`), so a FRESH CHAT can do item 3.
     Starter: "Read CLAUDE.md and key-quality.md section 19, do item 8 in order."
   - Legwork goes to the outside agent and Brandon's PC (source finding, page checks, grading passes, blocked downloads).
   - AFTER the release, a bot job (chat 10): the US key run writes its own old-against-new fact-check table per state, so no
     chat has to build it again.
12. **OPUS, ITEM 8 STATUS (19 Nov 7:20 AM CST).** (c) DONE: R-PP1 = draft **#278** (US 7c6e01e1bc2b -> 98b1f03ec6ed, switch
   KPC_PRESERVE_APART; the five lose their preserve record; 0 outlines lost; **Craters of the Moon US-0665 goes verified -> flagged**:
   POTA's pin is 22.7 km out, inside the preserve; job 4 decides; files tools-out `key-quality/2026-11-19/r-pp1/`). (d) STARTED:
   KPC-Data `kpc-trace-test.yml` + `kpc_trace_measure.py` (f307c407), ONE run 44530520714; list + report on tools-out
   `key-quality/2026-11-19/t1/` (report in `run-<id>/`), maps on throwaway branch `trace-test` (delete after Fable reads). (d2) DONE:
   tools-out `key-quality/2026-11-19/handoff-02/` (asked 64 layers, arrived 0, still short 64; hand-download list 592 rows: PC 487,
   BOT 81, AGENT 24; `handoff-02-kit.zip` for the agent, key in `kit-keys/`). (a) + (b) WAIT on US key run **44528656941** (started
   by hand 12:57 UTC as the missed 11:46 backup, Brandon's yes 6:52 AM; GitHub skipped the cron and the watchdog). When it is done:
   item 3 a-d (OLD side saved: tools-out `key-quality/2026-11-19/factcheck-pub/`), the table to Brandon, then merge #277.
13. **FABLE'S REVIEW OF WHAT OPUS HAD READY (19 Nov 8:10 AM CST; Brandon: "Review what Opus has ready").**
   - **#278 R-PP1: NOT YET, two changes (comment on the PR; files tools-out `key-quality/2026-11-19/r-pp1/fable-review/`).** The rule's
     exact test on all 50 areas: true for 8 rows, all AK + ID. The other scope states built: nothing moves (Colorado's Great Sand
     Dunes pair is untangled one step earlier, same result; Florida not finished in chat). What fails: POTA's OWN PIN sits inside
     the preserve record for Craters of the Moon US-0665 (78 activations, 22.7 km from the monument) and Wrangell-St. Elias US-0069
     (41, 2.8 km from the park record); Katmai, Lake Clark, Gates of the Arctic have it in or beside the park part.
   - **RULING R-PP1a (Fable, Brandon may overrule; replaces item 4's wording): a park number does NOT cover the preserve beside it
     unless POTA's own name says so OR POTA's own pin for that number sits inside the preserve record.** Change 1: the rule leaves
     such a row in place and names it as a person's question (US-0069 and US-0665 stay as they are until POTA answers; the other
     three move). Change 2: the changelog line must say "APPROVED, decided_by KPC owner" with his words (`kpc_preflight` refuses
     "decided_by Fable"): it waits for Brandon's yes to R-PP1a. Round 2: Opus shows Florida with ONE `kpc-key-measure.yml` run on
     the branch (the R-PP1 notices), no chat builds. Denali: POTA has NO preserve number (#276's text was wrong, its rule is right).
   - **GREY AREA G-PP2 for Brandon:** one combined record on a park-only POTA name (New River Gorge US-0696, Jean Lafitte US-0040,
     Oregon Caves US-0953). Left whole, as today; recommended: stay whole, ask POTA with the six park-only numbers.
   - **T1 run 44530520714: not enough to rule R-G9 on.** 13 traced of 60 (0 small / 9 middle / 4 large; spec 10 / 10 / 10). 5 drawn,
     all 5 GOOD by area; 8 refused by the tracer's own checks (a refusal is a pin). The throwaway branch was never written (save
     step bug), so maps and traces are gone; one line measure (US-11892) cannot be right. FIXED by Fable on KPC-Data main
     (dfc66f44): the save step, outside-ring line measure with holes counted apart, the tracer's own report saved, input `list`.
     **Run 2 on Brandon's go:** ONE run, list = `t1-list-2.json` (75 fact-verified parks that already have a stored official map
     link, 25 per size class, 11-14 map hosts each). Fable writes the R-G9 sheet (T3) from run 2. The tracer ran blind (checked).
   - **Hand-off 02: good to send.** One caution added: the 30 short layers a bot can re-read are NOT re-read before the release is
     signed off (old and new must be measured on the same shapes); then one by-hand cache run from the requests.
   - **Not ready, not reviewed:** item 3's table and the #277 merge. US key run 44528656941 FINISHED 14:03 UTC (8:03 AM CST), red on
     purpose (held states): a fresh Opus chat does item 3 a-d now (starter line in item 11), then merges #277.
14. **BRANDON'S YESES + THE AGENT'S ZIP (Fable, 19 Nov 8:30 AM CST). Brandon 8:13 AM: "1 yes for now, 2 yes, 3 yes 4 yes ... stay
   the course of the plan and limit usage so we can make it through the week ... accuracy and great work is very important".**
   - **R-PP1a: APPROVED FOR NOW by the owner.** #278's changelog line reads `APPROVED, decided_by KPC owner, 2026-11-19 (8:13 AM:
     "1 yes for now" to R-PP1a)`. It stays "for now" until POTA answers (a draft question for POTA is with Brandon).
   - **T1 run 2 STARTED 14:18 UTC: run 44542262740** (list `t1-list-2.json`). Report + the drawn traces: tools-out
     `key-quality/2026-11-19/t1/run-44542262740/`; maps on throwaway branch `trace-test`. Fable reads it and writes the R-G9 sheet.
   - **Hand-off 02, pass 1 is back** (tools-out `handoff-02/answers-pass1/`, READ-FIRST.md): 6 of 6 planted answers right. Job 4:
     POTA's pages link the combined unit and do not say; POTA's own comment on US-0665 sends activators to the southern expanded
     land (fits R-PP1a). Job 3: an official GIS layer named for 47 of the 100 busiest pin-only parks. ONE grader: nothing is used
     until a second pass agrees. **Correct our key: Denali NP = 4,740,911.16 acres** (we wrote 4,740,091).
   - **GREY AREA G-NPS1 for Brandon (from job 2):** Tallgrass Prairie US-3673 and Timucuan US-0658: our record is the FEDERAL land
     only (33 of 10,883 acres; 17,123 of 46,263); the unit's own boundary is in the NPS boundaries layer. Is an NPS park its whole
     unit boundary or only the federal land? Not ruled; nothing changes until it is.
   - **The 487 "PC" rows explained** (handoff-02/README.md, corrections): 410 layers on hosts bots may not contact; only 118 feed a
     park in the key; 123 open rows repeat a layer already downloaded 10-11 Nov; none is needed for the release. **No hand download
     is uploaded before the release is signed off** (a hand file is merged by the next key run and would change the shapes).
     After the release: the agent's own 49-file list, busiest first. **CORRECTION (Fable 8:35 AM, tested): the PC helper cannot use these
     rows today.** `kpc_pc_helper.py --list` shows 0 layers: the 406 open rows have no state, and the helper takes only rows with a
     state and a layer the US key has an entry for (the state rows of these layers are DONE). "Already in the PC helper" was wrong.
   - **Built:** the PC heartbeat (tools-out `key-quality/2026-11-19/pc-heartbeat/`, sent to Brandon): starts a watchdog only when it
     is over 115 minutes late. **The review packet bot goes to the OUTSIDE AGENT** (Brandon 8:25 AM: "no chat 10 no longer all chat numbers are retired ... give me handoff for outside agent"): hand-off 03A.
   - **OPUS'S ORDER NOW (fresh chat, the starter line of item 11):** (a) item 3 a-d on run 44528656941's files, the table to
     Brandon; (b) merge #277; (c) #278 round 2: the pin exception of R-PP1a, the owner's approval line, Colorado named, Florida
     shown by ONE `kpc-key-measure.yml` run on the branch (no chat builds); (d) NOT Opus's any more: Fable made the second-pass kit (hand-off 03B, with Brandon).
     Then ONE Fable sitting: (c), the table, T1 run 2.
15. **HAND-OFF 03 (Fable, 19 Nov 8:35 AM CST), tools-out `key-quality/2026-11-19/handoff-03/` (README there). Chat numbers are retired
   (Brandon 8:25 AM): nothing is handed to a numbered chat any more; builds a bot can be given to go to the outside agent.**
   - **03A, a BUILD job:** the review packet bot, in KPC-Data (KPC-Links cannot write to KPC-Data): `kpc-key-review-packet.yml` +
     `kpc_key_review_packet.py` + a test; by hand, never red, writes only tools-out `key-quality/review-packets/`. It comes back as a
     draft PR or a zip: a club session reads it before it is merged or started. Acceptance = #278 at ac2ab4c against 8140d35.
   - **03B, the SECOND PASS of hand-off 02** for a FRESH agent session (never give it `handoff-02/answers-pass1/`): jobs 2, 3 (pass
     1's 47 GIS + 8 open rows) and 4 (+ Denali + the three combined units of G-PP2), blind, reshuffled, 5 new planted answers.
     The key: `handoff-03/kit-keys/`. A row counts only where both passes agree; disagreements to Fable.
   - **Found while writing 03A:** KPC-Links `kpc-discord-relay.yml` (it restarts itself every 30 minutes, so GitHub's timer skips do
     not stop it) already carries a heartbeat for KPC-DATA's watchdog. A few lines more there for KPC-Links' OWN watchdog would have
     caught the 19 Nov miss with no PC. The PC heartbeat sent to Brandon is the backup. Small change for a club session, not an agent.
16. **THE PC HELPER IS NOT SET UP FOR HAND DOWNLOADS YET (Fable, 19 Nov 8:35 AM; Brandon: "My pc helper when the time comes everything
   will be set up to run it?").** Before Brandon is asked to download anything (after the release is signed off): (a) pick the
   files that are wanted: rows where hand-off 02 and 03B agree, plus a done layer only when its source changed; (b) each becomes a
   row of `data/needs-download.json` with a STATE and a layer id the US key knows, `who` person, `status` open; a NEW layer first
   gets its layer entry (`data/state-gis.json` is a rule file: draft PR, Fable reads it); (c) test exactly as on 19 Nov:
   `python3 tools/kpc_pc_helper.py --list --needs <the list>` must show those layers, busiest first; (d) only then Brandon gets ONE
   line to run. He checks it himself with `python tools\kpc_pc_helper.py --list`.
17. **OPUS, ITEM 14's ORDER DONE (19 Nov ~9 AM CST; fresh chat, starter line of item 11).**
   - **(a) FACT CHECK of run 44528656941 (rules 7c6e01e1bc2b): DONE, table to Brandon.** OLD = published key 8140d35, NEW = main d5ae6ad3
     (37 saved) + release `key-held` (13 held); same shapes (boundary-cache unchanged since 18 Nov) and parkinfo/truth (unchanged since
     c4415276). Outlines 11,715 -> 11,591, verified 8,304 -> 8,366, flagged 549 -> 386, SHARED 278 -> 116, OTHER_PARK 44 -> 15. Lost 126:
     planned 125 (Q1 88, contest 18 incl. 2 exact-name, D4 15, D3 4, park-preserve 0), `reviewed-approx` rows left 0. Held states:
     PASS AK AR DE GA MT NC RI UT VA WY; **STOP for Fable: FL + ID** (Rotenberger, Three Lakes, Bitterroot: SIZE_BIG on the SAME records;
     the published key had no `ac`, the run measured the union) **and OR** (Tillamook US-5461: Q1 took the approximate 627,317-acre record,
     the 21-acre one left is 40.3 km from the pin and held by the 5 Nov 15 km rule -> pin; the offline forecast lacked that rule). The 37
     saved states: nothing unexplained; their new PIN_FAR (NV, OK, WA) are in the forecast. Gold on NEW: TUNE wrong land 8 -> 2, too big
     9 -> 0, missing pieces 19 -> 29; SEALED 12: 0/0/0. Files: tools-out `key-quality/2026-11-19/factcheck-run-44528656941/` (README = the
     table + STOP list). The release run must NOT be a rerun to look: it waits for Fable's STOP reading and Brandon's yes per state.
   - **(b) #277 MERGED** (d19083c4, squash; no key run in flight; no small run, item 1).
   - **(c) #278 ROUND 2 READY FOR FABLE** (299d354b, rebased on main; US 7c6e01e1bc2b -> **90b7fc0a1d2c**): R-PP1a pin exception
     (`preserve_apart(..., P=P)`, the build's own `inside()`; a 0,0 pin is no pin; kept rows named once in a notice as a person's question):
     real pins tested: Wrangell-St. Elias + Craters of the Moon KEEP the preserve, Katmai / Lake Clark / Gates of the Arctic move. Owner's
     line in changelog + scope (`check_hash_pair` OK); Colorado named in the scope `why`. Florida: ONE measure run **44548425526** on the
     branch, 13 scope states, commit off: read its notices in the Fable sitting. Round 1's `ac2ab4c` (03A's acceptance figures) is still
     reachable by SHA (a tag push is blocked from the chat box).
   - **(d) 03B kit: Fable's** (tools-out `handoff-03/`), nothing for Opus.
   - **NEXT: ONE Fable sitting** (#278 round 2 + run 44548425526's notices, the table's STOP list, T1 run 2), then Brandon's yes per state ->
     KPC_DROP_OK -> ONE release run (Q1, held states, NPS, #277, R-PP1a), then kit D, then the step 3 PR.
   - **Brandon's eyes (19 Nov 8:56 AM: "Give my eyes.. I cant see all the information you all see"):** one page for him, private to him:
     https://claude.ai/artifact/3ZEKuejQhixfkd6HziB3CK ("Key Run Check, 19 Nov"): the totals, the 13 waiting states (green / red),
     and a card per changed park (131) with a small map: outline today, outline after the run, POTA's pin, the reason in plain words.
     Built from tools-out `factcheck-run-44528656941/`. Future tables to Brandon: give him a page like this, not only text.
   - **BRANDON HOLDS HIS YES (19 Nov 9:04 AM: "I not confident i can make the right choice at this time we will let fable do his round
     and see if has any more solutions at solving this...more research, bots etc etc").** No state is released, no KPC_DROP_OK, no
     release run. FOR FABLE'S SITTING: besides #278 round 2, the STOP list and T1 run 2, bring Brandon ways to make the per-state call
     easier or safer: what research, outside-agent passes or bots could settle the lost outlines (the Q1 pins, D4 lakes, contest
     parks) before or after the release, so his yes rests on more than the rules. Show him on his review page, not only in text.
18. **HAND-OFF 03A CAME BACK + A HOST RULE THAT MAY BE WRONG (Opus, 19 Nov 9:10 AM; Brandon 9:07-9:08 AM: "my outside agents keep
   thinking they was told not to use arcgis...they should check robot.txt" / "It maybe a rule on the repo that is wrong"). FOR FABLE'S SITTING.**
   - **03A = KPC-Data draft PR #124** (the review packet bot, three files, not merged, never run). The agent could not fork and was told not
     to run jobs on club repos, so it built AK, ID, CO offline from 8140d35 and ac2ab4c: scope 13 states, the same five parks, the R-PP1
     notice lines word for word (Colorado's Great Sand Dunes line too), US-0665 verified -> flagged 22.7 km, US-0069 pin 0 -> 2.79 km, gold
     the same both sides. Small differences left as they came: ID FAR_PIECE 12 vs our 13; gold missing pieces 20 vs our 19 of 65; a few
     notice lines one sentence apart (likely shapely on its side: our hand files were built without it; section 14). Ten states not
     built; part 2 (`run` mode) not added. **NO FORK NEEDED:** the hand-off's rule was "a club session reads it before it is merged or
     started": a club session reads #124's code, then starts its acceptance run on KPC-Data itself (by hand, never red, writes only
     tools-out `key-quality/review-packets/`) against #278 at ac2ab4c (still reachable by SHA). Then the agent adds part 2.
   - **GREY AREA G-NET1, the host rules.** The bots' `kpc_net_guard.py` (KPC-Links + `kpc_master.NEVER_CONTACT`, `kpc_preflight.HOST`)
     HARD-CODES: services*.arcgis.com, apps.fs.usda.gov, ncnhde.natureserve.org, Grant County NM: no request of any kind, robots.txt
     included. Brandon told the outside agent (t245u, its NOTES item 6): "all old per-host bans dropped ... robots.txt is the only test".
     What robots.txt says (agent, 19 Nov): services*.arcgis.com = "User-agent: * / Disallow: /" (so those stay off under either rule:
     ArcGIS's own no, not ours; a person's browser download is the way); **ncnhde.natureserve.org ALLOWS (Crawl-delay 10)**: our ban is
     stricter than its robots; apps.fs.usda.gov answers robots.txt with 403 (RFC 9309: a 4xx = no rules = allowed; the agent treated it
     as blocked, but treated POTA's 403 as allowed: inconsistent). History: an Oct 31 test report (KPC-Data `draft/tools/kpc_parcels/
     TEST_REPORT.md`) got a 403 from services*.arcgis.com robots for our UA and the layers opened; a later club rule read "a 403 counts
     as a disallow", then the hard ban. Questions for Brandon: (1) bots too: robots.txt the ONLY test (drop the hard-coded list, keep
     fail-closed when robots says no)? (2) a 4xx on robots.txt: allowed (the standard) or blocked (our old reading)? Recommended: (1) yes,
     (2) allowed for 404, ask for 401/403. Only after the release sign-off: a host change reads layers anew and would change the shapes.
     Hand-off 03B's README now says ArcGIS is not off limits; robots.txt is the only test.
19. **RULE SHEET R-NET1, WHO THE BOTS MAY ASK (Opus draft, 19 Nov 9:15 AM; Brandon 9:11 AM: "Set the rule up as you see fit so we
   are polite and following the rules. We only avoid restrictions etc"; 9:12 AM: "Have fable review the rule"). NOT IN FORCE: Fable
   reviews first; no code until then.** Replaces G-NET1's questions (item 18).
   1. **What counts as allowed:** any plain http(s) address whose site's robots.txt allows our ONE honest name
      `KPC (kentuckyportableclub.github.io)` (never changed to get around a no), read with the club's existing reading (store engine
      3.6.2, `kpc_manners` / `kpc_inbox_manners.robots_page`): 404, 410, 401, 403 and any other 4xx but 429 = no rules (the standard,
      RFC 9309); a page with no robots lines from the site's own address = no rules. ArcGIS is like any other site.
   2. **What does not:** a robots.txt "no" for us or for every agent, redirects included (each hop checked); 429 / 5xx / no answer on
      robots.txt = no for this run, try another day; a 401 / 403 / 429 on the DATA request = stop that host for the run (no retry
      with tricks); a site's terms that forbid automated use (`never_contact` true in layers.json, with the terms as the reason); a
      sign-in or a key (except the two keyed APIs Brandon approved); WDPA / Protected Planet geometry (licence).
   3. **Sources, best first:** the site's own live robots.txt; when it cannot be read by us (4xx) but a dated public reading says
      "no" to EVERY agent, that reading stands (polite case: services*.arcgis.com said "User-agent: * / Disallow: /" to the outside
      agent on 19 Nov while it answered our bot 403 on 31 Oct). Re-read monthly; the reading lives in a small table with its date.
   4. **When unsure:** no request; the row goes to the hand-download list (Brandon's PC or the agent), never a workaround.
   5. **Manners kept as today:** 1 request per 2 s per host, hub portals 60 s, Crawl-delay obeyed when longer, back off on 429 / 5xx,
      three strikes, contact nobody. **Dropped:** the hard-coded host bans that act BEFORE robots.txt (services*.arcgis.com,
      apps.fs.usda.gov, ncnhde.natureserve.org, the Grant County NM server; Brandon already dropped them for the agents, t245u).
   6. **Examples (from the agent's 19 Nov notes and the 31 Oct test):** services*.arcgis.com = NO (its published no to every agent;
      a person downloads); hub.arcgis.com download that redirects there = NO at the redirect; www.arcgis.com catalog = YES;
      an agency's own ArcGIS Server (kygisserver.ky.gov/arcgis/rest) = YES if its robots allows; ncnhde.natureserve.org = YES at 10 s
      (Crawl-delay 10; today banned by us); apps.fs.usda.gov = YES (robots 403 = no rules), STOP if the data answers 403;
      api.pota.app = YES (robots 403 = no rules, as today); gis.ohiodnr.gov, resources.gisdata.mn.gov, lastateparks.com = NO
      (Disallow: /); papionrd.org = NO (names our agent); floridastateparks.org pages answer 403 = STOP.
   **Code after Fable's yes (one draft PR per repo):** KPC-Links `kpc_net_guard.py` (drop SERVICES_RE / NEVER, add the dated
   readings table), `kpc_master.py` (NEVER_CONTACT, SAVED_ONLY_HOSTS, the arcgis check in live_ok), `kpc_preflight.HOST`; KPC-Data
   `kpc_host_rules.py` (same). Tests: the 6 examples. **Merged only AFTER the release is signed off** (newly readable layers change
   the shapes the fact check measured). Then one by-hand cache run for the rows it opens (ncnhde NC heritage, the USFS files).
   **For Fable:** is point 3's polite case right, or should a 403 to us simply mean "no rules" for ArcGIS too?
20. **FABLE'S SITTING 3 (19 Nov ~10 AM CST; Brandon 9:14 AM: "Review what Opus has ready (items 17, 18 and 19) ... look for more
   research, outside-agent checks or bots that would make my yes per state safer, and show me on my review page").** Files: tools-out
   `key-quality/2026-11-19/fable-sitting-3/` (README). Read-only: no bot run, no key or rule changed. Brandon's page is updated.
   - **#278 round 2: NOT YET, ONE small change (comment on the PR).** Both round 1 changes are right; hash 90b7fc0a1d2c and the gate OK;
     the rule's own function on real shapes / rows / pins, all 13 states: AK moves Gates of the Arctic, Katmai, Lake Clark and keeps
     Wrangell-St. Elias; ID keeps Craters of the Moon; Florida and ten more: nothing. What fails: **Colorado.** The pin of the PRESERVE
     number US-8295 Great Sand Dunes is inside the National PARK record, so the pin exception kept the park's land on the preserve's
     number and printed it as a question for POTA. POTA numbers both (US-0033 + US-8295): nothing to ask. The unit-code step gave the
     record back, so the key ends right, but the rule is wrong there and the notice is false. **R-PP1a amended (Fable; waits for the
     owner's yes):** ... OR POTA's own pin sits inside that record AND POTA has no number of its own for that part. Round 3: keep a row by
     the pin only when `KR.d9_winner(record name, the OTHER parks' names)` is None; test with US-8295's real pin; new hash. **Stamp agreed
     ahead** (no new sitting) if the diff is only that + its test + the hash lines, tests ALL PASS, and ONE measure run, states AK CO ID,
     shows in its JOB LOG: AK as now; CO `R-PP1 ... 2 record(s)` and no R-PP1a line; ID R-PP1a US-0665. Anything else: back to Fable.
   - **NOTICES: READ THE JOB LOG, NOT THE ANNOTATIONS.** GitHub keeps the first 10 notices of a step. Run 44548425526's annotations held
     Alaska only; `gh api repos/<repo>/actions/jobs/<job id>/logs` gave all 111 notice lines from the chat box. CLAUDE.md's annotations
     line loses every state after the first in a one-step, many-state run. The measure run also does not apply the 15 km hold (OR 382
     joined there, 378 in the release run's files; NV 219 / 195): it shows a rule's notices, it is not a forecast of the release.
   - **STOP LIST: FL, ID, OR CLEARED.** The three SIZE_BIG flags are a COUNTING error: with no union `ac` (the shapely union skips parks
     over 400 rings / 60,000 points), `KR.measured_ac` (KPC_MEASURED_ACRES) ADDS the rows: PAD-US + the state copies of the same land.
     Reproduced to the acre. True union: Rotenberger 31,847 (key 67,913; agency 29,000+), Three Lakes 66,020 (189,872; 63,000+),
     Bitterroot 1,651,125 (2,117,033; USFS report NFS 1,594,735, gross 1,664,512; the "official 743,000" is the wilderness share).
     Same records as the published key: the outlines do not change. Country-wide: 116 parks carry an added-up `ac` with 2+ rows, 84 are
     1.10x or more over, **10 SIZE_BIG flags are false** (FL 2, WI 6, CT 1, PA 1), no size witness is false, no SIZE_SMALL is hidden.
     Cause + fix AFTER the release (rule file: draft PR, Fable reads): `measured_ac` never adds across layers (union, or the largest
     layer family as the fact check's estimate does); test = the three parks. OR: Tillamook to a pin is RIGHT: record 241270 is every
     Board of Forestry forest in Oregon (608 pieces, 468 km north to south, 627,317 ac; the forest is about 360,000); the ODF layer is
     known (hand-off 02 pass 1, a person's download).
   - **NEW STOP: MONTANA, US-4501 Custer Gallatin NF (285 activations).** D7 sends the statewide copy sgmtd1213 to check "the managing
     agency's own record is joined", but only PAD-US 2652 (Custer NF, 1,115,748 ac) is joined; PAD-US 2660 "Gallatin National Forest"
     (1,850,408 ac, same Loc_Nm) sits in `nonum`. Outline 3,399,571 -> 1,143,001 ac; class stays verified (the pin is in the Custer
     part), no flag, not on the table. 2652 + 2660 = 2,966,156; the USFS report's Montana NFS = 2,966,225. **Fix before the release
     run: evidence batch 02**, one saved answer joining 2660 to US-4501 (evidence: the report + the two PAD-US fee records), Fable
     reads it like #277. Of 160 parks with a D7 row (all 50 states) this is the only one with an unjoined record of the same manager
     under the copy. **To look at (outside agent, which acres are open public land):** MT US-0399 Charles M. Russell NWR (FWS 935,617;
     joined 422,061; the dropped copy 954,399), US-0408 UL Bend (56,090 / 39,036); VA US-0563 Mason Neck (2,277 / 1,467), US-0572
     Rappahannock River Valley (11,365 / 7,938). Some FWS acres are private easements (Hailstone, Black Coulee: smaller is right).
   - **WHAT A YES CHANGES, 13 held states (the table counted lost outlines only):** 63 outline -> pin; 107 keep an outline but shrink 2%+;
     115 same land (copies dropped); 17 trails to the trail line; 4 bigger + 2 new outlines (Nez Perce NHP in MT and OR by unit code).
     New land of 100+ acres in 4 parks only: ID US-10429 Middle Fork Clearwater +44,581 and US-0890 Salmon +15,257 (each a federal
     record with its exact name), MT US-0054 +196, AR US-7184 +190. **Item 3d's table gets two columns from now on:** "keeps an outline
     but loses 20%+" and "new land 100+ ac", both by park.
   - **FOUND ON THE WAY, ON THE MAP TODAY (not this run): the Idaho key joins the USFS ownership layer's NOT-Forest-Service record.**
     Layer `EDW_BasicOwnership_02` (sgidd, `what: owned`, joined by `forestname` alone) holds one record of Forest Service land and one
     or two of other owners per forest; 11 parks carry both (US-4398 4474 4475 4477 4478 4479 4480 4481 4500 4505 4387), about
     2,902,000 acres. In ten of the eleven the largest record = the report's NFS acres within 1% and the rest = its gross minus NFS
     within 3-17%. Breaks "agency-owned land, never proclamation lines". Fix AFTER the release: a filter on the layer's owner-class
     field in `data/state-gis.json` (rule file: draft PR, Fable reads), then that layer re-read.
   - **T1 RUN 2 (44542262740): READ. Enough to rule; the answer is NOT ON THE MAP YET.** 30 traced (10 / 10 / 10 by the list; US-1601 was
     binned small on a wrong 57 ac). 19 refused (11 NO FIT, 6 NO LINE, 2 NEEDS A PERSON): safe, a refusal is a pin. 11 DRAWN, all GeoPDF
     (every control-point fit was refused): 7 GOOD, 2 TOO BIG (US-5427 Mount Hunger SF 1.42x, US-1601 Susquehanna SP 1.37x: a third of
     the trace outside, the colour fill swallowed neighbouring land), 2 MISSING PIECES (US-9058; US-9074 one of five parts), 0 WRONG
     LAND. The measure reproduces (US-5427: 838.9 / 590.3 ac, covered 0.986, outside 0.306). 8 of 11 drawn are NY DEC maps: not a
     general result. The throwaway branch `trace-test` can be deleted (traces are on tools-out).
     **DRAFT SHEET R-G9 (T3), NOT IN FORCE, for Brandon:** (1) counts: nothing yet; a traced line is never an official outline and
     never feeds a 2-fer. (2) does not: any trace from a map without its own coordinates; any trace the tracer refused. (3) sources:
     the agency's own GeoPDF, then the agency's published acres as the size check (a number the tracer never sees). (4) unsure = pin.
     (5) if ever shown: its own layer, labelled "traced from the agency's picture map (unofficial)", with the short notice. (6) the
     bar before any is shown: a gate of traced acres within 10% of the agency's acres (run 2: 5 pass, all GOOD: too few to prove),
     then a test of 60 gated traces with at most 1 TOO BIG and 0 WRONG LAND; plus "take every shape of that colour on the page or
     none" for missing parts.
   - **KPC-Data #124 (review packet bot): NOT YET, three fixes (comment on the PR). Do not merge, do not start.** (1) the workflow is
     invalid: `continue-on-error` twice on two steps; (2) no `GH_TOKEN` on any `gh` step: no shapes, an empty packet; (3) workflow-wide
     `contents: write` + `actions: write` while the PR's own code runs, the write credential kept in the packet job's checkout, and a
     typed PR number may be a stranger's fork: read-only everywhere, one last save job that runs no PR code, refuse a head repo that is
     not KPC-Links. The script is clean (no network, writes only in the packet folder, selftest passes, matched AK / ID / CO).
   - **R-NET1: YES WITH FOUR CONDITIONS (waits for Brandon's yes to the sheet as amended; code after the release, as written).** The
     polite case of point 3 is RIGHT: a 403 to us is not "no rules" when a dated reading shows the site says no to every agent. Checked
     against RFC 9309 (4xx = unavailable, may fetch; 5xx / no answer = assume no; rules belong to the exact host; a read is good for
     24 hours) and `kpc_inbox_manners.robots_verdict` (already reads it so). Conditions: (a) one dated reading per EXACT host
     (services, services1 ... each has its own robots.txt); (b) a reading older than 35 days with no re-read = unsure = no request,
     never a silent yes; a no turning into a yes needs a person's eyes; (c) robots.txt 401 / 403 AND the first data request 401 / 403 =
     the host is parked in the table until a person looks, not tried every run; (d) the readings table missing or unreadable = no
     request at all (fail closed, as the never_contact flags). Also: "no" is tested per address, longest match, Allow wins a tie; the
     live robots.txt is read every run. I could not read services.arcgis.com/robots.txt from the chat box: its "Disallow: /" is the
     outside agent's 19 Nov reading only.
   - **WAYS TO MAKE THE YES SAFER (on Brandon's page):** (1) a yes for NAMED PARKS: `kpc_key_drop_guard.py` lets ANY drop through for a
     state in KPC_DROP_OK; give it an approved list (state -> park numbers) and hold a state that loses any other outline; (2) the run's
     own table gets the shrink watch, the unjoined-record-under-a-dropped-copy check, true-union acres and the kit C tables (no
     network; scripts in fable-sitting-3/scripts are the pattern); (3) evidence batch 02 before the release run; (4) outside agent, two
     blind passes: the four refuges, the two Idaho river corridors, then the 63 pins busiest first; (5) kit D moved BEFORE the yes: 60
     random parks from the 13 states' would-be files; (6) the undo path written down (a state's files as of 8140d35); (7) after: the
     members' page, the POTA question.
   - **WAITING FOR BRANDON:** Montana waits for evidence batch 02; the named-parks guard before the release run; R-PP1a's amended
     wording; R-NET1 with the four conditions; R-G9 (traced lines stay off the map). **OPUS'S ORDER when he answers:** (a) #278 round 3;
     (b) evidence batch 02 (draft PR, Fable reads); (c) the named-parks guard + its test; (d) #124's three fixes go back to the outside
     agent; then Brandon's yes per state on the page -> ONE release run. Nothing is released before that.
21. **BRANDON'S ANSWERS + 03B SCORED + #124 SECOND READ (Fable, 19 Nov 10:15 AM CST).**
   - **The owner's yeses to item 20's five questions.** 10:06 AM: "1-4 no clue what your asking 5 i agree" (asked again in plain words on
     his page); 10:12 AM: **"1-4 I agree with your thoughts for now maybe revist later if new rules or info changes"**. So, all FOR NOW:
     (1) Montana waits for evidence batch 02 (Custer Gallatin US-4501); (2) the named-parks drop guard is built before the release run;
     (3) **R-PP1a as amended is APPROVED FOR NOW, decided_by KPC owner, 2026-11-19 (10:12 AM)**: the pin exception only where POTA has
     no number of its own for that part (#278 round 3's changelog line quotes his 10:12 words); (4) **R-NET1 with the four conditions
     is APPROVED FOR NOW** (code after the release, as written); (5) **R-G9: traced lines stay off the map** until the bigger test of
     the draft sheet passes (10:06 AM "5 i agree").
   - **Evidence batch 02, approved AHEAD (no new sitting) if it is exactly this:** ONE saved answer joining PAD-US 2660 "Gallatin National
     Forest" (its own Loc_Nm is "Custer Gallatin National Forest") to US-4501, fingerprint from the shape cache, evidence = that Loc_Nm +
     the USFS Land Areas Report FY2025 (Custer NF Montana 1,115,757 + Gallatin NF 1,850,468 NFS acres); a test build of Montana in which
     exactly ONE park changes (US-4501 gains 2660; about 2,966,156 ac); the tests pass. Anything more goes to a Fable sitting. The
     refuges (US-0399, US-0408, US-0563, US-0572) are NOT in it: they wait for an outside agent's look.
   - **HAND-OFF 03B, PASS 2, IS BACK AND SCORED** (tools-out `key-quality/2026-11-19/handoff-03/answers-pass2/`, SCORE-READ-FIRST.md).
     Planted answers 3 of 5: job 2 and job 4 right; job 3 one right, one left empty, **one WRONG (Mount Magazine SP: NOTHING where the
     Arkansas State Parks layer holds it)**: a pass-2 NOTHING is not proof. **Job 2: 9 of 9 rows agree with pass 1**: those official
     acres now count (Tallgrass 10,882.67 / 33.12 federal; Timucuan 46,262.76 / 17,122.67; Craters NM 53,437.64 with the preserve its
     own row; Osage 7,329 + 3,722; Acadia Cliffs 273 / 275.25; Diamond HMA 166,632; Longview Saline 6,020, WMA and natural area the
     same land; Tillamook 364,000 in the plan, 359,8xx Board of Forestry land in two districts; ODF's own zip is at
     gisapps.odf.oregon.gov, no forest-name field). **Job 4: both passes agree on every row**: no preserve number, POTA's page does
     NOT SAY (the five R-PP1 parks, Denali, New River Gorge, Jean Lafitte, Oregon Caves): only POTA can settle R-PP1a and G-PP2.
     **Job 3: both say GIS for 18 parks** (21 rows; `SCORE-job3-both-passes.csv`); 24 rows where pass 1 said GIS do NOT count (TVA dam
     parks with no park-named record, four rivers with no boundary in the Park Service's own layer, containing areas); 10 open rows
     are NOTHING. **Six of the 18 are Forest Service BOUNDARY layers** (Custer Gallatin 3,412,203 ac = the report's gross): never drawn
     (owned land only). Nothing is a saved answer or a layer yet; no hand download before the release sign-off (item 14).
   - **R-NET1, A CORRECTION TO ITEM 20: the ArcGIS "published no" is NOT shown.** Pass 1 (agent 1) wrote services*.arcgis.com robots.txt
     = "User-agent: * / Disallow: /". Pass 2 (agent 2) got 403 "Invalid URL" (no robots file), re-checked, says the owner checked too,
     and then read layers on services, services1, 2, 6, 7, 9 (about 120 requests, none refused). Our bot got 403 on 31 Oct. Two readings
     against one. Added to the conditions: **a "no" our bot cannot read for itself needs two readings that agree, or the owner's own
     eyes.** For ArcGIS that is not met, so point 1 decides when the code is built: robots.txt 403 = no rules = allowed, with the manners,
     and STOP on a 401 / 403 / 429 from the data. My line "ArcGIS-hosted layers stay a person's download" is withdrawn. Asked of
     Brandon, no hurry (nothing changes before the release): what his phone shows at services.arcgis.com/robots.txt. 440 of the 487
     PC rows of the hand-download list are on those hosts.
   - **KPC-Data #124, second read (5fb5803; the agent acted on the PR comment by itself within three minutes): the three fixes are
     right** (no repeated key, signed-in `gh`, read-only except the `save` job, outside pull requests refused, tests ALL PASS). **One
     small thing left (second comment on the PR):** `build` and `packet` ask for `actions: write` (not needed to upload a run file),
     and the build step holds `GH_TOKEN` while it runs the pull request's key builder: drop the permission, keep the token out of that
     step. Then: a club session MERGES it (GitHub starts a by-hand workflow only when its file is on main), then ONE acceptance run:
     pull request 278, new ac2ab4c80723ae3ebf19261339c339b3da6f849c, old 8140d35e14923e7fa17cc25254c854d78e3a86c2, states AK ID CO.
     **A comment on that PR starts the outside agent: write there only what it should act on.**
   - **OPUS'S ORDER NOW (fresh chat: "Read CLAUDE.md and key-quality.md section 19, do item 21's order"):** (a) #278 round 3 as item 20
     says, ONE measure run states AK CO ID, read its JOB LOG, stamp and merge if it reads as agreed; (b) evidence batch 02 as above;
     (c) the named-parks drop guard: `kpc_key_drop_guard.py` takes an approved list (state -> park numbers, written from Brandon's page:
     the lost outlines of `factcheck-run-44528656941/lost.json` for the states he names) and holds a state that loses any outline not
     on it; test both ways; (d) #124: read the agent's last fix, merge, the ONE acceptance run; (e) the run's table gets the two new
     columns of item 20 (shrinks 20%+, new land 100+ ac). Then Brandon's yes per state on his page -> the list -> ONE release run
     (Q1, held states, NPS, #277, R-PP1a, batch 02). Nothing is released before that. After the release: `measured_ac`, the Idaho
     ownership layer filter, R-NET1's code, the hand downloads both passes agree on, kit D.
22. **KPC-Data #124 MERGED + THE ONE ACCEPTANCE RUN STARTED (Fable, 19 Nov 10:16 AM CST; Brandon 10:13 AM relayed the agent: "ready for
   a club session to review and merge ... first run should be pull request 278 at the two hand-off commits, for AK, ID, and CO").**
   - Third read (e15a873): no job asks for an `actions` permission; the shapes download is its own signed-in step; the builds run
     with `env -u GH_TOKEN -u GITHUB_TOKEN`; tests ALL PASS; no repeated key. Squash-merged as KPC-Data **59465a7c**.
   - **Run 44564132024** (KPC-Data `kpc-key-review-packet.yml`, by hand: pr 278, new ac2ab4c8, old 8140d35e, states AK ID CO). NOT
     polled. Read next: tools-out `key-quality/review-packets/pr-278-ac2ab4c/summary.md` against
     `handoff-03/A-build-review-packet-bot/reference/`. Expected: AK four parks (US-0026, US-0044, US-0048, US-0069), ID US-0665
     verified -> flagged 22.7 km, CO 0 of 276 with the 2-record R-PP1 notice, gold the same both sides. No packet = read the job log
     (`gh api repos/KentuckyPortableClub/KPC-Data/actions/jobs/<job id>/logs`), do not rerun to look.
   - The red run 44550258133 (9:02 AM, push) was the agent's FIRST version: its workflow file was invalid (the repeated key), so
     GitHub failed it on the push. Nothing ran. The later pushes made no run.
   - Part 2 (`run` mode) waits for this packet to be read; Brandon starts the agent on it then.
