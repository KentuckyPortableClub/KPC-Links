# Hand-off: find each park's OWN page when POTA lists no link or a dead one (Fable, 23 Nov 2026 7:50 AM)

Owner 7:30 AM: "hand off for opus to finish the bot like you wanted". He had been told (another chat, same morning) that the job was not started, and that two questions were open: a web-search service, and where the links go. Both are answered below from rules already in force. Nothing here needs a new ruling from him.

## STATUS 23 Nov afternoon (Opus): FIRST FULL RUN DONE, L-list added
First 2f run: 4,441 parks, 164 sure, 117 unsure, 4,160 not found (2,673 nothing named on the agency sites, 1,486 busy or resting sites,
39 sites resting a day incl. fs.usda.gov, blm.gov, fws.gov, michigan.gov, nh.gov, parks.ky.gov). Biggest gaps: sites whose park pages
carry numbers (parks.ca.gov 253, Parks Canada 433, Ohio DNR 258, Oregon 160). Fix: rule L3b (park LIST pages from the front page),
KPC-Data 68d1b85c, PC copy sent and read back equal. Owner: upload the 1205 pack now; run 2f again TOMORROW (rests over).

## STATUS 23 Nov 8:30 AM (Opus): BUILT, waits for the owner
KPC-Data draft PR #186, KPC-Links draft PR #354, rule sheet L as built in mapping.md (on #354). Changes from the plan: the second
witness is a page point within 5 km of the PIN (the PC has no outlines) or the sister parks' list on a key-agency-table host; a page
point further off is unsure; the county witness and sitemaps are not used. A park whose sites were busy is looked for again next run.
PC files sent and read back equal; owner order: 2e, then 2f-FIND-OWN-PAGES.bat (NH trial, then all), then upload the newest pack;
after it, one by-hand `only: reader` run of kpc-official-links.yml.

## The job in one line

