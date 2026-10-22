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
