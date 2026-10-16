#!/usr/bin/env python3
"""KPC Discord relay: posts from the private Discord channel -> website, Facebook Page, another Discord server,
Groups.io, the email-updates list, the Events calendar and park condition warnings.

HOW A POST IS READ (Brandon Oct 15). Words at the very START of the post, before a colon, are the "tag":
  where it goes : Website / Facebook (FB) / Discord / Groups.io (Group) / Subscribers / Email (= Groups.io + subscribers) / All
  minus         : -Groups.io / No Facebook / All except Email  (only minuses = everywhere except those)
  how fast      : Now  (right away, everywhere unless other places are named, subscribers emailed at once)
  when          : Post Oct 20 8am / Schedule Friday 6pm / Post tomorrow noon  (waits until then, Central time)
  what kind     : Event (calendar)  /  Conditions US-1277 (red park warning, 30 days)  /  Activation (News page reports)
  extra page    : Campout / Announcement (these also still work anywhere in the post)
  not shared    : Skip: / Ignore: / Do not share:  (notes and the pinned how-to guide in the channel)
  Mix with + or spaces: "Now + Facebook:", "Campout + All:", "Event + Email:", "Post Oct 20 8am + All:".
No tag = Website + Facebook + the other Discord server. Email ONLY when the tag says Email / Groups.io / Subscribers /
All / Now. Website posts also go to the other Discord server (RELAY_DISCORD_WEBHOOKS).
Subscribers get ONE email each Sunday evening with the week's website posts (the roundup); "Now:" and "Subscribers:"
email them right away instead.
EDITS and DELETES in Discord follow on the website, Facebook and the other server (email can't be unsent).
PINNED Discord posts stay at the top of their website page.
Poster names are never shown. Reactions: ✅ done, ⏰ waiting for its time, ⏳ email still going out, ⚠️ a problem.

Secrets (GitHub -> Settings -> Secrets and variables -> Actions; never in the site or chat):
  DISCORD_BOT_TOKEN, KPC_RELAY_CHANNEL, FB_PAGE_ID, FB_PAGE_TOKEN, GROUPSIO_TO, SUBSCRIBE_SHEET_CSV,
  RELAY_MAIL_URL + RELAY_MAIL_KEY (Apps Script mailer in kpcwebhost@gmail.com), RELAY_DISCORD_WEBHOOKS (one or more
  webhook links of channels in other servers, separated by spaces or new lines). RELAY_SMTP_USER/PASS = old SMTP way.
DRY_RUN=1 prints what would happen and changes nothing.
"""
import base64, csv, datetime, hashlib, hmac, io, json, os, re, shutil, smtplib, ssl, sys, tempfile, time, uuid
import urllib.error, urllib.parse, urllib.request
from email.message import EmailMessage
from zoneinfo import ZoneInfo

TITLE = 'KPC Discord relay'
def notice(m): print('::notice title=' + TITLE + '::' + str(m).replace('%', '%25').replace('\r', '').replace('\n', '%0A'), flush=True)

ENV = lambda k: (os.environ.get(k) or '').strip()
TOKEN, CHAN = ENV('DISCORD_BOT_TOKEN'), ENV('KPC_RELAY_CHANNEL')
FB_ID, FB_TOKEN = ENV('FB_PAGE_ID'), ENV('FB_PAGE_TOKEN')
SMTP_USER, SMTP_PASS, GIO_TO = (ENV('RELAY_SMTP_USER') or 'kypotacampout@gmail.com'), ENV('RELAY_SMTP_PASS'), ENV('GROUPSIO_TO')
SUB_CSV = ENV('SUBSCRIBE_SHEET_CSV')
MAIL_URL, MAIL_KEY = ENV('RELAY_MAIL_URL'), ENV('RELAY_MAIL_KEY')
HOOKS = [u for u in re.split(r'\s+', ENV('RELAY_DISCORD_WEBHOOKS')) if re.match(r'https://(?:\w+\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+(\?\S*)?$', u)]
DRY = ENV('DRY_RUN').lower() in ('1', 'true', 'yes')
CAP = int(ENV('RELAY_DAILY_CAP') or 90)
SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
STATE, OUT, PHOTOS = 'kpc-relay-state.json', 'kpc-announcements.json', 'photos/announce'
API = 'https://discord.com/api/v10'
UA = 'KPC-Relay (https://kentuckyportableclub.github.io/KPC-Links/, 2.0)'
CT = ZoneInfo('America/Chicago')
NOW = datetime.datetime.fromisoformat(ENV('RELAY_NOW')).astimezone(CT) if ENV('RELAY_NOW') else datetime.datetime.now(CT)   # RELAY_NOW: tests only
PAGE_URL = {'campout': 'campout.html', 'news': 'news.html', 'activation': 'news.html#reports'}

if not TOKEN or not CHAN:
    notice('No DISCORD_BOT_TOKEN / KPC_RELAY_CHANNEL secret yet; nothing to do.'); sys.exit(0)

# ---------------------------------------------------------------- web helpers
def http(url, data=None, headers=None, method=None, timeout=60):
    h = {'User-Agent': UA}; h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, r.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429 and i < 3:
                try: wait = float(json.loads(body).get('retry_after', 2))
                except Exception: wait = 2
                time.sleep(min(wait, 30) + .5); continue
            return e.code, body
        except Exception as e:
            if i == 3: return 0, str(e).encode()
            time.sleep(3 * (i + 1))

def dc(path, method='GET', body=None):
    hd = {'Authorization': 'Bot ' + TOKEN}
    if body is not None: hd['Content-Type'] = 'application/json'; body = json.dumps(body).encode()
    return http(API + path, body, hd, method)

