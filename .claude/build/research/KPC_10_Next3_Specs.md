# Three builds for the outside coder (chat 10, Oct 31 2026)

Brandon, Oct 31 10:20 PM: "Give me instructions for 1-3 detailed ... I'll use outside bot to build it."

Every tool follows the KPC install contract (`KPC_Install_Contract.md`, and PART A of `KPC_10_Outside_Tools_Specs.md`):
- Python 3.12, standard library first.
- `--selftest` works offline.
- `--max-minutes`, then exit 3, then `--resume`.
- Every output only inside `--out`.
- Never OSM, Google or WDPA. Official sources only.
- robots.txt is obeyed, with a 2 s gap per host.

Chat 10 installs each tool, runs it on GitHub, and wires it.

---

## 1. `kpc_acres`: the official acres LIST (the checkers already exist)

**What we already have.** The acres CHECKERS are built:
- the map audit (KPC 10, test T2: outline acres vs official acres, PASS / OFF / WAY OFF);
- the key's own size check;
- the truth bot.

They all compare an outline's size with an "official" size. Today that size comes only from the outline record itself (PAD-US GIS_Acres, CPCAD O_AREA_HA). When the record is wrong, its own size is wrong too, so the check can't catch it.

**What is missing.** The tool that reads each agency's OWN size list and turns it into one club file. The audit then reads that file with `--acres`.

### Input
- **The acres research file**, `acres-us-ca-oct31.json`: 190 agencies. 176 are FOUND, with a list page or download, a size column and a unit; 5 have a page only; 9 have no list. It also holds 606 sizes copied by hand ("Acres not downloadable").
  - Chat 10's intake reader puts it in `data/intake/_in/acres/`.
  - Read whatever row shape the file has. Write the exact field names you used in the README.
- `--parkinfo data/parkinfo`: POTA parks with name, type, pin, state. Kentucky's parks are in KPC-Links `kpc-ky-data.json`; chat 10's `kpc_gps_prep.py` already writes them as `parkinfo/US-KY.json`.
- `--keys data`: `us-key`, `ca-key`. Used for the record names and ids each park is joined to.
- `--areas US-KY,US-TN,...`: the default is every US area, then every Canadian one.

### Steps for each agency list
1. **Open the list** the way it is published:
   - CSV / XLSX download;
   - an HTML table;
   - an ArcGIS layer (query `outFields=*`, `returnGeometry=false`);
   - a Socrata / CKAN dataset;
   - a PDF table (pypdf text, row by row: take only the rows the parser is sure of).
2. **Read the name, size and unit.** Also read the id and county where the list has them. The unit is taken from the research row, or from the column header ("Acres", "Hectares", "ha", "km²", "sq mi").
3. **Convert to acres:**
   - ha × 2.47105
   - km² × 247.105
   - sq mi × 640
   - m² × 0.000247105
4. **Match each row to a POTA park.** Stop at the first rule that matches:
   - **a.** the list carries the park number (`US-1234`) or the same record id our key joined (e.g. the PAD-US Unit_Nm + id, the CPCAD id);
   - **b.** SAME NAME + SAME KIND of place, in the same state / province. This is the key's rule:
     - generic words are dropped ("State Park", "WMA", "Wildlife Management Area" ...);
     - a WMA only matches a WMA, a state park only a state park;
     - "X Lake WMA" never matches "X Lake State Park";
   - **c.** where the list gives a county or a point, that must agree with the park's pin (same county, or within 25 km).
   - Anything else is **NOT matched**. It is listed in `unmatched.csv` with the reason. Never guess.
5. **Several rows for one park** (units, tracts) are added together, but only when every row matches the same park by rule a or b. The `parts` field says how many rows were added.
6. **The 606 hand sizes** are taken as given, with `how: "hand copy (<agency>, <page>)"`. They still go through the same match rules.
7. **Sanity checks.** These rows are flagged, never dropped:
   - under 0.1 acres, or over 20 million acres;
   - a size more than 50 times the park's current outline;
   - the same row matched to two parks.

### Output (KPC-Data side branch `tools-out`, folder `acres/`; chat 10 copies the small final file to main, held in the waiting room)
- `acres.json` → `{ref: {acres, value_given, unit_given, agency, record_name, how: "number|record id|name+kind", parts, source_url, read_date, flags: []}}`
- `acres-list.json` → `{ref: acres}`. This is exactly what the map audit's `--acres` takes.
- `unmatched.csv` (agency, row name, size, why not matched).
- `report.md`, with one line per agency:
  - read OK, or failed and why;
  - rows read, matched, unmatched, flagged.

### Test
- **Small run:** Kentucky (KY State Parks, KDFWR WMA list, Office of Nature Preserves), Tennessee, Ontario.
- **Pass mark:**
  - On the Kentucky parks that have a hand-checked size (`ky-answer-key.json` acres), 95% of matches agree within 10%.
  - No WMA is matched to a state park.
  - Chat 11 checks 30 random matches, and at least 28 are right.
- **Time:** all of the US + Canada in 3 runs of 50 minutes or less.

### How chat 10 wires it
1. It runs YEARLY, plus whenever a new acres file lands on intake-files (the intake reader sees it).
2. `acres.json` goes through the waiting room to chat 11 (kind `acres`).
3. On a YES:
   - the map audit and the key's size check read it;
   - the truth bot uses it as the "official size" for any park that has no known answer.
4. A park whose outline is 1.5x off its official acres goes on chat 2's "check this join" list by itself.

---

## 2. `kpc_shard`: run the map bots several states at once

