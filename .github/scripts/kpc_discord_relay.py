#!/usr/bin/env python3
"""KPC Discord relay: posts from the private Discord channel -> website + Facebook Page + Groups.io + email subscribers.

Anyone who posts in the channel is shared (bots are skipped). Where it goes on the website comes from words ANYWHERE
in the post: "campout" / "camp out" -> Campout page (and News), "announcement(s)" -> News page. No keyword -> News page.
WHERE it goes = a tag at the start ("Email:", "Facebook:", "Website:", "Facebook + Email:", "All:"); none = website + Facebook (see where_to).
Website posts carry a date stamp; Facebook posts do not. Links and pictures go everywhere.
Poster names are NOT shown anywhere (Brandon Oct 15). A ✅ reaction is added in Discord when a post went out.

Secrets (GitHub -> Settings -> Secrets and variables -> Actions, never in the site or chat):
  DISCORD_BOT_TOKEN, KPC_RELAY_CHANNEL (channel ID), FB_PAGE_ID, FB_PAGE_TOKEN,
  RELAY_SMTP_PASS (App Password of kypotacampout@gmail.com (the campout email), the sender; RELAY_SMTP_USER overrides the address), GROUPSIO_TO (the group's post address),
  SUBSCRIBE_SHEET_CSV (published CSV of the email-updates form sheet; optional)
  Email can instead go through an Apps Script web app in kpcwebhost@gmail.com (Brandon Oct 15): RELAY_MAIL_URL + RELAY_MAIL_KEY (used when set; mail comes FROM that account)
DRY_RUN=1 prints what would happen and changes nothing.
"""
import csv, datetime, hashlib, hmac, io, tempfile, json, mimetypes, os, re, smtplib, ssl, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from email.message import EmailMessage

TITLE = 'KPC Discord relay'
def notice(m): print('::notice title=' + TITLE + '::' + str(m).replace('%', '%25').replace('\r', '').replace('\n', '%0A'), flush=True)

ENV = lambda k: (os.environ.get(k) or '').strip()
TOKEN, CHAN = ENV('DISCORD_BOT_TOKEN'), ENV('KPC_RELAY_CHANNEL')
FB_ID, FB_TOKEN = ENV('FB_PAGE_ID'), ENV('FB_PAGE_TOKEN')
SMTP_USER, SMTP_PASS, GIO_TO = (ENV('RELAY_SMTP_USER') or 'kypotacampout@gmail.com'), ENV('RELAY_SMTP_PASS'), ENV('GROUPSIO_TO')
SUB_CSV = ENV('SUBSCRIBE_SHEET_CSV')
MAIL_URL, MAIL_KEY = ENV('RELAY_MAIL_URL'), ENV('RELAY_MAIL_KEY')   # Google Apps Script mailer in the campout account (no App Password needed)
DRY = ENV('DRY_RUN').lower() in ('1', 'true', 'yes')
SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
STATE, OUT, PHOTOS = 'kpc-relay-state.json', 'kpc-announcements.json', 'photos/announce'
API = 'https://discord.com/api/v10'
UA = 'KPC-Relay (https://kentuckyportableclub.github.io/KPC-Links/, 1.0)'

if not TOKEN or not CHAN:
    notice('No DISCORD_BOT_TOKEN / KPC_RELAY_CHANNEL secret yet; nothing to do.'); sys.exit(0)

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

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

state = load(STATE, {})
state0 = json.dumps(state, sort_keys=True)
feed = load(OUT, {'items': []})

# ---------------------------------------------------------------- read the channel
after = state.get('last_id')
code, raw = dc(f'/channels/{CHAN}/messages?limit=50' + (f'&after={after}' if after else ''))
if code != 200:
    notice(f'Discord said HTTP {code}: {raw[:200]!r}. Check the bot is in the server, can see the channel, and has Read Message History.')
    sys.exit(1)
msgs = sorted(json.loads(raw), key=lambda m: int(m['id']))
if not after:
    # First run: remember where the channel is now, post nothing old.
    if not DRY:
        state['last_id'] = msgs[-1]['id'] if msgs else '0'; json.dump(state, open(STATE, 'w'), indent=1)
    notice(f'First run: saved the starting point ({len(msgs)} older messages left alone). New posts from now on will be shared.')
    sys.exit(0)
if not msgs: notice('No new posts.')

# ---------------------------------------------------------------- helpers
def who(u, member=None):
    return ((member or {}).get('nick') or u.get('global_name') or u.get('username') or '').strip()

