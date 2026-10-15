O=https://kentuckyportableclub.github.io
c(){ echo "=== $1"; curl -s -m 25 -D /tmp/h -H "Origin: $O" "$1" | head -c ${2:-700}; echo; grep -i "access-control-allow-origin\|^HTTP" /tmp/h; }
c "https://api.pota.app/lookup?search=Vogel&size=5"
c "https://api.pota.app/park/US-2177" 1200
c "https://api.pota.app/locations"
c "https://api2.sota.org.uk/api/summits/W4G/NG-001" 900
c "https://api.sotl.as/summits/search?q=brasstown&limit=3" 900
c "https://api2.sota.org.uk/api/associations/W4G" 300
c "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Protected_Areas_Fee_Manager/FeatureServer/0/query?geometry=-83.96,34.76&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=Unit_Nm,Mang_Name,Loc_Mang,GIS_Acres&returnGeometry=false&f=json" 900
c "https://wwff.co/wwff-data/wwff_directory.csv" 600
c "https://spots.wwff.co/static/agendas.json" 300
