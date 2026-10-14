"""KPC Reports: one Google Form ("KPC Reports"), four kinds of answers. Needs the GitHub secret KPC_REPORTS_CSV
(the sheet's "Publish to web" CSV link). Runs every 2 hours from .github/workflows/kpc-reports.yml.

Form questions (each must START with these words; order doesn't matter; see .claude/CLAUDE.md):
  Call sign | What are you sending  (Park conditions / Report a problem on the website / Share a photo / Add an event)
  Park conditions: Park number | Condition | Details | Date you saw it
  Problem:         Which page or park | What's wrong
  Photo:           Photo | Where was it taken | Caption | OK to use on the website
  Event:           Event name | Event date | Start time | Location | Event website | About the event
  Comment:         Your comment | Show it on the website (Yes / No)
  ("What are you sending" also has the answer "Leave a comment")
  Approved (column Brandon adds to the sheet)

What happens to each kind:
  - Park conditions -> kpc-conditions.json (club members / pre-approved call signs, or YES in Approved; NO blocks).
    Shown for 30 days after "Date you saw it", then dropped. Only Kentucky POTA / SOTA / KFF references.
  - Problems -> never on the site and never saved in the repo. They are listed in ONE GitHub issue labelled
    "kpc-site-problems" until Brandon types DONE (or FIXED / NO) in the Approved cell. No open problems = issue closes.
  - Photos -> photos/members/ (shrunk to 1280 px, no EXIF/GPS) + kpc-member-photos.json, only when approved AND
    the "OK to use on the website" box is ticked.
  - Events -> kpc-events-submitted.json, and merged into kpc-events-auto.json ("found", source MEMBER) so they show
    on the Events page, the home page, Discord and Facebook right away. kpc_events.py merges them in too every Monday.
  - Comments -> kpc-comments.json (Community page "What members are saying"), only when "Show it on the website" is Yes
    AND approved / pre-approved. A No comment is never published, never saved in the repo and never put in the
    GitHub issue: Brandon reads it in his sheet."""
import csv, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_preapproved as PA

TITLE = 'KPC Reports'
def notice(m): print('::notice title=' + TITLE + '::' + str(m).replace('%', '%25').replace('\r', '').replace('\n', '%0A'), flush=True)
URL = os.environ.get('KPC_REPORTS_CSV', '').strip()
if not URL: notice('KPC_REPORTS_CSV secret not set yet; nothing to do.'); sys.exit(0)
TODAY = datetime.date.today()
KEEP_DAYS = 30
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
PRE = PA.load()

def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'KPC reports'}), timeout=60) as f: return f.read()

rows = list(csv.reader(io.StringIO(get(URL).decode('utf-8-sig'))))
if not rows: notice('Sheet is empty.'); sys.exit(0)
H = [h.strip().lower().replace('’', "'") for h in rows[0]]
def col(*names):
    for n in names:
        for i, h in enumerate(H):
            if h.startswith(n): return i
    return None
C = {'ts': col('timestamp'), 'call': col('call sign'), 'kind': col('what are you sending'),
     'ref': col('park number'), 'cond': col('condition'), 'details': col('details'), 'seen': col('date you saw'),
     'page': col('which page'), 'wrong': col("what's wrong", 'what is wrong'),
     'photo': col('photo'), 'where': col('where was it taken'), 'cap': col('caption'), 'ok': col('ok to use'),
     'ename': col('event name'), 'edate': col('event date'), 'etime': col('start time'), 'eloc': col('location'),
     'eweb': col('event website'), 'eabout': col('about the event'),
     'comment': col('your comment'), 'show': col('show it on the website'), 'app': col('approved')}
_miss = [k for k, v in C.items() if v is None and k != 'app']
if _miss: notice('Sheet columns not found (check the question names start with these words): ' + ', '.join(_miss) + '. Columns seen: ' + ' | '.join(h[:30] for h in H))
if C['app'] is None: notice('No "Approved" column in the sheet yet: only pre-approved call signs are posted.')
def cell(r, k): i = C[k]; return r[i].strip() if i is not None and i < len(r) else ''

