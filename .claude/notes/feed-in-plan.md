# Feed-in plan: the collecting bots' findings into the key, the size check and the grader (PLAN ONLY, no code)

Opus, 20 Nov 2026, from Brandon's 12:16 PM word ("write it down, but not build it"). For Fable to fold into the root-cause plan (REPAIRS.md step 3, fault (a)). Nothing here is built or switched on.

## Where the findings stop today
- **Acreage bot** (KPC-Data `kpc_acres`, Sunday timer): writes tools-out `acres/acres.json` (1,788 parks with an official size on 20 Nov) and drops a copy into the waiting room (`data/waiting`, held for chat 11). Nothing approves it, so no key file ever gets it.
- **Size check in the key** (`_selfchk` in kpc_us_key.py, `self_checks` in kpc_key_rules.py): reads `data/acres.json` in KPC-Links. That file does not exist, so the size line never fires.
- **Page reader** (KPC-Data `kpc-park-pages.yml`, every 3 h, one state per run): writes tools-out. No key, grader or keeper file reads it.
- **Grader** (`kpc_key_factcheck.py` / `kpc_key_grade.py`): sizes a park from its own outline (#298), but has no official size to compare it with.

## The plan, in order
1. **Rule sheet first** (RULES FIRST; it moves the US key rules hash, so Fable reviews it): which number is the official size when a list has two (reported or GIS acres: today the bot takes the one the research named first), how far off counts as "does not pass", hectares and square miles changed to acres, what happens when two lists disagree, a park with no official size is never held.
2. **One small hand-off file per bot on KPC-Data main**, each row with park number, value in acres, source link, agency and date read: acreage = the approved `acres.json`; page reader = only the facts the rule sheet names (sizes; hours, fees and closures for Kentucky only, per SCOPE).
3. **The waiting room stays the gate.** Chat 11 approves rows (or a rule the sheet writes approves them in bulk); only approved rows move on.
4. **The keeper copies the approved rows into its master records** (ONE MASTER COPY: it is the only writer of the saved copies). The key builder reads them from the saved copy in store mode, never from tools-out and never from a server.
5. **The size check reads that saved copy** in place of the missing `data/acres.json`, and compares against the acres measured from the park's own outline (`kpc_pin_edge.acres_geojson`), not the sum of its joined rows (REPAIRS step 3 faults (a) and (c)).
6. **The grader gets the same official size** as one more fact to check, read from the same saved copy (never from the saved answers).
7. **Tried on one state first** (Kentucky; it has the answer key), report only, then the list of parks that would change goes to Brandon. It goes on only at the one build, after the NO BUILDING hold is lifted.

## Grey areas for Brandon (numbered, not ruled)
- **FI-1:** reported acres or GIS acres when a list gives both (ME, MO, RI, SC, VT, VA, NH)?
- **FI-2:** how far apart the official size and the drawn outline can be before a park is held.
- **FI-3:** does an approved size go through chat 11 row by row, or does the rule sheet approve whole lists from an official agency?
- **FI-4:** which page-reader facts count outside Kentucky (sizes only?).
