# WHEN IS POTA BUSIEST (Sheet B) + app/hunters.json: REVIEW (Research desk, chat 8, Tue Oct 27)

Reviewed: Sheet B in `.claude/notes/logger-lounge-digi.md` (chat 3). Source: POTA's own spot list (api.pota.app/spot/activator), the only source, which is the right choice.

## Verdict
The sheet is honest about its limits (counts hunter spots, not hunters; "still counting" under 14 days). I found **5 breaks**, **9 edge cases**, answers for B1-B8 and **7 new grey areas**. The biggest: the numbers measure spot-posting, which is not the same as how many hunters are on, and the 8-week window will be skewed by one weekend.

## A. BREAKS
**B-1. "Hunter spot" vs "growth of the running count" can double count.** Rule 1 counts spots by someone other than the activator AND counts count-growth "the larger of the two". If a spot gets reposted (a re-spot with a comment) the id is new but the count grows too, and the max rule covers it only if both are read in the same 15 minutes. Test with a real re-spot sequence before building; state in the rule that one re-spot by the same hunter is one spot (call hashed, per activation).
**B-2. Counting only what is on the list at read time.** POTA's activator list shows spots from the last short window (about 30 minutes), so reads every 15 minutes overlap; a missed read (GitHub skips scheduled runs) silently drops spots. Example d (12:00 and 14:00 UTC missing) shows it. The sheet's proposal (no data, not 0) is right (B2). Add: an hour with only 1 or 2 of its 4 reads counts as "partial" and is scaled or left out (say, fewer than 3 of 4 reads = no data).
**B-3. Times: UTC to Central at the clock change (Nov 1).** The repeated 1 AM hour is filed twice in the same slot; the sheet calls this tiny but it adds a real double hour for ONE night; harmless in an 8-week average. OK, but the bot must file by the local hour at read time, not by a fixed -5 offset. Add a test for Nov 1 and Mar 8.
**B-4. 'Still counting' and the card.** Rule 4 says no lists under 14 days, yet example c wants Tue/Wed/Thu to show "not counted yet" while Sat/Sun show a window. A page that shows some days and not others under a "still counting" banner is mixed. Pick one: either nothing until 14 days (clean), or per-day with the minimum (B3). Rec: per day, only after 2 counted days of that weekday, with the banner "Still counting: N days so far".
**B-5. The grid and wording promise more than the data says.** "Busiest bands (%)" and "BEST ODDS ... N spots for each activator" are derived from hunter spots, not hunters or contacts. "Best odds" can mislead a hunter or an activator into thinking they will make that many contacts. Add "spots", never "contacts", and a line "Spots are not contacts."

## B. EDGE CASES
1. **Contest and event weekends** (B5): the 760 peak. 8 weeks smooths it, but an event on 2 of 8 weekends still moves a Saturday window.
2. **Holidays** (Thanksgiving, Christmas): a Thursday looks like a Sunday. Same as 1; mark, do not average silently.
3. **Contests that boost spots without POTA park activity** (the list holds only POTA activations, so little effect). Fine.
4. **Spot spam / test posts / one hunter respotting many times.** One hunter posting 50 spots in an hour lifts the count. Cap per hunter per activation per hour (say 1 count per hunter hash per activation per hour).
5. **Activator spots himself with another call (club call, own call).** Portable suffix stripping covers /P; a different call is not a self-spot by this test. Accept; note it as a known blur.
6. **Park outside the US** (B4): the sheet counts US only. A Kentucky ham wants US; fine. For the app's file the same.
7. **Time zone** (B1/example g): Kentucky spans Central and Eastern. Rec: the card shows the visitor's own clock with the zone name; posts show Eastern and Central.
8. **Data source outage lasting days.** The card says "counts paused since <time>" after 6 hours (proposed); the app must not show a window from a file older than 7 days (sheet). Add: the bot never writes a window computed from under 14 days.
9. **Privacy.** The bot saves hashed counts only (call signs never saved). The open-hour file lives in the Actions cache: confirm no raw call appears in any commit or issue. Add the rule to the sheet.

## C. ANSWERS TO B1-B8 (recommendations for Brandon)
- **B1 time zone:** viewer's own clock on the card; Eastern AND Central in posts (the sheet's proposal).
- **B2 no read:** NO DATA, not 0 (agree).
- **B3 minimum:** 2 counted days of that weekday (agree).
- **B4 region:** US parks only for now; revisit.
- **B5 events:** mark them in the data (event weekends flagged) and leave them IN the average but show an "event weekend counted" note; do not silently drop.
- **B6 window:** 8 weeks (agree), but start at 4 weeks while data is young and say so.
- **B7 app alerts:** top 4 windows only; no push alert until Brandon rules; chat 4 owns timing.
- **B8 the word:** "busiest" with "spots" (Brandon: not a head count). Use "most spots" in numbers, "busiest" in headings.

## D. NEW GREY AREAS (for Brandon)
- **BU-1.** Per-hunter cap (edge 4): one count per hunter per activation per hour. Rec: yes.
- **BU-2.** Partial hours (B-2): fewer than 3 of 4 reads = no data. Rec: yes.
- **BU-3.** "Spots are not contacts" line (B-5). Rec: yes, on the card and in posts.
- **BU-4.** Per-day or all-at-once reveal (B-4). Rec: per day after 2 counted days, with a "still counting" banner.
- **BU-5.** Holidays and events (edge 1-2): flag and keep. Rec: flag.
- **BU-6.** App file: what happens when the file is missing or old: no alert at all, never a guess. Rec: yes.
- **BU-7.** Do posts name days, or only "this weekend"? Rec: posts say "last N weeks" with the date range so a Friday post is not read as a forecast.

## E. NOT CHECKED
POTA's spot window length and re-spot behaviour (I could not open the API from here); real counts beyond what the sheet states; the Actions cache contents.

Sources: Sheet B in `logger-lounge-digi.md`; api.pota.app as cited there.