def kind_of(r):
    k = cell(r, 'kind').lower()
    if 'comment' in k: return 'comment'
    if 'condition' in k: return 'cond'
    if 'problem' in k: return 'problem'
    if 'photo' in k: return 'photo'
    if 'event' in k: return 'event'
    # no answer: guess from what was filled in
    if cell(r, 'ref') and cell(r, 'cond'): return 'cond'
    if cell(r, 'wrong'): return 'problem'
    if cell(r, 'photo'): return 'photo'
    if cell(r, 'ename'): return 'event'
    if cell(r, 'comment'): return 'comment'
    return None

def pdate(s):
    """Google Forms dates: 10/12/2026 (M/D/Y), 2026-10-12, or 'Oct 12, 2026'. Returns a date or None."""
    s = str(s or '').strip()
    m = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', s)
    try:
        if m: return datetime.date(int(m[1]), int(m[2]), int(m[3]))
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', s)
        if m: y = int(m[3]); return datetime.date(y + 2000 if y < 100 else y, int(m[1]), int(m[2]))
        m = re.match(r'([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})', s)
        if m and m[1].title() in MON: return datetime.date(int(m[3]), MON.index(m[1].title()) + 1, int(m[2]))
    except ValueError: return None
    return None

def norm_ref(r):   # same rules as kpc_park_notes.py
    r = re.sub(r'\s+', '', str(r).upper())
    if re.fullmatch(r'\d{1,5}', r): return 'US-' + r.lstrip('0').zfill(4)   # just the number = a POTA park (1277 -> US-1277)
    m = re.fullmatch(r'(US|K|KFF)-?0*(\d+)', r)
    if m: return ('KFF' if m.group(1) == 'KFF' else 'US') + '-' + m.group(2).zfill(4)
    m = re.fullmatch(r'W4K/?([A-Z]{2})-?0*(\d+)', r)
    if m: return f'W4K/{m.group(1)}-{m.group(2).zfill(3)}'
    return r

def clean_call(s): return re.sub(r'[^A-Z0-9/]', '', str(s).upper())[:15]
def rid(r, *extra): return hashlib.sha1('|'.join([cell(r, 'ts'), clean_call(cell(r, 'call'))] + list(extra)).encode()).hexdigest()[:12]
def tsdate(r): return pdate(cell(r, 'ts')) or TODAY

