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
     on it; test both ways; (d) #124: MERGED and the ONE acceptance run STARTED by Fable (item 22): do NOT merge or run again, only READ its packet against the hand figures and tell Brandon whether it matches (Brandon 10:24 AM: Opus checks it at 12, then he starts the agent on part 2; a mismatch = part 2 waits); (e) the run's table gets the two new
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
23. **R-NET1, THE ARCGIS LINE IS SETTLED BY THE OWNER'S OWN EYES (Fable, 19 Nov 10:25 AM CST; Brandon 10:23 AM, a screenshot of his
   phone).** `https://services.arcgis.com/robots.txt` in his browser shows two words, **"Invalid URL"**: no robots file. That is the
   third reading that says so (our bot 31 Oct: 403; agent 2 on 19 Nov: 403 "Invalid URL"; the owner 19 Nov 10:23 AM) against agent 1's
   "User-agent: * / Disallow: /", which is withdrawn. So in the sheet (item 19): point 3's polite case stays as a principle but has NO
   example today, and point 6 changes: **services*.arcgis.com = YES like any other site** when the bot's own live read of that host's
   robots.txt gives no rules (an error page with no robots lines, or a 4xx other than 429), at the usual manners, and STOP that host
   for the run on a 401 / 403 / 429 from the data; a hub.arcgis.com download that redirects there = YES when every hop passes. The four
   conditions of item 20 and the two-readings line of item 21 stand. **Nothing changes before the release sign-off** (item 19: newly
   readable layers change the shapes the fact check measured): the code comes after, then 440 of the 487 PC rows of the hand-download
   list become BOT rows and one by-hand cache run reads them. The outside agents may open those hosts under the same manners (the
   owner already told agent 2 so).
   - Acceptance run 44564132024 at 10:23 AM: scope and the three builds (AK, CO, ID) finished green, the packet job was running. Not read yet.
24. **OPUS, ITEM 21's ORDER (19 Nov ~10:30-11 AM CST; fresh chat, "Read CLAUDE.md and key-quality.md section 19, do item 21's order").**
   - **(a) #278 ROUND 3 PUSHED, NOT YET STAMPED** (3dd62f44; US 7c6e01e1bc2b -> **ee2b6f1e9673**). `preserve_apart` keeps a row by POTA's pin
     only when `KR.d9_winner(record name, the state's OTHER parks' names)` is None. Test with US-8295's real pin (37.7335, -105.512): the park
     record 3446 moves, nothing asked; with no POTA number for the park part the pin still keeps the row; US-0069 / US-0665 still keep the
     preserve. Scope `why` + `approved` and the changelog quote the owner's 10:12 words; `check_hash_pair` OK; R-PP1 test ALL PASS; preflight:
     only the known master check FAIL (3 suspect baselines, same on main). Diff = that + its test + the hash lines. **ONE measure run
     44567629638** (branch, us, states AK CO ID, commit off) was QUEUED behind the bot queue's live-refresh key run 44567326912 (same lock,
     started 16:32 UTC by kpc-bot-queue). **NEXT (no polling): read its JOB LOG** (`gh api repos/KentuckyPortableClub/KPC-Links/actions/jobs/<id>/logs`),
     expect AK as now (R-PP1 3 moved + R-PP1a US-0069), CO `R-PP1 ... 2 record(s)` and NO R-PP1a line, ID R-PP1a US-0665; if so add
     "Reviewed: Fable, 2026-11-19 (stamp agreed ahead, item 20)" to the changelog line, mark ready, merge (squash).
   - **(b) EVIDENCE BATCH 02 CANNOT BE DONE AS APPROVED: FOR FABLE.** The saved answer exactly as item 21 says (join 2660, fp ['Gallatin
     National Forest', 1850408], evidence = Loc_Nm + LAR FY2025 Table 3/5/28, Box link of the owner's download) is on branch
     `prep/evidence-batch-02` (b913a01, NO PR). A Montana test build (19 Nov saved shapes, main's rules, same start files both sides)
     changes **0 parks**: the saved-answer join path takes a record only when it lies within 0.6 deg of the box around POTA's pin
     (`near(la, lo, a['_bb'], .6)`, also in the fingerprint re-find). POTA's pin is in the Ashland district (45.5048, -105.997); 2660's box ends at
     -109.556. G-1 (far same-name pieces) does not help: 2660's own name is 'Gallatin National Forest'. **To make it count = a rule change
     (moves the hash, owner's yes):** e.g. a person's join BY ID with an `evidence` block and a matching fingerprint (same id, or same name +
     acres within 10% in the SAME layer) joins at any distance, as G-1 does for names. Montana stays held until then; the release run
     can go without Montana.
   - **(c) NAMED-PARKS DROP GUARD = draft KPC-Links #281** (not a rule file; hash unchanged). `.github/key-drop-approved.json` {state:
     parks, decided_by}; a listed state is held if it loses ANY outline (key joins or outline file) not named, whatever its percent or
     KPC_DROP_OK; `approve --lost lost.json --states ... --decided-by ...` writes it. No list in the repo today. Test both ways ALL PASS.
     Fable reads it in the next sitting; merged before the release run.
   - **(d) #124 ACCEPTANCE PACKET (run 44564132024): MATCHES the hand figures** (tools-out `review-packets/pr-278-ac2ab4c/` against
     `handoff-03/A-build-review-packet-bot/reference/`): the same five parks, records, acres and class (US-0665 verified -> flagged 22.7 km,
     US-0069 pin 0 -> 2.79 km), AK / ID counts as the reference fact check, CO 0 of 266 changed with the 2-record R-PP1 notice, gold the
     same both sides. The packet CSV has three empty 'record gained' columns more: fine. **Brandon may start the agent on part 2.**
   - **(e) TWO NEW COLUMNS DONE:** tools-out `factcheck-run-44528656941/table-two-new-columns.md` + `shrink20-new100-parks.csv`, and on
     Brandon's page (each state chip). 60 parks shrink 20%+ (MT 15, AR 10, FL 8, ID 8 ...), 4 gain 100+ ac (ID 2 rivers, MT Nez Perce,
     AR Moro Big Pine). Biggest shrink: Yellowstone in MT 2,187,128 -> 160,257: RIGHT (D7 drops a statewide copy of the whole park; WY and
     ID keep their parts: 3483 2,003,734 / 3481 36,921).
   - **FOR BRANDON / FABLE: the bot queue keeps starting US key live refreshes** (kpc-bot-queue.yml, every 14 days per group; 16:32 UTC
     today: CT ID ME ND OH TN WV). Its "save new live reads to the saved outlines" step can change the shapes the fact check measured
     (item 13: nothing re-read before the release sign-off). Suggest pausing the queue's kpc-us-key jobs (move their `next` past the
     release) until the release is signed off. Not done: not asked.
