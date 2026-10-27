# WILL WE HIT A WALL? Limits and growth plan (Fable, HQ, Tue Oct 27 2026 ~12:30 PM)

Measured in the repo and with gh on Oct 27. Nothing sensitive here. Ranked: FIX NOW / PLAN / FINE.

## The numbers today
| What | Today | Limit | Headroom |
|---|---|---|---|
| Public repo size (GitHub) | 607 MB (working tree 516 MB: data 300 MB, .claude 27 MB, img 9.5 MB) | GitHub recommends < 1 GB, warns at 5 GB; **one file may never exceed 100 MB** (push rejected) | ~40% to the 1 GB mark; data/fers/W-FR.json has been **90 MB** in one version (53 MB now) |
| Published site size (GitHub Pages) | ~490 MB (everything on main except dot-folders) | 1 GB soft | ~50%, but the world 2-fer data would eat most of it |
| Pages builds | ~100 by noon today (48 built, 51 cancelled as superseded) = 6–8 an hour, peaks of 25 pushes an hour | **10 builds an hour soft limit**; 100 GB a month bandwidth | peaks are already over the soft limit; builds take 2–7 min each because the whole 490 MB tree is uploaded every push |
| Pushes to main | 358 commits in 24 h (HQ notes 68, research desk 28, Hunter counts 24, 2-fer bot 44, weather 8, park alerts 6…) | none, but every push = a Pages build | the chats' note commits are the biggest single source |
| Actions, public repo | ~640 scheduled runs a day (POTA Discord spotter 288, Hunters 96, band alerts 48, 5 bots at 24) + bot runs up to 134 min | **free, no minute cap for public repos**; 6 h per job; 20 jobs at once; a schedule is paused after 60 days without a commit | fine; the 2-fer bot's 5½-hour job is the only one near a per-job limit (Fable's 2-fer #1 splits it) |
| Actions, private app repo | one build a day: Android 3 min + Windows 1–2 min (×2 billing) ≈ 8 billable min/day ≈ 250/month; 39 runs in 30 days | 2,000 min/month; 0.5 GB artifact storage (fixed Oct 25 with 1-day retention) | ~12% of minutes |
| App repo size | 33 MB | same as above | fine |
| Outside services, visitors | Hunters Lounge polls POTA spots every 60 s per open tab (same as pota.app itself); Happening Now 60 s / 5 min; band maps 1–2 min | POTA publishes no limit; it tolerates a pota.app-like client | fine until hundreds of tabs sit open at once |
| Outside services, bots | POTA spot feed every 5 min (spotter) + 15 min (hunters); Spothole 3 min from the app; PSKReporter ≤ 1/5 min; NWS/NOAA hourly; agency map servers only in nightly keys | Spothole asks for ≥ 60 s between calls; PSKReporter bans under 5 min; NWS asks for a User-Agent | all within the published asks |
| Biggest downloads a phone makes | locations.json 5.1 MB (Checker, SOTA, finder, Lounge), ky-hunting-areas.geojson 2 MB, ky-usace 0.9 MB, ky-dbnf-owned 0.8 MB | phone memory fine; cellular data and first-load time are the cost | the 5 MB file is the one to split |
| Browser storage | 64 scripts use localStorage/IndexedDB (Logger, voice keyer, settings); Logger logs stay on the device | ~5 MB localStorage per site, IndexedDB far larger | fine; the Logger already uses IndexedDB |

