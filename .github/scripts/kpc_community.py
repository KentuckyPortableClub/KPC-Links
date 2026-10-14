"""Copies APPROVED posts from the KPC Community Google Form sheet into kpc-community.json.
Needs the GitHub secret COMMUNITY_SHEET_CSV (the sheet's "Publish to web" CSV link).
Rows with YES in the Approved column are used, plus rows from pre-approved call signs (kpc_preapproved.py) unless marked NO. Photos from approved rows are downloaded from
Google Drive, shrunk to 1280 px and saved without location data in photos/community/."""
import csv,io,json,os,re,hashlib,sys,urllib.request,datetime
import kpc_preapproved as PA
PRE=PA.load()
URL=os.environ.get('COMMUNITY_SHEET_CSV','').strip()
def notice(m): print('::notice title=Community::'+str(m).replace('%','%25').replace('\n','%0A'))
if not URL: notice('COMMUNITY_SHEET_CSV secret not set yet; nothing to do.'); sys.exit(0)
def get(u):
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC community'}),timeout=60) as f: return f.read()
rows=list(csv.reader(io.StringIO(get(URL).decode('utf-8-sig'))))
if not rows: notice('Sheet is empty.'); sys.exit(0)
H=[h.strip() for h in rows[0]];L=[h.lower() for h in H]
def col(name):
  for i,h in enumerate(L):
    if h.startswith(name.lower()): return i
  return None
TYPES={'station setup':'setup','antenna build':'antenna','field tip':'tip','gear review':'review','activation story':'story','elmer':'elmer','operator spotlight':'spotlight'}
# question name -> field key, per type (title field first)
FIELDS={
 'setup':[('Setup name','title'),('Radio','radio'),('Antenna','antenna'),('Power','power'),('Mast or support','mast'),('Weight and packing','weight'),('Approximate cost','cost'),('About this setup','body')],
 'antenna':[('Antenna type','title'),('Bands','bands'),('Dimensions','dims'),('Feed and matching','feed'),('SWR results','swr'),('Build notes','body')],
 'tip':[('Tip title','title'),('Your field tip','body')],
 'review':[('Gear name','title'),('Rating','rating'),('Pros','pros'),('Cons','cons'),('Would you buy it again','again')],
 'story':[('Story title','title'),('Parks or summits','refs'),('Activation date','adate'),('Your story','body')],
 'elmer':[('Your area','area'),('I can help with','help'),('How to reach you','reach')],
 'spotlight':[('Name you go by','name'),('Home county','county'),('Licensed since','since'),('Favorite park or summit','fav'),('About you','body')],
}
C={'ts':col('Timestamp'),'call':col('Call sign'),'kind':col('What are you sharing'),'photo':col('Photos'),'app':col('Approved')}
if C['app'] is None: notice('No "Approved" column in the sheet yet: only pre-approved call signs are posted.')
def cell(r,i): return r[i].strip() if i is not None and i<len(r) else ''
try:
  from PIL import Image
except Exception: Image=None
items=[];newph=0;os.makedirs('photos/community',exist_ok=True)
for r in rows[1:]:
  if not PA.ok(cell(r,C['app']) if C['app'] is not None else '',cell(r,C['call']) if C['call'] is not None else '',PRE): continue
  kind=cell(r,C['kind']).lower();t=next((v for k,v in TYPES.items() if kind.startswith(k)),None)
  if not t: continue
  call=re.sub(r'[^A-Z0-9/]','',cell(r,C['call']).upper())
  ts=cell(r,C['ts']);iid=hashlib.sha1((ts+call+t).encode()).hexdigest()[:12]
  f={}
  for q,k in FIELDS[t]:
    v=cell(r,col(q));
    if v: f[k]=v[:4000]
  photos=[]
  for j,pid in enumerate(re.findall(r'id=([A-Za-z0-9_-]{20,})',cell(r,C['photo']))[:5]):
    fn=f'photos/community/{iid}-{j+1}.jpg'
    if not os.path.exists(fn) and Image:
      try:
        im=Image.open(io.BytesIO(get('https://drive.google.com/uc?export=download&id='+pid))).convert('RGB');im.thumbnail((1280,1280))
        im.save(fn,'JPEG',quality=80,optimize=True);newph+=1   # saved fresh: camera GPS/EXIF dropped
      except Exception as e: notice(f'Photo from {call} could not be copied (is the Drive folder shared "anyone with the link"?): {e}'); continue
    if os.path.exists(fn): photos.append(fn)
  m=re.match(r'(\d+)/(\d+)/(\d{4})',ts);iso=f'{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}' if m else ''
  items.append({'id':iid,'type':t,'call':call,'date':iso,'f':f,'photos':photos})
items.sort(key=lambda x:(x['date'],x['id']),reverse=True)
try: old=json.load(open('kpc-community.json'))
except Exception: old=None
if not old or old.get('items')!=items:
  json.dump({'updated':datetime.date.today().isoformat(),'items':items},open('kpc-community.json','w'),indent=1,ensure_ascii=False)
notice(f'{len(items)} approved post(s), {newph} new photo(s).')
