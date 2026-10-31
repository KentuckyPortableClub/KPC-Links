# HOW THE KENTUCKY PORTABLE CLUB WORKS: read this before any KPC build

KPC is a ham radio club. Its website and bots map POTA (Parks on the Air) parks across the US, Canada and the world, and find "2-fers":
spots where two POTA parks' official boundaries overlap, so one radio activation counts for both. Members drive to these spots.
**A wrong outline or a wrong 2-fer sends a ham to the wrong place.** Getting it right beats getting it fast.

## Who does what
- **The bots** (GitHub Actions, Python, headless) gather data and answer questions.
  They NEVER put anything live by themselves: every result goes into the **waiting room**.
- **Chat 11** (the checker) grades the waiting room (bar: A + B ≥ 90% on a 10-12 item sample) and says YES / NO / NOT SURE.
  Only a YES goes live.
- **Chat 2** owns outlines and 2-fers. **Chat 10** wires the bots. **Fable** (a senior reviewer) reviews and fixes outside code before it is wired.
- **Brandon** (the club owner, KZ4CP) rules on grey areas.
- Your tool is a HELPER. It writes reports and questions. **It never edits the club's live files**:
  - the keys (`us-key`, `ca-key`, `world-key`, `ky-answer-key.json`);
  - the outlines (`canada-bounds`, `world-bounds`);
  - the 2-fers (`data/fers`);
  - documents, cards, anything on the site.

## The rules your code must follow
1. **Official sources only:** the managing agency's own GIS layer, a national open-data portal, or a government basemap.
   - NEVER OpenStreetMap, Google (Maps, My Maps, tiles), AllTrails, Protected Planet / WDPA shapes, blogs or Wikipedia geometry.
   - Protected Planet's list may be used only as a phone book (to learn a park's official name), never for shapes.
   - Parcel (county land-owner) outlines are allowed only where the club says so, graded "Approximate".
2. **POTA's pins are never moved.** A pin outside its outline is only labelled.
3. **One park = where the designation legally applies.** National forests and the like = the agency-owned land inside the proclamation line, never the proclamation line itself. A park must be public and open.
4. **2-fer rules (R0-R10, short form):**
   - Two POTA-numbered parks only. Land with no POTA number never pairs.
   - Real layering (one designation on top of another on the same land) counts; parks that only touch side by side do not.
   - The overlap must be at least 50 yards across (R9; smaller = flagged "small overlap").
   - **R5 land trails:** the trail park = within 100 ft (30.48 m) of the official trail LINE.
   - **R5 water trails:** the water trail = within 100 ft of the **WATER'S EDGE** (the river bank) of the river it follows, NOT of a centre line.
     An earlier outside check measured river rows from the line / the spot's centre and wrongly said "NOT THERE": don't repeat that.
   - **R6:** wild and scenic river corridors = the official corridor polygon where one exists, else the river rule.
   - **R7:** water-only overlaps are listed apart.
   - Same land under two park numbers = shown as "same land, two park numbers", not an ordinary 2-fer.
   - **NOT SURE = kept out.** Never say parks DO overlap: the site says boundaries "may overlap".
5. **Detail:**
   - Outlines are saved simplified to 3 m at most (never over 5 m in the US / Canada).
   - Very big world parks may be capped coarser, with their detail labelled.
   - 2-fers are always worked out from the full live detail, never from the saved simplified copy.
6. **Grades on an outline:**
   - official;
   - Approximate (parcel, EU compilation);
   - approximate (picture map) / approximate (unofficial map);
   - pin only.
   - Never a 2-fer from a traced or unofficial outline.
7. **Order of work:** Kentucky first, then the rest of the US and Canada, then the rest of North America (Mexico, Central America, Caribbean, Greenland), then the world's top-activation countries.
8. **Practice data:** use the call sign K4TEST in any example (never a real call).
9. **Privacy:** no names or addresses of private people. A parcel owner's name never leaves the bot's memory.

## How the code must behave
- Python 3.11+, one main file, `requirements.txt`, `README.md`, `TEST_REPORT.md`, `tests/` (offline unit tests with made-up shapes).
- **Headless on GitHub Actions:**
  - `--max-minutes 50` stops cleanly, and `--resume` carries on, so no job passes 55 minutes;
  - exit 0 = done, 3 = "not finished, run again with --resume", 2 = bad input.
- **One failure never stops a batch.** Log the reason ("SOURCE DOWN", "CAN'T TELL") and go on; retry those next run.
- **Polite:**
  - at most 1 request per second per host;
  - User-Agent `KPC-<tool> (https://github.com/KentuckyPortableClub)`;
  - back off on 429 / 5xx;
  - obey robots.txt for web pages;
  - cache what you read (with a date).
- **Small outputs.** The club's data repo has a size limit, so:
  - keep outputs as JSON / CSV reports;
  - big files (pictures, geometries) go in a folder the club can put on a throwaway branch;
  - never a picture in the main report.
- **Plain words.** The club owner is a ham, not a developer. Every `why` is one plain sentence; summaries are short.
- **No API keys,** unless the spec names one.
- Deliver as a zip. **Do not wire anything:** the club's bot chat does that after Fable's review.

## The club's files (samples in `sample-data/`)
- **`us-key/US-XX.json`:** `parks` {ref: {n name, t type, g grade, src [sources], m [[record id, record name, acres, why matched], …], ac acres, c [...] }}.
  `src` 'PAD-US' = the USGS PAD-US layer. Other record ids go with `us-key/layers.json` {key: [layer query URL, name field, description]}.
- **`ky-answer-key.json`:** Kentucky's own key (agency layers per park).
- **`ca-key/CA-XX.json`:** same shape; integer ids = CPCAD (Environment Canada) OBJECTIDs.
- **`canada-bounds/CA-NNNN.json`, `world-bounds/<country>/N.json`:** saved simplified outlines (GeoJSON).
- **`fers/US-XX.json`:** 2-fer rows: `spots[]` with `refs`, `kind` (area / trail / river / water-only / same land), `center` [lat, lon], `shape`, `lines`, `acres`, `wide_m`, `status` (dropped / merged rows are not live).
- **`trails/<ref>.json`:** the official trail / river lines the club saved.
- **`parkinfo/US-XX.json`:** `parks` {ref: [name, website, type, access, access, lat, lon, …]}: the POTA pin is `lat, lon`.
- **POTA's own page:** `https://api.pota.app/park/<ref>` (current name, pin, website). No key; cache 30 days.
