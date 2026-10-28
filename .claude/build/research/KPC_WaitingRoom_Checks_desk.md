# WAITING ROOM checks (chat 11, Oct 28 12:55 PM CDT)
Rule: after a bot saves, the checker runs the checks below on the NEW file against the OLD one. Pass = live at once. Fail = new file held, old file stays live, ONE 'please look' line (reason + numbers). Unsure = hold. Numbers are starting values; tune after a month.

## 1. Every flaw caught since Oct 26 -> the automatic check
| flaw | check that catches it |
|---|---|
| 230 access points 270-380 km from their park; Robert Moses x2 sharing 27 points, Copan 15, Beaver Creek WMA | any point > 100 km from its park pin (line parks and trails exempt) = hold; > 2% of a state's points far = hold |
| a timed-out layer shrank a state's access/trail/camp file | new count < 60% of old (access, camps, trails 70%) = hold |
| federal campgrounds filed by office address: 196 in the wrong state, 132 in two states | pin outside the state's box/outline > 1%; same id in two state files = hold |
| a short POTA list retired parks | parks lost > 1% of the state's list (or > 5 parks) = hold + second read; known 3 parks missing = hold |
| Michigan water 'no answer' marked READY; Indiana 56 / Illinois 16 rows 'not checked' | any 'not checked/unanswered' rows > 0 = status must be STOPPED, never READY |
| docs: 83 WV / 130 GA / 53 FL parks share one rules page; 26 VA maps = inciweb | one URL used by > 20 parks (or > 10% of a state) as map/rules = hold; fire-news / Google-pin hosts banned |
| docs: map or rules links that return an error | every kept link must answer 200 on a re-test; > 3% dead = hold |
| closures: standing rules ('is prohibited'), Virginia notice under a KY park, expired item, duplicates | sentence with no date/place and 'prohibited/in violation' = reject; state named in text must match the park's state; end date in the past = reject; same place + date twice = merge |
| hours/fees: statewide licence prices as a park's fee, headings, duplicates | fee on > 20 parks of a state with the same text = hold; a heading ending ':' or no digit = reject |
| hours/campground gate drift (24% opened) | gate below its bar = hold (already works; keep) |
| parking explorer wiped a state's leads when a server did not answer | leads drop to 0 or < 50% = hold |
| campground: elevation stored as RV length, '13 sites' copied to 9 camps, 877 reservation line as phone | RV length > 100 ft or < 10 = reject; same count on > 3 camps of one agency = hold; 1-800/877 numbers are not a camp's phone |
| truth checker: a number from a map PDF or lake | acreage within 2x of the park's pin-size rules; > 10% 'off' rows in a state = look |
| intake: read error turned into REJECT; a bare copyright line made READY | a read error = RETRY; READY needs a named licence or open-data page |
| Canada: retired park still outlined (CA-2156); a key rebuild losing outlines | old outline count - new > 1% = hold; the 5 known parks (Banff, Jasper, Algonquin, Gros Morne, Bruce Pen.) must keep theirs |

## 2. Per data type: the checks and the numbers
- **Outlines / boundaries:** (1) shape count drop > 1%; (2) pin inside own outline, or within 200 m (entrance pins); (3) area within 3x of the agency size; (4) no invalid/empty geometry; (5) 5 known parks unchanged.
- **2-fers:** (1) known answers 18/18; (2) 'not checked' rows = 0 else STOPPED; (3) a big 2-fer must not be swallowed into a 3-fer patch (patch area <= smaller park); (4) no duplicate river rows; (5) NOT SURE count change > 30% = look.
- **Access points:** far-point rule (100 km, 2%); count drop > 40%; point at 0,0 or outside the state; duplicates within 6 m; 'name' ties need a park-name match.
- **Campgrounds:** count drop > 30%; pin outside state; id in two files; 5 known camps within 2 km; facts in range (sites 1-1,000, RV 10-100 ft, phone shape).
- **Trails:** a line keeps >= 50% of its saved points; 4 known trails (Sheltowee, AT, PCT, North Country) must keep lines; length within 25% of the old.
- **Docs / map links:** all links re-tested (200); one URL on > 20 parks = hold; map host on the agency's or a known gov domain; 'names the park' flag only when the park name is on the page.
- **Hours / fees / permits:** gate % of the known answers; statewide-price rule (same fee text on > 20 parks); fee 0-500 dollars; hours need a day AND a time.
- **Park lists:** loss > 1% or > 5 parks = hold + second read; 3 known parks present; numbers unique; new park needs pin + name.

## 3. Never wait (go live at once, check afterwards)
Closures and alerts (safety, time-limited: hold only if the file is empty/garbled), spots, and NEW PARKS' pin + name (the rest of a new park's data waits). A held closures file keeps the old one live but stamps it 'as of'. Everything else waits.

## Notes
- One 'please look' line per hold, reason first: '[bot] [area] held: [check] [old -> new]'. No 'what changed' summaries (EMAIL rule).
- Held output keeps old data live; never delete the old file.
- A flaw found later = add a numbered check here, then rerun.
