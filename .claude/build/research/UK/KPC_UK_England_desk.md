# United Kingdom: ENGLAND (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only; I could not query polygons. UK RULES: official sources first; WDPA never; a whole-line park (National Park, National Landscape/AONB, NSA, SSSI, SAC/SPA) is mostly private land, so a spot needs public land (World rules W-2/W-3: right to roam does NOT make land public); forests/MoD/charity land = "agency land" only with an ownership layer. Key = data/world-key/GB.json (7,074 parks, 2,804 with no outline, 1,073 pin outside the outline, 982 to check).
## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| NNR, LNR, Country Parks, SSSI, National Parks, National Landscapes (AONB) | Natural England Open Data Geoportal (ckan.publishing.service.gov.uk / environment.data.gov.uk) | Natural England | LNR dataset: updated 13 July 2026, **OGL v3.0**, "indicative, not definitive: local authorities hold the authoritative information" (A); attribution "© Natural England copyright" + Ordnance Survey | IN KEY (6 layers) |
| **Forestry England legal boundary** (the national forest estate) | https://www.data.gov.uk/dataset/forestry-england-legal-boundary ; Forestry Commission Open Data ArcGIS https://data-forestry.opendata.arcgis.com/datasets/92ae032e23a747859630ccb662d853ee_0 ; sub-compartments: ckan "forestry-england-subcompartments2025" (B) | Forestry Commission | **updated 20 Feb 2026, OGL v3.0**, "© Forestry Commission 2026" (A). Page does not say whether it is owned or leased land (A) | **NO. TOP ADD**: covers Kielder, New Forest (Crown), Forest of Dean, Thetford and ~1,500 woods |
| National Trust "Land - Always Open" / "Limited Access" | data.gov.uk national-trust-open-data-land-always-open (ArcGIS REST); layer https://services-eu1.arcgis.com/0zuv5ZFEncBv7NQQ/ArcGIS/rest/services/Core_Data_Non_WMS/FeatureServer/50 | National Trust | metadata 13 June 2023; page names no licence, site footer says OGL v3.0 "unless otherwise stated" (A). Always Open = foot access by CRoW right **or National Trust permission**; excludes buildings, gardens, crops (A) | NO. Useful: a **charity** (not a public body) but legally "inalienable" open-to-all land |
| CRoW Act 2000 Access Layer (open country + registered common + dedicated land + FC land) | https://ckan.publishing.service.gov.uk/dataset/crow-act-2000-access-layer2 | Natural England | data updated 29 Apr 2026; page shows "No Licence Provided", land types NOT described on the page (A) | NO. Ownership-free but tells where the public may walk by right. Check licence with Natural England before storing |
| OS Open Greenspace | docs.os.uk … os-open-greenspace | Ordnance Survey | GB; updates April and October; page names no licence (A; the OS product is OGL, C) | NO. Public parks, playing fields; **council parks** (1,144 plain "Park" unjoined) are mostly these |
| National Trails | https://ckan.publishing.service.gov.uk/dataset/national-trails-england3 ; REST https://services.arcgis.com/JJzESW51TqeY9uat/ArcGIS/rest/services/National_Trails_England/FeatureServer | Natural England | updated 15 May 2026, 15 trails; "No Licence Provided" but an OGL link and NE/OS credit (A) | NO. Fixes the National Scenic Trail pins (Pennine Way GB-1231, South Downs Way GB-1264, Offa\'s Dyke GB-1122, Hadrian\'s Wall Path GB-0766) |
| Local council greenspace / Parish | councils (each own) | | | NO |
## 2. No outline
- 1,144 of 1,184 plain **Parks** (e.g. Openshaw Park GB-0417, St Nicholas Park GB-0435, Bletchley Park GB-0507): city/council/private parks: council parks = never (Brandon); OS Open Greenspace is the only open GB list.
- 603 Nature Reserves, 399 Country Parks: Wildlife Trust, RSPB, council reserves; Country Parks should be in the Natural England layer, so many are **name mismatches** ("Billesley Common Country Park" vs "Billesley Common").
- 94 RSPB Reserves (Snettisham GB-0004, Marshside GB-0024): RSPB is a **charity**; boundaries not published as open data (C).
- 91 Forest Reserves/Forest Parks: Forestry England layer.
- **Name pattern:** the POTA name often carries the European label first ("Thames Basin Heaths SPA - Hawley Common SSSI" GB-0015): strip the "SPA -" / "SAC -" prefix and the English suffix and match the SSSI name.
- Lundy Island NNR GB-0322 (NONE): Natural England probably lists it under Lundy MCZ/SSSI; name mismatch likely.
## 3. Trails / access
National Trails line (above); England Coast Path (King Charles III England Coast Path GB-0711, NONE) is in Natural England's data (B); Rights of way (public footpaths): councils, no national open file (OS Open Roads and OSM are not official).
## 4. Tricky land
- **New Forest:** the National Park (GB-0112) overlaps Forestry England crown land, commons, NNRs (Kingston Great Common GB-0079) and the New Forest SSSI. Park contains villages.
- **Peak District, Lake District, Dartmoor:** National Parks mostly **private farm land**; the 2-fer test needs the CRoW access layer or a public body owner. Lake District High Fells GB-0770 is a Conservation Area (NT-owned).
- **Dartmoor:** Dartmoor Commons plus MOD firing ranges (closures): Salisbury Plain Protected Area GB-0285 sits on MoD training land, access only when not firing.
- **Thames Basin Heaths SPA** (GB-0015, 0172, 0188, 0198, 0248, 0259, 0309, 0351…): many numbers for one SPA split into SSSI/commons/country parks. Heavy "same land, two park numbers".
- **Forestry England leased land:** some of the "national forest estate" is leased, not owned (A, page silent).
- **Crown Estate, Duchy and MoD land:** no ownership layer found (C).
## 5. KNOWN-GOOD layers (answer key)
1. Natural England NNR, LNR, Country Parks, SSSI, National Parks, National Landscapes (already in key)
2. Forestry England legal boundary (OGL, 2026)
3. NT Always Open + Limited Access
4. CRoW Access Layer (after licence check)
5. National Trails (England)
6. OS Open Greenspace (public parks)
## 6. 2-fers to expect
Confident (C/B): National Park vs NNR inside it (Peak District GB-0048 vs Dovedale NNR GB-0106; New Forest GB-0112 vs Kingston Great Common GB-0079; Dartmoor GB-0349 vs East Dartmoor Woods NNR GB-0318): all layered; the spot must be on public land (W-2). SSSI vs NNR vs Country Park stacks. Hard: Kielder Water Forest Park GB-1285 (Forestry England, NONE) vs Kielder Mires NNR GB-0300 and Northumberland National Park GB-0210; Epping Forest SSSI GB-1578 (City of London Corporation land, a public body) vs Epping Forest.
