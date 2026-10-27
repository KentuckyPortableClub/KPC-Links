# POST-RELEASE READ (Research desk, chat 8, Mon Oct 26 ~9 PM)

Scope (HQ, 8:40 PM): the pages that went public tonight (Plan A), read as a guest from the repo as it is on main (ab8b93fc, 8:38 PM). The desk edited no page and no data file.

Method: opened 36 public pages in a guest browser (phone 390 px and desktop 1280 px, `navigator.webdriver` forced false so the gate treats the visitor as a guest). Checked: members door, locked links showing, members-only names showing, sideways scroll, page errors, footer link, the SHORT information line, both 2-fer notices, real call signs, "Map Room" wording. Then read the page text, checked claims against official pages and our own data files, and counted.

Limit: this session cannot open the live site and cannot reach most outside websites. Live data panels (Happening Now, maps, weather) load from the network, so they came up empty here. Two pages (Trip Planner, Am I in the Park) print "L is not defined" in my test only because the map library comes from the internet and was blocked; not a site fault.

## 1. GUEST VIEW: clean
- No members door on any of the 36 pages. `kentucky-parks.html` forwards to `parks.html`. No locked link visible anywhere. No sideways scroll at 390 px. No page errors that come from the site.
- Members-only names (Map Rep, Logger, VIP, Club Room, Monthly Recap, Top 50, Multi-Park Spots, 2-fer guide, PVA, Beta Test) do not show to guests. Only "Spot Me" shows as plain words in three places (item B4).
- "Map Room": only on the one-page pointer (`kpc-map-room.html`, says "The Map Room has moved", carries the SHORT line). Not in any menu, card, search or page text. (Left only in code comments.)
- Real call signs in page text: none used as examples. N4KPC (club call), K4TEST/W4KIDS (practice), W4K/W4G (SOTA codes), N1CC (a POTA award name), K3S (a radio model). Two real-call credits remain on purpose: "Meet the Founders: Brandon White KZ4CP" (Find It) and "Provided by KZ4CP" (Park Commander footer).
- Footer link "About our information" is on every page tested.
- Both Lounges have the same tab strip right under the hero. Activators: TOOLS · ACTIVATION BOARD · WEATHER · RADIO CONDITIONS · HAPPENING NOW. Hunters: SPOTS & LOG · PARK CHECKER · ACTIVATION BOARD · RADIO CONDITIONS · HAPPENING NOW. The current tab is lit on each page, and #live opens the Happening Now panel on both. (Could not see live data in it.)

## 2. THE ANNOUNCEMENT'S CLAIMS
| Claim | Result |
|---|---|
| Trip Planner, anywhere in the US | TRUE. KPC Trip Planner (kpc-planner-us) says "all 50 states", "any town in the US". |
| Park info and official maps | TRUE, with the usual limit. Info Finder works for any park number, summit or name; says "where one has been published". The BETA line on the planner admits not every outline is there yet. |
| Activation Kit anywhere in the US | TRUE ("any state"). |
| **Parking and access points anywhere in the US** | **OVERSTATED.** The Parking & Access Finder's own tag is "KENTUCKY · LIMITED REST OF US" (page and Lounge card). Say "Kentucky, plus many other states" or "parking and access points, Kentucky first" in the announcement/post, or the page. |
| Weather | TRUE. Field Weather works from any spot; its radar, warnings and weather-radio parts are US sources. |
| Radio conditions | TRUE (worldwide). |
| Happening Now and the Activation Board are tabs in both Lounges | TRUE (see section 1). |
| Kentucky tools on KY Parks | TRUE: Park Commander, Park Control, Park Checker, Plan A Radio Trip (KY Planner), Grid & County Lookup, Park Notes, plus the official agency links and the Outside Kentucky? card to the Lounge. "Kentucky 2-Fers Guide" shows "coming soon". |

