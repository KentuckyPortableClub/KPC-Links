"""Copies APPROVED park tips from the KPC Park Tips Google Form sheet into kpc-park-notes.json.
Needs the GitHub secret NOTES_SHEET_CSV (the sheet's "Publish to web" CSV link).
Rows with YES in the Approved column are used, plus rows from pre-approved call signs (kpc_preapproved.py) unless marked NO. Photos from approved rows are downloaded from
Google Drive, shrunk to 1280 px and saved without location data in photos/notes/."""
import csv,io,json,os,re,hashlib,sys,urllib.request
import kpc_preapproved as PA
import kpc_formtools as T
PRE=PA.load()
URL=os.environ.get('NOTES_SHEET_CSV','').strip()
def notice(m): print('::notice title=Park notes::'+str(m).replace('%','%25').replace('\n','%0A'))
FORM_URL='https://docs.google.com/forms/d/e/1FAIpQLSc6jTku8aIPejOVridQ19ChA5ACYsFK56n7Nk9WpIgAiLGTMw/viewform'
def find_form_entry():
  """Reads the public form and finds the hidden entry number of the 'Park number' question, so the site's
  Submit a tip buttons can pre-fill the park. Saved to kpc-park-notes-form.json."""
  try:
    html=urllib.request.urlopen(urllib.request.Request(FORM_URL,headers={'User-Agent':'Mozilla/5.0 KPC park notes'}),timeout=60).read().decode('utf-8','replace')
    m=re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);\s*</script>',html,re.S)
    data=json.loads(m.group(1));items=data[1][1];entry=None;names=[]
    for it in items:
      t=str(it[1] or '').strip();names.append(t)
      if t.lower().startswith('park number') and it[4]: entry='entry.'+str(it[4][0][0])
    if not entry: notice('Could not find the Park number question on the form. Questions seen: '+', '.join(names)); return
    new={'url':FORM_URL,'parkEntry':entry}
    try: old=json.load(open('kpc-park-notes-form.json'))
    except Exception: old=None
    if old!=new: json.dump(new,open('kpc-park-notes-form.json','w'),indent=1)
    notice('Form found; Park number is '+entry+'.')
  except Exception as e: notice('Could not read the Google Form: '+str(e))
# The form needs a Google sign-in, so it can't be read from here; the entry number is kept in kpc-park-notes-form.json.
if not URL: notice('NOTES_SHEET_CSV secret not set yet; nothing to do.'); sys.exit(0)
def get(u):
  r=urllib.request.Request(u,headers={'User-Agent':'KPC park notes'})
  with urllib.request.urlopen(r,timeout=60) as f: return f.read()
text=get(URL).decode('utf-8-sig')
rows=list(csv.reader(io.StringIO(text)))
if not rows: notice('Sheet is empty.'); sys.exit(0)
H=[h.strip().lower() for h in rows[0]]
def col(*names):
  for n in names:
    for i,h in enumerate(H):
      if h.startswith(n): return i
  return None
C={'ts':col('timestamp'),'call':col('call sign'),'ref':col('park number'),'type':col('type of tip'),'gps':col('gps'),'text':col('your tip'),'photo':col('photo'),'ok':col('ok to post'),'app':col('approved')}
if C['app'] is None: notice('No "Approved" column in the sheet yet: only pre-approved call signs are posted.')
D=json.load(open('kpc-ky-data.json'))
REFS={p['c'] for p in D['parks']}|{s['c'] for s in D['summits']}|{k['c'] for k in D['kff']}
def norm(r):
  r=re.sub(r'\s+','',str(r).upper())
  if re.fullmatch(r'\d{1,5}',r): r='US-'+r                    # "1277" = US-1277
  m=re.fullmatch(r'(US|K|KFF)-?0*(\d+)',r)
  if m: return ('KFF' if m.group(1)=='KFF' else 'US')+'-'+m.group(2).zfill(4)
  m=re.fullmatch(r'(W\d[A-Z]?|K[HL]\d)/?([A-Z]{2})-?0*(\d+)',r)     # any US SOTA summit: W4K/EC-001, W4T/SU-001, KH6/HA-001
  if m: return f'{m.group(1)}/{m.group(2)}-{m.group(3).zfill(3)}'
  return r
# Other US states (Brandon Oct 16): real POTA US-, WWFF KFF- and US SOTA numbers go to kpc-park-notes-us.json
PIX={}
try:
  for x in json.load(open('data/parkinfo/index.json')): PIX[x[0]]=(x[1],x[2],x[3],x[4])
except Exception: pass
WWFF={}
try:
  for x in json.load(open('data/wwff/KFF.json')): WWFF[x[0]]=(x[1],re.sub(r'^K-','',str(x[5])) if len(x)>5 else '',x[2],x[3])
