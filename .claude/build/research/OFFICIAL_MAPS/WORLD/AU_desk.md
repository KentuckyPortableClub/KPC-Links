# Australia (AU) official park maps (desk, Oct 28 2026)
Our key: 10,272 parks. Types: Reserve 2,286; State Forest 1,343; State Beach 1,231; Nature Reserve 954; National Park 749; Nature Park 474; Conservation Area 450; Wild & Scenic River 354. Grades: A opened, B search result only, C inference.
| State / agency | Where maps live and address pattern | Date method | Rules page | Status |
|---|---|---|---|---|
| **NSW National Parks (NPWS)** | PDF per park: nationalparks.nsw.gov.au/-/media/npws/maps/pdfs/parks/<park-slug>/<park-slug>-map.pdf (A: royal-national-park; B: border-ranges, eurobodalla, warranmadhaa); older style .../-/media/visitor/files/pdf/maps/<name>-pdf-map.pdf (B: werrikimbe, nymboida, hat-head, cathedral-rock, new-england) | printed on the map: 'Published 24-Mar-2026' (A, Royal NP); no version number | park page 'Know before you go' / alerts (BOT LOOK-UP) | READY for a bot (slug = park name lowercased, hyphens) |
| **Queensland Parks (DETSI/DESI)** | parks.qld.gov.au/parks/<park>/maps-resources and parks.desi.qld.gov.au/parks/<park>/maps-resources (A: crows-nest); page lists map names but the opened text showed NO file addresses (links load by script) | none | park pages 'Park management' (BOT LOOK-UP) | NEEDS A BROWSER BOT; two host names exist (old/new), handle both |
| **Parks Victoria** | park pages parkweb.vic.gov.au/explore/parks/<park>; visitor guides as PDFs; Forest/reserve maps at forestsandreserves.vic.gov.au/__data/assets/pdf_file/<id>/<file>.pdf (B: Brataualung Forest Park map, name carries 'July 2018') | date in the file name sometimes (B) | BOT LOOK-UP | NEEDS A BROWSER BOT; Avenza store (store.avenza.com) sells/holds Parks Victoria georeferenced maps (B) |
| **WA DBCA** | exploreparks.dbca.wa.gov.au (park pages; new site parks.dbca.wa.gov.au/park/<park>, B) and exploreparks.dbca.wa.gov.au/sites/default/files/<YYYY-MM>/<file>.pdf (B: western-australias-national-parks.pdf, 2022-04) | upload month in the path (B) | BOT LOOK-UP | NEEDS A BROWSER BOT |
| **SA, Tasmania, NT, ACT** | not searched (SA: parks.sa.gov.au; Tas: parks.tas.gov.au; NT: nt.gov.au/leisure/parks-reserves; ACT: environment.act.gov.au) | | | BOT LOOK-UP (addresses C) |
| **State forests (Forestry Corp NSW, VicForests etc.)** | many 'State Forest' (1,343 parks) are production forest, public access varies | | | grey area, below |
## Boundary layers (to chat 9)
- CAPAD (national protected-area database, DCCEEW): list in data/world-gis-sources.json (Brandon's xlsx); not re-checked.
- Crown land layers per state (W2 note: Crown land layer = public-land source): BOT LOOK-UP.
## Grey areas for Brandon (AU)
- State Beach (1,231 parks): beaches are often council/Crown reserve with no map of their own: pin only?
- State Forest (1,343): production forest with public access limited by operations: public + open test needed.
- 'Reserve' (2,286): mixed council/Crown reserves.
