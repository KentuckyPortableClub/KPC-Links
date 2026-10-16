"""Shared helpers for the KPC Google Form syncs that publish WITHOUT waiting for Brandon when a row looks safe
(Activation Board, Guestbook, CW Challenge Leaderboard).

  sheet(url)       -> (header list, rows)  from a "Publish to web" CSV link
  col(H, name)     -> column index: exact title first, then "starts with"
  clean(text)      -> '' when the text is fine, else the reason (link, email, phone number, swear word, shouting)
  real_call(call)  -> True / False / None (None = the license lookup could not be reached: wait for a YES)
  ref_name(ref)    -> the park / summit / reference name, '' when it does not exist, None when it could not be checked
Look-ups are remembered in data/kpc-form-checks.json (call signs and reference numbers only, both public)."""
import csv, io, json, os, re, time, urllib.request, urllib.parse, datetime

UA = {'User-Agent': 'KPC form sync (kentuckyportableclub.github.io)'}
CACHE_FILE = 'data/kpc-form-checks.json'
try: CACHE = json.load(open(CACHE_FILE))
except Exception: CACHE = {}
CACHE.setdefault('calls', {}); CACHE.setdefault('refs', {})
DAY = 86400

def notice(title, m): print(f'::notice title={title}::' + str(m).replace('%', '%25').replace('\n', '%0A'))

