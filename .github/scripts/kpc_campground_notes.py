"""Copies campground / cabin reviews from the KPC Campground Reviews Google Form sheet into kpc-campground-notes.json
for kpc-campgrounds.html. Needs the GitHub secret CAMPGROUND_SHEET_CSV (the sheet's "Publish to web" CSV link).
Rows with YES in the Approved column are used, plus rows from pre-approved call signs (kpc_preapproved.py) unless
marked NO. Photos are downloaded from Google Drive, shrunk to 1280 px and saved without location data in
photos/campgrounds/.

Form questions (each must START with these words; order doesn't matter; see .claude/CLAUDE.md):
  Call sign | What are you reviewing | Campground or cabin | Campground name | Town or county | GPS | Website |
  Type of campground | Rating | Site number | When did you stay | Restrooms | Showers | Hookups | Cell signal |
  RF noise | Room for antennas | Shade | Other amenities | Your review | Photos
"Campground or cabin" is pre-filled by the site's REVIEW IT buttons as "US-1277 · Ridgeline & Clifty Campgrounds".
Anything that doesn't match a place in kpc-campgrounds.json is shown in the "Stayed somewhere else?" section."""
import csv, io, json, os, re, hashlib, sys, urllib.request, datetime
import kpc_preapproved as PA
PRE = PA.load()
URL = os.environ.get('CAMPGROUND_SHEET_CSV', '').strip()
def notice(m): print('::notice title=Campground reviews::' + str(m).replace('%', '%25').replace('\n', '%0A'))
if not URL: notice('CAMPGROUND_SHEET_CSV secret not set yet; nothing to do.'); sys.exit(0)
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'KPC campground reviews'}), timeout=60) as f: return f.read()
rows = list(csv.reader(io.StringIO(get(URL).decode('utf-8-sig'))))
if not rows: notice('Sheet is empty.'); sys.exit(0)
H = [h.strip().lower() for h in rows[0]]
def col(*names):
    for n in names:
        for i, h in enumerate(H):
            if h.startswith(n): return i
    return None
C = {'ts': col('timestamp'), 'call': col('call sign'), 'kind': col('what are you reviewing'), 'place': col('campground or cabin', 'place'),
     'oname': col('campground name'), 'where': col('town or county', 'town', 'where'), 'gps': col('gps'), 'web': col('website'), 'otype': col('type of campground'),
     'rating': col('rating', 'overall rating'), 'text': col('your review', 'review'), 'site': col('site number', 'site'), 'when': col('when'),
     'rest': col('restrooms'), 'show': col('showers'), 'hook': col('hookups'), 'cell': col('cell signal', 'cell'), 'noise': col('rf noise', 'noise'),
     'ant': col('room for antennas', 'antenna'), 'shade': col('shade'), 'amen': col('other amenities', 'amenities'), 'photo': col('photo'), 'app': col('approved')}
FACTS = [('rest', 'Restrooms'), ('show', 'Showers'), ('hook', 'Hookups'), ('cell', 'Cell signal'), ('noise', 'RF noise'), ('ant', 'Room for antennas'), ('shade', 'Shade'), ('amen', 'Amenities')]
def cell(r, k): i = C[k]; return r[i].strip() if i is not None and i < len(r) else ''
if C['app'] is None: notice('No "Approved" column in the sheet yet: only pre-approved call signs are posted.')

CG = json.load(open('kpc-campgrounds.json', encoding='utf-8'))
PLACES = []   # (pota, id, name)
for p in CG['parks']:
    for x in p.get('campgrounds', []) + p.get('lodging', []): PLACES.append((p['pota'], x['id'], x['name']))
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
def find_place(txt):
    m = re.search(r'US-?0*(\d+)', txt.upper()); ref = 'US-' + m.group(1).zfill(4) if m else None
    name = norm(re.sub(r'US-?\d+\s*[·\-:|]*', '', txt, flags=re.I))
    cand = [p for p in PLACES if (ref is None or p[0] == ref)]
    for p in cand:
        if norm(p[2]) == name: return p[1]
    if ref:   # a park number and a close name, or the park's only place
        for p in cand:
            if name and (name in norm(p[2]) or norm(p[2]) in name): return p[1]
        if len(cand) == 1: return cand[0][1]
    return None

notes = []; newph = 0; os.makedirs('photos/campgrounds', exist_ok=True)
try:
    from PIL import Image
except Exception: Image = None
for r in rows[1:]:
    if not PA.ok(cell(r, 'app'), cell(r, 'call'), PRE): continue
    call = re.sub(r'[^A-Z0-9/]', '', cell(r, 'call').upper())
    outside = 'not in' in cell(r, 'kind').lower() or 'outside' in cell(r, 'kind').lower() or (not cell(r, 'place') and cell(r, 'oname'))
    ptxt = cell(r, 'oname') if outside else cell(r, 'place'); text = cell(r, 'text')
    if not (ptxt and (text or cell(r, 'rating'))): continue
    nid = hashlib.sha1((cell(r, 'ts') + call + ptxt).encode()).hexdigest()[:12]
    m = re.search(r'[1-5]', cell(r, 'rating')); rating = int(m.group(0)) if m else None
    place = None if outside else find_place(ptxt)
    photos = []
    for j, pid in enumerate(re.findall(r'id=([A-Za-z0-9_-]{20,})', cell(r, 'photo'))):
        fn = f'photos/campgrounds/{nid}-{j + 1}.jpg'
        if not os.path.exists(fn) and Image:
            try:
                im = Image.open(io.BytesIO(get('https://drive.google.com/uc?export=download&id=' + pid))).convert('RGB')
                im.thumbnail((1280, 1280)); im.save(fn, 'JPEG', quality=80, optimize=True)   # saved fresh: no GPS/EXIF
                newph += 1
            except Exception as e: notice(f'Photo from {call} could not be copied (is the Drive folder shared "anyone with the link"?): {e}'); continue
        if os.path.exists(fn): photos.append(fn)
    ts = cell(r, 'ts'); m = re.match(r'(\d+)/(\d+)/(\d{4})', ts)
    date = f'{["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(m.group(1)) - 1]} {m.group(3)}' if m else ''
    n = {'id': nid, 'place': place, 'call': call, 'rating': rating, 'text': text[:3000], 'site': cell(r, 'site')[:20], 'stayed': cell(r, 'when')[:40], 'date': date, 'photos': photos,
         'facts': [[lab, cell(r, k)[:160]] for k, lab in FACTS if cell(r, k)]}
    if not place:
        web = cell(r, 'web'); web = web if re.match(r'https?://', web) else ''
        n['other'] = {'name': re.sub(r'^\s*(outside a park:?)\s*', '', ptxt, flags=re.I)[:120] or 'Other', 'where': cell(r, 'where')[:120], 'gps': cell(r, 'gps')[:60],
                      'web': web[:300], 'type': cell(r, 'otype')[:60]}
    notes.append(n)
notes.sort(key=lambda n: (n['place'] or '~', n['id']))
try: old = json.load(open('kpc-campground-notes.json'))
except Exception: old = None
if not old or old.get('notes') != notes:
    json.dump({'updated': datetime.date.today().isoformat(), 'notes': notes}, open('kpc-campground-notes.json', 'w'), indent=1, ensure_ascii=False)
notice(f'{len(notes)} review(s) posted ({sum(1 for n in notes if not n["place"])} outside the parks), {newph} new photo(s).')