def clean(m):
    t = m.get('content') or ''
    names = {u['id']: who(u, u.get('member')) for u in m.get('mentions', [])}
    t = re.sub(r'<@!?(\d+)>', lambda x: names.get(x.group(1), ''), t)
    t = re.sub(r'<@&\d+>|<#\d+>|@everyone|@here', '', t)
    t = re.sub(r'<a?:(\w+):\d+>', r':\1:', t)               # custom emoji -> :name:
    t = re.sub(r'<(https?://[^>\s]+)>', r'\1', t)            # <link> (no preview) -> link
    t = re.sub(r'\*\*|__|~~|\|\||`{1,3}', '', t)            # Discord markdown marks
    t = TAG.sub('', t, count=1)                              # leading "Email + Facebook:" / "Announcement:" tag
    t = re.sub(r'[ \t]+\n', '\n', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()

# Where a post goes = the words at the very START of the post, before a colon (Brandon Oct 15):
#   "Email:" (Groups.io + email list)  "Groups.io:"  "Subscribers:"  "Facebook:"  "Website:"  "Facebook + Email:"  "All:"  ("only" / "and" / + & , / are fine).
#   The tag lists exactly where it goes; "All:" = website + Facebook + email. No tag = website + Facebook.
#   Email (Groups.io + the email-updates list) ONLY when the tag says email or all.
#   "Campout" / "Announcement" can sit in the tag too ("Campout email:"); they still work anywhere in the post.
TAGW = r'(?:groups?[ .]?io|groups?|subscribers?|e-?mail|facebook|fb|website|web ?site|web|site|all|everything|everywhere|camp ?-?out|announcements?|only|and|\+|&|,|/)'
TAG = re.compile(r'^\s*(' + TAGW + r'(?:\s*' + TAGW + r')*)\s*[:\-–]\s*', re.I)

def where_to(raw):
    """web, fb, gio (Groups.io), list (email-updates subscribers). 'Email' = gio + list."""
    m = TAG.match(raw or '')
    w = (m.group(1).lower() if m else '')
    if re.search(r'\b(all|everything|everywhere)\b', w): return {'web', 'fb', 'gio', 'list'}
    d = set()
    if re.search(r'e-?mail', w): d |= {'gio', 'list'}
    if re.search(r'groups?', w): d.add('gio')
    if re.search(r'subscriber', w): d.add('list')
    if re.search(r'facebook|\bfb\b', w): d.add('fb')
    if re.search(r'web|site', w): d.add('web')
    return d or {'web', 'fb'}

def pages_for(text):
    low = text.lower()
    p = []
    if re.search(r'camp\s?-?out', low): p += ['campout', 'news']
    if re.search(r'announcement', low) and 'news' not in p: p.append('news')
    return p or ['news']

def shrink(data, dest):
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(data)); im = ImageOps.exif_transpose(im)
    if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
    im.thumbnail((1280, 1280))
    im.save(dest, 'JPEG', quality=85, optimize=True)        # new file: no EXIF / GPS

def fb_post(text, files):
    if not FB_ID or not FB_TOKEN: return 'skipped (no Facebook secrets)'
    base = f'https://graph.facebook.com/v19.0/{FB_ID}'
    def form(url, fields, file=None):
        b = uuid.uuid4().hex; parts = []
        for k, v in fields.items(): parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        if file:
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="source"; filename="photo.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + open(file, 'rb').read() + b'\r\n')
        parts.append(f'--{b}--\r\n'.encode())
        c, r = http(url, b''.join(parts), {'Content-Type': 'multipart/form-data; boundary=' + b}, 'POST')
        j = json.loads(r or b'{}') if r else {}
        if c != 200 or 'error' in j: raise RuntimeError((j.get('error') or {}).get('message') or f'HTTP {c}')
        return j
    if len(files) == 1:
        form(base + '/photos', {'access_token': FB_TOKEN, 'caption': text}, files[0]); return 'posted with photo'
    fields = {'access_token': FB_TOKEN, 'message': text}
    for i, f in enumerate(files[:10]):
        j = form(base + '/photos', {'access_token': FB_TOKEN, 'published': 'false'}, f)
        fields[f'attached_media[{i}]'] = json.dumps({'media_fbid': j['id']})
    form(base + '/feed', fields); return 'posted' + (f' with {len(files)} photos' if files else '')

