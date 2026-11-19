# 2-fer owner answers, part 3

## What is NOT built

- The bot does not settle a row, does not read the not-sure list back, and does not hold a pair because a park is on it. Whether a park on that list should be NOT SURE for 2-fers is the owner's question, not this hand-off.
- Tripwire parks are not written here. The tripwire bot owns those rows.
- Part 4 is still only the proposal in the part 1 notes. No finer-grid code.
- The full gate was not run. This machine has Python 3.12.3 and not 3.13.
- No real area was run. No key or outline was changed.

## Baseline

Part 2 left the 2-fer rules hash at `180dcd51a7b0`. This part moves it to `9cee86692de2`.

`tests/test_fers_not_sure_nov19.py` and `tests/test_fers_math_guard_nov19.py` ended ALL PASS.

## What is built

At the end of a run the bot writes `not-sure-rows-<tag>.json` next to the report. The rows are the shared list's shape: `ref`, `area`, `name`, `code`, `how_sure`, `shows_now`, `why`, `wants`, `found_by` (`2-fer bot`), `evidence`. They are sorted by park number, then code. The JSON keys are sorted, so two runs on the same inputs write the same bytes.

Its own doubts only:

| Code | Plain line | Wants |
|---|---|---|
| `SUMMARY_MAP_ONLY` | Every joined record is a summary map, not the agency's own land. | official layer |
| `NEAR_SIZE_LINE` | An overlap is within one grid cell of a size line, so the grid cannot tell which side it is on. | map, a person |

`how_sure` is `unsure`. The bot does not say a row is wrong.

A withheld park is left out before the write, and the file then goes through the same write guard as every other 2-fer file. A tripwire park is left out.

The code names above are a proposal for the list's README. They are not free text.

## Guesses

1. "Park number" is the digits at the end of the ref, so US-2 sorts before US-10.
2. A run with no such doubt still writes the file, as an empty list, so the name is always there. The store-switch byte compare ignores `not-sure-rows-*`, the same way it ignores the receipt.
3. Evidence is one quote, the status line or the fixed sentence, and `where` is the area file or "the key join". There is no page address in a 2-fer row.

## Grey areas

1. A near-line row's status does not name the other park. If a later status did, and that other park were withheld, the row is dropped rather than written. Silent beats a leak.
