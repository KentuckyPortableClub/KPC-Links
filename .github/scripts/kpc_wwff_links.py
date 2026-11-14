#!/usr/bin/env python3
"""WWFF -> POTA cross reference for the US (KFF) and Canada (VEFF) (KPC owner, 2026-11-14).

Why: locations.json WWFF rows carry the linked POTA park in column 8, but kpc_search_lists.py mk_k only carried the old link
forward, so a WWFF area added after Oct 13 never got one (76 of the 575 KFF refs numbered 7000 and up were linked), and the
VEFF rows of data/canada.json had no link at all. This script works out a reviewed link per WWFF ref; the search-list writer
(kpc_search_lists.py) and the Canada pin writer (kpc_canada.py) then use only its CONFIRMED links.

Standard library only, no network. It never moves a pin and never changes a POTA row: it only reads pins to measure distance.

Sources (link_source):
  repo                  locations.json column 8 as it stood on 2026-11-14 (frozen in data/wwff-xref-sources.json, so a link this
                        writer adds is never counted back as a second source), plus Kentucky's own 'p' in kpc-ky-data.json
  community-VEFF-2025   VEFF-POTA cross reference list by VE3ZN (Aug 2025), deactivated (struck through) rows left out
  community-KFF-2018    KFF-POTA cross reference (2018): KFF-n = US-n for 0001-4446 except 3791, plus its explicit rows
  rule-name-distance    same normalised name (full or core), POTA park in the same state / province, exactly one such park
                        within 5 km of the WWFF pin (the Nov 14 offline method)
  hand                  a decision written in data/wwff-xref-sources.json 'hand' (who decided, when, why), or a person's answer in
                        the person_decision column of data/wwff-xref-review.csv: yes (the row's single pota_ref), a POTA ref (that
                        park), or no (never written to the site). Answers are kept from one build to the next.
Status:
  confirmed  two or more sources name the same POTA park, it is on today's POTA list and POTA lists it in the WWFF area's state /
             province (a park POTA lists in several states, such as a trail or a forest, counts in each of them); or a hand decision
  proposed   one source only, or the park fails the active / same state check (the reason is in note)
  conflict   sources name different POTA parks, or one source gives one WWFF ref several POTA parks (all are listed, '|' between)
  none       no source names a POTA park
Only confirmed links are written to the site. proposed and conflict rows go to data/wwff-xref-review.csv for a person.

  python3 .github/scripts/kpc_wwff_links.py build [--data DIR] [--date YYYY-MM-DD]   write the cross reference + review list
  python3 .github/scripts/kpc_wwff_links.py preview [--data DIR]                      what the writers would change (nothing written)
--data = where data/wwff and data/parkinfo are (default: this checkout, laid over from KPC-Data by kpc_overlay.sh).
Fails closed: a short or unreadable input writes nothing and exits 1; so does a build that would lose over a fifth of the
confirmed links of the last saved file."""
import argparse
import collections
import csv
import datetime as dt
import glob
import io
import json
import math
import os
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path('.')
SOURCES = 'data/wwff-xref-sources.json'
XREF = {'KFF': 'data/wwff-xref-KFF.json', 'VEFF': 'data/wwff-xref-VEFF.json'}
REVIEW = 'data/wwff-xref-review.csv'
COLUMNS = ['wwff_ref', 'wwff_name', 'region', 'pota_ref', 'link_source', 'status', 'distance_km', 'checked_date', 'note']
CREDIT = 'VEFF-POTA cross reference list by VE3ZN (Aug 2025); KFF-POTA cross reference (2018)'
MIN_ROWS = {'KFF': 6000, 'VEFF': 4000}           # the WWFF copy had 7,450 / 5,264 on Nov 14
MIN_POTA = {'KFF': 10000, 'VEFF': 4500}          # POTA had 13,040 US / 5,899 CA parks on Nov 14
NEAR_KM = 5.0
KST = {'KL': 'AK', 'KH6': 'HI', 'KH5': 'HI', 'KH7K': 'HI', 'KH8': 'AS', 'KH8S': 'AS', 'KP4': 'PR', 'KP2': 'VI', 'KP5': 'PR'}
VPROV = {'VE-MN': 'MB', 'VE-MB': 'MB', 'VE-ON': 'ON', 'VE-QC': 'QC', 'VE-BC': 'BC', 'VE-NB': 'NB', 'VE-NS': 'NS', 'VE-AB': 'AB',
         'VE-SK': 'SK', 'VE-PE': 'PE', 'VE-NL': 'NL', 'VE-YT': 'YT', 'VE-NT': 'NT', 'VE-NU': 'NU', 'CY0': 'NS', 'CY9': 'NS'}
