#!/usr/bin/env python3
"""BOT A: THE ANSWERS WRITER (Fable, Oct 29 2026 11:15 PM; Brandon 11:12 PM 'Do a'; plan: KPC_Key_And_2fer_Automation_Plan.md).
Copies chat 11's YES / NO answers from the waiting room's question files into the US key's rules file, data/us-key/overrides.json,
exactly the way chat 2 did by hand on Oct 29. It MOVES decisions; it never makes one: a row without a plain YES or NO changes
nothing, a layer the key does not read is skipped and listed, and a later answer on the same park + piece replaces the earlier one.

Reads  <DATA>/data/waiting/questions/*.json   (KPC-Data checkout; env DATA, default ../kpcdata, then ../kpc-data)
         rows: {ref, record, record_name, answer, checked_by, [layer], [acres|acres_approx], [kind]}  under 'questions' (list or dict)
       data/us-key/layers.json                 (key prefix per layer URL: a gis-hunter 'record' is a layer OBJECTID)
Writes data/us-key/overrides.json  parks[ref]: YES -> join += [id], fp[id] = [record_name, acres], (id taken out of 'no')
                                                NO  -> no += [id] (id taken out of 'join' + 'fp');  kind 'alias' + YES -> alias += [record_name]
       data/us-key/answers-applied.json       ledger {"<file>:<ref>:<id>": {answer, checked_by, applied}}: a row applied with the same
                                                answer is skipped, so the bot is safe to run every night; a changed answer is re-applied
       data/us-key/answers-states.txt         the states touched (for the changed-states rebuild, BOT B)
Prints one ::notice line. Exit 0 always (a bot step never goes red for a missing file).
  python3 kpc_key_answers.py            apply
  python3 kpc_key_answers.py --dry      show what would change, write nothing
"""
import datetime as dt, glob, json, os, pathlib, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: from kpc_save import save_json
except Exception:  # noqa: BLE001
    def save_json(p, o, indent=1): json.dump(o, open(p, 'w'), indent=indent, ensure_ascii=False); return True

KEY = pathlib.Path(os.environ.get('KEY_DIR') or 'data/us-key')
OVR, LEDGER, STATES = KEY / 'overrides.json', KEY / 'answers-applied.json', KEY / 'answers-states.txt'
PAD = 'edits.nationalmap.gov/arcgis/rest/services/pad-us/pad_us/mapserver/0'
FWS = 'fwsinterest_simplified_authoritative/featureserver/0'
DRY = '--dry' in sys.argv


def data_dir():
    for d in (os.environ.get('DATA'), '../kpcdata', '../kpc-data', 'kpcdata'):
        if d and pathlib.Path(d, 'data/waiting/questions').is_dir(): return pathlib.Path(d)
    return None


def load(p, d):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def rows_of(j):
    q = j.get('questions') if isinstance(j, dict) else j
    if isinstance(q, dict): q = list(q.values())
    return [r for r in (q or []) if isinstance(r, dict) and r.get('ref') and r.get('record') is not None]


def norm_url(u):
    u = str(u or '').strip().lower().split('?')[0].rstrip('/')
    u = re.sub(r'/query$', '', u)
    return re.sub(r'^https?://', '', u)


def layer_map():
    """layer URL (normalised) -> key prefix, from data/us-key/layers.json (a layer keeps its prefix for ever, see kpc_us_key.py)."""
    m = {}
    for pre, v in (load(KEY / 'layers.json', {}) or {}).items():
        if isinstance(v, list) and v and isinstance(v[0], str) and not v[0].startswith('file:'):
            u = norm_url(v[0]); m[u] = pre
            m[u.replace('/featureserver/', '/mapserver/')] = pre; m[u.replace('/mapserver/', '/featureserver/')] = pre
    return m


def key_id(row, lmap):
    """The key's own id for a question row: ('id' or None, why skipped)."""
    rec = str(row.get('record')).strip()
    lay = row.get('layer')
    if not lay:                                   # key-pieces rows: the record IS a key id (fws448, sgtni131, 195096, rst9580)
        return rec, ''
    u = norm_url(lay)
    if PAD in u: return rec, ''                   # PAD-US: the bare OBJECTID
    if FWS in u: return ('fws' + rec if not rec.startswith('fws') else rec), ''
    pre = lmap.get(u)
    if not pre: return None, f'layer not read by the key: {lay}'
    return (rec if rec.startswith(pre) else pre + rec), ''


