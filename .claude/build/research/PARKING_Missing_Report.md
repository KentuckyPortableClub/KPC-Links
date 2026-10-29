# PARKING / ACCESS: MISSING REPORT (chat 9, Oct 29 2026 ~9:55 AM CDT; HQ 9:38 AM step 1)
Made only from files we already have (no look-ups, no keyed calls). A park is MISSING when its POTA number has no parking / access point in our access files: KPC-Data `data/access/US-XX.json` (outside KY) or, in Kentucky, `kpc-ky-data.json` parks[].ap + `official-park-access.json` trailheads.

**Totals:** outside Kentucky 6,424 of 13,083 POTA parks have NO point (49%). Kentucky: 2 of 193.

## Kentucky, by name
- US-3791 Trail of Tears National Historic Trail (National / NPS)
- US-4572 Lewis and Clark National Historic Trail (National / NPS)

## By state (worst first): parks / missing / share
| state | POTA parks | missing | share |
|---|---|---|---|
| MS | 155 | 155 | 100% |
| SD | 120 | 120 | 100% |
| HI | 102 | 102 | 100% |
| DC | 35 | 35 | 100% |
| KS | 145 | 138 | 95% |
| NV | 367 | 334 | 91% |
| NM | 123 | 108 | 87% |
| UT | 692 | 605 | 87% |
| AZ | 123 | 107 | 86% |
| AK | 179 | 146 | 81% |
| LA | 123 | 99 | 80% |
| WY | 294 | 234 | 79% |
| ND | 155 | 117 | 75% |
| ID | 362 | 260 | 71% |
| NC | 253 | 174 | 68% |
| OR | 440 | 282 | 64% |
| MD | 186 | 117 | 62% |
| AL | 155 | 92 | 59% |
| IN | 229 | 135 | 58% |
| NH | 206 | 115 | 55% |
| MI | 388 | 216 | 55% |
| OK | 205 | 113 | 55% |
| AR | 306 | 160 | 52% |
| RI | 61 | 31 | 50% |
| MA | 421 | 203 | 48% |
| TN | 277 | 132 | 47% |
| ME | 148 | 70 | 47% |
| IL | 219 | 102 | 46% |
| VA | 184 | 84 | 45% |
| WA | 536 | 243 | 45% |
| TX | 222 | 95 | 42% |
| MT | 254 | 103 | 40% |
| NE | 198 | 79 | 39% |
| GA | 237 | 92 | 38% |
| CA | 410 | 148 | 36% |
| NY | 851 | 307 | 36% |
| WV | 172 | 56 | 32% |
| MN | 298 | 97 | 32% |
| DE | 89 | 28 | 31% |
| FL | 460 | 135 | 29% |
| CO | 276 | 78 | 28% |
| SC | 167 | 42 | 25% |
| CT | 157 | 38 | 24% |
| OH | 276 | 65 | 23% |
| IA | 181 | 40 | 22% |
| VT | 109 | 24 | 22% |
| NJ | 134 | 26 | 19% |
| WI | 348 | 58 | 16% |
| PA | 494 | 46 | 9% |
| MO | 561 | 38 | 6% |

**No access file at all:** DC, HI, MS, SD (every park missing).

## Missing parks by park type (all states outside KY, top 25)
| type | missing |
|---|---|
| Wildlife Management Area | 692 |
| State Park | 542 |
| BLM Recreation Management Area | 498 |
| National Wildlife Refuge | 442 |
| State Forest | 418 |
| State Recreation Area | 269 |
| State Historic Site | 257 |
| State Fishing Lake | 187 |
| Wilderness Area | 187 |
| National Forest | 161 |
| State Wildlife Area | 138 |
| BLM Herd Management Area | 130 |
| National Monument | 124 |
| State Nature Preserve | 124 |
| National Historic Trail | 118 |
| National Historic Site | 118 |
| State Conservation Area | 112 |
| State Game Land | 106 |
| State Trail | 98 |
| State Fish Hatchery | 97 |
| State Natural Area | 95 |
| National Park | 75 |
| National Wild and Scenic River | 74 |
| State Historical Monument | 69 |
| National Historical Park | 68 |

Notes: trail parks (National / State Trails) and water trails are LINE parks: a trailhead is their access point, so they belong to the trails data rather than parking. 'Recreation Management Area' (BLM, UT/ID/NV/WY/OR) is the biggest single group. The full per-park list (ref, name, type) is in `PARKING_Missing_list.json` next to this file, for the step-2 pull (waits on HQ's go).
