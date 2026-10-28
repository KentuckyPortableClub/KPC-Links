# Federal agencies, once (desk, Oct 28 2026)
Grades: A = opened, B = seen in a search result only (direct fetch of these sites is blocked from the desk), C = inference.

| Agency | List / map page pattern | Date method | Status |
|---|---|---|---|
| NPS | nps.gov/<unit code>/planyourvisit/maps.htm (A, bot-confirmed in earlier checks) | none on page; bot records read day | READY for a bot |
| US Forest Service | fs.usda.gov/main/<forest>/maps-pubs ("Visitor Maps and Guides"), also fs.usda.gov/r05/<forest>/maps-guides in Region 5 (B: lpnf, cleveland, blackhills, lassen, sierra, inyo, superior, cnnf, srnf) | none seen | NEEDS A BROWSER BOT (page lists load by script, C) |
| US Fish & Wildlife | fws.gov/refuge/<slug>/library lists the refuge's files (B: monte-vista, alamosa, cross-creeks, mathews-brake, pond-creek...); files at fws.gov/media/<title-slug> (e.g. media/montezuma-public-use-map-2021pdf, media/anahuac-trail-map-brohure-mar-2023) | the slug often carries the year or month ("2021", "mar-2023", "uploaded-august") (B) | READY for a bot, slugs need the library page |
| BLM | blm.gov/documents/<state>/public-room/map/<title-slug> (B: indian-valleywalker-ridge, price-recreation-area-georeferenced-map, lake-coeur-d-alene-recreation-sites-map, white-mountains-national-recreation-area); also .../public-room/brochure/<slug> | slug sometimes has a year (e.g. lacks-creek-management-area-map-2019, 2026-wyoming-recreation-guide-map) | NEEDS A BROWSER BOT |
| Army Corps | lake sites vary by district: swf-wc.usace.army.mil/<lake>/images/<LAKE>_OVERALL_RECREATION_MAP.pdf (B: Belton); corpslakes.erdc.dren.mil/visitors/ (status, reserve pages); campground maps on cdn.recreation.gov/webphotos/facilitymaps/<id>_<code>.pdf (B) | none | NEEDS A BROWSER BOT; one pattern per district |
| Parks Canada | parks.canada.ca/pn-np/<prov>/<park>/visit/... (from our 6 Quebec links, bot-confirmed); not researched further | none seen | NEEDS A BROWSER BOT |

Rules pages: not found for any federal agency from the desk. BOT LOOK-UP: NPS "Laws & Policies" per unit, USFS forest "Passes & Permits", FWS refuge "Rules and Regulations", BLM field-office page, Corps lake page.
Note: recreation.gov facility maps are a second source for USFS, Corps and some BLM sites (B).
