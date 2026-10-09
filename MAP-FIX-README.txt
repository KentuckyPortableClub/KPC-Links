KPC Find a Park map tile fix

Replace finder.js on GitHub with the updated file. No other files need changing for this map fix.

Map now uses the main OpenStreetMap tile host and automatically tries CARTO and Esri if the tile host fails. If all providers fail, the page shows a clear notice.

The app still needs internet access for map tiles. Check any browser ad/tracker blockers if tiles remain blank.
