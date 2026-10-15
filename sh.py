import urllib.request,json
def get(u):
  return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=40).read().decode('utf8','replace')
A=json.loads(get('https://api2.sota.org.uk/api/associations'))
print(len(A)); print(json.dumps(A[0])[:800])
for a in A:
  c=a.get('associationCode','')
  if c.startswith(('W','K','N','A')) and 'USA' in (a.get('associationName','')+a.get('dxcc','')): print(json.dumps({k:a.get(k) for k in ('associationCode','associationName','associationManager','associationManagerCallsign','dxcc','activeFrom','activeTo')}))
try:
  d=json.loads(get('https://api2.sota.org.uk/api/associations/W4K')); print(json.dumps(d)[:1500])
except Exception as e: print('ERR',e)