def mail(to, bcc, subject, text, files):
    if MAIL_URL and MAIL_KEY:
        # The campout Gmail sends it through its own Apps Script web app (.claude/build/relay/kpc-mailer.gs)
        import base64
        body = json.dumps({'key': MAIL_KEY, 'to': to, 'bcc': bcc, 'subject': subject, 'body': text,
                           'images': [{'name': os.path.basename(f), 'b64': base64.b64encode(open(f, 'rb').read()).decode()} for f in files]}).encode()
        c, r = http(MAIL_URL, body, {'Content-Type': 'application/json'}, 'POST', timeout=90)
        t = (r or b'').decode('utf8', 'replace')
        if c != 200 or '"ok":true' not in t.replace(' ', ''): raise RuntimeError(f'mailer said HTTP {c}: {t[:150]}')
        return 'sent'
    if not SMTP_USER or not SMTP_PASS: return 'skipped (no email secrets)'
    em = EmailMessage(); em['From'] = f'Kentucky Portable Club <{SMTP_USER}>'; em['To'] = to or SMTP_USER
    em['Subject'] = subject
    if bcc: em['Bcc'] = ', '.join(bcc)
    em.set_content(text)
    for f in files:
        em.add_attachment(open(f, 'rb').read(), maintype='image', subtype='jpeg', filename=os.path.basename(f))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context(), timeout=60) as s:
        s.login(SMTP_USER, SMTP_PASS); s.send_message(em)
    return 'sent'

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

# ---------------------------------------------------------------- Gmail daily limit
# A personal Gmail Apps Script may email about 100 people per rolling 24 hours (every To/Bcc address counts;
# Groups.io counts as ONE because Groups.io sends to its members itself). We stay under CAP, remember what went
# out in kpc-relay-state.json ("sent"), and leave the rest in "queue" for the next runs (every 15 min).
# Email addresses are never saved: only a keyed fingerprint (HMAC with the mail key) of who already got it.
CAP = int(ENV('RELAY_DAILY_CAP') or 90)
def react(mid, emo, how='PUT'):
    dc(f'/channels/{CHAN}/messages/{mid}/reactions/{urllib.parse.quote(emo)}/@me', how)
def fp(e): return hmac.new((MAIL_KEY or TOKEN).encode(), e.encode(), hashlib.sha256).hexdigest()[:20]
def room():
    now = time.time()
    state['sent'] = [x for x in state.get('sent', []) if now - x[0] < 86400 + 600]
    return CAP - sum(x[1] for x in state['sent'])
def spent(n): state.setdefault('sent', []).append([int(time.time()), n])
def photos_of(mid, tmp):
    c, r = dc(f'/channels/{CHAN}/messages/{mid}')
    if c != 200: return []
    out = []
    for n, a in enumerate([a for a in json.loads(r).get('attachments', []) if (a.get('content_type') or '').startswith('image/')][:10], 1):
        c2, data = http(a['url'])
        if c2 != 200: continue
        try: f = os.path.join(tmp, f'{mid}-{n}.jpg'); shrink(data, f); out.append(f)
        except Exception: pass
    return out
def unsub_line():
    """One-tap unsubscribe: the email-updates form with 'Unsubscribe' already picked."""
    f = load('kpc-subscribe-form.json', {})
    if re.match(r'https://docs\.google\.com/forms/', f.get('url') or '') and f.get('choiceEntry'):
        u = f['url'] + ('&' if '?' in f['url'] else '?') + 'usp=pp_url&' + urllib.parse.urlencode({f['choiceEntry']: f.get('unsubscribe') or 'Unsubscribe'})
        return 'To stop these emails, tap here and press Submit: ' + u
    return 'To stop these emails, use the UNSUBSCRIBE button on ' + SITE + 'news.html'