For parks whose page the reader cannot read (POTA lists no link, the link is dead, or the link is only the agency's home page), find the park's OWN page on its managing agency's own site, keep it only on a SURE match, and count what was found.

Size (KPC-Data `data/park-facts.json.gz`, page.kind 'none' / 'dead'): US 775 no link + 643 dead; Canada 481 + 323. Start with the US parks that are joined and not confirmed (577 + 181). Parks marked AGENCY_HOME_ONLY by the reader are the same job (not counted yet: count them first).

## What exists (checked 23 Nov; do not write a copy)

- **The page reader** (KPC-Data `.github/scripts/kpc_park_pages.py`, `_rules.py`, `_work.py`, `kpc_manners.py`). It already has every hard piece: robots.txt and slow pacing (`kpc_manners`), the ONE list of official sites (`official_host`; the link tool reads the same list through `kpc_link_ids.reader_official`), following a list page to one park's own link (`_park_link(links, pota_name, list_url)`, `_list_row`, `LIST_RULE`), the name test (`name_agreeing`: same / same-core / same-words, sibling guard), the own-page test, and the kept pages (`PageKeeper`, `page-reader\pages-kept` on the owner's PC, re-read offline with `--reextract`). It marks these parks today for a person: `NO_PAGE`, `LINK_DEAD`, `AGENCY_HOME_ONLY` (`PERSON_CODES`). It already reads the bot's address from `parkinfo-web.json` when POTA lists none (`kpc_park_pages.py`, where `web` is loaded).
- **The official-links bot** (KPC-Links `.github/workflows/kpc-official-links.yml`, monthly on the 9th, on the keep list; `kpc_link_harvest.py`, `kpc_map_finder.py`, `kpc_map_linkcheck.py`). It writes `data/parkinfo-web.json` ('web' / 'map' with '<kind>_by': 'bot: ...'; a person's value is never changed; 2,078 parks, 212 with a page, 20 of them from the bot). Its sources today: website fields of the map layers, the Park Service API, Recreation.gov, and official MAP files on agency park pages. It does not look for a park's own page. `kpc_state_links.py` shows bot links (`BOT_LINKS_GO = True` since 26 Oct).
- `.github/key-agency-table.json`: website host -> the managers whose land its parks sit on (141 hosts, learned from reviewed joins).

## The plan: two small pieces, each in the bot that already does that kind of work

**Piece A, the finder = a pass of the PAGE READER (KPC-Data).** Reason: a second crawler in `kpc_link_harvest.py` would copy the reader's manners, official-site list and name test. The reader runs on the owner's PC with those already in place, and its run sends no email.

1. Worklist: parks whose fact says NO_PAGE, LINK_DEAD or AGENCY_HOME_ONLY, in the order above.
2. Where to look, cheapest first:
   - **Kept pages (no request at all):** links already seen on kept official pages (list pages, menus) whose words name the park. Candidates only.
   - **Dead link:** walk up the dead address's own folders on the same site (3 requests at most) to a page that lists parks, then `_park_link` by name.
   - **Agency home only:** the home page is the list page: `_park_link` by name.
   - **No link:** the park's agency site is learned from its siblings (parks joined to the same layer, or the same state and kind, that have a working own page): their common parent folder is the agency's park list. One or two requests per AGENCY, kept, reused for every park of that agency. The host's sitemap, when robots.txt names one, is one more request per host.
   - Never a search engine (rule L3 below).
3. Every candidate is READ (one request) and judged by the reader's own tests. A sure page is taken as the park's page in that same run, so its name, address and points reach the park facts at once.
4. The fact carries `page.found` = {url, how, level: 'sure' | 'unsure', why}. The run report counts found / unsure / not found by state and by 'how'.
5. PC: one more step in the page-reader kit (a `--find-links` run after the read; no change to `RUN-OVERNIGHT.bat` while a run is going). The upload pack carries the facts as today.

**Piece B, the taker = one small source in the official-links bot (KPC-Links `kpc_link_harvest.py`).**

1. `from_reader(P, found)`: for a park whose park fact holds a SURE `page.found`, set 'web' = that page, 'web_by' = 'bot: page reader, agency site (<host>)'.
2. `main()` today skips 'web' when POTA has any link. Allow it when the park fact says that link is dead or is only the agency's home page. A person's value still wins.
3. A run mode `only: reader` that does this and nothing else: no web request at all. No new timer.
4. The whole found-and-unsure list goes on KPC-Data branch `tools-out` (`official-links/found-<date>.json`), never on main. Unsure ones reach chat 11 through the waiting room's existing intake; never write `data/waiting/in` by hand.

## Rule sheet L (DRAFT; copy the final sheet to mapping.md once chat 8 has tried to break it)

1. **Counts (SURE):** a page on the managing agency's own official site (the reader's official list) + the reader's own-page test passes (one park per page) + the page's own name agrees with POTA's as 'same' or 'same-core' + no other park in the state claims that page + one of: the page gives a point inside the park's joined outline (or within 5 km of POTA's pin when the park has no outline), or the county the page names holds the pin, or the site is the one the park's own land layer belongs to (`key-agency-table.json`).
2. **Does not count:** a list page, the agency's home page, a PDF, a page of a sibling unit (a state forest for a state park of the same name), the same name in another state, Wikipedia, tourism, trail, map-app and reservation sites, any site not on the official list. 'Same words, another kind' is never sure by itself.
3. **Sources, best first:** kept pages; the agency's own site (list page, sitemap); the Park Service and Recreation.gov lists the bot already reads. NO web-search service: "no other keyed API without his word" stands, and no search page is scraped. What is not found is counted, and that count is what goes to the owner if a search service is ever worth asking for.
4. **Unsure:** not written to `parkinfo-web.json`, not read as the park's page, listed with its reason, sent to the waiting room.
5. **What people see:** a sure link shows as the park's official page where bot links show today (bot-tagged; a person's link wins). POTA's own link stays on file as POTA's. No new page, menu or post.
6. **Examples (invented):** (a) Heron Marsh State Park, no POTA link; its siblings link to parks.zz.example.gov/parks/..., the list there has "Heron Marsh State Park", the page's address sits in the outline = SURE. (b) Dead link .../parks/red-notch.html; the folder above lists "Red Notch State Park" at a new address = SURE. (c) "Otter Lake" is both a state park and a state forest page = the forest page is refused (sibling). (d) Only a county tourism page names the park = not counted. (e) Two POTA parks' names both fit one page = UNSURE for both. (f) A city park with no siblings and no agency site learned = not found, counted.

Robots.txt always wins; a refusal stops that site for the run; never go round a bot check; nothing about a person is read.

## Not part of this job, but seen (for HQ, do not fix silently)

`kpc_link_harvest.py` `from_layers` asks the agency map servers itself for website fields. That is older than the 20 Nov design (only the keeper fetches from agency servers). This job neither runs it nor changes it. Reading those fields from the keeper's saved copies instead is its own small job, on the owner's word.

## Order of work, tests, done

1. Count first (no build): how many of the worklist parks have a sibling-learned agency site, and how many already have a candidate in the kept pages (the owner's PC, offline). If almost none, stop and tell him the number.
2. Piece A on a branch of KPC-Data with a test that fails without it (invented pages: the six examples above), Python 3.12 while working, 3.12 and 3.13 once before the merge. Say whether `kpc_manners` changed (it should not).
3. Try it on ONE state on the PC from kept pages before any wide run.
4. Piece B on a branch of KPC-Links with its test. No key rule file is touched, so no rules number moves; say so in the PR.
5. One by-hand `only: reader` run after the park facts hold the found pages. That is one email. No rerun to look.
6. DONE = a count the owner can check (found sure / unsure / not found, by state), the list on `tools-out`, and the reader's next report showing those parks read on their own page. One ledger line with that proof.

Standing rules as always: no key build, no workflow turned on, no new timer; draft PRs; no AI or co-author lines (author KPC owner); counts only in public files.
