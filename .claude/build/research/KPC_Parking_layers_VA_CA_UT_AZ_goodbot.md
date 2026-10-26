**Virginia (DCR / DWR)**

- **DCR State Parks – Facilities POI (includes Parking)**:  
  `https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/ArcGIS/rest/services/StatePark_FacilitiesPOI/FeatureServer/12`  
  Park/area field: `ParkAbbr` (also `Facility_Name`)  
  Type field: `USeDirect_UseType` (values include “Parking”, “Contact Station”, etc.)  
  Point count: 1,375 total / 362 Parking

- **DWR – Whitewater Boating Access Sites**:  
  `https://services5.arcgis.com/lElo6Muu6AKbgOrY/ArcGIS/rest/services/VA_DWR_River_Accesses_WFL1/FeatureServer/0`  
  Name fields: `SITENAME`, `WATERBODY`  
  Type: none (all are boat accesses)  
  Point count: 67  

Full DWR public boating access (~237 sites) is published on the official DWR ArcGIS Hub (`https://dwr-hub-gis-data-dgif-virginia.hub.arcgis.com/datasets/528b6848a9e14f5191605e3cec7c0ba5`). The exact FeatureServer URL for that layer was not resolved in the remaining time.

**California (State Parks)**

- **Parking Points**:  
  `https://services2.arcgis.com/AhxrK3F6WM8ECvDi/ArcGIS/rest/services/ParkingPoints/FeatureServer/0`  
  Park/area field: `UNITNAME`  
  Type fields: `TYPE`, `SUBTYPE`, `USETYPE`  
  Point count: 2,359

- **Park Entry Points**:  
  `https://services2.arcgis.com/AhxrK3F6WM8ECvDi/ArcGIS/rest/services/ParkEntryPoints/FeatureServer/2`  
  Park/area field: `PARK_NAME`  
  Type field: none (all are entrances)  
  Point count: 288  

These match the official California State Parks open data layers (Parking Areas + Park Entry Points) listed at parks.ca.gov and data.ca.gov.

**Utah (State Parks / DWR)**

- Statewide (UGRC) Boat Ramps (includes State Parks / DWR sites):  
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/BoatRamps/FeatureServer/0`  
  Point count: 117

- Statewide (UGRC) Trailheads:  
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahTrailheads/FeatureServer/0`  
  Point count: 568  

- Utah State Parks point locations (parks themselves, not facilities):  
  `https://services.arcgis.com/ZzrwjTRez6FJiOq4/ArcGIS/rest/services/Utah_State_Parks/FeatureServer/0`

DWR Walk-In Access parking/access points exist on the Utah DWR Hub but the precise FeatureServer URL was not retrieved.

**Arizona (State Parks / Game & Fish)**

- Arizona State Parks Freedom 250 Trailheads (derived from ASPT data):  
  `https://services1.arcgis.com/KbxwQRRfWyEYLgp4/ArcGIS/rest/services/Arizona_State_Parks_and_Trails_Freedom_250/FeatureServer/61`  
  Park/area field: `Park_Name`  
  Point count: 80  

Official live Arizona State Parks & Trails services are hosted at:  
`https://services2.arcgis.com/gdcQ6sUWKP8qwBmV/ArcGIS/rest/services`  
(The directory itself was confirmed; individual parking/trailhead/ramp layers were not fully enumerated before time ran out.)

---

**Advice for the next bot**

1. Start with the known official service roots and open-data portals (do not guess URLs):
   - VA DCR: `services1.arcgis.com/PxUNqSbaWFvFgHnJ`
   - VA DWR Hub: `dwr-hub-gis-data-dgif-virginia.hub.arcgis.com`
   - CA State Parks: `services2.arcgis.com/AhxrK3F6WM8ECvDi` + data.ca.gov California Department of Parks and Recreation datasets
   - UT DWR Hub: `dwr-data-utahdnr.hub.arcgis.com` + UGRC recreation layers
   - AZ State Parks: `services2.arcgis.com/gdcQ6sUWKP8qwBmV` + azstateparks.com GIS references
   - AZ Game & Fish: `azgfd.maps.arcgis.com` and the Fish & Boat AZ Experience

2. For any candidate FeatureServer/MapServer ending in `/N`:
   - Open `...?f=json` (or `/layers`) to confirm geometryType = `esriGeometryPoint` and identify the park/area name field and any type field.
   - Run `.../query?where=1=1&returnCountOnly=true&f=json` for the point count.
   - Filter by type values (Parking, Trailhead, Entrance, Boat Ramp, etc.) when a type field exists.

3. Prefer agency-owned ArcGIS Online organizations, official state open-data portals, and agency hubs. Discard third-party or aggregated layers unless the copyright/description explicitly attributes the data to the state agency.

4. Once the remaining VA DWR full boating access FeatureServer, Utah DWR WIA points, and the live Arizona State Parks parking/trailhead/ramp layers are identified, the same pattern (address + name field + type field + count) can be applied to finish the list.