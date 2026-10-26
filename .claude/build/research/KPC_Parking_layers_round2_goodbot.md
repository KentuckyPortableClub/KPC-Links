# Parking / trailhead / entrance / boat-ramp point layers, round 2 (Brandon's bot, tested 2026-10-26: all esriGeometryPoint, no login, counts from returnCountOnly)
Format: address | name field | type field | count | flags. HQ verdict in [brackets].

## Finished from round 1
- VA DWR boating access | https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_Boating_Access_Locations/FeatureServer/0 | SITENAME | TYPE (codes) / Type_of_Ramp | 237 | mixed owners (DWR 86) [USE, by PLACE only]
- UT DWR Walk-In Access | https://utility.arcgis.com/usrsvcs/servers/f90d840222e946ddb9f0978dc38d9d78/rest/services/ram/ram_WIA_PROD_v2/MapServer/0 | UDWR.DWRADMIN.DWR_PROPERTIES.PropName | PointTypeID (73 parking, 16 access) | 107 | LEASED PRIVATE LAND, names are landowners [SKIP: never publish private landowner names; WIA is not a POTA park anyway]
- AZ State Parks TrailAccess | https://services2.arcgis.com/gdcQ6sUWKP8qwBmV/arcgis/rest/services/TrailAccess/FeatureServer/0 | AccessName + MngUnit | Parking | 1310 | 2014 data, only 77 managed by AZ State Parks [USE by PLACE only; label 2014]
- AZGFD boat ramps | https://utility.arcgis.com/usrsvcs/servers/2045fa1bcdbc4b309f887f4cba94790b/rest/services/FishandBoat_reference/FeatureServer/2 | Name + Waterbody | none | 135 | mixed owners [USE by PLACE only]
- AZGFD wildlife area rec points | https://services2.arcgis.com/os1CphwIyxBDDUGn/arcgis/rest/services/Wildlife_Area_Rec_Points/FeatureServer/0 | - | - | 23 (12 trailheads, 1 launch) | 2019, 7 areas [USE]
## No-data states
- KS: parks/wildlife areas NOT FOUND; KDWP river access https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/River_Access_STWD_2022/FeatureServer/0 | RiverName | 82 [USE by PLACE]; ksoutdoors.gov 403
- MS: BLOCKED (MDWFP certificate)
- NM State Parks https://gis.emnrd.nm.gov/arcgis/rest/services/SPDView/NM_State_Parks/FeatureServer/3 (parking 11), /1 (trailheads 13), /6 (boating 4) | Park | partial [USE]
- NMDGF boat ramps https://services2.arcgis.com/CjbW1bVhK4dB3WOa/arcgis/rest/services/Boat_Ramps/FeatureServer/1 | Water_name | Ramp_type | 67 | mixed [USE by PLACE]
- NMDGF fishing access https://services2.arcgis.com/CjbW1bVhK4dB3WOa/arcgis/rest/services/Fishing_Access/FeatureServer/0 | Access_Name / Name_Working | Access_Type | 476 [USE by PLACE]
- SD: login (403) [SKIP]
- MT FWP fishing access sites https://services3.arcgis.com/Cdxz8r11hT0MGzg1/arcgis/rest/services/FWPLND_FAS_POINTS/FeatureServer/0 | NAME | BOAT_FAC | 337 [USE: FAS are POTA parks in MT]
- MT State Parks facilities https://services3.arcgis.com/Cdxz8r11hT0MGzg1/arcgis/rest/services/FWPLND_STATEPARKS_FACILITIES_PTS/FeatureServer/0 | SITE_NAME | FAC_TYPE (195 parking, 37 trailheads, 32 ramps) | 2129 [USE, filter FAC_TYPE]
- MT State Parks trailheads https://services3.arcgis.com/Cdxz8r11hT0MGzg1/arcgis/rest/services/Montana_State_Parks_Trailheads/FeatureServer/0 | SITE_NAME + TH_NAME | 108 [USE]
- HI State Parking Inventory https://services.arcgis.com/HQ0xoN0EzDPBOEci/arcgis/rest/services/State_Parking_Inventory/FeatureServer/0 | Site_Locat | Dpt_Agency (14 State Parks) | 185 | licence 'For Review Only' [SKIP: licence]
## Thin states
- TN State Parks recreation assets https://services5.arcgis.com/bPacKTm9cauMXVfn/arcgis/rest/services/TN_State_Parks_Recreation_Assets_(Public_View)/FeatureServer/0 | Park (code) + Name | Asset_Type (339 parking, 335 trailheads, 65 ramps) | 2278 [USE, filter Asset_Type]
- TN State Parks entrances https://services5.arcgis.com/bPacKTm9cauMXVfn/arcgis/rest/services/Park_Entrances_January/FeatureServer/0 | ParkFullName | EntranceType | 336 [USE]
- TN State Parks hiking assets https://services5.arcgis.com/bPacKTm9cauMXVfn/arcgis/rest/services/Public_Hiking_Assets_TN_State_Parks/FeatureServer/0 | 1468 | overlaps the assets layer [SKIP unless the first misses trailheads]
- TWRA WMA entrances https://services3.arcgis.com/PWXNAH2YKmZY7lBq/arcgis/rest/services/WMA_Entrances/FeatureServer/0 | WMA | all entrances | 385 [USE]
- TWRA access sites https://services3.arcgis.com/PWXNAH2YKmZY7lBq/arcgis/rest/services/AllAccessSites/FeatureServer/0 | Name | Type (716 boat launches) | 1120 [USE by PLACE]
- IN DNR fishing access https://gisdata.in.gov/server/rest/services/Hosted/Fish_Access_RO/FeatureServer/0 | site_name | boat_ramp yes/no | 1036 [USE by PLACE]; IN parking/trailheads NOT FOUND
- NCWRC boating access areas https://services1.arcgis.com/YfqBAUM5nWR3yhGP/arcgis/rest/services/NCWRC_Boating_Access_Areas_view/FeatureServer/0 | BAA_Name | 267 [USE by PLACE]; NC State Parks NOT FOUND
- NV State Parks https://arcgis.water.nv.gov/arcgis/rest/services/Hosted/Nevada_State_Parks_Reservation_Web_Map/FeatureServer/1 | systemname | type (96 parking, 29 trailheads, 17 launches) | 494 | 12 parks, 68 unnamed [USE; unnamed by PLACE]
- NDOW WMA points https://services.arcgis.com/RyxlXSfFi87rAosq/arcgis/rest/services/Wildlife_Management_Area_Point_Features/FeatureServer/0 | Source | Feature (102 parking) | 252, 9 WMAs [USE]
- LDWF boat ramps https://services1.arcgis.com/6euNCaGPCgCzgAVF/arcgis/rest/services/BoatRamps05152025/FeatureServer/0 | Boat_Launch | 735 | ~200 PRIVATE ramps [USE by PLACE only, drop private if an owner field exists]
- ADF&G launch ramps https://services.arcgis.com/VdkVOAHovLuozJG4/arcgis/rest/services/Sport_Fishing_Opportunities_and_Access_DRAFT/FeatureServer/2 | Name | 181 | DRAFT [USE by PLACE, label draft]
- WGFD habitat area facilities https://services6.arcgis.com/cWzdqIyxbijuhPLw/arcgis/rest/services/WHMA_Facilities/FeatureServer/1 | WHMA_Name | FacilityType (152 parking, 16 ramps) | 519 [USE]
- WGFD public access area facilities https://services6.arcgis.com/cWzdqIyxbijuhPLw/arcgis/rest/services/PAA_Facilities/FeatureServer/3 | PAA_Name | FacilityType (236 parking, 96 ramps) | 569 [USE]
- WY State Parks structures https://services1.arcgis.com/WOPmQY9FJsLgGOzw/arcgis/rest/services/BuildingsStructures_Reservations/FeatureServer/0 | Facility_1 | Building_T (34 ramps, 17 trailheads, 4 entrances) | 1457 [USE, filter]
- ND G&F fishing waters https://ndgishub.nd.gov/arcgis/rest/services/Applications/GNF_FishingWaters/MapServer/4 | Location_Name | UNIT_TYPE (434 ramps) | 2197 [USE ramps, by PLACE]; ND WMA parking /GNF_GeneralInformation/MapServer/54 (65, Oahe only) [USE]; PLOTS + state park parking NOT FOUND
