#!/usr/bin/env python3
"""Report-only confirm headers and match-checks extra lines (24 Nov 2026, plan B).

Park-facts hash, page-reader version, per-state restock stamp, and 'rule changes
since the last test'. Counts and IDs only: never a park name. Decides no join
(kpc_key_freeze.NOT_RULES). Standard library only.
"""
import hashlib, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import kpc_key_freeze as KF  # noqa: E402
import kpc_match_checks as MC  # noqa: E402


def park_facts_stamp(path=None):
    """'made <date> <first 12 of sha256>' plus the park-facts tool, or ''."""
    path = path or os.environ.get('PARK_FACTS') or ''
    stamp = MC.facts_stamp(path) if path else ''
    tool = ''
    if path and os.path.isfile(path):
        try:
            import gzip
            op = gzip.open if str(path).endswith('.gz') else open
            with op(path, 'rt', encoding='utf-8') as fh:
                head = json.load(fh)
            tool = str(head.get('tool') or '')
        except (OSError, ValueError, EOFError, TypeError):
            tool = ''
    if stamp and tool:
        return f'{stamp}, tool {tool}'
    return stamp or tool


def page_reader_version(path=None):
    """The page-reader bot label from the park facts 'sources.page', or ''."""
    path = path or os.environ.get('PARK_FACTS') or ''
    if not path or not os.path.isfile(path):
        return ''
    try:
        import gzip
        op = gzip.open if str(path).endswith('.gz') else open
        with op(path, 'rt', encoding='utf-8') as fh:
            data = json.load(fh)
        page = ((data.get('sources') or {}).get('page') or {})
        bot = page.get('bot') or page.get('tool') or page.get('version') or ''
        n = page.get('parks')
        extra = f', {n} parks with a page' if n else ''
        return f'{bot}{extra}'.strip(', ')
    except (OSError, ValueError, EOFError, TypeError):
        return ''


def official_size_count(path=None):
    """How many parks in the park facts carry a numeric official size."""
    path = path or os.environ.get('PARK_FACTS') or ''
    if not path or not os.path.isfile(path):
        return 0
    try:
        import gzip
        op = gzip.open if str(path).endswith('.gz') else open
        with op(path, 'rt', encoding='utf-8') as fh:
            data = json.load(fh)
        n = 0
        for row in (data.get('parks') or {}).values():
            s = (row or {}).get('size') if isinstance(row, dict) else None
            if isinstance(s, dict) and s.get('acres') not in (None, '', 'n/a'):
                try:
                    float(s['acres']); n += 1
                except (TypeError, ValueError):
                    pass
        return n
    except (OSError, ValueError, EOFError, TypeError):
        return 0


def layer_file_stamp(st, layer_files=None, store_dir=None):
    """25 Nov 2026 (the owner's MN test: the stamp showed only the Nov 12 saved copy, so it looked stale): the full layer file
    the build reads (KPC-Store's <area>.layer-records.json.gz): its 'made' stamp, from the store id fields file's layer_files
    (the key) or the file itself in the store folder (the PC test), plus the file's own date. '' when neither is given."""
    area = f'US-{str(st or "").upper()}'
    lf = (layer_files or {}).get(area) or {}
    made, fdate, name = str(lf.get('made') or ''), '', str(lf.get('file') or '')
    sd = store_dir or os.environ.get('KPC_LAYER_RECORDS_DIR') or ''
    f = pathlib.Path(sd) / (name or f'{area}.layer-records.json.gz') if sd else None
    if f is not None and f.is_file():
        import datetime
        fdate = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        if not made:
            try:
                import gzip
                with gzip.open(f, 'rt', encoding='utf-8') as fh: head = fh.read(4000)
                m = re.search(r'"made":\s*"([^"]+)"', head)
                made = m.group(1) if m else ''
            except (OSError, EOFError, ValueError):
                made = ''
    elif not lf:
        return 'no layer file' if (layer_files is not None or sd) else ''
    if not (made or fdate): return 'layer file (no date)'
    return 'layer file ' + ' '.join(x for x in (f'made {made}' if made else '', f'(file date {fdate})' if fdate else '') if x)


def restock_stamp(st, cache_dir=None, root=None, layer_files=None, store_dir=None):
    """Per-state saved-copy stamp: the copy's own 'saved' date and a short file hash, or ''; plus the full layer file's date
    (layer_file_stamp) when the layer files are known."""
    ls = layer_file_stamp(st, layer_files, store_dir)
    s = _saved_stamp(st, cache_dir)
    return f'{s}; {ls}' if s and ls else (s or ls)


