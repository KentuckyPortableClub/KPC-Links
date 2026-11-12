#!/usr/bin/env python3
"""kpc_master_cli.py: the trim tool and the checks for the outline master records. Plain words are in data/outlines/README.md.

  trim        read a layer file (GeoJSON / Esri JSON / Shapefile / GDB) or a live layer URL, keep ONLY the POTA parks' geometry, write master
              records, send the rest to a solver-queue CSV. Fails closed on a short read.
  check       is every master file whole, every hash right, nothing from WDPA, no raw layer files tracked, (optionally) no short saved copy?
  gate        before a build reads its SAVED copies (cache/us, cache/ca, cache/world): a copy shorter than the layer's own baseline is moved aside
              (cache/<x>/short/) and named in a report. Exit 7 = at least one short copy. No baseline yet = held too (exit 7), unless
              --first-ok: then the copy passes with a notice and the first good full read records its baseline (`baseline`).
  plan        read master first: which layers (not states) need a live re-read, and why.
  raw-add     add a downloaded raw layer file to the manifest (name, size, sha256, source, date). The file itself is never added to git.
  fill        THE master step (Nov 10): refill / verify the saved copies before the gate; the one writer of the saved copies.
              Hand files for any area (hand-<US-XX|CA-XX|CA-ALL|W-XX>.<layer>.geojson.gz): US ones are merged; Canada / world ones
              are checked into a per-area store (their builders do not read it yet: data/outlines/README.md).
  baseline    record a saved copy's first baseline (only when it has none; never lowered, never replaced): the first good full read.
  part        a build job: write ONLY its own states into its part (outline files; layer, cache and raw rows that changed).
  collect     the join job: put the build parts together per state (each from its owning part; a conflict fails, exit 1).
  needs       merge rows into a needs-download list, or print how many rows are open (bot / person / never).
  bundle-manifest  Nov 11: write a hand bundle's own manifest into it (trimmed to parks, per layer counts, who / when, sha256); --check, --show.
              The gate (--allow-trimmed) checks a trimmed copy against that manifest, exactly; --approved reads a SIGNED *.approved.json.
  save-check  before an upload of saved copies: refuse (exit 1, names the file) one that fails the gate baseline or holds fewer records,
              in total or for any layer, than the release copy (--against DIR); --ok-list FILE gets the ones that may be uploaded.
  resave      Nov 11: write every area file again through save_area: a park the key grades pin is left out, a record graded higher
              than the key allows is saved as approximate, and an area over 1 MB
              is written in parts (US-AK.geojson.gz + US-AK.p2.geojson.gz ...). --dry-run says what would change and writes nothing.
  wdpa-lookup managing agency of a park from a Protected Planet / WDPA file. Private output only, no geometry.

Exit codes: 0 ok | 1 check failed | 2 SHORT read | 3 cannot verify (no expected count) | 4 licence block | 5 live read not allowed | 6 shrink held | 7 short saved copy
"""
import argparse, csv, datetime, glob, gzip, json, os, pathlib, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_master as M  # noqa: E402
from kpc_scrub import notice_text, clip   # Nov 12: every log line scrubbed first, then cut


def notice(t, m): print('::notice title=%s::%s' % (t, notice_text(m, 20000)), flush=True)   # Nov 12: scrubbed (archive token)
def warn(t, m): print('::warning title=%s::%s' % (t, notice_text(m, 20000)), flush=True)
def err(t, m): print('::error title=%s::%s' % (t, notice_text(m, 20000)), flush=True)


def read_parks(path):
    """KPC-Data locations-pota.json rows: ['POTA', ref, name, lat, lon, url]. Read only; a pin is never changed."""
    rows = M.load_json(path, [])
    return [(r[1], r[2], float(r[3]), float(r[4])) for r in rows if isinstance(r, list) and len(r) >= 5 and r[0] == 'POTA']