except Exception: pass
GEO=T.CACHE.setdefault('geo',{})
def far(ref):
  """(name, state, lat, lon) for a real US reference outside Kentucky, or None"""
  if ref in PIX: return PIX[ref]
  if ref in WWFF: return WWFF[ref]
  if ref in GEO: return tuple(GEO[ref]) if GEO[ref] else None
  out=None
  if re.fullmatch(r'US-\d{4,5}',ref):
    j,ok=T.getj('https://api.pota.app/park/'+ref)
    if not ok: return None
    if j and j.get('name'): out=(j['name'],str(j.get('locationDesc') or '').replace('US-','').split(',')[0],j.get('latitude'),j.get('longitude'))
  elif '/' in ref:
    j,ok=T.getj('https://api2.sota.org.uk/api/summits/'+ref)
    if not ok: return None
    if j and (j.get('name') or j.get('summitName')): out=(j.get('name') or j.get('summitName'),'',j.get('latitude'),j.get('longitude'))
  GEO[ref]=list(out) if out else []
  return out
def cell(r,k): i=C[k]; return r[i].strip() if i is not None and i<len(r) else ''
notes=[];usnotes=[];skipped=[];os.makedirs('photos/notes',exist_ok=True);newph=0
try:
  from PIL import Image
except Exception: Image=None
for r in rows[1:]:
  if not PA.auto(cell(r,'app'),cell(r,'call'),PRE,[cell(r,k) for k in C if k not in {'ts','call','photo','app','gps','ok','show','seen','edate','etime','rating'}],cell(r,'photo')): continue
  ref=norm(cell(r,'ref'))
  info=None
  if ref not in REFS:
    info=far(ref) if re.fullmatch(r'(US|KFF)-\d{4,5}|(W\d[A-Z]?|K[HL]\d)/[A-Z]{2}-\d{3}',ref) else None
    if not info: skipped.append(cell(r,'ref')); continue
  call=re.sub(r'[^A-Z0-9/]','',cell(r,'call').upper())
  nid=hashlib.sha1((cell(r,'ts')+call+ref).encode()).hexdigest()[:12]
  photos=[]
  for j,pid in enumerate(re.findall(r'id=([A-Za-z0-9_-]{20,})',cell(r,'photo'))):
    fn=f'photos/notes/{nid}-{j+1}.jpg'
    if not os.path.exists(fn) and Image:
      try:
        im=Image.open(io.BytesIO(get('https://drive.google.com/uc?export=download&id='+pid)))
        im=im.convert('RGB');im.thumbnail((1280,1280))
        im.save(fn,'JPEG',quality=80,optimize=True)  # saved fresh, so camera GPS/EXIF data is dropped
        newph+=1
      except Exception as e: notice(f'Photo for {ref} from {call} could not be copied (is the Drive folder shared "anyone with the link"?): {e}'); continue
    if os.path.exists(fn): photos.append(fn)
  ts=cell(r,'ts');m=re.match(r'(\d+)/(\d+)/(\d{4})',ts)
  date=f'{["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(m.group(1))-1]} {m.group(3)}' if m else ''
  n={'id':nid,'ref':ref,'call':call,'type':cell(r,'type'),'gps':cell(r,'gps')[:120],'text':cell(r,'text')[:2000],'date':date,'photos':photos}
  if info:
    n.update({'name':info[0],'st':info[1] or '','la':info[2],'lo':info[3],'ts':ts}); usnotes.append(n)
  else: notes.append(n)
notes.sort(key=lambda n:(n['ref'],n['id']))
old=None
try: old=json.load(open('kpc-park-notes.json'))
except Exception: pass
if not old or old.get('notes')!=notes:
  json.dump({'updated':__import__('datetime').date.today().isoformat(),'notes':notes},open('kpc-park-notes.json','w'),indent=1,ensure_ascii=False)
# newest first for the other-states page (sheet time like 10/16/2026 14:05:00)
def tkey(n):
  m=re.match(r'(\d+)/(\d+)/(\d{4})\s*(\d+)?:?(\d+)?',n.get('ts',''))
  return (int(m.group(3)),int(m.group(1)),int(m.group(2)),int(m.group(4) or 0),int(m.group(5) or 0)) if m else (0,)
usnotes.sort(key=tkey,reverse=True)
for n in usnotes: n.pop('ts',None)
try: oldus=json.load(open('kpc-park-notes-us.json'))
except Exception: oldus=None
if not oldus or oldus.get('notes')!=usnotes:
  json.dump({'updated':__import__('datetime').date.today().isoformat(),'notes':usnotes},open('kpc-park-notes-us.json','w'),indent=1,ensure_ascii=False)
T.save_cache()
notice(f'{len(usnotes)} approved tip(s) from other states.')
notice(f'{len(notes)} approved tip(s), {newph} new photo(s).'+(f' Skipped unknown park numbers: {", ".join(skipped[:10])}' if skipped else ''))
