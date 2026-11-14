# WWFF to POTA links (Nov 14 2026)

Credit: VEFF-POTA cross reference list by VE3ZN (Aug 2025); KFF-POTA cross reference (2018); KFF County Database, KA2LHO et al., 2025-02-08.
Only ref-to-ref pairs from these lists are in this repo (`data/wwff-xref-sources.json`). The lists themselves are not.

## What it does
- `.github/scripts/kpc_wwff_links.py build` writes one row per WWFF ref:
  - US: `data/wwff-xref-KFF-1.json` (KFF-0001 to 3999) and `-2.json` (KFF-4000 and up), 7,450 rows in all. It is split in two to stay well under the 1 MB cap.
  - Canada: `data/wwff-xref-VEFF.json`, 5,264 rows.

  Columns: wwff_ref, wwff_name, region, pota_ref, link_source, status, distance_km, checked_date, note.
- It also writes the list for a person, `data/wwff-xref-review.csv`. That list holds every proposed and conflict row, plus the hand rows.
- The site uses **confirmed** links only:
  - `kpc_search_lists.py` mk_k fills column 8 of locations.json (daily, through kpc_new_refs.py). A row with no link gets the confirmed link. A link the row already has is kept, unless a hand decision or a confirmed link marked `replaces site link` says otherwise (see the rules). Kentucky still comes from kpc-ky-data.json `p`.
  - `kpc_canada.py` (nightly) adds `[None, potaRef]` to every VEFF row of data/canada.json, the same shape as locations.json. potaRef is blank when there is no confirmed link.
- `kpc-ref-check.yml` (Mondays) rebuilds the cross reference after the overlay and saves the files. If an input is short, or the confirmed links would drop by more than a fifth, nothing is written and last week's files stay.
- Standard library only, no network. No pin is moved. POTA rows are never changed.

## Rules
### Sources
- **repo**: locations.json column 8 as it was on Nov 14. This copy is frozen, so a link the writer adds is never counted again as a second source. Kentucky `p` also counts as repo.
- **community-KFF-2025**: the main US community list ('WWFF USA', territories included).
  - A ref it lists with several POTA parks counts only for its clear primary: the same number, else the one park with the same name. The others are noted. With no clear primary, all of them are listed and the row is a conflict. Only KFF-0680 has several parks (US-0680 and US-8081 to 8090); its primary is US-0680.
  - A ref it gives no POTA park ('WWFF not in POTA', 210 refs, or its 'Deleted' sheet, 110 refs) is evidence against any link. If a source still names a park, the row is a conflict; if none does, it is none.
- **community-KFF-2018**: the weaker list. KFF-n = US-n for 0001 to 4446, except 3791, plus 81 explicit pairs. Where the 2025 list covers the ref and says otherwise, the 2018 value is left out (the note says so).
- **community-VEFF-2025**: 3,766 live pairs. The 232 struck-through rows are left out.
- **rule-name-distance**: same normalised name, the same state or province, exactly one such park within 5 km.
- **rule-same-name-close-pin** (owner decision, 2026-11-14):
  - the same normalised name (type words may be dropped only if both sides then match exactly);
  - the same state or province;
  - pins within 1.0 km;
  - exactly ONE such park.

  This is enough on its own to confirm.
- **hand**: a line in the sources file, or a person's answer in the review list.
- **Checked, not used:** the proposed-reference sheet of 2025-02-07. Its 14 filled rows are all in the 2025 list and agree with it. Its IUCN and WDPA columns were never read into any file.

### Status
- **confirmed** needs all of these:
  - two sources name the same park, or the close-pin rule alone does;
  - the park is on today's POTA list;
  - POTA lists the park in the WWFF area's state or province.

  A park that POTA lists in several states counts in each of them. A hand decision is always confirmed.
- **Two sources against the site's one:** the site's link may be the only source for one park while the 2025 list, backed by the 2018 list or the close-pin rule, names another. Then the 2025 value is confirmed, and its note begins `replaces site link`. Only these rows, and hand rows, change an existing link. One source alone never does.
- **proposed**: only one source, or the park fails the active or same-state check.
- **conflict**: the sources name different parks, or the 2025 list gives the ref no park while a source names one. All the parks are listed, with `|` between them.
- **none**: no source names a park.
- **Territories** (PR-, VI-, AS-, GU-, UM-, AQ- in the 2025 list) are not on the US list the site reads. They stay proposed, with a note.