def read_file(path):
    """-> (features as {'attributes'|'properties', 'geometry': GeoJSON}, how). Esri JSON geometry is converted; a Shapefile needs pyshp, a GDB needs ogr2ogr."""
    p = pathlib.Path(path); low = p.name.lower()
    if low.endswith('.shp') or low.endswith('.shp.zip') or low.endswith('.zip') or low.endswith('.gdb') or low.endswith('.gpkg'):
        try:
            import shapefile  # pyshp
            if low.endswith('.shp'):
                sf = shapefile.Reader(str(p)); out = []
                for sr in sf.shapeRecords():
                    gj = sr.shape.__geo_interface__
                    out.append({'properties': sr.record.as_dict(), 'geometry': gj if gj.get('type') in ('Polygon', 'MultiPolygon', 'Point') else None})
                return out, 'shapefile'
        except ImportError: pass
        og = shutil.which('ogr2ogr')
        if not og: raise SystemExit('this input type needs pyshp (.shp) or ogr2ogr (.gdb / .gpkg / .zip) on this machine; neither is installed. Convert to GeoJSON first.')
        with tempfile.TemporaryDirectory() as t:
            out = pathlib.Path(t) / 'x.geojson'
            subprocess.run([og, '-f', 'GeoJSON', '-t_srs', 'EPSG:4326', str(out), str(p)], check=True)
            return read_file(out)
    op = gzip.open if low.endswith('.gz') else open
    with op(p, 'rt', encoding='utf-8') as f: doc = json.load(f)
    feats = doc.get('features') if isinstance(doc, dict) else doc
    if isinstance(doc, list) and doc and isinstance(doc[0], dict) and 'features' in doc[0]: feats = [x for pg in doc for x in pg.get('features', [])]   # pages
    out = []
    for ft in feats or []:
        if 'attributes' in ft: out.append({'attributes': ft.get('attributes') or {}, 'geometry': M.esri_to_geojson(ft.get('geometry'))})
        else: out.append({'properties': ft.get('properties') or {}, 'geometry': ft.get('geometry')})
    return out, 'esri-json' if feats and 'attributes' in feats[0] else 'geojson'


def cmd_trim(a):
    root = pathlib.Path(a.root) if a.root else M.OUTLINES
    doc = M.load_layers(root); L = dict(doc['layers'].get(a.layer_key) or {})
    for k in ('agency', 'license', 'g', 'record_id_field', 'detail', 'circle_m'):
        v = getattr(a, k, None)
        if v not in (None, ''): L[k] = v
    for k in ('id_fields', 'name_fields'):
        v = getattr(a, k)
        if v: L[k] = v.split(',')
    areas = [x for x in (a.area or '').split(',') if x] or L.get('areas') or []
    L['areas'] = areas
    try:
        if M.is_wdpa(a.layer_key, L.get('url'), L.get('agency'), a.input, L.get('license')):
            raise M.LicenseBlocked('this looks like Protected Planet / WDPA data: its geometry cannot be used here. Use wdpa-lookup (agency only, private).')
        if a.url:
            ok, why = M.live_ok(a.url)
            if not ok: raise M.LiveNotAllowed(why + '. Give a saved copy with --input instead.')
            fetch = M.http_fetcher(); feats_raw, info = M.read_layer(a.url, fetch, want_page=a.page, out_fields='*')
            feats = [{'attributes': f.get('attributes') or {}, 'geometry': M.esri_to_geojson(f.get('geometry'))} for f in feats_raw]
            expected, last_edit, how = info['count'], info.get('last_edit'), 'live'; L['url'] = a.url
        else:
            feats, how = read_file(a.input)
            expected = a.expected if a.expected is not None else L.get('expected_count'); last_edit = L.get('last_edit')
            if expected is None:
                err('trim', f'{a.input}: no expected count (pass --expected N from the layer\'s own total, or use --url). A read that cannot be checked is refused.'); return 3
            M.check_complete(expected, len(feats), a.input)
    except M.ShortRead as e: err('trim SHORT READ', e); return 2
    except M.LicenseBlocked as e: err('trim licence', e); return 4
    except M.LiveNotAllowed as e: err('trim live read', e); return 5
    parks = read_parks(a.parks)
    today = datetime.date.today().isoformat()
    cfg = {'id_fields': L.get('id_fields') or [], 'name_fields': L.get('name_fields') or [], 'record_id_field': L.get('record_id_field'), 'g': L.get('g', 'official'),
           'agency': L.get('agency', ''), 'layer_url': L.get('url') or ('file:' + os.path.basename(a.input or '')), 'license': L.get('license', ''), 'detail': float(L.get('detail', M.DEFAULT_DETAIL)),
           'circle_m': L.get('circle_m')}
    recs, queue = M.trim(parks, feats, cfg, today, source_count=len(feats))
    by_area = {}
    for ref, r in recs.items(): by_area.setdefault(areas[0] if len(areas) == 1 else ref.split('-')[0], {})[ref] = r   # one area given = that file; else by country prefix
    notes = {}
    for area, new in by_area.items():
        have = M.load_area(area, root)
        for ref, r in new.items():
            keep, what = M.merge(have.get(ref), r); have[ref] = keep; notes[what.split(':')[0].split(' ')[0]] = notes.get(what.split(':')[0].split(' ')[0], 0) + 1
        if not a.dry_run: M.save_area(area, have, root)
    try: M.accept_baseline(doc, a.layer_key, {'url': L.get('url', ''), 'agency': L.get('agency', ''), 'license': L.get('license', ''), 'areas': areas, 'g': L.get('g', 'official'),
                                              'id_fields': cfg['id_fields'], 'name_fields': cfg['name_fields'], 'record_id_field': cfg['record_id_field'],
                                              'last_edit': last_edit, 'read_date': today, 'source_count': len(feats), 'matched': len(recs), 'queued': len(queue),
                                              'read_how': how}, expected, accept_shrink=a.accept_shrink)
    except M.ShrinkHeld as e: err('trim shrink held', e); return 6
    if not a.dry_run:
        M.save_layers(doc, root)
        M.write_queue(root / 'solver-queue' / f'{a.layer_key}.csv', queue)   # Nov 11: deduped, and not rewritten when nothing changed
    notice('trim', f'{a.layer_key}: read {len(feats)} of {expected}; matched {len(recs)} parks ({sum(1 for r in recs.values() if r["via"] == "id")} by id), '
                   f'{len(queue)} to the solver queue; {notes}' + (' (dry run, nothing written)' if a.dry_run else ''))
    return 0


