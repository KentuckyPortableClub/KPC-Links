# Missed 2-fer finder: rule sheet + build spec (chat 10, Oct 31 2026)

Brandon, Oct 31 7:15 PM: "give the instructions I will have it built".
Builder: the outside coder. Folder `kpc_missed_fers/`; it follows the KPC install contract (KPC_Install_Contract.md). Chat 10 installs it.

**Idea.** POTA publishes every park's activation history. When different activators keep activating the SAME two nearby parks on the SAME day, those parks very likely overlap: a 2-fer. The tool lists those pairs **that our 2-fer lists do not have yet**, so the club's own 2-fer line and the research desk can check them against the official outlines.

**It never adds a 2-fer.** Its pairs are leads only. The official outlines and the club's 2-fer rules (R0-R10) still decide everything.

---

## PART 1. RULE SHEET (draft for chat 8 + Brandon)

**1. What counts as a lead.** Two POTA parks A and B where all of these hold:
- **Same day:** the same callsign activated both on the same UTC date.
- **Several activators:** this happened for **at least 3 different callsigns**, on **at least 3 different dates**.
- **Nearby:** the two parks' POTA pins are **within 15 km** of each other. If either park has an official outline, the outlines may be up to 2 km apart instead.
- **New to us:** the pair is in none of these lists:
  - our live 2-fer list (`data/fers/<area>.json`);
  - the missing-boundary list (`data/fers/missing-*.json`);
  - the known answers (`data/fers/known-answers.json`, both its YES and its NO pairs);
  - the dropped / checked-NO rows.

**2. What does not count:**
- **Rove days:** a callsign that activated **5 or more parks** that day adds nothing for that day. Roving activators string many parks together, and that proves nothing about overlap.
- **Pins too far apart:** more than 15 km, unless the outlines touch.
- **Not a POTA pair:** KFF / SOTA / WWFF references, or any reference without a POTA park number (only two POTA parks can be a 2-fer).
- **Different countries:** never paired.

**3. Sources, best first.**
- POTA's public data: `https://api.pota.app/park/activations/<ref>?count=all` (callsign, date, QSOs) and the park lists per location (`https://api.pota.app/location/parks/<location>`, e.g. US-KY). These need no key. The coder confirms the exact endpoints on day one and writes them in the README.
- Pins: the club's `data/parkinfo/*.json` (the same POTA pins).
- Outlines: the club's keys (`data/us-key`, `data/ca-key`, `data/world-key`), for the 2 km outline test and the outline status.

**4. When unsure.** Below the thresholds = not listed (kept only in the tool's own log). Callsigns are used only to count different people. **Callsigns never appear in any output** (privacy: we count people, we don't name them).

**5. What people see.** Nothing on the website. The leads go to the chats:
- **Both parks have official outlines** → chat 2's 2-fer line re-tests the pair and writes why it is not a 2-fer if it fails (usually a wrong or missing record: worth a look).
- **Either outline is approximate / pin-only** → chat 8's "check the official map" list (the same place as the missing-boundary list).
- **One of the two is a trail or river park** → its own short list, because trails cross many parks and need the 100 ft trail rule.

**6. Examples to test with (Kentucky first).**
- **Mammoth Cave NP + Green River state wild river (US-0050 + US-10105):** this is already a known pair. The tool must NOT list it (it is already ours).
- **Two state parks that only touch at a border:** activators may stand on the line, so the tool may list the pair. The outlines then say "touching only = not a 2-fer" (R-rules). This is a correct lead with a correct NO, and a good test of the hand-off.
- **Daniel Boone NF + a state nature preserve inside it:** a likely real miss when the preserve's outline is approximate. It goes to chat 8's list.
- **A rover who did 12 parks in one day:** must not create a single pair by himself.
- **A pair activated together by only 2 people:** not listed (threshold 3).

**Grey areas for Brandon:**
- **G-M1:** Are 3 activators / 3 dates the right threshold? Lower finds more, but is noisier.
- **G-M2:** Is 15 km between pins right? Big parks such as national forests have pins far from their edges.
- **G-M3:** Should a pair that our outlines say only touches (side by side) be shown to chat 2 at all, or dropped silently?

---

## PART 2. BUILD SPEC (`kpc_missed_fers/`)

**In.**
- `--areas US-KY,US-TN,...` (default: every US + CA area, then the world in the club's order)
- `--parkinfo data/parkinfo`
- `--keys data` (us-key / ca-key / world-key)
- `--fers data/fers`
- `--cache <dir>`: activation lists are cached; a park's list is re-read only when its activation count changed (the park list gives the count), so weekly runs are cheap.

**Steps.**
1. **Park list:** for each area, read the POTA park list with each park's activation count. Skip parks with 0 activations.
2. **Activation history:** for each park with activations, read its history (cached; 1 request every 2 s to api.pota.app; it stops cleanly at `--max-minutes` and resumes).
3. **Index:** build `(callsign, date) → [parks]`, then drop rove days (≥ 5 parks).
4. **Count the pairs:** for every pair of parks on the same (callsign, date), count the distinct callsigns and the distinct dates.
5. **Filter:** keep the pairs that pass the rule sheet (pins ≤ 15 km or outlines ≤ 2 km; ≥ 3 callsigns; ≥ 3 dates; not in any club list).
6. **Route each pair:** to `fers-retest`, `check-official-map` or `trail-river`, by the outline status of the two parks in the keys.

**Out** (on the KPC-Data side branch `tools-out`, folder `missed-fers/`; never main, BRANCH FIRST):
- `missed_fers.json`
  - per pair: `{a, b, a_name, b_name, area, activators, dates, first_date, last_date, pin_km, outline_km | null, a_outline: "official|approximate|pin", b_outline, route, why}`
  - **no callsigns anywhere**
- `summary.md`: counts per area and route, with the top 50 pairs by activators.

**Acceptance.**
- **Known pairs:** on Kentucky, Tennessee and Virginia, ≥ 90% of the pairs in our live 2-fer lists with ≥ 3 joint activators show up in the tool's raw counts (it sees what we know). The final list must then contain none of them.
- **Hand check:** chat 8 checks 20 listed pairs against the official maps. ≥ 50% are real overlaps or real data problems (a wrong or missing record). The rest are border pairs our outlines correctly reject.
- **Privacy:** no callsign appears in any output file (test it with a grep).
- **Time:** Kentucky runs in one 50-minute run from an empty cache; a weekly re-run of the whole US finishes in ≤ 3 runs.

**How chat 10 wires it.**
1. A weekly workflow, after the 2-fer checker on Sunday.
2. `fers-retest` pairs go to chat 2's 2-fer line as a test list.
3. `check-official-map` and `trail-river` pairs are appended to the research desk's list for chat 8.
4. One status-board line per run.
5. Never red.
