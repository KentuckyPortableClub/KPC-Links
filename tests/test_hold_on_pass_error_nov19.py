#!/usr/bin/env python3
"""F10 (outside review, 2026-11-19; reviewer's go 19 Nov; DRAFT): an error inside the US key's one-record-two-parks pass (the kind
pass, D9, the contest) used to print 'one-record-two-parks pass skipped' and save the state anyway. Behind KPC_HOLD_ON_PASS_ERROR
(OFF): switch OFF = the same notice, word for word, and no raise; switch ON = the error is raised, names the state, and run() fails
for that state like any other error of a state (FAILED, no key file written, its saved copy kept). No shapely needed.
Run:  python3 tests/test_hold_on_pass_error_nov19.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

NAME = 'KPC_HOLD_ON_PASS_ERROR'
sw = json.load(open(ROOT / '.github/key-switches.json', encoding='utf-8'))['switches']
check(KR.DEFAULTS.get(NAME) == '0' and sw.get(NAME) == {'on': []}, 'the switch is OFF by default and listed in key-switches.json with no area')
check(not KR.on(NAME, env={}, area='OH') and not KR.on(NAME, env={}, area='NH'), 'the switch is OFF unless set (committed switch file, no environment)')
check(KR.on(NAME, env={NAME: '1'}, area='OH'), 'an environment variable of the same name turns it on (offline proofs)')

# the helper alone
e = ValueError("boom 'x' 5%")
check(KR.pass_error('NH', e, False) is e, 'OFF: pass_error hands back the very same error (no raise)')
try: KR.pass_error('NH', e, True); raised = None
except KR.PassError as x: raised = x
check(raised is not None and 'NH' in str(raised) and 'boom' in str(raised) and raised.__cause__ is e, f'ON: PassError is raised, names the state and the error ({raised})')
check(issubclass(KR.PassError, Exception), "PassError is an Exception, so the builder's per-state 'except Exception' catches it (FAILED, carry on with the next state)")

# the builder's own except line, run as written (taken from the source, no shapely)
SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
OLD = "    except Exception as _e: notice(f'US key {st}', f'one-record-two-parks pass skipped: {_e}')  # noqa: BLE001"
lines = [ln for ln in SRC.splitlines() if ln.startswith("    except Exception as _e: notice(f'US key {st}', f'one-record-two-parks pass skipped")]
check(len(lines) == 1 and 'KR.pass_error(st, _e, _kr("KPC_HOLD_ON_PASS_ERROR"))' in lines[0] and OLD not in SRC,
      'kpc_us_key.py: the pass\'s except asks KR.pass_error with the switch read for this state')
def run_except(line, hold, err):
    out = []
    code = 'def f():\n    try: raise ERR\n' + line + '\n'
    g = {'ERR': err, 'notice': lambda t, m: out.append((t, m)), 'st': 'NH', 'KR': KR, '_kr': lambda n: hold if n == NAME else False}
    exec(compile(code, 'kpc_us_key.py (except line)', 'exec'), g)
    try: g['f'](); return out, None
    except Exception as x: return out, x  # noqa: BLE001
if lines:
    old_out, old_x = run_except(OLD, False, ValueError("boom 'x' 5%"))
    new_out, new_x = run_except(lines[0], False, ValueError("boom 'x' 5%"))
    check(new_x is None and new_out == old_out == [('US key NH', "one-record-two-parks pass skipped: boom 'x' 5%")],
          f'switch OFF: the same notice as before, byte for byte, and no raise ({new_out})')
    on_out, on_x = run_except(lines[0], True, KeyError('US-1234'))
    check(isinstance(on_x, KR.PassError) and 'NH' in str(on_x) and on_out == [], f'switch ON: the error is raised and names the state, no "skipped" notice ({on_x})')
i = SRC.index('        c = run(st)\n    except Exception as e:  # noqa: BLE001\n')
check("notice(f'US key {st}', f'FAILED: {e}'); continue" in SRC[i:i + 200] and SRC.index("save_json(OUT / f'US-{st}.json', out)") < i,
      "a state whose run() raises is named FAILED and skipped: its key file is written only at the end of run(), so the saved copy stays")
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