def tracked_files(repo):
    out = subprocess.run(['git', '-C', str(repo), 'ls-files', '-z'], capture_output=True, check=True).stdout.decode().split('\0')
    return [(f, os.path.getsize(pathlib.Path(repo) / f)) for f in out if f and (pathlib.Path(repo) / f).is_file()]


def cmd_check(a):
    root = pathlib.Path(a.root) if a.root else M.OUTLINES; bad, suspect = [], []
    doc = M.load_layers(root)
    for p in sorted(root.glob('*.geojson.gz')):
        if M.is_part_file(p.name): continue   # Nov 11: part 2+ of an area is read with its part 1
        try: recs = M.load_area(p.name[:-len('.geojson.gz')], root)
        except Exception as e: bad.append(f'{p.name}: unreadable ({e})'); continue
        for ref, r in recs.items():
            if M.content_hash(r) != r.get('hash'): bad.append(f'{p.name} {ref}: content hash does not match')
            try: M.assert_public_safe(r)
            except M.LicenseBlocked as e: bad.append(str(e))
            if r.get('g') not in M.RANK: bad.append(f'{p.name} {ref}: unknown g {r.get("g")!r}')
    for key, L in doc['layers'].items():
        if L.get('source_count') is not None and L.get('expected_count') is not None and L['source_count'] < L['expected_count']:
            bad.append(f'layer {key}: baseline is SHORT (source {L["source_count"]} of {L["expected_count"]})')
        if M.is_wdpa(key, L.get('url'), L.get('agency'), L.get('license')): bad.append(f'layer {key}: Protected Planet / WDPA in a public manifest')
        if L.get('source_count') is not None and L.get('expected_count') is not None and L['source_count'] > L['expected_count']:
            suspect.append(f"{key} (expected {L['expected_count']}, the file held {L['source_count']})")   # e.g. a count capped at 200 before the plain count query
    if a.cache:
        for f in sorted(glob.glob(os.path.join(a.cache, '*.json.gz'))):
            area = os.path.basename(f)[:-len('.json.gz')]; exp = (doc.get('caches') or {}).get(area, {}).get('expected_count')
            if exp is None:
                bad.append(f'{area}: no baseline in the manifest (caches): held, not used')
                continue
            try: M.check_saved_cache(f, exp)
            except M.ShortRead as e: bad.append(str(e))
    if a.repo:
        for f in M.raw_in_repo(tracked_files(a.repo)): bad.append(f'{f}: a raw layer file must not be tracked (use the raw manifest)')
    for b in bad: err('master check', b)
    if suspect: warn('master check suspect baseline', f'{len(suspect)} layer baseline(s) lower than the records the file held (the next verified full read re-records them): ' + '; '.join(suspect))
    notice('master check', ('all clear' if not bad else f'{len(bad)} problem(s)') + (f'; {len(suspect)} suspect baseline(s): ' + ', '.join(x.split(' ')[0] for x in suspect) if suspect else ''))
    return 0 if not bad else 1


