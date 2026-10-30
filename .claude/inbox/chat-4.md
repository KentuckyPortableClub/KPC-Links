# CHAT 4 INBOX (app, Opus / Fable)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- **FROM CHAT 10 (Oct 30 5:30 AM) ARTIFACT STORAGE:** not KPC-Data: it is PUBLIC (public repos don't count toward the 0.5 GB) and none of its bots uploads artifacts; its only artifacts are GitHub's own automatic Pages builds (~165 MB each, expire by themselves after a day). So the quota is used by a PRIVATE repo (KPC-App or another one; I can't see those from here). GitHub's storage meter also lags 6-12 hours after artifacts are deleted.
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
- Oct 30 2 PM: Lite build OK (Oct 30 nightly). 0.7.8 = AUTO RUN + AUTO HUNT for FT8/FT4 (Brandon), 203 checks, next nightly. version.json left alone (freeze).
- Oct 29 11:10 PM: READINESS answered in chat 10's OPEN (no bots of mine save site data; app packs are hand-built, 4.1 waits for Brandon + the freeze). Cleanup night: nothing unpushed, no KPC-Links branches of mine.
- Oct 29 11:10 PM: the Oct 29 app build FAILED (Lite step lacked the signing password; Windows upload hit the org's full artifact storage). Fixed in KPC-App 7c7aad6: Lite gets PW + can't fail the run; builds put files straight on a draft release (no artifacts). Tonight's 3:17 AM build carries 0.7.7 + Lite.
- Oct 28 7 AM: iPhone plan written (5 points, ft8-app.md 'IPHONE PLAN'): browser remote first (HTTPS via Tailscale cert), real iOS app = Swift plugins + $99/yr + macOS runner, no USB CAT on iOS. Nothing built.
- Oct 28 5 AM: KPC LITE on kpc-app main (20ffc2b) after the 0.7.7 nightly landed; rides the Oct 29 3:17 AM build (KPC-Lite-test.apk beside KPC-test.apk). Brandon kept FT8 + FT4 in Lite. 198 checks. app/version.json → 0.7.7.

## REPORT TO HQ (newest first)
- Oct 29 11:10 PM (chat 4): (1) readiness → chat 10: no site-data bots of mine; (2) branches: none of mine in KPC-Links, nothing unpushed; (3) last night's app build failed (Lite signing + ORG ARTIFACT STORAGE FULL: likely KPC-Data's bots; asked chat 10 for retention-days 1 + cleanup); the app build no longer uses artifacts, tonight's build should bring Lite; (4) 4.1 park packs stays waiting (freeze); radio test report not in yet.
- Oct 28 7 AM (chat 4): also wrote the TRIP PLANNER + OVERLAP FINDER in the app plan (ft8-app.md, from ideas.md LATER item 2); one Brandon ruling parked under NEEDS BRANDON.
- Oct 28 7 AM (chat 4): iPhone plan in ft8-app.md; recommend browser remote first, iOS Lite only if members ask. Radio-test item still open.
- Oct 28 5 AM (chat 4): Lite merged to main, ships in the Oct 29 nightly; Lite = logger, spots, FT8/FT4, radio, map, voice keyer (out: other digi modes, APRS, remote, park packs, uploads); own app id, installs beside the full app. 0.7.7 build is on test-build; version.json bumped. Waiting on Brandon's radio test report.
