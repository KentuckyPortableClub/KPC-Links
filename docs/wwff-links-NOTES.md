# WWFF to POTA links (Nov 14 2026)

Credit: VEFF-POTA cross reference list by VE3ZN (Aug 2025); KFF-POTA cross reference (2018).
Only the ref-to-ref pairs from those two lists are in this repo (`data/wwff-xref-sources.json`). The lists themselves are not.

## What it does
- `.github/scripts/kpc_wwff_links.py build` writes one row per WWFF ref:
  `data/wwff-xref-KFF.json` (US, 7,450 rows) and `data/wwff-xref-VEFF.json` (Canada, 5,264 rows).
  Columns: wwff_ref, wwff_name, region, pota_ref, link_source, status, distance_km, checked_date, note.
  It is split in two files to stay under the 1 MB cap (one file would be about 1.5 MB).
- It also writes the list for a person, `data/wwff-xref-review.csv`. That list holds every proposed and conflict row, plus the hand rows.
- The site uses **confirmed** links only:
  - `kpc_search_lists.py` mk_k fills column 8 of locations.json (daily, through kpc_new_refs.py). A row with no link gets the confirmed link. A link the row already has is kept. A hand decision replaces it. Kentucky still comes from kpc-ky-data.json `p`.
  - `kpc_canada.py` (nightly) adds `[None, potaRef]` to every VEFF row of data/canada.json, the same shape as locations.json. potaRef is blank when there is no confirmed link.
- `kpc-ref-check.yml` (Mondays) rebuilds the cross reference after the overlay and saves the three files. If an input is short, or the confirmed links would drop by more than a fifth, nothing is written and last week's files stay.
- Standard library only, no network. No pin is moved. POTA rows are never changed.

## Rules
- **Sources:**
  - **repo**: locations.json column 8 as it was on Nov 14. This copy is frozen, so a link the writer adds is never counted again as a second source. Kentucky `p` also counts as repo.
  - **community-VEFF-2025**: 3,766 live pairs. The 232 struck-through (deactivated) rows are left out.
  - **community-KFF-2018**: KFF-n = US-n for 0001 to 4446, except 3791, plus 81 explicit pairs. The PDF prints its 162 explicit rows twice, so they come to 81 pairs.
  - **rule-name-distance**: same normalised name, POTA park in the same state or province, and exactly one such park within 5 km.
  - **hand**: a line in the sources file, or a person's answer in the review list.
- **confirmed** needs all of these:
  - two sources name the same park;
  - the park is on today's POTA list;
  - POTA lists the park in the WWFF area's state or province.

  A park that POTA itself lists in several states, such as a trail or a forest, counts in each of those states. A hand decision is always confirmed.
- **proposed**: only one source, or the park fails the active or same-state check. The note gives the reason.
- **conflict**: the sources name different parks, or one source gives one WWFF ref several parks. All the parks are listed, with `|` between them.
- **none**: no source names a park.
- A POTA park may have many WWFF refs. One WWFF ref with many POTA parks is always flagged as a conflict.
- Repo plus the name rule counts as two sources. The brief's examples only named repo + community and community + rule. This choice changes nothing on the site, because those rows already have that link.

## Counts (real data, Nov 14)
| | confirmed | proposed | conflict | none |
|---|---|---|---|---|
| US (KFF) | 5,477 | 1,590 | 45 | 338 |
| Canada (VEFF) | 3,108 | 813 | 7 | 1,336 |

- **US confirmed, by sources:**
  - repo + 2018 + rule: 3,405
  - repo + rule: 1,289
  - repo + 2018: 745
  - 2018 + rule: 35
  - hand: 3
- **Canada confirmed:** all 3,108 are community + rule.
- **US proposed:**
  - 913 have only the repo link (they are already on the site and stay there);
  - 456 have only the name rule;
  - 216 have only the 2018 list (160 of them point to a POTA number that is not on today's list);
  - 5 others.
- **Review list:** 2,458 rows (52 conflict, 2,403 proposed, 3 hand).

## What changes on the site
- **locations.json** (next kpc-new-refs run after merge):
  - 35 KFF rows gain a link: KFF-0037, 0119, 0121, 0124-0128, 0147, 0902, 0971, 1639, 1642, 1643, 2208-2211, 2213-2215, 2217-2227, 3092, 3391, 3548. All 35 are 2018 + rule.
  - 3 rows change: KFF-4642, KFF-4643 and KFF-4645 go from US-4575 (Old Spanish National Historic Trail) to US-4475 (Caribou-Targhee National Forest). This is the hand fix.
  - Nothing else changes. Conflicts keep the link they have.
- **data/canada.json** (next kpc-canada run): 3,108 of 5,264 VEFF rows get a POTA link. Every reader of the file reads only POTA rows, or only columns 1-6 of a WWFF row, so the extra columns break nothing. That covers kpc-bounds.js, kpc-padus-layer.js, kpc-hunt.js and kpc-us-planner.js, the Python readers here, and the KPC-Data readers. KPC-Data gets the file through kpc-copy-from-links.yml.
- **New refs (7000 and up):** none of them gains a link yet. Of the 575, 364 unlinked refs have only the name rule (most with the WWFF pin on the POTA pin), and nothing else knows them. Under the two-source rule they wait for a person: write `yes` in `person_decision`.

## For a person (data/wwff-xref-review.csv)
- **person_decision:**
  - `yes` takes the row's single pota_ref;
  - a POTA ref (for example `US-1234`) takes that park;
  - `no` means never written to the site.

  Answers are kept from week to week and count as hand decisions. A line in the sources file `hand` wins over the review list.
- **The 10 direct-range disagreements**, as repo vs 2018:
  - KFF-0302: US-2357 vs US-0302
  - KFF-2357: US-0302 vs US-2357
  - KFF-0465: US-0464 vs US-0465
  - KFF-0646: US-7270 vs US-0646
  - KFF-0680: US-8082 vs US-0680
  - KFF-1542: US-1511 vs US-1542
  - KFF-2776: US-6344 vs US-2776
  - KFF-2805: US-6376 vs US-2805
  - KFF-4255: US-4304 vs US-4255
  - KFF-4304: US-4255 vs US-4304

  All 10 are conflicts. The site keeps today's link.
- **The 6 Canada disagreements**, as community vs rule:
  - VEFF-0871: CA-0871 vs CA-6594
  - VEFF-1246: CA-4081 vs CA-4080
  - VEFF-2137: CA-3839 vs CA-3838
  - VEFF-2176: CA-4080 vs CA-4081
  - VEFF-2379: CA-2062 vs CA-0038
  - VEFF-4287: CA-3123 vs CA-0671

  VEFF-2501 is also a conflict, because the community list gives it CA-1928 and CA-2220.
- **Other conflicts:**
  - 35 more US conflicts are mostly a same-name park nearby with a different number.
  - KFF-4853 and KFF-6705 have a site link over 1,000 km from the pin.
- **wwff-unmapped.json** is not used as a source, because nobody knows where it came from. It has 452 POTA refs for KFF rows that locations.json leaves blank. 33 of them match a confirmed link and 85 differ from the cross reference.

## Checks
- Rules hashes before and after (`kpc_area_hash.py hashes`): US d4ebfafce438, CA ba480fa34fb6, world 158325de87ce, 2-fers cef323de4c9a. They are unchanged. No key, rule or scope file is touched.
- `python3 tests/test_wwff_links_nov14.py` runs the synthetic cases and then the real lists. It reads the real lists from KPC-Data: set `KPC_DATA`, or put the checkout next to this repo.
- No WDPA ids, protectedplanet links or IUCN categories are in any file.