def react(mid, emo, how='PUT'):
    if mid and not DRY: dc(f'/channels/{CHAN}/messages/{mid}/reactions/{urllib.parse.quote(emo)}/@me', how)

def multipart(fields, files=(), field='source'):
    b = uuid.uuid4().hex; parts = []
    for k, v in fields.items(): parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for i, f in enumerate(files):
        name = field if field == 'source' else f'files[{i}]'
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{name}"; filename="photo{i + 1}.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + open(f, 'rb').read() + b'\r\n')
    parts.append(f'--{b}--\r\n'.encode())
    return b''.join(parts), {'Content-Type': 'multipart/form-data; boundary=' + b}

def load(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d

def mtime(mid):   # Discord ids carry their own time
    return datetime.datetime.fromtimestamp(((int(mid) >> 22) + 1420070400000) / 1000, CT)

# ---------------------------------------------------------------- reading a post
MONTHS = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}
DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
D_MONTH = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?'
D_DAY = r'(?:mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:rs(?:day)?)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\.?'
D_TIME = r'(?:\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?|a|p)(?!\w)|\d{1,2}:\d{2}|noon|midnight)'
D_ANY = r'(?:' + D_MONTH + r'|' + D_DAY + r'|' + D_TIME + r'|\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{1,2}(?:st|nd|rd|th)?|\d{4}|tomorrow|today|tonight|at|on|of|,)'
REFRX = r'(?:US-\d{4,5}|KFF-\d{4}|W4K/[A-Z]{2}-\d{3}|\d{4,5})'
WORDS = [  # (pattern, flag)  -- every word in a tag must be one of these, or it's just normal text
    (r'groups?[ .]?io|groups?', 'gio'), (r'subscribers?|email list|mailing list', 'list'), (r'e-?mails?', 'email'),
    (r'facebook|fb', 'fb'), (r'discord', 'dc'), (r'web ?site|web|site', 'web'), (r'all|everything|everywhere', 'all'),
    (r'now|urgent|important|asap', 'now'), (r'post|schedule[d]?|send', 'sched'),
    (r'events?', 'event'), (r'conditions?|park alert|warning', 'cond'), (r'activation(?: report)?s?', 'act'),
    (r'skip|ignore|do not share|don.?t share|not for sharing', 'skip'), (r'no|not|except|without|minus|but', 'not'), (r'camp ?-?out', 'campout'), (r'announcements?', 'news'), (r'only|and|also|\+|&|,|/|-', None),
    (r'US-\d{4,5}|KFF-\d{4}|W4K/[A-Z]{2}-\d{3}', 'ref'), (D_ANY, 'date'), (r'\d{5}', 'date')]
WRX = re.compile(r'\s*(?:' + '|'.join('(' + p + ')' for p, _ in WORDS) + r')(?:(?<=[^\w])|(?![\w/-]))', re.I)   # "+" may touch the next word

def split_tag(raw):
    """-> (set of flags, tag text, rest of the post) or (set(), '', raw) when the post has no tag."""
    m = re.match(r'\s*([^\n]{1,120}?):(?!\d)\s*', raw or '')
    if not m: return set(), '', raw or ''
    tag, pos, flags, neg = m.group(1), 0, set(), False
    PLACES = {'web', 'fb', 'dc', 'gio', 'list', 'email'}
    while pos < len(tag):
        w = WRX.match(tag, pos)
        if not w or w.end() == pos:
            if tag[pos:].strip() == '': break
            return set(), '', raw
        f = next((WORDS[i][1] for i, g in enumerate(w.groups()) if g), None)
        if f == 'not' or (w.group(0).strip() == '-' and pos < len(tag) - 1 and w.end() < len(tag) and not tag[w.end()].isspace()
                          and (w.start() == 0 or tag[w.start():w.end()].startswith(' ') or tag[w.start() - 1] in ' +,&')):
            neg = True                                   # "-Groups.io" / "No Facebook" / "All except Email"
        elif f in PLACES and neg: flags.add('no_' + f); neg = False
        else:
            flags.add(f)
            if f is not None: neg = False
        pos = w.end()
    flags.discard(None); flags.discard('not')
    real = {f for f in flags if not f.startswith('no_')} - {'date', 'ref'} | {'x' for f in flags if f.startswith('no_')}
    if not real: return set(), '', raw                     # "10:30:" or "Oct 5:" alone is not a tag
    if 'ref' in flags and 'cond' not in flags: return set(), '', raw
    if 'date' in flags and not flags & {'sched', 'event', 'cond', 'act'}: return set(), '', raw
    return flags, tag, raw[m.end():]

