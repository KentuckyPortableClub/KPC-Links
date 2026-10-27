# OUTSIDE-AGENT WORKSHEET TEMPLATE v2 (HQ, Oct 27 2026; from Fable's research-bots review #10)
Every round for the "good bot" or the second agent uses THIS shape, so returns can be machine-checked and imported into the Discovery leads list instead of read by hand.

## Tab 1: INSTRUCTIONS (same every round, round-specific goal at the top)
- Goal of this round (one sentence) + which rows to work (busiest first).
- RULES: official sources only (the agency's own site or its GIS server/account); a link you cannot trace to an agency page = NOT-SURE; never a third-party copy (Wikipedia, tourism blogs, camping sites, file-storage buckets, Avenza); stop after N rows and save; resumable (work the first row whose STATUS is blank).
- Research order: the state's open-data portal first, then the agency's park page "Maps"/"Alerts" section, then a web search.

## Tab 2: ROWS (one row per park / item; columns in this order, never reordered)
| Column | Who fills | Type |
|---|---|---|
| ROW_ID | KPC | fixed |
| PARK_REF | KPC | fixed (US-1234) |
| PARK_NAME | KPC | fixed |
| STATE | KPC | fixed |
| WHAT_WE_NEED | KPC | fixed (e.g. official park map / closures page / boundary layer / hours+fees) |
| STATUS | agent | DROP-DOWN: FOUND-OFFICIAL / FOUND-UNOFFICIAL / NONE-ON-AGENCY-SITE / BLOCKED / NOT-SURE |
| AGENCY_PAGE | agent | URL of the agency page where you found it |
| THE_LINK | agent | URL of the map / file / layer / feed itself |
| PUBLISHER | agent | DROP-DOWN: managing agency / state GIS office / federal agency / third party |
| WHAT_IT_IS | agent | DROP-DOWN: PDF map / web map / brochure / GIS service / RSS feed / web page |
| DATE_ON_IT | agent | the date shown on the map/page, or "none shown" |
| PROOF_LINE | agent | one quoted line from the page (title or caption) |
| NOTES | agent | short, optional |
| MC_LOADS | KPC (machine) | yes / no / 403, filled on return |
| MC_ALLOWLIST | KPC (machine) | domain on the agency allow list yes/no |
| MC_ALREADY_HAVE | KPC (machine) | matches a layer/link we already use yes/no |
| GRADE | KPC (chat 8) | A / B / C / reject |

## Tab 3: SUMMARY (agent)
Rows done, counts per STATUS, anything odd (site down, login walls).

## Import
A script reads Tab 2 by column name, fills the MC_ columns, and writes each row to data/discovery/leads.json as "agent-found, unchecked"; chat 8 grades only rows where a machine check failed or STATUS is NOT-SURE. Drop-downs are data-validated (house rule for forms/sheets).
