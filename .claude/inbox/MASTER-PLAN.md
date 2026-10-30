# MASTER PLAN + TASK LIST (HQ, Brandon's plan Oct 29 7:31 AM)
Every chat: when you FINISH a task below, change its `[ ]` to `[x]` and add the date/time + one short result. When you START one, `[~]`. New tasks only through HQ. HQ reads this file for every status report.

## SCOPE (Brandon Oct 29 8:36 AM, see CLAUDE.md 'SCOPE'): KY = everything; rest of US + Canada = boundaries, official docs/maps, 2-fers, parking/access points, trails; world = boundaries + docs/maps only; OUTSIDE KY no hours / fees / closures / camping.

## WEBSITE FREEZE (Brandon Oct 29 12:27 PM): nothing added/changed on the website until Rule Sheet G is done. Focus: Rule Sheet G + side missions (shrink Fable's list, collect parking, collect documents). EXCEPTIONS (Brandon 12:28 PM): KY hunt notes/closures go live Sat Oct 31; bots already updating the site keep running.

## FREEZE EASED (Brandon Oct 30 9:14 AM: 'release the hold on anything you think we should'): staged work now goes out IN SMALL STEPS, each tested, instead of one mass dump. Still held: posts (closure posts off), menu / new public pages (HOLD RULE: Brandon's GO), GIS hunter + world finder changes (Nov 6), the old-key Overlap Finder batch (stage-g = RETIRED, replaced by the new-key rerun).
## (eased Oct 30 9:14 AM) FINAL FREEZE (Brandon 12:56 PM): only auto-update bots touch the site. Rule G + collected data are STAGED and go out in ONE MASS DUMP after the map rebuild (Brandon's GO).
## FABLE'S LIST, HOW (HQ 12:58 PM): (1) chats 2/9/11 finish the side work (name matches, new state layers, lake parks); (2) Rule G key built (R-G1..G6 + official-record-at-any-distance often settles 'pin inside a bigger area'); (3) chat 8 re-runs its missing-boundaries list on the NEW key; (4) only what is left goes to ONE Fable session with KPC-Data attached (H.1).

## RELEASE GO GIVEN (Brandon 7:48 PM 'release the mckraken'). ## RELEASE (Brandon 3:02 PM): R-G8 key rebuild → chat 8 confirms + chat 11 approves → new keys to the site + every APPROVED waiting-room item (incl. parking points) in one batch; the rest stays held/frozen.

## 2-FER RERUN ORDER (Brandon 3:13 PM: 'run states with no parks on fable list 1st'): wave 1 = states with 0 open Fable-list parks: KY (own key), DC, NJ, OH, PA, SD; wave 2 = 1-3 open: MN IA RI VA HI ME CO NM AZ; then the rest from FEWEST open parks up, so each state runs after R-G7 has cleared it. (Open count per state, current key: NV 68, MS 51, ND 42, ID 38, OK 31, AR 22, WA 20, NC 19, KS 18, OR 18, IN 17, UT 17, MI 16, VT 14, WI 12, WY 11, TX 11, AL 11, FL 10 … 1.) Canada: same idea once its open list is counted.
## FABLE LIST ORDER (Brandon 3:15 PM): states LOW to HIGH: IA 1, MN 1, RI 1, CO 2, HI 2, ME 2, VA 2, AZ 3, NM 3, CT 4, DE 4, MO 4, MT 4, SC 4, IL 5, LA 5, MA 5, MD 5, CA 6, NH 7, WV 7, NY 8, TN 8, AK 9, GA 9, NE 9, FL 10, AL 11, TX 11, WY 11, WI 12, VT 14, MI 16, IN 17, UT 17, KS 18, OR 18, NC 19, WA 20, AR 22, OK 31, ID 38, ND 42, MS 51, NV 68. Chat 3 / chat 8 alternate down the list.
## (superseded split by size) FABLE LIST, MORE HANDS (Brandon 3:13 PM: 'work on fable list put more man power on it if needed'): 566 open parks in 45 states is too much for one chat. R-G7 step 3 (find the official map) is now split: CHAT 8 = NV, MS, ND, ID, OK, AR, WA, NC, KS, OR, IN (the big ones, biggest first); CHAT 3 (frozen site work, so free) = UT, MI, VT, WI, WY, TX, AL, FL, GA, AK, NE, NY, TN, WV, NH and every state with 1-6 open; both file their own SHARED LOOK-UP BOT requests and send per-state lists to chat 2. CHAT 10 (Fable) = R-G7 steps 4-5 HARD cases chat 2 cannot trace (ownership cuts, units inside bigger shapes) as they appear, so the true Fable leftovers get done in-line instead of waiting for a separate session. Chat 11 keeps step 6 yes/no.

