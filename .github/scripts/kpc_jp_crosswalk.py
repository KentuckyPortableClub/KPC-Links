#!/usr/bin/env python3
"""JAPAN A10 CROSSWALK in the world answer key (KPC owner, 2026-11-12; handoff item 6). BEHIND A SWITCH THAT STAYS OFF.

The file: data/research-inbox/answers/nov5/JP_A10_crosswalk.csv (KPC-Links #148; header + 70 rows): for a JP park, the official
Japanese name of its record in MLIT's National Land Numerical Information A10 (natural park areas), the park class (1 national,
2 quasi-national, 3 prefectural, U = an urban park / facility that is NOT in A10), the prefecture code(s) and a proposed answer
(match / note = join on that name and test the pin; other = a person decides).

THE SWITCH: the Japan A10 licence terms are an open owner question, so nothing here runs until he signs them. Repo variable
KPC_JP_A10_CROSSWALK, passed by kpc-world-key.yml as env: exactly 'on' = ON; anything else (unset, empty, 'off') = OFF.
OFF: the file is never opened and nothing changes (the JP key is byte for byte what it is without this module); the run says
'JP A10 crosswalk: OFF (licence not signed)'.

ON, for country JP only, after the builder's own join of every park (apply(), called once per country):
  * a row is USED only when its class is 1, 2 or 3, its answer is match or note, its name has no bracket / question mark, its park
    is in the POTA list, has a usable pin and is NOT joined already (a join is never replaced or moved). Class U rows are a
    facility inside a natural park: they are never joined to the park around them (never the bigger surrounding place).
    'other' rows are a person's call: not used.
  * the name is an ALIAS, never a location: a record joins only when its own Japanese name (the builder's jparts / jstrip reading of
    the A10 name, kind words dropped) is that name, its kind fits the class (np / qnp / pnp) and, when the record carries one, its
    prefecture code is one the row lists. Only pieces near the POTA pin join, by the builder's own name-join distances (within
    0.6 degree; a small piece only within 0.08 degree or holding the pin).
  * HELD, not joined (the records go to the park's 'c' = check by hand, with the reason): two rows give one name (two parks would
    share one outline), a prefectural row that lists more than one prefecture or whose name is found in more than one prefecture,
    a park with no usable POTA pin, and a name whose records are all far from the pin. A join it makes is new, so the join check
    after the builder (kpc_join_check.py) still holds it when it is over 5 km from the pin.
  * a file that cannot be read or is not the expected shape: nothing is applied, a loud warning; the country build goes on.
Joined pieces carry how = 'official Japanese name (A10 crosswalk): <name>'. Writes no file, no network, standard library only."""
import csv, io, os, re, sys

ENV = 'KPC_JP_A10_CROSSWALK'
FILE = 'data/research-inbox/answers/nov5/JP_A10_crosswalk.csv'
HEAD = ['ref', 'pota_name', 'a10_005_join_key_or_official_ja_name', 'park_class', 'prefecture_code(s)', 'proposed_answer', 'note']
KIND = {'1': 'np', '2': 'qnp', '3': 'pnp'}
HOW = 'official Japanese name (A10 crosswalk): '
REF = re.compile(r'^JP-\d{4,5}$')


def is_on(env=None):
    return str((os.environ if env is None else env).get(ENV) or '').strip().lower() == 'on'


def _say(notice, title, msg, loud=False):
    if loud: print(f"::warning title={title}::{msg}", flush=True)
    elif notice: notice(title, msg)
    else: print(f"::notice title={title}::{msg}", flush=True)
    sm = os.environ.get('GITHUB_STEP_SUMMARY')
    if sm:
        try:
            with open(sm, 'a', encoding='utf-8') as f: f.write(f"- {title}: {msg}\n")
        except OSError: pass


