# Agency Atlas: US-DE
Read FIRST before searching for this state's parks. ADD what you learn (one line, dated, your chat): open-data portal URL, each agency's ArcGIS server root + folders, park-page URL pattern, statewide / county parcel map, sites that block bots, dead hosts. Never delete others' lines; mark dead ones 'DEAD <date>'.

## Layers already wired into the key (from data/state-gis.json, Oct 30)
- **Delaware DNREC** · server root: https://enterprise.firstmap.delaware.gov/arcgis/rest/services
  - land: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Society/DE_State_Lands/FeatureServer/0 (name field NAME)
- **Delaware Forest Service** · server root: https://enterprise.firstmap.delaware.gov/arcgis/rest/services
  - forest: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/FeatureServer/0 (name field LABEL)
- **Delaware Fish & Wildlife (DNREC)** · server root: https://enterprise.firstmap.delaware.gov/arcgis/rest/services
  - wild: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Environmental/DE_Protected_Natural_Resources/MapServer/17 (name field AREA_NAME)
- **Delaware nature preserves (DNREC)** · server root: https://enterprise.firstmap.delaware.gov/arcgis/rest/services
  - preserve: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Environmental/DE_Protected_Natural_Resources/MapServer/8 (name field NAME)
- **Delaware public protected lands (DNREC)** · server root: https://enterprise.firstmap.delaware.gov/arcgis/rest/services
  - land: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Environmental/DE_Protected_Natural_Resources/MapServer/11 (name field NAME)

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

## Layers on these servers (atlas crawler, 2026-10-30; lists only, decides nothing; rewritten weekly)

- **https://enterprise.firstmap.delaware.gov/arcgis/rest/services**: 40 polygon layer(s) with park / boundary / recreation / wildlife / forest / lands words
  - State Forest: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/FeatureServer/0 (name field LABEL)
  - Pine Plantations: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/FeatureServer/1 (name field ?)
  - Urban Tree Canopy Estimates: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/FeatureServer/2 (name field NAME)
  - Forest Cover 2007: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/FeatureServer/3 (name field ?)
  - State Forest: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/MapServer/0 (name field LABEL)
  - Pine Plantations: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/MapServer/1 (name field ?)
  - Urban Tree Canopy Estimates: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/MapServer/2 (name field NAME)
  - Forest Cover 2007: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Forestry/MapServer/3 (name field ?)
  - DE Wildlife Action Plan Habitats 2025: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Wildlife_Action_Plan/MapServer/0 (name field ?)
  - DE Wildlife Action Plan Regions 2025: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Biota/DE_Wildlife_Action_Plan/MapServer/1 (name field ?)
  - Communities: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/FeatureServer/1 (name field ?)
  - Municipal Annexations: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/FeatureServer/2 (name field NAME)
  - Municipalities: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/FeatureServer/3 (name field NAME)
  - State  and County Boundaries: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/FeatureServer/4 (name field NAME)
  - Communities: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/MapServer/1 (name field ?)
  - Municipal Annexations: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/MapServer/2 (name field NAME)
  - Municipalities: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/MapServer/3 (name field NAME)
  - State  and County Boundaries: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Boundaries/MapServer/4 (name field NAME)
  - Water CPCN: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_CPCN/FeatureServer/0 (name field ?)
  - Wastewater CPCN: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_CPCN/FeatureServer/1 (name field ?)
  - Water CPCN: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_CPCN/MapServer/0 (name field ?)
  - Wastewater CPCN: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_CPCN/MapServer/1 (name field ?)
  - HUBZones: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Hub_Opportunity_Zones/FeatureServer/0 (name field STATE_NAME)
  - Opportunity Zones: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Hub_Opportunity_Zones/FeatureServer/1 (name field ?)
  - HUBZones: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Hub_Opportunity_Zones/MapServer/0 (name field STATE_NAME)
  - Opportunity Zones: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Hub_Opportunity_Zones/MapServer/1 (name field ?)
  - Tile Index Grid: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/FeatureServer/1 (name field TILE_NAME)
  - Zip Codes: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/FeatureServer/2 (name field PO_NAME)
  - USGS Quarter Quad Index: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/FeatureServer/3 (name field NAME)
  - Tidal Wetlands Index: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/FeatureServer/4 (name field ?)
  - USGS LiDAR Tile Index: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/FeatureServer/5 (name field NAME)
  - Tile Index Grid: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/MapServer/1 (name field TILE_NAME)
  - Zip Codes: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/MapServer/2 (name field PO_NAME)
  - USGS Quarter Quad Index: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/MapServer/3 (name field NAME)
  - Tidal Wetlands Index: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/MapServer/4 (name field ?)
  - USGS LiDAR Tile Index: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Index/MapServer/5 (name field NAME)
  - Spray Blocks: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Mosquito_Spray_Blocks/MapServer/0 (name field ?)
  - Police Beats: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_PoliceBeats/MapServer/0 (name field ?)
  - Election Districts: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Political_Boundaries/FeatureServer/0 (name field ?)
  - Senate Districts: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Boundaries/DE_Political_Boundaries/FeatureServer/1 (name field NAME)