TYPE = set('''national provincial state park parks wildlife area areas management wma nwr refuge reserve recreation recreational natural
historic site monument forest conservation ecological preserve the of and de du la le les des heritage nature trail trails regional protected
landscape wilderness waterway sanctuary marine unit division lands land fish game public use pa np pp ser wa nha nhs nra ca sf sp sra snr swa
sna sea cd'''.split())


def say(kind, title, msg):
    print(f'::{kind} title={title}::{msg}')


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(min(1.0, x)))


def strip(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and ').replace("'", '').replace('’', '')
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'\bmt\.?\b', 'mount', s); s = re.sub(r'\bst\.?\b(?=\s)', 'saint', s); s = re.sub(r'\bft\.?\b', 'fort', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def core(s):
    return ' '.join(w for w in strip(s).split() if w not in TYPE)


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def pin_ok(la, lo):
    return la is not None and lo is not None and (la, lo) != (0, 0) and -90 <= la <= 90 and -180 <= lo <= 180


def us_region(code):
    code = str(code or '')
    if re.fullmatch(r'K-[A-Z]{2}', code): return code[2:]
    return KST.get(code, '')


def ca_region(code):
    return VPROV.get(str(code or ''), '')


def load_json(p, default=None):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001  (fail closed by the caller's size checks)
        return default


# ---------------------------------------------------------------- inputs
def read_inputs(data):
    """Everything the build reads. data = folder with data/wwff and data/parkinfo (a KPC-Data checkout or this overlaid checkout)."""
    D = pathlib.Path(data)
    src = load_json(ROOT / SOURCES)
    if not isinstance(src, dict) or 'repo_baseline' not in src: raise SystemExit(f'{SOURCES} missing or unreadable')
    wwff = {pre: load_json(D / 'data' / 'wwff' / f'{pre}.json', []) or [] for pre in ('KFF', 'VEFF')}
    ky = load_json(ROOT / 'kpc-ky-data.json', {}) or {}
    loc = load_json(ROOT / 'locations.json', []) or []
    can = (load_json(ROOT / 'data' / 'canada.json', {}) or {}).get('rows') or []
    # POTA parks of today's list (active), with the states / provinces POTA lists each in
    st = collections.defaultdict(set)
    for f in glob.glob(str(D / 'data' / 'parkinfo' / 'US-*.json')):
        s = os.path.basename(f)[3:-5]
        for r in (load_json(f, {}) or {}).get('parks') or {}: st[r].add(s)
    for p in ky.get('parks') or []: st[p.get('c')].add('KY')
    for r, v in ((load_json(D / 'data' / 'parkinfo' / 'CA.json', {}) or {}).get('parks') or {}).items():
        if isinstance(v, list) and v and isinstance(v[-1], str) and re.fullmatch(r'[A-Z]{2}', v[-1]): st[r].add(v[-1])
    pota = {'KFF': {}, 'VEFF': {}}
    for r in loc:
        if isinstance(r, list) and len(r) > 4 and r[0] == 'POTA' and str(r[1]).startswith('US-'):
            pota['KFF'][r[1]] = {'ref': r[1], 'name': r[2], 'la': num(r[3]), 'lo': num(r[4]), 'st': st.get(r[1], set())}
    for r in can:
        if isinstance(r, list) and len(r) > 4 and r[0] == 'POTA' and str(r[1]).startswith('CA-'):
            pota['VEFF'][r[1]] = {'ref': r[1], 'name': r[2], 'la': num(r[3]), 'lo': num(r[4]), 'st': st.get(r[1], set())}
    site = {r[1]: (r[7] if len(r) > 7 else '') or '' for r in loc if isinstance(r, list) and len(r) > 1 and r[0] == 'WWFF'}
    kyp = {k.get('c'): k.get('p') or '' for k in ky.get('kff') or []}
    bad = [f'{pre} WWFF copy {len(wwff[pre])} rows (expected at least {MIN_ROWS[pre]})' for pre in wwff if len(wwff[pre]) < MIN_ROWS[pre]]
    bad += [f'{pre} POTA list {len(pota[pre])} parks (expected at least {MIN_POTA[pre]})' for pre in pota if len(pota[pre]) < MIN_POTA[pre]]
    if sum(1 for v in pota['KFF'].values() if v['st']) < 0.9 * len(pota['KFF']): bad.append('US POTA states (data/parkinfo) mostly missing')
    if sum(1 for v in pota['VEFF'].values() if v['st']) < 0.9 * len(pota['VEFF']): bad.append('CA POTA provinces (data/parkinfo/CA.json) mostly missing')
    return src, wwff, pota, site, kyp, bad


def community(src, pre):
    """{wwff_ref: [pota_ref, ...]} of the community list for this prefix."""
    out = collections.defaultdict(list)
    if pre == 'VEFF':
        for w, p in (src.get('community_veff_2025') or {}).get('pairs') or []:
            if p not in out[w]: out[w].append(p)
        return out, 'community-VEFF-2025'
    c = src.get('community_kff_2018') or {}
    for w, p in c.get('pairs') or []: out[w].append(p)
    lo, hi, ex = int(c.get('direct_from') or 0), int(c.get('direct_to') or -1), set(c.get('direct_except') or [])
    for n in range(lo, hi + 1):
        if n in ex: continue
        w = 'KFF-%04d' % n
        if w not in out: out[w].append('US-%04d' % n)   # an explicit row wins over the direct range
    return out, 'community-KFF-2018'


def name_rule(W, P, regions_of):
    """{wwff_ref: (pota_ref, km)} where exactly one same-name POTA park of the same state / province is within 5 km
    (or the nearest under 1 km and every other one at 5 km or more)."""
    by = collections.defaultdict(list)
    for p in P.values():
        if not pin_ok(p['la'], p['lo']): continue
        for r in p['st']:
            by[(r, 'F', strip(p['name']))].append(p)
            by[(r, 'C', core(p['name']))].append(p)
    out = {}
    for w in W.values():
        if not pin_ok(w['la'], w['lo']): continue
        cand = {}
        for r in regions_of(w):
            for kind, key in (('F', strip(w['name'])), ('C', core(w['name']))):
                if not key or (kind == 'C' and len(key) < 4): continue
                for p in by.get((r, kind, key), []):
                    cand.setdefault(p['ref'], hav(w['la'], w['lo'], p['la'], p['lo']))
        near = sorted((d, ref) for ref, d in cand.items() if d < NEAR_KM)
        if len(near) == 1 or (len(near) > 1 and near[0][0] < 1 and near[1][0] >= NEAR_KM):
            out[w['ref']] = (near[0][1], near[0][0])
    return out


# ---------------------------------------------------------------- the cross reference
def read_decisions():
    """{wwff_ref: (answer, pota_ref shown, original row)} from the person_decision column of the last review list."""
    out = {}
    try:
        for r in csv.DictReader(io.StringIO((ROOT / REVIEW).read_text(encoding='utf-8'))):
            v = (r.get('person_decision') or '').strip()
            if r.get('wwff_ref') and v: out[r['wwff_ref']] = (v, (r.get('pota_ref') or '').strip())
    except FileNotFoundError:
        pass
    return out


def decision_hand(ref, dec):
    """A person's yes / POTA ref as a hand entry, or 'no', or None (blank or not understood)."""
    if not dec: return None
    v, shown = dec
    m = re.fullmatch(r'(?i)\s*((?:US|CA)-\d{4,5})\s*', v)
    if m: return {'wwff': ref, 'pota': m.group(1).upper(), 'decided_by': 'person (review list)', 'date': '', 'why': 'review list answer ' + v}
    if v.lower() in ('yes', 'y', 'ok') and re.fullmatch(r'(US|CA)-\d{4,5}', shown):
        return {'wwff': ref, 'pota': shown, 'decided_by': 'person (review list)', 'date': '', 'why': 'review list answer yes'}
    if v.lower() in ('no', 'n'): return 'no'
    return None


def build_rows(pre, src, wwff, pota, kyp, prev, today, decisions=None):
    P = pota[pre]
    W = {}
    for x in wwff[pre]:
        if not isinstance(x, list) or len(x) < 4 or not str(x[0]).startswith(pre + '-'): continue
        W[x[0]] = {'ref': x[0], 'name': x[1], 'la': num(x[2]), 'lo': num(x[3]),
                   'codes': [x[5] if len(x) > 5 else '', x[6] if len(x) > 6 else '']}
    if pre == 'KFF':
        def regions_of(w): return [r for r in dict.fromkeys(us_region(c) for c in w['codes']) if r]
    else:
        def regions_of(w): return [r for r in dict.fromkeys(ca_region(c) for c in w['codes']) if r]
    rule = name_rule(W, P, regions_of)
    comm, comm_name = community(src, pre)
    repo = dict(src.get('repo_baseline') or {}) if pre == 'KFF' else {}
    if pre == 'KFF':
        for r, p in kyp.items():
            if p: repo.setdefault(r, p)
    hand = {h['wwff']: h for h in src.get('hand') or [] if str(h.get('wwff', '')).startswith(pre + '-')}
    said_no = set()
    for ref, dec in (decisions or {}).items():
        if not ref.startswith(pre + '-') or ref in hand: continue   # a hand line in the sources file wins over the review list
        h = decision_hand(ref, dec)
        if h == 'no': said_no.add(ref)
        elif h: hand[ref] = h
    rows = []
    for ref in sorted(W):
        w = W[ref]
        regs = regions_of(w)
        cands = collections.OrderedDict()
        def add(p, s):
            if p: cands.setdefault(p, [])
            if p and s not in cands[p]: cands[p].append(s)
        add(repo.get(ref), 'repo')
        for p in comm.get(ref, []): add(p, comm_name)
        if ref in rule: add(rule[ref][0], 'rule-name-distance')

        def km(p):
            q = P.get(p)
            if not q or not pin_ok(w['la'], w['lo']) or not pin_ok(q['la'], q['lo']): return ''
            return round(hav(w['la'], w['lo'], q['la'], q['lo']), 2)

        def problems(p):
            q = P.get(p)
            if not q: return ['POTA park not on today\'s POTA list']
            if not regs: return ['WWFF area has no state / province']
            if not q['st']: return ['no state / province for the POTA park']
            if not set(regs) & q['st']: return ['POTA lists the park in %s, the WWFF area is in %s' % ('/'.join(sorted(q['st'])), '/'.join(regs))]
            return []
        note = []
        if ref in hand:
            h = hand[ref]; pota_ref, srcs, status = h['pota'], 'hand', 'confirmed'
            note.append('hand: %s, %s: %s' % (h.get('decided_by', '?'), h.get('date', '?'), h.get('why', '')))
            other = ['%s %s' % ('+'.join(s), p) for p, s in cands.items()]
            if other: note.append('other sources: ' + '; '.join(other))
            note += problems(pota_ref)
            dist = km(pota_ref)
        elif not cands:
            pota_ref, srcs, status, dist = '', '', 'none', ''
        elif len(cands) > 1:
            pota_ref = '|'.join(cands); srcs = '|'.join('+'.join(s) for s in cands.values()); status = 'conflict'
            one_src = len({s for v in cands.values() for s in v}) == 1
            note.append('one WWFF ref, several POTA parks in one source' if one_src else 'sources name different POTA parks')
            for p in cands:
                pr = problems(p)
                if pr: note.append(p + ': ' + '; '.join(pr))
            dist = '|'.join(str(km(p)) for p in cands)
        else:
            pota_ref, s = next(iter(cands.items())); srcs = '+'.join(s)
            pr = problems(pota_ref); note += pr
            if len(s) >= 2 and not pr: status = 'confirmed'
            else:
                status = 'proposed'
                if len(s) < 2: note.append('one source only')
            dist = km(pota_ref)
        if status in ('confirmed', 'proposed') and pota_ref:
            others = [r for r, v in cands.items() if r != pota_ref]
            if others: note.append('also named: ' + ', '.join(others))
        if ref in said_no:
            if status == 'confirmed': status = 'proposed'
            note.append('a person answered no in the review list: not written to the site')
        if (decisions or {}).get(ref) and ref not in said_no and ref not in hand: note.append('review answer not understood: ' + decisions[ref][0])
        if pre == 'KFF' and ref in kyp and status == 'confirmed' and not kyp[ref] and pota_ref:
            note.append('Kentucky: the site takes this from kpc-ky-data.json (p is blank there); add it there by hand')
        old = prev.get(ref)
        same = old and old[3] == pota_ref and old[4] == srcs and old[5] == status
        rows.append([ref, w['name'], '/'.join(regs), pota_ref, srcs, status, dist, old[7] if same else today, '; '.join(note)])
    return rows


def write_outputs(results, pota, site, today, decisions=None):
    decisions = decisions or {}
    texts = {}
    for pre, rows in results.items():
        doc = {'about': 'WWFF -> POTA cross reference (%s), written by .github/scripts/kpc_wwff_links.py; only status confirmed is used by the '
                        'site (locations.json column 8 / data/canada.json). checked_date = the day this row last got its current answer.' % pre,
               'credit': CREDIT, 'checked': today, 'columns': COLUMNS,
               'counts': dict(collections.Counter(r[5] for r in rows)), 'rows': rows}
        s = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
        s = s.replace(',"rows":[[', ',"rows":[\n[').replace('],[', '],\n[')   # one row per line: a small diff each week
        texts[pre] = s + '\n'
    names = {r: p['name'] for P in pota.values() for r, p in P.items()}
    order = {'conflict': 0, 'proposed': 1, 'confirmed': 2}
    out = []
    for pre, rows in results.items():
        for r in rows:
            on = site.get(r[0], '') if pre == 'KFF' else ''
            if r[5] in ('conflict', 'proposed') or r[4] == 'hand' or 'Kentucky:' in r[8] or r[0] in decisions:
                pn = ' | '.join(names.get(p, '(not on POTA list)') for p in r[3].split('|')) if r[3] else ''
                out.append((order.get(r[5], 3), bool(on), r[0], [r[0], r[1], r[2], r[5], r[3], pn, r[4], r[6], on, r[8], (decisions.get(r[0]) or ('',))[0]]))
    out.sort(key=lambda x: x[:3])
    buf = io.StringIO()
    c = csv.writer(buf, lineterminator='\n')
    c.writerow(['wwff_ref', 'wwff_name', 'region', 'status', 'pota_ref', 'pota_name', 'link_source', 'distance_km', 'site_link_now', 'note', 'person_decision'])
    c.writerows(x[3] for x in out)
    texts['review'] = buf.getvalue()
    big = [k for k, t in texts.items() if len(t.encode('utf-8')) > 1_000_000]
    if big: raise SystemExit('::error title=WWFF links::over the 1 MB file cap, nothing written: ' + ', '.join(big))
    for pre in results: (ROOT / XREF[pre]).write_text(texts[pre], encoding='utf-8')
    (ROOT / REVIEW).write_text(texts['review'], encoding='utf-8')
    return len(out)


# ---------------------------------------------------------------- what the site writers use
def load_confirmed(pre, root=None):
    """{wwff_ref: (pota_ref, link_source)} of the CONFIRMED rows of data/wwff-xref-<pre>.json, or None when the file is missing or
    unreadable (the caller then behaves exactly as before this file existed)."""
    d = load_json(pathlib.Path(root or ROOT) / XREF[pre])
    if not isinstance(d, dict) or not isinstance(d.get('rows'), list) or d.get('columns', [])[:6] != COLUMNS[:6]: return None
    out = {}
    for r in d['rows']:
        if isinstance(r, list) and len(r) > 5 and r[5] == 'confirmed' and re.fullmatch(r'(US|CA)-\d{4,5}', str(r[3])):
            out[r[0]] = (r[3], r[4])
    return out


def pick_link(old, conf):
    """Column 8 of a WWFF row (not Kentucky). A hand decision wins; otherwise a link the row already has is kept (a conflict is for a
    person, never changed here); a row with no link gets the confirmed one. conf = load_confirmed(...).get(ref) or None."""
    if conf and conf[1] == 'hand': return conf[0]
    if old: return old
    return conf[0] if conf else ''


# ---------------------------------------------------------------- commands
def cmd_build(a):
    today = a.date or dt.date.today().isoformat()
    src, wwff, pota, site, kyp, bad = read_inputs(a.data)
    if bad:
        say('error', 'WWFF links', 'not built, nothing written: ' + '; '.join(bad)); return 1
    results, decisions = {}, read_decisions()
    for pre in ('KFF', 'VEFF'):
        prevd = load_json(ROOT / XREF[pre], {}) or {}
        prev = {r[0]: r for r in prevd.get('rows') or [] if isinstance(r, list) and len(r) >= 8}
        results[pre] = build_rows(pre, src, wwff, pota, kyp, prev, today, decisions)
        n_old = sum(1 for r in prev.values() if r[5] == 'confirmed')
        n_new = sum(1 for r in results[pre] if r[5] == 'confirmed')
        if n_old and n_new < 0.8 * n_old:
            say('error', 'WWFF links', f'{pre}: confirmed links would drop from {n_old} to {n_new}; nothing written (check the inputs)'); return 1
    n_rev = write_outputs(results, pota, site, today, decisions)
    for pre, rows in results.items():
        c = collections.Counter(r[5] for r in rows)
        say('notice', f'WWFF links {pre}', ', '.join(f'{k} {c.get(k, 0)}' for k in ('confirmed', 'proposed', 'conflict', 'none')))
    say('notice', 'WWFF links', f'{n_rev} rows for a person in {REVIEW}')
    return 0


def cmd_preview(a):
    loc = load_json(ROOT / 'locations.json', []) or []
    ky = {k.get('c') for k in (load_json(ROOT / 'kpc-ky-data.json', {}) or {}).get('kff') or []}
    conf = load_confirmed('KFF') or {}
    gain, change = [], []
    for r in loc:
        if not (isinstance(r, list) and r and r[0] == 'WWFF' and str(r[1]).startswith('KFF-')) or r[1] in ky: continue
        old = r[7] if len(r) > 7 else ''
        new = pick_link(old, conf.get(r[1]))
        if new != old: (gain if not old else change).append((r[1], old, new))
    print(f'locations.json KFF rows: {len(gain)} gain a link, {len(change)} change')
    for x in change: print('  change', *x)
    can = (load_json(ROOT / 'data' / 'canada.json', {}) or {}).get('rows') or []
    cc = load_confirmed('VEFF') or {}
    print(f'data/canada.json VEFF rows: {sum(1 for r in can if r[0] == "WWFF" and r[1] in cc)} of {sum(1 for r in can if r[0] == "WWFF")} get a link')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['build', 'preview'])
    ap.add_argument('--data', default='.', help='folder with data/wwff and data/parkinfo (default: this checkout)')
    ap.add_argument('--date', default=None, help='build: the checked date (default today)')
    a = ap.parse_args(argv)
    return cmd_build(a) if a.cmd == 'build' else cmd_preview(a)


if __name__ == '__main__':
    sys.exit(main())
