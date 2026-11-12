# Mystery parks – Nov 11, 2026 evening pass: full notes

Written Wednesday, Nov 11, 2026, about 6:10 PM CST, by the owner's outside agent (Fable, with Sonnet and Opus helpers). This file explains everything in the hand-back. It replaces `MYSTERY_PARKS_NOV11_PASS.md` and `MYSTERY_PARKS_NOV11_PASS_v2.md`.

## 1. What you are holding

| File | What it is |
|---|---|
| `mystery-parks-answers-nov11-final.csv` | **The hand-back.** 256 of the 366 parks in `mystery-parks-open.csv`. Answer columns only, plus official-point columns. Replaces the two earlier answers files. |
| `research-sources-nov11-additions.csv` | 22 new or updated GIS / document sources, in the same 12 columns as `research-sources-all.csv`. Append them to the ledger. |
| `MYSTERY_PARKS_NOV11_NOTES.md` | This file. |

Input was the updated zip (`mystery-parks-nov11_1.zip`): 366 truly open parks. The 288 parks in `found-waiting-world-key.csv` and everything in `solved-since.csv` were **not touched**. No ref was renamed, added, re-sorted into another file, or deleted, and no left-hand column was changed.

## 2. How to read the answers file

### Columns
| Column | Meaning |
|---|---|
| `ref`, `name`, `country`, `state_province` | Copied from the open list so a person can read the row. Not changed. |
| `answer` | `match`, `no boundary exists`, `wrong pin`, `other`, or blank. Same vocabulary as Nov 5 (see below). |
| `official_source_url` | One official URL for the answer. |
| `padus_id` | Left empty this pass (no new PAD-US work). |
| `other_official_id` | Registry id with a prefix, e.g. `ZNIEFF:260030337`, `NRHP:66000682`, `FAA:U92`, `WIDNR-PROP:8840`, `DO-Ley:202-04`. |
| `correct_lat`, `correct_lon` | Empty on every row. No official map gave us a corrected position for a wrong pin, so none was invented. |
| `official_point_lat`, `official_point_lon` | **New.** An official agency point for the place, where the agency publishes one. This is NOT a corrected POTA pin and NOT a boundary. |
| `official_point_kind` | Where the point came from: `agency GIS point`, `agency page`, `NRHP point`, `FAA`, `state tourism listing`, or `address only` (address recorded in the note, no coordinates). |
| `official_point_id`, `official_point_source_url` | The record id and the page or layer the point was read from. |
| `official_point_km_from_pota_pin` | Straight-line distance from the POTA pin to the official point. Anything over about 2 km deserves a look. |
| `notes` | Layered notes. Each later pass added a section, separated by ` || ` and opened with a tag in square brackets (see below). The first section is the main finding. |
| `researched_by` | Who did the work (see below). |

### Answer vocabulary, as used today
- **match** – an official record exists for exactly this named place and points to a real boundary (a GIS feature, an official map, or limits written into law). Check the note for flags: *renamed*, *name differs*, *NRHP listing boundary*, *legal description only*, *pin N km outside*.
- **no boundary exists** – the official source shows a road, a roadside marker, a route or a single monument. There is no land unit to outline.
- **wrong pin** – the official record exists under an exact, unique name but lies more than 25 km from the POTA pin. The pin is not moved; the row is flagged.
- **other** – always starts `NEEDS-PERSON:`. The agency confirms the place but publishes no outline, or the name / kind / piece does not line up. The candidate, its id, owner and size are in the note.
- **blank** – nothing official was found. The note says exactly what was searched so nobody repeats it.

### Note tags
| Tag | What that section is |
|---|---|
| (no tag, first section) | The main research finding from the first helper on that row. |
| `[NRHP sweep]` | Result of checking the Park Service's National Register layer at the pin. |
| `[WFS/EEA pin test]` | Browser pin test against the French national layer or the European Natura layer. |
| `[State GIS]`, `[State agency check]` | What the state agency's own layer shows at the pin. |
| `[Follow-up]` | Second look at the 15 "no boundary exists" rows. |
| `[Legal record]` | The creating law, decree or gazette notice (dead-end countries). |
| `[Official record]` | Airstrip, trail and river records. |
| `[Official point]`, `[Official address, no coordinates]` | Where the official point or address came from. |
| `[FAA record, browser 2026-11-11]` | The FAA airport record for the four Idaho airstrips. |

