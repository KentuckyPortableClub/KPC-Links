# Kentucky Portable Club website: notes for Claude

Owner: Brandon White, KZ4CP (brandonwhite42166@gmail.com). Plain-language answers please; he is a ham, not a web developer.
Live site: https://kentuckyportableclub.github.io/KPC-Links/ (GitHub Pages from `main`, repo KentuckyPortableClub/KPC-Links).

## House rules (do not break these)
- **N4KPC:** keep ALL N4KPC content off the site until Brandon says the FCC grant came through. When it does: add the call to the header, swap the hero image (KPC-logo-N4KPC.png is ready), add the Videos menu link.
  - Gold N4KPC lettering (transparent PNGs, Oct 14) is parked in .claude/build/n4kpc/ (not served by Pages): n4kpc-gold-straight.png (best for the small header call), n4kpc-gold-arch-outline.png (best laid over the hero photo; dark outline reads on any picture), n4kpc-gold-arch-smooth.png (spare; has a reddish fringe). Use only after the grant. Plan Brandon liked (Oct 14 preview, .claude/build/n4kpc/preview_shot.js has the CSS): header: replace the 'Est. 2026' line under the club name with n4kpc-gold-straight.png (cropped to its edges), LARGE = 26px tall (Brandon's pick; Medium 22px if it looks crowded once he sees it on his phone; 15px looked funny). Use !important on height/width because .brand img rules size it like the logo; hero = big KPC logo then the gold arch (phone stacked), and on computers the logo sits left of the arch (the logo is otherwise hidden on computers under 2040px by kpc-hero-logo-fix). WHERE (Brandon OK'd Oct 14): header gold call on EVERY page; big gold arch hero ONLY on index.html, the About page, members.html (with hero-founders picture) and contact-card.html. NOT on tool pages (they keep their own hero pictures).
