# Why parks have no outline: my reasons, with counts (chat 8, Oct 29 ~11:30 AM)
Brandon: "the names list once done with the other list: why you think we not matched, example boundary not available etc."
Facts from `scoreboard-parks.json` (nightly) plus my names work (NameMismatch, NameMismatch_Decoded, NoBoundaryHunt_Review, ClueSearch). Grades C: the reasons are my reading of names, types and agencies, not a look at every record.

## The size of it
19,194 parks. **No outline: 1,437** (US 896, Canada 541). **Pin only: 1,786** (US 631, Canada 1,155). Total 3,223 that cannot be tested for a 2-fer. Statuses in the scoreboard: 1,322 'no layer', 110 'likely name mismatch', 5 'missing'.

## The 8 reasons, biggest first
1. **The thing is a point, not an area (about 1,150 Canadian pin-only parks + 512 National Historic Sites).** Parks Canada has 512 'National Historic Site' numbers without outlines: most are plaque sites (a building, a ferry, a cabin like Abbot Pass Refuge Cabin or Athabasca Pass) where only a point exists. Also provincial heritage sites, 'Historic Site', 'National Heritage Site' (68). No agency draws a boundary because there isn't one. Honest answer: pin only; an outline only if the site is a named park.
2. **City and regional parks with no open layer (Canada: Regional Park 156, Recreation Park 179, Park 83; US city/county parks).** Examples: Mary Reimer Regional Park, Bright Angel Regional Park, Burnaby Mountain CA. These live in municipal or regional-district portals, one per city, each different; our state/province-level harvest never reads them. The biggest fixable group, with a municipal-portal harvest (BC regional districts, Metro Vancouver, Calgary, Edmonton, Winnipeg open data).
3. **BLM sites inside big units (US: BLM Recreation Management Area 388, + 35 SRMA, 33 historic, 27 airstrips).** Examples: Eagle, Walker Fork and West Fork Campgrounds (AK). Each is a small campground or trailhead that POTA numbers as its own park while the BLM layer holds only the big management area. The pin sits inside another record with a different name (NoBoundaryHunt: PIN INSIDE another area, 313). Right answer: pin only, or the campground's own small polygon where BLM publishes recreation sites.
4. **Small state sites that no layer holds (State Historic Site 109, Historical Monument 69, Fish Hatchery 57, Recreation Site 37, Fishing Lake 33).** NV Historical Monuments (Empire and Carson River Mills, Pioneer Memorial, Hastings Cutoff), AR Fish Hatcheries (Andrew H. Hulsey, Charlie Craig), AZ petroglyph sites. State agencies publish their parks, not their hatcheries and monuments. Weakest states: Utah (311), Nevada (149), Idaho (139), Wyoming (91), Mississippi (64), Washington (58).
5. **Name mismatch (110 flagged 'likely', 66 sister pairs, 36 aliases already kept).** The park exists in a layer under another name: spelling (Rockdale Heights / Highlands, Conners / Connors Marsh), abbreviation (SP, SRA, WMA), 'State Fishing Lake' vs lake name (Lloyd Vincent = Lake Vincent), capitals (Pāʻulaʻula), unit vs parent. My 8-rule code book is right 73% of the time when the pin is inside and the size fits; the clue search added 11 yesterday.
6. **Pin in the wrong place (clue search: 118 same-name layers far from the pin).** POTA's pin is off by 6-30 km, so a distance rule rejects the right record (Nash Stream, Max Israel, Priest Lake). Needs a look at the POTA link page or the agency page.
7. **Wrong join, the opposite problem (189 pairs more than 8 km apart in the wrong-joins file).** Not "no outline" but "wrong outline"; the part rule fixes it.
8. **Layer not harvested yet.** Inside the 1,322 'no layer': CA-QC 398, CA-ON 252, CA-NB 251, CA-NS 168; US-UT 311, NV 149, ID 139. Quebec and the Maritimes have provincial layers (SEPAQ, crown-land, protected-areas) that were not in the first sweep. Also fixable.

## What each fix is worth (my guess)
| Fix | Parks it could reach | Effort |
|---|---|---|
| Quebec / NB / NS / ON provincial layers | 600-900 | medium (harvest) |
| Municipal / regional-district portals (BC, AB, MB) | 300-500 | big, many portals |
| BLM recreation-site layer (sites, not RMAs) | 150-250 | small: one national layer |
| UT, NV, ID, WY state monument / hatchery / site layers | 200-300 | medium |
| Decode + clue-search aliases (names) | 100-200 | small, already running |
| Pin checks (the 8 + the 118 far ones) | 20-60 | small, needs eyes |
| Plaque-only historic sites and points | 700+ | none: stay pin only |

So of 3,223: roughly 700-800 are honest points that stay pin-only, 1,200-1,700 can be reached with new harvests, 150-300 with names and pins. About 1,000 are small sites no agency draws.

## Examples (for the page)
- Boundary not available anywhere: Abbot Pass Refuge Cabin NHS, Athabasca Pass NHS, Fort Vermilion NHS (plaque points).
- Layer exists, name differs: Rockdale Heights WMA = Rockdale Highlands WMA; Lloyd Vincent State Fishing Lake = Lake Vincent; Saddle Mt State Natural Area = Saddle Mountain.
- Small site inside a bigger record: Eagle / Walker Fork / West Fork Campground BLM (AK); Chinatown State Historical Monument sits next to Dayton State Park.
- No open layer for that type: Andrew H. Hulsey and Charlie Craig State Fish Hatcheries (AR); Empire and Carson River Mills State Historical Monument (NV).
- City / regional park: Mary Reimer Regional Park (AB), Bright Angel Regional Park (BC).
- Pin looks wrong: Nash Stream Forest NH (17.7 km from a 12,725 ac record of the same name).

ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.
