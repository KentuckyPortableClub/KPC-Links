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

## 6. Order of work
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
