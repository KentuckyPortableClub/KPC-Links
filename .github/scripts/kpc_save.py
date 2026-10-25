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


import atexit  # noqa: E402
atexit.register(flush_status)
