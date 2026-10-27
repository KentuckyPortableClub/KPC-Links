# RULE SHEET REVIEW: CHAT 5 BOTS (Research desk, chat 8, Tue Oct 27 ~5:40 AM)

Reviewed: `## POSTING RULE SHEET: CHAT 5 BOTS` at the end of `.claude/notes/website.md` (Oct 27), against the bot scripts (`.github/scripts/kpc_club_posts.py`, `kpc_park_alerts.py`, `kpc_discord_relay.py`) and the workflow schedules. Chat 5 changes nothing until Brandon rules. Official sources only; where a point is my reading of a script, it says so.

## Verdict
The sheet is sound: the 10 NEVER rules and the 9 bots cover what matters, and its own GAP list is honest. It breaks in **four places that are facts, not opinions** (A), and it has **16 more grey areas** (B, G7 to G22) beyond G1 to G6. The 6 original grey areas get a recommended answer in (C).

## A. FACTS THE SHEET GETS WRONG OR MISSES (no ruling needed; chat 5 fixes after the sheet is final)
| # | Finding | Evidence | Fix |
|---|---|---|---|
| A1 | **Rule 10 is not met by any bot.** NEVER 10 says posts that carry maps or park details need "ℹ️ Maps and park info are a planning aid, not a guarantee..." with the About our information link. None of `kpc_club_posts.py`, `kpc_park_alerts.py`, `kpc_discord_relay.py` or `kpc_fb_comments.py` contains that line or links to the About page (script search: 0 hits in each). The closure post ends with a blaze-orange line and "check the KDFWR page before you drive" only (`kpc_club_posts.py` line 211); park-alert posts end "worth a quick check before you set off". The sheet does not mark this as a GAP. | Scripts above | Add the short line + link to the closure post, the park-alert post and any holiday post that shows park details (a plain greeting does not need it). The relay posts only a person's words, so people carry it |
| A2 | **Rule 9 (nothing posts 9 PM to 6 AM) breaks every winter.** The park-alert workflow runs at `5 11,14,17,20,23,2 * * *` (UTC). That is 6, 9, noon, 3, 6, 9 PM in summer (CDT), but **5 AM, 8, 11, 2, 5, 8 PM in winter (CST)** after the clocks go back on Sun Nov 1 2026. A 5 AM park-closure post lands before the 6 AM line. | `.github/workflows/kpc-park-alerts.yml` line 8; DST ends Sun Nov 1 2026 | Either run the bot in Central time (check the clock inside the script and skip outside 6 AM to 9 PM) or move the cron an hour in winter |
| A3 | **"Wednesdays 9:41 AM" becomes 8:41 AM from Nov 1.** `kpc-club-posts.yml` runs `41 14 * * *` (UTC) and its comment says "9.41am Central, 10.41 in summer", which is backwards: 14:41 UTC is 9:41 CDT in summer and 8:41 CST in winter. The first closure post after the change (Wed Nov 4) goes out at 8:41, not 9:41, and the sheet's times (§3 and §4) are wrong for winter. | Workflow file lines 7 and 8 | Fix the comment and the sheet; decide whether 8:41 is fine (it is after 6 AM) |
| A4 | **The relay posts at any hour; rule 9 forbids it.** `kpc-discord-relay.yml` runs every 15 minutes (`7,22,37,52`), and a person's message typed at 11 PM posts within 15 minutes, with "Now:" emailing subscribers at once. Rule 9 has an exception only for "what a person scheduled on purpose", and "typed a post at night" is not scheduling. | Workflow line 8; sheet §1 and NEVER 9 | Say rule 9 means **bot-written** posts (closures, alerts, holidays), and that a person's own relay post goes when they send it, or hold relay posts typed 9 PM to 6 AM until 6 AM. This is a Brandon choice (G7) |

Also confirmed: the sheet's closure-day example is right (Wed Nov 11 2026 is Veterans Day and a Wednesday; Halloween is Sat Oct 31; Easter 2027 is Mar 28).