### `researched_by`
- `Sonnet`, `Opus` – helper agents did the research on that row (136 rows in the first round).
- `Fable (browser check on Sonnet lead)` – I tested the helper's lead against the agency layer in the browser and set the answer.
- `Fable (note only; Nov 5 answer unchanged)` – I added an explanation; the Nov 5 answer stands.
- `(Nov 5 answer unchanged)` followed by a helper name – the row keeps its Nov 5 answer; later helpers only added evidence or an official point.
- Anything after ` + ` names later passes that added to the row.

## 3. Results

| answer | US | CA | world | total |
|---|--:|--:|--:|--:|
| match | 18 | 1 | 30 | 49 |
| no boundary exists | 15 | 0 | 0 | 15 |
| wrong pin | 0 | 0 | 5 | 5 |
| other (NEEDS-PERSON) | 144 | 4 | 24 | 172 |
| blank (search noted) | 7 | 0 | 8 | 15 |
| **rows in the file** | 184 | 5 | 67 | **256** |

42 of the 49 matches are new today. The other 7 are US Nov 5 matches carried with a note on why the released key still shows a pin.

Official points: **53 rows have official coordinates and 7 more have an official address.**

## 4. What was done, pass by pass

| # | Who | Method | Rows | Outcome |
|--:|---|---|--:|---|
| 1 | 5 Sonnet + 1 Opus | Web research: the managing agency's own page or document for every park with no Nov 5 answer (92 US, 4 CA, 40 world). Every cited page was opened. | 136 | 21 match, 15 no boundary, 5 wrong pin, 82 other, 13 blank |
| 2 | Fable | Browser: agency layers queried by name and by a box round the pin, then point-in-polygon on our side. BLM Idaho/California, Wisconsin DNR, SWFWMD, Tennessee TDEC. | ~25 | 3 matches (Johnson, Sette, Wysong); units and negatives noted |
| 3 | Fable | Read the key fields for the 17 Nov 5 matches still graded pin. | 17 | Causes written into notes (section 6) |
| 4 | Sonnet (browser) | National Register sweep: every historic-type US pin against the Park Service points and polygons, 1.5 km window. | 65 | 8 polygon matches, 12 name-matched points, rest nothing |
| 5 | Sonnet (browser) | Europe: pin-tested today's French ids on the Géoplateforme; searched round the three unfound French pins; Romania and Estonia on the Natura layer. | 13 | France 9 of 9; RO confirmed; EE evidence; Poland skipped |
| 6 | Sonnet (browser) | State layers: Washington DNR, South Florida WMD, Arkansas G&F, Utah DWR. | 18 | No named polygons; parcel and point evidence added |
| 7 | Sonnet (browser + web) | Second look at the 15 "no boundary exists" rows for an official line, point or polygon. | 15 | All 15 stand; ids and points added |
| 8 | Sonnet (web) | Documents first for the "no official GIS" countries: creating laws, decrees, gazettes. | 27 | 9 match, 13 other, 5 blank |
| 9 | Sonnet (browser + web) | State units stuck on "only the parent found": MI, VT, NJ, MO, WI, AR, IL, LA, OH, ND, MS, CT, FL, NE. | 26 | No new matches; points and facts added |
| 10 | Fable (browser) | Official points for BLM sites from BLM's national Recreation Sites point layer. | 57 | 30 points; 27 have none |
| 11 | Sonnet (web) | FAA / state records for airstrips; agency records for trails and rivers. | 22 | Ids, lengths, 9 points |
| 12 | 2 Sonnet (browser + web) | Official points for every remaining US/CA row without an outline. | 84 | 17 points, 7 addresses, 60 none published |
| 13 | Fable (browser) | FAA airport records for the four Idaho airstrips. | 4 | Reference point and acreage for all four |

## 5. Matches, grouped by how strong they are

**Agency layer, pin tested (strongest)**
- US-10184 Johnson SWA = WI DNR "Deer Park SHA-WPRA", 213.18 ac, **pin inside**. DNR's page states the rename; acreage agrees.
- US-10195 Sette SWA = WI DNR "New Richmond SHA-WPRA", 77.21 ac, **pin inside**. Same evidence.
- US-7374 Wysong Park = SWFWMD "Wysong Lock And Dam", 4.31 ac fee, pin 0.01 km. Name differs between the land record and the recreation page – flag.
- France, all nine: FR-10548 (marine ZNIEFF 93M000091, **pin inside**), FR-10432 (Conservatoire du littoral FR1100689, 2.8 km), FR-11106 (protection perimeter FR9500105, 3.6 km), FR-11650 (ZNIEFF 410030308, 2.6 km), FR-12366 (910030146, 3.3 km), FR-13422 (260030337, 7.0 km), FR-14049 (820032056, 2.8 km), FR-14482 (830005446, 2.6 km), FR-14979 (260014888, **13.1 km – owner no, 2026-11-11**: the live join comes off; not a match).
- RO-0880 Pădurea Homița = Natura **ROSAC0159** in the 2024 data (61 ha, 2.4 km). The management plan calls it ROSCI0159; use the current code.