- **US-0608 Ohio River Islands NWR** was on hold; Brandon approved it Oct 13 2026 (KY part = Manchester 1 & 2 islands, boat only). It is now in the guide and tools. Its card was added to both Resource PDFs with `.claude/build/add_park_card.py` (numerical: page 17; A-Z: page 44, with Old Fort Harrod moved onto that page). The script refuses to run twice; if the PDFs are ever fully rebuilt, the generator must include US-0608 itself.
- **kpc-loaded-verticals.html stays hidden:** noindex, not linked from any menu, hub, search or sitemap.
- **Never ask Brandon to paste keys or tokens into chat.** Facebook/Discord secrets live only in GitHub → Settings → Secrets and variables → Actions: `FB_PAGE_ID`, `FB_PAGE_TOKEN`, `KPC_DISCORD_WEBHOOK`.
- **Service worker cache name `kpc-finder-v1` (kpc-finder-sw.js / kpc-offline.js) must never change.**
- **Don't load kpc-tools.js into pages that already have their own inline nav script** (it adds a second menu toggle). The club roster lives only in `MEMBERS=[...]` in kpc-tools.js; other scripts fetch that file as text and read the list.
- **Facebook can only post to the Page (ID 1342190728983628), never to Groups.**
- **"2-fer" means two overlapping POTA parks ONLY.** Call that group "Overlapping boundaries", never "shared" (parks that only touch at a border are not a 2-fer). A KFF or SOTA reference that shares ground with a POTA park is not a 2-fer: show it as "Also:" / a multi-program spot, never with the 2-fer label.
- **Members Room only:** `KPC_Kentucky_POTA_2fers_3fers_Guide.pdf`, `KPC_KY_POTA_2fers_3fers.gpx` and `kpc-multi-park-spots.html` (noindex) are linked only from members.html (#multipark). Keep them off public menus, hubs, search and sitemap.

## How pages are built
- Plain static HTML/CSS/JS, no build system. Every page carries the same header, menu ("More" menu) and footer copied from news.html. A menu change means updating all ~65 pages.
- New pages: write the main content to a scratch file, then from the repo root run
  `python3 .claude/build/assemble.py <main.html> <newpage.html> "<Title> | KPC" "<description>"`.
  Placeholders: `@@CSS@@`, `@@COMPARE@@`, `@@HEADER@@`, `@@FOOTER@@`.
- When adding a page, also add it to kpc-search.js, find.html, and toolbox.html or antennas.html as fits.
- Every footer has a Privacy link (kpc-privacy.html).
- When a page's script changes, bump its `?v=YYYYMMDDx` query in the `<script src>`.
- Must work at phone width (390px) with no sideways scroll. Test with Playwright (Chromium is preinstalled; use `NODE_PATH=$(npm root -g)`) against `python3 -m http.server 8765`.

## Pushing
- Before editing: `git fetch && git reset --hard origin/main`, because the bots commit too.
- Commit, then `git push origin HEAD:main`.
- Check the "pages build and deployment" run: `gh run list -R KentuckyPortableClub/KPC-Links -w 372361621 -L 1`.
- Getting Actions results: `gh run view --log` is blocked here. Scripts print `::notice title=...::` lines, so read them with `gh api repos/KentuckyPortableClub/KPC-Links/check-runs/<job id>/annotations`.
- Use REST rather than GraphQL for issues.
- Dispatch workflow runs one at a time; queued runs in the same concurrency group cancel each other.

## Automations (.github/workflows, scripts in .github/scripts)
- **kpc-events.yml**, Mondays: auto-finds KY events into kpc-events-auto.json (merged with the hand list in kpc-events.js), then posts the upcoming list to Discord and Facebook.
- **kpc-social.yml**, Facebook/Discord posts:
  - Daily: campout countdown, milestones, photo of the week, new-page roundup.
  - Wednesdays: rare-park pick.
  - Thursdays: weekend outlook.
  - State is kept in kpc-social-state.json. `dry_run` is the default for manual runs.
- **kpc-pota-discord.yml**: member POTA spots to Discord and Facebook. Facebook posts on band changes are limited to once per 30 minutes per operator and point people to kpc-spots.html.
- **kpc-band-alerts.yml**, every 30 min: band-alert posts to Discord only.
- **kpc-youtube.yml**: shares new club videos to Facebook (kpc-fb-posted.json).
- **kpc-link-check.yml**, Sundays, and **kpc-ref-check.yml**, monthly: both open GitHub issues.
- **kpc-go-live.yml** (one time): Oct 21 2026, 5 PM Central. Swaps campoutHOLD/eventsHOLD/resourcesHOLD.html into campout/events/resources.html and posts the new-page roundup. Until then, edits to events/resources/campout must also go into the HOLD copies.
- All workflows use actions/checkout@v5.

## Ideas Brandon has mentioned for later
- Satellite pass predictor.
- WWFF checker.
- Remote transmit.
- KPC CW practice night on Vail (Brandon to decide).
- N4KPC changes after the grant (see above).
- **KPC CW challenge LEADERBOARD (waiting on Brandon's Google Form):** the weekly challenge itself is built (QRQ tab, same 60 items for everyone from the ISO week, score in localStorage kpcWeekly, Share button). Still to do: a Google Form (Call sign, Week, Points, Top WPM + Approved column), published-CSV secret, a sync job like Community, and a leaderboard on the CW page. A reminder was scheduled for Brandon. Not picked yet: CW Night countdown card.
- **Voice (SSB) pileup practice — full version (to-do, Brandon Oct 14):** BETA is live but HIDDEN: kpc-ssb.html + kpc-ssb.js (noindex, not in menus/search/Find/Tool Box; Brandon shares the link with testers). Beta = activator only, browser speechSynthesis voices (one at a time, so pileups are back-to-back callers), levels 1-5, checked log, ADIF export marked PRACTICE. To-do for the full version: Hunt mode, mic + speech recognition replies (Chrome/Edge), then STEP 2 = real overlapping pileups from club members' recorded clips (phonetics, numbers, 'five nine', state names, QRZ, thanks: script + upload form), mixed in Web Audio with SSB filtering, QSB and noise. When Brandon OKs the beta: add it to the See More menu, search, Find and Tool Box.
- Community page chat/message board (later): embed the club Discord with WidgetBot for live chat, then Groups.io for threaded posts. Not giscus (most hams lack GitHub accounts).

## 2-fers & 3-fers (single source: .claude/build/fers/fers.json)
- fers.json holds the 62 spots, their GPS guide pins, the unconfirmed pairs, sources and the change log. Park names must match the POTA US-KY list exactly.
- Every GPS pin is a guide that gets people to the area, never a confirmed spot. Riverbank pins are approximate (not checked against the water line). The four historic trail sites (Wickliffe Mounds, Big Bone Lick, Golden Pond VC, Columbus-Belmont) are NOT within 100 ft of the river/trail and must cite their NPS page.
- After editing fers.json, rebuild from the repo root: `python3 .claude/build/fers/guide.py` (field guide PDF). `python3 .claude/build/fers/resource_patch.py` refreshes the index pages and the 2-fer lines in the two Resource PDFs, but it expects the ORIGINAL Resource PDFs (index pages at pages 3-5), so run it against the copies from git history before commit 'Recheck 2-fers' or adjust it.
- `python3 .claude/build/fers/sync.py` pushes fers.json into kpc-multi-park-spots.html, kpc-ky-data.json (tf) and ky-overlaps.geojson; `gpx.py` writes the GPX. NPS route files used for checks (Trail of Tears, Lewis & Clark route and auto tour route) are saved in .claude/build/fers; ky-lecl-auto.geojson is the simplified auto tour route map layer.
- Also keep in step: KPC_KY_POTA_2fers_3fers.gpx, the DATA array in kpc-multi-park-spots.html, `tf` in kpc-ky-data.json (only confirmed pairs), ky-overlaps.geojson (unconfirmed pairs use kind "unconfirmed"), and the trail boxes on parks.html.

## Web guides (the old PDFs are now printed from web pages)
- Each guide is a web page; the PDF with the OLD filename is printed from it by .github/workflows/kpc-guide-pdf.yml (.github/scripts/kpc_guide_pdf.js, Playwright). It runs when a kpc-guide-* file, kpc-ky-data.json or kpc-top25.json changes, after the weekly Top 25 refresh, Mondays, or by hand. It only commits a PDF whose words or links changed. Don't edit these PDFs by hand any more: edit the page or its data.
  - kpc-guide-pota.html (?order=num / ?order=az → the two POTA Resource PDFs), data kpc-guide-pota-data.json + live kpc-ky-data.json.
  - kpc-guide-sota.html, kpc-guide-wwff.html (data kpc-guide-sota-data.json / kpc-guide-wwff-data.json + kpc-ky-data.json).
  - kpc-guide-top25.html (kpc-top25.json, refreshed Mondays by kpc-top25.yml from api.pota.app).
  - kpc-guide-tools-links.html, kpc-guide-founders-favorites.html (kpc-guide-links.json, also read by the link checker), kpc-guide-beginners.html, kpc-guide-antenna-efficiency.html.
  - kpc-guide-safety.html is the light web version; the illustrated Safety Guide PDF stays as it was (not reprinted).
- Page sources and rebuild scripts: .claude/build/guides/ (POTA/SOTA/WWFF: src/*.html, build_pages.py, extract_*.py) and .claude/build/guides2/ (build.sh). Edit the src and rebuild rather than editing the built HTML.
- Guide maps (POTA/SOTA/WWFF regional maps, Wild Rivers map) draw counties from kpc-ky-counties-hd.json (US Census cb_2023 500k, simplified 30% with mapshaper keep-shapes, so neighbouring counties share edges). kpc-ky-counties.json (rougher) is still used by kpc-tools.js.
- Print rules: kpc-guide-print.css. A page must set `<html data-ready="1">` when fully drawn or the printer skips it.
- After editing fers.json, also run `python3 .claude/build/guides/extract_pota.py --fers` so the POTA web guide (and its PDFs) pick up the 2-fer changes. resource_patch.py is no longer needed for the Resource PDFs.
- Still PDF-only (not web pages): Campout Flyer, checklists, 2026 event photo archive, Meet the Founders, the two "Coming Soon" founders PDFs (convert when ready), the members-only 2-fers guide.

## Park Notes (kpc-park-notes.html)
- Community tips for every KY POTA park, SOTA summit and KFF reference (from kpc-ky-data.json, lowest number first).
- Tips come from Brandon's Google Form "KPC Park Tips" → Google Sheet. Only rows with YES in the sheet's Approved column are published.
- .github/workflows/kpc-park-notes.yml (every 2 hours) runs .github/scripts/kpc_park_notes.py: reads the sheet's published CSV from secret NOTES_SHEET_CSV, writes kpc-park-notes.json, copies approved photos to photos/notes/ (shrunk to 1280 px, no EXIF). Never put the CSV link in the site or in chat.
- The "Submit a tip" button needs FORM.url and FORM.parkEntry at the top of kpc-park-notes.js (from the form's pre-filled link).

## Campgrounds & Cabins (kpc-campgrounds.html) — LIVE since Oct 14 2026
- Brandon put it live early (Oct 14): in the See More menu (after Park Notes), search, Find It and Tool Box. No tools-disclaimer box on this page (Brandon's call). kpc_golive_campgrounds.py already ran; the Oct 21 go-live job runs it again harmlessly, and the go-live roundup in kpc_social.js still lists the page.
- Only places to stay INSIDE Kentucky POTA parks. Data: kpc-campgrounds.json (campgrounds + lodging per POTA park, checked against official pages; every URL was seen, never guessed). Park names, counties, GPS, KFF/SOTA lists and 2-fer partners come live from kpc-ky-data.json. Page source: .claude/build/campgrounds/main.html (rebuild with assemble.py). Script: kpc-campgrounds.js.
- Reviews: Brandon's Google Form "KPC Campground Reviews" (not made yet). Questions must START with: Call sign, What are you reviewing (choice: inside a park / recommend a campground NOT in a park), Campground or cabin, Campground name, Town or county, GPS, Website, Type of campground, Rating, Site number, When did you stay, Restrooms, Showers, Hookups, Cell signal, RF noise, Room for antennas, Shade, Other amenities, Your review, Photos; add an Approved column to the sheet. kpc-campground-form.json holds url, placeEntry (Campground or cabin), and optional kindEntry/kindInside/kindOutside (pre-fill the choice); REVIEW buttons stay hidden while url is empty. Secret CAMPGROUND_SHEET_CSV. .github/workflows/kpc-campground-notes.yml (every 2 h) runs kpc_campground_notes.py → kpc-campground-notes.json, photos/campgrounds/. Outside-park recommendations show in the "Campgrounds outside the parks" section.

## Pre-approval for all forms (.github/scripts/kpc_preapproved.py)
- Park Notes, Community, Campground reviews and KPC Reports (conditions, photos, events) publish a row when Approved = YES, or when Approved is empty and the call sign is pre-approved: every club member in MEMBERS in kpc-tools.js plus "extra" in kpc-preapproved.json (trusted non-members). Approved = NO always blocks. Call signs are self-typed on the form.

## KPC Community (kpc-community.html)
- Posts from Brandon's Google Form "KPC Community" (one form, branching sections by type: Station setup, Antenna build, Field tip, Gear review, Activation story, Elmer listing, Operator spotlight). Only rows with YES in Approved are published.
- .github/workflows/kpc-community.yml (every 2 hours) runs .github/scripts/kpc_community.py with secret COMMUNITY_SHEET_CSV; writes kpc-community.json and photos/community/ (1280 px, no EXIF). Question names in the form must match FIELDS in that script.
- The Share yours button uses FORM_URL at the top of kpc-community.js (set Oct 13 2026). Secret COMMUNITY_SHEET_CSV is set; first test post (KZ4CP Elmer listing) published OK.


## KPC Reports form (kpc-reports.yml) — built Oct 14 2026, form links not set yet
- One Google Form "KPC Reports", branching on the first question. Sheet columns must START with (any order, case-insensitive): Timestamp, Call sign, What are you sending (answers exactly: "Park conditions" / "Report a problem on the website" / "Share a photo" / "Add an event"); Park number, Condition (Gate locked / Road closed / Flooding / Campground closed / Hunting in progress / Construction / Other), Details, Date you saw it; Which page or park, What's wrong; Photo, Where was it taken, Caption, OK to use on the website (checkbox); Event name, Event date, Start time, Location, Event website, About the event; Your comment, Show it on the website (Yes/No); plus Brandon's Approved column. "What are you sending" also has the answer "Leave a comment". Park number may be just the number ("1277" = US-1277); US-/K-/KFF-/W4K/ prefixes work too.
- Secret KPC_REPORTS_CSV (published CSV; never in the site or chat). .github/workflows/kpc-reports.yml (every 2 h) runs .github/scripts/kpc_reports.py. Pre-approval rules as above (kpc_preapproved.py).
- Conditions → kpc-conditions.json {updated, items:[{id, ref, kind, details, seen, call, expires}]}; only refs in kpc-ky-data.json; shown 30 days after "Date you saw it" (expired ones dropped by the script and ignored by the pages). Red banners (class no-print) on Park Notes items (plus a count chip on the row), Campgrounds & Cabins park cards and POTA guide cards; a report on a park's KFF/SOTA ref also shows on the park (KPCReports.related).
- Problems → never on the site or in a repo file. One rolling GitHub issue labelled "kpc-site-problems" lists every problem row whose Approved cell is not DONE / FIXED / NO; it closes itself when none are left. The repo is public, so the issue is too (the privacy page says so). The issue step only runs inside GitHub Actions.
- Photos → only approved AND "OK to use" ticked: photos/members/<id>-N.jpg (1280 px, no EXIF) + kpc-member-photos.json {updated, photos:[{id, file, caption, where, call, date}]}, shown in the "Member Field Photos" album (section id member-photos) of photos.html, kept separate from the Google Photos event albums (same lightbox). Files no longer approved are deleted.
- Comments → only "Show it on the website" = Yes AND approved/pre-approved: kpc-comments.json {updated, comments:[{id, call, text, date}]} newest first, shown in "What members are saying" on kpc-community.html (kpc-community.js) with a LEAVE A COMMENT › button. Comments marked No are never published, never in a repo file and never in the GitHub issue (Brandon reads them in the sheet).
- Events → kpc-events-submitted.json {updated, events:[...]} (same format as kpc-events-auto.json, tag MEMBER, member:true, source MEMBER) and merged into kpc-events-auto.json "found" right away; kpc_events.py also merges the submitted file every Monday. So they appear on events/eventsHOLD, the home page Next Up, Discord and Facebook. No website → a MAP link (urllabel).
- Buttons come from kpc-reports-form.json {url, kindEntry, parkEntry, kinds{conditions, problem, photo, event}} via kpc-reports.js (shared helper, load it BEFORE the page script). All buttons stay hidden while url is empty: ⚠ REPORT CONDITIONS (Park Notes, Campgrounds), SHARE A PHOTO › (photos.html), + ADD AN EVENT (events.html + eventsHOLD.html), LEAVE A COMMENT › (kpc-community.html). kinds also has comment = "Leave a comment". The "Let us know" links in the kpc-disclaim boxes still go to contact.html.
- Menu (Oct 14, Brandon's call): the top-menu "Photos" link stays the Google Photos share URL in a new tab on every page (the move to photos.html was undone), and kpc-search.js's camera icon on old-style headers also opens Google Photos. The See More menu has "Member Field Photos" → photos.html#member-photos right after Community on every page (also in the kpc-search.js TOOLS list and find.html; the old "Photos" photos.html entries are kept).

## KPC-drawn boundaries (ky-kpc-drawn.geojson) — added Oct 14 2026
- Approximate outlines for KY POTA parks with NO official GIS boundary: US-3802 Buckley, US-10173 Horse Park, US-1264 Levi Jackson (now Laurel County), US-10099 Wolf Creek NFH (hull around hatchery + visitor center), US-3787 White Hall. From OpenStreetMap (ODbL, credited in the popup). Brandon OK'd them from screenshots.
- Layer "bkpc" in gis-overlays.js (Park Commander, checkbox gis-bkpc) and kpc-planner.js (B.bkpc): yellow #ffd400 dash-dot '12 5 2 5', NO shading (fillOpacity 0), popup warns it's approximate.
- William Whitley (US-3789) added Oct 14 (OSM way 848672001). Wolf Creek NFH was moved OUT of the KPC-drawn file: it now has official USFWS land in ky-fws.geojson.
- **ky-fws.geojson** (layer bfws, light blue #5ab0ff, Park Commander checkbox gis-bfws + planner B.bfws): USFWS owned land (FWSInterest_Simplified_Authoritative, INTTYPE1 O/S) for Green River NWR US-10098, Clarks River NWR US-0295, Reelfoot NWR US-0538, Ohio River Islands NWR US-0608, Wolf Creek NFH US-10099.
- Still missing: US-10172 Salato (no outline anywhere). E. Lucy Braun, Lake Malone, Fishtrap Lake WMA and the KY part of GW&J NF already have official outlines; their POTA + KFF pins were moved just inside them on Oct 14 (GW&J pin moved from Virginia to the KY piece near Pine Mountain, 37.09269,-82.73391).

## CW pages & member hero pictures — Oct 14 2026
- CW was split: kpc-cw.html = **CW Practice Room** (simulator, drills, live CW spots/receiver, key, log, Vail/VBand) and kpc-cw-info.html = **CW Info & Links** (typical exchanges with ▶ buttons played by the small kpc-cw-say.js, abbreviations, clubs/classes/apps). A pill strip under each hero links the two. Both are in the See More menu right after Band Plan by License on every page, plus kpc-search.js, find.html and toolbox.html.
- Hero pictures (wide X.jpg + tall X-mobile.jpg), applied by `.claude/build/hero_people.py` (re-runnable; adds `<style id="kpc-hero-pic">` and a name·call badge): Zach K4ZSR → both CW pages; Brent N4BDW → kpc-weather.html; Aaron KQ4HZK → kpc-community.html; KY flag + KPC → members.html; mountain lake camp → kpc-campgrounds.html; river camp → kpc-park-notes.html. On phones the member pictures sit on top with the words underneath.
- Happening Now (kpc-live.html): solar numbers only in the top Status bar and the Space Weather card (Brandon: two is plenty). The band-map widget hides its Solar Conditions tile when #kpc-bands has data-nosolar.

## Field Weather (kpc-weather.html + kpc-weather.js) — rebuilt Oct 14 2026
- Starts from: ?lat=&lon=&name= / ?ref= link, else the last spot (localStorage kpcWxLoc), else GPS if already allowed, else Frankfort. "USE MY LOCATION" button + one search box (KY park/summit/KFF number or name from kpc-ky-data.json, towns/ZIP via Open-Meteo geocoding).
- Shows: NWS alerts (api.weather.gov/alerts/active?point=, severe ones open), right now + field-call chips (storms/CAPE, gusts, rain, heat/cold), next 24 h strip, radar map (IEM NEXRAD 50-min loop, nowCOAST lightning, alert polygons; Leaflet from cdnjs, NOT kpc-tools.js because the page has its own nav script), 7-day bars + NWS text periods, NOAA Weather Radio for the county.
- NOAA Weather Radio data: kpc-nwr.json (transmitters around KY with SAME county codes), refreshed monthly by kpc-nwr.yml (.github/scripts/kpc_nwr.py from weather.gov/source/nwr/JS/ccl-data.js). County comes from the NWS points county zone (KYC073 → SAME 021073). Live audio plays on the page (no sign-in) from wxradio.org Icecast mounts listed in WXR in kpc-weather.js (KY-Frankfort-WZ2523, KY-Owenton-KZZ48, IN-Indianapolis-KEC74, WV-Charleston-WXJ84, OH-Chillicothe-KJY68, OH-Columbus-KIG86, TN-Memphis-WXK49, MO-StLouis-KDO89; source list noaaweatherradio.org). Broadcastify (KIH43/KIH44/KIH39) needs a sign-in, so it's only a text link.

## CW Practice (kpc-cw.html, kpc-cw.js, kpc-cw-rx.js, kpc-cw-spots.js)
- Tabs: Hunt, Activate (pileup size 0-12 with quick -/+), Ragchew (full QSO: name/QTH/rig/ant/WX, AGN? repeats, QRS slows them), Copy Drills (incl. Head copy and My problem letters), QRQ Ladder (copy + send, 3 misses, personal bests/badges in localStorage kpcQRQ), Free Send, Listen & Decode.
- Problem letters: every copy check (drills + QRQ copy) counts missed characters in localStorage kpcCWmiss.
- Zach's (K4ZSR) welcome is keyed once per visit on the first START; checkbox to turn it off.
- Paddle keyer is timed on the AudioContext clock; Swap Paddles button sits under the paddles. Mouse paddle box (computers only, hover+fine pointer): left button = dit, right = dah, both = squeeze (honors Swap); straight key = any button.
- Sprint tab: timed 5/10/15 min run, formats POTA run / CWops CWT / SKCC sprint, score = QSOs x states, personal bests in localStorage kpcSprint.
- Band conditions setting (Clean / Typical / Rough): static crashes, a neighbour station (QRM) and tuner-uppers during Hunt, Activate, Ragchew and Sprint only (never in drills or the QRQ ladder).
- Fist doctor under the fist meter: compares dah length and gaps (in a letter / between letters / between words) with textbook timing and gives up to 3 plain-word tips; with paddles only spacing is judged.
- Games tab: Falling letters (send to clear with key/paddles; keyboard = hear and type) and Beat the clock (A-Z, 0-9, call x3, PARIS); bests in localStorage kpcGames. Keyer tab: 8 big memory buttons (F1-F8), {MY} {THEIR} {REF} {ST} fill-ins, editable (localStorage kpcKeyerMem); sidetone only, does not key a radio.
- Gauntlet tab (expert): 5 rounds (35+ WPM copy; cut numbers + /P /QRP DX calls; 9-12 call pileup with look-alikes; weak station with deep QSB, crashes and a loud QRM 100 Hz away; bug/straight-key sloppy fists), one AGN per item, 30 s to answer, 3 busts = out; weekly option seeded from the ISO week; bests in localStorage kpcGauntlet. Could join the CW challenge leaderboard later.
- Decoder (kpc-cw-rx.js): mix-down + narrow 3-pole low-pass (auto width ~2.6 Hz per WPM, 50-160 Hz, or 50/100/200 picked), KPCRX.simulate({text,wpm,snr,offset,bw}) is a test bench (SNR in 2.5 kHz). Oct 14 bench: copies to about -6 dB at 15 WPM, -3 dB at 25-35 WPM (old Goertzel version failed below about +1 dB). SIGNAL readout is SNR in 2.5 kHz with GOOD/WEAK/TOO WEAK.

## Kentucky college scoreboard (kpc-community.html under the hero, kpc-scores.js) — Oct 14 2026
- UK, UL, WKU, EKU, Murray, Morehead (football + basketball M/W + baseball), NKU and Bellarmine (basketball + baseball). ESPN public team schedules fetched in the browser from site.WEB.api.espn.com (site.api.espn.com has no CORS for browsers), only for sports in season (plus a month early). Shows live, next 10 days, finals from the last 7 days; no fetch cache option (no-store adds headers that break ESPN CORS); live games refresh every minute; gentle auto-scroll that stops on touch.
- 🎧 LISTEN = the home KY school's audio page (UK: ukathletics.com/uk-sports-network/; others: <site>/sports/<slug>/schedule, each game's Listen link is there). ESPN ids are in TEAMS (baseball ids differ).
- Campgrounds page: a ⭐ reviews box (#cgRv, drawRv in kpc-campgrounds.js) sits under the closures/WMA notes: newest 3 reviews, SHOW ONLY PLACES WITH REVIEWS (turns on the ★ HAS REVIEWS chip), OUTSIDE-PARK PICKS ↓, WRITE A REVIEW ›.

## Other Oct 14 changes
- contact-card.html (the QR link card) restyled dark like the Park Commander header (round KPC-logo.png with gold glow); YouTube cards moved up under Facebook.
- photos.html: the EMAIL YOUR PHOTOS button is gone (photos come in through the KPC Reports form or the Google Photos album).
- kpc-antenna.html / kpc-battery.html badges: badge-camp-antenna.jpg / badge-river-radio.jpg (crops of the member scene pictures) instead of badge-sign.jpg (Brandon: the wooden Kentucky shape was wrong).
- Scoreboard cards: 🎧 LISTEN (school audio page) + 📻 RADIO (TuneIn search for the team's radio network, backup) + ESPN ↗.
- Campgrounds reviews box: SEE ALL N REVIEWS opens the full list (best rated first, facts shown), each item jumps to its park card or the outside-park section.
- Trip Planners dressed up: kpc-tools.css .tool-head.th-river (KY planner, hero-river-camp) and .th-flag (US planner, hero-ky-flag) + .th-chips feature chips; the pages load kpc-tools.css?v=20261014a.
- Park Commander (finder.html) dressed up: `<style id="kpc-pc-dress">` puts hero-lake-camp(.jpg/-mobile.jpg) behind the masthead header (header:not(.site-nav)), gold-glow logo, stat chips (#pcStats, counts filled from kpc-ky-data.json: POTA parks, SOTA summits, KFF, parks with 2-fers), icon jump buttons.
- Member heroes on computers (weather, community, both CW pages): hero_people.py draws the picture as .hero:before on the right (aspect-ratio 1672/941, mask fade on its left), so the whole person shows at any width; phones keep the picture-on-top layout. Edit hero_people.py, never the generated kpc-hero-pic block by hand.

## Dark mode (kpc-theme.js) — batch 1 Oct 14 2026
- Every page loads `<script src="kpc-theme.js?v=...">` right after `<meta charset>` (new pages get it from news.html via assemble.py; add it by hand to any page built another way). It follows the device setting, and a round 🌗/🌙/☀️ button it adds to the top bar cycles Auto → Dark/Light (localStorage kpcTheme).
- How it works: in dark mode it reads each element's computed colours and sets inline !important replacements (light backgrounds → dark, same hue; dark text on dark → light; light borders → dark). It re-checks elements added later or whose class/aria-pressed/open/hidden change. Pictures, SVG diagrams, map tiles, .qrbox and anything inside [data-keep-light] are skipped. Printing always reverts to light; ?print= / ?pdf= or <html data-no-dark> turn it off.
- Batch 2 (Oct 14): hover colours are recomputed while the pointer is over a link/button/card (pointerover, plus once more after 320 ms for transitions); SVG drawings/maps on a light background get a soft invert (filter invert(.9) hue-rotate(180deg)) so they sit on the dark page. Leaflet maps and [data-keep-light] are never touched.
- More headers (Oct 14, Brandon's pictures): kpc-tools.css classes th-aurora (Band Plan, Rare Parks; also Radio Conditions' own .hero), th-mast (SOTA, Antenna Calculator, Antenna Model, Radials), th-solar (Battery), th-map (Park Checker, Grid & County, Park Sheet), th-op (Tracker, Recap, On The Air live-head; only a tall picture, shown as a faded right panel on computers). Pictures hero-<name>.jpg + -mobile.jpg. Brandon: do NOT use the aurora-with-lantern picture. Club stats keeps its founders badge.
- Saved for later (Oct 14, not used on any page yet): hero-founders.jpg (wide) + hero-founders-mobile.jpg (tall) — the four founders as cartoons on a ridge over the lake with the big KPC logo and the Parks/Radio/Friends/Adventure sign. Good fit: Members Room hero, About page, or the Oct 21 go-live / campout. Ask Brandon where before using.
