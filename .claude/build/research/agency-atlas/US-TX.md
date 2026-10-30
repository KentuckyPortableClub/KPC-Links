# Agency Atlas: US-TX
Read FIRST before searching for this state's parks. ADD what you learn (one line, dated, your chat): open-data portal URL, each agency's ArcGIS server root + folders, park-page URL pattern, statewide / county parcel map, sites that block bots, dead hosts. Never delete others' lines; mark dead ones 'DEAD <date>'.

## Layers already wired into the key (from data/state-gis.json, Oct 30)
- **Texas Parks & Wildlife Department (state parks)** · server root: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services
  - park: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services/Texas_State_Parks_Boundaries/FeatureServer/0 (name field ParkName)
- **Texas Parks & Wildlife Department (public hunting lands)** · server root: https://tpwd.texas.gov/arcgis/rest/services
  - wild: https://tpwd.texas.gov/arcgis/rest/services/Wildlife/TPWD_PublicHuntLocatorMap/MapServer/9 (name field Name)
- **TPWD Wildlife Division (owner nancy.heger@tpwd.texas.gov_TPWD)** · server root: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services
  - wild: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services/WMA_Boundaries_4PublicDistribution/FeatureServer/0 (name field LoName)
- **Texas Parks and Wildlife (public conservation lands)** · server root: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services
  - land: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services/Public_ConservationLands/FeatureServer/0 (name field P_Loc_Nm)

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

## Parcel / ownership maps (statewide or by county)
- Chat 8 (Oct 30): statewide parcel compile = **2019_Texas_Parcels_StratMap** FeatureServer, same server root as the park layers above: https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services/2019_Texas_Parcels_StratMap/FeatureServer/0 (Texas has no live statewide parcel feed -- StratMap is a one-time TxGIO/TNRIS compile from county appraisal districts, so coverage/currency varies by county; filed a parcel look-up for the 11 THC historic sites against it, `8-parcel-tx-thc`).
