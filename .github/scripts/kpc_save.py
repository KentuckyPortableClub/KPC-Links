"""One way to save the park-data bots' files (KPC storage plan Stage 1, Oct 25 2026: 'a bot saves a file only when its
CONTENT changed; JSON written the same way every time; time stamps in one small status file').

save_json(path, obj)  - writes sorted, compact JSON, but only when the content is different from what is on disk.
                        A top-level 'updated' (and 'saved') is taken OUT of the data; the change date goes in data/status/<script>.json,
                        so a run that finds nothing new leaves the file - and git's history - untouched.
save_text(path, text) - the same for review pages and other text files.
Both return True when the file was written. Each bot keeps its OWN status file, data/status/<script>.json, so two bots
running at the same time never edit the same file (a shared one would clash when both push)."""
import json
import pathlib
import sys
import time

STATUS = pathlib.Path('data/status') / (pathlib.Path(sys.argv[0] or 'bot').stem + '.json')
STAMPS = ('updated', 'saved', 'when')
_changed = {}


def canon(obj, indent=None):
    if indent is None:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=indent) + '\n'


def _write_if_new(p, text):
    p = pathlib.Path(p)
    try:
        if p.exists() and p.read_text(encoding='utf-8') == text:
            return False
    except Exception:  # noqa: BLE001
        pass
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')
    _changed[str(p)] = time.strftime('%Y-%m-%d')
    return True


def save_json(path, obj, indent=None):
    if isinstance(obj, dict):
        obj = {k: v for k, v in obj.items() if k not in STAMPS}
    return _write_if_new(path, canon(obj, indent))


def save_text(path, text):
    return _write_if_new(path, text if text.endswith('\n') else text + '\n')


def flush_status():
    """Record when each changed file last changed (call once at the end of a run; tiny file)."""
    if not _changed:
        return
    try:
        st = json.loads(STATUS.read_text(encoding='utf-8')) if STATUS.exists() else {}
    except Exception:  # noqa: BLE001
        st = {}
    files = st.get('changed', {})
    files.update(_changed)
    st = {'about': 'When each park-data file last CHANGED (the files themselves carry no time stamps, so unchanged runs save nothing). Written by .github/scripts/kpc_save.py.',
          'changed': files}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(st, sort_keys=True, ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
    _changed.clear()


# ------------------------------------------------------------------ dates on every fact (Oct 27: Fable's research-bots review #2 +
# boundary review B2, HQ 12:20 PM: ONE helper). 'read' = the day a fact was last read from its agency. A fact that did not change
# keeps its date until it is REFRESH_DAYS old, so an unchanged nightly run does not rewrite the file.
REFRESH_DAYS = 30


def today(): return time.strftime('%Y-%m-%d')


def read_dates(old_items, new_items, old_read, refresh_days=REFRESH_DAYS):
    """{key: 'YYYY-MM-DD'} for every key in new_items (dicts of key -> content). Same content + a date younger than refresh_days
    = the old date; anything new, changed or older = today. Keys that are gone drop out."""
    t = today()
    cut = time.strftime('%Y-%m-%d', time.localtime(time.time() - refresh_days * 86400))
    out = {}
    for k, v in (new_items or {}).items():
        d = (old_read or {}).get(k)
        out[k] = d if d and d >= cut and canon((old_items or {}).get(k)) == canon(v) else t
    return out


def source_clock(old_meta, ok, n):
    """Change detection for one SOURCE (a feed, a layer): keeps 'kept_since' (the day reads started failing: the last good copy
    has been shown since then) and 'n_prev' (the last good count), so 'went from N to 0' and 'kept for weeks' can be seen."""
    old_meta = old_meta or {}
    prev = old_meta.get('n') if old_meta.get('ok', True) and old_meta.get('n') is not None else old_meta.get('n_prev')
    m = {} if prev is None else {'n_prev': prev}
    if not ok: m['kept_since'] = old_meta.get('kept_since') or today()
    return m


import atexit  # noqa: E402
atexit.register(flush_status)
