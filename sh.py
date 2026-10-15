import urllib.request,urllib.parse,json
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
for k in ['BLACKFORD','BOONE FOREST','CUMBERLAND FOREST','ELK FOREST','FORTNER','LEGACY','POCAHONTAS','RH GROUP','ROBINSON FOREST','ASHER','BETTERMENT','CONTINENTAL','ELK HORN','WELLS','BOONE COUNTY CLIFFS','DINSMORE','BICKFORD','STEPHENSON','LOGAN COUNTY GLADE','HOWARDS CREEK','MARTINS FORK','MARTIN','BESHEAR','MURPHY','KNOBS']:
  w=f"UPPER(Unit_Nm) LIKE '%{k}%' AND State_Nm='KY'"
  q={'where':w,'outFields':'Unit_Nm,Loc_Own,Own_Type,Loc_Mang,Mang_Type,Pub_Access,GIS_Acres,Category','returnGeometry':'false','f':'json'}
  try:
    j=json.loads(urllib.request.urlopen(urllib.request.Request(P+'?'+urllib.parse.urlencode(q),headers={'User-Agent':'KPC'}),timeout=40).read())
    seen=set()
    for f in j.get('features',[]):
      a=f['attributes'];key=(a['Unit_Nm'],a['Loc_Own'],a['Category'])
      if key in seen: continue
      seen.add(key);print(k,'|',a['Unit_Nm'],'|',a['Loc_Own'],a['Own_Type'],'|',a['Loc_Mang'],a['Mang_Type'],'|',a['Pub_Access'],a['Category'],a['GIS_Acres'])
    if not j.get('features'): print(k,'| none')
  except Exception as e: print(k,'ERR',e)
