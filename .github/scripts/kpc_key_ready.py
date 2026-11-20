#!/usr/bin/env python3
"""The baseline findings and the ready check of the master gate (keys-first hand-off rev 3.1, S3, F11; Opus 19 Nov 2026).

Reads files only and decides nothing by itself: the gate (kpc_master_cli.py gate) prints these findings and writes the report;
whether a finding HOLDS a state is behind two switches, both OFF until the reviewer has read the first report:
  KPC_GATE_STALE_REFUSE=1   a saved copy with FEWER records or rows than its baseline is moved aside (held). A baseline
                            LOWER than its copy never holds: it is raised to the copy's count (raise_low_baselines).
  KPC_READY_BLOCK=1         a state with a key layer that is missing, short, or waiting on a bot is held (a hand download never holds)

The counts:
  state baseline   layers.json caches[US-XX].expected_count  vs  the records in the saved copy (cache/us/US-XX.json.gz)
  layer baseline   layers.json layers['US-XX.<id>'].expected_count  vs  the copy's rows of that layer (OBJECTID '<id><number>')
  layer total      layers.json layers['<id>'].expected_count (the layer's own count, returnCountOnly), when there is one
Key layers of a state = its data/state-gis.json entries (id 'sg' + state + letter, the way kpc_us_key.py names them) and every
layers.json 'US-XX.<id>' entry. Not a rule file: it moves no rules hash, and it never edits data/state-gis.json.
"""
import collections, json, os, pathlib, re

ROW_ID = re.compile(r'^([a-z]+?)(\d+)$')
BOT_WAITING = ('open', 'held')


def switch(name, env=None):
    env = os.environ if env is None else env
    return str(env.get(name, '') or '').strip().lower() in ('1', 'on', 'yes', 'true')


