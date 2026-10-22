# Park boundaries: a brief for review

Written 22 Oct 2026 for Fable to read cold and come back with recommendations. Brandon asked for it at
3:39 AM. Everything here is the real state of things, including the parts that have not gone well.

---

## What we are trying to do, and why

Brandon White (KZ4CP) runs the Kentucky Portable Club. Members take radios to parks, lakes and summits and
make contacts from there — Parks on the Air (POTA), WWFF/KFF and SOTA. **To get credit, the operator has to
be inside the park's real boundary.** POTA gives us a park's name, a reference like US-1271, and a single
latitude/longitude pin. It does **not** give us the boundary.

That pin is often an office, a sign, a car park or a rough centre. So the question every activator actually
has — *where exactly can I set up?* — is one POTA cannot answer. Our answer is to join each POTA reference to
the official government land record for that place, which does carry a real outline.

Everything the club has built on top depends on that join being right:

- **Park Control** — every reference on one map with its outline and parking
- **Am I in the Park?** — phone tells you whether you are inside the line
- **the trip planners and the Kit** — what is reachable, what is nearby
- **2-fers** — two parks whose boundaries overlap, which needs real polygons
- **park alerts** — a closure notice has to reach the right park (we got this wrong, see below)

A wrong join is worse than no join: it draws a confident outline around the wrong piece of ground and someone
drives there.

## Where we are

| | places | POTA refs | joined | to check by hand | nothing found |
|---|---|---|---|---|---|
| United States | 50 | 13,074 | 10,150 (77%) | 904 | 1,448 |
| Canada | 15 | 5,897 | 3,891 (65%) | 253 | 1,697 |
| Rest of world | 28 | 55,876 | 41,225 (73%) | 4,209 | 10,442 |

"Joined" means we believe we know that park's outline. "Nothing found" is the bigger pile and gets the least
attention, because there is nothing to look at.

Brandon's stated priority (Oct 20): the United States and Canada first; the top ten countries after that;
beyond that is about 2% of POTA activity and is not worth more work. Historic sites, markers and council or
city parks are never worth chasing.

## How the bots work

All of this runs as GitHub Actions workflows on a schedule — there is no server. Scripts live in
`.github/scripts/`, data in `data/`, and each run commits what it found back to the repo.

- **`kpc_us_key.py`** → `data/us-key/US-XX.json`. Reads USGS **PAD-US** (federal and state fee land) plus
  per-state extras (BLM national conservation lands, wilderness study areas, herd management areas, state
  wildlife layers) and matches them to POTA's Kentucky-and-beyond park list.
- **`kpc_world_key.py`** → `data/world-key/CC.json`. Same idea per country, from whatever that country
  publishes: national registers, Natura 2000, protected-area services.
- **`kpc_ca_key.py`** → `data/ca-key/CA-XX.json`. Canada, per province.
- **`kpc_boundary_report.py`** + **`kpc-boundary-check.yml`** (nightly, 14 states a night) — the newest piece.
  It does not match anything; it *audits* the matches and writes findings into **GitHub issue #14**, editing
  the body rather than commenting so nobody gets emailed.
- **`kpc_park_alerts.py`** — separate but related: watches five agencies for closures and has to decide which
  park an alert is about. Same name-matching problem, different consequence.

House rules that shape all of it: **every failed run emails Brandon**, so scripts catch their own exceptions
and exit 0 rather than failing; bots must never flood; a bot comments on an issue only for a real problem.

### The shape of a key file

```
"US-1271": {
  "n": "Taylorsville Lake State Park", "t": "State Park",
  "m": [[objectid, "Taylorsville Lake", acres, "name"]],   // joined
  "c": [],                                                  // candidates for a person to look at
  "far": "edge",                                            // audit: pin is outside what we joined it to
  "swap": [[objectid, "...", acres]]                        // another area of the SAME NAME contains the pin
}
```

## How the matching actually works

Join on **same name AND same kind of place**, near the park's pin:

1. **Normalise the name.** Lowercase, strip punctuation and accents, expand abbreviations, then strip the
   "generic" words that say what kind of place it is — "state park", "wildlife management area", "national
   forest" — so that `Taylorsville Lake State Park` and `Taylorsville Lake` meet.
