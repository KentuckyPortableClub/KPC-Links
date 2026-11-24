# Plan: better sizes and better page look-ups (24 Nov 2026)

The owner, 6:41 AM: "1-3 yes 1 name i been screaming this! 3 wtf 403 again check the ducking rules!! ... 1-5 right up plan for all".

## First: the 403 mix-up (fixed today)
**The rule (club rule R-NET1, RFC 9309):**
- A robots.txt that answers 401, 403 or any other 4xx except 429 means **no rules**: reading is allowed.
- 429 or a server error means **not this run**.
- Only a real **Disallow** line means no.
- If the page or data itself answers 401 / 403 / 429, stop that host for the run.

**Why it kept coming back:**
- Two old checks still said "a robots 403 is a no": `kpc_master.robots_allows` and `kpc_leadtest`. Four tests pinned that old Nov 10 reading.
- The page reader did the right thing, but its messages still said "(a 403 counts as no)".
- Agents read those words and repeated them. Tonight Opus did too, about Tennessee and New Hampshire.

**Fixed:**
- KPC-Links PR #368: both checks follow the rule, the tests are updated, and no rules hash moves.
- KPC-Data 1282130d: the page reader's wording only.
- A one-line house rule in CLAUDE.md.

## Sizes (acreage)
1. **Each agency's yearly acreage list, read by the bot once a year.**
   - The acreage bot exists: KPC-Data `draft/tools/kpc_acres`, run through `kpc-tool-trial.yml` (tools=acres). Since 20 Nov it can read a PDF that holds many tables, made for Fish & Wildlife's yearly lands report.
   - To add: the Park Service's acreage report (every unit) and the Forest Service's Land Areas Report (every forest and grassland). Then the states that publish one list for all their parks.
   - First, look: check the research file on KPC-Data branch `intake-files` for rows already there. Add only the missing rows.
   - Then ONE bot run. Results go through the waiting room, as now.
   - About 1,000 federal parks get an official size from three documents.
2. **BLM: sizes from BLM's own map data**, because its web pages almost never give one (996 BLM pages had no size). Label it "agency map data", which is weaker than a list. It can confirm a size; it can never fail a park on its own.
3. **The sentence must name this park** (the Nov 18 rule; a refuge's size was once read off a sentence about another refuge). A size found on one page only is "weak" and can never fail a park on its own. Check that the page reader does this; fix it if not.

## Page look-ups
1. **Page names become a confirmed-name list** (the owner: "name i been screaming this!").
   - 2,214 parks have an official page that calls the park something other than POTA's name (`page.name_on_page`).
   - A bot checks each one: is there a map record with that page name at the pin? If yes, it's a name candidate.
   - Candidates go through the waiting room.
   - The key reads only the approved ones, as a name that counts like the park's own name.
   - Tonight this settled 30 parks by hand.
2. **"Part of" lines.** The page reader already saves `parts` (2,226 parks) and `inside_of` (65 parks).
   - A park whose page says it's part of X is never given X's whole outline.
   - X's own page list of parts helps find each unit's land.
3. **Sites that really say no.** Under the rule above, almost no site blocks us.
   - First, re-read anything skipped as "robots" because of the old wording (a page-reader list check; no new bot).
   - For a site with a real Disallow line: use the state's open-data map portal (research order step 1), not its pages.
4. **A secure page that sends us to the plain (http) address on the same site** (Forest Service pages do this). Grey area P-1 for the owner, below.
5. **Bots look up, chats judge.** Anything the key or the clean-up stage can't settle goes on the page reader's re-read list (the PC already has 2e / 2f). Its results come back in the next park facts. A chat only looks when the official page still doesn't settle it. Then the owner gets at most a one-line question.

## Rule sheets needed before building (RULES FIRST)
- **Page 1 (names) and page 2 (part of)** change what the key joins, so each gets a short rule sheet: what counts, what doesn't, sources, what happens when unsure, examples. That means a draft PR and the owner's own review.
- **Sizes 1-3 and pages 3 and 5 only collect information**, so they need no sheet.

## Grey areas for the owner (RULED 24 Nov 6:57 AM: '1 yes...2 yes...my 1??? Page reader whole reason is to read names!!': P-1 YES, A-1 YES, page names = job one)
- **P-1:** a Forest Service page redirects from https to http on the same site. May the page reader follow it, for reading public pages only?
- **A-1:** may a size from an agency's own map data (BLM) count as "official, weak": it can confirm a size, but never fail a park on its own?

## Order
1. PR #368 (robots) merged.
2. Acreage: check the research file, add the three federal lists, one bot run.
3. Rule sheets for page 1 and page 2, together with the key-side fixes (spellings, never another park's land, kind of land, part never takes the whole).
4. Page 3: re-read the skipped list.
5. Page 5 joins the clean-up stage (the other agent).

## Work split (owner 6:57 AM: 'you for sure take webpage look up, acreage..both of you will complete work and then each other has to approve of the final drafts')
Opus: page names list, spelling table, 'part of' data, page reader (P-1 redirect, re-read wrong-403 skips, open-data for real Disallow), acreage bot (NPS + USFS yearly lists, BLM map-data sizes as weak, sentence must name the park), PR #368. The other agent: #187/#188/#367 changes, #366, #189, auto-confirm rule (after his yes), the final-pass items, the solver's 'pin at the land' verdict. Each reviews the other's final drafts. Review: KPC-review-opus-nov24.zip.

- **Forest Service yearly sizes (owner 24 Nov 8:55 AM 'Don't we have the file all ready?'):** we DO: LAR_FY2025.xlsx, downloaded by hand by the owner on 19 Nov; its rows are in KPC-Store `key-quality/2026-11-19/kitC-acreage/answers/kitC-usfs-acres.answers.csv`. Now on KPC-Data intake-files as `acres-usfs-lar-fy2025.json` (211 whole units). Before searching the web for a list again, check KPC-Store key-quality answers and the intake-files branch first.
- **BLM map sizes (owner A-1 yes; measured 24 Nov 10:35 AM):** as a match witness they add nothing in NV + OR (0 more confirmed: 113 outlined BLM parks are joined to BLM's own record, 65 have no BLM acres record at the pin, 8 have another place's). Not built. Open option: show BLM's own map acres on park info as 'agency map data' (needs the owner's GO).