def read(path=None):
    """(rows, problem): the file's rows as dicts (HEAD keys), or ([], why) when it cannot be read or is not the expected shape."""
    path = path or FILE
    try:
        with open(path, encoding='utf-8', newline='') as f: txt = f.read()
    except FileNotFoundError: return [], f'not found ({path})'
    except Exception as e: return [], f'cannot be read ({type(e).__name__})'  # noqa: BLE001
    try: rows = list(csv.reader(io.StringIO(txt.lstrip('﻿'))))
    except csv.Error as e: return [], f'not a CSV ({e})'
    if not rows or len(rows[0]) != len(HEAD) or [h.split('(')[0].strip() for h in rows[0]][:4] != ['ref', 'pota_name', 'a10_005_join_key_or_official_ja_name', 'park_class']:
        return [], 'not the expected header (ref, pota_name, a10_005 join key, park class, prefecture codes, proposed answer, note)'
    body = [r for r in rows[1:] if any(c.strip() for c in r)]
    if not body: return [], 'has no rows'
    if any(len(r) != len(HEAD) for r in body): return [], f'has rows that are not {len(HEAD)} columns'
    return [dict(zip(HEAD, [c.strip() for c in r])) for r in body], ''


def anomalies(rows, park_refs=None):
    """Findings about the file (reported, never fixed here): duplicate refs, one name for two refs, refs not in the JP park list,
    bad refs, classes and answers outside the known values."""
    out, seen, keys = [], {}, {}
    for r in rows:
        seen.setdefault(r['ref'], 0); seen[r['ref']] += 1
        if r['park_class'] in KIND: keys.setdefault(r['a10_005_join_key_or_official_ja_name'], []).append(r['ref'])
        if not REF.match(r['ref']): out.append(f"{r['ref']}: not a JP park ref")
        if r['park_class'] not in ('1', '2', '3', 'U'): out.append(f"{r['ref']}: class {r['park_class']!r} is not 1 / 2 / 3 / U")
        if r['proposed_answer'] not in ('match', 'note', 'other'): out.append(f"{r['ref']}: answer {r['proposed_answer']!r} is not match / note / other")
        if park_refs is not None and r['ref'] not in park_refs: out.append(f"{r['ref']}: not in the JP park list")
    out += [f'{k}: {n} rows' for k, n in seen.items() if n > 1]
    out += [f"{k}: one name for {len(v)} parks ({' '.join(v)})" for k, v in keys.items() if len(v) > 1]
    return out


def _codes(s): return sorted(set(re.findall(r'\d{2}', s or '')))


def plan(rows):
    """{ref: (row, None)} rows that may be used, and {ref: why} rows that are not (before looking at the records)."""
    use, skip, keys = {}, {}, {}
    cnt = {}
    for r in rows: cnt[r['ref']] = cnt.get(r['ref'], 0) + 1
    for r in rows:
        if r['park_class'] in KIND: keys.setdefault(r['a10_005_join_key_or_official_ja_name'], set()).add(r['ref'])
    for r in rows:
        ref, k, cl, ans = r['ref'], r['a10_005_join_key_or_official_ja_name'], r['park_class'], r['proposed_answer']
        if cnt[ref] > 1: skip[ref] = 'held: the ref is in the crosswalk more than once'
        elif cl == 'U': skip[ref] = 'not used: an urban park / facility, not an A10 natural park (never the natural park around it)'
        elif cl not in KIND: skip[ref] = f'not used: class {cl!r}'
        elif ans == 'other': skip[ref] = 'not used: the answer is other (a person decides)'
        elif ans not in ('match', 'note'): skip[ref] = f'not used: answer {ans!r}'
        elif not k or re.search(r'[()（）?？]', k): skip[ref] = 'not used: the name is not a plain record name'
        elif len(keys.get(k, ())) > 1: skip[ref] = 'held: the same name is given for ' + ' '.join(sorted(keys[k])) + ' (two parks, one outline)'
        elif cl == '3' and len(_codes(r['prefecture_code(s)'])) > 1: skip[ref] = 'held: a prefectural park with more than one prefecture listed'
        else: use[ref] = r
    return use, skip


def _pref(q):
    v = str((q.get('_a') or {}).get('PREFEC_CD') or '').strip()
    return '' if v in ('', 'None') else v.zfill(2)


def _rparts(r, jstrip):
    return {re.sub(r'\s', '', q) for q in (r.get('jp') or [])} or ({jstrip(r['nj'])} if r.get('nj') else set())


