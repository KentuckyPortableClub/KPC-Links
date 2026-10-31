# Agency Atlas: US-VA
Read FIRST before searching for this state's parks. ADD what you learn (one line, dated, your chat): open-data portal URL, each agency's ArcGIS server root + folders, park-page URL pattern, statewide / county parcel map, sites that block bots, dead hosts. Never delete others' lines; mark dead ones 'DEAD <date>'.

## Layers already wired into the key (from data/state-gis.json, Oct 30)
- **Virginia Department of Forestry** · server root: https://services1.arcgis.com/zdPnl7ASQIo6PX54/arcgis/rest/services
  - forest: https://services1.arcgis.com/zdPnl7ASQIo6PX54/arcgis/rest/services/VDOF_State_Forests/FeatureServer/0 (name field Name)
- **Virginia DCR Natural Heritage** · server root: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services
  - preserve: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services/VSP_Natural_Area_Preserves/FeatureServer/1 (name field MANAME)
- **Virginia State Parks (DCR)** · server root: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services
  - park: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services/bclsp_State_Parks/FeatureServer/0 (name field LABEL)
- **Virginia DCR State Parks (tracts)** · server root: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services
  - park: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services/SP_Boundary_-_Tracts/FeatureServer/0 (name field MANAME)
- **Virginia DCR (Virginia's conservation lands)** · server root: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services
  - land: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services/VAConservationLands/FeatureServer/0 (name field LABEL)
- **Virginia DCR (local parks 2023)** · server root: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services
  - park: https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services/Local_Parks_2023/FeatureServer/0 (name field NAME)
- **Virginia Department of Wildlife Resources** · server root: https://services.dwr.virginia.gov/arcgis/rest/services
  - wild: https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_WMA_Boundaries/FeatureServer/0 (name field WMA_NAME)
- **Virginia Dept. of Historic Resources (credit)** · server root: https://vcris.dhr.virginia.gov/arcgis/rest/services
  - land: https://vcris.dhr.virginia.gov/arcgis/rest/services/dhr/dhr_public/MapServer/3 (name field PropertyNames)

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

- (chat 9, Oct 30) Northern Virginia Regional Commission PHNST service (services5 6MUPhDX27Ne3DNOw, PHNST_Northern_Virginia_WFL1): /30 PHNST Trail line (Name), /18 Park-PHNST Corridor polygons (Name), /3 gaps, /28 planning status; publisher = a regional government body (usable for its own items). NPS POHE centerline is the official line (US-DC.md).
