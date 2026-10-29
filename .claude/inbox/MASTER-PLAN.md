# MASTER PLAN + TASK LIST (HQ, Brandon's plan Oct 29 7:31 AM)
Every chat: when you FINISH a task below, change its `[ ]` to `[x]` and add the date/time + one short result. When you START one, `[~]`. New tasks only through HQ. HQ reads this file for every status report.

## THE PLAN (Brandon, in order)
1. Boundary accuracy: chats 2 + 3 (3 m close-ups everywhere, Canada re-saved at 3 m, wrong joins fixed).
2. Waiting room finished → chat 8 breaks it → Brandon's GO → PILOT = access/parking bot → wire the other website bots ONE AT A TIME → start the rest of the bots, repair as needed.
3. Chat 8: missing boundaries + name-mismatch report → Fable reviews → chats do Fable's recommendations.
4. Rerun ALL 2-fers for accuracy once 1-3 are done (through the waiting room).
5. Harvester done → more boundaries (each new outline → the small-batch 2-fer list).
6. Hunt closures = the yearly PDF guides → CHECKED lists (chat 8 reads, Brandon checks, expire at season end). KY FIRST (quota hunts start Nov 6-8).

## CHAT 2 (2-fer line + keys)
- [ ] 2.1 Wrong 'same land' joins: multipart fix + Canada layer-id fix + NB zones: reruns of the affected areas (NS NB MB/SK NY AB/BC NE NC), counts after (results ~9 AM)
- [ ] 2.2 Finish stopped areas: Utah (150 rows), Ontario (4 water), AB/BC (9 water), Mississippi held rows
- [ ] 2.3 New England: the 22 Appalachian Trail rows filed under ME (found by the Overlap Finder / packs?)
- [ ] 2.4 Canada outlines re-saved at ~3 m (measure 2 provinces first, compressed, stop if > ~+40 MB)
- [ ] 2.5 Confirm in writing which line passes read full-detail outlines live (US 2-fer math accuracy)
- [ ] 2.6 Virginia key double-counts tracts (Dragon Run 2x, from chat 11)
- [ ] 2.7 Fix the parks with a far outline piece named by the access run (NY US-10284…, MN, PA, OR, OK, ND, MO, MI)
- [ ] 2.8 Our own water copy near parks (release files, size first) AFTER the US queue
- [ ] 2.9 LATER: monthly 2-fer rerun with a changes list; keys change-check; small-batch list for new outlines (built? confirm)
- [ ] 2.10 Rerun ALL 2-fers (plan step 4)

## CHAT 3 (Overlap Finder / site maps)
- [ ] 3.1 3 m close-ups on every 2-fer map (US + Canada + KY), tested at full zoom + phone width, < 1 s extra
- [ ] 3.2 Add each area chat 8 passes (members, BETA); keep the 'hide' list for rows chat 8 drops
- [ ] 3.3 LATER (GO needed): owners / % water info line on the card; 'help us check' for the review list

## CHAT 8 (research desk) — IN THIS ORDER (Brandon: 'stick to the plan'; 8.5, 8.6, 8.8 moved to chat 11)
- [~] 8.1 (Oct 29 ~8:10 AM: graded neb READY, southcentral READY except NE, SK/PE/NL/NT fine, NS/NB/MB wait for the Canada rerun; Pacific, mtsw, caon, caabbc stopped) Area checks as they land (blocks chat 3): Midwest rerun, New England, CO/WY, ID/MT, Quebec, North, the READY states inside PART areas, and every rerun from 2.1/2.2
- [x] 8.2 (Oct 29 9:00 AM: list written, 4 closed areas + notes, Brandon checks 3 things; KPC_KY_HuntList_desk.md) KENTUCKY HUNT-CLOSURE LIST from the yearly guide PDF (KDFWR hunting guide quota tables): data/closures/hunt-lists/US-KY-2026-27.json, expires end of Feb; Brandon checks it (season starts Nov 6-8)
- [ ] 8.3 Missing boundaries + name-mismatch report (US + Canada) for FABLE to review
- [x] 8.4 NOT SURE groups (871 by reason: 4 fixable causes ~690 rows, KPC_NotSure_Groups_desk.md) + Nova Scotia SOLVED (label collision across two NS layers, KPC_NS_WrongJoins_desk.md)
- [x] 8.5 Waiting room BROKEN + 2 retests by chat 8 (Oct 29 ~7:45-7:55 AM): all 7 holes closed, 4 small gaps listed; 'fine for the access-points pilot' (KPC_WaitingRoom_Break_desk.md)
- [~] 8.6 Known 2-fer pairs, 3-5 per state (G7): chat 8 already started it, stays with chat 8
- [x] 8.7 State parks on federal land: report + rule R-SF (KPC_StateInFederal_Overlays_desk.md): 4 GREY AREAS for Brandon
- [→] 8.8 MOVED to chat 11 (11.5)
- [ ] 8.12 LAYERED-LAND LIST (Brandon Oct 29 7:48 AM: 'we need to track all these in case we have to review them'): one file .claude/build/research/KPC_LayeredLand_List_desk.md (+ data/fers/layered.json for the bots) of EVERY pair where the federal agency OWNS the land and the state MANAGES it (and the reverse), per pair: both POTA numbers + POTA's NAME and TYPE for each (does POTA call it a state WMA / state park or a federal unit?), owner + manager from PAD-US Own_/Mang_ fields at the patch, the agency evidence (lease / cooperative agreement page), live / not sure in the line, last checked. KY first (Redbird, Pioneer Weapons, Beaver Creek WMAs on Daniel Boone NF; Kentucky Lake WMA on TVA land; Corps-lake WMAs: Green River Lake, Grayson Lake, Paintsville Lake), then GA (Cohutta WMA on Chattahoochee NF), TN (Cherokee WMA on Cherokee NF), AR (WMAs on Ozark NF), then every state. Kept current: the line adds a row whenever it finds a new layered pair.
- [ ] 8.9 Agency own-land records (real private tracts) + official water's-edge sources (no OpenStreetMap)
- [ ] 8.10 Source Book 2 (Southeast next, then the rest); hunt sources per state
- [ ] 8.11 Other states' hunt PDF lists (or chat 9 if chat 8 is too slow: HQ decides)

