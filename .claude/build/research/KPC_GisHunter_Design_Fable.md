# GIS HUNTER: the bot that searches the Fable lists (US + Canada) for official GIS layers
**Design note for Opus (chat 10) — Fable, Oct 29 2026 9:40 PM CDT. Brandon 9:27 PM: "leave a note for opus on how to build or redesign a bot to search the Fable list and Canada Fable list for gis". RULES FIRST is satisfied: the rule sheet is Rule G (R-G1..R-G11, P-1..P-5, R-GC1..) in notes/mapping.md; this bot only automates R-G7 steps 2-3 (find the official record + the official layer) and P-2 / P-4 / P-5. It DECIDES nothing: it writes candidates with evidence; chat 11 says YES / NO; chat 2 writes the key. Nothing it does touches the site (freeze); everything lands in KPC-Data.**

## 0. Redesign, not a new bot
We already have the park detective's GAP FILLER (kpc_detective_bot.py job A: per park, ~8 requests, layers → agency ArcGIS → portal → PAD-US). It is the right idea with the wrong shape: it walks parks one at a time (one point query per layer per park = thousands of requests), reads pages before polygons, and writes its own review files nobody is wired to. Rebuild it as **kpc_gis_hunter.py** with these changes, and retire job A of the detective (job B, the questions, stays).

## 1. Input = the two Fable pools, nothing else
- US: `KPC-Links .claude/build/research/missing-after-key.json` (keys PIN INSIDE / NOTHING NEAR / LIKELY) + the R-G10 tags in `KPC-Links data/us-key/why-not.json` (`parks[ref].why` = name-mismatch / no-layer / needs-parcel / picture-map-only / pin-doubt / private).
- Canada: `KPC-Links .claude/build/research/missing-after-key-canada.json` (PIN INSIDE / CHECK / NOTHING NEAR).
- Pins + names: `data/parkinfo/US-XX.json`, `data/canada.json` (POTA pin; never moved, R-G7).
- Skip: a ref already outlined in the current key; a ref with a chat 11 answer in `data/waiting/questions/key-pieces.json`; `private` and `picture-map-only` tags (those are R-G9 / P-5 work, not a layer hunt).
- Order (Brandon 3:15 PM): states from the FEWEST open parks up; inside a state, P-4: group refs by agency words in the name (… State Park / WMA / State Forest / Historic Site / National Wildlife Refuge / BLM / city / county) and work a group at a time.

