# KPC Canada "Hard Look" – Reviewer Summary

**Workbook:** KPC_Canada_HardLook_progress.xlsx, Parks tab, columns P–U. All 1,608 rows are filled. No rows, columns or sheets were moved or renamed.

**Sources:** Every answer comes from an official government or agency source. No OpenStreetMap, Google, AllTrails, Protected Planet or Wikipedia. Every layer URL was checked with curl.

## Results

| Status | Rows | What to do with it |
|---|---|---|
| GIS FOUND | 490 | A named park polygon or line. Check it first; these are usually solid. |
| PARCEL | 619 | Land parcel or federal property record at the pin. Check the owner and size. |
| NAME SOLVED | 95 | The park was renamed, merged or misspelled. The note gives the official name and source. |
| PDF MAP ONLY | 76 | Official map file, no live layer. |
| UNOFFICIAL MAP | 23 | Only a non-government map exists. Low value. |
| NOT FOUND | 305 | Searched; the note says where and why nothing fit. |

### By province

| Prov | GIS | Parcel | Name | PDF | Unoff. | Not found | Total |
|---|---|---|---|---|---|---|---|
| AB | 13 | 18 | 2 | 2 | 1 | 29 | 65 |
| BC | 17 | 15 | 3 | 0 | 3 | 3 | 41 |
| MB | 28 | 44 | 2 | 2 | 0 | 13 | 89 |
| NB | 48 | 179 | 0 | 1 | 1 | 14 | 243 |
| NL | 18 | 22 | 4 | 0 | 0 | 23 | 67 |
| NS | 63 | 44 | 3 | 2 | 3 | 52 | 167 |
| NT | 4 | 36 | 1 | 0 | 1 | 9 | 51 |
| NU | 5 | 0 | 0 | 0 | 0 | 9 | 14 |
| ON | 114 | 39 | 28 | 18 | 0 | 49 | 248 |
| PE | 7 | 27 | 1 | 0 | 0 | 0 | 35 |
| QC | 93 | 164 | 22 | 30 | 13 | 71 | 393 |
| SK | 25 | 23 | 28 | 2 | 1 | 31 | 110 |
| YT | 55 | 8 | 1 | 19 | 0 | 2 | 85 |

## How to read the Notes (column U)

Each note says **WHERE** we looked, **WHAT** was solved, **WHY** the record is this park, and a **CONFIDENCE** of sure, likely or weak. Graded notes: 375 sure, 537 likely and 236 weak. Most of the rest are NOT FOUND rows, which have no grade. **Review weak rows first.** Most weak rows are parcels where the pin falls in the lot but the owner isn't confirmed, and the note says what to look up (for example SNB PLANET or the PEI PID lookup).

**Text searches that help:**
- Search column U for **"checker"**. About 420 rows ask you to confirm something specific.
- Search for **"PIN OFF"** or **"pin"**. About 180 rows say the POTA pin is wrong, and usually give the corrected location.

## Things to watch for

1. **Wrong pins are common.** The POTA API returns the same coordinates as the sheet, so it can't catch them. We found the real location from official addresses (DFHD, historicplaces.ca, provincial civic address points, federal property points).
2. **Renamed parks vs. column O.** Some records column O rejected as "a different place" are really the same park under a new name. Example: row 727, Prairie Coulees, renamed Hargrave Coulees Natural Area in 2020 (Alberta record 477). Please reconsider those rejections.
3. **The checker can give false "no hit" results.** This happens when the pin sits on a road or shoreline just outside the polygon, or when the name field is unusual. Examples: Sherbrooke, Fredericton, Courtin Island, and row 1331, which reuses DFRP FeatureServer/4.
4. **Federal property (DFRP) points:** PARCEL rows citing a DFRP property number point to a federal record, which is often a point, not an outline. Object IDs are not property numbers.
5. **Big parent parcels:** a few PARCEL answers are the whole parent property. Example: row 1272 Green Gables is the whole PEI National Park parcel. The note says so.
6. **Places that changed hands or were delisted:** Alberta sites that left the parks system in 2024, Saskatchewan changes in 2021, and churches sold privately. The notes give dates.

## Why most NOT FOUND rows stay not found
- Plaque-sized federal sites or lighthouses with only a point record, no outline.
- Newfoundland wharves and post offices.
- Ontario conservation authorities with no public lands layer (Upper Thames, Kettle Creek, Grand River passive lands, Mattagami).
- Manitoba has no open Crown land parcel layer.
- Nature Conservancy of Canada reserves.
- Ships, buildings and underwater sites that aren't land parcels.

Several NOT FOUND notes still list candidate lots or leads for a person to check.

## Companion files
- **FINDINGS_LOG.md:** about 110 dated, source-specific lessons, including the layers that worked in each province.
- **KPC_method_updated.md:** the method document with the "break the puzzle" steps added.
