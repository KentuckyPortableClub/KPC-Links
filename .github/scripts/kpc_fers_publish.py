#!/usr/bin/env python3
"""UPDATE PATHS FOR THE KENTUCKY 2-FER FILES AND THE HOURS (Nov 2 review, G10). Every part is OFF until Brandon says GO.

What it can update (one switch each; each switch is off | preview | on, default off):
  layer   KPC_FERS_LAYER     ky-overlaps.geojson (the map's Park Overlaps layer, also used by the planner and finder)
  gpx     KPC_FERS_GPX       KPC_KY_POTA_2fers_3fers.gpx  (built by the club's own .claude/build/fers/gpx.py)
  pdf     KPC_FERS_PDF       KPC_Kentucky_POTA_2fers_3fers_Guide.pdf (built by the club's own .claude/build/fers/guide.py)
  hours   KPC_HOURS_PUBLISH  kpc-ky-hours.json (hours and fees on the park pages)
  off = do nothing. preview = write the new file under preview/ only (nothing on the site changes). on = write the live file.

The 2-fer parts take ONLY spots listed in kpc-fers-reviewed.json "reviewed" (chat 8 check + Brandon's OK, written by HQ).
That list is empty today, so today they change nothing and say so. They only ADD: every hand-made row, field-checked pin
and existing feature is kept; a reviewed spot whose parks are already in the hand list is skipped (the hand row wins).
The hours part fills only EMPTY fields of rows that are not hand-done ('done'), from the hours bot's own lines (each with its
official page and read date). Nothing is fetched from the internet here.

  python3 kpc_fers_publish.py layer|gpx|pdf|hours [--data <KPC-Data dir>] [--repo <KPC-Links dir>]
Exit 0 always for 'nothing to do'; exit 1 (loud) when a guard refuses (a file would shrink or could not be read)."""
import datetime as dt, json, os, pathlib, shutil, subprocess, sys, tempfile

MODES = ('off', 'preview', 'on')
SWITCH = {'layer': 'KPC_FERS_LAYER', 'gpx': 'KPC_FERS_GPX', 'pdf': 'KPC_FERS_PDF', 'hours': 'KPC_HOURS_PUBLISH'}
TARGET = {'layer': 'ky-overlaps.geojson', 'gpx': 'KPC_KY_POTA_2fers_3fers.gpx',
          'pdf': 'KPC_Kentucky_POTA_2fers_3fers_Guide.pdf', 'hours': 'kpc-ky-hours.json'}
TODAY = dt.date.today().isoformat()


def say(kind, title, msg):
    print(f'::{kind} title={title}::{msg}', flush=True)


def mode_of(part):
    m = (os.environ.get(SWITCH[part]) or 'off').strip().lower()
    if m not in MODES:
        say('warning', SWITCH[part], f"unknown value '{m}'; treated as off")
        m = 'off'
    return m


def out_path(repo, part, mode):
    if mode == 'on': return repo / TARGET[part]
    p = repo / 'preview' / TARGET[part]
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read_json(p):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception as e:
        say('error', 'read', f'could not read {p}: {e}')
        sys.exit(1)


def reviewed_spots(repo, data):
    """-> (list of KPC-Data spots that are in the reviewed list, {id: review value}). Missing ids are reported."""
    rev = read_json(repo / 'kpc-fers-reviewed.json').get('reviewed') or {}
    if not rev:
        return [], rev
    spots = {s.get('id'): s for s in read_json(data / 'data/fers/US-KY.json').get('spots') or []}
    got = []
    for sid in sorted(rev):
        s = spots.get(sid)
        if not s:
            say('warning', 'reviewed list', f"'{sid}' is reviewed but no longer in KPC-Data (its outline changed: it needs a new review)")
        elif not str(s.get('status', '')).startswith(('candidate', 'very tight')):
            say('warning', 'reviewed list', f"'{sid}' is reviewed but KPC-Data now says: {s.get('status')}; skipped")
        else:
            got.append(s)
    return got, rev


def ring(pts):
    pts = [list(p) for p in pts]
    return pts + [pts[0]] if pts and pts[0] != pts[-1] else pts


