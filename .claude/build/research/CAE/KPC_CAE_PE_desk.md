# Canada East: PRINCE EDWARD ISLAND (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only. I cannot query polygons, so "covers" comes from the publisher text. CANADA RULES: federal first; WDPA never; plain Crown land is not a park; water layer = National Hydro Network (NHN).
Key: 53 parks, 36 with no outline (14 Provincial Parks).

## 1. Official boundaries
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| Provincial parks | PEI GIS data (gov.pe.ca / "PEI GIS Data" index, B). **I found no open polygon layer for PEI provincial parks.** PEI sells GIS data (gpei.ca GIS price list, B); some layers are free on the PEI Land Cover / Open Data page. | PEI Dept of Environment, Energy | unknown; **no licence read; may be a paid / licensed product** | 'PE-PP' in key (source unconfirmed) |
| National park | Prince Edward Island National Park CA-0076 | Parks Canada | OGL-Canada | in key |
| CPCAD | fallback for provincial parks (PEI reports them to CPCAD) | ECCC | not stated (A) | in key |

## 2. Parks with no outline (36)
All 14 Provincial Parks (Basin Head CA-0852, Belmont, Chelton Beach, Linkletter, Northumberland, Red Point, Sally's Beach, Tea Hill, Wood Islands, Jacques Cartier). Likely cause: **the PE-PP layer is an old or point-style set and these names differ** (check the layer's name field first: "Basin Head Provincial Park" vs "Basin Head"). If it is a name mismatch, fuzzy match fixes it; if not, **CPCAD is the safe fallback**.

## 3. Trails
Confederation Trail (rail line, province): not read.

## 4. Tricky land
- PEI is >90 % private land; provincial parks are small. Public-access shoreline vs private beach: the water line test matters.
- **Mi'kmaq reserves (Lennox Island, Abegweit)**: no park numbers found.

## 5. KNOWN-GOOD
CPCAD; Parks Canada; NHN; the PEI Open Data portal (find).

## 6. 2-fers
Few. Likely none except PEI National Park vs adjoining provincial beach parks (side by side, C).
- 2026-10-27 (desk, Round 2): still no open provincial park polygons; PE REST host gis.princeedwardisland.ca to be walked (BOT LOOK-UP 10). See KPC_BigHoles_desk.md R2-7.
