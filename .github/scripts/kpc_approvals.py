"""Daily 'waiting for your approval' email for Brandon (4 PM Central, kpc-approvals.yml).
Reads every club Google Form sheet (the same CSV secrets the sync jobs use), finds rows with an EMPTY Approved cell
that the website is NOT showing on its own, and emails one list: which form, date, call sign, the first words, and why
it is waiting. Nothing waiting = no email. The list only goes by email (never into the public repo or a GitHub issue).
Email goes through the club mailer (RELAY_MAIL_URL + RELAY_MAIL_KEY) to secret APPROVAL_EMAIL
(empty = the mailer's own Gmail inbox, kpcwebhost)."""
import os, re, sys, json, datetime, urllib.request, zoneinfo
sys.path.insert(0, os.path.dirname(__file__))
import kpc_formtools as T, kpc_preapproved as PA

N = lambda m: T.notice('Approvals', m)
CT = zoneinfo.ZoneInfo('America/Chicago')
NOW = datetime.datetime.now(CT)
if os.environ.get('FORCE', '').lower() not in ('true', '1', 'yes') and NOW.hour != 16:
    N(f'Not 4 PM in Kentucky yet ({NOW:%H:%M} Central); nothing sent.'); sys.exit(0)
PRE = PA.load()
TODAY = NOW.date()

def first(t, n=90):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return (t[:n] + '…') if len(t) > n else t

def text_reasons(texts):
    out = []
    for t in texts:
        r = T.clean(t)
        if r and r not in out: out.append(r)
    return out

def call_reason(call):
    if T.base(call) in PRE: return None
    ok = T.real_call(call)
    if ok is True: return ''
    return 'call sign not found in the license lists' if ok is False else "the license lookup didn't answer"

def rows_of(env):
    url = os.environ.get(env, '').strip()
    if not url: return None, None
    try: return T.sheet(url)
    except Exception as e: N(f'{env}: could not read the sheet ({e})'); return None, None

def generic(H, r, skip):
    return [T.cell(r, i) for i in range(len(H)) if H[i].lower().split(' (')[0].strip() not in skip and i < len(r)]

SECTIONS = []

def check(title, sheet, env, rowfn):
    H, rows = rows_of(env)
    if H is None: return
    app = T.col(H, 'Approved')
    items = []
    for r in rows:
        if app is not None and T.approval(T.cell(r, app)) in ('yes', 'no'): continue
        if app is not None and T.cell(r, app).strip().upper() in ('DONE', 'FIXED'): continue
        res = rowfn(H, r)
        if res: items.append(res)
    if items: SECTIONS.append((title, sheet, items))

def ts_date(H, r):
    d = T.sheet_date(T.cell(r, T.col(H, 'Timestamp')))
    return d.strftime('%b %-d') if d else ''

def photo_of(H, r, *names):
    for n in names:
        i = T.col(H, n)
        if i is not None and T.cell(r, i): return True
    return False

SKIP = {'timestamp', 'call sign', 'approved', 'photo', 'photos', 'gps', 'call sign or first name'}

# ---------------------------------------------------------------- Park Notes
def notes(H, r):
    call = T.cell(r, T.col(H, 'Call sign'))
    why = []
    if T.base(call) in PRE: return None
    if photo_of(H, r, 'Photo'): why.append('has a photo')
    cr = call_reason(call)
    if cr: why.append(cr)
    why += text_reasons(generic(H, r, SKIP))
    return why and (ts_date(H, r), call, first(T.cell(r, T.col(H, 'Your tip'))), why)
check('Park Notes tips', 'KPC Park Tips (responses)', 'NOTES_SHEET_CSV', notes)

# ---------------------------------------------------------------- Community
def community(H, r):
    call = T.cell(r, T.col(H, 'Call sign')); kind = T.cell(r, T.col(H, 'What are you sharing'))
    if T.base(call) in PRE or not kind: return None
    why = []
    if kind.lower().startswith('elmer'): why.append('Elmer listing (always checked by hand)')
    if photo_of(H, r, 'Photos'): why.append('has a photo')
    cr = call_reason(call)
    if cr: why.append(cr)
    why += text_reasons(generic(H, r, SKIP))
    words = ' '.join(x for x in generic(H, r, SKIP | {'what are you sharing'}) if x)
    return why and (ts_date(H, r), call, kind.split('(')[0].strip() + ': ' + first(words, 70), why)
check('Community posts', 'KPC Community (responses)', 'COMMUNITY_SHEET_CSV', community)

# ---------------------------------------------------------------- Campground reviews
def camp(H, r):
    call = T.cell(r, T.col(H, 'Call sign'))
    if T.base(call) in PRE: return None
    why = []
    if photo_of(H, r, 'Photo'): why.append('has a photo')
    cr = call_reason(call)
    if cr: why.append(cr)
    why += text_reasons(generic(H, r, SKIP))
    place = T.cell(r, T.col(H, 'Campground or cabin')) or T.cell(r, T.col(H, 'Campground name'))
    return why and (ts_date(H, r), call, first(place + ': ' + T.cell(r, T.col(H, 'Your review')), 80), why)
