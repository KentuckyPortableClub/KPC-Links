# Kentucky Portable Club website: notes for Claude

Owner: Brandon White, KZ4CP (brandonwhite42166@gmail.com). Plain-language answers please; he is a ham, not a web developer.
Live site: https://kentuckyportableclub.github.io/KPC-Links/ (GitHub Pages from `main`, repo KentuckyPortableClub/KPC-Links).

## House rules (do not break these)
- **N4KPC:** keep ALL N4KPC content off the site until Brandon says the FCC grant came through. When it does: add the call to the header, swap the hero image (KPC-logo-N4KPC.png is ready), add the Videos menu link.
- **US-0608 is on hold.** Don't add it anywhere (kpc-ref-check.yml has it in ON_HOLD).
- **kpc-loaded-verticals.html stays hidden:** noindex, not linked from any menu, hub, search or sitemap.
- **Never ask Brandon to paste keys or tokens into chat.** Facebook/Discord secrets live only in GitHub → Settings → Secrets and variables → Actions: `FB_PAGE_ID`, `FB_PAGE_TOKEN`, `KPC_DISCORD_WEBHOOK`.
- **Service worker cache name `kpc-finder-v1` (kpc-finder-sw.js / kpc-offline.js) must never change.**
- **Don't load kpc-tools.js into pages that already have their own inline nav script** (it adds a second menu toggle). The club roster lives only in `MEMBERS=[...]` in kpc-tools.js; other scripts fetch that file as text and read the list.
- **Facebook can only post to the Page (ID 1342190728983628), never to Groups.**

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
