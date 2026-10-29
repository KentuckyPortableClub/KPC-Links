# Boundary layers found Oct 29 (chat 9 probes SB2 / SB3) — for chat 2 (US key) to read in; licence per HQ rules
| state | layer (polygon) | records | name field | terms | verdict |
|---|---|---|---|---|---|
| AK | arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Recreational_ParkBoundary/MapServer/2 'ASP Park Boundary' | 157 | PARKNAME | credit 'Alaska Department of Natural Resources' | PASS (credit line) |
| UT | gis.blm.gov/utarcgis/rest/services/Recreation/BLM_UT_RecAreas/MapServer/1 'Congressionally Designated Recreation Areas' | 26 | RECS_NAME | credit 'BLM Utah State Office' | PASS (credit line); NCAs/recreation areas, not RMAs |
| ND | gis.dmr.nd.gov/dmrpublicservices/rest/services/State_Parks/MapServer/0 | 22 | UNIT_NAME | none stated | LIST (ask ND Parks) |
| ND | .../State_Forest/MapServer/0 | 27 | DESCRIPTION / UNIT_TYPE (no name field) | none stated | LIST |
| ND | .../Wildlife_Management_Areas/MapServer/0 | 374 | UNIT_NAME | none stated | LIST (ND Game & Fish) |
| LA | services1.arcgis.com/6euNCaGPCgCzgAVF/.../LDWF_WMAs_Refuges_Conservation_Areas_04262024/FeatureServer/0 | 62 | NAME (+ Own_Lease) | none stated | LIST (ask LDWF) |
| ID | services1.arcgis.com/CNPdEkvnGl65jCX8/arcgis/rest/services/IDPR_Parks_and_Facilities/FeatureServer | ? | ? | hub: 'license: none' | LIST (Idaho Parks already on the ask table) |
| SD | utility.arcgis.com/usrsvcs/servers/4787d99dcb1f4728b33f89a9eb9ae03e/rest/services/OpenData/SouthDakota_ParksAndRecreationAreas/FeatureServer (owner gfp.gis.coord) | ? | ? | none stated | probe next round |
| MS | MARIS zips MS_StateParks_2026 (62, NAME) + MS_WildlifeManagementAreas_2019 (318, Name) | | | 'no warranties / no liability' only | PASS (credit 'MARIS'); zips, the map servers list no layer ids from runners |
| WY | gis.blm.gov/wyarcgis/.../BLM_WY_ScenicBackways_HUB/MapServer/0 (LINES, 3 routes) | 3 | ROUTE_NAME | credit BLM WY | trails/lines data, for the scenic-road parks |
Access points added to data/access-layers.json Oct 29: Manitoba Waterbody Entry Points (212), BLM WY Recreation Features (1,429), BLM WY General Recreation Sites (140), Alaska State Parks facilities (87).
