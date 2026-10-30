# CHAT 4 INBOX (app, Opus / Fable)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- **FROM HQ (Oct 29 7:52 PM, Brandon 7:50 PM):** chat 10 is collecting a readiness table of every bot that feeds the waiting room. For YOUR bots: is it ready to run and save into the waiting room (held, not live)? What is missing? Answer chat 10 under its '## OPEN' (and REPORT TO HQ).
- **FROM HQ (Oct 29 7:35 PM) TONIGHT 12:05-12:50 AM CDT: WEBSITE REPO CLEANUP (Brandon 7:27 PM):** push NOTHING to KPC-Links between 12:00 and 1:00 AM; HQ pauses its bots, removes `.claude/lookup/` + `data/fers/` from the history, force-pushes, turns the bots back on. After 1 AM your next session MUST start with `git fetch && git reset --hard origin/main` (house rule already); any local unpushed work: push it BEFORE midnight. Branch check: reply in REPORT TO HQ which of YOUR KPC-Links branches are still needed (kept + rewritten) and which can be deleted.
- **FROM HQ (Oct 29 12:58 PM) FREEZE, FINAL (Brandon 12:56 PM: 'nothing changes on website besides the bots that do auto updates...once map is rebuilt we make one mass dump...finish rule g...and work on other tasks'):** chat 3's Rule G step 3 (live 12:42) is allowed THIS ONE TIME. From now on: NO website changes except the bots that already auto-update. Rule Sheet G's new output (chat 2's key + grades + queue, chat 3's further drawing, the held parking points, new outlines, documents) is STAGED (branch or hold files), NOT live, and goes out in ONE MASS DUMP after the map is rebuilt, on Brandon's GO. Work = finish Rule G + the side tasks (Fable's list, parking, documents).
- **FROM HQ (Oct 29 12:30 PM) FREEZE EXCEPTIONS (Brandon 12:28 PM OK):** (1) the KENTUCKY HUNT NOTES / closures go live as planned (wired through the waiting room Sat Oct 31, before Lake Barkley's hunt Mon Nov 2); (2) bots that ALREADY update the website keep running as they are (park alerts / closure notices, the access-parking pilot). Everything else new waits for Rule Sheet G.
- **FROM HQ (Oct 29 12:28 PM) WEBSITE FREEZE (Brandon 12:27 PM: 'Nothing gets added or changed on website till this is done...side mission lower fables list, collect parking info, documents. We focus on that.'):** until Rule Sheet G is built (chat 2 key + queue, chat 3 drawing, monthly loop), NOTHING new is added to or changed on the website (pages, cards, Finder regions, data the site reads). Work = Rule Sheet G + the side missions: shrink Fable's list, COLLECT parking points, COLLECT documents (into KPC-Data / hold files, not onto the site). Bots already running keep running as they are until HQ says otherwise (Brandon ruling pending on KY hunt notes).
- FROM CHAT 10 (Oct 29 7:55 AM): the access-points pilot is live (waiting room on, Ohio proof run passed): your 4.1 (rebuild the app park packs) can start when Brandon says.
- HQ (Oct 29 7:38 AM, Brandon): YOUR TASK LIST + ORDER is now `.claude/inbox/MASTER-PLAN.md` (section CHAT 4). Work it in that order and TICK each task there when done ([x] + time + one-line result). Older items below stay as detail.
- FROM CHAT 10 (Oct 28 11:45 AM): REBUILD THE APP PACKS for OK ID NY TN MO ND WI AR WA OR PA MI MN after KPC-Data's kpc-us-access run of Oct 28 ~11:40 AM lands (data/access/US-XX.json): that run drops access points tied by NAME more than 100 km from their park (two Robert Moses parks sharing 27 points 502 km apart, Copan WMA, Lost Nation, Beaver Creek WMA…). The packs built before it carry the wrong NEXT PARK 🧭 points; Kentucky's pack is not affected (KY pins are hand-checked).
- Brandon tests on the radio today (Fable's list in ft8-app.md / KPC_AppReadiness_Fable.md): read his builders' report when it comes.

- TO DO (Brandon Oct 28 7:07 AM: 'this is to do...make notes'): TRIP PLANNER + OVERLAP FINDER as screens in the app (plan in ft8-app.md 'TRIP PLANNER + OVERLAP FINDER IN THE APP'). After his radio test fixes; members-only or not is decided when it's built (Brandon 7:09 AM).
- TO DO (later): iPhone: browser phone remote first (plan in ft8-app.md 'IPHONE PLAN').

## NEEDS BRANDON
- ANSWERED (Brandon Oct 28 7:09 AM): a to-do for LATER, decided when it's built. WAS: Overlap Finder in the app: the overlap list is members-only on the website, the app is public: show it in the app or not? (only matters when we build it, later)

## DONE
- Oct 28 7 AM: iPhone plan written (5 points, ft8-app.md 'IPHONE PLAN'): browser remote first (HTTPS via Tailscale cert), real iOS app = Swift plugins + $99/yr + macOS runner, no USB CAT on iOS. Nothing built.
- Oct 28 5 AM: KPC LITE on kpc-app main (20ffc2b) after the 0.7.7 nightly landed; rides the Oct 29 3:17 AM build (KPC-Lite-test.apk beside KPC-test.apk). Brandon kept FT8 + FT4 in Lite. 198 checks. app/version.json → 0.7.7.

## REPORT TO HQ (newest first)
- Oct 28 7 AM (chat 4): also wrote the TRIP PLANNER + OVERLAP FINDER in the app plan (ft8-app.md, from ideas.md LATER item 2); one Brandon ruling parked under NEEDS BRANDON.
- Oct 28 7 AM (chat 4): iPhone plan in ft8-app.md; recommend browser remote first, iOS Lite only if members ask. Radio-test item still open.
- Oct 28 5 AM (chat 4): Lite merged to main, ships in the Oct 29 nightly; Lite = logger, spots, FT8/FT4, radio, map, voice keyer (out: other digi modes, APRS, remote, park packs, uploads); own app id, installs beside the full app. 0.7.7 build is on test-build; version.json bumped. Waiting on Brandon's radio test report.
