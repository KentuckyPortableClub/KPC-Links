# Round 11 for the good bot (HQ Oct 26): three national layers
Find the official ArcGIS layer (address ending /MapServer/N or /FeatureServer/N) for each, from the agency's own account. For each: address, geometry type (polygon or line), the name field, the count, and whether it is the legal boundary or something else. Test with ?f=json and /query?where=1=1&returnCountOnly=true&f=json. Don't guess addresses. A plain list is fine.
1. BLM Recreation Management Areas, national (BLM's own data; we are missing 391 of them, mostly in UT, ID, WY, NV).
2. National Historic Trails, the trail lines (NPS National Trails Office / NPS Land Resources; 117 missing).
3. National Wild and Scenic Rivers, the river segments (rivers.gov / the federal river agencies; 61 missing).