**National Register listing boundary (official, but a listing boundary is not automatically the park – confirm each; the layer has no acreage)**
- Pin inside: US-13474 Kyle Ranch, US-11820 Miller Brothers 101 Ranch, US-12735 Saline Courthouse. US-10274 Palmito Ranch Battlefield is **not a match** (owner, 2026-11-11): the National Register record is the whole 6,908-acre battlefield (the bigger place); it needs the Texas Historical Commission site outline.
- Within 0.45 km: US-8142 Fort Washita, US-3493 Nine-Mile Prairie, US-10521 Garnet, US-7975 Glen Echo.

**Official record found; pin not tested against a polygon**
- CA-2506 Saskeram WMA – Manitoba Reg. 171/2001 s.6(58), Plan No. 20475.
- Mexico (SEMARNAT/CONANP federal table): MX-0016, MX-0141 (pin 16.6 km off, inside the separate Sian Ka'an reserve), MX-0147 (officially an Área de Protección de Flora y Fauna), MX-0180 (Área de Protección de Recursos Naturales), MX-0191, MX-0221.
- Chile (creation decrees; copies are hosted by the Ministry of Education – check): CL-0012, CL-0037, CL-0049.
- PT-0382 Litoral Norte – Decreto Regulamentar 6/2005 settles the kind question. NZ-0051 – ECan's own park page (map image only).

**Boundary written into law, no map file**
- DO-0027, DO-0085, DO-0095, DO-0132 – Ley 202-04 art. 37 (article numbers for two not confirmed).
- BZ-0033, BZ-0034 – Forest Reserves (Consolidation) Order.
- GT-0005 – Decreto 55-2003. LK-0026 – Gazette Extraordinary 2247/3. UY-0049 – Decreto 343/2014 (official category differs from POTA's).

## 6. Why some Nov 5 matches are still pins
- **US-4376 Manhattan Project NHP** – filed under US-NM, but the pin is at Oak Ridge, Tennessee. A state-filtered join finds nothing. Join on park code MAPR with no state filter; the park has three units.
- **US-0754 Rosie the Riveter, US-11900 Blackwell School** – both records are in the PAD-US *Proclamation* layer, and the key says "no candidate". That layer is probably missing from the saved copies. (An inference from the key field, not something I could see on the box.)
- **US-6261 Pogue Creek Canyon** – Tennessee's own layer has a 58-acre piece 6.7 km away; PAD-US has 3,608 acres with the pin 0.2 km outside. The state layer is the incomplete one.
- **US-6259 Ozone Falls** – absent from the state layer; PAD-US is the only official polygon.
- **US-11297 Morgan Bar** – BLM Idaho has no site polygon; the pin is inside the Salmon River SRMA (the bigger place). The 6-acre PAD-US easement is the only site-sized record.
- **US-8422 Pope John Paul II Park** – not checked; the Massachusetts server failed its robots check.
- **Canada (8 rows)** – all are the over-15-km pin rule, held for the owner. Not researched again.

## 7. Official points – what they are and are not
Club rule tonight: where an agency publishes no outline, record the official point.
- A point was taken only from an official record that names this place: the agency's page, its own point layer, the National Register point, an FAA record, or a state tourism department listing.
- **Never** from the POTA pin, a geocoded address, the centre of a bigger park, or any unofficial site.
- The point does not change the answer. Rows with a point are still `other` (or `no boundary exists`).
- Breakdown: 30 BLM recreation-site points, 9 agency pages, 8 National Register points, 4 FAA records, 2 state tourism listings, 7 address only.
- **Idaho airstrips (FAA, effective 2026-10-29):** Antelope Valley U92 – 24 ac; Big Southern Butte U46 – 7 ac; Cavanaugh Bay 66S – 25 ac; Garden Valley U88 – 25 ac. All public, managed by the Idaho Division of Aeronautics, reference points within 40 m of the POTA pins. FAA marks the points "estimated" and gives acreage but no boundary.
- **Points far from the pin:** US-11309 Cutthroat Trout Campground (28 km – probable wrong pin), US-11640 Scipio (5.1 km, state tourism listing, no owner named), US-11318 Sage Hen Flats (2.2 km), US-12224 Bruneau River Take-Out (2.1 km, and not proven to be the POTA place).
- **Caveats:** Sandsage Bison Range's point is the headquarters building; the Boulder City hangar point is from a draft nomination; Shoup Bridge's point could not be re-opened tonight; Twin Points is converted from degrees and decimal minutes; three BLM trail points (Mansard, Four Bear, Paint Rock) are page map markers.
- **No official point published:** Nevada markers and byways, most Oklahoma Historical Society pages, 27 BLM pins, North Dakota forests, TVA, South Florida WMD pages, Sail Park and Pinson Mine airstrips (no FAA record found).

## 8. Pins to look at
MX-0140, MX-0145, MX-0176, MX-0181 (28–40 km) · NZ-0720 (33 km) · US-11309 (28 km) · FR-14979 (13 km) · MX-0186 (pin in Sinaloa; the federal reserve is Nayarit only) · KE-0018 Nairobi NP (about 15 km south of the park by the agency's description) · EE-0015 and EE-0060 (pins inside the neighbouring Natura site) · US-6043 Honeymoon Trail (filed Arizona; BLM's page and the pin are Utah).

## 9. Settled negatives – do not search these again
- BLM publishes no site-level polygons at state level: Idaho has only SRMAs, Wyoming points, Utah congressional areas, Nevada nothing, California nothing at Laguna Mountain.
- No polygon named for the mystery unit in: Washington DNR, South Florida WMD, Arkansas G&F, New Jersey DEP, Missouri MDC, Michigan, Vermont (points only), Utah DWR.
- Nevada DOT has no scenic-byway layer. All 15 "no boundary exists" rows stand.
- Tennessee's natural-areas layer is incomplete; a miss there proves nothing.
- The National Register public layer withholds sensitive sites (Spiro Mounds, Fort Towson are absent).

## 10. House rules – how they were kept
- Official sources only. Wikipedia, OSM, WDPA, Google and hiking sites were leads at most.
- **Never contacted:** any `services*.arcgis.com` host, `apps.fs.usda.gov`, `ncnhde.natureserve.org`, the Grant County NM server.
- Robots file read before each host was queried in the browser; one request every 2 seconds or slower per host (4 seconds when two workers shared a host).
- **Hosts skipped because the robots check failed:** ndgishub.nd.gov (503), sdi.gdos.gov.pl (403), arcgisserver.digital.mass.gov (502), gis.wildlifedepartment.com, gis.ksoutdoors.com, gisservices.gov.mb.ca (no answer).
- **Two things to know:** (1) one helper read pages on shpo.nv.gov, dot.nv.gov and fhwaapps.fhwa.dot.gov before checking their robots files; all three turned out to allow it. (2) The EEA host answers its robots request by redirecting to the services page; that was treated as "no rules", as on Nov 5.
- Nothing was downloaded to the owner's computer. No POTA pin was moved. No coordinates were invented.

## 11. What is left, and whose it is
| Left | Rows | Whose |
|---|--:|---|
| Japan | 47 | The box. `JP_A10_crosswalk.csv` gives each POTA park's exact Japanese name in the official layer (the box's phonetic spellings never matched POTA's). Join on that name, then pin-test. 21 of the 47 are kind questions; 26 need the join run. |
| Australia | 27 | Decisions: 19 already have a Nov 5 record (11 under the WA licence hold), 6 kind questions ("state beach" is not a land category), 2 far pins, 1 (Beenak G183) with no record found twice. |
| Canada | 11 | The far-pin rule (owner decision pending) (8 held, 3 wrong pin). |
| Robots-failed hosts | ~11 | Retry another day: ND state forests, PL-1911, MA Pope John Paul II Park, OK/KS wildlife lands, Saskeram pin test. |
| Hand downloads | 20+ | CONANP shapefile (MX ×11), Texas THC historic sites, CONAF SNASPE (CL), Swedish heritage dataset (SE-1697), ECan park map, CT DEEP property layer, FWS cadastral (Alberding Lagoon). Not fetched. |
| NEEDS-PERSON rows | 172 | the owner: point-only sites, units inside bigger parks, renamed or re-categorised places, places that are not what POTA calls them. Each note names the candidate. |

## 12. Citations to double-check before relying on them
- Chile: decree copies are on a Ministry of Education host; the China Muerta decree number came from a scan.
- Dominican Republic: the article numbers for Alto Bao and Lagunas de Bávaro were not confirmed; the law cited for DO-0117 appears to be a traffic law.
- Mexico: the id field holds the official category and name, not CONANP's numeric id.
- Wisconsin unit pages (Pleasant Valley, Swinging Gate, Adell): the DNR map PDFs were linked but not opened.
- France: the licence text of the extra Géoplateforme layers was not re-read tonight.