25. **KEY REFRESHES OFF THE BOT QUEUE (Opus, 19 Nov 10:55 AM CST; Brandon 10:50 AM: "Yeah we dont need constant key refreshed we have fable
   make plans to fix").** All nine queue jobs (US key x7 groups, Canada, world) moved from `jobs` to `paused_jobs` in `data/bot-queue.json`,
   untouched; the queue now says "nothing to do" (tested). To bring one back, move it into `jobs`. The run it started at 16:32 UTC
   (44567326912: CT ID ME ND OH TN WV + held states) was left to finish; its drop guard holds what it should. **FOR FABLE:** plan the fixes
   in place of blind refreshes: which layers need a re-read and when (the keeper's change check, notes/layer-refresh.md, parked plan R-LR1..4),
   after the release sign-off, one by-hand run per batch of fixes.
26. **FABLE'S SITTING 4 (19 Nov 10:55 AM - 11:50 AM CST; Brandon 10:52 AM: "Fable your turn"; asked: review #281, rule on the Custer
   Gallatin far join, plan the fixes in place of refreshes). Files: tools-out `key-quality/2026-11-19/fable-sitting-4/` (README).**
   - **IDAHO AND OREGON WERE SAVED TO MAIN WITHOUT THE OWNER'S YES (run US-44567326912, bot queue start 16:32 UTC, commit 00d65a98,
     17:16 UTC).** The drop guard's count is NET. Evidence batch 01 (#277) gave back Milner (ID), Topsy and Bear Gulch (OR), Nez Perce is
     new in OR, so official 174 -> 174 and 344 -> 345 read as "no drop" while ID lost 3 outlines (US-2239, US-2240, US-2250, D4 lakes) +
     one grade (US-11530) and OR lost 9 (Tillamook SF US-5461 among them). Every one is on the fact check's list and both states were
     CLEARED in sitting 3; only the key files moved (data/outlines is not saved in a red run), but the site's tools read the key files.
     Item 19.2's "nothing reaches the map until Brandon says yes" was WRONG for this reason. **Brandon decides: leave ID and OR as they
     are (recommended: cleared, all planned) or put the two files back (`git show 00d65a98~1:data/us-key/US-ID.json`, tracts, index rows).**
     With Flathead fixed, Montana's count would have read 242 -> 242: the old guard would have saved Montana with Custer Gallatin cut.
   - **#281 THE DROP GUARD: REVIEWED, CHANGED, MERGED (3b033da6).** Not a rule file. Now: (1) NEVER WORSE IS JUDGED PARK BY PARK at
     limit 0: a park that lost its outline or its official grade holds its state unless the owner named it; a gain elsewhere never
     offsets it; (2) the list `.github/key-drop-approved.json` (state -> parks, decided_by) lets a state through only when every such
     park is named; KPC_DROP_OK cannot override a list; (3) **`stop`: a state held whatever its list says. MONTANA IS ON IT** (take it
     off only when R-FJ1 and its answer are merged); (4) the outline file follows the save's own rule (pin / in-no-key outlines left
     out on purpose are no loss: as first written it would have held ID, MT, UT after a yes); (5) `approve --lost lost.json
     grade-drops.json --states ... --decided-by ...` (refuses a stopped state). Proof: replay of that run's own files (main's guard 11
     held, this one 13 with the parks named); rehearsal on run 44528656941's files: full list = all 13 through, one park off = held.
     The guard's lost count equals lost.json in all 13 states (63 = 63).
   - **SIX PARKS KEEP THE SAME OUTLINE BUT GET THE "APPROXIMATE" LABEL (D7 "only a copy"; not on any table until now):** MT US-4502
     Flathead NF (190 act), US-11215 Bear Paw Battlefield, US-12630 Upper Missouri WSR; VA US-9899 Fort Hunt (106), US-9937 Meadowood
     (96); ID US-11530 Hells Canyon Reservoir (saved today). `grade-drops.json`; they go on Brandon's list with the lost outlines.
   - **FLATHEAD NF US-4502: A SAVED "NO" WAS WRONG = draft #284 (evidence batch 02a, answers only, no hash).** A 2 Nov chat NO ("pattern
     OUTSIDE/FAR", no evidence) kept PAD-US 2658 'Flathead National Forest' (USFS fee, 2,414,171 ac) off the park; the Forest Service's
     report says 2,414,170.7 NFS acres. The copy drawn today (sgmtd744, 2,649,452) is the gross boundary (report 2,650,379). #284 joins
     2658 with fingerprint + evidence and drops the NO; Montana test build: exactly ONE park changes (approximate on the copy ->
     official on 2658). Fable APPROVES on the facts; Opus reads it and merges (Montana is on STOP, so no release can ride on it).
     **"Blocks only remove" (section 5) is not safe:** a NO on the agency's own record leaves the worse copy drawn.
   - **#278 R-PP1a ROUND 3: STAMPED AND MERGED (20ad4c19; main's US rules = ee2b6f1e9673).** The measure run 44567629638 never ran (a
     scheduled boundary check took its place in the key lock's line and GitHub cancelled it). Checked by Fable's own builds instead (AK, CO, ID;
     main against the PR; KPC_KEY_REMATCH_IDS=1): AK exactly US-0026 / US-0044 / US-0048 lose the preserve record, US-0069 kept as a
     question; CO 0 of 276 change, no question; ID 0 change, US-0665 a question; 0 outlines lost. **`kpc-key-measure.yml` does NOT set
     KPC_KEY_REMATCH_IDS:** it prints a rule's notices but carries saved ids, so its keys show 0 change for parks joined already. For a
     rule PR use the review packet bot (KPC-Data `kpc-key-review-packet.yml`), never the measure run.
   - **RULE SHEET R-FJ1, A FAR JOIN BY A PERSON'S EVIDENCE (Fable draft; NOT IN FORCE: waits for the owner's yes).** Why: a saved join
     takes a record only within 0.6 degrees of the box round POTA's pin; Custer Gallatin's pin is at the east end, the Gallatin record
     (2660, 1,850,408 ac; report 1,850,468) 3.5 degrees west.
     1. Counts: the answer names the record by its exact id in `join` AND in a new list `far`; it carries `decided_by` and `evidence`
        (who, source, saw, date); the record read today still fits the saved fingerprint (same name, acres within 10% or 20 ac). The
        row is a person's join ('reviewed').
     2. Does not: a join by name; an id that is gone and found again by fingerprint (that search stays near the pin); no evidence or
        no fingerprint; a record on the park's NO list; an `approx` answer (Q1 keeps it a pin).
     3. Sources: the managing agency's own record + its published acres (Forest Service Land Areas Report; NPS and FWS acre reports).
     4. Unsure (name or acres no longer fit): no join, one check row "check (R-FJ1): the far record no longer fits its saved name or acres".
     5. People see the outline as any person's join; the run prints once per state "R-FJ1 far joins by a person's evidence: <park> <id> <name>".
     6. Examples: US-4501 + 2660 joins; the same answer without `far` = today (nothing); `far` id now under another name = check;
        `far` without evidence = ignored + warning; a NAME in `far` = ignored; Ouachita NF in Oklahoma US-4424 + 3001 would join
        (batch 03); Pine Island SP -> 'Pine Island' (1 Nov) has no evidence answer = G-1 as today.
     **Stamp agreed ahead (no new sitting) if exactly:** switch KPC_FAR_JOIN default ON; the join-path change; its test (the six
     examples); scope US-MT; changelog "APPROVED, decided_by KPC owner" with his words; ONE answer: US-4501 gains join 2660 + fp +
     `far` + evidence (the text of b913a01). ONE packet run, states MT, against main with #284 in: parks changed = US-4501 only
     (2652 name + 2660 reviewed, about 2,966,156 ac, sgmtd1213 still on check); switch OFF = 0 parks. Then Montana comes off `stop`.
   - **TWO SWEEPS (no network; saved answers and each key's `nonum` list against POTA's names):** 35 of the 738 saved NOs sit on a
     record with the park's OWN full name (Flathead is one; busiest: Delaware Seashore SP, Lake Dardanelle SP, Sandy Point SP, DeGray
     Lake, Buck's Pocket, Seneca Creek, Meramec): a second look by the outside agent, two blind passes (official acres; is this
     record the park). And **four forest halves in another state are a pin today** with the Forest Service's own record unjoined and
     its acres equal to the report within 10: Ouachita NF in Oklahoma (797 act), Sawtooth NF in Utah (163), Umatilla NF in Washington
     (120), Manti-La Sal NF in Colorado (111). EVIDENCE BATCH 03 under R-FJ1, AFTER the release (they add land, take none away).
   - **ALSO SEEN:** 12 old outlines of parks the key already grades pin sit in today's outline files (Henrys Lake Airstrip US-7816 in two
     state files, Willard Spur US-5779 ...); the first save that is not red drops them. The release run also takes about 63 planned
     outlines off the map in the 37 saved states (their outline files were never saved): they are on Brandon's page under all 50 states.
   - **THE PLAN IN PLACE OF KEY REFRESHES (Brandon 10:50 AM: "we dont need constant key refreshed we have fable make plans to fix").**
     What is OFF: the bot queue's nine 14-day key jobs (item 25) and the two monthly blind cache jobs (already off). What stays: the two
     nightly key starts (9:17 and 11:46 UTC), which build only states that new answers or a rule change touch, from the saved shapes.
     A layer is re-read only for a NAMED reason, one by-hand run per batch, each batch fact-checked old against new by the packet bot:
     1. BEFORE THE RELEASE (no layer re-read at all): #284; R-FJ1 on the owner's yes; the list from Brandon's page; ONE release run.
     2. RIGHT AFTER (answers and rule files, no re-read): evidence batch 03 (the four forest halves); `measured_ac` never adds across
        layers; the step 3 PR (dropped last word, `_keep`, same_land label); the bot job that writes the run's own table.
     3. FIRST RE-READS, by hand, one batch each: (a) the Idaho USFS ownership layer with its owner-class filter (11 forests);
        (b) R-NET1's code, then one cache run for the rows it opens (440 ArcGIS rows, ncnhde, USFS); (c) the 30 short layers and the
        three suspect baselines (CO sgcoa, OR sgorf, WA sgorf: reads cut off at 200).
     4. AFTER THAT a layer is re-read only when the keeper says it changed, or a person's row asks (notes/layer-refresh.md: built,
        off; turn it on by hand, `from_requests`), plus R-LR1's 180-day rule. No blind rotation again.
     5. Agents meanwhile (two blind passes each): the 35 saved NOs, the four refuges, the 63 pins busiest first, G-NPS1, kit D.
   - **OPUS'S ORDER NOW (fresh chat: "Read CLAUDE.md and key-quality.md section 19, do item 26's order"):** (a) read #284, mark ready,
     merge when no key run is in flight; (b) on Brandon's yes to R-FJ1: its PR exactly as the sheet says, ONE packet run MT, stamp as
     agreed, merge, then take MT off `stop` in `.github/key-drop-approved.json`; (c) on Brandon's yes per state: `approve --lost
     lost.json grade-drops.json` for the states he names with his words as decided_by, commit, ONE release run (check first that no key
     run is in flight and none is queued in the kpc-us-key lock), then empty `states`; (d) item 20's bot-table columns go to the packet
     bot's part 2 (the other Fable chat's PART-2-ADDITIONS). Not Opus's: R-FJ1's yes, the ID / OR choice, the yes per state.
27. **BRANDON'S ANSWERS TO SITTING 4 (Fable, 19 Nov 11:50 AM CST; Brandon 11:49 AM: "1 leave them 2 yes pins are only references they are
   not always right...have opus make handoff for the outaide agent").**
   - **Idaho and Oregon STAY as the 11:16 AM save left them** ("1 leave them"). They are released. Waiting for his yes now: 11 states
     (AK AR DE FL GA MT NC RI UT VA WY), Montana on STOP.
   - **R-FJ1 IS APPROVED, decided_by KPC owner, 2026-11-19 (11:49 AM: "2 yes pins are only references they are not always right").**
     The sheet of item 26 is in force as written; the PR's changelog line quotes those words. Stamp agreed ahead on item 26's
     conditions (ONE packet run, states MT, parks changed = US-4501 only). His reason is a principle to keep: POTA's pin is a
     reference, not proof; a person's evidence about a named record outranks the distance to the pin.
   - **HAND-OFF 04 FOR THE OUTSIDE AGENT: OPUS MAKES IT** (tools-out `key-quality/2026-11-19/handoff-04/`; the form of hand-offs 02
     and 03: README-FOR-THE-AGENT, one answer sheet per job, no keys in the zip, planted known answers with their key apart in
     `kit-keys/`, TWO fresh sessions, never pass 1's answers to pass 2, a row counts only where both agree; robots.txt is the only
     host test, ArcGIS included). Each row asks the same four things: the official page, the official acres, where the official
     outline lives, and a YES / NO / PART on the record named. Jobs, busiest parks first:
     A. the 34 saved NOs on a park's own full name (`fable-sitting-4/saved-no-on-own-name-35.csv` without Flathead): is the refused
        record the park? Give the record's name and acres, never our NO or its reason (blind).
     B. a SECOND WITNESS for the seven Forest Service figures that rest on one pass (kit C): the report's NFS acres for Flathead NF,
        Custer NF in Montana, Gallatin NF, and the state portions of Ouachita (OK), Sawtooth (UT), Umatilla (WA), Manti-La Sal (CO)
        (`cross-state-forests.md`): table and row named. Batch 03 and R-FJ1's answer count on it.
     C. the five parks left with only a state's copy (`grade-drops.json` without Flathead): Fort Hunt, Meadowood, Bear Paw
        Battlefield, Upper Missouri River, Hells Canyon Reservoir: does the managing agency publish its own outline, and its acres.
     D. the four refuges of item 20 (US-0399, US-0408, US-0563, US-0572): acres by kind (owned / easement / another agency's land).
     E. the parks that become pins in the 11 waiting states, busiest 25 first (`factcheck-run-44528656941/lost.json`).
     Planted answers only from what is proven (Flathead's record = YES, 2,414,171 ac; evidence batch 01's records; gold TUNE, never
     SEALED). Kit D (60 random parks, item 5 / item 20) is its own kit, after this one.
   - **OPUS'S ORDER NOW (fresh chat: "Read CLAUDE.md and key-quality.md section 19, do item 27's order"):** (a) hand-off 04, zip to
     Brandon; (b) read #284, mark ready, merge (no key run in flight); (c) R-FJ1's PR as item 26 says, ONE packet run MT, stamp,
     merge, then MT off `stop`; (d) wait for Brandon's yes per state, then item 26 (c). No release run before that.
28. **WHAT IS KNOWN ABOUT THE 11 WAITING STATES (Fable, 19 Nov noon; Brandon 11:52 AM: "The 11 states i dont have enough information to
   make them calls do you?"). Answer given: for 4 yes, for 6 not yet, Montana locked.** File: tools-out
   `fable-sitting-4/shrinks-47-what-is-known.csv`.
   - 48 outlines become pins (the safe direction: a pin claims nothing). **The risk is the 47 parks that keep an outline but lose a
     fifth or more** (both Montana faults hid there). Against the agencies' own tables on file (kit C, ONE pass): 6 match within
     about 1% (Glacier Bay N Preserve, Aniakchak NM + Preserve, Bitterroot NF's Montana part, Big Hole NB, Big Lake NWR); 4 are one
     state's piece of a unit that crosses state lines (Yellowstone, Bighorn Canyon, Hovenweep, Fort Union); **9 refuges come out at
     17-70% of the FWS total** (MT: Charles M. Russell, UL Bend, Red Rock Lakes, Lake Mason, Hailstone, Black Coulee; VA: Rappahannock
     River Valley, Mason Neck; FL: Crystal River): the FWS total counts easements and other agencies' land, so it is no clean test;
     1 is Custer Gallatin; **27 have NO official figure on file** (AR 9, FL 7, MT 3, DE 2, UT 2, VA 2, WY 1, AK 1).
   - Only 158 of the 2,430 outlines in these states carry a clean official acre figure. The fact check's "verified" = pin, name, kind
     and agency agree; it does NOT check size (Custer Gallatin stayed "verified"). Sitting 3's "12 pass" meant no unexplained lost
     outline and no new hard flag, nothing more. The 18 Nov bar (Q2) is not yet measured on these files.
   - R-PP1a in Alaska lands on the Park Service's own federal acres: Gates of the Arctic 7,279,313 (NPS 7,359,810), Katmai 3,624,170
     (3,611,564), Lake Clark 2,487,856 (2,481,441).
   - **Fable's call, for Brandon to say yes or no to: READY = RI and NC (outlines to pins only; NC also two trails to their line),
     GA (4 pins, 5 trims of 3-11%), AK. WAIT for official sizes = WY 1, DE 2, UT 2, AR 9, FL 7 + 1 refuge, VA 2 + 2 refuges. LOCKED = MT.**
   - **HAND-OFF 04 CHANGES: a new job goes FIRST, before item 27's A-E.** Job F: the official acres of the 27 "NO FIGURE" parks (the
     agency's own page or table, quoted), and for the 9 refuges the acres BY KIND (owned in fee / easement / another agency's land),
     which replaces job D's four. A shrink passes when the outline is between 0.8x and 1.25x of the figure both passes agree on;
     anything outside goes to Fable. That table is what the yes for the six waiting states rests on.
   - A yes for some states needs no extra run when the next key start rebuilds them anyway: Opus writes the list for the states he
     names (`approve`, his words as decided_by) and checks which start will build them; else ONE by-hand run.
29. **BRANDON HOLDS ALL 11 STATES (Fable, 19 Nov 12:01 PM CST; Brandon 12:00 PM: "I am waiting till we have more info better to be right
   then wrong back to opus now").** No state is named, no list is written, no release run, the four "ready" states included. The
   guard holds all 11 by park and Montana by STOP, so nothing can slip. His yes comes after hand-off 04's job F table is back from
   two agreeing passes. **OPUS'S ORDER (fresh chat: "Read CLAUDE.md and key-quality.md section 19, do item 27's order with item 28's
   job F first"):** (a) hand-off 04, job F first, zip to Brandon; (b) read and merge #284; (c) R-FJ1's PR, ONE packet run MT, stamp,
   merge, MT off `stop`. Then wait: nothing is released without his word per state.
30. **OPUS, ITEM 27's ORDER (19 Nov ~12:05-12:25 PM CST; "Read CLAUDE.md and key-quality.md section 19, do item 27's order", job F first per item 29).**
   - **(b) #284 Flathead NF MERGED** (6efe1d7b, squash). Read against today's main: only US-4502 differs; saved-answer tests pass.
   - **(c) R-FJ1 = draft KPC-Links #285** (prep/r-fj1-far-join; US ee2b6f1e9673 -> **c82bdade8675**). `KR.far_join_ok` (rules file) +
     the saved-join loop: an id in `join` AND `far`, decided_by + evidence (who, source, saw, date), fingerprint still fits = joins past
     the 0.6 degree box; never by name, never a re-found id, never `approx`, never past a NO; misfit = check row; no evidence = warning.
     Switch KPC_FAR_JOIN (default ON). US-4501's answer: join + far 2660, fp, evidence (b913a01's text), decided_by with the owner's
     11:49 words. Montana test build (re-match mode, main with #284): ONLY US-4501 changes (2652 name + 2660 reviewed; sgmtd1213 still on
     check); switch OFF = 0 parks. Test `test_r_fj1_far_join_nov19.py` ALL PASS (the six examples, the join path, NO wins, name never
     far, scope, changelog); R-PP1 test ALL PASS; preflight: the known master check only. **ONE packet run 44584564753** (KPC-Data,
     pr 285, states MT), started 18:08 UTC. **NEXT:** read `tools-out key-quality/review-packets/pr-285-*/summary.md` once: parks changed
     must be US-4501 only (record 2660 gained). If so: changelog "Reviewed: Fable, 2026-11-19 (stamp agreed ahead, item 26)", ready,
     squash merge, then delete `MT` from `stop` in `.github/key-drop-approved.json` (Montana then waits for his yes like the others).
   - **(a) HAND-OFF 04 DONE, zips sent to Brandon** (tools-out `key-quality/2026-11-19/handoff-04/`, README there). Two blind kits
     (pass 1, pass 2: same rows, different order, item numbers and plants; key in `kit-keys/`, never to an agent). Jobs, F first: F 36
     (27 no-figure shrinks + 9 refuges by kind; replaces item 27's D), A 34 (saved NOs on the park's own name, blind), C 5 (state-copy
     parks), E 25 (busiest new pins of the 11 waiting states), B 7 (second witness, Forest Service acres). Plants: Timucuan / Tallgrass,
     Flathead 2658 (YES) / Tillamook 241270 (NO-PART), MassGIS Great Brook Farm / Arkansas State Parks Mount Magazine, Cardigan / Hobbs.
     Scoring: plants first, a row counts where both passes agree, job F's 0.8x-1.25x rule (item 28), disagreements to Fable.
   - **UPDATE 12:20 PM (Opus): #285 R-FJ1 MERGED** (b1039f5b; main's US rules = **c82bdade8675**). Packet run 44584564753 (green, folder
     `review-packets/pr-285-33f2cdc/`): MT only, US-4501 1,115,748 -> 2,966,156 ac (+2660), nothing verified lost, gold the same: as
     agreed, stamped "Reviewed: Fable" (agreed ahead). **Montana is off STOP** (cb4044b6); with no list, the guard holds all 11 waiting
     states park by park. The next key start sees the new rules and rebuilds Montana; the guard holds it (red on purpose).
     Brandon asked about the packet bot's PART 2: its instructions (PART-2-ADDITIONS.md, Fable 11:40 AM) were sent to him to give
     the builder agent.
31. **PACKET BOT PART 2 (`run` mode) MERGED (Opus, 19 Nov 12:55 PM CST; KPC-Data #125 -> 968aec29).** Brandon deleted the first
   builder agent at 12:20; a new session got the catch-up kit (tools-out `handoff-03/KPC-hand-off-03A-part2-catch-up.zip`) and opened
   #125. Read before merge: permissions read-only except `save`; every `gh` step signed in, every KPC-Links script run with the tokens
   removed; no repeated keys; tests ALL PASS, `--selftest` ok, KPC-Data's hidden-failure tests 0 FAIL; shapely installed in the shared
   inputs step. Its offline test: the same 60 shrinks, 4 new-land parks and 126 lost outlines (same causes) as the known answers;
   24 shrinks differ from Fable's grid by more than 2%, none across the 20% line. **The gaps are the grid's:** against the records' own
   measured acres the bot is within about 1-2% (Custer Gallatin 2652 1,107,363 vs 1,115,748; Lake Dardanelle 202 vs 206; Yellowstone MT
   158,302 vs 158,798) and the grid 1-6% high (edge cells). Not run yet: the fact check and gold inside `run` (wired, they run live).
   The agency-acres check (addition 5) was not built: optional, later. **Use:** after the release run, ONE by-hand run, mode `run`,
   old = the published key commit before the release; read `review-packets/run-<date>/` once.
32. **HAND-OFF 04 IS BACK AND SCORED (Opus, 19 Nov ~1:35 PM CST; Brandon 1:18 PM sent both zips).** tools-out
   `key-quality/2026-11-19/handoff-04/SCORE-READ-FIRST.md` (+ answers-pass1/, answers-pass2/). **Planted 8 of 8 right.**
   - **Job F (the yes rests on it): 31 of 36 shrinks PASS** (outline 0.8-1.25x of the size both passes agree on; refuges on FWS Table 3
     primary-jurisdiction land, no easements, no secondary overlay). One witness (Beaverhead Rock, fits). No figure: DE McGinnis Pond,
     DE Laurel (Delaware refuses automated visitors). **Problems:** AR US-1092 Lake Fort Smith SP = an empty outline (one 0-acre record
     166847; official 256.69; job A: both passes say sgarb19 IS the park: lift that NO); UT US-6063 Red Cliffs RMA = outline 61,479 ac
     against an 873-ac recreation area / 44,859-ac NCA: **Fable**.
   - **Job A:** 16 old NOs are wrong by both passes (the record IS the park: evidence batch 03, after the release unless the park is in
     a waiting state and matters: Lake Fort Smith AR, DeGray Lake AR is a pin today), 10 PART keep their NO, 5 agreed CANNOT TELL,
     3 differ (Buck's Pocket, Deep River ST, Chatfield Hollow): Fable.
   - Jobs C, E: background for after the release. Job B: pass 2 blocked; pass 1 read the owner's file: same as kit C.
   - **Per state (Opus):** READY = AK GA NC RI (item 28) + **FL VA WY** (every shrink fits) + **MT** (all fit; Custer Gallatin and
     Flathead were fixed after the held files: read them in the release run's packet). **AR** after the Lake Fort Smith answer (saved
     answers only, no hash). **UT** after Fable on Red Cliffs (or say yes with Red Cliffs named). **DE**: two small parks no agent could
     check; Brandon's own browser can open Delaware's pages, or say yes knowingly.
33. **BRANDON'S OWN LOOK-UPS (Opus, 19 Nov ~1:30-1:55 PM CST).**
   - **PARK AND PRESERVE, R-PP1b (owner 1:32 PM: "no I looked the website up from pota and each one says national park+preserve or
     etc...no need to email them"; 1:36 PM: "The Alaska parks was easy clicked on link at pota and read the hero"; other parks: official
     site or PDF map).** No question to POTA. A park number keeps its own unit's preserve unless POTA numbers the preserve itself
     (Glacier Bay, Aniakchak, Great Sand Dunes stay apart). **Draft KPC-Links #286** (US c82bdade8675 -> c64b8ace0411, switch
     KPC_PRESERVE_WITH_PARK): offline AK CO ID builds: Denali, Gates of the Arctic, Katmai, Lake Clark get their preserve back; CO, ID 0.
     Packet run 44602628319 (AK CO ID) started. **For Fable:** review #286 (it moves the hash); the packet must show those four only.
     Alaska's would-be file then changes: 3 shrinks gone (Glacier Bay Preserve and the two Aniakchak rows still shrink, rightly).
   - **DELAWARE: McGinnis Pond is RIGHT.** DNREC's own map (Brandon's screenshot, documents.dnrec...): the Wildlife Area boundary runs
     along the pond's shore; the pond is not in it. POTA numbers both: US-5722 McGinnis Pond State Wildlife Area (the land, sgdec16
     108 ac) and US-10682 McGinnis Pond State Fishing Lake (the pond, sgdea751 49 ac). The new outline is the pond. **Laurel** keeps one
     of the three 'Industrial Forest Lands - Laurel Complex' tracts (359 of 1,093 ac; the other two held by G-1, far from the pin):
     missing pieces, the safe kind of mistake; Brandon wants more before calling it.
   - **Brandon asked (1:36 PM) "why do I have to decide them states? Are you all not sure?"** Answered: the guard holds any state that
     loses an outline until a PERSON names the parks (his rule, 18 Nov: KPC_DROP_OK is his word, not ours). Offered him a standing
     rule instead: release a state when every lost or shrinking park passes the two-pass size check; ask him only about the rest.
   - **Brandon asked (1:41-1:42 PM) for a bot that opens POTA's park web link and reads name, location, park type, maps, directions.**
     Have today: link harvester (finds an official page / map when POTA gives none), truth bot (opens the official page, reads the
     park's size), docs bot (map + rules links). Missing: the page's own heading (the designation: "National Park & Preserve"), and
     the location / address. Would be a reading step added to the truth bot (KPC-Data), built by the outside agent, robots.txt manners.
34. **STANDING RULE FOR RELEASING STATES (KPC owner, 19 Nov 1:56 PM: '"release a state when every lost or shrinking park passes the
   two-agent size check; ask me only about the problems....if fable thinks the error ratio is low and we done excellent job matching
   parks release them bring me the problems you can not figure out').** Replaces "Brandon's yes per state" (items 3e, 29).
   - A state is RELEASED (written into `.github/key-drop-approved.json` with decided_by = this rule + the date, then ONE release run)
     when: (1) every park that loses its outline or official grade, and every park that shrinks 20%+, passes the two-agent size check
     (both passes agree, the new outline 0.8-1.25x of that size) or is explained (a planned rule: Q1 / D3 / D4 / contest / a piece of a
     unit across state lines); (2) **Fable** has read the numbers and says the error ratio is low and the matching excellent (the 18 Nov
     bar, Q2: wrong land under 1% of outlines, none in the 25 busiest of each state, nothing over 2x official unexplained).
   - Brandon hears only the problems the chats and agents cannot settle, by park number. Open now: **US-6063 Red Cliffs BLM RMA (UT)**
     and **US-12938 Laurel Industrial Forest Land SWA (DE)** (given to him 1:57 PM). Red Cliffs goes to Fable first.
   - **NEXT (one Fable sitting):** #286 R-PP1b review (packet run 44602628319), Red Cliffs, the 3 job-A disagreements, and the yes under
     this rule for the waiting states (Opus's reading: AK GA NC RI FL VA WY MT pass; AR after Lake Fort Smith; UT after Red Cliffs;
     DE after Laurel). Then Opus: Lake Fort Smith saved answer, the list, ONE release run, the `run` packet, empty the list.
   - **UPDATE 2:05 PM (Opus):** Lake Fort Smith = **draft KPC-Links #287** (evidence batch 03a, saved answers only): the 2 Nov NO was right
     for the 1,613-ac shape sgarb19 held then; today sgarb19 is the 257-ac park (Arkansas State Parks layer 256.69; both passes YES).
     Arkansas test build: exactly ONE park changes. For the Fable sitting with #286; R-PP1b packet run 44602628319 still running.
     **Fable starter:** "Read CLAUDE.md and key-quality.md section 19, items 33 and 34: review #286 and #287, Red Cliffs, the job-A
     disagreements, and make the release call under the owner's standing rule."
35. **RED CLIFFS + LAUREL SETTLED FROM POTA'S OWN LINKS; R-PP1b PACKET; TWO OWNER POINTS (Opus, 19 Nov ~2:00-2:15 PM CST).**
   - **Draft KPC-Links #288 (evidence batch 03b, saved answers only):** the owner read POTA's links himself (2:01 PM). US-6063 Red Cliffs
     BLM RMA = BLM's Red Cliffs Recreation Area (campground site; POTA's pin; 872.88 GIS ac): join rma9123 + rst9123, NO the 61,251-ac
     'Red Cliffs SRMA' (NCA-sized; POTA numbers the NCA, US-6077). US-12938 Laurel = DNREC's 'Laurel Complex' tracts: join all three
     records (359 + 462 + 272). Test builds: DE only US-12938 changes (approximate -> official), UT only US-6063. So Utah and Delaware
     have no open problem left once #288 is merged.
   - **#286 R-PP1b packet run 44602628319 (green, `review-packets/pr-286-de445ba/`):** AK exactly US-0022, US-0026, US-0044, US-0048 gain
     their preserve record; CO, ID 0; nothing verified lost or worse. **The gold score moves: US-0022 Denali = WRONG LAND** because the
     gold answer was graded under the old reading ("Denali National Preserve is other land"). The owner's 1:32 PM ruling names Denali
     among the park numbers whose POTA link is the combined unit. **FOR FABLE:** update the gold answer for US-0022 to the ruling (a
     ruling changes the answer key, not the other way round), then stamp #286.
   - **Owner 2:02 PM: "I think our bots and them gathering information for the ones our program dont solve from the beginning we have
     way less issues".** Agreed: everything settled today (preserves, Red Cliffs, Laurel, Flathead, Custer Gallatin) came from reading the
     park's OWN page (POTA's link) and the agency's own acres. Plan: the POTA-link reading step (item 33) runs FIRST for every park the
     rules leave unsure, before any outline goes to a person; the agents only get what that step cannot read.
   - **Owner 2:04 PM: "We should also only build keys if we have most of our layers so we dont rebuild over and over...I know we always
     be missing some".** For Fable's fix plan (item 26): a layer-completeness gate before any key build: build a state only when its
     layers are present and not short (the master check's short-copy test, the keeper's asks); otherwise wait and say which are missing.
     The release run itself goes ahead on today's saved shapes (the fact check measured those).
36. **FABLE'S SITTING 5: HAND-OFF 05 (HELPER BOT), #286 / #287 / #288 MERGED, GOLD, JOB A, THE 11 STATES RELEASED (19 Nov ~2:10-3:10 PM CST;
   Brandon 2:08 PM: "make me a handful for my other agent to build the helper bot ... make it the work horse it could be" then the
   sitting; 2:15 PM: "accurate and reliable and very efficient in our time...bots, schedules, out side resources, other agents, my pc,
   build tools I can run on my pc or you all start and come back later and fetch it"; 2:26 PM: "would it be smart if the tool i use on
   the pc that prematches parks and pulls data made a list for the bot ... or the keeper made the list? ... should the bot screen shot
   what it thinks are maps etc on the weblinks if it cant download it?").**
   - **HAND-OFF 05, the PARK PAGE READER** (tools-out `key-quality/2026-11-19/handoff-05/`, zip sent to Brandon): KPC-Data
     `kpc_park_pages.py` in four parts (reader + facts file; worklist + by-hand workflow + summary; PC runner + person page + intake;
     blind two-pass kits). Four laws: reports never decides; silent beats wrong (every fact has its address and quote); fetches only
     through `kpc_manners`; nobody feeds it. Rule sheet R-PR1 to R-PR13 (own page, name, kind words + combined unit +
     `pota_numbers_part`, inside-of, labelled sizes, coordinates, address roles, maps + tracts, facts in an address, refusals, unsure,
     what people see, map pictures). 30 known answers from today (six "& Preserve" heroes, Red Cliffs fixture, Laurel, McGinnis,
     agency-home and unofficial links). **Both owner points are in it:** (a) LIST DROPS: the keeper, the key run and his PC pre-match
     tool drop a small list on `intake-files:park-pages/lists/`, the reader picks lists up itself and writes answers back
     (`lists-done/`); the club wires its tools to write that shape (chat 10 / Opus, after part 2); (b) MAP PICTURES (R-PR13): yes in a
     browser run, only where the site let the page be read, only for a park still in question, one small JPEG in the run's output,
     deleted when answered, never traced. **Fable's defaults, his to overrule:** G-PR1 a refusal holds on every machine (the PC run
     never asks a host that said no); G-PR2 no key rule reads these facts until a block shows 95 in 100 right and a reviewed rule
     change says so; G-PR3 schedule off until his GO; G-PR4 pictures stay in the run's output, never a branch or the site.
   - **#286 R-PP1b: REVIEWED, MERGED (0e133c9f). Main's US rules hash = c64b8ace0411.** Two code lines read; packet pr-286-de445ba and
     a combined Alaska test build both show exactly US-0022, US-0026, US-0044, US-0048 gaining their preserve record. The published
     key has NO other park kept apart by R-PP1 except Great Sand Dunes (US-0033 / US-8295; stays apart), so the 13 declared states
     change in Alaska only. **Gold: US-0022 record 3300 NO -> YES, graded 'adjudicated'** (tools-out d64e81a1 + ed00b051); no other
     gold answer conflicts with today's rulings (US-6077 keeps the SRMA as YES and the 873-ac site as NO).
   - **#287 Lake Fort Smith: REVIEWED, MERGED (d330a7b9).** sgarb19 = the state parks layer's own record, 256.69 ac, pin inside.
   - **#288: Red Cliffs RIGHT; LAUREL WAS ONE RECORD SHORT.** DNREC's map (north to the left, the state line down the right edge)
     shows FOUR parcels in three named tracts and the layer has four 'Industrial Forest Lands - Laurel Complex' records: sgdec38 +
     sgdec21 = Whitesville Tract (two parcels), sgdec69 = Edwin Bell Tract (the pin), **sgdec25 (285 ac) = Ralph's Corner, added**:
     Laurel = 1,378 ac. **Batch 03c added in the same change:** US-12918 Seven Sisters State Fish and Wildlife Area = FWP's 7.8-acre
     fishing access site (POTA's own link), NO to the 1,554-ac WMA records it held (the one gold park still on wrong land, known
     since 18 Nov); US-12646 (the WMA) NO to the site's records. Rebuilt on main after #287 (the two changes clashed on the parts
     fingerprint lines), test builds DE / UT / MT: only US-12938, US-6063, US-12918, US-12646 change. **MERGED (bc5cac43).**
   - **JOB A, the three rows settled:** Buck's Pocket AL US-1035, record 256239 (669 ac) = **PART** (the park is 2,000 acres:
     Encyclopedia of Alabama); the NO stays. Deep River State Trail NC US-12717, 214825 (1,669 ac) = **PART**: an older copy; the
     park already holds the state's own record (sgnca3303, 2,433 ac; NC Parks listed 1,274 ac in 2011, 1,277 in 2019 and has added
     land every year since); the NO stays, nothing changes. Chatfield Hollow CT US-1656, sgcta4113 (399 ac) = **YES** (the park is
     412 acres): the NO is lifted in batch 03 (17 YES now).
   - **THE RELEASE CALL (owner's standing rule, item 34): ALL 11 RELEASED: AK AR DE FL GA MT NC RI UT VA WY.** What was read:
     (1) the guard's own list of run 44600381160 (20:25 UTC): **50 parks** lose their outline or official grade, every one by a
     planned rule (Q1 20, contest 14 incl. 2 exact-name, D4 9, D7 4 [outline stays, labelled approximate], D3 3); 0 unexplained.
     (2) the 20:25 would-be files equal the 17:16 files hand-off 04 measured, but for US-4501 / US-4502 (fixed) and the Alaska
     preserves (R-PP1b). (3) the 47 real shrinks: job F's 36 (19 pass by machine; the 9 refuges re-added by hand from both passes'
     FWS Table 3 rows: land under FWS's own jurisdiction 0.87-1.07 of the outline; 2 Florida forests on the FFS layer; Deep Creek
     North; Beaverhead Rock one witness; McGinnis by the owner's map; Lake Fort Smith and Red Cliffs FIXED), 6 on agency tables, 4
     pieces of units across state lines, Custer Gallatin fixed. (4) the 29 gold parks of these states: wrong land or too big 9 on
     today's map -> 0 after this release (Seven Sisters was the last); right 18 -> 17; pins 2 -> 12. **Five of those pins have a
     known right record: 2 heritage areas (D3, the owner's rule) and US-7348 Longview Saline WMA (AR), US-6744 Terra Ceia Frog Creek
     (FL), US-6045 Swasey Mountain HMA (UT): batch 03.** NOT proven and said so to Brandon: the 18 Nov bar "under 1% wrong land" on a
     RANDOM sample (kit D, after the release) and "none wrong in the 25 busiest per state" as its own measure. Every CHANGE was
     checked; unchanged outlines are the ones on today's map.
   - **DONE BY FABLE:** list `.github/key-drop-approved.json` = the 50 parks by name (98ea4752, decided_by = the standing rule);
     **ONE release run 44613348117 started 20:54 UTC**, states the 11. It will build about 22 states: #286's scope declares 13
     (AK AL CA CO FL ID KS LA NM NV OR TX WV) and a rules change builds declared + not-yet-green states whatever the states input
     says. A state outside the 11 that loses anything is held by the guard (red, nothing bad saved).
   - **LESSON (test builds):** a local build differs from the bot's held file by the workflow's AFTER-build holds (Noatak 16 km
     hold, White Mountains "not signed", 4 Utah, 2 Arkansas rows). Compare local base to local head, never local to the bot's file.
   - **THE CRON REDS:** the two daily starts rebuild every not-yet-green state, so the 11 held states made a red run (an email) at
     18:22 and 19:38 UTC today. The release ends that. Next time a state is held on purpose, park it in the scope or pause the
     starts (Opus, with the layer gate below).
   - **NEXT, Opus (one short session, when Brandon says "check the release run"):** (a) read run 44613348117: `gh api
     repos/KentuckyPortableClub/KPC-Links/actions/jobs/<join job>/logs` and grep "Drop guard": the 11 must be "let through by
     the named-parks list"; a held state = STOP, tell Fable; (b) ONE packet-bot `run` mode run (old = c556310c, the published key
     before the release) and read it: Laurel 1,378 ac, Red Cliffs 873, Lake Fort Smith 257, Seven Sisters 8, the four Alaska
     parks whole; (c) EMPTY `states` in key-drop-approved.json (the guard test's last check fails until then, by design); (d)
     evidence batch 03 (17 wrong NOs + the three gold-YES pins above + check AL sgala2's shape against 2,000 ac), draft for Fable;
     (e) kit D (random sample of the released files): the first real measure of the 1% bar; (f) the layer-completeness gate
     (item 35) and R-NET1's code; (g) wire the keeper + key run to write list drops once hand-off 05 part 2 is merged.
   - Brandon's page ("Key Run Check, 19 Nov", slug 14b24a57-71d5-4f8c-87d2-a0c53b95a518) carries the release block at the top: version 1795121760-4655.
   - **CORRECTION (Fable, 3:00 PM, from the run's own plan): run 44613348117 builds ALL 50 states, not 22** ("0 reused, code hash c64b8ace0411": any rules change moves the code hash, so no state reuses its build; 3 jobs of about 69 minutes). The other 39 states were built green earlier today, so they should come out as they are on main; a state that loses anything is held by the guard (red, nothing bad saved). Read the run about 80 minutes after 20:54 UTC.
37. **THE NOT-SURE LIST + BOTS WIRED THROUGH IT (Fable, 19 Nov 3:10-3:20 PM CST; Brandon 3:07 PM: "The system should do the work before and
   leaves us less head scratching...my 2fer, us and world tools probably should be updated some point...and the shelfed 2fer rules pr at
   somepoint we should get the agent to make us a draft and you review and have them edit it how you want ...also all these bots should
   be wired together to share the load and help to solve mysteries in how ever you think....we should also keep a list of parks we mot
   100% sold on and why").**
   - **STARTED: the list.** tools-out `not-sure/not-sure-parks.json` + `.csv` + README, **104 rows**, one park + one doubt + the reason in
     plain words: wrong likely 21 (17 wrong NOs of job A incl. Chatfield Hollow, 3 pins whose right record is known, Noatak held 16 km
     from its pin), unsure 60 (the release's 50 named parks by rule, 5 cannot-tell, White Mountains, 4 classes), incomplete 16 (12 part
     records, 4 cross-state forest halves), fairly sure 5 (Laurel placed from the map picture, Red Cliffs name against link, Seven
     Sisters, Beaverhead Rock, Moro Big Pine), unchecked 2 (the unchanged outlines: kit D; Idaho + Oregon as saved).
   - **THE WIRING = THAT LIST.** Hand-off 05 ADDENDUM 1 (in the zip, tools-out handoff-05/): `kpc_not_sure.py`, one shared list every bot
     writes (park, doubt code, why, what would settle it) and every bot reads (the rows it can help with), `tried` notes with quotes, a
     row closes only with who + how, nothing deleted; what no bot settles is what a person or agent gets. The page reader works open
     rows first and may never settle one. The club wires the key run, fact check, size checker, drop guard, keeper to write rows after
     the module is merged (chat 10 / Opus).
   - **ORDER (so nothing is built twice):** (1) Opus reads the release run (item 36 NEXT); (2) the agent builds hand-off 05 parts 1-2 +
     addendum; (3) the club's bots write rows; (4) **Brandon's PC tools (2-fer, US, world) are updated ONCE, then**, to write list
     drops / rows and read the answers (he connects their folder to the chat that does it); (5) **the shelved 2-fer fixes**
     (`fers-fix-later.md`): Fable writes hand-off 06 for the agent (draft PR, Fable reviews, the agent edits); the 7 owner questions
     come first. Fresh Fable chat starter: "Read CLAUDE.md, key-quality.md section 19 items 36-37 and fers-fix-later.md: bring me the 7
     questions, then write hand-off 06 (the shelved 2-fer fixes) for the outside agent."
38. **THE SEVEN 2-FER QUESTIONS ANSWERED + HAND-OFF 06 (Fable, 19 Nov 3:15-4:00 PM CST; Brandon 3:13 PM: the starter of item 37).**
   - **FINDING: `fers-fix-later.md` WAS OUT OF DATE.** It was written 17 Nov 12:43 PM ("nothing below is built"); the agent's fix list
     (Handoff 9, KPC-Links #269) was merged at 3:50 PM that day. Run today on main: `tests/test_fers_handoff9_nov17.py` ALL PASS;
     fers rules hash 0637d083bd98 = the changelog's. Of the 10 shelved bugs 6 are fixed, 2 are built behind settings, 2 are left;
     all seven questions were already built as settings, ALL OFF. The note now says so at its top.
   - **HIS ANSWERS (rule sheet R-2F0 to R-2F7: tools-out `key-quality/2026-11-19/handoff-06/RULE-SHEET.md`; also in mapping.md):**
     Q1 summary-map outlines = APPROXIMATE ("Yes, approximate"). Q2 park beside a forest = NOT held back (17 Nov 4:04 PM). Q3 near a
     size line = NOT SURE, the band is ONE GRID CELL (5 m at pass 3), never a typed number (N3; HQ's 8 m goes). Q4 "Need yo be from
     the new better system we are building now...old efee data is not trustworthy pre rebuild....after rebuild i trust this system
     more sp yeah maybe?" then "Yes, that's it" to: (1) a row made before this rebuild is never copied forward; (2) a new-system row
     is copied only while the key entry of both its parks is unchanged. Q5 a separate overlap piece that passes the 25-yard test is
     its own spot, NO 100 m (17 Nov 4:04 PM). Q6 "Say we are missing this boundary possible 2fer check for offical missing boundary
     or something like thay": the drawing comes off, the row says "Possible 2-fer. We are missing an official boundary here: check
     both official boundary maps before you count it."; the old rows of such parks: "Drop until re-checked". Q7 "D10 yes ...shelf i
     trust the new shelf more theb the old system": D10's scope entry = approved; the THIN-SHELF fallback (an area under 90% stays
     on the old path) is NOT approved and goes: every shelf area is read, what the shelf lacks is not tested and is counted.
   - **R-2F0, his own summary of POTA's rules, 3:42 PM** (quoted whole in the rule sheet): overlapping parks, public land, you and
     all your equipment in it, 100 ft each side of a trail / of the water's edge, no size requirement; "we need to be a touch
     stricter to account for map errors being off a little". So no new number in the 2-fer code, ever, but POTA's, his, or the
     measuring tool's own error. The 25-yard floor and the tight lists stay (N4).
   - **MEASURED TODAY with the real 5 m grid** (made-up squares, 43 widths x 16 placements; `handoff-06/known-answers/`): a true
     16-22 m overlap that gets past the 25-yard floor reads 23-27 m; a true 42-45 m reads up to 49; a true 46-49 m reads down to 45.
     One cell (5 m) catches every one. On the 17 Nov 472-row file: 380 rows fall in the 5 m band (8 m: 385).
   - **A DEFECT IN THE BUILT Q4 SETTING:** `kpc_fers_age.py` compares a row with the whole key's `build` in `data/us-key/index.json`,
     which is the id of the last key RUN (today: US-44600381160, 39 areas reused, 0 rebuilt). Switched on as built it would throw
     every copied row away after any key run, twice a day. Hand-off 06 replaces it with a per-park stamp (`made_on`).
   - **HAND-OFF 06 = the 2-FER RULES PR** (tools-out 8375ceb, `key-quality/2026-11-19/handoff-06/`, zip sent to Brandon; ONE agent
     session, a build). Part 1: one switch file `.github/fers-switches.json` under the fers hash (the key-switches pattern; a missing
     file stops the bot; the receipt records every setting) + R-2F1 to R-2F7. Part 2: what the shelf still holds (a math guard test
     instead of the dead `FERS_ALGO`; byte tests on Python 3.12 and 3.13; the test that writes into the repo: stray tracked file
     `data/status/test_fers_final_redact_nov17.json`, commit 43720d6). Part 3: the 2-fer bot writes its own doubts in the NOT-SURE
     list's shape. Part 4: a PROPOSAL only, measuring a near-line spot finer. 30 known answers, 27 must. NOT in it: the Kentucky
     path, the rules-in-one-table job, any run.
   - **EACH PART MOVES THE FERS HASH: draft PR to KPC-Links, then a Fable chat** ("review PR n"); nobody merges before that.
   - **SAID TO BRANDON, HIS TO OVERRULE:** (a) the 25-yard floor was NOT lowered on "a touch stricter"; (b) every 2-fer row on file
     today is old-system data: it is replaced area by area at the first fresh run, nothing is hidden meanwhile; (c) at the
     switch-over a thin area (US-HI 9.5% on 17 Nov) will show only the pairs between parks on the shelf.
39. **HAND-OFF 05 CAME BACK: FOUR DRAFT PRs, FABLE'S REVIEW = NOT YET, THREE SMALL CHANGES (Fable, 19 Nov 3:50-4:15 PM CST; Brandon
   3:50 PM: "look at this, your fable so only do what fable needs to do wr have outside agents and opus and sonnet) your the brains,
   reviewer and manager your responsibility is to make sure we are producing the best maps possible and efficiently and we have
   very little errors and we catch and fix it").**
   - **KPC-Data #126 (part 1, reader) <- #127 (part 2, worklist + workflow + `kpc_not_sure.py`) <- #129 (part 3, PC runner, person
     page, intake) <- #130 (part 4, blind kits)**, stacked, all draft. Nothing merged, nothing started.
   - **WHAT FABLE READ:** every part's notes, the +80 lines in `kpc_manners.py`, the guard test, the picture path, the workflow
     (dispatch only, schedule commented out, `contents: read`, read job without credentials, one save job, no key twice: all good),
     `kpc_not_sure.settle()`. NOT read line by line: `kpc_park_pages_rules.py` (1,285 lines), parts 3 and 4.
   - **THE THREE CHANGES** (one comment on #126: issuecomment-7023249764; asked for as ONE more draft PR on top of part 4,
     `prep/park-pages-part5-review`, no rebase): (1) the manners guard was loosened to "no new def but the picture one": any added
     line inside `robots_ok` would pass, and it is skipped without origin/main: pin both files by sha256 instead; (2) pictures are
     outside the request and time budget, are taken for information-only questions, and fall back to a shot of the whole window:
     budget them, R-PR13's parks only, no map part = no picture, note the picture on the facts; (3) `settle()` closes a row for any
     caller with an empty who / how: refuse those, refuse the reader, a bot only from a list in the module (empty today).
   - **THE ACCURACY CLAIM is honest and small:** 0 wrong on 26 expected facts (inside_of: ONE fixture). Enough to merge a tool that
     only reports. **G-PR2 stands: no key rule reads a block until a real run shows 95 in 100 right, measured blind with part 4's kits.**
   - **ORDER FOR OPUS** (starter: "Read CLAUDE.md and key-quality.md section 19 items 36 and 39: check the release run, then item
     39's order"): (a) item 36 NEXT (a)-(c) first (main got "US answer key" 6e110a6 at about 4 PM); (b) when part 5 is in: the
     hand-off gate on a FULL machine at the top of the stack (the agent's 33 "new" failures are missing modules and no KPC-Links
     checkout: GATE PASS here is the merge condition), a line read of `kpc_park_pages_rules.py` against R-PR1 to R-PR13 and of
     part 2's 132 deleted lines, then merge #126 -> #127 -> #129 -> #130 -> part 5 in one sitting, no run between; (c) the seed
     (104 rows) onto tools-out `not-sure/` by area, then ONE by-hand reader run, no browser, the not-sure parks first; read
     `summary.md` the next session, never wait on it; (d) `kits --n 40`: two zips to Brandon for two fresh agent sessions,
     `kits score`, the per-block table to Fable; (e) wire the club's bots to write not-sure rows (item 37 step 3); (f) a club
     change of its own: anchor the documents bot's `gov_of` ([a-z]{2}.gov matches "idaho.gov" by its last letters).
   - **THE AGENT'S QUEUE, in this order:** part 5 of hand-off 05 (small), then hand-off 06.
   - **FABLE'S NEXT SITTINGS (only these):** "review PR n" for each hand-off 06 part; the reader's per-block accuracy table when the
     two kit passes are back (which blocks a rule may read); the answer to hand-off 06's part 4 proposal.
40. **HAND-OFF 07: THE WHOLE MAP PIPELINE FOR AN OUTSIDE REVIEWER (Fable, 19 Nov 4:05-4:20 PM CST; Brandon 4:05 PM: "Give me a quick
   handoff to review our process from store room, keys, 2fer, matching the helping bots etc all map related ....give plenty of
   details, known issues, usage, what works good what doesn't..your thoughts for improvements etc").**
   - ONE file, read-only review, sent to Brandon and on tools-out e4ef95e
     `key-quality/2026-11-19/handoff-07/KPC-hand-off-07-map-pipeline-review.md`: the chain stage by stage (layers, the store room,
     keys and matching, 2-fers, the helper bots, who does what), each with its numbers and known issues, every number tagged with
     the day it was measured; what works; what does not, ranked; usage; Fable's ten thoughts; twelve questions; what to send back.
   - It comes back as ONE report (findings ranked, file / line or park number, the smallest fix, how to test it). It goes to a
     Fable chat: "Read CLAUDE.md and key-quality.md section 19 item 40: read the reviewer's report and turn it into an order of work."
   - Tagged in it as NOT re-checked today (from the 17-18 Nov notes): the PC push check, the waiting room's 497 files, the repo
     sizes, the name traps of the 18 Nov grade. The reviewer is asked to test them, and to list every place notes and code disagree.
41. **THE PUBLIC MAP IS STILL THE 11 NOV RELEASE: "RELEASED" MEANT THE KEY, NOT THE MAP (Fable, 19 Nov 4:15-4:40 PM CST; Brandon 4:13 PM
   sent Opus's report of items 36 + 39).**
   - **OPUS'S REPORT, taken as read:** release run 44613348117: no state held, 11 let through by the named list, the 50 named parks
     exactly; key saved 6e110a6c; red only on the outline master check (408 problems, 412 before). Packet run 44625389642 started
     (old = c556310c). `states` emptied (5a702d3). Part 5 of hand-off 05 = KPC-Data #131, covers the three changes. Stopped at the
     gate: no shapely / pyproj / fitz in the chat, installs blocked. His flag: "the US map's outline files weren't re-saved".
   - **WHAT FABLE FOUND BEHIND THAT FLAG (checked in the repo):** the public pages read `data/released/` ONLY
     (`data/released/RELEASED.json`, written only by `kpc_release.py`; `kpc-bounds.js` draws a US park from the released copy of
     `data/outlines/US-XX.geojson.gz`). **The by-hand Release (`kpc-release.yml`) last ran for the US on 11 Nov 22:10 UTC (from
     addf5c4e), CA and KY on 12 Nov. Nothing since.** The working outline files `data/outlines/US-XX` were also last written 11 Nov
     (store mode, 15 Nov, skips the key run's outline step). So every key change of 12-19 Nov is in the working key only.
   - **Examples (released copy against today's working key):** US-12918 Seven Sisters: on the map with the 1,554-ac WMA records; key
     today = the 8-ac fishing access site. US-4502 Flathead and US-4501 Custer Gallatin: on the map with the state copy. US-12938
     Laurel: map approximate 1,093 ac, key official 1,378. Montana 50 of 254 parks differ, Delaware 29 of 89.
   - **CORRECTION TO ITEM 36 (Fable's own):** "ALL 11 RELEASED" = their keys were saved to main. "Wrong land ... 9 on today's map ->
     0 after this release" was WRONG as written: the map did not change. Fable did not check what the map reads. Told to Brandon.
   - **THE RELEASE'S OWN CONDITIONS:** only Brandon's login may start it; a commit on main; per area; green, no worse than live, and
     RELEASE-READY: YES in a Quality verdicts file (`data/status/quality/verdicts.json` is NOT on main; Quality is retired).
   - **ORDER FOR OPUS** (starter: "Read CLAUDE.md and key-quality.md section 19 items 39 and 41: do item 41's order"):
     (a) read packet run 44625389642 once (item 36 b); (b) FIND AND SAY, five lines, no fix yet: which job writes
     `data/outlines/US-XX` in store mode (kpc-us-key.yml's master steps, or the keeper's display copy), why the key run skips it,
     and the master check's 408 problems by kind (are they key-against-outline disagreements?); what `kpc_release.py` wants in a
     verdicts file; (c) ONE run that brings the working outline files in line with the saved key, all states, working files only
     (a change that moves a rules hash = draft PR to Fable first); (d) ONE packet-bot run, mode `run`, OLD = the RELEASED files
     (commit addf5c4e, what the public sees), NEW = today's key + the rebuilt outlines: per state outlines lost / gained / shrunk
     20%+, flagged and verified before and after, to tools-out `key-quality/2026-11-19/public-vs-working/`; (e) then stop: Fable
     reads (d) in one sitting and writes the verdicts (YES / HOLD per state, with the reason); (f) Brandon's GO, and HE starts
     "Release map files (by hand)": Opus gives him the three values (area, areas, source_sha). Nothing public changes before (f).
   - **HAND-OFF 05, after Opus's stop:** do the line reads now (`kpc_park_pages_rules.py` against R-PR1 to R-PR13, part 2's 132
     deleted lines): they need no gate. THE GATE RUNS ON GITHUB, never in a chat: look at KPC-Data `kpc-tool-tests.yml`; if it
     cannot run `kpc_full_suite.py` on a branch with both checkouts, a by-hand, never-red gate workflow is a small club build
     (every later hand-off needs it too). Brandon changes no setting. The `settle()` kind gap (a bot could say "person") is NOT a
     merge blocker: when the club wires its bots, add a repo test that no bot script passes kind person / reviewer.
   - **STANDING FIX (for the readiness board, hand-off 07 idea 4):** every day one line per state: key saved <date>, outlines
     written <date>, public Release <date>. A gap between the three is shown, never found by accident.
   - Hand-off 07 has this as stage C2 and as its first known issue (tools-out 852f13d).
42. **HAND-OFF 06 IS BACK + WHO GATES THE PUBLIC RELEASE (Fable, 19 Nov 4:30 PM CST; Brandon 4:26 PM relayed the agent, then: "Just
   got this send new one to agent? We release once you think keys are excellent").**
   - **IN, all draft, nothing merged:** KPC-Data #131 (hand-off 05 part 5, the three review changes). KPC-Links #289 (06 part 1,
     20 files, +1,141 / -247) <- #290 (part 2) <- #292 (part 3); the part 4 proposal is in part 1's notes. fers 0637d083bd98 ->
     9cee86692de2 across the three; US / CA / world hashes unchanged. The agent's own numbers: 14 targeted tests pass; R-2F1 recount
     127 summary-map parks (74 on 17 Nov: ask why it rose); the full gate not finished (Python 3.12 only on its machine).
   - **THE OWNER'S RULING: the public Release waits on Fable's judgement of the keys** ("We release once you think keys are
     excellent"). He still starts it (only his login can). This replaces "Brandon's GO" as a separate step in item 41 (f).
   - **HOW FABLE APPLIES IT (told to Brandon, his to overrule):** two different yeses. (1) A STATE GOES TO THE PUBLIC MAP when the
     public-against-working table of item 41 (d) is clean for it: every outline lost or shrunk 20%+ against what is on the map NOW
     is explained or passes the size check, and nothing the fact check calls verified gets worse. The map up today is the 11 Nov
     key with known wrong outlines, so a better key is not held back for a number. (2) THE KEY IS CALLED "EXCELLENT" only on a
     measured number, the 18 Nov bar: a blind random sample of 300 outlined parks, two outside-agent passes that must agree, wrong
     land under 1% (0 wrong in 300 is what proves that; 1 or 2 wrong = "up to about 2%", said as that), and none wrong among the
     25 busiest parks of each state (blind line-ups only for the ones the fact check does not already verify). Reported with its
     range, never one number.
   - **THE SAMPLE = KIT D, Opus builds it with `kpc_key_grade.py`** (sample seeded, packet blind with plants, keys apart) from the
     key that goes public, two zips to Brandon for two fresh agent sessions, score, table to Fable. After item 41 (a)-(d).
   - **THE THREE 2-FER PRs NEED FABLE BEFORE ANY MERGE (each moves the fers hash). A FRESH Fable chat** (this one is very long):
     "Read CLAUDE.md, key-quality.md section 19 items 38 and 42, and the rule sheet on tools-out
     key-quality/2026-11-19/handoff-06/RULE-SHEET.md: review KPC-Links #289, #290 and #292 and answer the part 4 proposal."
     The agent cannot see comments on KPC-Links PRs: Brandon passes the review on. 2-fer runs stay parked; this review does not
     hold up the map Release.
   - **HAND-OFF 07 GOES TO A FRESH AGENT SESSION** (not the one that built 05 and 06: it would be reviewing its own work).
   - **THE GATE WORKFLOW (item 41) runs Python 3.12 AND 3.13** (hand-off 06 part 2 asks for both; the agent had 3.12 only).

43. **ITEM 41's ORDER DONE TO (e) + THE GATE ON GITHUB + THE LINE READS (Opus, 19 Nov 4:30-5:30 PM CST; Brandon 4:30 PM: the item 41 starter).**
   - **(a) PACKET run-2026-11-19 (44625389642) IS WRONG, DO NOT READ IT:** it laid the 20:25 UTC `key-held` files (run 44600381160, before
     #286/#287/#288) over the 21:52 key, because the release run held nothing and so never replaced `key-held`. That is why it showed
     Laurel 1,093 -> 359, Seven Sisters 5,676 -> 1,554, Lake Fort Smith 0, the four Alaska parks losing their preserves. Its table is
     right on one thing: only the 11 states change (46 outlines lost + the 4 D7 grade drops = the 50 named). **FIXED** (KPC-Data 4137506):
     the packet bot lays `key-held` over only when it was written at most 20 minutes before the new side's index `built` (same run); the
     summary says when it was not. New input `folder` (key runs). Tested on today's times: stale = refused, the 20:25 key's own = laid.
   - **(b) FOUND:** (1) NOTHING writes `data/outlines/US-XX` in store mode: kpc-us-key.yml's "Outlines from the key" step (the only US
     writer, `kpc_outlines_from_key.py`, which DOES rebuild an outline whose records are not the key's and drops pin outlines; the
     workflow comment "never replaced" is stale) has `if: KPC_KEY_SOURCE != 'store'`; the keeper writes no display copy. (2) The 408 are
     ALL key-against-outline disagreements, 44 states: 123 "the key grades the park PIN; it must not have an outline", 285 "holds
     record(s) not in the key's m"; the rest of the check was clean. (3) `kpc_release.py` per area wants: a `verdicts.json` with `sha`
     (= source_sha), optional `build` (= the area's build in data/us-key/index.json), and `areas: {"US-MT": {"RELEASE-READY": "YES"}}`
     (or a top-level `RELEASE-READY: YES`); PLUS a key-check `data/status/key-check/us-<build>.json` with `gate: PASS` at source_sha
     (none for US-44613348117: the key run's postcheck was skipped because the run ended red; last is US-43293787778, 13 Nov); PLUS
     green in the index; PLUS `no_worse_than_live`: **fewer outlined parks than the released file = refused. All 11 states lose
     outlines on purpose, so the Release as written refuses every one of them** (needs a named-parks rule like the drop guard's: Fable /
     owner); PLUS no outline holding a record not in the key (fixed by (c)).
   - **(c) DONE:** new by-hand workflow `kpc-us-outlines-sync.yml` (KPC-Links 224f053; never red, the US key run's lock, per state:
     `kpc_outlines_from_key.py` from the saved copy + the master check for that state; a state that fails keeps main's files; no rules
     file touched). Run 44630258977: **50 clean, 0 held**, saved edf15be8. Master check on main after it, run here: **all clear** (3 suspect
     baselines as before). Working files only; the public map is unchanged (data/released/).
   - **(d) STARTED, NOT READ:** KPC-Data packet run 44630734620, mode run, OLD = addf5c4e (what the public sees), NEW = today's key
     (6e110a6c; the bot draws outlines from the key's records + the saved copies, the same thing (c) wrote), `key-held` refused by the
     new rule, to tools-out `key-quality/2026-11-19/public-vs-working/`. Read it once next session. Caveat for (e): the old side is the
     KEY at addf5c4e, not `data/released/` itself (the release copied the outline files made from that key, pins dropped).
   - **(e) = FABLE.** For (f), the three values once the verdicts exist: area `US`, areas = the YES states (`US-MT US-DE ...`),
     source_sha = the main commit that holds the key, the outlines (edf15be8 or later) AND the verdicts + key-check files.
   - **THE GATE IS ON GITHUB NOW:** KPC-Data `kpc-handoff-gate.yml` (bbb7c35; by hand, never red, read only): checks out the branch,
     main and KPC-Links main (LINKS), installs every library the tests import, runs `kpc_full_suite.py` on MAIN first and uses main's
     failures of today as the baseline (known-fail-main.txt is from 7 Nov), Python 3.12 + 3.13. Verdict = the notice line "GATE PASS /
     GATE FAIL" per Python. **First run 44631073762 on `prep/park-pages-part5-review` (#131, top of the hand-off 05 stack): read it
     next session.** GATE PASS on both = the merge condition of item 39 (b). (Artifacts cannot be downloaded from a chat: read the
     job log with `gh api .../actions/jobs/<id>/logs`.)
   - **PART 2's 132 DELETED LINES (#127): OK.** 130 are `kpc_park_pages.py`: the per-area read loop rebuilt as one worklist sequence
     (stop + `left` for the next run), the old fingerprint skip now a 30-day refresh plus a same-fingerprint skip after the fetch, and
     `cmd_read` split into `_prepare` / `_finish`; every rule of the old loop is still there (no page, agency home, budget, refused /
     dead / script-built, list page, evidence drafts). New: no fixtures + KPC_NO_NET=1 reads nothing. One old edge kept: a park marked
     unchanged with no old fact on disk is written as an empty stub (a fresh --out with an old --state).
   - **`kpc_park_pages_rules.py` AGAINST R-PR1 TO R-PR13 (read whole, 1,285 lines). Three real defects, each reproduced on the code:**
     **(A) R-PR4 "a sentence about THIS place" is not tested:** only trail / campground / visitor-place subjects are refused, so "The
     Gauley River flows within the New River Gorge National Park" and "Nearby, Babcock State Park is part of the Monongahela National
     Forest ..." are stored as `inside_of` facts. **(B) A park inside ITSELF:** `inside_units` never uses the park's name and
     `match_unit_ref` does not skip the park's own number: "Recreation sites within the Red Cliffs National Conservation Area ..." on
     that NCA's page = INSIDE_BIGGER_UNIT with its OWN number. **(C) R-PR9 `center=<lon>,<lat>`:** read as lat,lon whenever |lon| <= 90,
     so every such point east of -90 (all of the East, Kentucky too) is turned around and then dropped (silent, not wrong).
     Smaller: R-PR3's kind list is hand-written, not built from the parkinfo types (no National Grassland / Scenic Area / Heritage Area
     / Natural Area / Game Land: those stay silent); a "GPS:" line is always role `park` (R-PR6 says label-led); tract words add
     `Corner` (for Laurel) and `Unit` / `Section` catch office names (questions only); a 2-park shared page gives its sizes and
     inside_of to both parks (G-PR2 must not let a key rule read those for a shared page); a list page reuses the code
     AGENCY_HOME_ONLY. What holds: unofficial host = no sizes / location / inside / maps; agency home and lists read nothing; two
     units = neither stored; heading-vs-title disagreement = best null; sizes only through `sizes_in`, never added; no geocoder;
     pictures only per R-PR13 after part 5; quotes clipped at 200.
   - **OPUS'S CALL, Fable's to overrule:** (A) and (B) are wrong facts, so they would count WRONG in the blind kits: fix them BEFORE
     `kits --n 40` (a small part 6 for the agent: subject must be this park's name / "the park" / "this <kind>", or the page's own
     heading; skip a unit whose core + kind equal the park's own; `match_unit_ref` skips `ref`; center = lon,lat when the key is
     `center` and the numbers are degrees). They do not block the MERGE (the tool only reports, G-PR2), so merge #126 -> #131 on GATE
     PASS, then part 6.
   - NOT DONE (next, in order): read 44630734620 + 44631073762; merge the stack on GATE PASS; the seed + ONE by-hand reader run; kits
     after part 6; wire the not-sure rows; anchor `gov_of`.
44. **HAND-OFF 06 REVIEWED: #289 / #290 / #292 ALL NOT YET, PART 4 = YES ON TERMS (Fable, 19 Nov ~5:20 PM CST; the item 42 starter).** Read at 18d0eb0 / 906d5e8 / f9fb3cc, run on Python 3.13.18, numpy 2.5.3, OpenCV 5.0.0 (3.12 not possible in the chat). Review file `REVIEW-hand-off-06-PRs-289-290-292.md` + `review-06-probes.zip`, given to Brandon for the agent. No changelog line is stamped.
   - **#289:** six rules right. R-2F4: `made_on` is missing on every row that leaves `decide()` early (water only, not sure, dropped, KNOWN_LIVE), so the copy paths would drop them and call them "made before this rule" (the 28 Oct Kentucky Lake loss again); the stamp misses `parts` (27 parks) and `approx`; no outline in the stamp on runs without the store (Kentucky, old path, world); the "still from before this rule" report line names the file the run just wrote. `test_fers_area_boxes_time_nov11.py` and `test_fers_one_program_nov16.py` pass on 7b36ae5 and fail on the branch.
   - **#290:** the math guard misses `merge` and nine more functions (a change to `merge()`'s pad passes it); pasting a new fingerprint into the fixture, with nothing re-measured, satisfies it.
   - **#292:** the new file is written with `write_text`, not `save_json`: `test_fers_store_nov13.py` fails (the red check on the PR). Rows are not limited to the run's own areas.
   - **MY ERROR IN THE RULE SHEET:** KA-13 cannot happen. `merge()` joins spots of one pair whose boxes are within 0.0005 degrees each side, about 100 m: two 30 m strips are ONE spot at 80 m apart, two at 120 m (run with the real grid). Owner question G1: the 100 m he ruled out is still in the measuring step; my lean is to fix it as its own change before the first fresh 2-fer run. Not asked yet.
   - **PART 4:** a second look at 1 m cells for near-line area rows only, same `area_spots()` math, band stays one cell of the grid that measured, own draft PR after parts 1 to 3 pass. Measured with the real code, 43 widths x 16 placements: 5 m reads -4 to +8 m; 2 m reads -2 to +3 m and one reading (true 45 m read 48 m) slips a one-cell band; 1 m reads -1 to +1 m and none slips. Told to Brandon as a tool setting, his to overrule.
   - **74 to 127:** 127 is right (re-run with the bot's own test). Idaho's 55 lake parks were already in the key on 17 Nov and the layer labels have not changed since, so 74 was an undercount.
   - **GATE STILL OWED** on Python 3.12 and 3.13 for the stack. NEXT: the agent's second round on the same three branches, the gate, then a Fable chat. 2-fer runs stay parked.

45. **THE TWO OUTSIDE REVIEWS, THE KEYS HAND-OFF (REVISION 3.1), AND THE OWNER'S STOP (Fable, 19 Nov 5:30-6:40 PM CST).**
   - **THE OWNER'S RULING, 5:53 PM, his words:** "No building maps till all the oatches are done...we writing patch after patch and we still have a mess fix the problems get the info we need and then try one last time before I give up". **HOW FABLE APPLIES IT (told to Brandon, his to overrule):** no key rebuild, no outline rebuild, no Release, no 2-fer run. BOTH daily key starts go off (Opus, first). A small offline test build that only makes a "who changes" list is allowed.
   - **THE PATCH LIST IS CLOSED. Four things, nothing added unless it blocks one:** (1) hand-off 06 second round (#289 / #290 / #292); (2) the hand-off 05 stack; (3) the keys first slice (revision 3.1, S1 to S6); (4) the Release guard fix (Grok F1), the daily map-lag line (Grok F3) and three release checks: an outline sits only in the file of a state whose key lists the park; none is `via: name+pin` unless named; NV US-2635 is held or fixed first. New findings go on a list for later.
   - **THE INFO, gathered while the patches are written:** the sample on TODAY'S saved key (at least 299 random outlined parks, two blind passes, plus the 25 busiest per state; graders and outside agents; no build needed); Kit C's second pass; the "who changes" lists, read by Fable in one sitting. **THEN ONE BUILD:** every switch Fable passes on together, one run, the parks changed must be exactly the lists or it does not save; fact check; a second sample; a state goes public only on its numbers.
   - **BOTH OUTSIDE REVIEWS READ** (hand-off 07: the Claude one, F1 to F24; and Grok's, F1 to F17 with `gap.py`). They agree: about a third of public US outlines were not built from the key; the drop guard sees only a lost outline; "verified" mostly checks the name against itself; no error rate yet; sealed gold and kit answers are on the public branch. Item 43 (c) already cut the not-from-key outlines 3,862 -> 197 in the WORKING files; 166 of the 197 are strays in another state's file. Grok measured the public shelf at 76.6% of outlined US parks and 13.2% of Canada (notes say 85.2%): matters after R-2F7. NV US-2635 is now built from the key and so holds the whole 321,709-acre recreation area: Nevada does not go public until it is held or fixed.
   - **THE KEYS HAND-OFF = `KPC-hand-off-keys-first-for-Opus.md`, REVISION 3.1 (6:25 PM), accepted by Fable with two additions:** (a) the stop above (both starts off; the sample is on today's key and waits for no build; S1 comes before the sample); (b) the three drafts that edit `kpc_us_key.py` are STACKED in this order: hold on error, holder table, saved answers; S5 waits for S4.
   - **WHO DOES WHAT:** the outside agent drafts five (the hold-on-error part of S2, S6a, S6b, S4, S6c), each a draft PR for a Fable chat. **Opus does S1, the workflow parts of S2, S3 and S5.** Matching rules (names that collide, the size test A1, switching the piece rule and D5 on) wait for the sample and a rule sheet from Fable. Batch 2 (2-fers) is held whole; T6 (push check) and T7 are free.
   - **OPUS'S ORDER:** (1) both daily key starts off; (2) these two items saved; (3) item 43's open lines that are not builds; **the information bot is next, by the owner (6:18 PM: "Lets get the information bot running soon"):** read gate run 44631073762, merge the 05 stack on GATE PASS, part 6 for the three reading faults (A, B, C of item 43; Fable agrees with Opus's call), then ONE by-hand run on Kentucky only, then a blind check before any tool reads its facts; (4) S1; (5) the sample kit from today's saved key, two zips to Brandon, and the Kit C second-pass packet; (6) S2 workflow parts, S3, S5; (7) the gate on 3.12 and 3.13 for each outside-agent stack when it comes back.
   - **KPC-DATA SIZE (Brandon's two-day check, 1.49 GB):** told him yes to write-on-change for `layers.json.gz` and the scoreboard; yes to the cleanup but keep `tools-out`, `intake-files`, `lookup`, `picture-maps` and every branch with an open PR; the history restart waits until the patch list is closed. After S1, squash `tools-out` so the old sealed answers leave the public history.
   - **STILL FABLE'S, NOT DONE:** item 43 (e), the public-against-working table (packet run 44630734620). The release steps are stopped by the ruling above anyway.
   - **A catch-up zip for a fresh outside-agent chat** (`KPC-catch-up-19-Nov.zip`: jobs A = 06 second round, B = the five key drafts) was given to Brandon at 6:05 PM. At that time GitHub showed no second-round push and no key-draft branch.
   - **OPUS, 19 Nov 7:10 PM (saving this item):** done so far of the order: (1) both US key starts + the nightly boundary rebuild off (KPC-Links ad948ef); (3) the 05 stack's first gate FAILED only on the stack being behind main and the reader workflow's commented `cron:` line (the club's schedule guards count it); fixed, GATE PASS 3.12 + 3.13 (KPC-Data run 44643536837), landed in main b9b8e28; faults A / B / C fixed with one test each, GATE PASS (run 44645715357), main 2ea99d0; the ONE Kentucky reader run = KPC-Data run 44647016424 (read next). Item 43 (d)'s packet (44630734620) was NOT saved (the named-folder save staged only review-packets/; fixed fd34b10) and is not rerun. Next: the blind check of the Kentucky facts, then S1.
46. **OPUS, 19 Nov 7:10-8:00 PM CST: the information bot's Kentucky run, S1 DONE, the sample kit and Kit C pass 2 handed out.**
   - **Kentucky reader:** run 44647016424 stopped at the start (the flat not-sure seed sat beside the area files; fixed KPC-Data a82e06e,
     two tests; the 104 seed rows are now area files on tools-out `not-sure/`, cc23aa4, all kept). Run 44651852948 read NOTHING:
     `data/parkinfo` leaves Kentucky out on purpose. The reader now fills US-KY from POTA's saved list
     (`data/pota/saved/parks/US-KY.json.gz`, type from `data/docs/US-KY.json`; f652660, one test; 193 parks, worklist 193).
     **Run 44654168919 is the real first Kentucky run: read it next, then the blind check of its facts before any tool reads them.**
   - **S1 DONE.** KPC-Store 9e29899: `key-quality/` holds gold-us.json and 96 answer files (every kit-keys/, answers*/, score/,
     gold-old/new.txt, hand-off 04's rows.json + scored files), same paths as on tools-out; README there. The 12 SEALED rows were
     public: all 77 gold rows are TUNE now (`was_sealed_until`). **New sealed set:** 12 parks of the sample nobody had seen (not in any
     kit, packet, answer file, gold, the not-sure list or these notes), named only in the sample's private key (`sealed_next`).
     tools-out: the 96 files deleted (no history rewrite; `key-quality/ANSWERS-MOVED.md`); squash it later as item 45 says.
     Packet bot (KPC-Data 7b92c0e + 19166c3): reads no gold; its summary says where gold is scored. **Gold is scored only in
     KPC-Store, "KPC gold score (private, by hand)"** (`kpc-store-gold-score.yml`): KPC-Links MAIN's grader at the commit it records,
     a read-only scoring job, counts only in the log, results on the private branch `gold-scores`. First run 44653805226 (TUNE only,
     so flattering): release key addf5c4e wrong land 10.4%, too big 11.7%, missing pieces 28.6%; today's key 1.3% / 0.0% / 26.3%.
   - **THE SAMPLE KIT** (KPC-Store `key-quality/2026-11-19/sample/`, seeded `scripts/make_sample.py`, key US-44613348117): population
     11,585 outlined parks (official + approximate) in the 50 areas of the US key (Kentucky has its own key). Job S = 300 random +
     8 planted per pass (gold TUNE rows: 8 show only the right records = YES, 8 add one wrong record); job T = the 25 busiest of each
     state less those in S, 1,193 rows. Two passes: different order, item numbers and plants. Zips `KPC-sample-19-Nov-pass1.zip` /
     `-pass2.zip` given to Brandon for two fresh agent sessions; Kit C's second-pass packet `KPC-kitC-pass2.zip` too.
     **Answers come back into KPC-Store, never tools-out.**
   - **NEXT (fresh Opus chat, order of item 45):** read Kentucky run 44654168919 + the blind check; S2's workflow parts (a held state
     ends as a warning, not a failed run; the check that refuses a rule-file edit with no scope entry; `index.json` records source
     mode, drop limits and every switch value; both starts are already off); S3 (the three baselines from the saved copies' counts,
     the gate refuses a stale baseline and treats a missing copy as a finding, the ready check as a report with its blocking part
     behind a switch, OFF); S5 waits for the agent's S4. Then the gate on 3.12 + 3.13 for each outside-agent stack.
47. **OPUS, 19 Nov 7:35-8:10 PM CST: item 46's NEXT. The Kentucky run had read nothing; two crashes fixed; the real run started.**
   - **Run 44654168919 read NOTHING:** it stopped on park 1 of 193 (US-3791) with `NameError: re` in `_extra_urls` and stayed green
     (the reader step ends in a warning). An offline dress rehearsal (all 193 KY parks through the whole reader, fixture pages, no
     network) then found a SECOND stop the live run would have hit: the refuge (FWS) path handed `urlunsplit` urlparse's six parts.
     Both fixed (KPC-Data main 4816f03f), one test each, plus: each park is read inside a guard (a page the reader cannot handle is
     skipped, named in a warning and in summary.md "Skipped on a reader error", read again next run; the others carry on) and a test
     that every reader file uses only names it imports. Reader tests ALL PASS on 3.12 + 3.13; full suite = main's same 23 failures
     (libraries missing here), none new. Rehearsal after the fix: 193 of 193 read, 0 left.
   - **THE REAL FIRST KENTUCKY RUN = KPC-Data run 44656781088 (on 4816f03f, areas US-KY).** Read it next: summary.md (asked 193?
     any "Skipped on a reader error"?), then the blind check of its facts before any tool reads them.
   - **S2 workflow parts and S3 NOT STARTED:** `KPC-hand-off-keys-first-for-Opus.md` (revision 3.1) is in none of the three repos;
     item 46 holds only one-line summaries, and these edit kpc-us-key.yml's hold / freeze logic. Asked Brandon to attach the file;
     when it comes, save it to KPC-Store `key-quality/2026-11-19/` so the next chat has it. S5 still waits for the agent's S4.
48. **OPUS, 19 Nov 8:27-9:10 PM CST: the rev 3.1 file came; S2 + S3 drafted; the Kentucky run read; REPAIRS.md is the one list.**
   - The hand-off file is saved in KPC-Store `key-quality/2026-11-19/keys-first/` (34834e6). **S2 workflow parts = draft #294**, **S3 = draft #300**. Neither moves a rules hash (US c64b8ace0411).
   - **S3, for the reviewer:** the three layer baselines are now 317 / 2,150 / 228 (the saved copies' rows, no re-read). On all 50 saved copies (tools-out fbeca817): 24 state baselines are LOWER than their copies (Nov 10 baselines; copies grew), 90 layer baselines differ in 48 states, and the ready check would hold 48 of 50 states. So both blocking parts are switches, OFF (KPC_GATE_STALE_REFUSE, KPC_READY_BLOCK), until the reviewer sets which count a baseline must match.
   - **Kentucky run 44656781088:** 193 of 193 read, 0 skipped, 53 resting (read again next run), 73 AGENCY_HOME_ONLY. Facts: KPC-Data tools-out `park-pages/facts/US-KY.json`. NEXT: the blind check, before any tool reads them.
   - **`.claude/inbox/REPAIRS.md`** (Fable's checklist, 9:05 PM) is the ONE list for every map chat; ticked only with proof.
