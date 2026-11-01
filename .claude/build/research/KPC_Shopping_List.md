# KPC shopping list: what we look for, where it has come from, and how to hand finds back (chat 10, Nov 1 2026)

Please ADD to these. Anything already in the sources zip (`KPC_engine_sources.zip`) is known: skip it.

## A. What we look for (per park)

| kind | where | what counts |
|---|---|---|
| Boundary outline | US, Canada, world | the managing agency's own polygon layer (or the national / state mapping agency's), as REST / WFS / a download; trails = the agency's own line |
| Official map + page | US, Canada, world | the park's own agency page and its own map (PDF / image / map page) |
| Parking / access points | US, Canada | official parking, entrances, gates, kiosks, boat ramps, trailheads (agency point layers) |
| Campgrounds | US, Canada | official campground points / loops + day-use areas, picnic shelters, overlooks (activating spots) |
| Official acres | US, Canada | each agency's size list (CSV / XLSX / PDF table / layer field) |
| Hours, fees, closures | Kentucky only (shown) | word-for-word from the agency page |
| County parcels | US small parks / Canada (cadastre) | public parcel layers with an owner or use code (approximate only) |
| Open-data portals | everywhere | the portal's search address (ArcGIS Hub, CKAN, Socrata, INSPIRE) |

Most wanted next: **state trails** (13% of the activity on parks we're missing), then **state parks + recreation areas**, then **historic sites** (national + state), then county / city / regional parks and BLM areas. World: **RU, CN, KR, JP, NZ, TH, BR, MX, TR, AR** have no official layer yet.

## B. Never
WDPA / Protected Planet, OpenStreetMap, Google, AllTrails, Wikipedia / Wikidata geometry, tourism / app sites, sign-in ("Token Required") layers, tokens found inside public web maps, getting around robot checks.

## C. How to hand finds back (the bots read these by themselves from KPC-Data branch `intake-files`)
- **Layers:** `external-sources-<name>.json` = `{"Parks|US-1234": ["https://…/MapServer/3"], "Trail|US-4567": ["…"]}`. Or `world-sources-<name>.json` = `{"rest": {"<ref>": {"layer": "https://…/FeatureServer/0", "field": "NAME"}}, "other": {...WFS / downloads...}}`.
- **Exact records per park** (best): a Hard Look workbook `hardlook-<name>.xlsx` with the same columns (Park number, NEW official layer URL, Name field, Record id / name for THIS park, Status, Notes).
- **Maps / pages:** `docs-found-<name>.json` = `{"<ref>": {"st": "TN", "page": "…", "map": "…", "map_page": 1, "kind": "PDF", "agency": "…"}}`, plus page fixes as `docs-pagefix-<name>.csv`.
- **Parking:** `parking-hunt-<name>.json` (the same shape as parking-hunt-oct31).
- **Camping:** `camping-<name>.json` (the same shape as camping-us-oct31).
- **Acres:** `acres-<name>.json` (the same shape as acres-us-ca-oct31).
- **Portals:** `portals-<name>.json`.

Every file is tested by a bot, then graded by chat 11, before anything is used.

## D. Where our GIS has come from so far

## US: 514 layer addresses on 78 hosts

- services1.arcgis.com (93)
- services.arcgis.com (52)
- services5.arcgis.com (34)
- gis.blm.gov (29)
- services6.arcgis.com (23)
- services3.arcgis.com (20)
- services2.arcgis.com (19)
- dnrmaps.wi.gov (12)
- enterprise.firstmap.delaware.gov (11)
- gis.ohiodnr.gov (11)
- enterprise.gisdata.mn.gov (10)
- programs.iowadnr.gov (8)
- conservationgis.alabama.gov (8)
- arcgis.dnr.alaska.gov (8)
- apps.fs.usda.gov (8)
- geodataservices.wdfw.wa.gov (7)
- arcgis.water.nv.gov (6)
- geodata.hawaii.gov (6)
- gis.dnr.mo.gov (6)
- services9.arcgis.com (6)
- gisdata.in.gov (5)
- nhgeodata.unh.edu (5)
- utility.arcgis.com (5)
- gis.dnr.wa.gov (5)
- services7.arcgis.com (4)
- risegis.ri.gov (4)
- gis.ardot.gov (4)
- gis2.ohiodnr.gov (4)
- gis.colorado.gov (4)
- maps.prd.state.or.us (4)
- ca.dep.state.fl.us (4)
- services8.arcgis.com (4)
- gisblue.mdc.mo.gov (4)
- maps.gov.bc.ca (4)
- gis.arkansas.gov (3)
- gis.transportation.wv.gov (3)
- gis.myfwc.com (3)
- geo.dot.gov (3)
- anrmaps.vermont.gov (3)
- gisdnr.state.co.us (2)
- gis.saskatchewan.ca (2)
- gis.grey.ca (2)
- mapservices.nps.gov (2)
- gis.dmr.nd.gov (2)
- ncnhde.natureserve.org (2)
- gis.dcnr.pa.gov (2)
- vcris.dhr.virginia.gov (2)
- mdgeodata.md.gov (2)
- mapsdep.nj.gov (2)
- www.gis.dcnr.pa.gov (2)
- tpwd.texas.gov (2)
- tnmap.tn.gov (2)
- enterprise.firstmaptest.delaware.gov (2)
- maps2.grca.on.ca (2)
- novarocmaps.novascotia.ca (2)
- gis.princeedwardisland.ca (2)
- services.dwr.virginia.gov (2)
- gisec2.agfc.com (2)
- arcgisserver.digital.mass.gov (2)
- conservationexplorer.dcnr.pa.gov (2)
- … and 18 more hosts (full lists in the sources zip)

## Canada: 91 layer addresses on 29 hosts

- services1.arcgis.com (13)
- gis.saskatchewan.ca (8)
- servicescarto.mrnf.gouv.qc.ca (8)
- services.arcgis.com (7)
- ws.lioservices.lrc.gov.on.ca (6)
- services2.arcgis.com (5)
- maps.gov.bc.ca (4)
- gis-erd-der.gnb.ca (4)
- geospatial.alberta.ca (4)
- geo.environnement.gouv.qc.ca (3)
- www.apps.geomatics.gov.nt.ca (3)
- gis.princeedwardisland.ca (2)
- gis.grey.ca (2)
- nsgiwa.novascotia.ca (2)
- mapservices.gov.yk.ca (2)
- maps2.grca.on.ca (2)
- novarocmaps.novascotia.ca (2)
- services5.arcgis.com (2)
- services6.arcgis.com (2)
- gis.burnaby.ca (1)
- idgsi-rpgdi-arcgis.spac-pspc.gc.ca (1)
- maps-cartes.ec.gc.ca (1)
- gis.rvca.ca (1)
- gis.lsrca.on.ca (1)
- geonb.snb.ca (1)
- utility.arcgis.com (1)
- gispublic.barrie.ca (1)
- services3.arcgis.com (1)
- services.aadnc-aandc.gc.ca (1)

## World: 95 layer addresses on 37 hosts

- spatial-gis.information.qld.gov.au (11)
- services.arcgis.com (11)
- services7.arcgis.com (9)
- services-eu1.arcgis.com (9)
- bio.discomap.eea.europa.eu (8)
- gis.forest-atlas.org (4)
- services1.arcgis.com (4)
- paca.environment.gov.za (4)
- maps.sa.gov.au (3)
- services2.arcgis.com (3)
- gis.environment.gov.au (2)
- mapprod3.environment.nsw.gov.au (2)
- geoportail.oeil.nc (1)
- gis.planning.gov.bm (1)
- services6.arcgis.com (1)
- services.slip.wa.gov.au (1)
- geoservices.big.go.id (1)
- biod-gis.mapshare.vic.gov.au (1)
- geohub.necca.gov.gr (1)
- mapageneral.mineria.gob.do (1)
- portal.app.gov.mk (1)
- visor.infona.gov.py (1)
- ingtgeo.gov.cv (1)
- gis.nature.cz (1)
- geomaticasig1.semarnat.gob.mx (1)
- kartor.regeringen.ax (1)
- public-services.slip.wa.gov.au (1)
- geodata.rw (1)
- geoportal.vizugy.hu (1)
- gisapps.nsdi.gov.lk (1)
- services.thelist.tas.gov.au (1)
- services.gisqatar.org.qa (1)
- gis.us.fo (1)
- services.ga.gov.au (1)
- maps.gov.scot (1)
- mapas.msj.go.cr (1)
- arcgis.mma.gob.cl (1)

## Parking (US + CA): 248 layer addresses on 46 hosts

- services1.arcgis.com (52)
- services.arcgis.com (28)
- services2.arcgis.com (18)
- services5.arcgis.com (17)
- services3.arcgis.com (15)
- services6.arcgis.com (11)
- risegis.ri.gov (8)
- gis.dnr.mo.gov (6)
- gis.ohiodnr.gov (6)
- anrmaps.vermont.gov (5)
- conservationgis.alabama.gov (5)
- geodataservices.wdfw.wa.gov (5)
- enterprise.gisdata.mn.gov (5)
- gis.emnrd.nm.gov (4)
- www.gis.dcnr.pa.gov (4)
- enterprise.firstmap.delaware.gov (4)
- programs.iowadnr.gov (3)
- www.wildlifedepartment.com (3)
- ca.dep.state.fl.us (3)
- gisec2.agfc.com (3)
- nhgeodata.unh.edu (3)
- gisblue.mdc.mo.gov (3)
- services9.arcgis.com (2)
- gis.myfwc.com (2)
- services.dwr.virginia.gov (2)
- dnrmaps.wi.gov (2)
- maps.gov.bc.ca (2)
- gisdata.in.gov (2)
- arcgis.dnr.alaska.gov (2)
- gis.grey.ca (2)
- ws.lioservices.lrc.gov.on.ca (2)
- services8.arcgis.com (2)
- ndgishub.nd.gov (2)
- mapservices.nps.gov (2)
- gis.blm.gov (2)
- www.gis.dcnr.state.pa.us (1)
- gis.colorado.gov (1)
- mapsdep.nj.gov (1)
- geospatial.alberta.ca (1)
- utility.arcgis.com (1)
- arcgis.water.nv.gov (1)
- gis.arkansas.gov (1)
- apps.fs.usda.gov (1)
- tpwd.texas.gov (1)
- arcgisserver.digital.mass.gov (1)
- gis.saskatchewan.ca (1)

