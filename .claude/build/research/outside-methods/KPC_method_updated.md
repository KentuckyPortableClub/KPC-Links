# How to fill park Hours / Fees / Closures from official sources (KPC method)

Written from the Oct 31, 2026 US (13,083 parks) and Canada (5,918 parks) builds.

## 1. Ground rules
- Fill only the target columns; never edit identity columns (park name, ID, column F link, POTA link). Never reorder, delete or rename rows, columns or sheets.
- Official agency/government or operator pages only. No Google results, TripAdvisor, AllTrails, Yelp, blogs, Wikipedia, directories or booking resellers. Don't use search snippets as a source.
- Every URL written must open. Never guess a link.
- Copy text word for word, in the original language. Never turn prices into a range yourself (if the agency writes a range, copy it).
- Standard wording: "not stated on the agency page", "no fee", "open all year, no hours stated".
- Status: FOUND (hours, fees and closures links) / PARTLY / NOT FOUND (pages checked, nothing stated) / NO AGENCY PAGE. Blocked sites are left blank and logged, never marked NOT FOUND.

## 2. Work agency by agency (biggest win)
- Group rows by agency/domain first. One agency-wide fees page, passes page or alerts page often covers hundreds of parks at once. Write "agency-wide page" in Notes.
- Do the biggest agencies first, then the long tail of one-off sites.

## 3. Fix bad source links, don't edit them
- Many column F links were dead, moved, mistyped (missing ".com", "idaho.goc") or pointed to the wrong park.
- Find the right page on the same official site and put it in Notes: "Column F link wrong/dead; correct official page: <URL>". Log every fix to a CSV. Never edit column F.
- Check that the page title matches the park before using it.

## 4. Reading sites in order of escalation
1. A plain script fetch (fast, parallel, cached).
2. The WebFetch tool for sites that block scripts (keep a list of domains that only work this way).
3. A browser pass for whatever is left: write a targets CSV (row, park, official start URL, rows sharing the page), have the browser agent copy text and record address-bar URLs into a results CSV, then merge it.
4. Still blocked? Leave blank, log to blocked_rows.csv with domain and reason, retry at the end.
- Never spoof user agents, never click through certificate warnings, never sign in, never get around JavaScript or robot checks.

## 5. Hidden data sources that helped
- National Park Service hours pages fill hours with scripts. Each park has a public, keyless data file at https://www.nps.gov/<code>/structured_data_<code>.json, and its "operatingHours" text gave real hours for many parks.
- Old Forest Service PDF links (404) usually have a current fs.usda.gov recreation page.
- Heritage/historic designation registers aren't visitor pages. Find the actual operator (Parks Canada, a province, a city or the museum society) and use its own hours and rates page.
- Some parks have changed hands (e.g. a state handing a park to a city). Follow the current owner's page.

## 6. Quality checks
- Checkpoint every ~200 rows: save, copy to a checkpoint file, log progress.
- Before each delivery: open every URL, compare identity columns to the original data (0 mismatches), spot-check random rows.
- Watch for page boilerplate copied into Hours cells, prices from the wrong site, and generic lines passed off as park-specific (put those in Notes only).

## 7. Deliverables
- The filled workbook, the column F fixes CSV, and blocked_rows.csv (domain, row, reason) so anyone can retry later.

## 8. Break the puzzle before saying NOT FOUND (from the Oct 31 Canada "Hard Look" outline run)
A large share of "missing" rows weren't missing at all; the row itself was wrong. Check these three things on every hard row:
- **Wrong pin.** Typos are common: one digit in the latitude or longitude (Fort Providence 62 instead of 61, 111 km off; Long Lake Bog -65.96 instead of -64.94, 81 km off), pins at 0,0, pins copied from a neighbouring park, and pins geocoded to the nearest town instead of the site (Erebus/Terror at Gjoa Haven, about 119 km off). Some BC pins were 137–823 km off.
- **The POTA API can't catch a wrong pin.** Its coordinates always equal the sheet pin. Settle pins from official sources instead: the agency's own address, the Directory of Federal Heritage Designations, historicplaces.ca (PlaceLatitude/PlaceLongitude meta tags, sometimes rounded), tourism-board listing JSON-LD, or the agency's own point layer.
- **Wrong or old name.** Parks get renamed (Indigenous names in BC: Colony Farm became ƛ̓éxətəm; Mount Douglas became Pkols), merged (five Saskatchewan rec sites folded into Porcupine Hills PP), or carry a different official name (Grassy Island Fort is now Canso Islands; Colony of Avalon is listed federally as the "Old Sir David Kirke Site"). Try French/English/Indigenous variants and keyword LIKE searches, not just exact names.
- **Wrong kind of place.** A "park" may really be a building, lighthouse, ship, dam, station, campground lot, or a biosphere or Ramsar designation with no land boundary. Look for the source that fits the real kind (building footprints, heritage registers, federal property).
- **Changed hands or delisted.** Parks get cancelled or transferred (Sylvan Lake PP went to the town in 2018; Alberta delisted several areas in January 2024; Saskatchewan repealed many rec sites in 2021). Check regulations and news releases, then follow the new owner's site. This matters for hours and fees too: the current operator's page is the right one.
- **Same name, different place.** Beware look-alike matches (Denys Fort in Shippagan vs the "Nicholas Denys Site" in Bathurst; a "Longwoods" conservation area 30 km from Battle Hill). Always check the distance as well as the name.

## 9. Don't trust earlier "no hit" results blindly
- Earlier automated checks had false negatives: a pin sitting on the road just outside the polygon, a name stored in an odd field (Yukon campgrounds keep the name in REMARKS), or a match rule that was too strict (Parks Canada trails: match on the section name, not just the word "trail"). Re-test a "tried" source when there's a clear reason, and say why in Notes.
- Log blocked sources (TLS failures, Cloudflare challenges, token-only services, servers that only answer curl) as BLOCKED with the reason, never as NOT FOUND.
- Never use an access token you find embedded in a public web map's config. Treat that service as not public.

## 10. Notes standard (every row)
Each Notes cell should say, in plain words:
1. **Where you looked:** each source and what it gave (hit, no hit, points only, blocked).
2. **What you solved:** "PIN OFF: real lat,lon, distance, source", "NAME SOLVED: agency calls it X", "WRONG KIND: it's a lighthouse".
3. **Why this record is this park:** name match, distance, size, the official page that confirms it.
4. **Confidence:** sure / likely / weak, plus what a checker should double-check.

Keep a shared, dated findings log of reusable lessons (source quirks, false negatives, renames) so the next run starts smarter.

## 11. Running many workers at once
- Split rows by region or agency, about 150–230 rows per worker. Eight parallel workers was the sweet spot; past that they hit the same government servers and get rate-limited.
- Each worker writes its own results file and saves every 25–50 rows, so an interrupted worker can resume where it stopped.
- Partners on the same region share a "layers found" file and skip rows the other already has.
- Run a first pass on everything, then a second pass on only the NOT FOUND and weak rows with every trick learned so far. The second pass often solves half or more of what's left.
- Pass a good trick sideways as soon as it's found. For example, the Quebec cadastre plus the 2026 property-roll use codes solved about 130 Quebec rows once both workers had it.
