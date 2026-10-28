# Scoreboard: world key (28 countries), by country and park type (desk, Oct 27 2026 night)
Read only. Source: `data/world-key/XX.json` (this clone). Every row is in `KPC_Scoreboard_World.csv`. Order = world-stages.md (W1-W25; the Baltic pack EE LT LV LU last). Same method as the North America scoreboard: pin-only types apart (city/generic 'Park', beaches, recreation parks, historic/heritage/monument, local walks as pins, botanical gardens, small natural monuments), line types apart (trails, parkways), the rest = 'name mismatch' (the matcher holds a near-miss to check) or 'no layer found'.

Important: **'with outline' abroad mostly means a European (EEA) or national-register outline, not an ownership map.** Outlines exist for most countries, but ownership and public-access data do not (see KPC_2fer_Preflight_World_desk.md), so these counts show OUTLINE holes only, not 2-fer readiness. The 'Park' type (city/generic) is pin-only by the house rule.

## Totals
**55,876 parks; 39,749 with an outline; 16,127 without.** Pin-only 7,027, line 1,516, name mismatch 3,879, no layer 3,705: real outline gap about **7,584**.

## By country (POTA activity order)
| Step | Country | Activations | Parks | With outline | Without | Pin-only | Line | Mismatch | No layer |
|---|---|---|---|---|---|---|---|---|---|
| W1 | GB | 42831 | 7,074 | 3,288 | 3,786 | 1,612 | 409 | 592 | 1,173 |
| W2 | AU | 20396 | 10,272 | 6,977 | 3,295 | 1,531 | 420 | 615 | 729 |
| W3 | JP | 128611 | 1,217 | 185 | 1,032 | 789 | 0 | 0 | 243 |
| W4 | DE | 33286 | 1,265 | 683 | 582 | 269 | 135 | 122 | 56 |
| W5 | PL | 30529 | 2,982 | 2,691 | 291 | 31 | 0 | 159 | 101 |
| W6 | FR | 17455 | 14,367 | 13,102 | 1,265 | 361 | 0 | 721 | 183 |
| W7 | ES | 13230 | 2,497 | 1,789 | 708 | 108 | 195 | 271 | 134 |
| W8 | IT | 11925 | 2,167 | 1,919 | 248 | 21 | 0 | 122 | 105 |
| W9 | NO | 6360 | 3,337 | 3,044 | 293 | 53 | 8 | 52 | 180 |
| W10 | NL | 5322 | 312 | 81 | 231 | 84 | 3 | 96 | 48 |
| W11 | CH | 5009 | 319 | 261 | 58 | 15 | 8 | 17 | 18 |
| W12 | PT | 4208 | 410 | 223 | 187 | 4 | 0 | 101 | 82 |
| W13 | RO | 4182 | 1,334 | 305 | 1,029 | 528 | 78 | 215 | 208 |
| W14 | AT | 3946 | 420 | 273 | 147 | 71 | 10 | 47 | 19 |
| W15 | SE | 3682 | 2,224 | 2,016 | 208 | 110 | 17 | 55 | 26 |
| W16 | SI | 2853 | 1,181 | 137 | 1,044 | 814 | 108 | 76 | 46 |
| W17 | CZ | 2091 | 232 | 193 | 39 | 20 | 0 | 2 | 17 |
| W18 | BE | 2050 | 593 | 164 | 429 | 64 | 1 | 254 | 110 |
| W19 | DK | 1829 | 291 | 106 | 185 | 95 | 1 | 49 | 40 |
| W20 | IE | 1492 | 307 | 96 | 211 | 37 | 12 | 50 | 112 |
| W21 | SK | 792 | 352 | 83 | 269 | 254 | 0 | 12 | 3 |
| W22 | HR | 686 | 381 | 366 | 15 | 8 | 0 | 6 | 1 |
| W23 | FI | 673 | 1,838 | 1,592 | 246 | 15 | 0 | 197 | 34 |
| W24 | HU | 325 | 244 | 23 | 221 | 67 | 107 | 21 | 26 |
| W25 | EE | 723 (pack) | 155 | 72 | 83 | 63 | 4 | 10 | 6 |
| W25 | LT |  | 38 | 28 | 10 | 0 | 0 | 9 | 1 |
| W25 | LV |  | 14 | 7 | 7 | 3 | 0 | 4 | 0 |
| W25 | LU |  | 53 | 45 | 8 | 0 | 0 | 4 | 4 |

## The 20 biggest country × type gaps
| # | Country | Park type | Total | Without | Gap | Mismatch | No layer |
|---|---|---|---|---|---|---|---|
| 1 | GB | Nature Reserve | 1,558 | 603 | 603 | 204 | 399 |
| 2 | AU | Reserve | 2,286 | 521 | 521 | 360 | 161 |
| 3 | AU | State Forest | 1,343 | 491 | 491 | 92 | 399 |
| 4 | FR | Biological Reserve | 11,195 | 408 | 408 | 321 | 87 |
| 5 | GB | Country Park | 803 | 399 | 399 | 87 | 312 |
| 6 | FR | Conservation Area | 406 | 317 | 317 | 237 | 80 |
| 7 | JP | Prefectural Nature Park | 306 | 216 | 216 | 0 | 216 |
| 8 | PL | Nature and Landscape Complex | 246 | 213 | 213 | 116 | 97 |
| 9 | ES | Wetland Reserve | 220 | 200 | 200 | 114 | 86 |
| 10 | BE | Nature Reserve | 265 | 198 | 198 | 145 | 53 |
| 11 | GB | Reserve | 191 | 187 | 187 | 56 | 131 |
| 12 | NO | National Recreation Area | 159 | 159 | 159 | 17 | 142 |
| 13 | RO | Natural Area | 138 | 128 | 128 | 45 | 83 |
| 14 | FI | State Nature Preserve | 288 | 127 | 127 | 120 | 7 |
| 15 | IT | Other Conservation Area | 144 | 114 | 114 | 38 | 76 |
| 16 | GB | RSPB Reserve | 149 | 94 | 94 | 49 | 45 |
| 17 | GB | Forest Reserve | 92 | 91 | 91 | 17 | 74 |
| 18 | BE | National Park | 128 | 91 | 91 | 58 | 33 |
| 19 | IE | National Forest | 73 | 73 | 73 | 19 | 54 |
| 20 | AU | Conservation Area | 450 | 69 | 69 | 25 | 44 |