def parse_when(s, base=None, default_hour=8):
    """'Oct 20 8am', 'Friday 6:30pm', 'tomorrow noon', '11/7', 'Nov 7 2026' -> (datetime CT, had_time) or (None, False)."""
    base = base or NOW; s = s.lower()
    d = None
    m = re.search(D_MONTH.replace('\\.?', '') + r'\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?', s)
    if m:
        mon = MONTHS[m.group(0)[:3]]; day = int(m.group(1)); yr = int(m.group(2) or base.year)
        try: d = datetime.date(yr, mon, day)
        except ValueError: return None, False
        if not m.group(2) and d < base.date() - datetime.timedelta(days=2): d = d.replace(year=yr + 1)
    if not d:
        m = re.search(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', s)
        if m:
            yr = int(m.group(3)) if m.group(3) else base.year
            if yr < 100: yr += 2000
            try: d = datetime.date(yr, int(m.group(1)), int(m.group(2)))
            except ValueError: return None, False
            if not m.group(3) and d < base.date() - datetime.timedelta(days=2): d = d.replace(year=yr + 1)
    if not d and re.search(r'\btomorrow\b', s): d = base.date() + datetime.timedelta(days=1)
    if not d and re.search(r'\b(today|tonight)\b', s): d = base.date()
    if not d:
        m = re.search(r'\b(' + '|'.join(DAYS) + r')[a-z]*\b', s)
        if m:
            ahead = (DAYS.index(m.group(1)) - base.weekday()) % 7
            d = base.date() + datetime.timedelta(days=ahead)
    hh = mm = None
    m = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?|a|p)(?!\w)', s)
    if m:
        hh, mm = int(m.group(1)) % 12, int(m.group(2) or 0)
        if m.group(3).startswith('p'): hh += 12
    elif re.search(r'\bnoon\b', s): hh, mm = 12, 0
    elif re.search(r'\bmidnight\b', s): hh, mm = 0, 0
    elif re.search(r'\btonight\b', s): hh, mm = 19, 0
    else:
        m = re.search(r'\b(\d{1,2}):(\d{2})\b', s)
        if m: hh, mm = int(m.group(1)), int(m.group(2))
    if d is None and hh is None: return None, False
    if d is None:
        d = base.date()
        if datetime.datetime.combine(d, datetime.time(hh, mm), CT) <= base: d += datetime.timedelta(days=1)
    elif hh is not None and re.search(r'\b(' + '|'.join(DAYS) + r')[a-z]*\b', s) and not re.search(r'\d{1,2}/\d|' + D_MONTH, s):
        if datetime.datetime.combine(d, datetime.time(hh, mm), CT) <= base: d += datetime.timedelta(days=7)
    if hh is None or hh > 23 or mm > 59: return datetime.datetime.combine(d, datetime.time(default_hour, 0), CT), False
    return datetime.datetime.combine(d, datetime.time(hh, mm), CT), True

def who(u, member=None):
    return ((member or {}).get('nick') or u.get('global_name') or u.get('username') or '').strip()

