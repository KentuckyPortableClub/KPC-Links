# KPC "NO rechecker" bot: build instructions (HQ, Oct 31 2026; for chat 10)

Brandon, Oct 31 4:59 PM: "instructions for building the rechecker bot ... it is worth doing". Chat 11 found that about 1 in 20
of its NO answers was wrong when it went back and read the record page (Chena Wayside, for example, became NOT SURE). That is under
its 1-in-10 bar, so this is NOT urgent: build it after the jobs already open in chat-10.md.

## What it is for
Chat 11 grades layer matches mostly by name, kind of place and acres (grade B), without the map. A NO can be wrong because:
- the agency's record uses another name (an old name, the unit name, or initials);
- the name sits in a field other than the one the layer's name field points to;
- the record was the wrong piece, and the right record sits next to it on the same layer.

The bot looks again at every NO with more evidence and flags the ones worth a second human look. **It never changes an answer.**

## Rule sheet (RULES FIRST)
1. **What gets flagged:**
   - **LOOK AGAIN** = POTA's pin is inside the record (or within 100 ft of a line record), AND the name scores ≥ 0.90; or it scores 0.75 to 0.90 and the acres are within 3× of POTA's / PAD-US's.
   - **BETTER RECORD** = another record on the same layer within 2 km of the pin matches clearly better. The row gives that record's id, name and acres.
2. **What stays NO (KEEP NO):**
   - the pin is outside and more than 2 km from the record;
   - the name scores under 0.75;
   - the record is a different kind of place (a WMA is not a state park; the whole lake is not the recreation area: Indiana SRA ruling, Oct 30);
   - the size is off by more than 10×.
3. **Sources, best first:**
   - the layer itself (query by record id with `returnGeometry`, all attribute fields);
   - POTA's park page (`api.pota.app/park/<ref>`: current name, pin, website);
   - the title of the agency page POTA lists;
   - PAD-US / CPCAD acres when the club's key has them.
   - Official hosts only. Never OpenStreetMap, Google or Protected Planet. No keyed APIs.
4. **When unsure** (layer down, no geometry, record gone): the verdict is CAN'T TELL with the reason, and the row is retried next run. Never guessed.
5. **What people see:** nothing on the site. Chat 11 gets questions in `data/waiting/questions/no-recheck.json` (answer null). Each row says the old answer, the new evidence in one plain line, and the suggested record. Chat 11's answer then goes through the normal waiting room. **2-fers are never made from a flipped row until chat 11 says YES.**
6. **Examples the gate must get right:**
   - Chat 11's own Oct 31 rechecks: every row whose `how` starts "NOT SURE: record page read" or was flipped. Example: Chena Wayside vs "Chena River State Recreation Site", 27 ac, Alaska State Parks → **LOOK AGAIN**.
   - The six Indiana SRAs joined to Monroe / Mississinewa / Cagles Mill Lake → **KEEP NO** on the lake record, but **BETTER RECORD** where the own-size piece exists.
   - Old Erie Canal vs the whole Erie Canal → **KEEP NO** (part vs whole).
   - A WMA record for a state forest park → **KEEP NO** (kind conflict).
   - A record named only by initials ("R. F. Kennedy") → name normalising must join the initials. Same normaliser as the outside coder's map-page link extractor (`kpc_map_links.py`: initials joined, type words dropped, token-set ratio gated by the park's own words).

## Inputs
Every answer that starts with `NO` in KPC-Data `data/waiting/questions/`:

| file | NO answers on Oct 31 |
|---|---|
| `gis-hunter.json` | 362 |
| `layers.json` | 157 |
| `key-pieces.json` | 63 |
| `world-finder.json` | 2,140 |

Order: US and Canada first, Kentucky first of all, then the world in the W-order (`notes/world-stages.md`). Skip any row whose `norecheck` date is less than 90 days old.

## How to build
- One script: `.github/scripts/kpc_no_recheck.py`, plus its own workflow `kpc-no-recheck.yml`.
  - By hand, plus once a week after the Sunday collector run.
  - Up to 55 min a job, `--resume` from `data/no-recheck/state.json`, 1 request per second per host.
  - Every step `|| true` / `continue-on-error`: it never goes red.
- Per row, write `norecheck: <date>` and `norecheck_verdict` into `data/no-recheck/<file>.json`, NOT into the question files. Chat 11 owns its answers.
- New flags go to `data/waiting/questions/no-recheck.json` (same shape as `layers.json`, plus `old_answer` and `evidence`).
- **Safety cap:** if more than 15% of a batch's NOs come out LOOK AGAIN, stop. Write "too loose: check the scoring" on the status board and add no questions. Chat 11 found about 5%, so 15% means the bot is wrong, not the answers.
- Status line on the board (`kpc_status.py`), one line in `data/status/inbox-chat-11.md` when new questions are waiting.

## Test before turning it on
1. **Gate:** run it on chat 11's Oct 31 hand-recheck sample. It must:
   - flag every row chat 11 flipped;
   - KEEP at least 90% of the NOs chat 11 confirmed.
2. Then run Kentucky + Tennessee only. Chat 11 grades 10 to 12 flags (bar: A + B ≥ 90%).
3. Only then run the whole list, US + Canada first.

## Report
One REPORT TO HQ line in `chat-10.md`: gate result, and how many LOOK AGAIN / BETTER RECORD / KEEP NO / CAN'T TELL rows per file.
