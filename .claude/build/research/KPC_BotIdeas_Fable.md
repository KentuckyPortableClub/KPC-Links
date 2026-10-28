# KPC BOT IDEAS (Fable, chat 10 'bot workshop', Oct 28 2026 ~2:45 AM CDT) — HQ job 3: DREAM BIG

Ten bots that would pay off most for KPC's members and data, each with what it does, the payoff, the effort, the risks
(email noise, server manners, storage, rules-first needed?), then my top 3 and what I built tonight. Every one obeys the house
rules: own script + workflow + folder in KPC-Data, robots.txt (ArcGIS REST API excepted), 1 request / 2 s per host, three
strikes = a day's rest, metadata + page text only, resumable 55-minute chunks, one commit each, email only for a real break,
nothing reaches a member until Brandon's GO. "Decides nothing" = review lists or facts with sources; "RULES FIRST" = it
chooses what members see, so a rule sheet, chat 8's break and Brandon's ruling come first.

| # | Bot | Decides? | Payoff | Effort |
|---|---|---|---|---|
| 1 | Cell Coverage Atlas (FCC) | no (facts) | very high (self-spotting) | medium; needs a free FCC token |
| 2 | Hours, Fees & Permits bot | no (facts) | high (every card) | medium — **BUILT tonight** |
| 3 | POTA Activity Pulse | no (facts) | high (hunters + activators) | low (rides the leaders cache) |
| 4 | Weather & Fire Watch | yes | high (safety) | low-medium — RULES FIRST |
| 5 | Access Pin Verifier | no (review list) | high (maps right without people) | medium |
| 6 | Elevation & Take-off Atlas | no (facts) | medium (VHF, antennas) | medium |
| 7 | Line-Park Freshness Watch | no (review list) | medium (trail/river 2-fers) | medium |
| 8 | 2-fer Field Guide Builder | uses ruled data | high (members' favourite) | medium; GO per guide |
| 9 | Hunting Season Calendar | partly (notes feed closures) | high (safety, hunt closures) | high — RULES FIRST |
| 10 | Field-Confirmation Loop | yes (what 'confirmed' means) | high (maps right with people) | medium — RULES FIRST |

## 1. CELL COVERAGE ATLAS (the FCC National Broadband Map, official)
- **What:** for every US park pin, every access point and every campground, read the FCC Broadband Data Collection's MOBILE coverage (4G/5G, by carrier, outdoor stationary) at that spot from the FCC's own API; store one small record per point (carrier → yes/no/edge, data vintage); refresh twice a year when the FCC publishes a new vintage. Canada later from ISED's coverage data if its terms allow.
- **Payoff:** "will I have a signal to spot myself / log?" is the first question every activator asks about a park nobody has been to; hunters get "why nobody spots from there". It pays off for years and needs no person.
- **Effort:** medium. The FCC BDC public API needs a free token (Brandon registers once at the FCC's BDC site; the token goes in Actions secrets, never in chat). ~25,000 points × 1 request = 14 hours at 1 request / 2 s, twice a year, chunked.
- **Risks:** server manners (FCC's API has a documented rate limit: we stay under it); storage small (~1 MB per state simplified); no email; no rule sheet (facts with the FCC's vintage date), but the CARD WORDING ("FCC says: Verizon 4G yes, AT&T edge") goes to chat 3 after Brandon's GO with the short info line.

## 2. HOURS, FEES & PERMITS BOT — BUILT (see the end)
- **What:** for every US + Canada park with an official page, read the agency's own page (and its official map PDF's first page) for OPEN HOURS (daylight to dark, gate times, days closed, seasonal hours), ENTRY / PARKING FEES and PASSES, and PERMITS NEEDED (a WMA user permit, a day-use permit, a drawn permit), each fact quoted with its source line and date; Kentucky's hand-checked kpc-ky-hours.json is the answer key (Otter Creek's Wed–Sun, Buckley's $8, Peabody's permit).
- **Payoff:** hours and fees are the second question after "where do I park"; Otter Creek taught us a wrong hour sends people to a locked gate; permits keep members legal (POTA: permit land counts, with a note).
- **Effort:** medium; reuses the truth checker's page reading and manners. ~19,000 parks, 1–2 pages each: ~24 hours once, then quarterly (pages checked < 90 days ago are skipped).
- **Risks:** text parsing gets some hours wrong (so: quote, never paraphrase; chat 8 grades a sample; cards after Brandon's GO); no email; storage ~2 MB; no rule sheet needed for the gathering (facts), the SHOWING uses the notices and Sheet D's '🎫 Permit needed' note wording.

## 3. POTA ACTIVITY PULSE
- **What:** per park: activations ever, this year, last activation date, unique activators, QSOs — read from the same POTA activation lists the state-leaders bot already caches (one shared cache, no second read), plus a weekly diff: NEVER ACTIVATED parks per state, "quiet for 2+ years", "newly activated this week", busiest 25 per state.
- **Payoff:** activators love "unactivated parks near me" (a first activation is a trophy); hunters love "which parks are live this month"; our own bots get a better BUSIEST-FIRST order for checking outlines (today it is a one-off count).
- **Effort:** low: a reader of the leaders bot's cache (same cache key) + a weekly summary file per state; no new POTA requests.
- **Risks:** POTA's API is not formally public (the club already reads it politely for leaders, new refs, spots); we add NO load; storage ~1 MB; no email; no rule sheet (facts), though the Lounge wording goes through chat 3 + Brandon's GO.

## 4. WEATHER & FIRE WATCH (RULES FIRST)
- **What:** for every park pin: NWS active alerts (api.weather.gov, official, no key, polite) within the park's county/zone — red flag, flood, winter storm, tornado watch; NIFC/NASA FIRMS fire perimeters and hotspots within ~10 miles; USGS stream gauges in flood for river parks. Written per state, every 2 hours, into a file the cards and the Wednesday post can read.
- **Payoff:** safety: a member heading to a WMA under a red-flag warning or a flooded river access sees it on the card; HQ's 'safety alerts skip the second check' rule already exists for Kentucky posts.
- **Effort:** low-medium (two official JSON APIs).
- **Risks:** it DECIDES what members see (an alert on a card) → RULE SHEET first (what counts, radius, wording "NWS says…", how long shown, never 'safe'); server manners fine (NWS asks for a UA with contact: use the club site, never an email); storage tiny; email never.

## 5. ACCESS PIN VERIFIER (review list)
- **What:** for every access point / parking pin in data/access and ky access points: is the pin inside or within 100 ft of the park's owned land? on or within 50 ft of a public road (TIGER/Line roads, official, Census) or a Forest Service road (FS roads layer)? does the park page say 'gate', 'locked', 'seasonal road', 'walk-in only' near the pin's name? Output: weakest pins first + "no access pin yet" parks per state.
- **Payoff:** keeps the parking layer honest without people (the Oct 25–26 night built 1,000s of pins from layers; nobody can check them all).
- **Effort:** medium (one roads read per state from Census TIGER REST, ArcGIS so robots-exempt).
- **Risks:** none for members (review list only); server manners normal; storage none (lists only); no rule sheet.

## 6. ELEVATION & TAKE-OFF ATLAS
- **What:** elevation at every park pin, access pin and campground (USGS 3DEP point service, official, no key; NRCan CDEM for Canada), the park's HIGHEST POINT inside its outline (3DEP image service samples), and a simple take-off score (how open the horizon is) for VHF/UHF and satellite people; stored per state, refreshed never (terrain does not move).
- **Payoff:** SOTA-minded members and VHF activators ("the ridge road lot at 2,400 ft beats the river lot"); planners can sort by elevation.
- **Effort:** medium (sampling a grid inside each outline is many requests: ArcGIS getSamples takes a list, so one request per park).
- **Risks:** server manners (one 3DEP request per park; fine); storage ~1 MB; no rule sheet; no email.

## 7. LINE-PARK FRESHNESS WATCH (review list)
- **What:** for every trail / river / parkway park with a line or corridor: record the official layer's edit date, length and piece count; monthly re-read; flag changes (a reroute, a new section, a lost piece), and recompute which 2-fer spots sit within 100 ft of the moved line → a review list for chat 2 / chat 8.
- **Payoff:** trail 2-fers (Sheltowee, Lewis & Clark, Trail of Tears) are the ones that go stale quietly.
- **Effort:** medium (reads the layers the keys already use).
- **Risks:** none for members; storage none; no rule sheet (it flags; the 2-fer rules decide).

## 8. 2-FER FIELD GUIDE BUILDER
- **What:** one PDF per state (and per Kentucky region) built from the RULED 2-fer data: each spot with its map, both park numbers, the 'same land, two numbers' label, the small-overlap / very-tight tiers, access pin, closures note, last-checked date, both notices word for word; rebuilt when the 2-fer file changes; members download it offline.
- **Payoff:** the thing members would print and carry; the club's signature product.
- **Effort:** medium (the guide-PDF script already exists for Kentucky; generalize + maps as images from our outlines).
- **Risks:** it SHOWS 2-fers → every guide needs Brandon's GO and the FULL 2-fer notice; storage: PDFs are big (keep them on a release, not in git); no email; no new rules (uses the 14 rules as ruled).

## 9. HUNTING SEASON CALENDAR (RULES FIRST)
- **What:** each state's official hunting regulations (agency PDF / page) → per WMA and state forest: the gun deer / turkey / waterfowl season dates, quota-hunt days, 'closed to non-hunters' days; output '🦌 Hunting season <dates>: wear orange' notes and the HUNT items the closures super-bot needs (Sheet D class c).
- **Payoff:** safety and legality for activators on WMAs; feeds the closures bot the hunt closures every state has and few publish as 'closures'.
- **Effort:** high (regulations are long PDFs that change yearly; one reader per state, built state by state, Kentucky + Georgia first).
- **Risks:** it decides what members see (a 'closed to non-hunters' line) → RULE SHEET D already covers the showing; the reading needs its own sheet (what a 'season' is, which days are closures); storage small; email never; wrong dates are dangerous → chat 8 grades every state before GO.

## 10. FIELD-CONFIRMATION LOOP (RULES FIRST)
- **What:** reads the club's own reports (Map Rep tool, campground notes form, guestbook, Discord 'I parked here / activated from here' with a 👍 from staff) and tags access pins, campgrounds and 2-fer spots 'confirmed on the ground by a member on <date>' (no call signs public unless the member says so); flags disagreements ('member says gate locked, agency says open') for chat 8.
- **Payoff:** the only thing better than an official map is a member who stood there; it closes the loop the notices promise ('check before you go' → 'someone checked').
- **Effort:** medium (the forms + approvals pipeline exists; add a 'confirms' field to the data files).
- **Risks:** privacy (names, GPS from photos: the posting rules already strip them); it decides what 'confirmed' means → RULE SHEET first; email never; storage tiny.

## TOP 3
1. **Cell Coverage Atlas (#1):** the biggest payoff per request we will ever get; official source; decides nothing. It waits only for the free FCC token (Brandon: register at the FCC's Broadband Data Collection site, add the secret `FCC_BDC_TOKEN` (and `FCC_BDC_USERNAME`) to KPC-Data's Actions secrets; never paste it in chat). The campground info bot (job 4) already carries the FCC read, so the atlas is that read extended to every park pin and access point once the token exists.
2. **Hours, Fees & Permits bot (#2):** built tonight (below), because it is the only one of the three that needs no new secret and no question about a server's terms, and because Otter Creek's hours proved the need.
3. **POTA Activity Pulse (#3):** low effort, high payoff, zero new load on POTA; build when HQ says the Lounge wants it.

## BUILT TONIGHT: HOURS, FEES & PERMITS BOT (KPC-Data: `.github/scripts/kpc_hours_bot.py`, `.github/workflows/kpc-hours.yml`, `data/hours/`)
Facts with sources; decides nothing. Kentucky first with the answer key (kpc-ky-hours.json) as the test gate, then the 2-fer region order; quarterly refresh. Output `data/hours/<area>.json` + `data/hours/review.md` for chat 8; card wording after Brandon's GO (chat 3).
