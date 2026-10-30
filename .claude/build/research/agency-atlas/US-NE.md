# Agency Atlas: US-NE
Read FIRST before searching for this state's parks. ADD what you learn (one line, dated, your chat): open-data portal URL, each agency's ArcGIS server root + folders, park-page URL pattern, statewide / county parcel map, sites that block bots, dead hosts. Never delete others' lines; mark dead ones 'DEAD <date>'.

## Layers already wired into the key (from data/state-gis.json, Oct 30)
- **Nebraska Game and Parks Commission** · server root: https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services
  - wild: https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services/Conservation_Partner_Lands/FeatureServer/0 (name field AreaName)
  - park: https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services/Park_Areas/FeatureServer/0 (name field AreaName)
- **NGPC (owner NGPC.GISAdmin)** · server root: https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services
  - land: https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services/NPGCProperties2023_2024/FeatureServer/268 (name field AreaName)
- **National Park Service (legal boundary)** · server root: https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services
  - park: https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2 (name field UNIT_NAME)

## Open-data portal
- (add)

## Agency servers / folders worth walking
- (add)

## Park pages (URL pattern) + where the map link sits
- (add)

## Parcel / ownership maps (statewide or by county)
- **Statewide parcels (GISCAT)** · https://giscat.ne.gov/enterprise/rest/services/StatewideParcelsExternal/MapServer/0 -- no owner-name field; has Ownership_Type, Property_Parcel_Type, Classification_Code, Parcel_URL (likely links to the county assessor's own page with the owner name). My own point query through WebFetch returned the empty form page, not a result; hand parcel look-ups on this layer to the look-up bot. (chat 8, Oct 30)

## Blocks bots / dead / private (don't retry)
- (add)