## B. NEW GREY AREAS (for Brandon), building on G1 to G6
Each is a question; my recommendation is marked **(rec)**.

**Closures (§4) and alerts (§5)**
- **G7. Relay at night.** See A4. Should a person's own post typed 9 PM to 6 AM (a) go within 15 minutes, (b) wait until 6 AM, or (c) only wait if it uses "Now:" (the email)? **(rec) (c)**: a night email to subscribers is the one that annoys people.
- **G8. Closures that end before the weekend.** The weekly post only lists closures that touch the coming Saturday or Sunday. A WMA closed Wed to Fri is not posted, but weekday activators drive out on Thursday. Post weekday closures too, or leave them to the park card? **(rec)** card only; the post stays a weekend heads-up.
- **G9. "Closed to non-hunters" is a fixed template.** The post says the WMA is "closed to non-hunters". KDFWR quota-hunt pages sometimes say the whole area is closed to ALL public use, or "closed to hunters without a draw permit". The template could be wrong for a given WMA. Should the post quote KDFWR's own words per WMA instead of the template? **(rec)** yes: a short quote of the agency's sentence, the template only when KDFWR's wording is plain "closed to non-hunters".
- **G10. Urgent alerts and the two-check rule.** A change must show on two checks in a row (3 hours apart in the day). A tornado, flood or fire closure then waits up to 3 hours, and an overnight one until the next 6 AM check. Do safety-type alerts (fire, flood, severe weather, evacuation) skip the second check and post at once (still not at night)? **(rec)** yes, for those categories only.
- **G11. A mass closure (federal government shutdown, ice storm, state emergency).** The alert lists would show many parks changing at once, or one statewide notice that cannot be tied to one park (G5). Post one plain "many parks are affected, check the agency" message, or post each? **(rec)** one message, with the agency link, and only after a person approves it in the staff room.
- **G12. Time zones inside Kentucky.** All times are Central, but eastern Kentucky is on Eastern time (WMA quota-hunt start times, park hours). A closure "6 AM Saturday" quoted from a KDFWR page is in local time. Should the post say "local time" or convert? **(rec)** "local time" and quote the page's own wording.