def feature(s, review):
    refs = s['refs']; names = s.get('names') or {}
    if s.get('kind') in ('trail', 'river'):
        geom = {'type': 'LineString', 'coordinates': [list(p) for p in s['shape']]}
    else:
        geom = {'type': 'Polygon', 'coordinates': [ring(s['shape'])]}
    return {'type': 'Feature', 'geometry': geom, 'properties': {
        'kind': '3fer' if len(refs) >= 3 else '2fer', 'acres': round(s.get('acres') or 0),
        'areas': [names.get(r, r) for r in refs], 'types': [s.get('kind', '')] * len(refs),
        'pota': [[r, names.get(r, r)] for r in refs], 'kff': [], 'sota': [],
        'spot_id': s['id'], 'reviewed': review if isinstance(review, str) else json.dumps(review)[:200],
        'source': 'KPC-Data data/fers/US-KY.json (Park Overlap Finder, reviewed)'}}


def refset(refs):
    return frozenset(r for r in refs if r.startswith('US-'))


def do_layer(repo, data, mode):
    spots, rev = reviewed_spots(repo, data)
    cur = read_json(repo / TARGET['layer']); feats = cur.get('features') or []
    if not spots:
        say('notice', 'Park Overlaps layer', f'nothing reviewed yet; {TARGET["layer"]} left as it is ({len(feats)} features)')
        return 0
    have = {f['properties'].get('spot_id') for f in feats} | {refset(r for r, _ in f['properties'].get('pota') or []) for f in feats}
    add = [feature(s, rev[s['id']]) for s in spots if s['id'] not in have and refset(s['refs']) not in have]
    new = dict(cur, features=feats + add, built=TODAY)
    if len(new['features']) < len(feats) * 0.5 and os.environ.get('KPC_FERS_ALLOW_SHRINK') != 'yes':
        say('error', 'Park Overlaps layer', 'the new file would have less than half the features; refused'); return 1
    if not add:
        say('notice', 'Park Overlaps layer', 'every reviewed spot is already on the map; nothing changed'); return 0
    out_path(repo, 'layer', mode).write_text(json.dumps(new, separators=(',', ':')) + '\n', encoding='utf-8')
    say('notice', 'Park Overlaps layer', f'{len(add)} reviewed spot(s) added ({mode}): ' + ', '.join(f['properties']['spot_id'] for f in add))
    return 0


def hand_entry(s, review):
    refs = s['refs']; names = s.get('names') or {}
    pts = []
    pin = (s.get('access_pin') or {}).get('at')
    if pin:
        pts.append({'la': pin[0], 'lo': pin[1], 'q': 'B', 'what': 'Closest spot inside every park to the public access (approximate)',
                    'note': (s.get('access_pin') or {}).get('note', '')})
    c = s.get('center')
    if c:
        pts.append({'la': c[0], 'lo': c[1], 'q': 'C', 'what': 'Middle of the overlap (approximate)', 'note': 'Not field checked.'})
    size = f"about {s['acres']} acres" if s.get('acres') else (f"about {round(s['len_m'] / 1609.3, 2)} mi" if s.get('len_m') else '')
    maps = s.get('maps') or []
    return {'type': '3-fer' if len(refs) >= 3 else '2-fer', 'how': f"Reviewed overlap ({s.get('kind', 'area')})",
            'refs': refs, 'names': [names.get(r, r) for r in refs], 'size': size, 'county': 'Kentucky', 'points': pts,
            'note': f"Reviewed in the Park Overlap Finder ({review if isinstance(review, str) else 'chat 8 check + Brandon OK'}). Spot {s['id']}.",
            **({'site': {'url': maps[0][1]}} if maps else {})}


def hand_list(repo, data, part):
    """-> (new fers.json dict, entries waiting for this part). Added entries carry 'g10': {part: date} so the GPX and the PDF
    each pick up every reviewed spot once, whichever switch is turned on first."""
    spots, rev = reviewed_spots(repo, data)
    hand = read_json(repo / '.claude/build/fers/fers.json')
    have = {refset(d['refs']) for d in hand['spots']}
    add = [dict(hand_entry(s, rev[s['id']]), g10={}) for s in spots if refset(s['refs']) not in have]
    new = dict(hand, spots=hand['spots'] + add)
    wait = [d for d in new['spots'] if 'g10' in d and part not in d['g10']]
    if add:
        new['changes'] = list(hand.get('changes') or []) + [f"{TODAY}: {len(add)} reviewed spot(s) added from the Park Overlap Finder (Nov 2 G10 path)"]
    return new, wait