def sg_ids(st, n):
    """The ids kpc_us_key.py gives a state's state-gis entries, in order: sgcoa, sgcob, ... sgcoz, sgcoaa ..."""
    out = []
    for i in range(n):
        out.append(f'sg{st.lower()}' + (chr(97 + i) if i < 26 else chr(97 + i // 26 - 1) + chr(97 + i % 26)))
    return out


def layer_rows(blob):
    """Counter: layer id -> rows of it in a saved copy."""
    c = collections.Counter()
    for r in (blob or {}).get('recs') or []:
        m = ROW_ID.match(str((r or {}).get('OBJECTID') or ''))
        if m:
            c[m.group(1)] += 1
    return c


def stale_baselines(stem, blob, layers_doc):
    """[(kind, key, baseline, count)] where a baseline differs from the count it should match (see the module note)."""
    out = []
    exp = ((layers_doc.get('caches') or {}).get(stem) or {}).get('expected_count')
    n = len((blob or {}).get('recs') or [])
    if exp is not None and exp != n:
        out.append(('state', stem, exp, n))
    rows = layer_rows(blob)
    for key, L in sorted((layers_doc.get('layers') or {}).items()):
        if not key.startswith(stem + '.') or L.get('expected_count') is None:
            continue
        lid = key.split('.', 1)[1]
        if rows.get(lid, 0) != L['expected_count']:
            out.append(('layer', key, L['expected_count'], rows.get(lid, 0)))
    return out


def is_short(finding):
    """A copy with FEWER records / rows than its baseline (Fable's ruling, 19 Nov: only this may ever hold a copy)."""
    return finding[3] < finding[2]


def raise_low_baselines(doc, stem, blob, how):
    """Fable's ruling (19 Nov, review of #300, 5.1): a baseline LOWER than its saved copy is raised to the copy's count, no re-read;
    it never holds. The state baseline (caches) and every 'STEM.<id>' layer baseline. A baseline is never lowered here.
    Returns [(key, old, new)]."""
    out = []
    n = len((blob or {}).get('recs') or [])
    c = (doc.get('caches') or {}).get(stem)
    if isinstance(c, dict) and c.get('expected_count') is not None and c['expected_count'] < n:
        out.append((stem, c['expected_count'], n)); c['expected_count'] = n; c['baseline_how'] = how
    rows = layer_rows(blob)
    for key, L in sorted((doc.get('layers') or {}).items()):
        if not key.startswith(stem + '.') or L.get('expected_count') is None:
            continue
        got = rows.get(key.split('.', 1)[1], 0)
        if got > L['expected_count']:
            out.append((key, L['expected_count'], got)); L['expected_count'] = got; L['baseline_how'] = how
    return out


def source_gaps(stem, layers_doc):
    """Ruling 5.4: a layer whose server count (source_count) differs from its baseline; information, never a hold."""
    return [(k, L['expected_count'], L['source_count']) for k, L in sorted((layers_doc.get('layers') or {}).items())
            if k.startswith(stem + '.') and L.get('expected_count') is not None and L.get('source_count') is not None
            and L['source_count'] != L['expected_count']]


def key_layers(stem, state_gis, layers_doc):
    st = stem.split('-', 1)[1]
    ids = sg_ids(st, len(((state_gis or {}).get('states') or {}).get(st) or []))
    ids += [k.split('.', 1)[1] for k in (layers_doc.get('layers') or {}) if k.startswith(stem + '.')]
    return list(dict.fromkeys(ids))


def _waiting(stem, state_gis, layers_doc, needs_rows):
    """{layer id: [needs-download rows]} of this state: rows with its area, and rows with no area matched by layer id or address
    (Fable's review of #300, 4: 405 of the 406 open person rows on 19 Nov carry no area)."""
    mine = key_layers(stem, state_gis, layers_doc)
    st = stem.split('-', 1)[1]
    ents = ((state_gis or {}).get('states') or {}).get(st) or []
    by_url = {str(e.get('url') or '').strip(): lid for lid, e in zip(sg_ids(st, len(ents)), ents) if isinstance(e, dict) and e.get('url')}
    out = {}
    for r in needs_rows or []:
        lid = str(r.get('layer') or r.get('src') or '')
        if r.get('area'):
            if r.get('area') != stem:
                continue
        elif lid.startswith('url:') and lid[4:].strip() in by_url:
            lid = by_url[lid[4:].strip()]
        elif str(r.get('url') or '').strip() in by_url and lid not in mine:
            lid = by_url[str(r.get('url')).strip()]
        elif lid not in mine:
            continue
        out.setdefault(lid, []).append(r)
    return out


def ready(stem, blob, state_gis, layers_doc, needs_rows):
    """{layer id: [kinds]} for one state; kinds = missing, short, bot, hand, hand-held. blob None = no saved copy.
    hand = a person's download is open and the copy holds NONE of the layer (a real download);
    hand-held = a person's download is open but the copy already holds the layer (the row was never closed; Fable, 19 Nov)."""
    L = layers_doc.get('layers') or {}
    rows = layer_rows(blob) if blob is not None else collections.Counter()
    mine = key_layers(stem, state_gis, layers_doc)
    wait = {}
    for lid, rs in _waiting(stem, state_gis, layers_doc, needs_rows).items():
        for r in rs:
            if r.get('who') == 'bot' and r.get('status') in BOT_WAITING:
                wait.setdefault(lid, set()).add('bot')
            elif r.get('who') == 'person' and r.get('status') == 'open':
                wait.setdefault(lid, set()).add('hand')
    out = {}
    for lid in mine + sorted(set(wait) - set(mine)):
        kinds = []
        got = rows.get(lid, 0)
        total = (L.get(lid) or {}).get('expected_count')
        if total is None:
            total = (L.get(f'{stem}.{lid}') or {}).get('expected_count')
        if got == 0:
            kinds.append('missing')
        elif total is not None and got < total:
            kinds.append('short')
        kinds += sorted(wait.get(lid, ()))
        if 'hand' in kinds:   # waiting for a person's download: that is why it is missing or short, and a hand download never blocks
            kinds = [k for k in kinds if k not in ('missing', 'short')]
            if got > 0:
                kinds = ['hand-held' if k == 'hand' else k for k in kinds]
        if kinds:
            out[lid] = kinds
    return out


def hand_downloads(stem, blob, state_gis, layers_doc, needs_rows):
    """The REAL hand downloads of one state (Fable, 19 Nov): open person rows whose layer the saved copy holds none of, with the
    links a person needs. [{area, layer, copy_rows, url, page, why, id}]"""
    rows = layer_rows(blob) if blob is not None else collections.Counter()
    out = []
    for lid, rs in sorted(_waiting(stem, state_gis, layers_doc, needs_rows).items()):
        if rows.get(lid, 0) > 0:
            continue
        for r in rs:
            if r.get('who') == 'person' and r.get('status') == 'open':
                u = str(r.get('url') or '')
                if not u and str(r.get('layer') or '').startswith('url:'):
                    u = str(r['layer'])[4:]
                out.append({'area': stem, 'layer': lid, 'copy_rows': 0, 'url': u, 'page': r.get('page') or '', 'why': (r.get('why') or '')[:200],
                            'id': r.get('id') or ''})
    return out


def blocks(kinds):
    """The first three kinds block (with KPC_READY_BLOCK on); a hand download does not."""
    return any(k in ('missing', 'short', 'bot') for k in kinds)


def load_json(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return default


def needs_rows(path):
    d = load_json(path, {}) if path else {}
    return (d.get('rows') if isinstance(d, dict) else d) or []
