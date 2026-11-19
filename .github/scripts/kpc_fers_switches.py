#!/usr/bin/env python3
"""kpc_fers_switches.py: the 2-fer rule switches in one file (hand-off 06, 19 Nov 2026).

The owner's answers live in .github/fers-switches.json. Every run reads that file. An environment variable of the same
name still wins (a test, an offline proof) and the run says so once. A missing file, a broken file, or a setting the
code asks for that the file does not hold stops the bot (exit 4). It never runs with every rule quietly off.

Standard library only. kpc_fers.py, kpc_fers_store.py and kpc_fers_age.py all read this module."""
import json, os, pathlib

FILE = pathlib.Path(__file__).resolve().parent.parent / 'fers-switches.json'
NAMES = ('KPC_FERS_SUMMARY_APPROX', 'KPC_FERS_NEAR_LINE', 'KPC_FERS_CARRY_MADE_ON', 'KPC_FERS_FINE_ONLY', 'KPC_FERS_STRIP_HELD')
NEED = ('value', 'rule', 'date', 'ruled_by', 'words')
_DOC = {'loaded': False, 'switches': None}
_SAID = set()


def _stop(why):
    print(f'::error title=2-fer bot::the 2-fer switch file {FILE} could not be used ({why}): the bot stops here', flush=True)
    raise SystemExit(4)


def load(path=None):
    """The switch entries. Called once. A bad file stops the bot."""
    path = pathlib.Path(path or FILE)
    if _DOC['loaded'] and path == FILE and _DOC['switches'] is not None:
        return _DOC['switches']
    try:
        d = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        _stop(e)
    sw = d.get('switches') if isinstance(d, dict) else None
    if not isinstance(sw, dict):
        _stop("no 'switches' object")
    out = {}
    for name in NAMES:
        e = sw.get(name)
        if not isinstance(e, dict):
            _stop(f'no entry for {name}')
        for k in NEED:
            if not str(e.get(k) or '').strip():
                _stop(f'{name} has no {k}')
        out[name] = {k: e[k] for k in NEED}
    if path == FILE:
        _DOC['loaded'] = True
        _DOC['switches'] = out
    return out


def value(name, env=None):
    """(value, 'file' or 'env'). The environment wins when the name is set, even to 0 or off."""
    env = os.environ if env is None else env
    if name in env:
        if name not in _SAID:
            _SAID.add(name)
            print(f'::notice title=2-fer switches::{name} comes from the environment ({env.get(name)}), not from the switch file', flush=True)
        return str(env.get(name)), 'env'
    sw = load()
    if name not in sw:
        _stop(f'the code asked for {name}, and the file has no entry for it')
    return str(sw[name]['value']), 'file'


def on(name, env=None):
    v, _ = value(name, env)
    return v.strip().lower() not in ('0', 'off', 'false', 'no', '')


def snapshot(env=None):
    """Every setting in force, and where it came from, for the run receipt."""
    out = []
    for name in NAMES:
        v, src = value(name, env)
        out.append({'name': name, 'value': v, 'from': src, 'rule': load()[name]['rule']})
    return out


load()