def save(path, key, items, extra=None):
    """Write {updated, key: items} only when the items changed (keeps the bots from committing every run)."""
    try: old = json.load(open(path, encoding='utf-8'))
    except Exception: old = None
    if old and old.get(key) == items: return False
    json.dump({'updated': TODAY.isoformat(), key: items, **(extra or {})}, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return True

D = json.load(open('kpc-ky-data.json', encoding='utf-8'))
REFS = {p['c'] for p in D['parks']} | {s['c'] for s in D['summits']} | {k['c'] for k in D['kff']}
CONDS = ['Gate locked', 'Road closed', 'Flooding', 'Campground closed', 'Hunting in progress', 'Construction', 'Other']

conds, problems, photos, events, comments = [], [], [], [], []
skipped_refs, held = [], 0
os.makedirs('photos/members', exist_ok=True)
try:
    from PIL import Image
except Exception: Image = None
newph = 0; keep_files = set()

for rowno, r in enumerate(rows[1:]):
    k = kind_of(r)
    if not k: continue
    call = clean_call(cell(r, 'call'))
    app = cell(r, 'app').strip().upper()

    if k == 'problem':   # never published; Brandon's to-do list in a GitHub issue
        if app in ('DONE', 'FIXED', 'NO', 'N'): continue
        what = cell(r, 'wrong')
        if not what and not cell(r, 'page'): continue
        problems.append({'date': tsdate(r).isoformat(), 'ts': cell(r, 'ts'), 'call': call, 'page': cell(r, 'page')[:200], 'what': what[:1500]})
        continue

    if k == 'comment':   # private unless the sender said Yes to showing it; private ones stay only in the sheet
        if not cell(r, 'show').strip().lower().startswith('y') or not cell(r, 'comment'): continue

    if not PA.ok(app, call, PRE): held += 1; continue

    if k == 'cond':
        ref = norm_ref(cell(r, 'ref'))
        if ref not in REFS: skipped_refs.append(cell(r, 'ref') or '(blank)'); continue
        cond = cell(r, 'cond') or 'Other'
        cond = next((c for c in CONDS if cond.lower().startswith(c.lower())), cond)[:40]
        seen = min(pdate(cell(r, 'seen')) or tsdate(r), TODAY)
        exp = seen + datetime.timedelta(days=KEEP_DAYS)
        if exp < TODAY: continue
        conds.append({'id': rid(r, ref, cond), 'ref': ref, 'kind': cond, 'details': cell(r, 'details')[:600],
                      'seen': seen.isoformat(), 'call': call, 'expires': exp.isoformat()})

    elif k == 'photo':
        okbox = cell(r, 'ok').lower()
        if not okbox or okbox.startswith('no'): continue   # box not ticked (empty): never used
        nid = rid(r, 'photo')
        for j, pid in enumerate(re.findall(r'id=([A-Za-z0-9_-]{20,})', cell(r, 'photo'))):
            fn = f'photos/members/{nid}-{j + 1}.jpg'
            if not os.path.exists(fn) and Image:
                try:
                    im = Image.open(io.BytesIO(get('https://drive.google.com/uc?export=download&id=' + pid))).convert('RGB')
                    im.thumbnail((1280, 1280)); im.save(fn, 'JPEG', quality=80, optimize=True)   # saved fresh: no GPS/EXIF
                    newph += 1
                except Exception as e: notice(f'Photo from {call} could not be copied (is the Drive folder shared "anyone with the link"?): {e}'); continue
            if os.path.exists(fn):
                keep_files.add(fn)
                photos.append({'id': f'{nid}-{j + 1}', 'file': fn, 'caption': cell(r, 'cap')[:300], 'where': cell(r, 'where')[:160],
                               'call': call, 'date': tsdate(r).isoformat(), '_k': (tsdate(r).isoformat(), rowno, -j)})

    elif k == 'comment':
        comments.append({'id': rid(r, 'comment'), 'call': call, 'text': cell(r, 'comment')[:1500], 'date': tsdate(r).isoformat(), '_k': (tsdate(r).isoformat(), rowno)})

    elif k == 'event':
        name = cell(r, 'ename'); start = pdate(cell(r, 'edate'))
        if not name or not start or start < TODAY or start > TODAY + datetime.timedelta(days=500): continue
        loc = cell(r, 'eloc'); web = cell(r, 'eweb')
        if web and not re.match(r'https?://', web) and re.match(r'[\w-]+(\.[\w-]+)+(/\S*)?$', web): web = 'https://' + web
        tags = [t for t, pat in (('POTA', r'\bpota\b|parks on the air'), ('SOTA', r'\bsota\b|summits on the air'), ('HAMFEST', r'hamfest|swap ?meet|convention|tailgate'),
                                 ('CONTEST', r'contest|qso party|sprint'), ('ONAIR', r'field day|\bnet\b|special event'))
                if re.search(pat, (name + ' ' + cell(r, 'eabout')).lower())] + ['MEMBER']
        ev = {'name': name[:120], 'tags': tags, 'start': start.isoformat()}
        t = cell(r, 'etime')
        if t: ev['time'] = re.sub(r':00(\s*[AP]M)$', r'\1', re.sub(r'^(\d{1,2}:\d{2}):\d{2}', r'\1', t))[:80]
        ev['where'] = loc[:200] or 'See the event website'
        ev['by'] = 'Shared by ' + call if call else 'Shared by a KPC member'
        if web and re.match(r'https?://', web): ev['url'] = web[:300]
        elif loc: ev.update({'url': 'https://www.google.com/maps/search/?api=1&query=' + urllib.request.quote(loc[:200]), 'urllabel': 'MAP ↗'})
        else: ev.update({'url': 'events.html#ky-radio-calendar', 'local': True})
        if cell(r, 'eabout'): ev['about'] = cell(r, 'eabout')[:400]
        ev.update({'source': 'MEMBER', 'member': True, 'id': rid(r, 'event', name)})
        events.append(ev)

# ---------- conditions
conds.sort(key=lambda c: (c['seen'], c['id']), reverse=True)
save('kpc-conditions.json', 'items', conds)

# ---------- member photos (newest first; files no longer published are removed)
photos.sort(key=lambda p: p['_k'], reverse=True)
for p in photos: del p['_k']
save('kpc-member-photos.json', 'photos', photos)
gone = 0
for f in os.listdir('photos/members'):
    p = 'photos/members/' + f
    if re.fullmatch(r'[0-9a-f]{12}-\d+\.jpg', f) and p not in keep_files: os.remove(p); gone += 1

# ---------- comments (newest first)
comments.sort(key=lambda c: c['_k'], reverse=True)
for c in comments: del c['_k']
save('kpc-comments.json', 'comments', comments)

# ---------- events (dedupe: same name + date once)
def nn(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
seen_ev, uniq = set(), []
for e in sorted(events, key=lambda e: (e['start'], e['name'])):
    key = (nn(e['name']), e['start'])
    if key in seen_ev: continue
    seen_ev.add(key); uniq.append(e)
events = uniq
save('kpc-events-submitted.json', 'events', events)
try:
    auto = json.load(open('kpc-events-auto.json', encoding='utf-8'))
    have = {(nn(e.get('name')), e.get('start')) for e in auto.get('recurring', []) + auto.get('found', []) if e.get('source') != 'MEMBER'}
    found = [e for e in auto.get('found', []) if e.get('source') != 'MEMBER'] + [e for e in events if (nn(e['name']), e['start']) not in have]
    if found != auto.get('found', []):
        auto['found'] = found
        open('kpc-events-auto.json', 'w', encoding='utf-8').write(json.dumps(auto, ensure_ascii=False, indent=1) + '\n')
except Exception as e: notice('Could not merge member events into kpc-events-auto.json: ' + str(e))

# ---------- problems: one rolling GitHub issue
problems.sort(key=lambda p: (p['date'], p['ts']), reverse=True)
def md(s):   # keep sheet text from pinging people or breaking the table
    s = re.sub(r'<[^>]*>', '', str(s)).replace('|', '/').replace('@', '@​')
    return re.sub(r'\s+', ' ', s).strip() or '-'
body = ('Website problems sent in on the **KPC Reports** form (“Report a problem on the website”). '
        'These are never shown on the website.\n\n'
        '**When one is fixed, type `DONE` in its Approved cell in the sheet.** (`NO` hides a junk report.) '
        'This list updates every 2 hours and the issue closes itself when nothing is left.\n\n'
        '| Sent | Call | Page or park | What\'s wrong |\n|---|---|---|---|\n' +
        '\n'.join(f"| {datetime.date.fromisoformat(p['date']).strftime('%b %d, %Y')} | {md(p['call'])} | {md(p['page'])} | {md(p['what'])} |" for p in problems) + '\n')
title = f'Website problem reports ({len(problems)} open)'
if os.environ.get('GITHUB_ACTIONS') == 'true' and shutil.which('gh') and (os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')):   # only touch issues from the workflow
    import kpc_issue
    kpc_issue.report('kpc-site-problems', title, body, len(problems))
else:
    print('(Not running in GitHub Actions with gh + GH_TOKEN, so the issue was not touched. It would be:)')
    print(('OPEN ' + title + '\n' + body) if problems else 'CLOSE any open kpc-site-problems issue (no open problems).')

notice(f'{len(conds)} condition(s) showing, {len(photos)} member photo(s) ({newph} new, {gone} removed), {len(events)} member event(s), {len(comments)} comment(s) shown, '
       f'{len(problems)} open problem report(s), {held} row(s) not posted (waiting for YES in Approved, or marked NO).' + (f' Skipped unknown park numbers: {", ".join(skipped_refs[:10])}' if skipped_refs else ''))