check('Campground reviews', 'KPC Campground Reviews (responses)', 'CAMPGROUND_SHEET_CSV', camp)

# ---------------------------------------------------------------- KPC Reports
def reports(H, r):
    call = T.cell(r, T.col(H, 'Call sign')); kind = T.cell(r, T.col(H, 'What are you sending')).lower()
    if not kind or 'problem' in kind: return None                     # website problems live in their own GitHub issue
    if 'comment' in kind and not T.cell(r, T.col(H, 'Show it on the website')).lower().startswith('y'): return None
    if 'photo' in kind:
        ok = T.cell(r, T.col(H, 'OK to use')).lower()
        if not ok or ok.startswith('no'): return None                 # not ticked: never used, nothing to approve
        if T.base(call) in PRE: return None
        return (ts_date(H, r), call, 'Photo: ' + first(T.cell(r, T.col(H, 'Caption')), 70), ['has a photo (photos are always checked by hand)'])
    if 'event' in kind:
        d = T.sheet_date(T.cell(r, T.col(H, 'Event date')))
        if not d or d < TODAY: return None
    if 'condition' in kind:
        d = T.sheet_date(T.cell(r, T.col(H, 'Date you saw it'))) or T.sheet_date(T.cell(r, T.col(H, 'Timestamp')))
        if d and (TODAY - d).days > 30: return None
    if T.base(call) in PRE: return None
    why = []
    cr = call_reason(call)
    if cr: why.append(cr)
    why += text_reasons(generic(H, r, SKIP | {'ok to use on the website', 'show it on the website', 'date you saw it', 'event date', 'start time'}))
    what = T.cell(r, T.col(H, 'Details')) or T.cell(r, T.col(H, 'Your comment')) or T.cell(r, T.col(H, 'Event name'))
    return why and (ts_date(H, r), call, kind.capitalize() + ': ' + first(what, 70), why)
check('KPC Reports', 'KPC Reports (responses)', 'KPC_REPORTS_CSV', reports)

# ---------------------------------------------------------------- Activation Board
def acts(H, r):
    call = T.cell(r, T.col(H, 'Call sign')); kind = T.cell(r, T.col(H, 'What are you posting?')).lower()
    req = 'hunter' in kind or 'request' in kind
    refs = T.split_refs(T.cell(r, T.col(H, "Park(s) you need" if req else 'Park, summit or reference number(s)')))
    if not refs: return None
    posted = T.sheet_date(T.cell(r, T.col(H, 'Timestamp'))) or TODAY
    d = None
    if req:
        if (TODAY - posted).days > 30: return None
    else:
        d = T.sheet_date(T.cell(r, T.col(H, 'Date')))
        if not d or d < TODAY: return None
    why = []
    if T.base(call) not in PRE:
        cr = call_reason(call)
        if cr: why.append(cr)
    bad = [x for x in refs if not T.ref_name(x)]
    if bad: why.append('number not found: ' + ', '.join(bad))
    if d and d > TODAY + datetime.timedelta(days=60): why.append('more than 60 days away')
    why += text_reasons([T.cell(r, T.col(H, 'Notes (request)' if req else 'Notes'))])
    if not why: return None                                           # (the 3-a-day limit is rare; the board job reports it)
    return (ts_date(H, r), call, ('Park request: ' if req else f'Activation {d:%b %-d}: ') + ', '.join(refs), why)
check('Activation Board', 'KPC Activations & Park Requests (responses)', 'KPC_ACTIVATIONS_CSV', acts)

# ---------------------------------------------------------------- Guestbook
def guest(H, r):
    name = T.cell(r, T.col(H, 'Call sign or first name'))
    if not name: return None
    why = text_reasons([name, T.cell(r, T.col(H, 'Town')), T.cell(r, T.col(H, 'Your message'))])
    return why and (ts_date(H, r), name, first(T.cell(r, T.col(H, 'Your message')) or '(no message)'), why)
check('Guestbook', 'KPC Guestbook (responses)', 'KPC_GUESTBOOK_CSV', guest)

