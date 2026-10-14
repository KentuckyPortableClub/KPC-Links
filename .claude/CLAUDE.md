# Kentucky Portable Club website: notes for Claude

Owner: Brandon White, KZ4CP (brandonwhite42166@gmail.com). Plain-language answers please; he is a ham, not a web developer.
Live site: https://kentuckyportableclub.github.io/KPC-Links/ (GitHub Pages from `main`, repo KentuckyPortableClub/KPC-Links).

## House rules (do not break these)
- **N4KPC:** keep ALL N4KPC content off the site until Brandon says the FCC grant came through. When it does: add the call to the header, swap the hero image (KPC-logo-N4KPC.png is ready), add the Videos menu link.
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

## Campgrounds & Cabins (kpc-campgrounds.html) — goes live with the Oct 21 go-live
- HIDDEN until Oct 21 2026 5 PM Central: noindex (marked `<!-- KPC-GOLIVE -->`), not in menus/search/Find/Tool Box. kpc-go-live.yml runs .github/scripts/kpc_golive_campgrounds.py, which unhides it and adds the menu link (after Park Notes), search, Find It and Tool Box entries; the go-live roundup in kpc_social.js lists it. Don't link it anywhere before then.
- Only places to stay INSIDE Kentucky POTA parks. Data: kpc-campgrounds.json (campgrounds + lodging per POTA park, checked against official pages; every URL was seen, never guessed). Park names, counties, GPS, KFF/SOTA lists and 2-fer partners come live from kpc-ky-data.json. Page source: .claude/build/campgrounds/main.html (rebuild with assemble.py, then re-add the noindex line until go-live). Script: kpc-campgrounds.js.
- Reviews: Brandon's Google Form "KPC Campground Reviews" (not made yet). Questions must START with: Call sign, What are you reviewing (choice: inside a park / recommend a campground NOT in a park), Campground or cabin, Campground name, Town or county, GPS, Website, Type of campground, Rating, Site number, When did you stay, Restrooms, Showers, Hookups, Cell signal, RF noise, Room for antennas, Shade, Other amenities, Your review, Photos; add an Approved column to the sheet. kpc-campground-form.json holds url, placeEntry (Campground or cabin), and optional kindEntry/kindInside/kindOutside (pre-fill the choice); REVIEW buttons stay hidden while url is empty. Secret CAMPGROUND_SHEET_CSV. .github/workflows/kpc-campground-notes.yml (every 2 h) runs kpc_campground_notes.py → kpc-campground-notes.json, photos/campgrounds/. Outside-park recommendations show in the "Campgrounds outside the parks" section.

## Pre-approval for all forms (.github/scripts/kpc_preapproved.py)
- Park Notes, Community and Campground reviews publish a row when Approved = YES, or when Approved is empty and the call sign is pre-approved: every club member in MEMBERS in kpc-tools.js plus "extra" in kpc-preapproved.json (trusted non-members). Approved = NO always blocks. Call signs are self-typed on the form.

## KPC Community (kpc-community.html)
- Posts from Brandon's Google Form "KPC Community" (one form, branching sections by type: Station setup, Antenna build, Field tip, Gear review, Activation story, Elmer listing, Operator spotlight). Only rows with YES in Approved are published.
- .github/workflows/kpc-community.yml (every 2 hours) runs .github/scripts/kpc_community.py with secret COMMUNITY_SHEET_CSV; writes kpc-community.json and photos/community/ (1280 px, no EXIF). Question names in the form must match FIELDS in that script.
- The Share yours button uses FORM_URL at the top of kpc-community.js (set Oct 13 2026). Secret COMMUNITY_SHEET_CSV is set; first test post (KZ4CP Elmer listing) published OK.

