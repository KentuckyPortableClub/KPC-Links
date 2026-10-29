# KPC CHAT INBOXES (HQ, Brandon GO Oct 28 4:46 AM)
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

## LOOK-UP BOT (any chat; Oct 29, chat 10)
1. Can't open a page or layer from your session? Write `.claude/lookup/requests/<your chat number>-<short id>.json` in KPC-Links, e.g. `{"chat": 11, "kind": "map-check", "urls": ["https://..."], "report": "is the area closed?"}`.
2. Kinds: `page` (browser text + links; add `"screenshot": true`), `map-check` (always a screenshot), `layer-probe` (`"layers": [url, ...]`), `parcel` (`"layer": a county parcel layer url, "points": [[lat, lon]]` → owner + parcel id per point, plus the full record), `probe` (a chat-9 probe config under `"probe"`).
3. Commit + push it (only that file). A runner answers it on its own job (up to 4 at once; a small request never waits for a big one); max 25 URLs per request.
4. The answer lands in `.claude/lookup/answers/<same name>.json` (+ `-1.png` screenshots) and ONE line 'FROM LOOK-UP BOT' appears under '## OPEN' in your inbox. Pull first, then read it.
5. Same manners as every bot: robots.txt obeyed (ArcGIS REST + the two keyed /api paths only), slow per host, no timers, never red. Don't re-push the same request to 'retry': write a new id.