**Honest status.**
- The US boundary key ALREADY runs states side by side: a 6-group matrix, nightly for the touched states, monthly for all of them.
- The bots below still go through their areas ONE AT A TIME, and chain run after run:
  - layer collector (every 2 h);
  - documents merge;
  - map-format converter;
  - US access / parking (monthly);
  - state + US trails;
  - camp layers;
  - map-page links;
  - world finder;
  - the 2-fer checker.

GitHub gives a public repo **20 jobs at once**, free. We use about 3 of them.

**Build:** a small library plus one workflow template, so ANY of those bots can be split without rewriting it.

### `kpc_shard.py` (library + command line)
1. **`plan --areas <list|all> --groups N --weights <file>`.** Splits the areas into N groups of about the same work.
   - Weight = parks in the area. Read it from `data/parkinfo/*.json`, or take a weights file `{area: number}`.
   - Biggest first: a greedy fill.
   - The club's order is kept inside each group: US + Canada first, then North America, then W1-W10, then the rest (chat 10's `kpc_order.py` `rank()`: import it, don't copy it).
   - Prints the GitHub matrix JSON: `[{"i":1,"areas":"US-TX,US-RI,..."}, ...]`.
2. **`hosts --areas ... --map <file>`.** Many areas hit the SAME server (PAD-US `edits.nationalmap.gov`, the Forest Service EDW, `services.arcgis.com`). Given a `{area: [hosts]}` map (or the bot's own layer list), it puts areas that share a slow host in as few groups as it can, so at most **2 jobs ever hit one host at the same time**. The rest of the manners stay inside each bot (2 s gap per host).
3. **`join --parts <dir> --into <data dir>`.** Each job writes ONLY its own areas' files into `parts/<i>/`, plus a small `state-<i>.json`.
   - The join copies the area files in and merges the state files: the newest `done` per area wins; the counts are added up.
   - It also checks that no two parts wrote the same area. If two did, nothing is copied and the problem is reported.
4. **Exit codes, per job:** 0 = done; 3 = time ran out. The join then lists the unfinished areas, so the next run takes only those.

### `kpc-sharded.yml` template (a reusable workflow, `workflow_call`)
- **Inputs:** `bot` (the script to run), `areas`, `groups` (default 8, at most 12), `minutes`, `env` (JSON).
- **Job `plan`:** `kpc_shard.py plan`, then the matrix.
- **Job `run`** (matrix, `fail-fast: false`, `max-parallel` = groups):
  - checkout;
  - `AREAS=<group> python3 <bot> --out parts/<i>`;
  - upload `parts/<i>` as an artifact (artifacts, NOT git: no history cost).
- **Job `join`:**
  - download all artifacts;
  - `kpc_shard.py join`;
  - the waiting room `divert` (as each bot does today);
  - ONE push.
  - Chain once more if `join` says areas are left.
- **Never red:** every step is `continue-on-error`, and one status-board line goes up with the groups, areas done and areas left.
- It must keep the bot's existing concurrency group, so two runs of the same bot never write at once.

### What each bot needs (chat 10 does these small edits; the coder only builds the library + template)
- It must read `AREAS` from the environment (most already do).
- It must write only its own areas' files, plus a part state file.

### Test
- **Layer collector, on 12 US states:** split = 4 groups vs 1 job.
  - Same output files byte for byte (except dates).
  - Time cut by 3x or more.
  - No host hit by more than 2 jobs at once (log the timestamps per host).
- **Join refusal:** two parts writing the same area must be refused.

### How chat 10 wires it
1. **The collector goes first.** It is our widest funnel: 20 portals → layers → pin tests.
2. Then docs merge, access, trails, the converter, the camp layers, the world finder and map links, one at a time, each tested on a small area.
3. The 2-fer line stays one-at-a-time until chat 2 says the split is safe. Its neighbour-state edge rows read other states' files.

---

## 3. Map rebuilds the next morning (mostly ours to switch, not a new tool)

**Honest status (chat 10 was wrong earlier tonight).**

| map | rebuild today |
|---|---|
| US key (`kpc-us-key.yml`) | NIGHTLY (09:19 UTC) for the states touched by chat 11's new answers, plus a monthly full rebuild |
| Canada key | nightly ONLY when BOT W wires a new province layer; monthly full |
| World key | nightly wiring of approved world layers (BOT W); the full world rebuild is MONTHLY |
| Kentucky key | weekly (Mondays) |

So a US answer already shows the next morning. The slow ones are world outlines, and Canada outlines approved without a new layer.

**This is better done by chat 10 than by the outside coder.** It is three small edits in our own workflows:
1. **One "what changed today" file.** Every night after the release step, the waiting room writes `data/waiting/touched.json` → `{"US": [states], "CA": [provinces], "W": [countries], "KY": true|false}`, from:
   - that day's released items;
   - chat 11's new YES answers;
   - BOT W's wired layers.
2. **Each key workflow's nightly step reads `touched.json`** and rebuilds ONLY those areas:
   - Canada: any touched province, not only a new layer;
   - World: the touched countries, with the light saved outlines, as now;
   - Kentucky: the KY key when `KY: true`;
   - US: as now.

   Nothing touched = a green run that does nothing and posts one notice.
3. **The order every night:**
   1. release (06:43 UTC)
   2. `touched.json`
   3. the keys (09:19 US, 09:49 Canada, a new nightly slot for world + KY)
   4. the 2-fer line, only for the touched areas (chat 2's BOT E file `released-key.json` already does this for the US)

**Cost:** free (public repo), and only the touched areas are rebuilt. Storage: the world saved outlines stay light (Brandon: "old blocky is fine"), and they stay on the single-commit `world-bounds` branch.

**When:** after the Nov 1 monthly US run, so the first run doesn't fight the monthly one.

**What only Brandon can decide:** nothing. Chat 10 will do it unless he says otherwise.