## 2. Step A = POLYGONS BEFORE PAGES (P-2), one request per state per layer
For every state (or province) with open refs, take EVERY layer we already know: `data/state-gis.json` (states[XX], portals), `data/us-key/layers.json`, `data/ca-key/layers.json`, the national layers (PAD-US fee + designation, FWS, USFS, NPS, BLM, CPCAD in Canada), `data/trails-layers.json`. For each layer run **one** `query` with `geometry` = a multipoint of ALL the state's open pins (esriGeometryMultipoint, `spatialRel=esriSpatialRelIntersects`, `outFields=*`, `returnGeometry=false`), then one more call per hit to fetch the hit polygon's envelope and area. That replaces thousands of per-park calls with ~5-15 per state. Where a server refuses multipoint (some old MapServers), fall back to per-park point queries, 2 s apart, cap 40 per layer per run.
Judge each hit with the house rule, written down, never loosened:
- **SURE** = pin inside + name words match (kpc_us_key.py's name_ok / the R-G8 shared-words rules) + similar size when both sizes are known → row for chat 11 as "candidate, SURE".
- **NAME MISMATCH** = pin inside, size plausible, names share no word → row "candidate, name mismatch: both names" (this is the biggest group: ID 106, NV 76, UT 251, WY 57 are mostly BLM/state names that differ from POTA's; R-G2 + the BLM name batch HQ asked chat 2 for).
- **DIFFERENT LAND** = pin inside a polygon whose kind contradicts the park (a county, a hunting unit, a watershed) → tag `inside-other` with the record, for R-G7 step 4 (ownership) later. Never offered as an outline.
- **NO HIT** anywhere → Step B.

## 3. Step B = find a layer we do not have yet (the real "GIS search"), per AGENCY not per park
Only for refs with no hit in A. Group by agency (P-4). Per agency, in Rule G research order, stop at the first official layer that answers:
1. **State / provincial open-data portal** (`state-gis.json` portals + ArcGIS Hub search API `/api/v3/datasets?q=<agency words>&filter[source]=…` + Socrata/CKAN catalog search as the harvester does): publishers that read like the agency itself only.
2. **The agency's own ArcGIS**: `arcgis.com/sharing/rest/search?q=owner:<org> type:"Feature Service"` for the agency's org id (learned once per agency and cached in `data/gis-hunter/agencies.json`); the agency's ArcGIS Server root `…/arcgis/rest/services?f=json` folder walk (max 3 levels, cap 60 layers), picking layers whose name / fields carry park words (name_ok on the layer name, field names like NAME / UNIT / PARK / PROP).
3. **The agency page the POTA record links** (parkinfo-web.json / parkinfo link) read in the headless browser (look-up bot code, `kind: page`): collect map-service URLs embedded in it (`/arcgis/rest/services/`, `FeatureServer`, `MapServer`, `.geojson`, `wfs?`, `ogc/features`). A page link is a LEAD, never a boundary.
4. **County / city GIS** (P-5, R-GC4) ONLY when the park's name says city / county / regional / MRC / conservation authority: one lookup per body, the county from the address file (`KPC_FableList_Addresses.json`) — reuse chat 9's parcel `kind` for owner + parcel id (R-G7 step 4b) and write the parcel row, not a boundary.
Every new layer found is **probed once** (chat 9's kpc_adds_probe.layer: answers, geometry, name field, count, licence, dates) and **appended to `data/intake/queue.json`** (`from: 'gis-hunter'`, `closes: [refs]`), so the existing intake → READY → chat 9 approval path does the rest. The hunter never writes `state-gis.json` or a key itself.

## 4. Output = rows people already read, no new review file
- **Per ref** → one line appended to the Fable file WORK LOG BY STATE (`KPC_MissingBoundaries_ForFable_desk.md` / `…Canada…`), the format already there: `| ref | park | step | what was found (layer url, record name, acres, pin inside?) | result (candidate SURE / name mismatch / inside-other / no layer: what was tried) | date | by: gis-hunter |`. Same row to `data/gis-hunter/<area>.json` for machines. Add rows, never delete others' (HQ 3:23 PM).
- **Candidates for a person** → `data/waiting/questions/key-pieces.json` (kpc_key_questions.py format: park, record, acres, why, record link, POTA link, question "Is this piece part of that park on the agency's own map? YES / NO"), so chat 11 answers in ONE place and chat 2 rechecks (G-4). Mark `source: 'gis-hunter'`.
- **New layers** → intake queue (above). **Parcel answers** → the P-3 table in the Fable file.
- **Nothing found** → the why-not tag stays, plus `tried: [...]` so nobody repeats the search; a "no layer" with 0 tried steps is a bug, fail loudly in the COUNT line.
- COUNT line per state: `open N / step A hits: sure S, mismatch M, inside-other O / step B: layers found L (queued), parcel P / still nothing Z (tried steps)`. 'grade me' line via kpc_status.py for chat 11.

## 5. Manners, size, pace
kpc_manners.py (robots.txt; ArcGIS REST + the two keyed /api paths only; 2 s per host; three strikes = a day's rest). Cache every layer answer per run (`/tmp`), never store geometry (storage rule): envelopes + areas only. Workflow `kpc-gis-hunter.yml` in KPC-Data, dispatch only (areas input, chunks, chain), never red, saves `data/gis-hunter` + `data/intake` + `data/waiting/questions` with kpc_push_data.sh; writes to the KPC-Links Fable file need the look-up-bot lesson (no cross-repo key): write the WORK LOG rows to `data/gis-hunter/worklog-<area>.md` and let chats 3 / 8 paste them, or HQ copies them in its pass. Test on ONE small state first (IA 1, RI 1, DE 4), then one province (PE 7), then chain. Expect: step A alone should move most `name-mismatch` refs (ID/NV/UT/WY) into candidate rows in one run per state.

## 6. What NOT to build
- No tracing, no drawing, no key edits, no pin moves (R-G7 step 5-7 belong to chat 2 / chat 11).
- No picture-map lines (R-G9 is a separate tool, Brandon's GO first).
- No Google / third-party / community shapes; no web search before the portal + agency steps.
- No new rule: a question Rule G does not answer = a numbered grey area in REPORT TO HQ, not a guess.

## 7. Acceptance test (chat 11 grades)
Run on IA + RI + DE + PE. PASS = every candidate row has pin-inside + a named record + a link; a random 10 candidates are 9+ right on the agency's own map; no row says "no layer" with an empty `tried`; no request to a host outside the manners rules; the intake queue gained only layers that answer; the Fable file rows are in the WORK LOG format.