def _saved_stamp(st, cache_dir=None):
    cache_dir = cache_dir or os.environ.get('GEO_CACHE') or ''
    if not cache_dir:
        return ''
    st = str(st or '').upper()
    if not st:
        return ''
    name = f'US-{st}.json.gz' if len(st) == 2 else f'{st}.json.gz'
    f = pathlib.Path(cache_dir) / name
    if not f.is_file():
        f = pathlib.Path(cache_dir) / f'US-{st}.json.gz'
    if not f.is_file():
        return ''
    h = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
    saved = ''
    try:
        import gzip
        with gzip.open(f, 'rt', encoding='utf-8') as fh:
            data = json.load(fh)
        saved = str(data.get('saved') or data.get('updated') or data.get('made') or '')
    except (OSError, ValueError, EOFError, TypeError):
        saved = ''
    if saved:
        return f'saved {saved} {h}'
    return h


def rule_changes_since(last_hash=None, kind='us-key', root=None):
    """Scope-change ids after last_hash (the hash the last test ran). [] if none or last_hash is current."""
    root = pathlib.Path(root) if root else ROOT
    last_hash = (last_hash or os.environ.get('KPC_LAST_TEST_RULES') or '').strip()
    now = KF.rules_hash(kind, root)
    if not last_hash or last_hash == now:
        return []
    path = root / KF.SCOPE_FILES[kind]
    try:
        changes = json.loads(path.read_text(encoding='utf-8')).get('changes') or []
    except (OSError, ValueError):
        return []
    ids, seen = [], False
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        if ch.get('from') == last_hash:
            seen = True
        if seen:
            ids.append(ch.get('id') or '')
    if not seen:   # 25 Nov: the last test ran rules this tree never recorded (a test kit of an unmerged change): never say "none"
        return [f'the last test ran rules not recorded here ({last_hash}; this run {now}), so the changes cannot be listed']
    return [x for x in ids if x]


def header_lines(root=None, facts_path=None, cache_dir=None, states=None, last_rules=None, layer_files=None, store_dir=None):
    """Plain header lines for a key run or a PC test report. Counts only; no park names."""
    root = pathlib.Path(root) if root else ROOT
    facts_path = facts_path or os.environ.get('PARK_FACTS') or ''
    lines = []
    try:
        us, ca = KF.rules_hash('us-key', root), KF.rules_hash('ca-key', root)
        lines.append(f'Rules this run: US {us}, Canada {ca}.')
    except Exception as e:  # noqa: BLE001
        lines.append(f'Rules this run: could not be read ({type(e).__name__}).')
    pf = park_facts_stamp(facts_path)
    lines.append(f"Park facts: {pf}." if pf else 'Park facts: not found.')
    pv = page_reader_version(facts_path)
    if pv:
        lines.append(f'Page-reader facts: {pv}.')
    nsz = official_size_count(facts_path)
    lines.append(f'Official sizes in the park facts: {nsz:,}.')
    last_rules = last_rules or os.environ.get('KPC_LAST_TEST_RULES') or ''
    ch = rule_changes_since(last_rules, 'us-key', root) if last_rules else None
    if last_rules and ch is not None:
        if not ch:
            lines.append(f'Rule changes since the last test ({last_rules}): none.')
        else:
            lines.append('Rule changes since the last test (' + last_rules + '): ' + ', '.join(ch) + '.')
    elif not last_rules:
        lines.append('Rule changes since the last test: not given (set KPC_LAST_TEST_RULES to the last test\'s US hash).')
    stamps = []
    for st in states or []:
        s = restock_stamp(st, cache_dir, root, layer_files, store_dir)
        if s:
            stamps.append(f'{st} {s}')
    if stamps:
        lines.append('Restock stamps: ' + '; '.join(stamps) + '.')
    return lines


def match_checks_extra(mc, ra_used=0, ra_bridged=0, restock=''):
    """The auto-confirm / size-flag / bridge piece of the match-checks line."""
    mc = mc or {}
    held = mc.get('by_held name and pin', 0)
    exact = mc.get('by_name_exact', 0)
    spell = mc.get('by_name_spelling table', 0)
    loose = mc.get('by_name_looser name', 0)
    page = mc.get('by_page names the land', 0)
    belt = mc.get('county_belt', 0)
    far = mc.get('size_far_confirms', 0)
    far_ids = mc.get('size_far_ids') or []
    held_back = mc.get('size_hold', 0)
    parts = [
        f'auto-confirm: held name and pin {held} (exact {exact}, spelling table {spell}, looser name {loose})',
        f'page names the land {page}',
        f'county belt kept {belt}',
        f'store-id fields on {ra_used} record(s) (+{ra_bridged} by name and size)',
        f'size far from official acres (report only): {far}',
    ]
    if held_back:
        parts.append(f'size-hold switch withheld {held_back}')
    if far_ids:
        parts.append('flagged IDs: ' + ', '.join(far_ids[:20]) + ('…' if len(far_ids) > 20 else ''))
    if restock:
        parts.append(f'restock stamp: {restock}')
    return '; '.join(parts)


if __name__ == '__main__':
    for ln in header_lines():
        print(ln)
