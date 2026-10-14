"""Copies APPROVED park tips from the KPC Park Tips Google Form sheet into kpc-park-notes.json.
Needs the GitHub secret NOTES_SHEET_CSV (the sheet's "Publish to web" CSV link).
Only rows with YES in the Approved column are used. Photos from approved rows are downloaded from
Google Drive, shrunk to 1280 px and saved without location data in photos/notes/."""
import csv,io,json,os,re,hashlib,sys,urllib.request
URL=os.environ.get('NOTES_SHEET_CSV','').strip()
def notice(m): print('::notice title=Park notes::'+str(m).replace('%','%25').replace('\n','%0A'))
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
if C['app'] is None: notice('No "Approved" column in the sheet yet.'); sys.exit(0)
D=json.load(open('kpc-ky-data.json'))
REFS={p['c'] for p in D['parks']}|{s['c'] for s in D['summits']}|{k['c'] for k in D['kff']}
def norm(r):
  r=re.sub(r'\s+','',str(r).upper())
  m=re.fullmatch(r'(US|K|KFF)-?0*(\d+)',r)
  if m: return ('KFF' if m.group(1)=='KFF' else 'US')+'-'+m.group(2).zfill(4)
  m=re.fullmatch(r'W4K/?([A-Z]{2})-?0*(\d+)',r)
  if m: return f'W4K/{m.group(1)}-{m.group(2).zfill(3)}'
  return r
def cell(r,k): i=C[k]; return r[i].strip() if i is not None and i<len(r) else ''
notes=[];skipped=[];os.makedirs('photos/notes',exist_ok=True);newph=0
try:
  from PIL import Image
except Exception: Image=None
for r in rows[1:]:
  if cell(r,'app').upper() not in ('YES','Y','APPROVED','X'): continue
  ref=norm(cell(r,'ref'))
  if ref not in REFS: skipped.append(cell(r,'ref')); continue
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
  notes.append({'id':nid,'ref':ref,'call':call,'type':cell(r,'type'),'gps':cell(r,'gps')[:120],'text':cell(r,'text')[:2000],'date':date,'photos':photos})
notes.sort(key=lambda n:(n['ref'],n['id']))
old=None
try: old=json.load(open('kpc-park-notes.json'))
except Exception: pass
if not old or old.get('notes')!=notes:
  json.dump({'updated':__import__('datetime').date.today().isoformat(),'notes':notes},open('kpc-park-notes.json','w'),indent=1,ensure_ascii=False)
notice(f'{len(notes)} approved tip(s), {newph} new photo(s).'+(f' Skipped unknown park numbers: {", ".join(skipped[:10])}' if skipped else ''))
