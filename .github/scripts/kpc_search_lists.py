#!/usr/bin/env python3
"""Keep the Park Finder's search lists current (Opus, Oct 23 2026; Brandon: 'Should we fix the search?').

locations.json (every US park, KFF area and SOTA summit the Finder, US planner and offline mode search) was built once
on Oct 13 and never refreshed, so new parks were missing and retired ones stayed. kpc_new_refs.py already reads the
full official lists every morning; it now calls update() with them:
  POTA  US-* rows   = POTA's list today (Kentucky parks use the club's own pins + names from kpc-ky-data.json)
  WWFF  KFF-* rows  = the WWFF directory's ACTIVE areas (Kentucky ones from kpc-ky-data.json)
  SOTA  US rows     = the SOTA summits valid today (W4K from kpc-ky-data.json)
A program whose read failed or came back short is passed as None and its rows are left exactly as they are.
Rows of other kinds (world parks, anything else) are never touched. locations-ky.json = the rows inside its 'box'.
Row shapes (unchanged): POTA [prog, ref, name, la, lo, url]; WWFF [.., url, None, potaRef]; SOTA [.., url, 'metres', 'SOTA<pts>']."""
import json
import pathlib
import re

LOC, LKY, KY = pathlib.Path('locations.json'), pathlib.Path('locations-ky.json'), pathlib.Path('kpc-ky-data.json')
US_SOTA = re.compile(r'^(W\d|K[HLP]\d)')


def _ok(la, lo):
    return isinstance(la, (int, float)) and isinstance(lo, (int, float)) and (la or lo)


def update(pota=None, kff=None, sota=None, write=True):
    """pota/kff/sota = {ref: {name, la, lo, ...}} from today's official read, or None to leave that program alone.
    Returns a short summary per program: (kept, added, removed)."""
    rows = json.loads(LOC.read_text(encoding='utf-8'))
    ky = json.loads(KY.read_text(encoding='utf-8'))
    KP = {p['c']: p for p in ky.get('parks', [])}
    KK = {k['c']: k for k in ky.get('kff', [])}
    KS = {s['c']: s for s in ky.get('summits', [])}
    old = {(r[0], r[1]): r for r in rows}
    out, summary = [], {}

    def mine(r):   # is this row one of the programs being refreshed?
        if r[0] == 'POTA' and pota is not None and str(r[1]).startswith('US-'): return 'POTA'
        if r[0] == 'WWFF' and kff is not None and str(r[1]).startswith('KFF-'): return 'WWFF'
        if r[0] == 'SOTA' and sota is not None and US_SOTA.match(str(r[1])): return 'SOTA'
        return None
    out = [r for r in rows if not mine(r)]

    def build(prog, cur, mk):
        n0 = sum(1 for k in old if k[0] == prog and mine(old[k]))
        new_rows = []
        for ref in sorted(cur):
            r = mk(ref, cur[ref], old.get((prog, ref)))
            if r: new_rows.append(r)
        have = {r[1] for r in new_rows}
        oldrefs = {k[1] for k in old if k[0] == prog and mine(old[k])}
        summary[prog] = {'rows': len(new_rows), 'added': len(have - oldrefs), 'removed': len(oldrefs - have), 'before': n0}
        return new_rows

    if pota is not None:
        def mk_p(ref, c, o):
            k = KP.get(ref)
            name = (k or {}).get('n') or c.get('name') or (o[2] if o else '')
            la, lo = ((k['la'], k['lo']) if k else (c.get('la'), c.get('lo')))
            if not _ok(la, lo) and o: la, lo = o[3], o[4]
            if not _ok(la, lo): return None
            return ['POTA', ref, name, la, lo, 'https://next.pota.app/park/' + ref]
        out += build('POTA', pota, mk_p)
    if kff is not None:
        def mk_k(ref, c, o):
            k = KK.get(ref)
            name = (k or {}).get('n') or c.get('name') or (o[2] if o else '')
            la, lo = ((k['la'], k['lo']) if k else (c.get('la'), c.get('lo')))
            if not _ok(la, lo) and o: la, lo = o[3], o[4]
            if not _ok(la, lo): return None
            p = (k or {}).get('p') if k else (o[7] if o and len(o) > 7 else '')
            return ['WWFF', ref, name, la, lo, 'https://wwff.co/directory/', None, p or '']
        out += build('WWFF', kff, mk_k)
    if sota is not None:
        def mk_s(ref, c, o):
            k = KS.get(ref)
            name = (k or {}).get('n') or c.get('name') or (o[2] if o else '')
            la, lo = ((k['la'], k['lo']) if k and _ok(k.get('la'), k.get('lo')) else (c.get('la'), c.get('lo')))
            if not _ok(la, lo) and o: la, lo = o[3], o[4]
            if not _ok(la, lo): return None
            m = str(round(c['ft'] * 0.3048)) if c.get('ft') else (o[6] if o and len(o) > 6 else '')
            pts = 'SOTA%d' % c['pts'] if c.get('pts') is not None else (o[7] if o and len(o) > 7 else '')
            return ['SOTA', ref, name, la, lo, 'https://sotl.as/summits/' + ref, m, pts]
        out += build('SOTA', sota, mk_s)

    if write:
        LOC.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
        k = json.loads(LKY.read_text(encoding='utf-8'))
        b = k['box']
        k['rows'] = [r for r in out if b[0] <= r[3] <= b[1] and b[2] <= r[4] <= b[3]]
        k['total'] = len(k['rows'])
        LKY.write_text(json.dumps(k, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    return summary