2. **Check the kind matches.** A hatchery only joins a hatchery; a trail only joins a trail; a WMA joins a
   WMA. This is what stops a park joining the forest it sits inside.
3. If the names agree and the kinds agree and it is near the pin, **join**. Otherwise put it in `c` for a
   person, with a reason: *similar name*, *same name but different kind*, or *the pin is inside it*.

Two extra rules were added this week:

- **NAME_JOIN** (world script only): POTA often writes the kind onto the end of the official name — "Nemuno
  delta Regional Park" for an area simply called "Nemuno delta". Those names already agree once generics are
  stripped; only the *kind* differed. Measured before enabling: 600 joined, 44 left ambiguous.
- **PIN_JOIN** (Japan only): if the pin sits inside exactly one official area of a fitting kind, that is the
  park whatever it is called. Took Japan from 102 joined to 182, check pile 82 → 2.

## What has been difficult, honestly

**1. There is no such thing as "the" boundary data.** Every country, and in the US every state, publishes
differently. Some have one clean national register; some have a dozen agency layers that overlap; some
publish nothing. A lot of the work has been finding a usable source at all, and several have no public one.

**2. Names are the only thing both sides share, and they disagree constantly.** POTA's name is whatever the
person who submitted the reference typed. The official name is whatever the agency calls it. They differ by
abbreviation (SWA / State Wildlife Area), by word order, by the kind word being present or absent, by
accents, by sub-unit names, by language.

**3. Stripping generic words is necessary and dangerous.** We strip "refuge" because it usually means
*what kind of place*. But "**Refuge** Cove" is a cove called Refuge. Stripping it left "cove recreation site",
which then matched *Settler's* Cove State Recreation Site — a different place. Fixed on 22 Oct by putting a
leading type word back when stripping leaves almost nothing. **This fix is English-only.** French, Spanish,
Italian and German put the type word first ("Parc national de…", "Nationalpark…"), so the same rule ported
naively would keep "parc" in every name and wreck half of Europe. ⚠️ This is the single easiest way to break
things badly, and it has not been solved for other languages.

**4. Confident wrong answers are the real risk, not missing answers.** Three examples, all real:
- The Mammoth Cave "Green River Ferry" closure notice was attached to **Green River State Forest** *and*
  **Green River Lake State Park** — two parks, neither of them the ferry. Fixed by refusing a match when the
  next word in the text is a place word that is not in our park's own name.
- "Beaver Creek Wilderness" in the Daniel Boone forest was attached to **Beaver Lake** in Anderson County,
  150 miles away.
- **Upper** White Oak Lake and **Lower** White Oak Lake had *both* joined the single White Oak Lake State
  Park. Fixed 22 Oct: Upper/Lower/North/South/East/West now tell two places apart.

**5. The hand-check pile cannot be hand-checked.** 6,850 parks at twenty seconds each is about thirty-eight
hours. The only way through is rules that clear hundreds at a time, measured against the saved keys before
being switched on. That is how NAME_JOIN was done.

**6. We were measuring the wrong thing, and did not know for months.** Until 21 Oct, a join was counted a
success the moment the names agreed. Nothing ever asked whether the boundary we picked actually contains the
park. The first audit said **37% of joins in Idaho, Utah, Nevada and Wyoming have the pin outside** — which
read like a disaster. It was not. On six fully-audited states (1,095 joins):

- 485 sit **just outside the line** (within about a mile) — boundary precision, or a pin at a gate
- 41 are **well outside** — and on inspection most are huge scattered areas (Kodiak National Wildlife Refuge
  is islands; one pin cannot be inside every piece) or abbreviations
- **4 were really wrong** — 0.4%
- **0** had another area of the same name containing the pin

So the matching is in far better shape than the headline suggested — but it took building the audit to know
that, and the 37% would have been quoted as fact if nobody had looked at the actual rows.

**7. Some sources simply do not publish.** Kentucky's nature preserves (20 references) and state forests (7)
have no closures or conditions page anywhere. The Corps of Engineers publishes closures only as press
releases. Checked, confirmed, written off — those gaps are not for want of looking.

## What we think comes next

1. Port the audit to the world and Canada keys — it is mechanical, and it is the only way to know whether
   73% and 65% mean anything.
