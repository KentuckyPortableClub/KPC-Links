# Site scope check + health, Oct 29 ~9:40 AM CDT (chat 11, independent of chats 1/3/5)
How: the live site is not reachable from this workspace (proxy), so the check ran against the code deployed on main (deploy fb2be003d 13:44Z = success) served locally, with every KPC-Data fetch answered from the KPC-Data clone and all other outside hosts blocked; Playwright, GUEST (navigator.webdriver = false) and MEMBER, 390 px and 1280 px = 4 views x 18 pages = 72 loads. The site-health + link check on the LIVE site runs on the runner: kpc-bot-health.yml 'full' dispatched once (run 40885942620, in progress at write time; result next inbox).
Limit: non-KY park LOOKUPS (park sheet, Kit) need the POTA API, which is outside; locally the TN / CA / Ontario sheets stop at 'Could not find US-0533', so for those two pages the non-KY verdict is from the CODE (the Oct 29 diffs) plus the KY page, not from a rendered non-KY card.

## Scope: dropped features outside Kentucky (closures, hours/fees, camping)
| page | KY park | non-KY (TN US-0533, CA US-0014, ON CA-0138) | guest = member? | verdict |
|---|---|---|---|---|
| Park sheet | closures 3, hours 2, fees 3, campgrounds 3 shown (right) | code: campfed read only when st === 'KY'; stay list says 'Campground details are shown for Kentucky parks only'; rendered sheets empty (lookup outside) | yes | PASS for camping; **FAIL for closures text**: `kpc-closures.js html()` still renders a closures panel for non-KY parks: for AR CA CO FL GA MO MT NC NJ OR WI it says 'Checked: <agency> (every 6 hours)' from the 11 sources still listed in data/alerts/us-parks.json (bot OFF, ok:false = a false claim); for every other state 'We do not watch closures in <state> yet'. Both are closure info outside KY. |
| Activation Kit | KY: closures 2, campground 3 (right) | 'Could not find US-0533' locally; code: HEADS UP conds only when P.ky; campground block says KY-only | yes | PASS (by code) |
| US trip planner (?q=TN park) | — | only UI copy ('⛺ Campgrounds & shelters' legend); no federal camps outside KY (code line 237) | yes | PASS; wording 'tap a dot for ... campgrounds' is a leftover label |
| Activators Lounge | — | no data hits; tab 'Campgrounds & Cabins: ... state by state' | yes | PASS; **wording leftover** ('state by state' on a KY-only feature) |
| Campgrounds page (?state=TN) | shows Kentucky | picker hidden, TN param ignored, Kentucky list shown; the 50-state <select> is still in the DOM (hidden) | yes | PASS; **wording leftover**: subtitle 'in every US state' |
| Map Coverage (members) | header: STATE / PARKS / WITH A MAP / MISSING / PIN ONLY / % COMPLETE: no hours / fees / campground columns | same | guest = door | PASS (legend sentence still lists 'hours, fees ... campground' as columns a park 'could have': wording) |
| Overlap Finder (members) | loads; reads data/fers/US-KY.json + missing-ky.json | n/a | guest = door | PASS for scope; QUESTION for HQ: those files are committed as 'hidden data' in every 2-fer line commit; if this page reads them live, they are not hidden |
| Home, Park notes US | 'camping' / 'hours' only in prose | — | yes | PASS |
Closures DATA: kpc-conditions.json uc- items 0 (chat 5 cleared 177; KY pa-/hc- 40 kept); data/alerts/us-parks.json items 0, sources 11 (the leftover above).

## Site health (local, 72 loads)
- Console/page errors: 0 on every page except Overlap Finder's local 404s for KPC-Data paths (a local-serving artefact: on github.io ../KPC-Data resolves to the data site).
- Sideways scroll at 390 px: none on any page. Header/menu: present on every page (collapsed 'See More' on phones); footer: every page.
- Notices: info notice on every tool page opened (park sheet, Kit, planner, Lounge, Campgrounds, Park notes, Map Coverage for members); 2-fer notice on park sheet, Kit, planner, Lounge. Home and Campgrounds carry no 2-fer notice (they mention no 2-fers: fine).
- Member lock: guests get the door on Map Coverage and Overlap Finder; park sheet, Kit, planner, Lounge, Campgrounds open to guests (as listed PUBLIC).
- Links: the runner's link check (run 40885942620) reports next inbox.

## Leftovers (one line each, sent)
1. chat 3 (owns kpc-closures.js) + chat 5 (owns us-parks.json): for a non-KY park the closures panel must render NOTHING (`if (!r.ky) return ''`), and the 11 agency entries in data/alerts/us-parks.json 'sources' go (or the panel ignores sources with ok:false). Today a California park sheet says 'Checked: California State Parks (every 6 hours)'.
2. chat 3: wording: Campgrounds page subtitle 'in every US state' -> 'in Kentucky'; Lounge tab line 'state by state'; planner legend 'campgrounds, picnic shelters' (non-KY shows none).
3. HQ: Overlap Finder reads data/fers/US-KY.json live: hidden or not?
