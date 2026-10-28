# Name mismatches, not missing layers (chat 9 list, Oct 28 2026)
HQ: LIST only, no matcher change; the name-match rule (Rule Sheet C) waits on Brandon's rulings N-1..N-10. Sources: chat 8's region summaries + BigHoles R2-9 + chat 9's probes (rounds 5-8). "Cause" says which ruling would fix it.
Causes: **T** = the layer drops the type word ('Beall Woods' vs 'Beall Woods State Park'; Rule Sheet C); **A** = accent / spelling ('Montaña', 'Finnell'); **W** = the park sits in a different record/name (unit name, district, French name); **S** = same name, different park or province (must NOT join); **P** = POTA files the park under several states (counting artifact, already joined elsewhere).

## Fixed by a source-list change (chat 9, on the holding branch)
- **NY:** NYS_Park_Polygons now reads `Label` as a second name ('Thompsons Lake State Park'; `Name` drops the type word). Expected to clear most NY park mismatches: Thompsons Lake, Iona Island, Barcelona (historic: joins only on a sure match).

## Southeast
- **AL (T/W):** De Soto SP US-1039, Butler County WMA US-12311, Kinterbish WMA US-6459, state historical parks US-13473 / 13533 / 13558, Elk River Lodge? US-6457.
- **GA (W):** Okefenokee SP US-2200 (nothing near it in the key: desk look first; Stephen C. Foster SP?), Suwannee River Eco-Lodge US-7861, Bartram + Hitchiti state forests US-4648/4649 (held in the WMA layer as 'Bartram Forest').
- **TN (T/A):** Grundy Forest + 6 State Natural Areas US-3941, 6237, 6247, 6259, 6261, 6273, 6280 (TN_Natural_Areas already read); WMAs US-3950, 7565, 7570, 7577 ('Finnel' vs 'Finnell'); state forest lands US-12775, 13514. Mountains to Sea Trail US-8313 = **P** (joined in NC).

## Midwest
- **IN (T):** Prophetstown Fen, Westercamp, Bryan Woods, J.E. Roush Lake, Spencer County SF, the 13 lake SRAs (ManagedLands_DNR_Open holds them as 'Unit on Lake'; `manager` = kind).
- **IL (T):** Beall Woods, Donnelley/DePue, Kishwaukee River, Ray Norbut, Rauchfuss Hill, North Point Marina, Washington County, Copperhead Hollow.
- **MO (T):** the three SCAs, Lost Valley, Roger Pryor, Bruce Watkins, Felix Vallé (A).
- **WI (T):** eight wildlife areas, Kohler-Andrae, four SRAs, Menominee River units.
- **MN (T):** Whitewater, McCarthy Lake, Schueler. **IA:** La Soya, Teal Basins. **ND:** Lone Tree, Little Metigoshe. **SD:** three SRAs.

## Northeast
- **VT (W):** all 14 state parks (ANR layer 38 holds forests by name; parks need a check by hand).
- **PA (T):** state forests: the BOF layer names DISTRICTS ('Tioga'), not 'Tioga State Forest' (layer not added).
- **NY:** Crystal Lake SF, Dannemora SF, Split Rock SF, Jamaica Bay SWA (DEC lands use unit codes).
- **CT:** Ferry Landing, Beckley Iron Furnace, Satan's Kingdom, Comer Memorial. **RI:** Hillsdale Preserve, Silver Spring, Beach Pond, Rome Point. **MA:** Rockdale Heights, Greycourt, Lynn Shores, Farnham-Connolly, Martini, Pope John Paul II.
- **NH:** Androscoggin Wayside, Gardner Memorial Wayside, Winslow, Max Israel, Nash Stream, White Farm, Wantastiquet, Gov. Wentworth, Taylor Saw Mill. **ME:** Little Ossippee, Dresden Bog, Bog Brook, Capitol SP, two ecological reserves.
- **MD:** Sideling Hill Creek, Idylwild, Monocacy, Sassafras, Heaters Island. **DE:** Masseys Millpond, Trussum Pond.

## South Central
- **TX (T):** all 11 State Historic Sites (join on a sure match only). **NE (T):** nine Omaha/Lincoln SRAs (Park_Areas now added: 'Alexandria SRA' style names).
- **OK (T/W):** WMAs Carl Blackwell, Selman, Camp Gruber, Sparrow Hawk; fishing lakes. **AR:** Muddy Creek WMA (two WMAs share the name: **S** check), SRAs on lakes. **KS:** Cross Timbers SP.

## Mountain West
- **CO:** Buena Vista SWA, Grenada SWA. **WY:** Packers Lake PAA, Ellis WHMA. **ID:** Ted Trueblood. **MT:** Grey Cliff (two), Big Horn, Brownes Lake.
- **NV (W):** Cave Rock + Sand Harbor (= Lake Tahoe Nevada SP units), Artesia Lake. **AZ:** Dankworth Pond, River Island. **NM:** Rock Hound.
- **BLM 'Recreation Management Area' parks (W, NOT to be stripped yet, HQ):** round 6 test: 106 of 347 unmatched names are found in BLM's site POINTS, only 11 / 7 in the two polygon layers = mostly sites (pin only). True areas to check by hand: Leslie Gulch, Klamath Hills, Diamond Craters, Logandale Trails, Cathedral Valley, Dry Valley.
- National forests (W/P): 'La Sal Mountain' = Manti-La Sal; 'Columbia River Gorge National Forest' = the Scenic Area; Sawtooth / Caribou-Targhee / Idaho Panhandle filed under another state.

## Pacific
- **CA (A/T):** Montaña de Oro (layer has 'Montaña de Oro SP': chat 2's accent fold fixes it once approved), Van Sickle, La Purisima, Tijuana Estuary, 3 State Beaches.
- **OR:** Bob Creek Wayside, Strawberry Hill Wayside, Owyhee airstrip (pin only).
- **WA (T):** all 13 State Forests ('Capitol State Forest' vs 'Capitol Forest'), Bayview SP, Chief Joseph SWA. **AK:** 10 recreation sites. **HI:** Hanauma Bay, Kawainui Marsh.

## Canada
- **Same province only (S):** La Vérendrye (ON CA-0259 is not QC CA-1027), Frontenac (QC CA-0496 is not ON CA-0219), Duck Mountain (MB CA-0538 / SK CA-0596), Cypress Hills (SK CA-0592 / AB CA-0642), Elk Island (AB NP CA-0020 / MB CA-0540), Tombstone TP CA-4636 vs NHPA CA-4635 (two designations).
- **French names (W):** Mount Royal = 'Parc du Mont-Royal' (CA-0511), Parc Angrignon (CA-0962). **NB/NS (T):** 'X Recreation Park', 'X Nature Reserve' suffixes. **ON:** most of the 255 (fuzzy). **MB:** Ethelbert (Duck Mountain) WMA CA-2410.
- **Same land, two park numbers:** Garibaldi Park Recreation Park CA-3537 / Garibaldi Provincial Park CA-0723 (show with that label).