## 3. COUNT CLAIMS vs OUR DATA
| Claim (where) | Our data | Verdict | Where it could go stale |
|---|---|---|---|
| **216 W4K summits** (Parks, Find It, SOTA Summit Checker chip, Park Control chip, SOTA guide) | 216 in `kpc-ky-data.json`, 216 W4K codes in `kpc-guide-sota-data.json`, 216 in the GPX, 216 in the KML, 216 in the SOTA tile files (`data/sota/t`) | RIGHT | Typed by hand on about 8 pages. SOTA publishes new summit lists in its regular updates; the data files refresh daily/weekly but the page text will not. |
| **more than 200** (New to SOTA) | 216 | RIGHT | Safe unless the list drops below 200. |
| **193 POTA parks** (New to POTA, Park Control chip, Club Room badge note) | 193 in `kpc-ky-data.json` and 193 US refs in `kpc-guide-pota-data.json`; the 3 Kentucky parks POTA retired in October (US-7969, US-13604, US-13605) are not in it | RIGHT | The number is typed by hand in 3 places. A new or retired Kentucky park (the new-refs bot and the retired sweep change the data nightly/weekly) moves the data but not the page text. Best fix: let the pages read the number from `kpc-ky-data.json`, or reword to "about 190" / "nearly 200". |
| **142 KFF references** (Park Control chip) | 142 in `kpc-ky-data.json` = 140 in WWFF's directory under Kentucky + 2 shared with other states (Ohio River Islands KFF-0608, Big South Fork KFF-0686) | RIGHT as the site counts it | WWFF's own Kentucky list is 140; the KFF guide lists 140. Anyone comparing to WWFF will see 140. |
| **about 140 KFF** (New to WWFF) | 140 (guide) / 142 (map data) | RIGHT (about) | Fine. |
| Lounge headline: 67,000+ WWFF areas | 67,852 in `data/wwff` | RIGHT | Grows weekly; safe. |
| Lounge headline: 172,000+ SOTA summits | 172,123 in `data/sota/t` | RIGHT, thin margin (123) | Typed by hand; fine today. A summit list clean-up could drop it under 172,000. Use "170,000+" or read it from the data. |
| Lounge headline: 92,000+ POTA parks | 75,675 outside the US in `data/pota` (nightly) plus the US list, which comes from a different source the desk could not total | NOT SURE | Check once against pota.app's own park count. |

## 4. FIXES BY CHAT