def cmd_resave(a):
    """Nov 11 (KPC owner, 2026-11-11): every area file through save_area once (pin-graded parks out, parts when over 1 MB)."""
    root = pathlib.Path(a.root) if a.root else M.OUTLINES; key = pathlib.Path(a.key) if a.key else root.parent / 'us-key'
    areas = [x for x in (a.areas or '').replace(',', ' ').split() if x] or sorted(p.name[:-len('.geojson.gz')] for p in root.glob('*.geojson.gz')
                                                                            if not M.is_part_file(p.name) and M.AREA_RE.match(p.name[:-len('.geojson.gz')]))
    total = lowered = 0
    for area in areas:
        if not M.area_path(area, root).is_file(): print(f'{area}: no outline file, nothing to do'); continue
        recs = M.load_area(area, root); _, drop, low = M.key_fix(area, recs, key); drop, low = sorted(drop), sorted(low); total += len(drop); lowered += len(low)
        if a.dry_run:
            if drop: print(f'{area}: {len(recs)} outline(s); would drop {len(drop)} the key grades pin: ' + ' '.join(drop))
            if low: print(f'{area}: would save {len(low)} as approximate (the key grades them approximate): ' + ' '.join(low))
            continue
        before = [f.read_bytes() for f in M.area_files(area, root)]
        M.save_area(area, recs, root, key_dir=key)
        after = [f.read_bytes() for f in M.area_files(area, root)]
        if after != before: print(f'{area}: written ({len(recs) - len(drop)} outline(s) in {len(after)} file(s)' + (f'; dropped {len(drop)}: ' + ' '.join(drop) if drop else '')
                                  + (f'; approximate now {len(low)}: ' + ' '.join(low) if low else '') + ')')
    notice('resave', f'{len(areas)} area(s); {total} outline(s) of parks the key grades pin ' + ('would be dropped' if a.dry_run else 'dropped')
           + f'; {lowered} outline(s) ' + ('would be saved as approximate (dry run, nothing written)' if a.dry_run else 'saved as approximate'))
    return 0


def cmd_gate(a):
    """Nov 11 (KPC owner, 2026-11-11): each copy is checked against its own manifest when it says it was trimmed to parks (only with
    --allow-trimmed), else an owner-approved baseline (--approved, a signed *.approved.json), else the full baseline (layers.json
    caches). Always exact: fewer records = SHORT = moved aside. A copy refused for any reason is moved aside too. Nothing is written
    to layers.json: a trimmed copy never replaces a full copy's baseline."""
    root = pathlib.Path(a.root) if a.root else M.OUTLINES; doc = M.load_layers(root); caches = doc.get('caches') or {}
    cache = pathlib.Path(a.cache); short = []
    approved, why = M.load_approved_baselines(a.approved) if a.approved else ({}, '')
    if a.approved and why and os.path.exists(a.approved): err('master gate approved baselines', why + ': the layers.json baselines apply (fail closed)')
    elif approved: notice('master gate approved baselines', f'{len(approved)} owner-approved baseline(s) read from {os.path.basename(a.approved)}: ' + ' '.join(sorted(approved)))

    def aside(f, stem):
        (cache / 'short').mkdir(exist_ok=True); shutil.move(str(f), str(cache / 'short' / f.name)); short.append(stem)
    for f in sorted(cache.glob('*.json.gz')):
        stem = f.name[:-len('.json.gz')]
        try: blob = M.load_saved(f); sha = M.sha256_file(f)
        except Exception as e: err('master gate', f'{f.name}: unreadable ({e})'); aside(f, stem); continue  # noqa: BLE001
        how, exp, why = M.gate_baseline(f.name, blob, sha, caches, approved, allow_trimmed=a.allow_trimmed)
        if how == 'refuse' and a.first_ok and (caches.get(stem) or {}).get('expected_count') is None and stem not in approved and not M.is_trimmed(blob):
            notice('master gate NO BASELINE YET', f'{stem}: no baseline in the manifest (caches) yet: used (--first-ok); the first good full read records it'); continue
        if how == 'refuse':
            err('master gate NO BASELINE' if 'no baseline' in why else 'master gate REFUSED', why); aside(f, stem); continue
        try:
            if how == 'manifest': M.check_against_manifest(f.name, blob)
            else: M.check_complete(exp, len(blob.get('recs') or []) if isinstance(blob.get('recs'), list) else 0, str(f))
            if how != 'full': notice('master gate', why + ('' if (caches.get(stem) or {}).get('expected_count') is None else f"; the full baseline {caches[stem]['expected_count']} is not used here and not changed"))
        except M.ShortRead as e: err('master gate SHORT', e); aside(f, stem)
        except M.MasterError as e: err('master gate REFUSED', e); aside(f, stem)
    if a.report and short: pathlib.Path(a.report).write_text('\n'.join(short) + '\n')
    notice('master gate', 'no short saved copy' if not short else f'SHORT saved copy moved aside: {" ".join(short)}')
    return 7 if short else 0


