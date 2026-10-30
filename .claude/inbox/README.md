# KPC CHAT INBOXES (HQ, Brandon GO Oct 28 4:46 AM)
**US + CANADA FIRST (Brandon Oct 30 12:44 PM): in any pile you work, US and Canada items go first, then the rest of the world in its order.**

**RULES: read `.claude/RULES-NOW.md` (62 KB, the rules in force copied word for word), NOT all of notes/mapping.md (390 KB). New rulings still go in mapping.md, then `python3 .claude/build/rules_now.py` (HQ / chat 2).**

**RESEARCH LAYOUT (Oct 30): Fable book = `.claude/build/research/fable/US-XX.md | CA-XX.md` (one file per area, one row per park, updated in place); Agency Atlas = `.claude/build/research/agency-atlas/` (read your area's file FIRST, add one dated line per find).**

**EVERY TIME YOU READ YOUR INBOX (Brandon Oct 29 10:49 PM: 'remind them daily of Fable's workflow to make it run better'): skim `.claude/build/research/KPC_Fable_Note_To_Opus_Efficiency.md` (the twelve habits): saved copies first, network last · IDs beat names · polygons before pages · batch by agency / county, never by park · one book, one row, one why-not tag · sanity-check numbers · small independent samples · save as you go · quarantine, never delete; stage, never ship · bulk off the website repo · write the ruling once · feed the look-up bot batched requests (official hosts only).**

Brandon used to copy every task between chats. Now: HQ (chat 7) writes each chat's tasks in `.claude/inbox/chat-N.md`; Brandon just types **inbox** to that chat.

WHEN BRANDON SAYS "inbox":
1. `git fetch && git reset --hard origin/main` (or pull), open YOUR file only: `.claude/inbox/chat-N.md`.
2. Do the OPEN items top to bottom (skip any you already did; say so). House rules (CLAUDE.md) still apply: rules first, batch pushes, never wait on bots, email only for real issues.
3. Move each finished item to DONE with the date + one line of result, and write your short REPORT TO HQ at the bottom of the same file (newest first). Push once. Then give Brandon a 2-3 line summary in your chat.
4. If an item needs Brandon (a ruling, a secret, a GO), put it under NEEDS BRANDON in your file and tell him in one line.

WRITING TO ANOTHER CHAT: add an item to THEIR inbox under OPEN, starting `FROM CHAT N (date):` (e.g. chat 8's grading fixes go to chat 10's inbox). BOTS never write here (a KPC-Links push = a site rebuild): they write their 'grade me' lines to KPC-Data `data/status/inbox-chat-8.md`, which chat 8 reads too.
SAVES: one push per chat per 'inbox' session, never per item.
HQ reads every inbox each session, tidies, and keeps the order right.

CHAT 11 (Oct 28) = BOT-OUTPUT CHECKER (Sonnet): grades what the bots make; chat 8 keeps 2-fers, boundaries, rule sheets.
RULINGS.md = Brandon's one daily list of open questions with HQ's leans.
RELEASE TRAIN = one members-only batch a week (chat 3), one GO from Brandon.

FINDING ANSWERS (Brandon Oct 28 7:35 AM): bots first (the Park Detective's question queue, KPC-Data data/detective/questions.json), then chat 8 / chat 11, and only then Brandon looks. HQ + Brandon make the decisions.

## MASTER-PLAN.md (Oct 29, Brandon)
The numbered task list for every chat. When you finish a task, tick it `[x]` with date/time + one short result; `[~]` when started. HQ reads it for status reports.

## LOOK-UP BOT (any chat; MOVED to KPC-Data Oct 29 7:40 PM, Brandon 'protect size on both repos')
NEVER write look-up files in KPC-Links again (the old .claude/lookup path is gone). Everything lives on KPC-Data's orphan branch `lookup`:
1. `git clone -b lookup --single-branch --depth 1 https://github.com/KentuckyPortableClub/KPC-Data kpc-lookup` (or `git fetch origin lookup` in your KPC-Data clone), write `requests/<your chat number>-<short id>.json`, e.g. `{"chat": 11, "kind": "map-check", "urls": ["https://..."], "report": "is the park line drawn?"}`.
2. Kinds: `page` (text + links; `"screenshot": true`), `map-check` (always a picture; a PDF gives page 1, `"pages": 3` for up to 3), `layer-probe` (`"layers": [url, ...]`), `parcel` (`"layer": county parcel layer, "points": [[lat, lon]]` → owner + parcel id), `probe` (a chat-9 config under `"probe"`). Max 25 URLs.
3. Commit + `git push origin HEAD:lookup` (only that file). Each request runs on its own job (6 at once). No inbox line any more: when you read your inbox, `git pull` the branch and look in `answers/<same name>.json` (+ `-1.jpg` pictures).
3b. SEEING THE PICTURES (Oct 30, chat 11 could not see them): the JPEGs are files on the `lookup` branch, not inside the .json. In your KPC-Data copy: `git fetch origin lookup && git show origin/lookup:answers/<name>-1.jpg > /tmp/<name>-1.jpg`, then open /tmp/<name>-1.jpg with the Read tool (it shows the picture). The order of the pictures = the order of `urls` (each request's `report` says which is which). LOOK BEFORE you push read/: read/ deletes the pictures.
4. Done reading? Push an empty `read/<same name without .json>`: the answer, pictures and request are deleted. Unread answers go after 7 days.
5. Same manners as every bot (robots.txt; ArcGIS REST + the two keyed /api paths only; slow per host; never red). Don't re-push a request to retry: new id.
5b. A request whose URL(s) + kind were answered in the last 7 days gets that answer again ('reused': no new fetch); add "fresh": true to force a new read.
6. PICTURE MAPS (house rule Oct 29 11:10 PM): found an official PDF / picture map for a park with NO GIS outline? File kind `save-map`: `{"chat": 3, "kind": "save-map", "ref": "US-9652", "name": "Grenada State Wildlife Area", "agency": "CPW", "url": "<the PDF / picture, or the park page that links it>", "pages": 1, "hint": "granada"}`. It lands small on KPC-Data's branch `picture-maps` (maps/<ref>_<name>.jpg + index.json) and is deleted once the park gets an official outline. Never trace from it.

## WAITING ROOM MORNING LIST (Oct 30)
- **Chat 11: when you open your inbox, also read KPC-Data `data/waiting/today.md`** (everything held, oldest first, why; open questions per file; approvals not yet used). The nightly run (11:13 UTC) rewrites it and lets out what you approved.

## LAYER LINES (Oct 30; any chat, mostly chat 8)
Found an official layer for a park? Write ONE line anywhere in that area's Fable file (.claude/build/research/fable/<area>.md):
`LAYER | <park ref> | <agency> | <layer URL (…/MapServer/N or …/FeatureServer/N, or a download link)> | name field: <FIELD> | <one-line note>`
The daily copy run (KPC-Data, ~5:41 AM / 8:41 PM CDT) pin-tests it (Rule G: pin inside, name, size) and makes a chat 11 question + queues the layer for the intake. A line that fails gets its reason in KPC-Data data/intake/collector.json. Write each line once; it is read once.

## PARCEL LOOK-UP (who owns the land at a pin; Oct 30, HQ 8:20 AM)
1. Find the county's parcel map in the Agency Atlas (agency-atlas/<area>.md 'Parcel / ownership maps') or the county GIS site: you need its ArcGIS REST parcel LAYER (…/MapServer/N or …/FeatureServer/N). A viewer page alone is not enough: open it in the look-up bot (`page`) and take the layer link from its answer.
2. File `{"chat": 8, "kind": "parcel", "layer": "<parcel layer URL>", "points": [[lat, lon], ...], "report": "US-XXXX owner at the pin"}` on the `lookup` branch (up to 50 points; the POTA pin first).
3. The answer gives per point `owner` + `parcel_id` (+ the full record). Owner = the agency (e.g. 'State of Rhode Island DEM') = public land for R-G7 step 4b; write owner, parcel id and the parcel layer URL in the park's Fable row. A private owner = tag `private` (R-G10). Example: Richmond, RI (chat 3).

## STATUS BOARD FIRST (Oct 30, HQ 8:45 AM (6))
Every bot writes its one-line result to the KPC-Data status board (data/status/board.json). Read the board first; open run logs / annotations ONLY when the board says FAILED or a line is missing. That saves usage.

