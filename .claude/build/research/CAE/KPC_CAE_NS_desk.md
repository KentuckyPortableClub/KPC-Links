# Canada East: NOVA SCOTIA (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only. I cannot query polygons, so "covers" comes from the publisher text. CANADA RULES: federal first; WDPA never; plain Crown land is not a park; water layer = National Hydro Network (NHN).
Key: 489 parks, 168 with no outline (66 NHS, 38 Provincial Parks, 34 National Heritage Sites).

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| Protected areas (national parks, NWAs, **Wilderness Areas, Nature Reserves, selected provincial parks**, selected land trust properties and easements) | "The Nova Scotia Protected Areas System": data.novascotia.ca/datasets/ticv-5du5 (GeoJSON export https://data.novascotia.ca/api/geospatial/ticv-5du5?method=export&format=GeoJSON), mirrored at geo.ca record 21a1cbdc-7a9d-cdf0-d272-6dbb965e97dc (A) | NS Environment and Climate Change | no dataset date shown; licence id "ns-oglns" (NS Open Government Licence; terms not read) | in key ('Nova Scotia ', 'NS-PPA') |
| Provincial parks | 'NS-PPA' / 'Nova Scotia ' in key. Note: the Protected Areas System has only **"selected" provincial parks**, so many are missing — that is why 38 provincial parks show as unjoined (Fort Point Lighthouse CA-0461, Lawrencetown Beach CA-0465, Scots Bay, Sherbrooke, Trout Brook) | NS Lands and Forestry | | PARTLY |
| Crown land | 'NS-F111' (key) | NS | **Crown land mix**: layer holds Crown land of all uses — not a park layer | in key — **check** |
| NHS / Heritage | 'NS-NHS' | Parks Canada | | pin only |

## 2. Parks with no outline (168)
- **38 Provincial Parks:** day-use beach and roadside parks (Lawrencetown Beach CA-0465, Fort Point Lighthouse CA-0461): the NS provincial parks polygons were not found as an open layer; the Protected Areas System lists "selected" parks. Check the NS Topographic Database / NS Property Online (B, not opened). **UNCOVERED.**
- Cole Harbour–Lawrencetown Coastal Heritage Park CA-5426 (joined) overlaps Lawrencetown Beach PP CA-0465 (not): a same-land pair.
- Cliffs of Fundy Geopark CA-5435: UNESCO Global Geopark, no boundary rule: pin.
- 66 NHS + 34 National Heritage Sites: pin.

## 3. Trails
Trans Canada Trail / Rails to Trails: none read.

## 4. Tricky land
- **Mi'kmaq lands and Wilderness Areas in the Mi'kmaq Treaty region:** Kejimkujik CA-0042 / Kejimkujik Seaside Adjunct CA-0043 is both a national park and a National Historic Site (Mi'kmaq cultural landscape). **Grey area CAE-5** (co-managed with Mi'kmaq).
- Land trust "easements" are on private land by agreement: not park land. 
- Water: Bay of Fundy tides, Bras d'Or Lake (inland sea). Use NHN + tidal limit.

## 5. KNOWN-GOOD layers
1. NS Protected Areas System (data.novascotia.ca ticv-5du5)
2. Parks Canada places; CPCAD
3. NHN water

## 6. 2-fers to expect
Confident (C): Kejimkujik NP vs Kejimkujik Seaside Adjunct (neighbours, not overlap); Cape Breton Highlands NP CA-0013 vs adjoining Wilderness Areas (side by side). Hard: Cole Harbour–Lawrencetown vs Lawrencetown Beach PP.