## FABLE BOOK ORDER (Brandon 5:28 PM: 'Once fable book been gone through opus gives it a shot and then fable final review ....then move on to Canada'): (1) chats 3 + 8 (+2/9/11) work every US state in the Fable file to 'STATE DONE'; (2) an OPUS pass on every row still 'pin, no source' / grey area (chat 10 on Opus, all files attached), same Rule G; (3) FABLE does the FINAL review of what is left (one session, KPC-Links + KPC-Data attached = H.1); (4) THEN Canada's list goes through the same steps. Canada addresses (chat 8) can be collected meanwhile; no Canada R-G7 tracing until the US is through step 3.

## FABLE'S METHOD (Oct 29 6:20 PM, Brandon GO): R-G9 picture maps = Approximate only (tool later, chat 10); R-G10 'why not' tags; R-G11 pin-outside split (chat 2 → chat 11); P-1 size units + rebuild (chat 2); P-2 polygons before pages (chat 9); P-3 address+parcel by county (chats 8, 3); P-4 by agency; P-5 city/county parks. Fable returns for the FINAL review.

## CANADA (Fable, Oct 29 7:05 PM, Brandon 6:56 PM): Rule Sheet G, Canada (R-GC1..R-GC8) + starter layer list in mapping.md; chat 9 probes + P-2, chat 2 wires + Rule G pieces into the Canada key (staged); tracing waits for the US passes.

