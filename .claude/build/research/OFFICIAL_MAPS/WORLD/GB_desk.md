# United Kingdom (GB) official park maps (desk, Oct 28 2026)
Our key: 7,074 parks. Biggest types: Nature Reserve 1,558; SSSI 1,356; Park 1,184; Country Park 803; National Scenic Trail 367; NNR 314; RSPB Reserve 149; Historic Site 99. No map links on file yet (parkinfo-web.json has none for GB), so every row below is new. Grades: A opened, B search result only, C inference.

## Agencies
| Agency (who manages) | Where maps live and address pattern | Date method | Rules page | Status |
|---|---|---|---|---|
| **Forestry England** (state forests, England) | visitor map PDFs at forestryengland.uk/sites/default/files/documents/<Forest name> map.pdf (A: Wyre Forest map) | printed in the map footer ('2310 / Jun 2021', © Crown copyright) (A) | per-forest pages forestryengland.uk/<forest> (BOT LOOK-UP) | READY for a bot once forest list page is read; file names have spaces |
| **Forestry and Land Scotland** | forestryandland.gov.scot/media/<id>/<file>.pdf (B): those hits are management-plan maps, not visitor maps; visitor maps sit on each forest page (BOT LOOK-UP) | plan file names carry years (e.g. lmp-2024-2034) (B) | BOT LOOK-UP | NEEDS A BROWSER BOT |
| **Natural England** (NNRs, England) | gov.uk 'National nature reserves in <region>' pages: ONE regional PDF map, e.g. assets.publishing.service.gov.uk/media/5a7e2d33ed915d74e62249a1/nnr-east-midlands.pdf (A); not per reserve | page published 26 June 2013 (A): old; Open Government Licence v3 | NNR pages on gov.uk (BOT LOOK-UP) | maps are regional and old: use the GIS layer, not this |
| **NatureScot** (NNRs, Scotland) | per-reserve doc pages nature.scot/doc/<reserve>-national-nature-reserve-nnr-... with trail leaflets (A: Beinn Eighe, 'FOR PRINT ONLY', published 2025; no licence stated) | page date | BOT LOOK-UP | NEEDS A BROWSER BOT |
| **Natural Resources Wales** | forest/visit pages and cdn.cyfoethnaturiol.cymru/<id>/<name>.pdf (B: the hits are forest PLAN maps) | none | BOT LOOK-UP | NEEDS A BROWSER BOT |
| **RSPB** (149 reserves) | each reserve page rspb.org.uk/reserves-and-events/find-a-reserve/<reserve>/ ; maps also posted on community.rspb.org.uk/placestovisit/<reserve>/ (B) | none seen | reserve page 'visitor information' (BOT LOOK-UP) | NEEDS A BROWSER BOT |
| **National Trust, Woodland Trust, Wildlife Trusts (46 local trusts), National Parks, councils (country parks)** | many independent sites, no one pattern | varies | varies | NOT SURVEYED: too many owners; BOT LOOK-UP: take the top 30 by park count from the key's agency names |

## Boundary layers (for the outline side, to chat 9)
- NatureScot Protected Areas (WFS/WMS): ogc.nature.scot/geoserver/protectedareas/wfs (A, via spatialdata.gov.scot): layers NNR, SSSI, SAC, SPA, Ramsar, Country Parks, Regional Parks, World Heritage; reference date 2023-06-09; **Open Government Licence v3** (A).
- Natural England: NNR layers on data.gov.uk / ckan.publishing.service.gov.uk (B: 'National Nature Reserves - England'); download or Esri service address = BOT LOOK-UP.
- Scotland, Wales, England country parks have no single national layer (BOT LOOK-UP: data.gov.uk search; Esri 'Country Parks (England)').

## Grey areas for Brandon (UK)
- SSSI is a designation, not a park or public land: 1,356 of our 7,074 parks. Public access to an SSSI is often NOT allowed (private land). Needs a rule before any outline or 2-fer (public-land test, W-1/W-2).
- Right to roam / open-access land in England and Scotland is NOT public land (W-3).
- Many Wildlife Trust reserves are private charity land open to visitors: 'public + open'? needs Brandon's ruling.
