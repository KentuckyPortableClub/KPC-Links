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