## DONE Oct 29 11:53 PM-12:00 AM CDT: WEBSITE REPO CLEANUP (HQ): history rewritten without .claude/lookup/, data/fers/, chat 2's key-preview files (local pack 690 → 562 MB, -128 MB; main's files identical to before, checked file by file); 18 merged / owner-OK branches deleted (37 → 19; kept: main, bot-state, chat9-world, stage-g, stage-shapes, key-speed, namematch-test, owned-land-ky, stepb, note-world-tool, claude-shot, claude-trail-fetch, zz-*); all 66 bots paused and re-enabled; Discord relay ran OK after. GitHub's own size (686 MB) only drops after GitHub cleans unreferenced data (days; old pull-request refs may keep some; GitHub support can purge). Every chat: next session starts with git fetch && git reset --hard origin/main.
## (old plan) TONIGHT: WEBSITE REPO CLEANUP (Brandon 7:27 PM 'Yes tonight'; HQ runs it; storage = HQ's job)
- WINDOW: 12:05-12:50 AM CDT (05:05-05:50 UTC) = the quietest hour in the bot schedule (no 6-hourly / nightly job; only the every-15/30/hour bots: hunters, band alerts, POTA Discord, bot queue, FB comments, Discord watch / relay, boards).
- BEFORE: chat 10's look-up move to KPC-Data DONE (the folder stops growing); chats push NOTHING to KPC-Links 12:00-1:00 AM.
- STEPS (HQ): (1) disable every KPC-Links workflow (gh workflow disable; list saved) and wait for running ones to finish; (2) full mirror clone; (3) git filter-repo removes ONLY `.claude/lookup/`, `data/fers/` (moved to KPC-Data Oct 27) and `.claude/build/preview/key-preview*.json` (chat 2's temp preview, 7.8 MB) from ALL history; chat 2's 7 branches (chat2-*) are all OK to DELETE (chat 2, 7:45 PM); chat 11 has none; (4) delete the 13 MERGED branches + the stale Oct 14-21 probe branches (zz-*, probe, probe2, claude-shot, claude-trail-fetch, note-email-topics) after chat 2/9 confirm; KEEP main, bot-state, stage-g, stage-shapes, chat2-fable-parts, chat2-ky-refine, chat9-world, key-speed, namematch-test, owned-land-ky, stepb, note-world-tool (rewritten, not deleted); (5) force-push all kept refs; (6) re-enable exactly the saved list; (7) check the site deploys + one bot run; (8) sizes before/after to Brandon. GitHub may take days to show the smaller size (its own clean-up).
- EXPECTED: about 130 MB out of history (look-up 68 MB + old 2-fer results 63 MB) + whatever the dropped branches held.

## FABLE AUDIT (Oct 30 6:55 AM): built + working = 2-fer line A1-A6, Step 0, BOT A/D/E, hunter step A, tiers, limits plan, research-bot fixes. Gaps sent: chat 2 (nightly key rebuild, outline refresh never fired, BOT F reads 'STATE XX DONE', BOT C line, owned land outside KY, B1/B2/B5/B7, Canada why-not), chat 10 (detective 'gaps' off, discovery rerun-or-retire; hunter step B + INSPIRE CSW + page reader ON HOLD to Nov 6: Brandon 6:45 AM, Fable's tuning runs a week untouched), chat 9 (missing Canada layers), chat 3 (split locations.json, staged), chats 3/8 ('STATE XX DONE' lines).

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
- [ ] 2.11 SCOPE: NO world 2-fers (stages off); world = outlines only
- [ ] 2.9 LATER: monthly 2-fer rerun with a changes list; keys change-check; small-batch list for new outlines (built? confirm)
- [ ] 2.10 Rerun ALL 2-fers (plan step 4): Brandon 3:09 PM: old-key results QUARANTINED (water/parcel/known answers kept), rerun on the NEW key starts when chat 8 + chat 11 clear it, areas 1/3 the old size, Finder keeps the old BETA list until each new area passes

## CHAT 3 (Overlap Finder / site maps)
- [x] 3.1 3 m close-ups on every 2-fer map (US + Canada + KY), tested at full zoom + phone width, < 1 s extra · Oct 29 7:55 AM: KPCB.closeUp re-reads live outlines near the spot at 0.00003 deg (1.5 s cap, giants skipped); KY + canada-bounds use the 2-fer 'lines'; live US server untested from here (Brandon to eyeball one non-KY spot)
- [ ] 3.2 Add each area chat 8 passes (members, BETA); keep the 'hide' list for rows chat 8 drops · STANDING: 34 states on as of Oct 29 5:40 AM, 14 pairs hidden
- [x] 3.4 SCOPE: HIDE campground data outside Kentucky on every page/tool (Lounge campground tab/cards, park cards, planner, Kit): keep the files, don't show them; closures outside KY disappear when chat 5 clears them · Oct 29 8:55 AM: Campgrounds page = Kentucky only (KY_ONLY switch in kpc-campgrounds-us.js, no picker / NEAR ME / ?state=), Kit + park sheet outside KY say 'Campground details are shown for Kentucky parks only for now', US planner shows no federal campgrounds outside KY; files untouched
- [ ] 3.3 LATER (GO needed): owners / % water info line on the card; 'help us check' for the review list

## CHAT 8 (research desk) — IN THIS ORDER (Brandon: 'stick to the plan'; 8.5, 8.6, 8.8 moved to chat 11)
- [~] 8.1 (Oct 29 ~8:10 AM: graded neb READY, southcentral READY except NE, SK/PE/NL/NT fine, NS/NB/MB wait for the Canada rerun; Pacific, mtsw, caon, caabbc stopped) Area checks as they land (blocks chat 3): Midwest rerun, New England, CO/WY, ID/MT, Quebec, North, the READY states inside PART areas, and every rerun from 2.1/2.2
- [x] 8.2 (Oct 29 9:00 AM: list written, 4 closed areas + notes, Brandon checks 3 things; KPC_KY_HuntList_desk.md) KENTUCKY HUNT-CLOSURE LIST from the yearly guide PDF (KDFWR hunting guide quota tables): data/closures/hunt-lists/US-KY-2026-27.json, expires end of Feb; Brandon checks it (season starts Nov 6-8)
- [x] 8.3 (Oct 29 8:55 AM: one-page index KPC_MissingBoundaries_ForFable_desk.md pointing to the 5 detailed reports) Missing boundaries + name-mismatch report (US + Canada) for FABLE to review
- [x] 8.4 NOT SURE groups (871 by reason: 4 fixable causes ~690 rows, KPC_NotSure_Groups_desk.md) + Nova Scotia SOLVED (label collision across two NS layers, KPC_NS_WrongJoins_desk.md)
- [x] 8.5 Waiting room BROKEN + 2 retests by chat 8 (Oct 29 ~7:45-7:55 AM): all 7 holes closed, 4 small gaps listed; 'fine for the access-points pilot' (KPC_WaitingRoom_Break_desk.md)
- [x] 8.6 (Oct 29 12:30 PM: 231 pairs proposed, 49 states, KPC_KnownPairs_Proposed_desk.md; needs map spot check) Known 2-fer pairs, 3-5 per state (G7): chat 8 already started it, stays with chat 8
- [x] 8.7 State parks on federal land: report + rule R-SF (KPC_StateInFederal_Overlays_desk.md): 4 GREY AREAS for Brandon
- [→] 8.8 MOVED to chat 11 (11.5)
- [x] 8.12 (Oct 29 9:20 AM: KPC_LayeredLand_List_desk.md + layered.json, 932 pairs; evidence columns need a bot pass) LAYERED-LAND LIST (Brandon Oct 29 7:48 AM: 'we need to track all these in case we have to review them'): one file .claude/build/research/KPC_LayeredLand_List_desk.md (+ data/fers/layered.json for the bots) of EVERY pair where the federal agency OWNS the land and the state MANAGES it (and the reverse), per pair: both POTA numbers + POTA's NAME and TYPE for each (does POTA call it a state WMA / state park or a federal unit?), owner + manager from PAD-US Own_/Mang_ fields at the patch, the agency evidence (lease / cooperative agreement page), live / not sure in the line, last checked. BOTH sides must be POTA PARKS (Brandon 7:54 AM: 'we compare POTA parks to POTA parks'): a federal POTA park (e.g. a national forest) + a state POTA park (e.g. a state WMA) on that federal land = 2-fer IN THE OVERLAP. A WMA on Corps / TVA land with no federal POTA number = NOT a pair (one park only). KY first (Redbird, Pioneer Weapons, Beaver Creek WMAs x Daniel Boone NF), then GA (Cohutta WMA x Chattahoochee NF), TN (Cherokee WMA x Cherokee NF), AR (WMAs x Ozark NF), then every state; confirm both POTA numbers before listing a pair. Kept current: the line adds a row whenever it finds a new layered pair.
- [ ] 8.9 Agency own-land records (real private tracts) + official water's-edge sources (no OpenStreetMap)
- [~] 8.10 (Oct 29 11:15 AM: KPC_SourceBook2_NothingNear_desk.md for NV MS ND + next 8 states; bot probes handed to chat 9) Source Book 2 (Southeast next, then the rest): ONLY boundaries / own-land / hydrography / official docs + maps / parking-access / trails items (no hunt, closure, hours, camping items outside KY: SCOPE)
- [-] 8.11 DROPPED by SCOPE (no closures outside KY)

## CHAT 10 (bot workshop)
- [ ] 10.L (Brandon 11:59 AM GO) SHARED LOOK-UP BOT: any chat files a request, jobs run side by side, real browser + screenshots, answers to the asker's inbox
- [ ] 10.W (Brandon 9:46 AM) WIRING PACE: next bot is wired after 3 CLEAN DAYS of the one before (pilot clean → Sat Oct 31), still one at a time: KY closures first, then documents, hours, campground info
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

## CHAT 5 (bots / Discord / Facebook)
- [x] 5.1 (DONE Oct 29 8:50 AM, chat 5: both timers off, script stops unless FORCE_RUN, 177 uc- items cleared; KY pa-/hc- 40 kept) SCOPE: turn OFF closures on park cards OUTSIDE Kentucky (US park closures bot + the Georgia source): stop the non-KY closure sources, clear their items from the live closures file so cards outside KY show none; Kentucky's stay

## CHAT 11 (bot-output checker)
- [ ] 11.1 Grade every 'grade me' line as it lands (truth IL, hours, closures, intake, docs WV, campground) — 8:30 AM: truth v15 VA PASS / IL FAIL (new junk class), hours v11 FAIL (kept rows), intake 8 READY (3 junk) FAIL; docs WV v6/v7 + campground still owed; ongoing
- [ ] 11.2 Grade the waiting room's first week once it is on — started 8:30 AM: OH access PASS agrees with my independent count (0 far, 0 outside); week runs to Nov 5
- [-] 11.3 NOT NEEDED: chat 8 already broke + retested it (8.5). WAS: BREAK the waiting room when chat 10 writes 'ready to break': try to make bad files pass + good files hold; grey areas to HQ. Your OK = Brandon's signal for his GO
- [-] 11.4 BACK WITH CHAT 8 (8.6, already started). WAS: Known 2-fer pairs, 3-5 per state, from official maps (a mix of kinds; one actually activated where possible), stable key, into data/waiting/known/fers.json
- [x] 11.6 (9:40 AM, report KPC_Site_ScopeCheck_Oct29_desk.md) 72 loads guest+member x 390+1280: camping hidden outside KY PASS; ONE leftover: the closures panel still renders text for non-KY parks ('Checked: California State Parks' / 'We do not watch closures in TN yet') -> chat 3 + chat 5; 3 wording leftovers -> chat 3; health clean (0 errors, 0 scroll, notices + lock OK); runner link check 40885942620 reads next inbox
- [ ] 11.5 (from 8.8) Review list data/fers/review-all.md: the 148 NOT SURE + 115 'water map weak' rows first, biggest first (LIVE / DROP / still NOT SURE + why / for members); POTA-history hints last

## CHAT 9 (data adds)
- [ ] 9.K (Brandon 9:49 AM GO) ONE keyed pull of missing parking + 4 KY camps → HOLD file → chat 11 accuracy check (11.K) → Brandon GO → live
- [~] 9.1 (Oct 29 8:45 AM: 14 of 18 rows placed: 8 from recreation.gov records, 4 WMA + Kingdom Come + Otter Creek from the agencies' own entrance pins (precision 'entrance'); Turkey Bay pin added; keyed NPS/RIDB look-up CANCELLED (not approved), 4 left: Houchin Ferry, Breaks, Fenton, LBL self-service x10; LBL self-service x10 + Fenton, Houchin Ferry, Breaks left: NPS API + RIDB look-up in run 40884335904) Campground points for Land Between the Lakes + KY state parks (Camp & Activate's 20 missing)
- [x] 9.2 (Oct 29 5:10 AM: probe folder 1.2 MB to 16 KB, old rounds kept in git history; KPC-Data writes ~80 KB) Storage tidy of its own folders
- [x] 9.3 (Oct 29 10:55 AM: v3 done: FWS solid with auto controls; NPS tracts lack NERI/BISO entirely; Ohio nolakes keeps a leased lake; to chat 8 for grading) River-layer test v3 (Park Service / Fish & Wildlife control points)
- [-] 9.4 DROPPED by SCOPE
- [~] 9.5 (Oct 29 11:20 AM: keyed pull DONE, HOLD file with 2,818 lead points for 771 parks, chat 11 grading; Manitoba entry points added) (Oct 29 10:55 AM: step 2 ONE keyed pull running in KPC-Data (HOLD file, chat 11 checks); access layers found: Parks Canada Facilities points, Manitoba Waterbody Entry Points, Ontario fishing access, NMDGF fishing access, LDWF launches, MARIS rec facilities: details in probe SB2) (Oct 29 9:55 AM: step 1 MISSING report done, .claude/build/research/PARKING_Missing_Report.md; step 2 waits on HQ GO; layer search re-sent) (Oct 29 8:45 AM: first search running for KS LA NM AZ AK MS HI + Canada MB NB NT NU PE NS YT NL + Parks Canada (these have 0-50 access points); run 40884335904) PARKING / ACCESS points: find official parking / entrance / boat-ramp layers for US states still thin AND Canada (provinces + Parks Canada); feed them to the access bot (through the waiting room)

## CHAT 4 (app) — waits for Brandon
- [ ] 4.1 Rebuild the app park packs for the 13 states (after the access pilot)
- [ ] 4.2 Brandon's radio test + builders' report

## BRANDON
- [x] B.1 RIDB / NPS keyed APIs: Oct 29 9:37 AM: missing report FIRST (chat 9) → ONE pull of missing parking + missing KY info → only recurring = NPS alerts for KY closures
- [x] B.2 GO given Oct 29 7:42 AM: waiting room ON for the access/parking pilot
- [x] B.3 Check the KY hunt list (8.2): Oct 29 9:23 AM: no closed areas, all quota hunts = notes, Tract 1 closed noticeable, state-park notice OK, no-number WMAs out; + season dates on cards (chat 3: ky-hunting.json already has them, + 2 turkey rows)
- [x] B.4 Check the Park Service key result on the check-up page (Oct 29 9:30 AM: NPS key WORKS: closures source nps-ky ok today, 8 notices read, 5 kept; KY only)
- [-] B.5 Permission emails: PARKED (Brandon Oct 29: not now)

## SHRINK FABLE'S LIST (Brandon 10:29-10:30 AM)
- [ ] F.1 chat 8: Source Book 2 for the nothing-near states (NV MS ND first) → chat 2 reads layers → chat 11 checks
- [ ] F.2 chat 2 BOT checks all ~480 (pin / size / owner) → CAN'T TELL rows to chat 11 (Sonnet, after bot grading) → chat 2 reviews + adds SURE ones; was: chat 11: name matches (107 SURE, 140 maybes, 112+66 near-misses, 18 aliases) → YES list → chat 2 REVIEWS each, adds only the ones it also passes (Brandon 10:30)
- [ ] F.3 chat 8: Canada regrade after chat 2's rerun
- [ ] F.6 (Brandon 2:02 PM) R-G7 on 289 + 266 + 11 open parks, state by state: chat 8 step 3 official maps (files its own look-ups), chat 9 Source Book 2 probes on the shared bot, chat 2 steps 4-5 trace/cut, chat 11 step 6 yes/no, staged
- [ ] F.4 Fable gets only: the 313 'pin inside a bigger area' state parks (part-level clip method)

- [ ] F.5 (Brandon 11:17 AM) chat 9 research bot: official department maps for every lake-type POTA park FIRST → then Brandon decides the lake-outline rule

## HQ
- [ ] H.4 MASS DUMP CHECKLIST, step 1 (Brandon Oct 30 7:11 AM 'remind me when it's that time'): before chat 3 swaps the Finder / pages / locations split, HQ tells Brandon: 'switch chat 3 to OPUS now'.
- [ ] H.3 (cleanup DONE Oct 30 12 AM; FOLLOW-UP: chat 4 reports the ORG Actions ARTIFACT storage is FULL (app build failed): find which workflows upload artifacts without retention-days 1, set it, and clear old artifacts) STORAGE IS HQ'S JOB (Brandon Oct 29 7:22 PM): watch KPC-Links (687 MB) + KPC-Data (268 MB) sizes; check right after chat 10's look-up move, then every Sunday; stop any chat / bot that writes bulk files to KPC-Links; squash KPC-Data's `lookup` branch when it passes 150 MB.
- [ ] H.1 Fable review of chat 8's missing-boundaries/name report WAITS (Brandon 9:46 AM): first plan step 1 boundary fixes pushed (chat 2: far pieces, Virginia, Canada 3 m) → HQ tells Brandon → chat 8 RECHECKS its list (fixes may clear rows) → then Fable, with KPC-Data attached
- [ ] H.2 Status reports from this file on request; Sunday members' update; Sunday storage check
- chat 8 (Oct 29 1:40 PM): F.3 Canada regrade NS + NB READY and clean; MB has 3 far rows to check (see KPC_IssuesForFable_Oct29.md).

## RESEARCH LAYOUT + AUTOMATION (Oct 30 7:40 AM, Brandon 7:31 'do it all')
- DONE: Fable book split = fable/US-XX.md (45) + CA-XX.md (13), one row per park; Agency Atlas seeded (agency-atlas/US-XX, CA-XX; W-XX for world as touched).
- ORDERED: chat 2 BOT F reads 'STATE XX DONE' from the per-state file + new parks' states into the nightly rebuild; chat 10 look-up answer reuse (7 days) + new-park pipeline (hunter as tuned, no logic change before Nov 6); chat 9 writes probes into the atlas.
- WORLD (Brandon 5:51 + 7:33 AM): top 10 = 2-fers + full GIS search; W11-W15 = GIS search only; everyone else = what the hunter finds. W-XX atlas + Fable files only for the top 15.
- Oct 30 8:10 AM (Brandon 'automate all we can'): LAYER lines in fable files → chat 10 nightly collector → intake → chat 11 YES → chat 2 auto-wires into state-gis.json → nightly rebuild → hunter re-trigger. No hand copy anywhere.
- Oct 30 8:20 AM (Brandon 8:15): chat 3 is back on OPUS (mass-dump step 1 done) and OFF the Fable list; chat 8 holds all 45 US states (IA RI HI VA NM DE MT IL MA CA WV TN GA FL TX WI MI UT OR WA OK ND NV moved from chat 3).
- Oct 30 8:50 AM (Brandon 8:45): STORAGE KEEPER bot ordered (chat 10): weekly measure + safe cleanup; warns HQ at KPC-Links 650 MB / KPC-Data 400 MB; HQ's Sunday check = read its board line.
- Oct 30 11:05 AM: CAMPING OUTSIDE KY SHOWN AGAIN (Brandon Oct 30 11:05 AM: 'un hide rest of us camping information...but we won't search for closures, information etc. What is there is there and people can still submit info and reviews for rest of us'): the campground data we already HAVE for the rest of the US is shown again (Campgrounds page, Kit, park sheet, US planner), with people's submissions + reviews open for every US state (same approval as KY). NO bot refreshes or searches camping, hours, fees or closures outside KY; hours / fees / closures outside KY stay hidden. Outside-KY camping carries one line: 'Outside Kentucky we don't keep this up to date: check the agency before you go.' + the short information notice. (chat 3 un-hides; chat 10 keeps camp bots KY only)
- Oct 30 11:10 AM: CAMP BOT ON FOR THE WHOLE US (Brandon Oct 30 11:10 AM: 'turn bot on', after HQ: its changes go through the waiting room / chat 11): the campground bot(s) refresh CAMPING for every US state (KY as now; other states ONCE A WEEK, staggered, to keep runs and chat 11's checks light), every change through the waiting room → chat 11's YES. CAMPING ONLY: hours / fees / closures outside KY stay off and hidden. Pages show 'last checked <date>' on camping (replaces 'we don't keep this up to date').
- Oct 30 12:22 PM: W-2 USE UNTIL BETTER (Brandon Oct 30 12:22 PM: 'change it so we use them till we find better'): an EU compilation layer (EEA Natura 2000 / CDDA) record that matches a park by Rule G (pin inside + name tier + size) IS used now as the park's outline, grade APPROXIMATE, labelled 'EU compilation of national data' (never Official, never used by the 2-fer line as Official). The moment the country's own agency layer gives the park an Official outline, it REPLACES the EU one (same hand-back as traced picture maps). Chat 11 grades these rows by Rule G like any other (not an automatic NO).
- Oct 30 12:24 PM: WORLD OPEN (Brandon Oct 30 12:24 PM: 'I am opening the world to maps and 2fers'): every POTA country is in scope for OUTLINES and 2-FERS (replaces the Oct 29 8:33 AM 'no world 2-fers' and the 7:33 AM 'top 10 / top 15 / hunter-only' limits). ORDER stays: world-stages W1-W10 first (Australia, UK, then by activity), then W11+ by activity; one country at a time through the 2-fer line, each held in the waiting room and graded by chat 11 (2-fers) + chat 8 checks, like the US. Same rules everywhere (Rule G, world 2-fer rules, W-2 EU compilation = Approximate until better, W-9 phone book). Outlines stored SIMPLIFIED in KPC-Data (storage keeper watches). Hours / fees / closures outside KY stay off.
- Oct 30 12:40 PM: NORTH AMERICA EXPRESS LANE (Brandon Oct 30 12:40 PM: 'North America to front of the line...American express lane'): after the US + Canada, the rest of North America goes FIRST in the world order, ahead of W1-W10: X3 Mexico + Central America (MX CR PA BZ HN GT SV NI), X1 Dominican Republic, X2 Caribbean pack (incl. Puerto Rico / USVI if POTA lists them apart), X4 Greenland + St Pierre & Miquelon; THEN W1-W10 (Australia, UK, Japan…), then the rest by activity. Outlines + 2-fers, same rules, one country / pack at a time through the waiting room.
- Oct 30 12:44 PM: US + CANADA FIRST IN EVERY PILE (Brandon Oct 30 12:44 PM: 'Canada and USA to front of the line...everyone else graded next...just IF USA or Canada in a pile work them 1st'): in ANY queue (chat 11's YES list, waiting room, intake, look-ups, LAYER collector, hunter questions, research rows), US and Canada items are worked FIRST, every time; the rest follows in the world order (rest of North America, then W1-W10, then by activity). Bots that pick an order sort US / CA to the top too.
