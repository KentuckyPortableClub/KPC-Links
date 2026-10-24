# Starting a new chat (Brandon Oct 24 2026: 'this chat so big … a note by category for a new chat to be up to speed')

Every new chat reads `.claude/CLAUDE.md` (house rules) by itself. Paste ONE starter below as the first message; it tells the new chat which topic file to read, so it does not spend usage reading everything.

## Things every chat must know (already in CLAUDE.md)
- Brandon White KZ4CP, plain-language answers, he is a ham not a developer. Short notes, his words.
- Email only for real problems (bots/runs must not fail; no 'what changed' issue comments).
- Members-only site: kpc-gate.js PUBLIC list; new pages are members-only until added.
- Practice calls K4TEST / W4KIDS (app tests: Q-prefix calls). Never a real call as an example.
- No POTA/SOTA/WWFF logos; footer independence line. '2-fer' = two overlapping POTA parks only.
- Never ask for keys/passwords in chat. Never write the member password anywhere.
- Push: `git fetch && git reset --hard origin/main` before editing, commit, `git push origin HEAD:main`.
- Test at 390 px (phone) and desktop with Playwright before pushing.
- QRZ bios: no 4-byte emoji (QRZ cuts the bio off at the first one).

## 1. Website pages & tools (general)
"Read .claude/notes/website.md and .claude/notes/ideas.md. We're working on KPC website pages (menus, looks, forms, guides, CW/kids rooms, Discord/Facebook bots)."

## 2. Maps, boundaries & park data
"Read .claude/notes/mapping.md. We're working on park boundaries / answer keys (KY, US, Canada, world), Park Control, trip planners, Am I in the Park, Map Rep, 2-fers, closures."

## 3. Hunters Lounge + Activators Lounge (+ KPC Logger, spots pages)
"Read .claude/notes/logger-lounge-digi.md and the Activators Lounge / Hunters Lounge bullets in .claude/notes/ideas.md. We're working on the Hunters Lounge (public kpc-hunters.html + Park Checker, members kpc-hunt.html), the Activators Lounge (kpc-activators-lounge.html, members-only until I show the club), Park Tracker, Rarely Activated, Top 25, SOTA checker, the KPC Logger."

## 4. KPC App (FT8 + logger + digital modes, Android + Windows)
"Read kpc-app/CLAUDE.md and kpc-links/.claude/notes/ft8-app.md (the end: latest builds + what I tested). Private repo KentuckyPortableClub/kpc-app. Build = once a night 3:17 AM; batch changes. Fable = engine/remote/decoder, Opus = screens/features."
(Clone the app repo in that chat: it is attached with add_repo KentuckyPortableClub/kpc-app.)

## 5. Bots, Discord, Facebook, email relay
"Read .claude/notes/website.md (Discord relay / social / bots parts). We're working on the GitHub Actions bots, Discord posts, the Facebook Page, the email relay. Remember: email only for real issues."

## 6. Campout & events (KPC27, calendar, videos)
"Read .claude/notes/website.md (campout + events parts) and ideas.md (KPC27 challenges scorer, contests on the calendar, videos). We're working on the 2027 campout pages and the Kentucky Radio Calendar."

## Links
- Website: https://kentuckyportableclub.github.io/KPC-Links/
- Activators Lounge (members): https://kentuckyportableclub.github.io/KPC-Links/kpc-activators-lounge.html
- Hunters Lounge (public): https://kentuckyportableclub.github.io/KPC-Links/kpc-hunters.html · Park Checker: kpc-hunters-need.html
- N4KPC QRZ bio source: .claude/build/n4kpc/qrz-bio.html

## OPEN TO-DO PER CHAT (Oct 24 5:40 PM, Brandon: 'to do list by new chat complete'). Tick off here as done.
1. Website: three new club bots (Lonely Parks, Park of the Week, + the 3rd in ideas.md) after the app stage · contests on the main calendar (Brandon OKs the list) · App look back onto the site (after he likes the app) · Hunters Lounge installable app · KPC NET voice net (pick AllStar/EchoLink/other) · DigiPi help + guide page · UV-K5 fox (ask which firmware first) · Ask-later talk: release trip planners, 'boundaries in process' note, Lounge plans.
2. Maps: Canada + world boundary check (US only today) · hook Canada/world keys into planner / Info Finder / Kit (still the old canada-bounds file) · BIG JOB all-states closures + 2-fer/3-fer overlaps · closure watcher: Forest Service, WMAs, Corps · use data/state-gis.json elsewhere (WAIT for Fable to finish it) · Map Rep Tool Box for the world + new-park search (maybe own repo) · US-11852 Beaver Creek wrong join · KY PVA table per county · POTA trails around KY list.
3. Lounges + Logger: Activators Lounge LAUNCH (menu + search + toolbox + PUBLIC list + the See More menu-description fix in the same pass) · Spot Me + QRM warning to every spot button after his beta · CAT tune in the public Hunters Lounge (after the remote features settle) · website KPC Logger: NEW TO ME from the hunter file, county + auto comment (done Oct 24) · On The Air Now: mark spots new to you · When Is POTA Busiest (once counted) · JS8 in the DIGI tab.
4. App: TEST 0.7.0 (new modes on the FT-710, voice keyer, CW key line, Fable's 0.6.11 decoder + remote sound) · bump app/version.json after the build · waiting on reports: 0.7 kHz SSB jump, Tailscale remote, IC-7300 lock-up · not built: JS8, QRM warning, app/hunters.json website job, PSKReporter/WSJT-X spot sources, DXCC table, live log to Log4OM/HRD/N3FJP/DXKeeper, event checklists, rotator, SWR guard, one-tap update, Fox & Hound, WSJT-X Improved extras, PC hot keys · later as planned: contest scoring, KPC27 scorer, POTA + LoTW upload, guest pass, IC-705 WiFi / Flex / OmniRig, KPC Lite, iPhone, opt-in usage counts.
5. Bots: ~~Facebook question helper step 2 (auto-reply)~~ DONE Oct 24 (needs pages_manage_engagement on the token, setup-todo #6) · Discord: decide Founders (Administrator) vs a smaller KPC Mod role (Brandon) · keep 'email only for real issues'.
6. Campout & events: KPC27 challenges scorer (needs the rules from Brandon first) · contest + QSO party scoring (shared with the app) · more videos when wanted (music credit only on YouTube).
