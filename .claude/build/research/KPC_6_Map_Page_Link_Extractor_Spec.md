# KPC AGENCY MAP-PAGE LINK EXTRACTOR: build spec for an outside coding agent (Fable reviews afterwards)

## Why
Most park agencies keep every park's map / brochure on ONE page ('Maps & brochures', 'Area maps', 'Hunting maps', a document library). Given that page, this tool finds the right PDF / map for each of the agency's parks automatically, filling the club's official-documents files far faster than park-by-park research.

## Input
`agency_pages.json`: `[{agency, state_or_prov, index_url, park_refs: ["US-1234", …]}]` + `parks.json` `{ref: {name, type, lat, lon, alt_names: []}}` (POTA name, current POTA name, agency's own name if known).

## What it does, per agency page (batch; one failure never stops the run)
1. Open the index page (static HTML first; a headless browser (Playwright, Chromium) only if the links are built by script). Follow pagination and sub-pages on the SAME host, max depth 2.
2. Collect candidate links: PDFs, images, map pages, KMZ; keep the link text, nearby headings, the file name and the URL path.
3. **Match each park** to candidates by name: normalise (case, accents, punctuation; expand / drop type words SP, SHS, SRA, WMA, NWR, CA, PP, 'State Park', 'Wildlife Management Area'…), then score (token-set ratio on link text + file name + heading). Accept ≥ 0.9; 0.75–0.9 = POSSIBLE; else none. Never assign one file to more than 3 parks (a shared statewide file is not a park's map: report it as SHARED).
4. For each accepted PDF: HEAD / GET it (must open, must be a PDF / image), read page 1-2 text if possible to confirm the park name appears; record the file's Last-Modified / PDF creation date.
5. Output `docs_found.json`: `{ref: {page_url, map_url, kind PDF / IMAGE / MAP PAGE, map_date, match_score, status OK / POSSIBLE / SHARED / NONE, why}}` + `report.csv`.

## Rules
- Only the official agency's own pages and files (the index URL's host and the agency's own document hosts).
- Never Google, OpenStreetMap, AllTrails, TripAdvisor, Wikipedia; respect robots.txt; one request at a time per host, User-Agent naming the club, back-off.
- Headless on GitHub Actions, ≤ 55 min per job, chunk + resume.
- Decides nothing final: POSSIBLE rows go to a person.

## Tech
Python 3.11; requests, beautifulsoup4, rapidfuzz, pypdf (text check), playwright (only when needed).

## Test
5 agencies: Kentucky Fish & Wildlife WMA maps, New York DEC WMA maps, a state parks 'park maps' page, a Forest Service unit's maps page, a Canadian conservation authority. Report matched / possible / shared / none.

## Deliver
`kpc_map_links.py` (`--agencies agency_pages.json`, `--resume`), `requirements.txt`, README, the test report. Not wired: the club's bot chat does that after Fable's review.