def get(u, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as f: return f.read()

def getj(u):
    try: return json.loads(get(u).decode('utf-8', 'replace') or 'null'), True
    except urllib.error.HTTPError as e: return None, e.code in (400, 404)     # 404 = really not there
    except Exception: return None, False                                    # could not reach it

def sheet(url):
    rows = list(csv.reader(io.StringIO(get(url, 60).decode('utf-8-sig'))))
    return ([h.strip() for h in rows[0]], rows[1:]) if rows else ([], [])

def col(H, name):
    L = [h.lower().strip() for h in H]; n = name.lower()
    if n in L: return L.index(n)
    return next((i for i, h in enumerate(L) if h.startswith(n)), None)

def cell(r, i): return r[i].strip() if i is not None and i < len(r) else ''

def save_cache():
    os.makedirs('data', exist_ok=True)
    json.dump(CACHE, open(CACHE_FILE, 'w'), indent=0, sort_keys=True)

# ------------------------------------------------------------------ text filter
BAD = r'''f+u+c+k\w*|sh[i1]t\w*|b[i1]tch\w*|cunts?|dick(head)?s?|cocks?(sucker)?|puss(y|ies)|assholes?|bastards?|damn(it)?|
goddamn\w*|motherf\w*|wh[o0]res?|sluts?|fags?|faggots?|n[i1]gg\w*|retard\w*|twats?|wank\w*|piss(ed)?|crap|douche\w*|
jackass\w*|dumbass\w*|porn\w*|sex\w*|nude\w*|xxx|viagra|cialis|casino|crypto|bitcoin|forex|loan|lottery'''
BAD_RE = re.compile(r'\b(' + BAD.replace('\n', '') + r')\b', re.I)
LINK_RE = re.compile(r'https?://|www\.|\b[a-z0-9-]+\.(com|net|org|io|us|info|biz|ru|cn|xyz|top|co|me|ly|gg)\b', re.I)
MAIL_RE = re.compile(r'[^\s@]+@[^\s@]+\.[a-z]{2,}', re.I)
PHONE_RE = re.compile(r'(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')
CALLISH = re.compile(r'\b[A-Z0-9]{1,3}\d[A-Z0-9]{1,4}(/[A-Z0-9]{1,4})?\b|\b[A-Z]{1,4}-\d{1,5}\b|\b(CW|SSB|FT8|FT4|FM|AM|POTA|SOTA|WWFF|KFF|QRP|QRT|QSO|QSL|USA|KY|UTC|WPM|NWR|WMA|SP|NF)\b')

def clean(t):
    t = t or ''
    if not t.strip(): return ''
    if LINK_RE.search(t): return 'has a link'
    if MAIL_RE.search(t): return 'has an email address'
    if PHONE_RE.search(t): return 'has a phone number'
    if BAD_RE.search(t): return 'has a word on the not-allowed list'
    letters = re.sub(r'[^A-Za-z]', '', CALLISH.sub('', t))
    if len(letters) >= 12 and sum(c.isupper() for c in letters) / len(letters) > 0.7: return 'is mostly CAPITALS (shouting)'
    if re.search(r'(.)\1{7,}', t): return 'has a long run of the same letter'
    return ''

# ------------------------------------------------------------------ call signs
CALL_RE = re.compile(r'^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}$')

def base(call):
    parts = [p for p in re.sub(r'[^A-Z0-9/]', '', str(call).upper()).split('/') if p]
    return max(parts, key=len) if parts else ''

def real_call(call):
    c = base(call)
    if not CALL_RE.match(c) or not re.search(r'[A-Z]', c) or c in ('K4TEST', 'W4KIDS'): return False
    hit = CACHE['calls'].get(c)
    if hit and time.time() - hit[1] < (30 if hit[0] else 3) * DAY: return hit[0]
    ok, answered = None, False
    j, reached = getj('https://callook.info/' + urllib.parse.quote(c) + '/json')        # US calls
    if reached and j is not None:
        answered = True
        if j.get('status') == 'VALID': ok = True
    if not ok:                                                                          # other countries: HamDB
        j2, r2 = getj('https://api.hamdb.org/' + urllib.parse.quote(c) + '/json/kpc')
        if r2 and j2 is not None:
            answered = True
            if str(((j2.get('hamdb') or {}).get('messages') or {}).get('status', '')).upper() == 'OK': ok = True
    if not answered: return None
    ok = bool(ok)
    CACHE['calls'][c] = [ok, int(time.time())]
    return ok

# ------------------------------------------------------------------ references
try: KY = json.load(open('kpc-ky-data.json'))
except Exception: KY = {}
KYN = {p['c'].upper(): p.get('n', '') for k in ('parks', 'summits', 'kff') for p in KY.get(k, [])}

def norm_ref(r):
    r = re.sub(r'\s+', '', str(r).upper())
    if re.fullmatch(r'\d{1,5}', r): r = 'US-' + r.zfill(4)                  # "1277" = US-1277
    m = re.fullmatch(r'([A-Z0-9]{1,4})-(\d{1,5})', r)
    if m and not m.group(1).endswith('FF'): r = f'{m.group(1)}-{m.group(2).zfill(4)}'
    return r

def split_refs(t): return [norm_ref(x) for x in re.split(r'[,;\s]+', t or '') if x.strip()]

def ref_name(ref):
    r = norm_ref(ref)
    if r in KYN: return KYN[r] or r
    hit = CACHE['refs'].get(r)
    if hit and time.time() - hit[1] < 60 * DAY: return hit[0]
    name = None
    if '/' in r:                                                  # SOTA: W4K/EC-001
        j, reached = getj('https://api2.sota.org.uk/api/summits/' + urllib.parse.quote(r))
        if reached: name = (j or {}).get('name') or (j or {}).get('summitName') or ''
    elif re.match(r'^[A-Z0-9]+FF-\d+$', r):                       # WWFF: KFF-1271
        try:
            d = json.load(open(f"data/wwff/{r.split('-')[0]}.json"))
            name = next((x[1] for x in d if x[0] == r), '')
        except Exception: name = None
    else:                                                         # POTA: US-1271
        j, reached = getj('https://api.pota.app/park/' + urllib.parse.quote(r))
        if reached: name = (j or {}).get('name') or ''
    if name is None: return None
    CACHE['refs'][r] = [name, int(time.time())]
    return name

# ------------------------------------------------------------------ dates and times from the sheet
def sheet_date(t):
    t = (t or '').strip()
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', t)
    if m: return datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', t)
    if m: return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

def sheet_time(t):
    m = re.match(r'\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*([AaPp][Mm])?', t or '')
    if not m: return ''
    h, mi = int(m.group(1)), int(m.group(2))
    if m.group(3):
        h = h % 12 + (12 if m.group(3).lower() == 'pm' else 0)
    return f'{h:02d}:{mi:02d}'

def approval(cell_text):
    a = (cell_text or '').strip().upper()
    if a in ('NO', 'N', 'REJECT', 'REJECTED', 'HIDE'): return 'no'
    if a in ('YES', 'Y', 'APPROVED', 'X', 'OK'): return 'yes'
    return ''

def write_if_changed(path, data, key):
    try: old = json.load(open(path))
    except Exception: old = None
    if not old or old.get(key) != data.get(key) or {k: v for k, v in old.items() if k not in ('updated', key)} != {k: v for k, v in data.items() if k not in ('updated', key)}:
        json.dump(data, open(path, 'w'), indent=1, ensure_ascii=False)
        return True
    return False
