# Northeast Source Book: NEW YORK (desk, Oct 27 2026)
Key: 850 parks, 27 unjoined; sgnya NY DEC lands (services6.arcgis.com/DZHaqZm9cxOD4CWM), sgnyb NYS Parks.

## 1. Official boundaries
| Type | Layer | Publisher | Read? |
|---|---|---|---|
| DEC lands (WMAs, State Forests, Forest Preserve, Unique Areas) | sgnya. Same data at https://gisservices.dec.ny.gov/arcgis/rest/services/reference/MapServer/2 "DEC Lands" (A): polygon, CATEGORY (20+ values), MANAGE_BY, OFFICE, UPDATED; copyright blank | NYS DEC | YES |
| State parks, historic sites | sgnyb | NYS OPRHP | YES |
| Adirondack/Catskill Park | the "blue line" parks are regions, not parks: US-2001 Adirondack State Park, US-8070 Catskill State Park | Adirondack Park Agency / DEC | **NO polygon in key** |
| NYC parks (NPS Gateway NRA units, city parks) | NPS units: US-8081…8090 (Floyd Bennett, Fort Tilden, Jacob Riis, Fort Wadsworth, Miller Field, Great Kills, Canarsie Pier…) | NPS | partly |

## 2. Unjoined (27)
- **US-2001 Adirondack State Park, US-8070 Catskill State Park:** the Forest Preserve is DEC land inside the Parks' blue lines; the Parks include private land. By Brandon's agency-land rule only the state-owned Forest Preserve counts. **Name mismatch likely** (sgnya holds the land as "Forest Preserve" units).
- Name suspects: Crystal Lake SF US-12060, Dannemora SF 5197, Split Rock SF 5308, Iona Island WMA 2081, Thompsons Lake SP 2151, Barcelona Neck Cooperative State Wildlife area 8064, Jamaica Bay State Wildlife Area 8082, Canarsie Pier / Breezy Point / Miller Field / Great Kills (these are NPS Gateway units mis-typed "State Recreation Area" in POTA).
- Erie Canalway NHC (corridor, no polygon), Hamilton Grange, Ellis Island, North Country/AT/Washington-Rochambeau/Captain John Smith trails.

## 3. Trails and access
Read: parking, boat launches, park entrances, facilities, DEC boat launches. Good.

## 4. Tricky land
- **Adirondack Forest Preserve vs. private inholdings** inside the blue line.
- **Gateway NRA (NPS)** sits in NYC/NJ; city and state parks inside.
- **Cooperative areas** (Barcelona Neck "Cooperative State Wildlife area" is a county/state cooperative; private by agreement).
- Water: Long Island Sound, Great South Bay, Lake Ontario.

## 5. KNOWN-GOOD layers
1. DEC Lands (reference/MapServer/2, A) and DEC dil_land_activities
2. OPRHP parks (sgnyb)
3. NPS Gateway NRA / NPS land resources boundary
4. DEC boat launches, parking
5. APA Adirondack Park boundary (for context only)

## 6. 2-fers
Confident (B): Adirondack Park / Forest Preserve units vs. DEC Wild Forests (same DEC land listed under different names, e.g. "High Peaks Wilderness" inside Forest Preserve). Hard: Gateway NRA (NPS) vs. city and state parks inside Jamaica Bay; Fire Island NS vs. state parks (Robert Moses SP touches).