# ---------------------------------------------------------------- CW Leaderboard
def cw(H, r):
    call = T.cell(r, T.col(H, 'Call sign')); wk = T.cell(r, T.col(H, 'Week')).upper()
    wkid = lambda d: '%d-W%02d' % d.isocalendar()[:2]
    if wk not in {wkid(TODAY - datetime.timedelta(weeks=i)) for i in range(8)}: return None
    kind = 'gauntlet' if 'gauntlet' in T.cell(r, T.col(H, 'Which challenge?')).lower() else 'copy'
    why = []
    if T.base(call) not in PRE:
        cr = call_reason(call)
        if cr: why.append(cr)
    try: pts, wpm = int(float(T.cell(r, T.col(H, 'Points')))), int(float(T.cell(r, T.col(H, 'Top WPM'))))
    except ValueError: return None
    sent = T.sheet_date(T.cell(r, T.col(H, 'Timestamp'))) or TODAY
    if wk not in (wkid(sent), wkid(sent - datetime.timedelta(weeks=1))): why.append('sent for an old week')
    okn = (0 <= pts <= 3000 and 0 <= wpm <= 5) if kind == 'gauntlet' else (0 <= pts <= 20000 and 5 <= wpm <= 70)
    if not okn: why.append('the score numbers look too high')
    return why and (ts_date(H, r), call, f"{'Gauntlet' if kind == 'gauntlet' else 'Copy challenge'} {wk}: {pts} points", why)
check('CW Leaderboard', 'KPC CW Challenge Leaderboard (responses)', 'KPC_CWBOARD_CSV', cw)

T.save_cache()
total = sum(len(s[2]) for s in SECTIONS)
if not total: N('Nothing is waiting for approval. No email sent.'); sys.exit(0)

lines = [f"{total} post{'s' if total != 1 else ''} waiting for your YES or NO ({NOW:%a %b %-d}, 4 PM).", '']
for title, sheet, items in SECTIONS:
    lines += [f'■ {title.upper()} ({len(items)})  —  sheet: "{sheet}"']
    for d, who, what, why in items:
        lines.append(f'   • {d} · {who or "(no call)"} · {what}')
        lines.append(f'       waiting because: {"; ".join(why)}')
    lines.append('')
lines += ['HOW TO APPROVE: open the sheet (Google Drive → search the sheet name), find the row, and pick YES or NO in the Approved column.',
          'YES shows it on the website within about 20 minutes to 2 hours. NO keeps it off for good. Either one takes it off this list.',
          '', 'This list only comes by email, and only on days something is waiting.', '— KPC website robot']
body = '\n'.join(lines)

# Discord too (Brandon Oct 21: 'can discord also notify us if someone needs something from us?'). Same list,
# in the room he is already in. Names and what people wrote stay out of the public repo either way.
def to_discord():
    # a staff room if there is one (KPC_ADMIN_WEBHOOK), otherwise the usual bot room
    hook = (os.environ.get('KPC_ADMIN_WEBHOOK') or os.environ.get('KPC_DISCORD_WEBHOOK') or '').strip()
    if not hook.startswith('https://'):
        N('No Discord webhook set; nothing sent to Discord.'); return
    L = [f"**{total} post{'s' if total != 1 else ''} waiting for a YES or NO.**", '']
    for title, sheet, items in SECTIONS:
        L.append(f'**{title}** ({len(items)})')
        for d, who, what, why in items[:6]:
            L.append(f'• {d} · {who or "(no call)"} · {what}')
        if len(items) > 6:
            L.append(f'• …and {len(items) - 6} more')
        L.append('')
    L.append('Open the form\'s sheet in Google Drive, find the row and pick YES or NO in the Approved column. '
             'YES puts it on the website within a couple of hours.')
    d = json.dumps({'username': 'KPC', 'allowed_mentions': {'parse': []},
                    'embeds': [{'title': 'Somebody is waiting on us', 'color': 0xd5a63a,
                                'description': '\n'.join(L)[:4000]}]}).encode()
    try:
        rq = urllib.request.Request(hook, d, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(rq, timeout=60) as f: f.read()
        N('Posted the waiting list to Discord.')
    except Exception as e:  # noqa: BLE001
        N(f'Discord failed: {str(e)[:160]}')

if os.environ.get('DRY', '').lower() not in ('true', '1', 'yes'):
    to_discord()

url, key = os.environ.get('RELAY_MAIL_URL', ''), os.environ.get('RELAY_MAIL_KEY', '')
if os.environ.get('DRY', '').lower() in ('true', '1', 'yes') or not (url and key):
    N(f'{total} post(s) waiting' + ('' if url and key else ' (mailer secrets missing, so no email)') + '. Practice run: email not sent.')
    print(body if os.environ.get('SHOW') else '(list not printed in the public log)')
    sys.exit(0)
req = urllib.request.Request(url, json.dumps({'key': key, 'to': os.environ.get('APPROVAL_EMAIL', '').strip(), 'bcc': [],
                             'subject': f'KPC: {total} post{"s" if total != 1 else ""} waiting for approval', 'body': body, 'images': []}).encode(),
                             headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=90) as f: t = f.read().decode('utf8', 'replace')
    ok = '"ok":true' in t.replace(' ', '')
except Exception as e: ok, t = False, str(e)
N(f'Approval email {"sent" if ok else "FAILED: " + t[:150]} ({total} waiting)' + ('' if os.environ.get('APPROVAL_EMAIL') else ' to the club mailer inbox (APPROVAL_EMAIL not set)') + '.')
