#!/usr/bin/env python3
"""kpc_master_fill.py: THE master step (Nov 10: the master tool is the only owner of the saved copies).

Plain words. Before the US key's gate checks the saved copies, this step:
  1. lists the work: the needs-download rows for this job's states, the saved copies that are SHORT against their baseline (the
     same check the gate makes, read only here) or missing a layer, the checked downloads a person sent (hand-*.geojson.gz on the
     boundary-cache release), and with --refresh all every layer of every state (the fresh start);
  2. asks robots.txt of every host a bot may read (never before the host rules; a 403 counts as a no);
  3. has the key read those layers (its own reader, kpc_us_key.py in refill mode) into layer files, nothing merged yet;
  4. per layer file: the count must reach the layer's own total (fail closed), then `trim` (master records + the layer's count), then
     `raw-add` (the raw-file manifest), then the keep-bigger merge into the saved copy (a smaller read never replaces a saved layer);
  5. writes a row for every layer it may not or could not fetch (who = person / never / bot) for the needs-download list.
The existing save step uploads the saved copies this step changed. It never changes the gate or the cache baselines.
"""
import datetime, gzip, json, os, pathlib, shutil, subprocess, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_master as M  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)
def warn(t, m): print('::warning title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)


def short_states(cache, states, caches):
    """{st: (have, expected)} for saved copies under their gate baseline; a missing copy is ('missing', expected). Read only."""
    out = {}
    for st in states:
        p = pathlib.Path(cache) / f'US-{st}.json.gz'; exp = (caches.get(f'US-{st}') or {}).get('expected_count')
        if not p.exists(): out[st] = ('missing', exp); continue
        if exp is None: continue   # no baseline: the gate holds it; nothing a refill can prove
        try: M.check_saved_cache(p, exp)
        except M.ShortRead: out[st] = (len(M.load_saved(p).get('recs') or []), exp)
        except Exception: out[st] = ('unreadable', exp)  # noqa: BLE001
    return out


def _u(u): return M.re.sub(r'/query/?$', '', str(u or '').replace('svc:', '', 1).split('|')[0]).rstrip('/')


def new_layer_states(cache, states, us_layers_path, state_gis_path):
    """{st: [urls]}: a state-GIS layer (data/state-gis.json, where new layers arrive) with no records in the state's saved copy."""
    lj = M.load_json(us_layers_path, {}) or {}
    byurl = {_u(v[0]): k for k, v in lj.items() if isinstance(v, list) and v}
    sg = (M.load_json(state_gis_path, {}) or {}).get('states') or {}
    out = {}
    for st in states:
        cp = pathlib.Path(cache) / f'US-{st}.json.gz'
        if not cp.exists(): continue
        have = set(M.prefix_counts(M.load_saved(cp)))
        for l in sg.get(st) or []:
            u = _u(l.get('url'))
            if not u or not l.get('nm') or not M.re.search(r'/\d+$', u): continue
            if byurl.get(u) not in have: out.setdefault(st, []).append(u)
    return out


def layer_table(xs_path, us_layers_path, state_gis_path):
    """prefix -> {'url', 'name_field', 'label', 'states'}: the key's own table when it wrote one, else data/us-key/layers.json."""
    t = M.load_json(xs_path, {}) if xs_path else {}
    for k, v in (M.load_json(us_layers_path, {}) or {}).items():
        if isinstance(v, list) and v and k not in t: t[k] = {'url': v[0], 'name_field': v[1] if len(v) > 1 else '', 'label': v[2] if len(v) > 2 else '', 'states': None}
    return t


def robots_checker(offline=False):
    """robots_ok(url) for hosts live_ok allows. robots.txt is fetched only after live_ok said yes; a 401 / 403 / 5xx counts as a no."""
    if offline: return None
    fetch_robots = {}
    pacer = M.Pacer()

    def get(u):
        ok, _ = M.live_ok(u)
        if not ok: raise M.LiveNotAllowed(u)
        pacer.wait(M.parts(u)[0])
        req = M.urllib.request.Request(u, headers={'User-Agent': M.UA})
        try:
            with M.host_checked_opener().open(req, timeout=30) as r: return r.status, r.read(200000).decode('utf-8', 'replace')
        except M.urllib.error.HTTPError as e: return e.code, ''

    def ok(u):
        if not M.live_ok(u)[0]: return False
        return M.robots_allows(M.re.sub(r'^svc:', '', str(u)).split('|')[0], get, fetch_robots)
    return ok


def run_key_refill(states, layers_out, layers_in, force, saved_only_extra, key=None, env=None):
    e = dict(os.environ, **(env or {}))
    e.update({'STATES': ' '.join(states), 'GEO_CACHE_MODE': 'use', 'KPC_REFILL_ONLY': '1', 'KPC_LAYER_OUT': str(layers_out),
              'KPC_LAYER_IN': str(layers_in), 'KPC_REFILL_FORCE': force or ''})
    if saved_only_extra:
        base = os.environ.get('KPC_SAVED_ONLY_HOSTS') or ','.join(sorted(M.SAVED_ONLY_HOSTS))
        e['KPC_SAVED_ONLY_HOSTS'] = ','.join(sorted(set(base.split(',')) | set(saved_only_extra)))
    e.pop('KPC_MASTER_OWNS', None)
    return subprocess.run([sys.executable, str(key or HERE / 'kpc_us_key.py')], env=e).returncode


def apply_layer_file(path, cache, root, parks, raw_root=None):
    """Count check -> trim -> raw-add -> keep-bigger merge. Returns (ok, what)."""
    import kpc_master_cli as CLI
    meta, feats = M.read_layer_file(path)
    area, pre = meta.get('area'), meta.get('layer')
    exp = M.layer_file_expected(meta); got = int(meta.get('count_raw') if meta.get('count_raw') is not None else len(feats))
    if exp is None: return False, f'{area} {pre}: the layer did not report its own total, so the read cannot be checked: not merged'
    if got < exp: return False, f'{area} {pre}: read {got} of {exp} records: SHORT, not merged (fail closed)'
    key = f'{area}.{pre or "padus"}'
    rc = CLI.main(['trim', '--layer-key', key, '--input', str(path), '--expected', str(exp), '--parks', str(parks), '--area', area, '--root', str(root),
                   '--agency', str(meta.get('label') or ''), *(['--name-fields', meta['name_field']] if meta.get('name_field') else [])])
    if rc != 0: return False, f'{area} {pre}: trim refused it (exit {rc}): not merged'
    M.raw_add(path, (meta.get('raw') or {}).get('source') or meta.get('url') or meta.get('page') or 'unknown', root=raw_root or root)
    if meta.get('raw'):   # a person's download: their original file's name, size and sha256 (the PC helper measured it)
        doc = M.load_json(M.raw_manifest_path(raw_root or root), {'format': M.FORMAT, 'files': []}); r = meta['raw']
        doc['files'] = [x for x in doc['files'] if x['name'] != r.get('name')] + [{k: r.get(k) for k in ('name', 'size', 'sha256', 'source', 'date')}]
        doc['files'].sort(key=lambda x: x['name']); M.raw_manifest_path(raw_root or root).write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    cp = pathlib.Path(cache) / f'{area}.json.gz'
    if not cp.exists(): return False, f'{area}: no saved copy to merge into (the gate holds it)'
    blob = M.load_saved(cp)
    new = [(ft.get('properties') or {}).get('_kpc') for ft in feats]
    new = [r for r in new if r]
    blob2, what = M.merge_saved_layer(blob, pre, new)
    if blob2 is not blob: M.save_saved(cp, blob2)
    return True, f'{area} {what}'


def official_files(rows, dest, robots=None):
    """Nov 10: download each open bot row's official direct file once (kpc_master.download_official_file: live_ok, robots.txt,
    pacing). Returns [(row, facts or None)]. A file a bot may not fetch is skipped, never retried another way."""
    out, seen, pacer = [], {}, M.Pacer()
    for r in rows:
        f = M.direct_file_of(r)
        if not f or r.get('who') != 'bot' or r.get('status', 'open') != 'open': continue
        if f in seen: out.append((r, seen[f])); continue
        name = M.re.sub(r'[^A-Za-z0-9._-]+', '_', f"{r.get('area')}.{r.get('layer')}.{M.parts(f)[1].rstrip('/').split('/')[-1] or 'file'}")[:150]
        try: seen[f] = M.download_official_file(f, pathlib.Path(dest) / name, pacer=pacer)
        except Exception as e: warn('Master step', f"{r.get('id')}: official file not downloaded ({e})"); seen[f] = None  # noqa: BLE001
        out.append((r, seen[f]))
    return out


def fill(a):
    states = [s for s in (a.states or '').split() if s and s != 'KY']
    root = pathlib.Path(a.root); doc = M.load_layers(root); caches = doc.get('caches') or {}
    work = pathlib.Path(a.work); lin, lout = work / 'in', work / 'out'
    for d in (lin, lout):
        shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True, exist_ok=True)
    needs = M.load_needs(a.needs) if a.needs else M.load_needs(None)
    open_rows = [r for r in needs['rows'] if r.get('status') == 'open' and str(r.get('area', '')).startswith('US-') and r['area'][3:] in states]
    # the checked downloads a person sent (PC helper): hand-US-XX.<prefix>.geojson.gz; one already recorded (same sha256) is not applied twice
    applied = {r.get('sha256') for r in M.load_json(M.raw_manifest_path(root), {'files': []}).get('files', [])}
    hand = []
    for p in sorted(pathlib.Path(a.hand).glob('hand-US-*.geojson.gz')) if a.hand else []:
        nm = p.name[len('hand-'):]; st = nm[3:5]
        if st not in states: continue
        if M.sha256_file(p) in applied: continue
        meta, _ = M.read_layer_file(p)
        if (meta.get('raw') or {}).get('sha256') in applied: continue
        shutil.copy(p, lin / nm); hand.append(nm)
    short = short_states(a.cache, states, caches)
    refresh = a.refresh == 'all'
    new = new_layer_states(a.cache, states, a.us_layers, a.state_gis)
    todo = sorted(set(short) | {st for st, us in new.items() if any(M.live_ok(u)[0] for u in us)} | {r['area'][3:] for r in open_rows} | {n[3:5] for n in hand} | (set(states) if refresh else set()))
    todo = [s for s in todo if short.get(s, (0,))[0] != 'missing']   # no saved copy at all: the build makes the first one
    force = 'all' if refresh else ' '.join(sorted({r['layer'] for r in open_rows if r.get('who') == 'bot' and r.get('layer')}))
    if not a.no_key:   # the key's own layer table first (no state, no request: the key only writes xs.json and stops)
        run_key_refill(['ZZ'], lout, lin, '', set(), key=a.key)
    table = layer_table(lout / 'xs.json', a.us_layers, a.state_gis)
    robots = robots_checker(a.offline)
    blocked_hosts = set()
    if robots is not None:
        hosts = {}
        for v in table.values():
            u = v.get('url') or ''
            if (v.get('states') is None or set(v['states']) & set(todo)) and M.live_ok(u)[0]: hosts.setdefault(M.parts(u)[0], u)
        for h, u in sorted(hosts.items()):
            if not robots(u): blocked_hosts.add(h)
        if blocked_hosts: notice('Master step', 'robots.txt says no (or 403) for: ' + ' '.join(sorted(blocked_hosts)) + ' - those layers stay saved-copy only and go to the list')
    notice('Master step', f"states to refill: {' '.join(todo) or 'none'}; short now: {', '.join(f'{k} {v[0]}/{v[1]}' for k, v in sorted(short.items())) or 'none'}; "
                          f"hand files: {len(hand)}; open rows: {len(open_rows)}; refresh: {'all' if refresh else 'no'}")
    results, rows = [], []
    if todo and not a.no_key and not a.offline:
        rc = run_key_refill(todo, lout, lin, force, blocked_hosts, key=a.key)
        if rc: warn('Master step', f'the key reader stopped (exit {rc}); the layer files it wrote are still checked one by one')
    table = layer_table(lout / 'xs.json', a.us_layers, a.state_gis)
    done = set()
    for lf in sorted(lout.glob('US-*.geojson.gz')):
        ok, what = apply_layer_file(lf, a.cache, root, a.parks)
        meta, _ = M.read_layer_file(lf); k = f"{meta.get('area')}|{meta.get('layer')}"
        results.append((ok, what)); (notice if ok else warn)('Master step', what)
        if ok: done.add(k)
        else:
            u = meta.get('url') or (table.get(meta.get('layer')) or {}).get('url', '')
            rows.append(M.needs_row(meta.get('area'), meta.get('layer'), u, what, 'master', who='bot' if meta.get('source') == 'live' else 'person',
                                    expected=M.layer_file_expected(meta), have=None))
    # what the bots may not or could not fetch, where it is needed. Nov 10 (actually missing): a layer is listed only when the
    # live key joins a park to a record of it that the saved copy does not hold (data/us-key/US-XX.json against the copy), or
    # when the copy has nothing at all from a layer of this state's own (a new layer, never read). A short copy alone is not a
    # reason: its missing records may sit in no joined layer, and then no one is asked for anything.
    short_after = short_states(a.cache, todo, caches)
    prev_rows = {M.needs_key(r): r for r in needs['rows']}
    for st in states:
        cp = pathlib.Path(a.cache) / f'US-{st}.json.gz'
        if not cp.exists(): continue
        blob = M.load_saved(cp); have = M.prefix_counts(blob)
        miss = M.joined_missing(pathlib.Path(a.us_key) / f'US-{st}.json', blob) if getattr(a, 'us_key', None) else {}
        for pre, v in sorted(table.items()):
            if v.get('states') is not None and st not in v['states']: continue
            u = v.get('url') or ''
            if not u or f'US-{st}|{pre}' in done: continue
            if pre == '': continue   # PAD-US comes from an allowed host; a by-id read fills it
            n = have.get(pre, 0); gone = miss.get(pre, 0)
            prev = prev_rows.get(f'US-{st}|{pre}')
            fileu = M.direct_file_of(prev) if prev else None
            who, why = M.who_for(u, (lambda x: M.parts(x)[0] not in blocked_hosts), file_url=fileu)
            if who == 'bot' and not fileu: continue
            if prev and (prev.get('status') == 'held' or (prev.get('status') == 'done' and n >= int(prev.get('expected') or 0) and not gone)): continue   # done (and still whole) / a person held it
            mine = n > 0 or (v.get('states') is not None) or pre.startswith(f'sg{st.lower()}')   # this layer is this state's (not a national layer with nothing here)
            if not mine: continue
            if gone: need = f"the live key joins {gone} record(s) of this layer that the saved copy of US-{st} does not hold"
            elif n == 0: need = 'the saved copy has no records from this layer (a new layer, or never read)'
            else: continue   # the saved copy holds every record the key joins from this layer: nothing is missing
            rows.append(M.needs_row(f'US-{st}', pre, u, need, 'master', who=who, expected=(n + gone) if gone else None, have=n, note=why + ((' direct file: ' + fileu) if fileu and fileu not in why else '')))
    if getattr(a, 'official_files', False) and not a.offline:   # Nov 10: the official-file download path (the fresh-start run); same checks as every read
        got = official_files(rows + [r for r in needs['rows'] if r.get('status') == 'open'], work / 'files', robots)
        for r, facts in got:
            if facts: M.raw_add_facts(facts, root=root); notice('Master step', f"{r['id']}: official file {facts['name']} ({facts['size']} bytes) downloaded; the PC helper's check packs it")
    for k in sorted(done):
        ar, pre = k.split('|', 1)
        rows.append({**M.needs_row(ar, pre, (table.get(pre) or {}).get('url', ''), 'refilled and checked by the master step', 'master', who='bot'), 'status': 'done'})
    try:   # Nov 10: give each row its official download source (data/outlines/download-sources.json) and whether a bot may check it
        import kpc_master_watch as W
        W.link_rows(root / 'download-sources.json', rows)
    except Exception as e: warn('Master step', f'download sources not linked ({e})')  # noqa: BLE001
    if a.out_rows:
        pathlib.Path(a.out_rows).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out_rows).write_text(json.dumps({'format': M.NEEDS_FORMAT, 'rows': rows}, indent=1, sort_keys=True))
    c = {}
    for r in rows: c[(r['who'], r['status'])] = c.get((r['who'], r['status']), 0) + 1
    notice('Master step', f"{sum(1 for x in results if x[0])} layer(s) merged, {sum(1 for x in results if not x[0])} refused; rows: " + (', '.join(f'{w} {s} {n}' for (w, s), n in sorted(c.items())) or 'none'))
    return 0