## FIX NOW (this week; small)
1. **Keep the hidden 2-fer data out of the published site and under 100 MB per file.** data/fers (88 MB) is "hidden" only by having no link: Pages serves it. Two moves: (a) the bot writes the world files split per country part (never one file near 100 MB; the 90 MB W-FR.json would have broken a push at 100 MB and stopped the bot); (b) a `_config.yml` with `exclude: [data/fers, data/outline-leads, data/access-leads, data/trails, cache, .claude]` so Pages skips bot-only folders (this also cuts every Pages build's upload by ~100 MB). Jekyll is already on (no .nojekyll), so an exclude list is the only change. Chat 2 + chat 1 (one line each). Check first that no page fetches a file in an excluded folder (grep the html/js).
2. **Pushes = Pages builds: batch them.** 358 pushes a day means the live site is rebuilt ~150 times a day and queued builds get cancelled at peaks (the site lags main by minutes to an hour at busy times). Rules: chats push notes ONCE per session end, not per decision (HQ was the worst offender today: 68); the Hunters count bot and the 2-fer passes commit at the end of a run, not per state; data-only bots that run every 5–15 min (POTA spotter, band alerts) must not commit at all unless something changed (check they don't). Target: under 60 pushes a day. Chat 5 (bots) + every chat (notes).
3. **One daily `git gc` is not available on GitHub, so stop growing history with big files.** The 90/53/36/22/18 MB versions of W-FR.json and the 22 MB owned-land file are all in history for good (the repo is 607 MB on GitHub for 516 MB of files). Rule for every bot: a generated file over ~20 MB does not go in git; it goes to a Release asset (STORAGE PLAN already says so for PDFs) or is split. Chat 2.

## PLAN (next month)
4. **Split locations.json (5.1 MB)** by state/program so the Checker, SOTA tool, Park Commander and the Lounge load only what the visitor needs; cuts first-load on cellular from ~5 MB to under 1 MB. Chat 2 (data) + chat 3 (Lounge).
5. **Spotter at every 5 minutes = 288 runner starts a day.** Free, but GitHub may delay dense schedules and each run is ~1 min of VM for a few seconds of work. Either move it to every 10 min, or make one long-running job per hour that loops inside (12 polls per run). Chat 5.
6. **Release assets for the PDFs** (24.7 MB photo archive, 9.7 MB safety guide, 6.5 + 4.9 + 3.7 MB guides = ~50 MB in the tree and in every Pages upload): the STORAGE PLAN stage already decided this; do it now that the site is public. Chat 1.
7. **Visitor load on POTA/Spothole if the Lounge takes off:** add a shared cache step: the Hunters bot already writes spot counts; have it also write the last spot feed to a small JSON every 2 min, and let the Lounge read that file first (one fetch to GitHub's CDN instead of one to POTA per visitor), falling back to POTA live. Only worth it past ~100 simultaneous visitors; design it now, build when the counter shows it. Chat 3 + chat 5.
8. **Pages bandwidth** (100 GB/month soft): today's traffic is far below it; the 5 MB file × many visitors is the only way to reach it. Item 4 covers it. Watch GoatCounter monthly.
9. **Private app repo:** fine at ~12% of minutes. If Linux builds are turned on by default (both AppImages), the day doubles; keep them on the 'linux' tick box as now.

## FINE (checked, nothing to do)
- Actions minutes on the public repo (free), concurrency (20), per-job limit (only the 2-fer job is near 6 h and its split is already ordered).
- Browser storage and phone memory: the biggest pages hold under 10 MB in memory; the Logger uses IndexedDB.
- Bots' outside calls all sit inside each service's published asks (Spothole 60 s, PSKReporter 5 min, NWS User-Agent, RIDB key).
- App repo artifact storage (fixed Oct 25 with 1-day retention).
- The 60-day "no commits = schedules paused" rule: the repo commits daily.

## How to know we are close (watch these monthly, HQ)
- `gh api repos/KentuckyPortableClub/KPC-Links --jq .size` (KB): worry at 900,000.
- Biggest file in the tree: worry at 60 MB (`find . -size +60M`).
- Pages builds a day: `gh run list -w 372361621 -L 200` grouped by day: worry above 240 (10/hour).
- App repo: `gh api repos/KentuckyPortableClub/kpc-app/actions/runs/<id>/timing` on a real build: worry above 40 billable min a day.
- GoatCounter monthly views × 5 MB: worry at 20,000 views a month of the heavy pages (= 100 GB).