2. Cross-port the rules each script is missing: NAME_JOIN is world-only, Upper/Lower is US-only.
3. Extend PIN_JOIN past Japan. The "nothing found" pile is 13,587 across the world and Canada, nearly twice
   the check pile, and no rule has ever been aimed at it.
4. Transliteration for non-Latin scripts — Greece, Bulgaria, Korea, Israel, Thailand, Russia are matching
   English POTA names against native-script official names and failing almost completely. Japan got romaji
   via pykakasi; nowhere else did.

## What we would value your view on

- Is name-plus-kind the right backbone at all, or should the pin and the geometry lead, with names as the
  tie-breaker? We arrived at name-first by accident rather than by deciding.
- How would you handle the leading-type-word problem across languages without hand-writing a rule per
  language?
- Is there a cheaper signal we are ignoring — area, pin-to-polygon distance, how many candidates overlap —
  that would separate right from wrong joins better than more name rules?
- The audit's "well outside" flag is mostly noise (scattered areas, abbreviations). Is there a better test
  for "this join is wrong" than whether the pin is inside?
- Anything in the above that looks like it will break at scale, or that you would not have built this way.

---

## Review — Fable, 22 Oct 2026, for Opus

Read quickly at Brandon's request. Same session that wrote the brief, so treat this as a hard second look,
not an outside one. The recommendations are concrete and each can be measured against the saved keys
before being switched on, the way NAME_JOIN was.

### The one structural answer to question 1: invert it. Geometry leads, names tie-break.

The brief says name-first was arrived at by accident. It shows. Every confident-wrong-answer in the
"difficult" list — Refuge Cove, Green River Ferry, Beaver Creek → Beaver Lake, Upper/Lower White Oak — is a
name match that geometry would have refused in one line. Meanwhile the single rule that *does* lead with
geometry, PIN_JOIN, produced the best result anywhere (Japan 102→182, check pile 82→2) and is switched on
for **one country**. That is the finding of the whole brief and it is stated as item 3 of a to-do list.

Replace the pile of special-case rules with **one score per candidate**:

- pin **inside** the candidate: strong
- pin within a distance scaled by the candidate's size (see below): medium
- normalised name **exact**: medium — and only strong when that name is **unique** in the country
- name fuzzy: weak
- kind mismatch: gate (reject), as now
- POTA's **state and county** disagree with the candidate's: gate (reject)

Join when the top score clears a threshold **and the runner-up is well behind**. Everything else to the
check pile with the scores shown. One function, one threshold to tune, measured once.

### Question 2 — the leading-type-word problem: stop guessing by position.

The 22 Oct fix is a positional hack and the brief rightly says it breaks outside English. Drop it for this:

**A match must share at least one STRONG token** — a word that is (a) not in the country's generic list,
(b) not a bare geographic noun (cove, creek, lake, river, bay, point, mountain, hollow, fork…), and (c) at
least four letters. "Refuge Cove" vs "Settler's Cove" share only *cove*, which is a geographic noun → reject.
"Kodiak NWR" vs "Kodiak NWR" share *kodiak* → accept. "Parc national de la Vanoise" vs "Vanoise" share
*vanoise* → accept, whatever order the words come in. The geographic-noun list is short (~50 words a
language), stable, and far safer than reasoning about word order. It also kills the Beaver Creek → Beaver
Lake class outright, because *beaver* alone would pass but *creek* ≠ *lake* is a weak-token mismatch when
it is the only other thing they share.

### Question 3 — cheap signals being ignored. All of these are already in the data.

1. **County.** POTA's API carries the state and county of every reference. The alerts matcher and the keys
   ignore it. Beaver Creek Wilderness (Daniel Boone) → Beaver Lake (Anderson County, 150 miles off) dies the
   instant county is a gate. This is the cheapest, highest-value fix in the whole document.
2. **Area.** `acres` is stored for every candidate and never used. A "State Park" of 2 acres or 2 million is
   wrong. Use the kind to set a plausible range and reject outside it.
3. **Distance normalised by size.** "Edge" is currently a flat ~1 mile. A mile outside a 500,000-acre refuge
   is nothing; a mile outside a 40-acre SWA is a different place. Use distance ÷ √area.
4. **Name uniqueness.** Pre-count how many official areas in the country share each normalised name. A name
   match against a unique name is near-certain; against one of twelve "Beaver Creek"s it is near-worthless.
   One pass, then it is a number on every candidate.