def build_with(repo, part, new, mode):
    """Run the club's own builder on a copy, then copy the one output file to its place."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    b = tmp / '.claude/build/fers'; b.mkdir(parents=True)
    shutil.copy(repo / '.claude/build/fers' / ('gpx.py' if part == 'gpx' else 'guide.py'), b)
    (b / 'fers.json').write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding='utf-8')
    if (repo / 'KPC-logo.png').exists(): shutil.copy(repo / 'KPC-logo.png', tmp)
    cwd = tmp
    r = subprocess.run([sys.executable, str(b / ('gpx.py' if part == 'gpx' else 'guide.py'))], cwd=cwd, capture_output=True, text=True)
    print(r.stdout + r.stderr)
    made = tmp / TARGET[part]
    if r.returncode or not made.exists():
        say('error', TARGET[part], f'the builder stopped (exit {r.returncode}); nothing changed'); return 1
    if part == 'gpx':
        old_n = (repo / TARGET['gpx']).read_text(encoding='utf-8').count('<wpt ')
        new_n = made.read_text(encoding='utf-8').count('<wpt ')
        if new_n < old_n:
            say('error', TARGET['gpx'], f'the new GPX has fewer pins ({new_n}) than today ({old_n}); refused'); return 1
    shutil.copy(made, out_path(repo, part, mode))
    return 0


def do_hand(repo, data, part, mode):
    new, wait = hand_list(repo, data, part)
    if not wait:
        say('notice', TARGET[part], 'nothing reviewed (or every reviewed spot is already in this file); file left as it is'); return 0
    rc = build_with(repo, part, new, mode)
    if not rc:
        if mode == 'on':   # keep the hand list (the source of both files) in step, and mark this file as done for these spots
            for d in wait: d['g10'][part] = TODAY
            (repo / '.claude/build/fers/fers.json').write_text(json.dumps(new, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        say('notice', TARGET[part], f'{len(wait)} reviewed spot(s) added ({mode}): ' + ', '.join('+'.join(a['refs']) for a in wait))
    return rc


def short(lines, n=2):
    seen = []
    for x in lines or []:
        t = ' '.join(str(x.get('line', '')).split())
        if t and t not in seen: seen.append(t)
    return '; '.join(seen[:n])


def do_hours(repo, data, mode):
    bot = read_json(data / 'data/hours/US-KY.json'); site = read_json(repo / TARGET['hours'])
    parks = site.get('parks') or {}; changed = []
    lines = ['| Park | Name | New line(s) | Official page |', '|---|---|---|---|']
    for ref, b in sorted((bot.get('parks') or {}).items()):
        if b.get('status') != 'ok': continue
        row = parks.get(ref)
        if row is None or row.get('done'): continue   # hand-done rows are never touched; parks not on the site are not added
        filled = {}
        for field, src in (('hours', b.get('hours')), ('fee', b.get('fees'))):
            if not row.get(field) and src:
                filled[field] = short(src)
                url = src[0].get('url'); read = src[0].get('read') or bot.get('read')
        if not filled: continue
        row.update(filled)
        row.setdefault('link', url)
        row['src'] = {'url': url, 'read': read, 'by': 'hours bot (KPC-Data data/hours/US-KY.json)'}
        changed.append(ref); lines.append(f"| {ref} | {b.get('n', '')} | " + ' / '.join(f'{k}: {v}' for k, v in filled.items()).replace('|', '/') + f" | {url} |")
    if not changed:
        say('notice', 'Hours', 'no empty field has an official line waiting; kpc-ky-hours.json left as it is'); return 0
    site['updated'] = TODAY
    out_path(repo, 'hours', mode).write_text(json.dumps(site, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if mode == 'preview':   # one page Brandon can read line by line before any GO
        (repo / 'preview/kpc-ky-hours.changes.md').write_text('# Hours lines waiting for a GO (preview only)\n\n' + '\n'.join(lines) + '\n', encoding='utf-8')
    say('notice', 'Hours', f'{len(changed)} park(s) filled ({mode}): ' + ', '.join(changed))
    return 0


def main(argv):
    part = argv[0] if argv else ''
    if part not in SWITCH:
        print(__doc__); return 2
    opt = dict(zip(argv[1::2], argv[2::2]))
    repo = pathlib.Path(opt.get('--repo', '.')); data = pathlib.Path(opt.get('--data', 'kpc-data'))
    mode = mode_of(part)
    if mode == 'off':
        say('notice', SWITCH[part], f'switch is off (the default); {TARGET[part]} not touched'); return 0
    if part == 'layer': return do_layer(repo, data, mode)
    if part == 'hours': return do_hours(repo, data, mode)
    return do_hand(repo, data, part, mode)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
