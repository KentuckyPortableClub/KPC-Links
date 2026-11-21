# World GIS layers still needed by hand

Rechecked 21 Nov 2026 (America/Chicago) against saved copies on the box and against KPC-Links / KPC-Data. The source list is the 11 Nov 2026 remaining-downloads note (30 open items then). Ontario Conservation Authorities belong on the US+Canada hand list, not here.

Park counts are how many parks in that country still lacked a joined official outline on the 11 Nov world search list. They are country totals, not a promise that one layer will cover every park. Held, withheld, or sampled parks are not named.

## House rules

- Official-agency data only. Do not use an NGO or third-party aggregator copy unless its item metadata cites a specific national-government source file; then take that original.
- `services*.arcgis.com` and other saved-copy-only hosts: saved copies only. Never fetch those hosts live.
- WDPA / Protected Planet exports stay internal (cross-reference only). Do not use them as a public outline source.
- Links only. Do not commit zips or raw layer files to this repo.

## Still open (25 items)

| Country | Parks still missing a boundary | Official page | What to get |
|---|---:|---|---|
| Argentina | 390 | https://sib.gob.ar/cartografia | Administración de Parques Nacionales (SIB) cartography. The live map and "Descargar" links are on the site; the shapefile/GeoJSON URL was not visible in a static fetch. |
| Costa Rica | 42 | https://www.sinac.go.cr/ | SINAC protected-area layer. Also check the SIGSINAC viewer and https://www.snitcr.go.cr/ (National Spatial Data Infrastructure) for a public ArcGIS/WFS service. |
| Hungary | 221 | http://geo.kvvm.hu/ | TIR viewer. No public WMS/WFS/REST found. May need contact with the ministry / okir.hu. No open-data download was found. |
| Bosnia and Herzegovina (FBiH) | 192 | https://www.e-prirodafbih.ba/ | No endpoint found on e-prirodafbih.ba; try the Federal Geodetic Administration geoportal at https://www.fgu.com.ba/ . |
| Slovenia | 1,044 | https://podatki.gov.si/dataset/zavarovana-obmocja-poligoni | ARSO protected-area polygons (Zavarovana območja). Official open-data page; eProstor metadata is https://eprostor.gov.si/imps/srv/api/records/50a097f2-99d9-417b-8ca5-dce7051f181a . The licence line on the open-data page was not a named open licence when last checked — record it before use. |
| France (INPN) | 1,248 | https://inpn.mnhn.fr/ | INPN RNN / protected-area shapes, also listed at https://www.data.gouv.fr/datasets/espaces-naturels-proteges . Some INPN sites may be down; check the PatriNat mirror at https://www.patrinat.fr/ . Country count is shared with the ONF row. |
| France (ONF) | 1,248 | https://www.data.gouv.fr/ | ONF biological reserves. The dataset page lists an `ogc:wfs` resource; the WFS base URL needs a browser click. Country count is shared with the INPN row. |
| Liechtenstein | 18 | https://opendata.swiss/ | Naturschutzgebiete via llv.li Geodata Infrastructure. The CKAN entry has no WFS/WMS link; browse llv.li for the layer. |
| Ukraine | 114 | https://eco.mepr.gov.ua/ | e-cadastre interactive map. No documented OGC endpoint; inspect network requests while the map loads. |
| Lithuania | 10 | https://stvk.lt/ | VSTT State Cadastre of Protected Areas (STVK). Agency page: https://vstt.lrv.lt/en/cadastre/ . The 11 Nov note found only a request-form process; recheck whether the cadastre now offers a public spatial download. |
| Russia | 8,766 | https://ooptaari.nextgis.ru/ | NextGIS OOPT polygon layer. Browse the resource tree for the resource id, then use the standard WFS/GeoJSON export. |
| Moldova | 232 | https://ieg.asm.md/ | Ministerul Mediului / ieg.asm.md viewer. https://dataset.gov.md/ had no spatial resources when checked. |
| Slovakia | 268 | https://www.sopsr.sk/ | SOP SR map portal. No endpoint surfaced by search; likely an embedded map app. |
| Bulgaria | 212 | https://eea.government.bg/zpo | ExEA/IAOS register viewer. No WFS/WMS found. Do not fall back to the European EEA WISE dataset in place of the national layer. |
| Estonia | 83 | https://geoportaal.maaruum.ee/ | Maa-amet / Maaruum public WMS/WFS services page. Direct fetch was blocked; visit in a browser for the GetCapabilities URL. |
| Greece | 64 | https://www.gov.gr/ | YPEN Natura 2000 viewer entry point; follow through to the INSPIRE geoportal/viewer. |
| Korea (Mountain Safety Map) | 1,287 | https://www.forest.go.kr/ | Korea Forest Service "산옥안전지도" (sanlog.forest.go.kr or the Forest Service portal). Confirm it has park-boundary polygons, not only trail or safety markers. Country count is all Korean parks still missing a boundary. |
| Thailand | 859 | https://www.dnp.go.th/ | Department of National Parks. Check https://gis.dnp.go.th/ and portal.dnp.go.th for a public REST/WFS service. |
| Cook Islands | 16 | https://pacificdata.org/ | National Environment Service. No public national GIS portal was found. First step: SPREP Pacific Data Hub item metadata — use it only if it cites an NES source file, not a SPREP-derived polygon. |
| Niue | 2 | https://pacificdata.org/ | Same SPREP check as Cook Islands: original Niue government shapefile only. |
| Micronesia (FSM) | 45 | https://pacificdata.org/ | Fragmented by state (Chuuk, Kosrae, Pohnpei, Yap). Same SPREP original-source check. |
| Nauru | 2 | https://pacificdata.org/ | No public GIS portal found. Same SPREP original-source check; this may be a dead end. |
| Ghana | 12 | https://fc.gov.gh/wildlife-division/ | Forestry Commission / Wildlife Division. No public GIS/REST endpoint found; may need a direct request. |
| DR Congo | 9 | | No known public DRC GIS service. A WRI Congo Basin forest-atlas layer is acceptable only if it cites ICCN (the DRC park authority) as the original source, not if it is WRI's own derived product. |
| Jamaica | 15 | https://www.data.gov.jm/ | Forestry Department / NEPA. Check data.gov.jm and NEPA's own site for a protected-areas layer. |

The 1,248 France figure is one country total, listed on both France rows. Across these countries the 11 Nov list had 15,151 parks still missing a boundary (Russia is 8,766 of that).

## Dropped after the 21 Nov recheck

- **Korea — Hamyang-gun local park.** The official shapefile is already on the box in the sources/downloads tree (Hamyang-gun wildlife protection zone, dated 7 May 2026). It still needs a merge into the key, not a new download. The Mountain Safety Map row above stays open.
- **Ontario Conservation Authorities.** These are Canada, not world. Three authorities still need a person to check their official pages (Hamilton, Nottawasaga Valley, Long Point Region). Lake Simcoe Region CA is already on the Canada key layer list (`ON-LSRCA`) and is not a hand download.

Layers already covered by saved country copies or earlier hand bundles (AT, AU, GB, IE, JP, and the 11-layer Nov 11 bundle) stay off this list.