def collect(a):
    """Join job: the parts' master records, layer counts, raw-manifest rows and needs rows into one place."""
    root = pathlib.Path(a.root); doc = M.load_layers(root); raw = M.load_json(M.raw_manifest_path(root), {'format': M.FORMAT, 'files': []})
    rows = []
    for d in sorted(pathlib.Path(p) for p in a.parts):
        if not d.is_dir(): continue
        for f in sorted(d.glob('US-*.geojson.gz')): shutil.copy(f, root / f.name)
        sq = d / 'solver-queue'
        if sq.is_dir():
            (root / 'solver-queue').mkdir(parents=True, exist_ok=True)
            for f in sq.glob('*.csv'): shutil.copy(f, root / 'solver-queue' / f.name)
        L = M.load_json(d / 'layers.json', {}).get('layers') or {}
        for k, v in L.items():
            if k.startswith('US-') and '.' in k: doc['layers'][k] = v   # only the layers the master step trimmed (area.prefix keys)
        for r in M.load_json(d / 'raw-manifest.json', {}).get('files') or []:
            raw['files'] = [x for x in raw['files'] if x['name'] != r['name']] + [r]
        rows += M.load_json(d / 'needs-rows.json', {}).get('rows') or []
    raw['files'].sort(key=lambda r: r['name'])
    M.save_layers(doc, root); M.raw_manifest_path(root).write_text(json.dumps(raw, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    if a.needs_out:
        nd = M.load_needs(a.needs_in) if a.needs_in else M.load_needs(None)
        nd, add, upd = M.merge_needs(nd, rows)
        M.save_needs(nd, a.needs_out)
        notice('Master step', f'needs-download rows from this build: {len(rows)} ({add} new, {upd} updated); open: {M.needs_summary(nd)}')
    return 0
