# OFFICIAL TRAIL LINES: Pine Mountain State Scenic Trail and Sheltowee Trace (Research desk, chat 8, Oct 27)

Research only. I cannot query a layer's geometry from here, so everything below is "this layer exists and says this"; chat 2's bot must test it.

## 1. Pine Mountain State Scenic Trail: an official line EXISTS (grade B)
**Kentucky's own trails map service:** https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Recreational_Trails_WGS84WM/MapServer (Kentucky Division of Geographic Information host, title "kytrails_1z").
- Service description: "This map service provides access to local, state, and federally designated recreational trails in the Commonwealth of Kentucky." Credits: "Kentucky State Parks, Kentucky Division of Geographic Information (DGI), US Forest Service, US Parks Service." No date given.
- **Layer 1, "Pine Mountain Trail (Open)"**, polyline, supports query (JSON / geoJSON), up to 1000 records: https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Recreational_Trails_WGS84WM/MapServer/1
- **Layer 0, "Pine Mountain Little Shepherd Trail"**, polyline (not part of the designated scenic trail; the state's page calls it the extension "for another 38 miles from US 119 to US 421").
- Layer 1's extent converts to about lon -82.81 to -82.32, lat 37.06 to 37.31: that is the Breaks to US 119 stretch. It matches the state's description of the **designated, open part: 44 miles (Birch Knob 28 + Highlands 16), Breaks Interstate Park to US 119**; the planned 120 miles to Cumberland Gap is not drawn. The layer itself has no description, date or copyright text (the credit is at the service level), so grade B, not A.
- Official state pages: Nature Preserves page (owner "Kentucky State Parks"; says see Kentucky State Parks' page for current details): https://eec.ky.gov/Nature-Preserves/Locations/Pages/Pine Mountain State Scenic Trail.aspx. Kentucky State Parks' own page (https://parks.ky.gov/whitesburg/parks/recreation/pine-mountain-state-scenic-trail) could not be opened from here, so I did not see its "Maps" section.
- A free Avenza "KyGeoNet" PDF map (2023, "State Park Trails Edition") also exists: https://store.avenza.com/products/pine-mountain-state-scenic-trail-kygeonet-map. It is a map, not a line to test against, and Avenza is a third-party store, so use it only as a cross-check.
- The sister layer "State Park Trails" (layer 6, field TRAIL_NAME) is where other state-park trails live.

**What it means for the 5 NOT SURE pairs:** the trail's own line is now available for the designated 44-mile open section. Rule: test the other park's public land within 100 ft (30.5 m) of THIS line. Limits to tell Brandon: (a) the line covers only the open section, so any pair on the planned remainder stays NOT SURE; (b) layer 1 has no attributes at all, so the bot must confirm by comparing length (about 44 miles) and by checking that Breaks Interstate Park lies at one end; (c) the Kentucky Heritage Land Conservation Fund deed restrictions mean the trail sits on state-owned or easement land, which is a second reason to run the ownership step.
**Suggested record for the data:** "Pine Mountain State Scenic Trail line = Ky_Recreational_Trails layer 1, read <date>, service credit Kentucky State Parks / DGI".

## 2. Sheltowee Trace: the Forest Service's own line EXISTS (grade A for the layer, B for the trail's rows)
**Forest Service national trails layer:** https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_TrailNFSPublishWithDataStatus_01/MapServer, layer 0 "National Forest System Trails": https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_TrailNFSPublishWithDataStatus_01/MapServer/0
- Description: "The TrailNFS_Publish Layer is designed to provide information about National Forest System trail locations." Copyright: "USDA Forest Service." Polyline. Fields include **TRAIL_NAME**, TRAIL_TYPE, TRAIL_CLASS and **NATIONAL_TRAIL_DESIGNATION**. The service "depicts National Forest Service trails that have been approved for publication" and is "kept current by daily updates from forest SDE geodatabases."
- Layers 3/8 mark where "Trail Centerline data available" per forest or district: check that the Daniel Boone districts are on the "centerline data available" list before trusting the line (a district shown as "data unavailable" has no line).
- Use TRAIL_NAME = Sheltowee Trace (and its National Recreation Trail designation) to select the line. I did not open a Sheltowee record, so the exact TRAIL_NAME spelling and whether the trail is split into many segments is NOT checked.
- The trail also leaves Forest Service land (state, private and Corps stretches). Those parts are not in this layer, which is another reason for the ownership step.
- Other pages: the Daniel Boone National Forest site and the Sheltowee Trace Association (https://sheltoweetrace.org/trail, a club site, not official); the National Recreation Trail listing https://nrtapplication.org/trails/sheltowee-trace (third party). Use the Forest Service layer.

## 3. What chat 2 should do
1. Pine Mountain: query layer 1, save the line's length and a read date, run the 100-ft test for the 5 pairs; any pair on a stretch not covered stays NOT SURE.
2. Sheltowee: query layer 0 for the Sheltowee records, check the district "centerline" status, use the line instead of the current one if it is more precise, and write "line source + date" in every row (already a rule).
3. The bot must keep the national-trail lines (Trail of Tears, Lewis and Clark) as "approximate" (NPS 1:100,000).

## 4. Not checked
Layer geometry and attributes (I cannot query), the parks.ky.gov Pine Mountain "Maps" section, and Kentucky State Parks' official GPX (none found).

Sources: https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Recreational_Trails_WGS84WM/MapServer/layers ; https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Recreational_Trails_WGS84WM/MapServer/info/iteminfo?f=pjson ; https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_TrailNFSPublishWithDataStatus_01/MapServer ; https://eec.ky.gov/Nature-Preserves/Locations/Pages/Pine Mountain State Scenic Trail.aspx