## CHAT 10 (bot workshop)
- [x] 10.1 (7:50 AM) done: G2 key, Fable's 3 gaps, chat 8's 2 rounds of holes, G5 stamp file (data/waiting/known/stamps.json); replay 38/38 — WAITING ROOM: G2 stable key, Fable's 3 gaps (30-km same land, .gz seen, no compact rewrite), G5 stamp file; replay still catches every flaw → 'ready to break' line to chat 8
- [~] 10.2 (7:50 AM) PILOT ON: kpc-us-access saves into data/waiting/in/, the checker promotes or holds (KPC-Data 04920e32); proof run OH 40875906766 PASSED and went live (7:55 AM); other website bots later, one at a time — PILOT the waiting room on the access/parking bot (Brandon's GO), then wire the other website bots one at a time
- [x] 10.3 (7:25 AM) table in chat-10 REPORT (26th pass) — Classification table: HIDDEN bots (run when fixed) vs WEBSITE bots (wait for the waiting room)
- [x] 10.4 (7:45 AM) truth v15 VA + IL: both gates PASS (VA agree 65, IL 91); chat 11 grades — Truth: Illinois run on the 'did you know' fix
- [x] 10.5 (7:15 AM) intake: coverage layers never READY, READY needs 3+ name matches (offline 21 -> 1); test run 40870647571 — Intake: never READY on a pin-only match (16 of 21 wrong)
- [~] 10.6 (round 14) the checked yearly hunt list is the KY rule (waits for chat 8's list + Brandon's check); one reader after chat 11's pass — Closures: use the checked yearly hunt list (8.2) as the KY rule; then one closures reader (switch off the old KY reader + fold the US one in) after a pass
- [x] 10.7 (6:55 AM) docs WV 36 -> 135 maps; docs v7 (ID viewer links) WI run 40870643848 — Documents: West Virginia rerun (run 40818621004 never landed); keep good maps
- [x] 10.8 (Oct 29 night) known-goods past the park-word filter; NL CKAN 400 handed to chat 9 — Harvester: Netherlands CKAN HTTP 400; known-goods past the park-word filter
- [x] 10.9 (Oct 29 night) detective v5: layer steps first, 'budget used up' reported — Detective: report 'budget used up', layer steps first
- [~] 10.10 state-park rows done (93%); federal rows wait for Brandon's RIDB decision — Campground: rerun after any fix; federal rows wait for Brandon's RIDB decision

## CHAT 11 (bot-output checker)
- [ ] 11.1 Grade every 'grade me' line as it lands (truth IL, hours, closures, intake, docs WV, campground)
- [ ] 11.2 Grade the waiting room's first week once it is on
- [-] 11.3 NOT NEEDED: chat 8 already broke + retested it (8.5). WAS: BREAK the waiting room when chat 10 writes 'ready to break': try to make bad files pass + good files hold; grey areas to HQ. Your OK = Brandon's signal for his GO
- [-] 11.4 BACK WITH CHAT 8 (8.6, already started). WAS: Known 2-fer pairs, 3-5 per state, from official maps (a mix of kinds; one actually activated where possible), stable key, into data/waiting/known/fers.json
- [ ] 11.5 (from 8.8) Review list data/fers/review-all.md: the 148 NOT SURE + 115 'water map weak' rows first, biggest first (LIVE / DROP / still NOT SURE + why / for members); POTA-history hints last

## CHAT 9 (data adds)
- [ ] 9.1 Campground points for Land Between the Lakes + KY state parks (Camp & Activate's 20 missing)
- [ ] 9.2 Storage tidy of its own folders
- [ ] 9.3 River-layer test v3 (Park Service / Fish & Wildlife control points)
- [ ] 9.4 STANDBY: other states' hunt PDFs if HQ moves 8.11 here

## CHAT 4 (app) — waits for Brandon
- [ ] 4.1 Rebuild the app park packs for the 13 states (after the access pilot)
- [ ] 4.2 Brandon's radio test + builders' report

## BRANDON
- [ ] B.1 Decide RIDB / NPS keyed APIs (allow / block both / leave as is)
- [x] B.2 GO given Oct 29 7:42 AM: waiting room ON for the access/parking pilot
- [ ] B.3 Check the KY hunt list (8.2)
- [ ] B.4 Check the Park Service key result on the check-up page
- [-] B.5 Permission emails: PARKED (Brandon Oct 29: not now)

## HQ
- [ ] H.1 Next scheduled Fable session: attach KPC-Data (last night's could not save there)
- [ ] H.2 Status reports from this file on request; Sunday members' update; Sunday storage check
