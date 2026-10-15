O=https://kentuckyportableclub.github.io
B=https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0
curl -s -m 60 -H "Origin: $O" "$B/query?geometry=-83.7567,33.9607,-83.7167,34.0007&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=Unit_Nm,Mang_Name,Des_Tp,GIS_Acres&returnGeometry=false&f=json" | python3 -c "import json,sys;d=json.load(sys.stdin);print([f['attributes'] for f in d.get('features',[])] or d)" | head -c 800; echo
curl -s -m 60 -H "Origin: $O" "$B/query?where=Unit_Nm%20LIKE%20%27%25Yargo%25%27&outFields=Unit_Nm&returnGeometry=true&outSR=4326&geometryPrecision=5&maxAllowableOffset=0.0002&f=geojson" | head -c 300; echo
curl -s -m 60 -H "Origin: $O" "$B/query?where=Unit_Nm%20LIKE%20%27%25Yargo%25%27&outFields=Unit_Nm&returnGeometry=true&outSR=4326&geometryPrecision=5&maxAllowableOffset=0.0002&f=json" | head -c 300; echo
