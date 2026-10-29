# WORLD HARVESTER: SEEDS FOR THE UNSEEDED COUNTRIES (Research desk, chat 8, Oct 29 2026)
Context: 24 of 42 countries show "done, 0 leads" because nothing was seeded (= NOT SEARCHED). Poland's three known-good servers answered but the park-word filter dropped their layers; one address is a 404 (chat 2's note). Grades: **A** = I fetched the page/document and read the address; **B** = address seen in a search result (service not opened); **C** = from memory. I cannot test-query agency servers (fetch allowlist), so every row is a seed to TRY: the harvester's own run is the test. No licence below is final until the bot prints the service's terms.

## 1. SEEDS (add to the seed script; format = servers / ogc / downloads)
| CC | Address | Type | Grade | Licence / note |
|---|---|---|---|---|
| SE | https://geodata.naturvardsverket.se/naturvardsregistret/wfs  (WMS: .../naturvardsregistret/wms) | WFS (ogc) | A (Naturvårdsverket's own address list, 2022-09-30) | open, no sign-up (page says so); this is Skyddad natur: national parks, nature reserves. Also .../n2000/wfs (Natura 2000) |
| SE | https://geodata.naturvardsverket.se/andra_skydd/wms | WMS | A | other protections; no WFS listed |
| ES | https://wms.mapama.gob.es/sig/Biodiversidad/ENP  (GetCapabilities: ?request=getcapabilities&service=wms) | WMS only | A (idee.es record) | **CC BY-SA 3.0**, credit "Ministerio para la Transición Ecológica y el Reto Demográfico"; boundaries "informative only" (so GetFeatureInfo/WMS = lead, shapes need the download page) |
| ES | https://www.miteco.gob.es/es/biodiversidad/servicios/banco-datos-naturaleza/informacion-disponible/ (descarga ENP shapefile) | download | B | already in my ES file |
| ES | https://nco.ign.es/server/rest/services/nco/ParquesNacionales/MapServer | ArcGIS server | B | IGN España; national parks |
| FI | https://gtkdata.gtk.fi/arcgis/rest/services/Tukes/suojelualueet/MapServer | ArcGIS server | B | name says 'protection areas' but sits under Tukes (safety agency): may be NOT nature. Check first |
| FI | SYKE: old https://paikkatieto.ymparisto.fi/arcgis (ended end of 2023) replaced by GeoServer; **CC BY 4.0** (syke.fi, A) | WFS | C address | bot: probe https://paikkatieto.ymparisto.fi/geoserver/wfs?request=GetCapabilities. avoindata.fi catalog gave HTTP 403 to the bot: skip it |
| CH | STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.bafu.schutzgebiete-paerke_nationaler_bedeutung  and ...schutzgebiete-schweizerischer_nationalpark | STAC (ogc) | A | licence says "proprietary" (producer FOEN/cantons): **read the opendata.swiss terms before any storing**; assets list was empty, so download link is on ckan.opendata.swiss/dataset/schweizerischer-nationalpark-und-parke-von-nationaler-bedeutung-perimeter |
| CO | https://mapas.parquesnacionales.gov.co/arcgis/rest/services/pnn/runap/FeatureServer  (+ .../IGAC/nuevas_areas/MapServer) | ArcGIS server | B | Parques Nacionales Naturales = the agency; RUNAP = national protected areas register |
| ZA | https://dffeportal.environment.gov.za/hosting/rest/services/PACA/SAPAD_Buffer/MapServer ; https://dpmegis.dpme.gov.za/arcgis/rest/services/Environmental2/MapServer/1 ("Protected Areas DFFE2022Q1") | ArcGIS | B | official DFFE SAPAD; the Western Cape copy (gis.westerncape.gov.za .../DFFE_ConservationSites/MapServer/0) is already known |
| BR | ICMBio layers via https://portal-espacial.sibbr.gov.br/ws/layers/view/more/uc_federal_pi_4326_iso88591_dbf_fix (+ _us_, state and municipal UC sets) | download listing | B | SiBBr is the Biodiversity Information System (ICMBio data); downloads, not a server |
| MX | https://serverags1.economia.gob.mx/arcgis/rest/services/SDE_EXTERNAS/CAPAS_EXTERNAS_V2/MapServer/2 ("Áreas Naturales Protegidas") | ArcGIS | B | Secretaría de Economía copy of CONANP: use as lead; CONANP's own server not found. NOAA copy: https://gis.ngdc.noaa.gov/arcgis/rest/services/GulfDataAtlas/FederalProtectedAreas_Mexico/MapServer/0 (US agency, Gulf coast only) |
| CL | https://arcgis.mma.gob.cl/server/rest/services/IDE/Biodiversidad_IDE/MapServer | ArcGIS | B | Ministerio del Medio Ambiente IDE; SNASPE and protected areas should be in its layers |
| JP | https://www.biodic.go.jp/trialSystem/EN/info/nps.html (Biodiversity Center, MoE: national parks/quasi-national parks, KML download) and https://nlftp.mlit.go.jp/ksj/ (A10 'Natural park areas' GML/shape, Japan's MLIT) | downloads | B | nothing seeded today; both are ministry sites. Licence: MLIT's 国土数値情報 terms (cite source) - bot prints it |
| NL | https://api.pdok.nl/rvo/nationale-parken-geharmoniseerd/ogc/v1 ; https://api.pdok.nl/rvo/nationaal-beschermde-gebieden-cdda/ogc/v1 | OGC API | A (my NL file) | **not yet in the seed**; PDOK = national open data, CC0 mostly |
| DE | https://geodienste.bfn.de/ogc/wfs/... (BfN Schutzgebiete) | WFS | A (my DE file) | seed has only 2 addresses; add the full BfN list |
| ZA/Cuba/other | https://gisportal.wcs.org/arcgis/rest/services/Hosted/National_Integrated_Protected_Areas_System/FeatureServer/1 (Philippines NIPAS, WCS = NGO, not official: lead only); https://gis.ngdc.noaa.gov/.../FederalProtectedAreas_Cuba/MapServer/0 | ArcGIS | B | from my X-files; unofficial/US-copy, mark as such |