def tidy(t, m):
    names = {u['id']: who(u, u.get('member')) for u in m.get('mentions', [])}
    t = re.sub(r'<@!?(\d+)>', lambda x: names.get(x.group(1), ''), t)
    t = re.sub(r'<@&\d+>|<#\d+>|@everyone|@here', '', t)
    t = re.sub(r'<t:(\d+)(?::\w)?>', lambda x: datetime.datetime.fromtimestamp(int(x.group(1)), CT).strftime('%b %-d, %Y %-I:%M %p'), t)
    t = re.sub(r'<a?:(\w+):\d+>', r':\1:', t)
    t = re.sub(r'<(https?://[^>\s]+)>', r'\1', t)
    t = re.sub(r'\*\*|__|~~|\|\||`{1,3}', '', t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()

KYD = load('kpc-ky-data.json', {})
KYREFS = {p['c']: p.get('n', '') for k in ('parks', 'summits', 'kff') for p in KYD.get(k, [])}
COND_KINDS = [('Gate locked', r'gate|locked'), ('Road closed', r'road.{0,12}closed|closed road|washed out|bridge out'),
              ('Flooding', r'flood|high water|under water'), ('Campground closed', r'campground.{0,12}closed|camping closed'),
              ('Hunting in progress', r'hunt|deer season|gun season|turkey season'), ('Construction', r'construction|work crew|repair')]

def parse(m):
    raw = m.get('content') or ''
    flags, tag, rest = split_tag(raw)
    text = tidy(rest, m)
    low = raw.lower()
    p = {'flags': flags, 'tag': tag, 'text': text}
    p['kind'] = 'event' if 'event' in flags else 'cond' if 'cond' in flags else 'act' if 'act' in flags else 'news'
    p['now'] = 'now' in flags
    named = flags & {'web', 'fb', 'dc', 'gio', 'list', 'email', 'all'}
    nots = {f[3:] for f in flags if f.startswith('no_')}
    if nots and not (named - {'all'}): named = {'all'}         # only minuses = everywhere except those
    if 'all' in named or (p['now'] and not named): dest = {'web', 'fb', 'dc', 'gio', 'list'}
    elif named:
        dest = set(named) - {'email'}
        if 'email' in flags: dest |= {'gio', 'list'}
        if 'web' in dest: dest.add('dc')                   # the other server mirrors the website
    elif p['kind'] == 'cond': dest = set()                 # a condition is just the red park warning unless places are named
    else: dest = {'web', 'fb', 'dc'}
    for f in nots: dest -= {'gio', 'list'} if f == 'email' else {f}
    p['dest'] = dest
    p['list_now'] = 'list' in dest and (p['now'] or 'list' in flags)   # otherwise subscribers get it in the Sunday roundup
    if p['kind'] == 'act': pages = ['activation']
    else:
        pages = []
        if 'campout' in flags or re.search(r'camp\s?-?out', low): pages += ['campout', 'news']
        if 'news' not in pages: pages.append('news')
    p['pages'] = pages
    p['due'] = p['when'] = None
    if 'sched' in flags and not p['now']:
        # "tomorrow 8am" means tomorrow from when the post was written (or last edited), not from today's run
        base = datetime.datetime.fromisoformat(m['edited_timestamp']).astimezone(CT) if m.get('edited_timestamp') else mtime(m['id']) if m.get('id') else NOW
        when, _ = parse_when(tag, base=base)
        p['when'] = when
        if when and when > NOW + datetime.timedelta(minutes=2): p['due'] = when
        elif not when: p['bad_when'] = True
    if p['kind'] == 'cond':
        refs = []
        for r in re.findall(REFRX, tag.upper()) + re.findall(REFRX, text.upper()):
            r = 'US-' + r if re.fullmatch(r'\d{4,5}', r) else r
            if r in KYREFS and r not in refs: refs.append(r)
        p['refs'] = refs
        p['cond_kind'] = next((k for k, rx in COND_KINDS if re.search(rx, text, re.I)), 'Other')
    if p['kind'] == 'event': p['event'] = parse_event(text)
    return p

def parse_event(text):
    """First line = name; 'Date:', 'Time:', 'Where:' / 'Location:', 'Link:' / 'Website:' lines; the rest = about."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    f, about, name = {}, [], ''
    for l in lines:
        m = re.match(r'(date|dates|when|time|times|start|where|location|place|link|website|web|url|end|ends)\s*[:\-–]\s*(.+)$', l, re.I)
        if m:
            k = m.group(1).lower()
            k = {'dates': 'date', 'when': 'date', 'times': 'time', 'start': 'time', 'location': 'where', 'place': 'where',
                 'website': 'link', 'web': 'link', 'url': 'link', 'ends': 'end'}.get(k, k)
            f[k] = m.group(2).strip()
        elif not name: name = l
        else: about.append(l)
    if not f.get('date') and name:              # "Fall Activation Day Nov 7"
        w, _ = parse_when(name)
        if w and re.search(D_MONTH + r'|\d{1,2}/\d{1,2}', name, re.I): f['date'] = name
    start, _ = parse_when(f.get('date', ''), default_hour=0) if f.get('date') else (None, False)
    if not name or not start: return None
    ev = {'name': name[:120], 'start': start.date().isoformat()}
    rng = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|to|thru|through)\s*(' + D_MONTH + r'\s*)?(\d{1,2})\b', f['date'], re.I)
    end = None
    if f.get('end'): end, _ = parse_when(f['end'], base=start, default_hour=0)
    elif rng:
        try:
            mon = MONTHS[rng.group(2).strip()[:3].lower()] if rng.group(2) else start.month
            e = datetime.date(start.year + (1 if mon < start.month else 0), mon, int(rng.group(3)))
            if e > start.date(): end = datetime.datetime.combine(e, datetime.time(0), CT)
        except (ValueError, KeyError): pass
    if end and end.date() > start.date(): ev['end'] = end.date().isoformat()
    if f.get('time'): ev['time'] = f['time'][:80]
    ev['where'] = (f.get('where') or 'See the event details')[:200]
    tags = [t for t, pat in (('POTA', r'\bpota\b|parks on the air'), ('SOTA', r'\bsota\b|summits on the air'),
                             ('HAMFEST', r'hamfest|swap ?meet|convention|tailgate'), ('CONTEST', r'contest|qso party|sprint'),
                             ('ONAIR', r'field day|\bnet\b|special event'), ('CAMPOUT', r'camp ?out'))
            if re.search(pat, text.lower())]
    ev['tags'] = tags + ['MEMBER']
    ev['by'] = 'Kentucky Portable Club'
    link = (f.get('link') or '').strip()
    if link and not re.match(r'https?://', link) and re.match(r'[\w-]+(\.[\w-]+)+(/\S*)?$', link): link = 'https://' + link
    if re.match(r'https?://\S+$', link): ev['url'] = link[:300]
    elif f.get('where'): ev.update({'url': 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(f['where'][:200]), 'urllabel': 'MAP ↗'})
    else: ev.update({'url': 'news.html', 'local': True})
    if about: ev['about'] = ' '.join(about)[:400]
    return ev

# ---------------------------------------------------------------- pictures
def shrink(data, dest):
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(data)); im = ImageOps.exif_transpose(im)
    if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
    im.thumbnail((1280, 1280))
    im.save(dest, 'JPEG', quality=85, optimize=True)        # new file: no EXIF / GPS

def get_photos(m, folder):
    out = []
    for n, a in enumerate([a for a in m.get('attachments', []) if (a.get('content_type') or '').startswith('image/')][:10], 1):
        c, data = http(a['url'])
        if c != 200: continue
        f = os.path.join(folder, f"{m['id']}-{n}.jpg")
        try: shrink(data, f); out.append(f)
        except Exception as e: notice(f'Picture skipped ({e}).')
    return out

def other_files(m):
    return [a['url'] for a in m.get('attachments', []) if not (a.get('content_type') or '').startswith('image/')]

# ---------------------------------------------------------------- Facebook
def fb_call(path, fields, files=(), method='POST'):
    if method == 'DELETE':
        c, r = http(f'https://graph.facebook.com/v19.0/{path}?access_token={urllib.parse.quote(FB_TOKEN)}', None, None, 'DELETE')
    else:
        body, hd = multipart(dict(fields, access_token=FB_TOKEN), files)
        c, r = http(f'https://graph.facebook.com/v19.0/{path}', body, hd, 'POST')
    j = json.loads(r or b'{}') if r else {}
    if c != 200 or 'error' in j: raise RuntimeError((j.get('error') or {}).get('message') or f'HTTP {c}')
    return j

def fb_new(text, files):
    if len(files) == 1:
        j = fb_call(FB_ID + '/photos', {'caption': text}, files); return j.get('post_id') or j.get('id')
    fields = {'message': text}
    for i, f in enumerate(files[:10]):
        j = fb_call(FB_ID + '/photos', {'published': 'false'}, [f]); fields[f'attached_media[{i}]'] = json.dumps({'media_fbid': j['id']})
    return fb_call(FB_ID + '/feed', fields).get('id')

# ---------------------------------------------------------------- the other Discord server(s)
def hook_send(url, text, files, mid=None):
    payload = {'content': text[:1990], 'username': 'Kentucky Portable Club', 'allowed_mentions': {'parse': []}}
    if mid:
        body, hd = multipart({'payload_json': json.dumps(payload)})
        base, _, q = url.partition('?')
        c, r = http(f'{base}/messages/{mid}' + ('?' + q if q else ''), body, hd, 'PATCH')
    else:
        body, hd = multipart({'payload_json': json.dumps(payload)}, files[:10], field='files')
        c, r = http(url + ('&' if '?' in url else '?') + 'wait=true', body, hd, 'POST')
    if c not in (200, 204): raise RuntimeError(f'webhook HTTP {c}: {(r or b"")[:120]!r}')
    return (json.loads(r).get('id') if r else mid)

def hook_delete(url, mid):
    base, _, q = url.partition('?')
    http(f'{base}/messages/{mid}' + ('?' + q if q else ''), None, None, 'DELETE')

# ---------------------------------------------------------------- email
def mail(to, bcc, subject, text, files):
    if MAIL_URL and MAIL_KEY:
        body = json.dumps({'key': MAIL_KEY, 'to': to, 'bcc': bcc, 'subject': subject, 'body': text,
                           'images': [{'name': os.path.basename(f), 'b64': base64.b64encode(open(f, 'rb').read()).decode()} for f in files]}).encode()
        c, r = http(MAIL_URL, body, {'Content-Type': 'application/json'}, 'POST', timeout=90)
        t = (r or b'').decode('utf8', 'replace')
        if c != 200 or '"ok":true' not in t.replace(' ', ''): raise RuntimeError(f'mailer said HTTP {c}: {t[:150]}')
        return
    if not SMTP_PASS: raise RuntimeError('no email secrets')
    em = EmailMessage(); em['From'] = f'Kentucky Portable Club <{SMTP_USER}>'; em['To'] = to or SMTP_USER
    em['Subject'] = subject
    if bcc: em['Bcc'] = ', '.join(bcc)
    em.set_content(text)
    for f in files: em.add_attachment(open(f, 'rb').read(), maintype='image', subtype='jpeg', filename=os.path.basename(f))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context(), timeout=60) as s:
        s.login(SMTP_USER, SMTP_PASS); s.send_message(em)

def subscribers():
    """Latest answer per email wins: Subscribe -> on the list, Unsubscribe -> off."""
    if not SUB_CSV: return []
    c, r = http(SUB_CSV)
    if c != 200: notice(f'Could not read the subscriber sheet (HTTP {c}).'); return []
    rows = list(csv.reader(io.StringIO(r.decode('utf-8-sig'))))
    if not rows: return []
    hd = [h.strip().lower() for h in rows[0]]
    ie = next((i for i, h in enumerate(hd) if 'email' in h), None)
    ic = next((i for i, h in enumerate(hd) if 'subscribe' in h or 'what would you like' in h), None)
    if ie is None or ic is None: notice('Subscriber sheet needs an Email column and a Subscribe/Unsubscribe column.'); return []
    on = {}
    for row in rows[1:]:
        e = (row[ie] if ie < len(row) else '').strip().lower()
        if not re.fullmatch(r'[^@\s,;<>]+@[^@\s,;<>]+\.[a-z]{2,}', e): continue
        on[e] = not re.search(r'unsub|stop|remove', (row[ic] if ic < len(row) else '').lower())
    return sorted(e for e, v in on.items() if v)

def spam_tip():
    return ('Tip: save kpcwebhost@gmail.com as a contact so our emails stay out of Spam (a one-tap contact card is at '
            + SITE + 'news.html). If one lands in Spam, tap "Not spam".')

def unsub_line():
    f = load('kpc-subscribe-form.json', {})
    if re.match(r'https://docs\.google\.com/forms/', f.get('url') or '') and f.get('choiceEntry'):
        u = f['url'] + ('&' if '?' in f['url'] else '?') + 'usp=pp_url&' + urllib.parse.urlencode({f['choiceEntry']: f.get('unsubscribe') or 'Unsubscribe'})
        return 'To stop these emails, tap here and press Submit: ' + u
    return 'To stop these emails, use the UNSUBSCRIBE button on ' + SITE + 'news.html'

# Gmail daily limit: a personal Gmail Apps Script may email about 100 people per rolling 24 hours (every To/Bcc counts;
# Groups.io counts as ONE because it sends to its members itself). We stay under CAP, remember what went out ("sent"),
# and leave the rest in "queue" for the next runs. No email addresses are saved: only keyed fingerprints of who got it.
def fp(e): return hmac.new((MAIL_KEY or TOKEN).encode(), e.encode(), hashlib.sha256).hexdigest()[:20]
def room():
    now = time.time()
    state['sent'] = [x for x in state.get('sent', []) if now - x[0] < 86400 + 600]
    return CAP - sum(x[1] for x in state['sent'])
def spent(n): state.setdefault('sent', []).append([int(time.time()), n])

def flush_mail():
    q = state.get('queue') or []
    if not q: return
    if not (MAIL_URL and MAIL_KEY) and not SMTP_PASS:
        notice(f'{len(q)} email(s) waiting: the email secrets are not set yet.'); return
    subs = None
    with tempfile.TemporaryDirectory() as tmp:
        for it in list(q):
            files = []
            if it.get('mid'):
                c, r = dc(f"/channels/{CHAN}/messages/{it['mid']}")
                if c == 200: files = get_photos(json.loads(r), tmp)
            bad = []
            if it.get('gio') and GIO_TO:
                if room() < 1: break
                try: mail(GIO_TO, [], it['subject'], it['body'], files); spent(1); it['gio'] = False
                except Exception as e:
                    bad.append('groups.io: ' + str(e)[:150])
                    if re.search(r'too many|quota|limit', str(e), re.I): break
            elif it.get('gio'): it['gio'] = False
            if it.get('list'):
                if subs is None: subs = subscribers()
                todo = [e for e in subs if fp(e) not in it['done']]
                while todo:
                    n = min(80, room() - 1)                    # -1: the account's own To: address counts too
                    if n < 1: break
                    part = todo[:n]
                    try: mail('' if MAIL_URL else SMTP_USER, part, it['subject'], it['body'] + '\n\n' + spam_tip() + '\n\n' + unsub_line(), files)
                    except Exception as e: bad.append('email list: ' + str(e)[:150]); break
                    spent(len(part) + 1); it['done'] += [fp(e) for e in part]; todo = todo[n:]
                if not todo: it['list'] = False
            if bad:
                notice('Email problem: ' + '; '.join(bad)); react(it.get('mid'), '⚠️')
                it['tries'] = it.get('tries', 0) + 1
                if it['tries'] >= 8: q.remove(it); notice('Gave up on an email after 8 tries.'); continue
            if not it.get('gio') and not it.get('list'):
                q.remove(it); react(it.get('mid'), '⏳', 'DELETE')
                if not bad: react(it.get('mid'), '✅')
                notice(f"Emailed {it.get('what') or 'a post'} ({len(it['done'])} subscriber(s)).")
            else:
                react(it.get('mid'), '⏳')
                notice('Gmail daily limit reached; the rest goes out in the next runs.'); break
    state['queue'] = q

def queue_mail(mid, subject, body, gio, lst, now, what=''):
    item = {'mid': mid, 'subject': subject, 'body': body, 'gio': bool(gio), 'list': bool(lst), 'done': [], 'what': what}
    q = state.setdefault('queue', [])
    q.insert(0, item) if now else q.append(item)

# ---------------------------------------------------------------- state
state = load(STATE, {})
state0 = json.dumps(state, sort_keys=True)
feed = load(OUT, {'items': []})
feed0 = json.dumps(feed, sort_keys=True)
posts = state.setdefault('posts', {})      # mid -> what we published (fb id, other-server ids, ...)
sched = state.setdefault('sched', {})      # mid -> due time (ISO, Central)

code, raw = dc(f'/channels/{CHAN}/messages?limit=100')
if code != 200:
    notice(f'Discord said HTTP {code}: {raw[:200]!r}. Check the bot is in the server, can see the channel, and has Read Message History.')
    sys.exit(1)
window = sorted(json.loads(raw), key=lambda m: int(m['id']))
byid = {m['id']: m for m in window}
full = len(window) < 100                   # we can see the whole channel
oldest = int(window[0]['id']) if window else 0
c, r = dc(f'/channels/{CHAN}/pins')
pins = {m['id'] for m in json.loads(r)} if c == 200 else None

if not state.get('last_id'):
    if not DRY:
        state['last_id'] = window[-1]['id'] if window else '0'; json.dump(state, open(STATE, 'w'), indent=1)
    notice(f'First run: saved the starting point ({len(window)} older messages left alone). New posts from now on will be shared.')
    sys.exit(0)

def visible(mid): return full or int(mid) >= oldest

def feed_remove(mid):
    feed['items'] = [it for it in feed.get('items', []) if it.get('id') != mid]
    for f in os.listdir(PHOTOS) if os.path.isdir(PHOTOS) else []:
        if f.startswith(mid + '-') and not DRY: os.remove(os.path.join(PHOTOS, f))

def unpublish(mid):
    rec = posts.pop(mid, {})
    feed_remove(mid)
    if rec.get('fb') and FB_TOKEN and not DRY:
        try: fb_call(rec['fb'], {}, method='DELETE')
        except Exception as e: notice('Could not delete the Facebook post: ' + str(e)[:150])
    for i, hid in rec.get('dc', []):
        if i < len(HOOKS) and not DRY: hook_delete(HOOKS[i], hid)
    state.get('conds', {}).pop(mid, None); state.get('events', {}).pop(mid, None)
    state['queue'] = [q for q in state.get('queue', []) if q.get('mid') != mid]
    notice(f'Post {mid} was deleted in Discord, so it was taken off everywhere it was shared.')

def body_for(p, plain):
    page = SITE + PAGE_URL[p['pages'][0]] if 'web' in p['dest'] else SITE
    return plain + '\n\n— Kentucky Portable Club\n' + page

def subject_for(p):
    first = re.sub(r'\s+', ' ', (p['text'].split('\n')[0] if p['text'] else ''))[:70]
    pre = {'event': 'KPC event: ', 'act': 'KPC activation: '}.get(p['kind'], 'KPC: ')
    return pre + (first or 'Club update')

def sync(m, first):
    """Bring every place in line with this Discord post (first = never shared before)."""
    mid = m['id']; p = parse(m); rec = posts.get(mid, {})
    sig = (m.get('edited_timestamp') or '') + '|' + str(len(m.get('attachments', [])))
    plain = p['text'] + ('\n\n' + '\n'.join(other_files(m)) if other_files(m) else '')
    if not p['text'] and not m.get('attachments'): return
    if DRY:
        notice(f"[dry run] {'new' if first else 'edited'} post {mid}: {p['kind']} -> {sorted(p['dest'])} pages {p['pages']}"
               + (f" refs {p.get('refs')}" if p['kind'] == 'cond' else '') + (f" event {p.get('event')}" if p['kind'] == 'event' else '')
               + ('' if p['list_now'] or 'list' not in p['dest'] else ' (subscribers: Sunday roundup)') + f'\n{plain[:400]}')
        return
    res, problems = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        files = get_photos(m, tmp) if m.get('attachments') else []
        # website
        if 'web' in p['dest']:
            os.makedirs(PHOTOS, exist_ok=True)
            feed_remove(mid)
            urls = []
            for f in files:
                dst = os.path.join(PHOTOS, os.path.basename(f)); shutil.copy(f, dst); urls.append(dst)
            when = rec.get('date') or (NOW if 'sched' in p['flags'] else min(NOW, mtime(mid))).isoformat(timespec='seconds')
            item = {'id': mid, 'date': when, 'pages': p['pages'], 'text': plain, 'photos': urls}
            if not first: item['edited'] = NOW.isoformat(timespec='seconds')
            if pins is not None and mid in pins: item['pinned'] = True
            feed['items'].insert(0, item)
            feed['items'].sort(key=lambda it: it.get('date', ''), reverse=True)
            feed['items'] = feed['items'][:150]
            res['website'] = ', '.join(p['pages'])
        elif rec.get('web'): feed_remove(mid)
        rec['web'] = 'web' in p['dest']; rec['date'] = rec.get('date') or (NOW if 'sched' in p['flags'] else min(NOW, mtime(mid))).isoformat(timespec='seconds')
        # Facebook
        if 'fb' in p['dest'] and FB_ID and FB_TOKEN:
            try:
                if rec.get('fb'): fb_call(rec['fb'], {'message': plain}); res['facebook'] = 'updated'
                else: rec['fb'] = fb_new(plain, files); res['facebook'] = 'posted' + (f' with {len(files)} photo(s)' if files else '')
            except Exception as e: problems.append('Facebook: ' + str(e)[:150])
        elif rec.get('fb') and FB_TOKEN:
            try: fb_call(rec.pop('fb'), {}, method='DELETE'); res['facebook'] = 'removed'
            except Exception as e: problems.append('Facebook delete: ' + str(e)[:150])
        # other Discord server(s)
        hooks_text = plain + ('\n\n' + SITE + PAGE_URL[p['pages'][0]] if 'web' in p['dest'] else '')
        have = dict((i, h) for i, h in rec.get('dc', []))
        if 'dc' in p['dest'] and HOOKS:
            for i, url in enumerate(HOOKS):
                try: have[i] = hook_send(url, hooks_text, files, have.get(i))
                except Exception as e: problems.append('other Discord: ' + str(e)[:150])
            res['other Discord'] = f'{len(HOOKS)} server(s)'
        elif have:
            for i, h in have.items():
                if i < len(HOOKS): hook_delete(HOOKS[i], h)
            have = {}
        rec['dc'] = sorted(have.items())
    # calendar + park warnings
    if p['kind'] == 'event':
        if p.get('event'): state.setdefault('events', {})[mid] = dict(p['event'], id='dc-' + mid, source='MEMBER', member=True); res['calendar'] = p['event']['start']
        else: problems.append('Event: no date found. Put the date on its own line, like "Date: Nov 7 2026".')
    else: state.get('events', {}).pop(mid, None)
    if p['kind'] == 'cond':
        if p.get('refs'):
            seen = mtime(mid).date()
            state.setdefault('conds', {})[mid] = [{'id': f'dc-{mid}-{r}', 'ref': r, 'kind': p['cond_kind'], 'details': p['text'][:400],
                                                   'seen': seen.isoformat(), 'call': '', 'expires': (seen + datetime.timedelta(days=30)).isoformat()} for r in p['refs']]
            res['park warning'] = ', '.join(p['refs'])
        else: problems.append('Conditions: no Kentucky park / KFF / SOTA number found (like US-1277).')
    else: state.get('conds', {}).pop(mid, None)
    # email (only the first time; an edit before it goes out updates the waiting email)
    if first:
        lst_now = p['list_now']
        if ('gio' in p['dest'] and GIO_TO) or lst_now:
            queue_mail(mid, subject_for(p), body_for(p, plain), 'gio' in p['dest'], lst_now, p['now'], 'post ' + mid)
            res['email'] = 'on its way'
        rec['listnow'] = lst_now
    else:
        for q in state.get('queue', []):
            if q.get('mid') == mid and not q['done']: q['subject'], q['body'] = subject_for(p), body_for(p, plain)
    rec['sig'] = sig
    posts[mid] = rec
    if p.get('bad_when'): problems.append("Couldn't read the date/time in the tag, so it went out now.")
    if problems: notice('Problems: ' + '; '.join(problems)); react(mid, '⚠️')
    if first and not problems and not res.get('email'): react(mid, '✅')
    if not first and not problems: react(mid, '✅')
    notice(('Shared' if first else 'Updated') + f' post {mid}: ' + '; '.join(f'{k} {v}' for k, v in res.items()))

done = 0
# 1) deleted / edited posts we already shared
for mid in list(posts):
    if not visible(mid): continue
    m = byid.get(mid)
    if m is None or 'skip' in parse(m)['flags']: unpublish(mid); done += 1   # deleted, or edited to start with Skip:
    elif (m.get('edited_timestamp') or '') + '|' + str(len(m.get('attachments', []))) != posts[mid].get('sig'): sync(m, False); done += 1
# 2) waiting (scheduled) posts: deleted, edited to a new time, or due now
for mid, due in list(sched.items()):
    m = byid.get(mid)
    if m is None and visible(mid): sched.pop(mid); notice(f'Scheduled post {mid} was deleted before its time.'); continue
    if m is None:
        c, r = dc(f'/channels/{CHAN}/messages/{mid}')
        if c == 404: sched.pop(mid); continue
        m = json.loads(r) if c == 200 else None
    if not m: continue
    p = parse(m)
    if p['when'] and p['when'].isoformat() != due: sched[mid] = due = p['when'].isoformat()
    if not p['when'] or datetime.datetime.fromisoformat(due) <= NOW:
        if not DRY: sched.pop(mid); react(mid, '⏰', 'DELETE')
        sync(m, True); done += 1
# 3) new posts
last = int(state.get('last_id') or 0)
for m in window:
    if int(m['id']) <= last: continue
    if not DRY: state['last_id'] = m['id']
    if m.get('author', {}).get('bot') or m.get('type', 0) not in (0, 19): continue
    p = parse(m)
    if 'skip' in p['flags']: notice(f"Post {m['id']} starts with Skip:, so it was not shared."); continue
    if p['due']:
        if DRY: notice(f"[dry run] post {m['id']} waits until {p['due']:%a %b %-d %-I:%M %p} Central"); continue
        sched[m['id']] = p['due'].isoformat(); react(m['id'], '⏰')
        notice(f"Post {m['id']} will go out {p['due']:%a %b %-d at %-I:%M %p} Central."); continue
    sync(m, True); done += 1
# 4) pinned posts stay at the top of their page
if pins is not None:
    for it in feed.get('items', []):
        if it.get('id') in pins: it['pinned'] = True
        else: it.pop('pinned', None)

# 5) Sunday evening roundup for the email-updates list
wk = NOW.strftime('%G-W%V')
if NOW.weekday() == 6 and NOW.hour >= 18 and state.get('roundup') != wk and not DRY:
    state['roundup'] = wk
    since = (NOW - datetime.timedelta(days=7)).isoformat()
    items = [it for it in sorted(feed.get('items', []), key=lambda it: it['date']) if it.get('date', '') >= since and not posts.get(it['id'], {}).get('listnow')]
    if items:
        parts = []
        for it in items:
            d = datetime.datetime.fromisoformat(it['date']).astimezone(CT)
            parts.append(f"■ {d:%a %b %-d}\n{it['text']}" + (f"\n({len(it['photos'])} photo(s) on the website)" if it.get('photos') else ''))
        body = (f"Here's what the Kentucky Portable Club posted this week ({len(items)} update{'s' if len(items) != 1 else ''}).\n\n"
                + '\n\n'.join(parts) + '\n\n— Kentucky Portable Club\n' + SITE + 'news.html')
        queue_mail(None, f"KPC weekly roundup: {NOW:%b %-d, %Y}", body, False, True, False, 'the weekly roundup')
        notice(f'Weekly roundup queued with {len(items)} post(s).')

# 6) email, then save
if DRY:   # practice run: say whether the email-updates sheet can be read (a count only, never addresses)
    notice(('Email-updates list: ' + str(len(subscribers())) + ' subscriber(s) found.') if SUB_CSV else 'Email-updates list: SUBSCRIBE_SHEET_CSV secret not set.')
if not DRY:
    flush_mail()
    # park warnings + calendar items made from Discord (ids start with dc-), merged with the KPC Reports form's own items
    today = NOW.date().isoformat()
    for mid in list(state.get('conds', {})):
        state['conds'][mid] = [c for c in state['conds'][mid] if c['expires'] >= today]
        if not state['conds'][mid]: state['conds'].pop(mid)
    for mid in list(state.get('events', {})):
        e = state['events'][mid]
        if (e.get('end') or e['start']) < today: state['events'].pop(mid)
    dconds = [c for v in state.get('conds', {}).values() for c in v]
    devents = sorted(state.get('events', {}).values(), key=lambda e: (e['start'], e['name']))
    def merge(path, key, mine, sortkey, rev):
        old = load(path, {key: []})
        keep = [x for x in old.get(key, []) if not str(x.get('id', '')).startswith('dc-')]
        new = sorted(keep + mine, key=sortkey, reverse=rev)
        if new != old.get(key, []):
            old[key] = new; old['updated'] = today
            json.dump(old, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    merge('kpc-conditions.json', 'items', dconds, lambda c: (c['seen'], c['id']), True)
    merge('kpc-events-submitted.json', 'events', devents, lambda e: (e['start'], e['name']), False)
    auto = load('kpc-events-auto.json', None)
    if auto is not None:
        found = [e for e in auto.get('found', []) if not str(e.get('id', '')).startswith('dc-')] + devents
        if found != auto.get('found', []):
            auto['found'] = found
            open('kpc-events-auto.json', 'w', encoding='utf-8').write(json.dumps(auto, ensure_ascii=False, indent=1) + '\n')
    # forget old records (keep 120 days so edits/deletes still follow)
    cut = NOW - datetime.timedelta(days=120)
    for mid in list(posts):
        if mtime(mid) < cut: posts.pop(mid)
    state['due'] = min(sched.values()) if sched else ''   # the 1-minute watcher reads this to start the relay on time
    if json.dumps(feed, sort_keys=True) != feed0:
        feed['updated'] = NOW.isoformat(timespec='seconds')
        json.dump(feed, open(OUT, 'w'), indent=1, ensure_ascii=False)
    if json.dumps(state, sort_keys=True) != state0: json.dump(state, open(STATE, 'w'), indent=1)
notice(f'{done} post(s) shared or updated. {len(sched)} waiting for their time. {len(state.get("queue", []))} email(s) waiting.')