**Relay (§1) and Club Post Form (§2)**
- **G13. A secret pasted into a post.** The relay posts what a person typed. A pasted token, password or the member password (NEVER 7) would go to the website, Facebook and email. Scan before posting for key-like strings and hold? **(rec)** yes, hold with ⚠️ and ask in the staff room (same hold rule as G2).
- **G14. Photos carry hidden data.** Club Post Form photos go to the website. Phone photos often hold GPS in the file. A member's home or private camp spot could be published. Strip location data from every image the relay publishes? **(rec)** yes, always. Also: photos that show a screen with a real call sign or a members-only tool (rule 3 and 4) can't be checked by a bot, so people carry it.
- **G15. A deleted or edited post the email already sent.** The sheet says deletes follow on the website and Facebook but email "can't be unsent". If the deleted post had an error (a wrong date, a 2-fer claim, a members-only link), the error stays in subscribers' inboxes. Add a correction email on request? **(rec)** a one-line "correction" email only when a person asks for it by tag.
- **G16. The "2-fer" check (G1) by words.** If the relay holds posts that mention "2-fer", "3-fer", "overlap" or "multi-park" without the notice, how does it tell a ham joking about "a two-fer meal"? **(rec)** hold only when a park number (US-####, KFF-####) or a known park name is in the same post, then ask in the staff room; never refuse silently.
- **G17. Multiple or mistyped tags.** "Website + Facebok:" (typo) or "All + Skip:" (conflict). G2 covers unreadable tags; a conflicting pair (Skip with anything) should always win as "Skip". **(rec)** yes.

**Holidays (§3), Facebook (§6), Discord (§7), health bots (§9)**
- **G18. Holiday posts and a closure on the same morning.** G6 asks both or holiday-only. Add: two Discord posts and two Facebook posts within minutes of each other reads like spam. **(rec)** both, but the holiday post first and at least 30 minutes before the closure post, or fold the closure into the next day's run.
- **G19. Holidays that depend on religion or local custom** (Easter, Christmas, Hanukkah, Juneteenth). The sheet says only holidays Brandon marks GO post; only Halloween is on today. Should a "neutral" holiday set (Memorial Day, Veterans Day, Independence Day, Thanksgiving) be pre-approved and the religious ones always personal? **(rec)** Brandon's choice; list what he wants GO in `data/holiday-post-go.json` once.
- **G20. Facebook comment helper and minors.** Facebook comments can come from children (the kids pages link to the Page). The helper flags comments to the staff room and never stores names; confirm the staff-room flag carries no minor's name or photo link beyond what the staff already see on Facebook itself. **(rec)** never auto-reply to a comment that mentions an age or school (already the safe default while auto-reply is off).
- **G21. Fixed Facebook answers going stale.** A ready answer such as the campout date or "the Lounge is open" can outlive the facts. Each answer should carry its source page link and be checked when that page changes. **(rec)** answers link to the live page, never repeat a date.
- **G22. The Check-up bot's issue is PUBLIC.** The sheet says the check-up uses one issue (#17). The repo is public, so an issue naming "page X shows a members-only link" tells the world which members-only pages exist. The CLAUDE.md house rule keeps review lists in the issue BODY (no email), but the body is still public. Should private pages be named by number or short code in the public issue, with the full list in the private staff room? **(rec)** yes.

## C. THE SHEET'S OWN GREY AREAS G1 TO G6: recommended answers
- **G1** Relay refuses a post with 2-fer/overlap and no notice: **yes, hold and ask** (with the park-number condition from G16).
- **G2** Unreadable tag: **hold and ask**, never the default places.
- **G3** Partial WMA closures: **card only**, not the weekly post (it is "part of the WMA", not "the WMA"), unless KDFWR's own page headline says closed.
- **G4** Correction after KDFWR changes dates: **yes, one short correction post** the next 9:41/8:41 run, keyed to the same WMA; never silent.
- **G5** Unlinked alert: **ask in the staff room**; no public post until a person ties it to a park.
- **G6** Holiday on a closure Wednesday: see G18.

## D. WHAT THE SHEET GETS RIGHT (keep)
Kentucky-only closure posts (NEVER 2); "never guess in public, hold and ask" (NEVER 8); two-check change rule for alerts; "looks open again" worded as "the notice was taken down"; auto-reply off; FB helper uses fixed answers only; Discord mod only mutes and never bans; approvals email never in a public repo.

## E. WHAT I DID NOT CHECK
Facebook's and Discord's own posting limits; the KDFWR quota-hunt wording per WMA (G9 needs a sample read of 10 pages; I can do it on request); whether the staff-room messages (KPC_ADMIN_WEBHOOK) can be read by anyone outside the staff.

Sources: `.claude/notes/website.md` (rule sheet), `.github/workflows/kpc-club-posts.yml`, `kpc-park-alerts.yml`, `kpc-discord-relay.yml`, `.github/scripts/kpc_club_posts.py`, `kpc_park_alerts.py`; DST date from the standard US rule (second Sunday of March to first Sunday of November; Nov 1 2026).

## RULED (Brandon via HQ, Oct 27 8:10 AM, see mapping.md / website.md 'FINAL (HQ Oct 27 8:10 AM)')
Brandon accepted chat 8's recommendations for G7-G22, with: ALL holidays post (holiday-post-go = all); night posts 9 PM-6 AM: website + Discord at once, email waits until 6 AM; safety alerts skip the second check; closures quote the agency's own sentence; strip photo GPS; hold key-like strings; never name members-only pages in public issue #17.
