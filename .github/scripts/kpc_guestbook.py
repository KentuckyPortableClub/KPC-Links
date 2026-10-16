"""Guestbook: copies the 'KPC Guestbook' form answers into kpc-guestbook.json.
Needs the GitHub secret KPC_GUESTBOOK_CSV (the answer sheet's "Publish to web" CSV link).

A signature shows when Approved says YES, or when Approved is EMPTY and the name, town and message have no links,
emails, phone numbers, swear words or shouting. Anything else waits for a YES; NO always hides it.
Only name, state, town, ham/not and the message are published. 'How did you find us' and 'What did you like'
are only published as totals (counts), never per person."""
import os, sys, hashlib, datetime
sys.path.insert(0, os.path.dirname(__file__))
import kpc_formtools as T

URL = os.environ.get('KPC_GUESTBOOK_CSV', '').strip()
OUT = 'kpc-guestbook.json'
N = lambda m: T.notice('Guestbook', m)
if not URL: N('KPC_GUESTBOOK_CSV secret not set yet; nothing to do.'); sys.exit(0)
H, rows = T.sheet(URL)
c = lambda name: T.col(H, name)
C = dict(ts=c('Timestamp'), name=c('Call sign or first name'), st=c('Where are you from?'), town=c('Town'),
         ham=c('Are you a ham?'), found=c('How did you find us?'), like=c('What did you like?'), msg=c('Your message'), app=c('Approved'))
if C['name'] is None: N('The sheet has no "Call sign or first name" column; is this the right CSV link?'); sys.exit(0)
out, waiting, states, found, liked = [], 0, {}, {}, {}
for r in rows:
    g = lambda k: T.cell(r, C[k])
    ap = T.approval(g('app'))
    if ap == 'no': continue
    name, town, msg = g('name')[:30], g('town')[:30], g('msg')[:300]
    if not name: continue
    if ap != 'yes' and (T.clean(name) or T.clean(town) or T.clean(msg)): waiting += 1; continue
    d = T.sheet_date(g('ts')) or datetime.date.today()
    ham = g('ham')
    e = {'id': hashlib.sha1((g('ts') + name).encode()).hexdigest()[:12], 'name': name, 'state': g('st'), 'town': town,
         'ham': 'yes' if ham.lower().startswith('licensed') else 'study' if 'stud' in ham.lower() else 'no' if ham else '',
         'msg': msg, 'date': d.isoformat()}
    out.append(e)
    if e['state']: states[e['state']] = states.get(e['state'], 0) + 1
    for v in [x.strip() for x in g('found').split(',') if x.strip()]: found[v] = found.get(v, 0) + 1
    for v in [x.strip() for x in g('like').split(',') if x.strip()]: liked[v] = liked.get(v, 0) + 1
out.sort(key=lambda e: (e['date'], e['id']), reverse=True)
T.write_if_changed(OUT, {'updated': datetime.date.today().isoformat(), 'entries': out, 'states': states, 'found': found, 'liked': liked}, 'entries')
N(f'{len(out)} signature(s) shown from {len(states)} place(s); {waiting} waiting for YES in the Approved column.')
