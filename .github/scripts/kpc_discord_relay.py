#!/usr/bin/env python3
"""KPC Discord relay: posts from the private Discord channel -> website + Facebook Page + Groups.io + email subscribers.

Anyone who posts in the channel is shared (bots are skipped). Where it goes on the website comes from words ANYWHERE
in the post: "campout" / "camp out" -> Campout page (and News), "announcement(s)" -> News page. No keyword -> News page.
Website posts carry a date stamp; Facebook posts do not. Links and pictures go everywhere.
A ✅ reaction is added in Discord when a post went out.

Secrets (GitHub -> Settings -> Secrets and variables -> Actions, never in the site or chat):
  DISCORD_BOT_TOKEN, KPC_RELAY_CHANNEL (channel ID), FB_PAGE_ID, FB_PAGE_TOKEN,
  RELAY_SMTP_USER + RELAY_SMTP_PASS (a Gmail address + its App Password), GROUPSIO_TO (the group's post address),
  SUBSCRIBE_SHEET_CSV (published CSV of the email-updates form sheet; optional)
DRY_RUN=1 prints what would happen and changes nothing.
"""
import csv, datetime, io, json, mimetypes, os, re, smtplib, ssl, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from email.message import EmailMessage

TITLE = 'KPC Discord relay'
def notice(m): print('::notice title=' + TITLE + '::' + str(m).replace('%', '%25').replace('\r', '').replace('\n', '%0A'), flush=True)

ENV = lambda k: (os.environ.get(k) or '').strip()
TOKEN, CHAN = ENV('DISCORD_BOT_TOKEN'), ENV('KPC_RELAY_CHANNEL')
FB_ID, FB_TOKEN = ENV('FB_PAGE_ID'), ENV('FB_PAGE_TOKEN')
SMTP_USER, SMTP_PASS, GIO_TO = ENV('RELAY_SMTP_USER'), ENV('RELAY_SMTP_PASS'), ENV('GROUPSIO_TO')
SUB_CSV = ENV('SUBSCRIBE_SHEET_CSV')
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
if not msgs: notice('No new posts.'); sys.exit(0)

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
    t = re.sub(r'^\s*(announcements?|camp ?out)\s*[:\-–]\s*', '', t, flags=re.I)  # a leading "Announcement:" tag
    t = re.sub(r'[ \t]+\n', '\n', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()

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
    when = m['timestamp']
    author = who(m.get('author', {}), m.get('member'))

    files, urls = [], []
    for n, a in enumerate(imgs[:10], 1):
        c, data = http(a['url'])
        if c != 200: continue
        dest = f'{PHOTOS}/{mid}-{n}.jpg'
        try:
            if not DRY: shrink(data, dest)
            files.append(dest); urls.append(dest)
        except Exception as e:
            notice(f'Picture skipped ({e}).')

    page_url = SITE + ('campout.html' if 'campout' in pages else 'news.html')
    plain = text + ('\n\n' + '\n'.join(others) if others else '')
    if DRY:
        notice(f'[dry run] {author} -> pages {pages}, {len(files)} picture(s)\n{plain[:600]}'); continue

    feed['items'] = [it for it in feed.get('items', []) if it.get('id') != mid]
    feed['items'].insert(0, {'id': mid, 'date': when, 'pages': pages, 'author': author, 'text': plain, 'photos': urls})
    feed['items'] = feed['items'][:150]

    res = {}
    try: res['facebook'] = fb_post(plain, files)
    except Exception as e: res['facebook'] = 'FAILED: ' + str(e)[:200]
    subject = 'KPC: ' + (re.sub(r'\s+', ' ', text.split('\n')[0])[:70] or 'Club update')
    body = plain + f'\n\n— Kentucky Portable Club\n{page_url}'
    if GIO_TO:
        try: res['groups.io'] = mail(GIO_TO, [], subject, body, files)
        except Exception as e: res['groups.io'] = 'FAILED: ' + str(e)[:200]
    if subs is None: subs = subscribers()
    if subs:
        try:
            for i in range(0, len(subs), 80):   # Gmail limit per message
                mail(SMTP_USER, subs[i:i + 80], subject, body + '\n\nUnsubscribe: use the UNSUBSCRIBE button on ' + SITE + 'news.html', files)
            res['email list'] = f'sent to {len(subs)}'
        except Exception as e: res['email list'] = 'FAILED: ' + str(e)[:200]
    ok = not any(str(v).startswith('FAILED') for v in res.values())
    dc(f'/channels/{CHAN}/messages/{mid}/reactions/{urllib.parse.quote("✅" if ok else "⚠️")}/@me', 'PUT')
    notice(f'Shared {author}\'s post ({", ".join(pages)} page): ' + '; '.join(f'{k} {v}' for k, v in res.items()))
    state['last_id'] = mid; done += 1

if not DRY:
    feed['updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    json.dump(feed, open(OUT, 'w'), indent=1, ensure_ascii=False)
    json.dump(state, open(STATE, 'w'), indent=1)
notice(f'{done} post(s) shared.')