## Counts (real data, Nov 14)
| | confirmed | proposed | conflict | none |
|---|---|---|---|---|
| US (KFF) | 6,833 | 268 | 64 | 285 |
| Canada (VEFF) | 3,252 | 667 | 11 | 1,334 |

The review list has 1,013 rows.

## Links that change (locations.json, next kpc-new-refs run after merge)
| WWFF | site now | becomes | why |
|---|---|---|---|
| KFF-0302 Bogue Chitto (LA) | US-2357 | US-0302 | 2025 + 2018 + name rule |
| KFF-2357 Bogue Chitto | US-0302 | US-2357 | 2025 + 2018 + close pin |
| KFF-0465 Desert | US-0464 | US-0465 | 2025 + 2018 |
| KFF-0646 Buffalo | US-7270 | US-0646 | 2025 + 2018 |
| KFF-0680 Gateway (NY) | US-8082 | US-0680 | 2025 primary + 2018; the 2025 list also gives US-8081 to 8090, including US-8082 |
| KFF-1542 Sterling | US-1511 | US-1542 | 2025 + 2018 + close pin |
| KFF-2776 Cherokee Area at Grand Lake | US-6344 | US-2776 | 2025 + 2018 |
| KFF-2805 Spavinaw Area at Grand Lake | US-6376 | US-2805 | 2025 + 2018 |
| KFF-4666 Farm Island | US-8162 | US-8163 | 2025 + close pin |
| KFF-4800 Cherokee | US-2776 | US-6344 | 2025 + close pin |
| KFF-6705 Conner | US-6705 | US-6444 | 2025 + close pin; the old link was 1,621 km away |
| KFF-4642 Caribou (UT) | US-4575 | US-4475 | hand |
| KFF-4643 Caribou (WY) | US-4575 | US-4475 | hand |
| KFF-4645 Targhee (WY) | US-4575 | US-4475 | hand |

Nothing else changes.

- Two of the 10 direct-range disagreements do not change: KFF-4255 and KFF-4304. There the 2025 list sides with the site, not with 2018.
  - KFF-4255 is confirmed for the site's US-4304.
  - KFF-4304 is a conflict, because the close-pin rule says US-4304.
- These site vs 2025 disagreements stay conflicts, and the site keeps its link:
  - KFF-4618: the 2025 list alone; POTA lists the site's US-0465 only in another state.
  - KFF-4833: only the 5 km rule backs the 2025 list.
  - KFF-4853: the 2025 list also deletes the ref.
  - KFF-5977: the close-pin rule backs the site, and the 2025 value is not on today's POTA list.
- KFF-5012, KFF-6863 and KFF-6881 have a link from a source, but the 2025 list says they are not in POTA. They are conflicts.

## Rows that gain a link
- **locations.json:** 504 KFF rows.
  - 390 by the close-pin rule alone;
  - 114 by the 2025 list plus the 2018 list or a name rule.
- **New refs (7000 and up):** of the 499 with no link, 346 are confirmed.
- **data/canada.json:** 3,252 of 5,264 VEFF rows get a link.

## Canada
- **Disagreements:** these stay conflicts, as community vs rule:
  - VEFF-0871: CA-0871 vs CA-6594
  - VEFF-1246: CA-4081 vs CA-4080
  - VEFF-2137: CA-3839 vs CA-3838
  - VEFF-2176: CA-4080 vs CA-4081
  - VEFF-2379: CA-2062 vs CA-0038
  - VEFF-4287: CA-3123 vs CA-0671

  More conflicts were added by the close-pin rule.
- **VEFF-2501:** the community list gives it two parks, so it is a conflict.

## For a person (data/wwff-xref-review.csv)
- **person_decision:**
  - `yes` takes the row's single pota_ref;
  - a POTA ref takes that park;
  - `no` means never written.

  Answers are kept from week to week and count as hand decisions. A line in the sources file `hand` wins over the review list.
- **wwff-unmapped.json** is not used as a source, because nobody knows where it came from. It has 452 POTA refs for rows that locations.json leaves blank.

## Checks
- Rules hashes before and after (`kpc_area_hash.py hashes`): US d4ebfafce438, CA ba480fa34fb6, world 158325de87ce, 2-fers cef323de4c9a. They are unchanged.
- `python3 tests/test_wwff_links_nov14.py` runs the synthetic cases and then the real lists. It reads the real lists from KPC-Data: set `KPC_DATA`, or put the checkout next to this repo.
- No WDPA ids, protectedplanet links or IUCN categories are in any file.