5. **Many-to-one.** Two POTA references joined to one polygon (the White Oak Lake case) is a red flag with
   no false positives worth worrying about. Detect it and demote both. General, trivial, not yet done.
6. **Nested candidates.** PIN_JOIN gives up when the pin sits inside more than one area. It should prefer
   the **smallest** candidate of a fitting kind — a pin inside forest > wilderness > trail is the trail.

### Question 4 — a better "this join is wrong" test than pin-inside.

Pin-inside is one-sided: inside means almost certainly right; outside means *unknown*, which is why
"well outside" is mostly noise. The discriminating question is **"does a different candidate fit better?"**
— which is the swap test, correctly conceived but too narrow. Extend it from *same name* to *any candidate
of a fitting kind that contains the pin when the joined one does not*. That catches Beaver Creek Wild and
Scenic River → "Eastern Interior Field Office" (the river polygon almost certainly contains the pin; the
office boundary does not). With county and size-normalised distance added, the audit stops needing a human
to read 41 rows to find 4.

### Question 5 — what breaks at scale.

**Three scripts, three divergent matchers** is the structural fault. NAME_JOIN is world-only; PIN_JOIN is
Japan-only; Upper/Lower is US-only; the leading-word rule is English-only. Every rule has to be ported by
hand to the other two, and each port is a chance to get it subtly different. Put the scoring function in
**one module** (`kpc_match.py`) that all three import; per-country configuration is a generic-word list, a
geographic-noun list and the source list. Then a rule written once applies everywhere and is measured once.

**No regression test.** Rules are checked by hand in a REPL against whatever cases someone remembers. Keep
a **golden file** of the known cases — Refuge Cove / Settler's Cove, Kodiak, Upper/Lower White Oak, Green
River Ferry, Nemuno delta, Camp Robinson WMA, Beaver Creek → Beaver Lake, Lake Mead — with the required
verdict, and run it on every push. The next rule change will break something old otherwise; it is only a
matter of which one.

**Measure-before-enable is the best practice in the brief.** Formalise it: a `--dry` flag that reports
joins gained / demoted per rule against the saved keys. It is already how the good decisions got made.

**The audit should not be a separate pass.** Once pin distance is in the score, "is the join right" is
answered at join time. Keep the nightly report for the humans; stop maintaining two notions of correct.

### If only three things get done

1. Gate on **county** everywhere. One afternoon, kills a whole class of error.
2. Turn **PIN_JOIN on everywhere** with the smallest-of-fitting-kind rule, measured first. Biggest lever on
   the 13,587 "nothing found".
3. The **golden test file**, before any further rule changes.

Everything else follows from the single scoring module, which is the real fix and a few days' work.

### Speed — Fable, 22 Oct (Brandon: 'Any suggestions on how to speed up the process')

Nearly all the time is **re-downloading the same official geometry every run**. ~11 min a state is PAD-US
paging; the matching is seconds. In order of effect:

1. **Fetch once, cache, match locally.** Pull each state/country layer one time, simplify (~0.0005°), store
   compressed as **GitHub release assets** (not in the repo), refresh monthly. A full 50-state rebuild then
   takes minutes. Everything below depends on this.
2. **Split fetch from match.** One script does both today, so measuring a rule change costs a 5-hour run —
   and geometry rules (PIN_JOIN, distance, swap) cannot be measured offline at all because the saved keys
   keep no shapes. With a cache, a rule is measured in two minutes. This is what makes the single scoring
   module practical.
3. **Matrix.** 10 parallel jobs × 5 states, each uploads its key as an artifact, one final job commits.
   All 50 in one run. (Mostly moot once 1 is done; fixes the four-night crawl now.)
4. **Skip unchanged states.** Hash the POTA list + source metadata; rebuild only on change. The nightly
   audit becomes near-free.
5. **Pull less.** PAD-US `where`: fee land only, plausible designation types only, GIS_Acres ≥ 1. Fewer pages
   before anything else.
6. **World: batch Wikidata.** SPARQL `VALUES` with 50 ids per query, cache answers. Already identified as
   the slow part in the Oct 19 trigger notes.

Do 1 and 2 together; they are the same refactor. 3–6 are each an hour.
