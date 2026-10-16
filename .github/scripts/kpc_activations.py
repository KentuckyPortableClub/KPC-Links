"""Activation Board: copies the 'KPC Activations & Park Requests' form answers into kpc-activations.json.
Needs the GitHub secret KPC_ACTIVATIONS_CSV (the answer sheet's "Publish to web" CSV link).

A row shows on the website when the Approved cell says YES, or when Approved is EMPTY and it looks safe:
  * the call sign is a club member / pre-approved call, or a real licensed call (callook.info, HamDB)
  * every park / summit / reference number really exists (POTA, SOTA, WWFF)
  * activations are dated today up to 60 days ahead (requests stay up 30 days)
  * notes (if any) have no links, emails, phone numbers, swear words or shouting
  * no more than 3 posts from the same call on the same day
Anything else waits for a YES. NO always hides it. Nothing about why a row is waiting is published."""
import os, re, sys, hashlib, datetime, json
sys.path.insert(0, os.path.dirname(__file__))
import kpc_formtools as T, kpc_preapproved as PA

URL = os.environ.get('KPC_ACTIVATIONS_CSV', '').strip()
OUT = 'kpc-activations.json'
N = lambda m: T.notice('Activation Board', m)
if not URL: N('KPC_ACTIVATIONS_CSV secret not set yet; nothing to do.'); sys.exit(0)
H, rows = T.sheet(URL)
PRE = PA.load()
c = lambda name: T.col(H, name)
C = dict(ts=c('Timestamp'), call=c('Call sign'), kind=c('What are you posting?'), now=c('Planned or on the air now?'),
         refs=c('Park, summit or reference number(s)'), prog=c('Program'), date=c('Date'), start=c('Start time'),
         end=c('End time'), tz=c('Time zone'), bands=c('Bands'), modes=c('Modes'), freqs=c('Frequencies'),
         extras=c('Extras'), notes=c('Notes'), need=c("Park(s) you need"), rprog=c('Program (request)'),
         rbands=c('Bands you can hear'), rmodes=c('Modes you can work'), when=c('When works best for you?'),
         rnotes=c('Notes (request)'), app=c('Approved'))
if C['call'] is None: N('The sheet has no "Call sign" column; is this the right CSV link?'); sys.exit(0)
today = datetime.date.today()
lst = lambda t: [x.strip() for x in (t or '').split(',') if x.strip()]
items, waiting, per_day = [], 0, {}
for r in rows:
    g = lambda k: T.cell(r, C[k])
    ap = T.approval(g('app'))
    if ap == 'no': continue
    call = T.base(g('call'))
    if not call: continue
    ts = g('ts'); posted = T.sheet_date(ts) or today
    req = 'hunter' in g('kind').lower() or 'request' in g('kind').lower()
    refs = T.split_refs(g('need') if req else g('refs'))
    if not refs: continue
    iid = hashlib.sha1((ts + call + ','.join(refs)).encode()).hexdigest()[:12]
    notes = (g('rnotes') if req else g('notes'))[:300]
    it = {'id': iid, 'kind': 'req' if req else 'act', 'call': g('call').upper().replace(' ', ''), 'posted': posted.isoformat(), 'refs': []}
    if req:
        it.update(prog=lst(g('rprog')), bands=lst(g('rbands')), modes=lst(g('rmodes')), when=lst(g('when')), notes=notes)
        if (today - posted).days > 30: continue
    else:
        d = T.sheet_date(g('date'))
        if not d or d < today - datetime.timedelta(days=1): continue        # past activations drop off
        it.update(now='now' in g('now').lower(), date=d.isoformat(), start=T.sheet_time(g('start')), end=T.sheet_time(g('end')),
                  tz=g('tz') or 'Eastern', prog=lst(g('prog')), bands=lst(g('bands')), modes=lst(g('modes')),
                  freqs=re.sub(r'[^0-9., ]', '', g('freqs'))[:60], extras=lst(g('extras')), notes=notes)
    names = {ref: T.ref_name(ref) for ref in refs}
    it['refs'] = [{'ref': ref, 'name': names[ref] or ''} for ref in refs]
    if ap != 'yes':
        safe = True
        if T.base(call) not in PRE:
            safe = T.real_call(call) is True
        safe = safe and all(names[ref] for ref in refs)
        safe = safe and not T.clean(notes)
        if not req: safe = safe and T.sheet_date(g('date')) <= today + datetime.timedelta(days=60)
        k = (call, posted.isoformat()); per_day[k] = per_day.get(k, 0) + 1
        safe = safe and per_day[k] <= 3
        if not safe: waiting += 1; continue
    items.append(it)
acts = sorted([i for i in items if i['kind'] == 'act'], key=lambda i: (i['date'], i['start'] or '99'))
reqs = sorted([i for i in items if i['kind'] == 'req'], key=lambda i: i['posted'], reverse=True)
T.save_cache()
T.write_if_changed(OUT, {'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'items': acts + reqs}, 'items')
N(f'{len(acts)} activation(s) and {len(reqs)} park request(s) on the board; {waiting} waiting for YES in the Approved column.')
