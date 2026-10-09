KPC Activation Finder — GitHub Pages deployment

Upload ALL eight files in this folder to the SAME directory of your GitHub Pages repository. Replace the existing parks.html only after keeping a backup.

Files: parks.html, finder.html, finder.css, finder.js, locations.json, wwff-unmapped.json, KPC-logo.png, README.txt.

Open https://YOUR-SITE/finder.html to test. HTTPS is required for GPS on normal hosted pages. The map uses Leaflet/OpenStreetMap tiles and town lookup uses Nominatim; internet access is required for both.

WWFF data: January 10, 2025 reference/cross-reference snapshot. WWFF mapped coordinates come from matched POTA points, not verified WWFF boundaries. Other WWFF references are searchable by reference only. Potential POTA+WWFF cross-references do not prove activation eligibility. No automatic verified SOTA/POTA/WWFF double or triple activation detection is claimed.

Check: GPS permission, town lookup, each program checkbox, exact reference lookup, maps, favorites, trip, exports, share link, mobile navigation. The JavaScript syntax and data archive were checked offline, but browser/device and live service tests still require a hosted website.

Source counts: {'POTA': 12710, 'SOTA': 30794, 'WWFF': 6342}; unmapped WWFF: 475; WWFF with POTA references: 6342

TRAILS FEATURE (October 2026):
Three trail resource cards added to finder.html: Sheltowee Trace, Trail of Tears, Lewis & Clark. Official map/data-source links and example nearby-town searches are included. No trail geometry or campsite/trailhead data is bundled: route GIS downloads could not be retrieved in this build environment. Do NOT describe this as an along-route spatial search or a trail navigation map.

Trail coverage notice: The Trails section clearly states that the included trail information is limited and not a comprehensive US trail database.

OFFICIAL TRAIL MAP LINKS: Scanned all 12710 POTA entries; 356 names matched trail-related keywords. 69 have agency resources or national trail directory links; other trail-named parks are listed in pota-trail-parks-map-audit.csv for manual verification. This is NOT a nationwide verified map catalog. Keep official-trail-maps.json alongside finder.js.

OCTOBER 2026 ADDITION — OFFICIAL MAPS / ACCESS
- Added Pine Mountain State Scenic Trail and Dawkins Line Rail Trail to the trail planning cards.
- Added official-park-access.json with selected official park/trailhead/camping links.
- Dawkins trailhead parking coordinates come from Kentucky State Parks; check live alerts.
- Map directory entries are not equivalent to verified park-specific maps.
- 2025 WWFF-to-POTA references are historical cross-references, NOT validated 2-fers.
- No geospatial polygon overlap or live boundary validation is performed.
- This is a limited pilot, not complete nationwide coverage.

OFFICIAL EVIDENCE REVIEW (2026-10-08): official-2fer-evidence.json and official-2fer-review.csv contain five reviewed government-source trail/park connections. These are NOT confirmed multi-program activation overlaps. Every 2-fer display is labeled POSSIBLE. The reference point for Lewis & Clark in this dataset is outside Kentucky.
