# Agency Atlas: US-OR
Read FIRST before searching for this state's parks. ADD what you learn (one line, dated, your chat): open-data portal URL, each agency's ArcGIS server root + folders, park-page URL pattern, statewide / county parcel map, sites that block bots, dead hosts. Never delete others' lines; mark dead ones 'DEAD <date>'.

## Layers already wired into the key (from data/state-gis.json, Oct 30)
- **Oregon Parks & Recreation Department** · server root: https://maps.prd.state.or.us/arcgis/rest/services
  - park: https://maps.prd.state.or.us/arcgis/rest/services/Land_ownership/Oregon_State_Parks/FeatureServer/0 (name field NAME)
- **Oregon Parks and Recreation Department (AGOL owner orstateparks)** · server root: https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services
  - park: https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/OPRD_Rec_Parks_view/FeatureServer/0 (name field FULL_NAME)
- **Oregon Department of Fish and Wildlife (AGOL owner ODFW_AGO)** · server root: https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services
  - wild: https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/ODFW_Wildlife_Areas/FeatureServer/0 (name field AreaName)
- **State of Oregon (all state owned and managed lands)** · server root: https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services
  - land: https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/All_State_Owned_and_Managed_Lands/FeatureServer/0 (name field NAME)
- **State of Oregon (Oregon parklands)** · server root: https://maps.prd.state.or.us/arcgis/rest/services
  - park: https://maps.prd.state.or.us/arcgis/rest/services/Land_ownership/Oregon_Parklands/FeatureServer/0 (name field PARK_NAME)
- **BLM recreation SITE polygons (national, 3,478)** · server root: https://gis.blm.gov/arcgis/rest/services
  - land: https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recs_poly/MapServer/1 (name field FET_NAME)
- **BLM Areas of Critical Environmental Concern (national, 1,120)** · server root: https://gis.blm.gov/arcgis/rest/services
  - land: https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_ACEC/MapServer/0 (name field ACEC_NAME)
- **BLM Oregon/Washington recreation management areas (2,188)** · server root: https://gis.blm.gov/orarcgis/rest/services
  - land: https://gis.blm.gov/orarcgis/rest/services/Recreation/BLM_OR_Recreation_Management_Areas/MapServer/0 (name field RMA_NAME)

## Open-data portal
- (add)

## Agency servers / folders worth walking
- (add)

## Park pages (URL pattern) + where the map link sits
- (add)

## Parcel / ownership maps (statewide or by county)
- (add)

## Blocks bots / dead / private (don't retry)
- (add)

## Agency servers / folders worth walking
- Chat 8 (Oct 30): Oregon-specific ACEC layer (separate from the national one already wired): https://gis.blm.gov/orarcgis/rest/services/Special_Management_Area/BLM_OR_Areas_of_Critical_Environmental_Concern/MapServer