def save_check(path, against_dir, caches, assets=None, first_ok=False):
    """'' when a saved copy may replace the release copy; else why not. It must pass the gate's baseline check and hold at least as
    many records, in total and for every layer, as the release copy (downloaded into against_dir). No release copy: allowed only with
    first_ok, and (when the release's asset list is given) only when the release really has no such asset (owner rule, 2026-11-10)."""
    name = os.path.basename(path); stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else name
    try:
        if M.is_trimmed(M.load_saved(path)): return f'{name}: a trimmed copy (manifest says trimmed to parks): never uploaded over a release copy by a bot'
    except Exception as e: return f'{name}: unreadable ({e})'  # noqa: BLE001
    exp = (caches.get(stem) or {}).get('expected_count')
    if exp is None: return f'{name}: no baseline in the manifest (caches): the gate would hold it'
    try: tot_new = M.check_saved_cache(path, exp)
    except M.ShortRead as e: return str(e)
    except Exception as e: return f'{name}: unreadable ({e})'  # noqa: BLE001
    old_p = pathlib.Path(against_dir) / name
    if not old_p.is_file():
        if not first_ok: return f'{name}: the release copy was not downloaded to compare against'
        if assets is None: return f'{name}: the release asset list could not be read, so a first copy cannot be told from a failed download'
        if name in assets: return f'{name}: the release has this copy but its download failed: held, not replaced'
        return ''
    try: tot_old = len(M.load_saved(old_p).get('recs') or [])
    except Exception as e: return f'{name}: the release copy could not be read to compare ({e})'  # noqa: BLE001
    new, old = M.saved_counts(path), M.saved_counts(old_p)
    if tot_new < tot_old: return f'{name}: {tot_new} records, fewer than the release copy ({tot_old})'
    less = sorted(k for k in old if new.get(k, 0) < old[k])
    if less: return f'{name}: fewer records than the release copy for ' + ', '.join(f"{k or 'PAD-US'} ({new.get(k, 0)} < {old[k]})" for k in less[:10])
    return ''


def cmd_save_check(a):
    root = pathlib.Path(a.root) if a.root else M.OUTLINES; caches = M.load_layers(root).get('caches') or {}
    assets = None
    if a.assets:
        try: assets = set(open(a.assets, encoding='utf-8').read().split())
        except OSError: assets = None
    ok, bad = [], []
    for f in a.files:
        why = save_check(f, a.against, caches, assets, a.first_ok)
        if why: bad.append(why); err('save-check REFUSED', why)
        else: ok.append(f)
    if a.ok_list: pathlib.Path(a.ok_list).write_text(''.join(x + '\n' for x in ok))
    notice('save-check', f'{len(ok)} saved copy(ies) may be uploaded' + (f'; {len(bad)} refused' if bad else ''))
    return 1 if bad else 0


def cmd_baseline(a):
    """First baseline of a saved copy (owner rule, 2026-11-10): only when the manifest has none. It is the copy's record count, or the
    release copy's (--against DIR) when that is smaller, so the copy the gate reads next is never under it. An existing baseline is
    never lowered or replaced (a changed total goes through a person, as for layers)."""
    root = pathlib.Path(a.root) if a.root else M.OUTLINES; doc = M.load_layers(root); doc.setdefault('caches', {}); n = 0
    for f in a.files:
        name = os.path.basename(f); stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else name
        if (doc['caches'].get(stem) or {}).get('expected_count') is not None: notice('baseline', f'{stem}: has a baseline already; unchanged'); continue
        try: blob = M.load_saved(f); cnt = len(blob.get('recs') or [])
        except Exception as e: err('baseline', f'{name}: unreadable ({e}); no baseline recorded'); return 1  # noqa: BLE001
        if M.is_trimmed(blob): err('baseline', f'{name}: a trimmed copy (its manifest says so) never records a full baseline'); return 1
        old = pathlib.Path(a.against) / name if a.against else None
        if old is not None and old.is_file():
            try: cnt = min(cnt, len(M.load_saved(old).get('recs') or []))
            except Exception as e: err('baseline', f'{name}: the release copy could not be read ({e}); no baseline recorded'); return 1  # noqa: BLE001
        if cnt <= 0: err('baseline', f'{name}: no records; no baseline recorded'); return 1
        doc['caches'][stem] = {'expected_count': cnt, 'read_date': datetime.date.today().isoformat(), 'read_how': a.how}
        notice('baseline', f'{stem}: first baseline {cnt} records ({a.how})'); n += 1
    if n: M.save_layers(doc, root)
    return 0


