# Agency Atlas: US-WA
Read FIRST before searching for this state's parks. ADD what you learn (one line, dated, your chat): open-data portal URL, each agency's ArcGIS server root + folders, park-page URL pattern, statewide / county parcel map, sites that block bots, dead hosts. Never delete others' lines; mark dead ones 'DEAD <date>'.

## Layers already wired into the key (from data/state-gis.json, Oct 30)
- **Washington State Parks** · server root: https://services5.arcgis.com/4LKAHwqnBooVDUlX/arcgis/rest/services
  - park: https://services5.arcgis.com/4LKAHwqnBooVDUlX/arcgis/rest/services/ParkBoundaries/FeatureServer/2 (name field ParkName)
- **Washington Department of Fish and Wildlife** · server root: https://geodataservices.wdfw.wa.gov/arcgis/rest/services
  - wild: https://geodataservices.wdfw.wa.gov/arcgis/rest/services/WP_RealEstate/ManagedPlaces/MapServer/0 (name field ManagedPlaceName)
- **Washington State Department of Natural Resources** · server root: https://gis.dnr.wa.gov/site3/rest/services
  - preserve: https://gis.dnr.wa.gov/site3/rest/services/Public_Boundaries/WADNR_PUBLIC_Cadastre_OpenData/MapServer/6 (name field PARCEL_LABEL_NM)
- **Washington State Department of Natural Resources (Non-DNR Major Public Lands parcels; MANAGER field gives WDFW / State Parks)** · server root: https://gis.dnr.wa.gov/site3/rest/services
  - land: https://gis.dnr.wa.gov/site3/rest/services/Public_Boundaries/WADNR_PUBLIC_Major_Public_Lands_NonDNR/MapServer/1 (name field NAME)
- **Washington State Department of Ecology (NHD Waterbodies, owner WAECY_Geoservices)** · server root: https://services.arcgis.com/6lCKYNJLvwTXqrmp/arcgis/rest/services
  - land: https://services.arcgis.com/6lCKYNJLvwTXqrmp/arcgis/rest/services/NHD/FeatureServer/6 (name field GNIS_Name)
- **Washington Dept. of Fish and Wildlife (credit: WDFW)** · server root: https://geodataservices.wdfw.wa.gov/arcgis/rest/services
  - wild: https://geodataservices.wdfw.wa.gov/arcgis/rest/services/WP_RealEstate/WildlifeAreas/FeatureServer/0 (name field WildlifeAreaUnitName)
  - wild: https://geodataservices.wdfw.wa.gov/arcgis/rest/services/WP_RealEstate/WildlifeAreas/FeatureServer/1 (name field WildlifeAreaName)
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