def flush_mail():
    q = state.get('queue') or []
    if not q: return
    if not (MAIL_URL and MAIL_KEY) and not SMTP_PASS:
        notice(f'{len(q)} email post(s) waiting: email secrets are not set yet.'); return
    subs = None
    with tempfile.TemporaryDirectory() as tmp:
        for it in list(q):
            files = photos_of(it['mid'], tmp)
            bad = []
            if it.get('gio'):
                if room() < 1: break
                try: mail(GIO_TO, [], it['subject'], it['body'], files); spent(1); it['gio'] = False
                except Exception as e:
                    bad.append('groups.io: ' + str(e)[:150])
                    if re.search(r'too many|quota|limit', str(e), re.I): break
            if it.get('list'):
                if subs is None: subs = subscribers()
                todo = [e for e in subs if fp(e) not in it['done']]
                while todo:
                    n = min(80, room() - 1)              # -1: the account's own To: address counts too
                    if n < 1: break
                    part = todo[:n]
                    try:
                        mail('' if MAIL_URL else SMTP_USER, part, it['subject'],
                             it['body'] + '\n\n' + unsub_line(), files)
                    except Exception as e:
                        bad.append('email list: ' + str(e)[:150]); break
                    spent(len(part) + 1); it['done'] += [fp(e) for e in part]; todo = todo[n:]
                if not todo: it['list'] = False
            if bad:
                notice('Email problem: ' + '; '.join(bad)); react(it['mid'], '⚠️')
                it['tries'] = it.get('tries', 0) + 1
                if it['tries'] >= 8:                       # give up after ~2 hours of failures
                    q.remove(it); notice('Gave up on emailing post ' + it['mid']); continue
            if not it.get('gio') and not it.get('list'):
                q.remove(it); react(it['mid'], '⏳', 'DELETE'); react(it['mid'], '✅')
                notice(f'Emailed post {it["mid"]} ({len(it["done"])} subscriber(s)).')
            else:
                react(it['mid'], '⏳')
                notice(f'Post {it["mid"]}: Gmail daily limit reached; the rest goes out in the next runs.'); break
    state['queue'] = q

# ---------------------------------------------------------------- go
os.makedirs(PHOTOS, exist_ok=True)
subs = None
done = 0
for m in msgs:
    mid = m['id']
    if m.get('author', {}).get('bot') or m.get('type', 0) not in (0, 19):
        state['last_id'] = mid; continue
    text = clean(m)
    imgs = [a for a in m.get('attachments', []) if (a.get('content_type') or '').startswith('image/')]
    others = [a['url'] for a in m.get('attachments', []) if a not in imgs]
    if not text and not imgs:
        state['last_id'] = mid; continue
    pages = pages_for(m.get('content') or '')
    dest = where_to(m.get('content') or '')
    when = m['timestamp']
    author = who(m.get('author', {}), m.get('member'))

    files, urls = [], []
    for n, a in enumerate(imgs[:10], 1):
        c, data = http(a['url'])
        if c != 200: continue
        fp = f'{PHOTOS}/{mid}-{n}.jpg'
        try:
            if not DRY: shrink(data, fp)
            files.append(fp); urls.append(fp)
        except Exception as e:
            notice(f'Picture skipped ({e}).')

    page_url = SITE + ('campout.html' if 'campout' in pages else 'news.html')
    plain = text + ('\n\n' + '\n'.join(others) if others else '')
    if DRY:
        notice(f'[dry run] {author} -> {sorted(dest)} pages {pages}, {len(files)} picture(s)\n{plain[:600]}'); continue

    res = {}
    if 'web' in dest:
      feed['items'] = [it for it in feed.get('items', []) if it.get('id') != mid]
      feed['items'].insert(0, {'id': mid, 'date': when, 'pages': pages, 'text': plain, 'photos': urls})
      feed['items'] = feed['items'][:150]
      res['website'] = ', '.join(pages) + ' page'
    if 'fb' in dest:
      try: res['facebook'] = fb_post(plain, files)
      except Exception as e: res['facebook'] = 'FAILED: ' + str(e)[:200]
    subject = 'KPC: ' + (re.sub(r'\s+', ' ', text.split('\n')[0])[:70] or 'Club update')
    body = plain + '\n\n— Kentucky Portable Club' + (f'\n{page_url}' if 'web' in dest else '\n' + SITE)
    if ('gio' in dest and GIO_TO) or 'list' in dest:
        # Email waits in a queue so we never go over Gmail's daily limit (sent by flush_mail() below)
        state.setdefault('queue', []).append({'mid': mid, 'subject': subject, 'body': body,
            'gio': bool('gio' in dest and GIO_TO), 'list': 'list' in dest, 'done': []})
        res['email'] = 'queued'
    for f in ([] if 'web' in dest else files):  # pictures only needed for Facebook: keep them off the site
        try: os.remove(f)
        except OSError: pass
    ok = not any(str(v).startswith('FAILED') for v in res.values())
    if not ok: react(mid, '⚠️')
    elif 'email' not in res: react(mid, '✅')
    notice(f'Shared {author}\'s post: ' + '; '.join(f'{k} {v}' for k, v in res.items()))
    state['last_id'] = mid; done += 1

if not DRY:
    flush_mail()
    if done:
        feed['updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        json.dump(feed, open(OUT, 'w'), indent=1, ensure_ascii=False)
    if json.dumps(state, sort_keys=True) != state0: json.dump(state, open(STATE, 'w'), indent=1)
notice(f'{done} post(s) shared.')