def cmd_bundle_manifest(a):
    """Nov 11 (KPC owner, 2026-11-11): the step that makes a hand bundle (a W-XX / US-XX / CA-XX copy trimmed to the features near
    POTA parks) ends with this: it writes the copy's own manifest INTO the copy (per layer and total record count, 'trimmed', who
    made it and when, the records' sha256, optionally each source layer's full count), so the gate can check the copy exactly
    against what it was made with. Run it on the final file, right before the upload; any later change to the records needs a new
    manifest (--replace). --check checks, --show prints (both write nothing). Offline; standard library only."""
    full = {}
    for x in a.source_full:
        k, _, v = str(x).partition('=')
        if not k or not v.strip().isdigit(): err('bundle-manifest', f'--source-full {x!r}: use LABEL=N'); return 1
        full[k] = int(v)
    bad = 0
    for f in a.files:
        name = os.path.basename(f); stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else ''
        if not M.AREA_RE.match(stem): err('bundle-manifest', f'{name}: not a saved copy name (US-XX / CA-XX / CA-ALL / W-XX .json.gz)'); bad += 1; continue
        try: blob = M.load_saved(f)
        except Exception as e: err('bundle-manifest', f'{name}: unreadable ({e})'); bad += 1; continue  # noqa: BLE001
        if not isinstance(blob, dict) or not isinstance(blob.get('recs'), list) or not blob['recs']: err('bundle-manifest', f'{name}: no records'); bad += 1; continue
        if a.show:
            print(json.dumps({'file': name, 'records': len(blob['recs']), 'layers': M.copy_layer_counts(stem, blob), 'file_sha256': M.sha256_file(f),
                              'manifest': blob.get('manifest'), 'manifest_problems': M.manifest_problems(name, blob) if blob.get('manifest') else []}, indent=1, ensure_ascii=False)); continue
        if a.check:
            probs = M.manifest_problems(name, blob)
            if probs: err('bundle-manifest', f'{name}: ' + '; '.join(probs)); bad += 1
            else: notice('bundle-manifest', f"{name}: manifest matches ({blob['manifest']['total']} records, {'trimmed' if blob['manifest']['trimmed'] else 'full'})")
            continue
        if not str(a.by or '').strip(): err('bundle-manifest', 'say who made the copy (--by)'); return 1
        if blob.get('manifest') and not a.replace: err('bundle-manifest', f'{name}: has a manifest already (use --replace to write a new one)'); bad += 1; continue
        made = a.made or datetime.date.today().isoformat()
        try: datetime.date.fromisoformat(made)
        except ValueError: err('bundle-manifest', f'--made {made!r} is not a date'); return 1
        blob['manifest'] = M.make_manifest(name, blob, a.by, made, trimmed=not a.full, source_full=full, note=a.note)
        M.save_saved(f, blob)
        probs = M.manifest_problems(name, M.load_saved(f))
        if probs: err('bundle-manifest', f'{name}: the manifest written does not check ({"; ".join(probs)})'); bad += 1; continue
        notice('bundle-manifest', f"{name}: manifest written ({blob['manifest']['total']} records in {len(blob['manifest']['layers'])} layer(s), "
                                  f"{'trimmed to parks' if not a.full else 'full'}, by {a.by}, {made}); upload this file as it is now")
    return 1 if bad else 0


def cmd_plan(a):
    root = pathlib.Path(a.root) if a.root else M.OUTLINES; doc = M.load_layers(root)
    max_days = float(os.environ.get('KPC_MASTER_MAX_DAYS') or a.max_days)
    fetch = None if a.no_probe else M.http_fetcher()

    def probe(L):
        if fetch is None: return None
        try: i = M.layer_info(L['url'], fetch); return {'count': i['count'], 'last_edit': i['last_edit']}
        except Exception as e: warn('plan probe', f"{L.get('url')}: {clip(e, 120)}"); return None   # noqa: BLE001
    areas = a.areas.split(',') if a.areas else None
    if a.prefix: areas = sorted({x for L in doc['layers'].values() for x in L.get('areas') or [] if x.startswith(a.prefix)}) or ['(none)']
    rows = M.plan(doc, datetime.datetime.now(datetime.timezone.utc), max_days, probe, areas=areas)
    print(json.dumps(rows, indent=1))
    for r in rows:
        if r['action'] != 'use-master': notice('master plan', f"{r['layer']}: {r['action']} - {r['reason']}")
    if a.out: pathlib.Path(a.out).write_text(json.dumps(rows, indent=1))
    return 0


def cmd_raw_add(a):
    row = M.raw_add(a.file, a.source, root=pathlib.Path(a.root) if a.root else None); print(json.dumps(row)); return 0


def cmd_wdpa(a):
    ok, why = M.private_path_ok(a.out)
    if not ok: err('wdpa-lookup', why); return 4
    rows = M.load_json(a.input, [])
    rows = rows.get('features', rows) if isinstance(rows, dict) else rows
    rows = [(r.get('properties') or r.get('attributes') or r) for r in rows]
    out = M.wdpa_agency_lookup(rows)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for r in out for k in r})
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(out)
    notice('wdpa-lookup', f'{len(out)} rows (agency fields only, no geometry) written privately'); return 0


