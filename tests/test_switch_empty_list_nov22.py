#!/usr/bin/env python3
"""Review F4 (KPC owner, 22 Nov 2026): a switch listed in .github/key-switches.json is ON only for its areas and OFF everywhere else,
even when its code default is on, so an empty 'on' list really turns a default-on rule off. A switch the file does not list keeps
its code default. The real switch file does not list the four default-on rules (KPC_APPROX_PIN, KPC_PRESERVE_APART, KPC_FAR_JOIN,
KPC_PRESERVE_WITH_PARK), so they stay on everywhere and no result changes; the switch file itself is not changed. Offline; invented areas only."""
import json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg, flush=True)

FOUR = ('KPC_APPROX_PIN', 'KPC_PRESERVE_APART', 'KPC_FAR_JOIN', 'KPC_PRESERVE_WITH_PARK')
t = pathlib.Path(tempfile.mkdtemp())
f = t / 'sw.json'
f.write_text(json.dumps({'switches': {'KPC_APPROX_PIN': {'on': []}, 'KPC_FAR_JOIN': {'on': ['OH']}}}))
check(KR.DEFAULTS['KPC_APPROX_PIN'] == '1' and not KR.on('KPC_APPROX_PIN', env={}, area='OH', path=str(f)),
      "an empty 'on' list turns a default-on switch OFF")
check(KR.on('KPC_FAR_JOIN', env={}, area='OH', path=str(f)) and not KR.on('KPC_FAR_JOIN', env={}, area='TN', path=str(f)),
      'a default-on switch listed for one state is on there and off elsewhere')
check(KR.on('KPC_PRESERVE_APART', env={}, area='OH', path=str(f)) and not KR.on('KPC_ANSWER_HOLDERS', env={}, area='OH', path=str(f)),
      'a switch the file does not list keeps its code default (on stays on, off stays off)')
check(KR.on('KPC_APPROX_PIN', env={'KPC_APPROX_PIN': '1'}, area='OH', path=str(f)), 'an environment variable still wins')
real = json.loads((ROOT / '.github/key-switches.json').read_text(encoding='utf-8'))['switches']
check(not any(k in real for k in FOUR), 'the real switch file does not list the four default-on rules (it is not changed)')
check(all(KR.on(k, env={}, area=a) for k in FOUR for a in ('OH', 'KY', 'US-TN', None)),
      'so with the real file the four stay on for every state (no result changes)')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