def answer_of(row):
    a = str(row.get('answer') or '').strip().upper()
    return a if a in ('YES', 'NO') else ''


def st_of(row):
    a = str(row.get('area') or row.get('st') or '')
    m = re.search(r'\b([A-Z]{2})\b', a.replace('US-', ''))
    return m.group(1) if m else ''


def main():
    D = data_dir()
    if D is None:
        print('::notice title=Key answers::no KPC-Data checkout with data/waiting/questions: nothing applied'); return
    lmap = layer_map()
    ovr = load(OVR, {'parks': {}}); P = ovr.setdefault('parks', {})
    led = load(LEDGER, {})
    today = dt.date.today().isoformat(); stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    n_yes = n_no = n_alias = n_skip = n_same = 0; skipped = []; states = set(); touched = set()
    # last answer wins: rows are read file by file (sorted), in file order; the latest row for a (file, ref, id) is the one applied
    for f in sorted(glob.glob(str(D / 'data/waiting/questions/*.json'))):
        name = pathlib.Path(f).stem
        latest = {}
        for row in rows_of(load(f, {})):
            kid, why = key_id(row, lmap)
            if not kid:
                if answer_of(row): n_skip += 1; skipped.append(f"{row.get('ref')} {why}")
                continue
            latest[(row['ref'], kid)] = row
        for (ref, kid), row in latest.items():
            ans = answer_of(row)
            if not ans: continue                                     # NOT SURE / blank: nothing changes
            lk = f'{name}:{ref}:{kid}'
            if (led.get(lk) or {}).get('answer') == ans: n_same += 1; continue
            v = P.setdefault(ref, {})
            nm = str(row.get('record_name') or '').strip()
            ac = row.get('acres') if row.get('acres') is not None else row.get('acres_approx')
            if ans == 'YES':
                if str(row.get('kind') or '').lower() == 'alias' and nm:
                    v.setdefault('alias', [])
                    if nm not in v['alias']: v['alias'].append(nm)
                    n_alias += 1
                else:
                    v['no'] = [x for x in v.get('no', []) if str(x) != kid] or v.get('no', [])
                    if not v.get('no'): v.pop('no', None)
                    v.setdefault('join', [])
                    if kid not in [str(x) for x in v['join']]: v['join'].append(kid)
                    v.setdefault('fp', {})[kid] = [nm, round(float(ac)) if ac not in (None, '') else 0]
                    n_yes += 1
            else:
                v['join'] = [x for x in v.get('join', []) if str(x) != kid]
                if not v['join']: v.pop('join', None)
                if kid in (v.get('fp') or {}): v['fp'].pop(kid)
                if not v.get('fp'): v.pop('fp', None)
                v.setdefault('no', [])
                if kid not in [str(x) for x in v['no']]: v['no'].append(kid)
                n_no += 1
            v['why'] = (v.get('why', '') + ' · ' if v.get('why') else '') + f"{stamp}: {name} row {ans} '{nm[:40]}' ({row.get('checked_by') or 'chat 11'}; applied by kpc_key_answers)"
            v['when'] = today
            led[lk] = {'answer': ans, 'checked_by': row.get('checked_by'), 'applied': stamp}
            touched.add(ref); st = st_of(row); states.add(st) if st else None
    msg = f"{n_yes} yes / {n_no} no / {n_alias} alias applied on {len(touched)} parks; {n_same} already applied; {n_skip} skipped; states: {' '.join(sorted(states)) or '-'}"
    if DRY:
        print('DRY ' + msg); [print('  skip ' + s) for s in skipped[:20]]; return
    if touched:
        save_json(OVR, ovr, 1); save_json(LEDGER, led, 1)
        STATES.write_text(' '.join(sorted(states)) + '\n')
    elif STATES.exists(): STATES.write_text('\n')
    print('::notice title=Key answers::' + msg + (f"; skipped: {'; '.join(skipped[:5])}" if skipped else ''))


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Key answers::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