def cmd_needs(a):
    doc = M.load_needs(a.list); rows = []
    for p in a.add: rows += M.load_json(p, {}).get('rows') or []
    if rows:
        doc, add, upd = M.merge_needs(doc, rows); changed = M.save_needs(doc, a.list)
        notice('needs-download', f'{add} new, {upd} updated row(s)' + ('' if changed else ' (no change, not saved)'))
    print(json.dumps({'open': M.needs_summary(doc), 'rows': len(doc['rows'])})); return 0


def cmd_watch(a):
    """The low-cost change check of the official download sources (kpc_master_watch.py); allowed requests only."""
    import kpc_master_watch as W
    out = W.watch(a.sources, a.needs, offline=a.offline, min_days=float(os.environ.get('KPC_WATCH_MIN_DAYS') or 7))   # owner rule, 2026-11-10
    notice('Download sources', f"{out['checked']} checked, {len(out['changed'])} changed ({', '.join(out['changed']) or 'none'}), "
           f"{out['not_checked']} not checked this run, {out.get('recent', 0)} checked in the last days (skipped), {out['person']} checked by a person (the PC helper's --reminders)")
    print(json.dumps(out, sort_keys=True)); return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest='cmd', required=True)
    t = sp.add_parser('trim'); t.add_argument('--layer-key', required=True); t.add_argument('--input'); t.add_argument('--url'); t.add_argument('--parks', required=True)
    t.add_argument('--area'); t.add_argument('--expected', type=int); t.add_argument('--agency'); t.add_argument('--license'); t.add_argument('--g', choices=sorted(M.RANK))
    t.add_argument('--id-fields'); t.add_argument('--name-fields'); t.add_argument('--record-id-field'); t.add_argument('--detail', type=float); t.add_argument('--circle-m', type=float)
    t.add_argument('--page', type=int, default=500); t.add_argument('--accept-shrink', action='store_true'); t.add_argument('--dry-run', action='store_true'); t.add_argument('--root')
    rs = sp.add_parser('resave', help='write every area file again: pin-graded parks out, parts when over 1 MB (Nov 11)')
    rs.add_argument('--root'); rs.add_argument('--key', help='the us-key folder (default: next to the outlines folder)'); rs.add_argument('--areas'); rs.add_argument('--dry-run', action='store_true')
    c = sp.add_parser('check'); c.add_argument('--root'); c.add_argument('--cache'); c.add_argument('--repo')
    p = sp.add_parser('plan'); p.add_argument('--root'); p.add_argument('--areas'); p.add_argument('--prefix'); p.add_argument('--max-days', type=float, default=30); p.add_argument('--no-probe', action='store_true'); p.add_argument('--out')
    g = sp.add_parser('gate'); g.add_argument('--cache', required=True); g.add_argument('--root'); g.add_argument('--report')
    g.add_argument('--first-ok', action='store_true', help='a saved copy with NO baseline yet passes (notice); a short one is still held')
    g.add_argument('--allow-trimmed', action='store_true', help='a copy whose own manifest says trimmed to parks is checked against that manifest (else refused)')
    g.add_argument('--approved', help='owner-approved baselines (*.approved.json with a sign-off); a proposed file is never read')
    bm = sp.add_parser('bundle-manifest', help='write a saved copy\'s own manifest into it (a copy trimmed to parks on purpose), or --check / --show it')
    bm.add_argument('files', nargs='+'); bm.add_argument('--by', help='who made the copy (e.g. KPC owner)'); bm.add_argument('--made', help='date made (YYYY-MM-DD, default today)')
    bm.add_argument('--full', action='store_true', help='the copy is NOT trimmed (default: trimmed to parks)')
    bm.add_argument('--source-full', action='append', default=[], help='LABEL=N: the source layer\'s own full count, for the record (repeat)')
    bm.add_argument('--note', default=''); bm.add_argument('--replace', action='store_true', help='replace a manifest the copy already has')
    bm.add_argument('--check', action='store_true', help='only check each copy against its manifest (exit 1 on a problem)')
    bm.add_argument('--show', action='store_true', help='only print each copy\'s record count per layer, sha256 and manifest (writes nothing)')
    b = sp.add_parser('baseline', help="record a saved copy's first baseline (only when it has none)")
    b.add_argument('files', nargs='+'); b.add_argument('--root'); b.add_argument('--against', help='the release copies as downloaded (the baseline is never above them)')
    b.add_argument('--how', default='first good full read of the saved copy')
    r = sp.add_parser('raw-add'); r.add_argument('file'); r.add_argument('--source', required=True); r.add_argument('--root')
    w = sp.add_parser('wdpa-lookup'); w.add_argument('--input', required=True); w.add_argument('--out', required=True)
    f = sp.add_parser('fill', help='THE master step: refill / verify the saved copies before the gate (kpc_master_fill.py)')
    f.add_argument('--cache', required=True); f.add_argument('--states', required=True); f.add_argument('--root'); f.add_argument('--parks', required=True)
    f.add_argument('--needs'); f.add_argument('--hand'); f.add_argument('--refresh', default=''); f.add_argument('--work', required=True)
    f.add_argument('--out-rows'); f.add_argument('--us-layers', default='data/us-key/layers.json'); f.add_argument('--state-gis', default='data/state-gis.json')
    f.add_argument('--key'); f.add_argument('--offline', action='store_true'); f.add_argument('--no-key', action='store_true')
    f.add_argument('--us-key', default='data/us-key', help='the live key files (US-XX.json) whose joined record ids decide what is actually missing')
    f.add_argument('--official-files', action='store_true', help='download the open bot rows\' official direct files (the fresh-start run only)')
    f.add_argument('--areas', default='', help='more area ids for hand files: US-XX, CA-XX / CA-ALL, W-XX (space or comma list)')
    f.add_argument('--checked', help='the per-area checked store for Canada / world hand files (default: <work>/checked)')
    co = sp.add_parser('collect', help='join job: the build parts\' master records, layer counts, raw rows and needs rows')
    co.add_argument('parts', nargs='*'); co.add_argument('--root'); co.add_argument('--needs-in'); co.add_argument('--needs-out')
    co.add_argument('--us-key', help='data/us-key: with it, every park the key knows that has no outline lands in solver-queue/US-XX.nomatch.csv with a reason')
    pa = sp.add_parser('part', help='build job: write only this job\'s own states (outline files, changed layer / cache / raw rows) into its part (Nov 11)')
    pa.add_argument('--root', required=True); pa.add_argument('--base', required=True); pa.add_argument('--states', required=True); pa.add_argument('--out', required=True)
    n = sp.add_parser('needs', help='merge rows into a needs-download list, or print its size')
    n.add_argument('--list', required=True); n.add_argument('--add', nargs='*', default=[])
    sc = sp.add_parser('save-check', help='before an upload: refuse a saved copy that fails the gate baseline or has fewer records than the release copy')
    sc.add_argument('files', nargs='*'); sc.add_argument('--against', required=True); sc.add_argument('--assets'); sc.add_argument('--first-ok', action='store_true')
    sc.add_argument('--ok-list'); sc.add_argument('--root')
    wa = sp.add_parser('watch', help='the change check: a HEAD / catalog fingerprint per official download source; reopens a changed source\'s rows')
    wa.add_argument('--sources', default=str(M.OUTLINES / 'download-sources.json')); wa.add_argument('--needs'); wa.add_argument('--offline', action='store_true')
    ie = sp.add_parser('import-existing', help='take in the downloads already on the box: raw facts, done rows, checked hand files (kpc_master_import.py)')
    ie.add_argument('--csv', help='the filled source list (box only; its licence notes never go public)'); ie.add_argument('--copies', help='a folder of the saved copies (US-XX, CA-ALL, W-XX)')
    ie.add_argument('--same-as', help='box-side {area: {list label: saved-copy label}} for sources whose label differs'); ie.add_argument('--us-layers', default='data/us-key/layers.json')
    ie.add_argument('--add', nargs='*', default=[], help="the master step's needs rows (fill --out-rows) to add"); ie.add_argument('--hand-map'); ie.add_argument('--downloads-md')
    ie.add_argument('--drive-index'); ie.add_argument('--research'); ie.add_argument('--box-only', help='box-side list of rows whose records are only in a box file')
    ie.add_argument('--hand-out', default='kpc-hand'); ie.add_argument('--parks'); ie.add_argument('--needs-out', required=True); ie.add_argument('--root')
    ie.add_argument('--upload', action='store_true', help='upload the checked hand files to the boundary-cache release (gh)'); ie.add_argument('--repo', default='KentuckyPortableClub/KPC-Links')
    a = ap.parse_args(argv)
    if a.cmd == 'trim' and bool(a.input) == bool(a.url): ap.error('give exactly one of --input or --url')
    if a.cmd == 'import-existing':
        import kpc_master_import as I
        return I.main(a)
    if a.cmd in ('fill', 'collect', 'part'):
        import kpc_master_fill as F
        a.root = a.root or str(M.OUTLINES)
        return {'fill': F.fill, 'collect': F.collect, 'part': F.part}[a.cmd](a)
    return {'trim': cmd_trim, 'check': cmd_check, 'gate': cmd_gate, 'plan': cmd_plan, 'raw-add': cmd_raw_add, 'wdpa-lookup': cmd_wdpa, 'needs': cmd_needs, 'watch': cmd_watch, 'save-check': cmd_save_check, 'baseline': cmd_baseline, 'resave': cmd_resave, 'bundle-manifest': cmd_bundle_manifest}[a.cmd](a)


if __name__ == '__main__': sys.exit(main())