def apply(cc, parks, P, recs, jstrip, near, inside, notice=None, path=None, env=None):
    """Join / hold the JP parks of the crosswalk (switch ON only). Returns {'on', 'joined', 'held', 'skipped'} (for the tests and the log)."""
    if cc != 'JP': return None
    title = 'JP A10 crosswalk'
    if not is_on(env):
        _say(notice, title, 'OFF (licence not signed): the crosswalk is not read; the JP key is built as before')
        return {'on': False, 'joined': {}, 'held': {}, 'skipped': {}}
    rows, problem = read(path)
    if problem:
        _say(notice, title, f'ON, but the crosswalk file is {problem}: NOTHING applied (fail closed); the JP build goes on', loud=True)
        return {'on': True, 'joined': {}, 'held': {}, 'skipped': {}, 'problem': problem}
    use, skip = plan(rows)
    joined, held = {}, {}
    def hits(r, codes):
        key, kind = jstrip(r['a10_005_join_key_or_official_ja_name']), KIND.get(r['park_class'])
        return [q for q in recs if q.get('nj') and key in _rparts(q, jstrip) and (not kind or not q.get('_k') or kind in q['_k'])
                and (not codes or _pref(q) in ('', *codes))]
    def hold(ref, pk, why, qs):
        held[ref] = why
        pk['c'] = (pk.get('c') or []) + [[q['id'], q['n'], q['src'], why] for q in qs[:6]]
    for ref, why in sorted(skip.items()):   # held before looking at the pin: the records of that name go to 'check by hand'
        pk = parks.get(ref)
        r = next((x for x in rows if x['ref'] == ref), None)
        if why.startswith('held') and pk is not None and not pk.get('m') and r is not None: hold(ref, pk, why, hits(r, set()))
    for ref, r in sorted(use.items()):
        pk, x = parks.get(ref), P.get(ref)
        if pk is None or x is None: skip[ref] = 'not used: not in the JP park list'; continue
        if pk.get('m'):
            mine = {(str(q[2]), str(q[0])) for q in pk['m']}
            same = any(q.get('nj') and jstrip(r['a10_005_join_key_or_official_ja_name']) in _rparts(q, jstrip) for q in recs if (str(q.get('src')), str(q.get('id'))) in mine)
            skip[ref] = 'not used: already joined (never replaced)' + ('' if same else '; the joined record does not carry the crosswalk name (a person checks)')
            continue
        la, lo = (x[5], x[6]) if len(x) > 6 else (None, None)
        codes = set(_codes(r['prefecture_code(s)']))
        hit = hits(r, codes)
        if not la and not lo: hold(ref, pk, 'held: POTA has no usable pin to test the record against', hit); continue
        if not hit: skip[ref] = 'not used: no record has that name'; continue
        pref = {_pref(q) for q in hit} - {''}
        if r['park_class'] == '3' and len(pref) > 1:
            hold(ref, pk, 'held: the name is found in more than one prefecture (' + ' '.join(sorted(pref)) + ')', hit); continue
        def ok(q):
            b = q.get('_bb')
            if not b or not near(la, lo, b, .6): return False
            return inside(la, lo, q.get('_r') or []) or near(la, lo, b, .08) or (b[2] - b[0] > .15 or b[3] - b[1] > .15)
        good = [q for q in hit if ok(q)]
        if not good: hold(ref, pk, 'held: the record of that name is far from the POTA pin', hit); continue
        pk['m'] = [[q['id'], q['n'], q['src'], HOW + r['a10_005_join_key_or_official_ja_name']] for q in good]; pk['c'] = []
        joined[ref] = len(good)
    _say(notice, title, f"ON: {len(rows)} rows; joined {len(joined)} ({' '.join(sorted(joined)) or '-'}); held {len(held)} "
                        f"({'; '.join(f'{k} {v}' for k, v in sorted(held.items())) or '-'}); not used {sum(1 for k in skip if k not in held)}"
                        + ''.join(f"; joined to another record, kept: {' '.join(sorted(k for k, v in skip.items() if 'a person checks' in v))}" for _ in [0] if any('a person checks' in v for v in skip.values())))
    return {'on': True, 'joined': joined, 'held': held, 'skipped': {k: v for k, v in skip.items() if k not in held}}


if __name__ == '__main__':   # a dry look at the file: python3 kpc_jp_crosswalk.py [csv] [JP park list json]
    import json
    rows, prob = read(sys.argv[1] if len(sys.argv) > 1 else None)
    if prob: print('not read:', prob); sys.exit(1)
    refs = set(json.load(open(sys.argv[2], encoding='utf-8'))['parks']) if len(sys.argv) > 2 else None
    use, skip = plan(rows)
    print(json.dumps({'rows': len(rows), 'may_join': sorted(use), 'not_used': skip, 'anomalies': anomalies(rows, refs)}, ensure_ascii=False, indent=1))