### Chat 1 (pages, copy, notices)
1. **Overlap notice (word for word) missing where the 2-fer rule is explained to guests.** New to POTA, Rules You Should Know and POTA Room each explain the 2-fer rule with no notice. The house rule says every guide that mentions 2-fers carries the notice. Add the FULL notice on those three; add the SHORT on the one-line mentions: Activation Kit ("Kentucky ones add ... 2-fers"), Printable Park Sheet ("Kentucky parks add ... 2-fers"), Trip Planner (US) ("adds hand-checked access points, 2-fers"), New to WWFF ("with the POTA overlaps"). Or reword those four lines so they do not say 2-fers. (HQ to decide how far the rule goes for a passing mention.)
2. **POTA quote is now word-for-word except one skipped sentence.** Checked today against https://docs.pota.app/docs/rules.html. POTA's text has this sentence between the first and second one that our pages quote: "Activation Location and Access Rule #1 applies to simultaneous activations." Our pages (New to POTA, Rules You Should Know, POTA Room) run the quote straight on without it. Add "..." where it was cut, or add the sentence. The "Multi-loc" wording and the last two sentences now match.
3. **Short information line missing on Find It** (it lists Park Commander, map files, parking points, pins). Also missing on Field Weather, Radio Conditions and Band Plan; those are covered by the footer link and the LIVE INFORMATION paragraph, so only Find It really needs it.
4. **Spot Me named to guests who cannot open it** (low). Activation Kit intro sentence ("... and a Spot Me button") and its page description/share text; Activation Board sentence ("also spot yourself with Spot Me"); Find It's "Spot Me" card is hidden correctly. Reword, or leave (HQ said no Spot Me in public descriptions; the Kit's description still has it).
5. **Stale tag on KY Parks:** the Grid & County Lookup card says "GRID ANYWHERE · COUNTY & PARKS IN KY". Since this evening's change (commit e2eaf5b6) it gives county/state/province/country anywhere. Change to "ANYWHERE" (the Lounge card already says ALL PROGRAMS).
6. Find It still lists Top 25 as "Kentucky POTA parks ranked"; the page's heading says Kentucky too, but its script has a state picker. Make the wording match the page (low).
7. The "coming soon" lines on KY Parks (Kentucky 2-Fers Guide) and the Lounge (Park Overlap Finder) are fine, each carries the SHORT overlap notice.
8. Carried over from the pre-release reads: all four are now fixed. "Simplex only" is gone, the SOTA Room says 82 ft, the Club Room leftover "PICKS" sentence is gone, and the WWFF log file name now reads `K4TEST @ KFF-1234 20261026.adi` (the same spacing as WWFF's own example).

### Chat 2 (map tools)
1. **Parking & Access Finder is "Kentucky · limited rest of US"**; the announcement says anywhere in the US (see section 2). Either the announcement changes or the tool grows.
2. **The About our information page says "Where we have no official boundary, we say so and never draw our own."** Tools still draw outlines from OpenStreetMap when there is no official one: Trip Planner (US) ("SHOW UNOFFICIAL OUTLINE", "dashed outline marked Approximate"), Am I in the Park ("KPC-drawn (approximate)", yellow dashes), Park Commander and Park Control ("OSM BOUNDARY"). They are labelled unofficial, which is honest, but "KPC-drawn" reads like KPC drew them. Either say "OpenStreetMap outline, not official" in the tools, or soften the sentence on the About page (that one is chat 1's page, so HQ decides).
3. Overlap notice: Park Commander (FULL), Trip Planner (FULL) and Park Control (SHORT) are in place now. Nothing left to do there.

### Chat 3 (Lounges)
1. Nothing wrong found in the tab strips or cards. One check the desk could not do: with the network blocked, the Happening Now panel was 8,351 px tall and empty. If it shows a long empty block when POTA/SOTA feeds are slow, that is worth a look on a real phone.
2. Lounge headline "92,000+ POTA parks": confirm once (section 3). "172,000+" has only 123 to spare.

### Chat 5 (bots, checks)
1. Sunday's link check (issue #2, Oct 25) is still open: 2 broken links, one of them on a public page: `kentuckytourism.com/explore/lake-cumberland-state-resort-park-433` returns 404 on **kpc-campgrounds.html**. The other two items are `x.jpg` and `x-mobile.jpg` named in kpc-tools.css.
2. The check cannot open 41 sites that block robots. Links on today's public pages that a person should click once: `parksontheair.com/rules` (POTA Room, Park Control; search still lists it), `wwff.us/` and `wwff.us/?page_id=133` (WWFF Room, New to POTA/WWFF/SOTA, Rules), the Forest Service Daniel Boone alerts page (Rules), the Forest Service trail guide PDF `stelprdb5427184.pdf` and two forest pages (KY Parks). Old-style addresses (`.aspx`) on KY Parks all point at eec.ky.gov and fw.ky.gov; the check passed them on Oct 25.
3. Counts typed by hand (section 3): 193, 216, 142, 172,000+ would go stale silently. A small check that compares the page text with `kpc-ky-data.json` each week would catch it.

### HQ
1. Decide how far the overlap-notice rule goes (chat 1 item 1).
2. Decide the announcement wording for parking and access points, and the "never draw our own" sentence (chat 2 item 2).

## 5. WHAT WAS NOT CHECKED
- The live site itself, live data panels, outside links (see section 4, chat 5).
- Plan B pages; the Club Room and members-only tools (not visible to guests).
- Whether the website's hosted copy matches main (GitHub Pages deploy not looked at).