## 2. Countries where I found NO harvestable server (the EEA walk is their only seed)
CZ, SK, HU, HR, SI, RO, AT, EE, LV, LT, LU, IT, FR, AR, KR, TH, PH, TR, RU, CN, DO. Notes:
- **EEA nationally designated areas** (NatDA, was CDDA): https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/CDDA_Dyna_WM/MapServer (A: ~38 countries, official EEA; description says EEA may not redistribute some sites of Estonia, Ireland, Türkiye = skip those). The harvester already walks it ONCE and gives the lead to the first country it meets: **make it write one lead PER COUNTRY** (filter by the layer's country/ISO field) or those 19 countries stay at "0 leads".
- FR: INPN download pages only (inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ep/pn, /pnr, /rnn …) = downloads (A), data.gouv.fr API already walked (it found 17 downloads).
- IT: ISPRA/NNB EUAP record exists (inspire-geoportal.ec.europa.eu record ispra_rm:Meta_NNB_EUAP01_2017, B) but no endpoint shown. Probe the INSPIRE record XML for the service URL.
- AT: inspire.gv.at / data.gv.at (BML), B only. HU: agrarstatisztika.kormany.hu 'védett natúra' data (B).

## 3. PROBLEMS IN THE RUN ITSELF (from state.json log)
1. **'done, 0 leads' with 0 seeds = NOT SEARCHED.** Print `status: not searched` when servers+ogc+agol_orgs+known_good = 0 and every catalog step errored.
2. **Catalog errors are silent:** avoindata.fi (FI) = HTTP 403, data.gov.cz (CZ) = HTTP 404: the catalog URL or the bot's user agent is wrong. Log them as a failure, not as 0 hits. (CZ's open data is data.gov.cz/sparql or a NKOD catalog: https://data.gov.cz/datové-sady is the human page, B.)
3. **Poland:** the three known-good servers answered but the park-word filter dropped their layers: for a known-good server skip the word filter, or add Polish words: 'obszar chronionego krajobrazu', 'park narodowy', 'park krajobrazowy', 'rezerwat', 'użytek ekologiczny', 'Natura 2000', 'formy ochrony'. The 404 one: drop it.
4. **AGOL searches:** most countries report hits but 'read 0': the filter rejects accounts that are not government. Fine, but log the top 3 rejected org names so I can grade.

## 4. BOT LOOK-UP rows (chat 9 can run before the harvester)
| Row | What |
|---|---|
| 1 | GET each section 1 address (GetCapabilities / ?f=pjson / STAC collection), print status, layer or feature-type names, licence/terms; 20 lines per country |
| 2 | EEA CDDA service: print layers + the country field name and counts for EE, IE, TR (restricted) vs FR, ES, IT |
| 3 | Probe FI GeoServer wfs and avoindata.fi API (with a browser user agent) |
