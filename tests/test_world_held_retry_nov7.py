#!/usr/bin/env python3
"""Offline test, Nov 7 world fix part A (hash-neutral; Brandon kept every approved layer). kpc-world-key.yml's build step:
a country HELD by kpc_world_key.py (exit 3: a source failed or came back empty with no saved records) is tried again at the end of
the job after a wait, never past the step's own limit; a timeout (124) or an error is NOT retried; a held country that builds on the
retry leaves failed.txt. The slow (own-job) country restores / saves cache/world/parts (the layer checkpoints part B writes); the save
only runs when there is something to save. A short saved copy (gate exit 7) is not built or retried; the other countries of the shard still are. Runs the build step's real bash with a stand-in kpc_world_key.py. No network."""
import os, pathlib, stat, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


y = yaml.safe_load(open(HERE / '.github/workflows/kpc-world-key.yml'))
steps = y['jobs']['build']['steps']
b = next(s for s in steps if s.get('id') == 'kept_green_b')
FAKE = '''import os, pathlib, sys
c = os.environ['COUNTRIES']; plan = dict(x.split('=') for x in os.environ['FAKE_PLAN'].split())
n = pathlib.Path('tries-' + c); k = int(n.read_text()) if n.exists() else 0; n.write_text(str(k + 1))
seq = plan.get(c, '0').split(',')
rc = int(seq[min(k, len(seq) - 1)])
if rc == 0:
    pathlib.Path('data/world-key').mkdir(parents=True, exist_ok=True); pathlib.Path(f'data/world-key/{c}.json').write_text('{}')
sys.exit(rc)
'''


def run(mine, plan, retries='1', waitmin='0', cmin='5', step_min='335', gate_rc=0, short=None, write_rc=True):
    with tempfile.TemporaryDirectory() as t:
        tp = pathlib.Path(t); (tp / '.github/scripts').mkdir(parents=True); (tp / '.github/scripts/kpc_world_key.py').write_text(FAKE)
        (tp / 'bin').mkdir(); pip = tp / 'bin/pip'; pip.write_text('#!/bin/sh\nexit 0\n'); pip.chmod(pip.stat().st_mode | stat.S_IEXEC)
        env = dict(os.environ, PATH=f"{tp / 'bin'}:{os.environ['PATH']}", MINE=mine, FAKE_PLAN=plan, RETRIES=retries, WAITMIN=waitmin,
                   CMIN=cmin, STEP_MIN=step_min, PIN_JOIN='', WB_DIR='')
        rt = tp / 'runner'; rt.mkdir()
        if write_rc: (rt / 'master-gate.rc').write_text(str(gate_rc) + '\n')
        if short is not None: (rt / 'master-short.txt').write_text(short)
        env['RUNNER_TEMP'] = str(rt)   # always isolated: a leftover box/CI RUNNER_TEMP must not trip the short-copy filter
        r = subprocess.run(['bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c', b['run']], cwd=t, env=env, capture_output=True, text=True, timeout=120)
        failed = (tp / 'part/failed.txt').read_text().split()
        tries = {c: int((tp / f'tries-{c}').read_text()) for c in mine.split() if (tp / f'tries-{c}').exists()}
        return r.returncode, failed, tries, r.stdout + r.stderr


rc, failed, tries, out = run('DE AX CH CL', 'DE=0 AX=3,0 CH=3 CL=124')
check(rc == 0, 'the build step itself ends cleanly (exit 0)' + ('' if rc == 0 else ': ' + out[-600:]))
check(tries.get('DE') == 1 and 'DE' not in failed, 'a country that builds is run once and not listed')
check(tries.get('AX') == 2 and 'AX' not in failed and 'built on held retry 1' in out, 'a held country that builds on the retry leaves failed.txt')
check(tries.get('CH') == 2 and failed.count('CH') == 1 and 'still HELD' in out, 'a country held twice is listed as failed once')
check(tries.get('CL') == 1 and 'CL' in failed, 'a timeout (124) is not retried')
rc, failed, tries, out = run('AX DO', 'AX=3 DO=3,3,0', retries='2')
check(tries == {'AX': 3, 'DO': 3} and failed == ['AX'], 'KPC_WORLD_HELD_RETRIES=2 gives two more tries')
rc, failed, tries, out = run('AX', 'AX=3,0', retries='0')
check(tries == {'AX': 1} and failed == ['AX'], 'KPC_WORLD_HELD_RETRIES=0 = the old behaviour (no retry)')
rc, failed, tries, out = run('AX', 'AX=3,0', step_min='8')
check(tries == {'AX': 1} and failed == ['AX'] and 'no time left' in out, 'no retry when the step has no time left')
rc, failed, tries, out = run('AX', 'AX=1')
check(tries == {'AX': 1} and failed == ['AX'], 'an error (exit 1) is not retried')
# Nov 12 (KPC owner, 2026-11-12): a short saved copy holds only that country; the rest of the shard still builds.
# AX would be retried if it were a source-held (exit 3); a short copy must not be built or retried.
rc, failed, tries, out = run('DE AX CH', 'DE=0 AX=3,0 CH=0', gate_rc=7, short='W-AX\n')
check(rc == 0, 'short-copy gate: the build step itself ends cleanly' + ('' if rc == 0 else ': ' + out[-600:]))
check(tries.get('DE') == 1 and tries.get('CH') == 1 and 'AX' not in tries, 'short-copy gate: only the short country is not built')
check(failed == ['AX'], 'short-copy gate: only the short country is listed failed (held, not joined)')
check('short saved copy moved aside' in out, 'short-copy gate: the short country is named held')
rc, failed, tries, out = run('DE AX', 'DE=0 AX=0', gate_rc=7, short='')
check(tries == {} and 'not this job' in out, 'exit 7 with an empty short list: no country is built (fail closed)')
rc, failed, tries, out = run('DE AX', 'DE=0 AX=0', gate_rc=7, short='W-FR\n')
check(tries == {} and 'not this job' in out, 'exit 7 with a short copy the job does not own: no country is built (fail closed)')
# Quality M1: a missing or non-0/7 gate rc must not fall through to build everyone (fail closed).
rc, failed, tries, out = run('DE AX', 'DE=0 AX=0', write_rc=False)
check(tries == {} and 'not 0 or 7' in out and 'none' in out, 'missing gate rc (mg=none): no country is built (fail closed)' + ('' if tries == {} else ': ' + out[-400:]))
rc, failed, tries, out = run('DE AX', 'DE=0 AX=0', gate_rc=1)
check(tries == {} and 'not 0 or 7' in out, 'gate exit 1: no country is built (fail closed)' + ('' if tries == {} else ': ' + out[-400:]))
check(b['env']['RETRIES'] == "${{ vars.KPC_WORLD_HELD_RETRIES || '1' }}" and b['env']['WAITMIN'] == "${{ vars.KPC_WORLD_HELD_WAIT_MIN || '10' }}",
      'retries and wait are repo variables (defaults 1 and 10 min)')
check(int(b['env']['STEP_MIN']) == int(b['timeout-minutes']), "STEP_MIN matches the build step's timeout-minutes")
pin = next(s for s in steps if s.get('id') == 'kept_green_parts_in'); pout = next(s for s in steps if s.get('id') == 'kept_green_parts_out')
names = [s.get('id') for s in steps]
check(names.index('kept_green_parts_in') < names.index('kept_green_b') < names.index('kept_green_parts_out'), 'restore before the build, save after it')
check(pin['uses'].startswith('actions/cache/restore@') and pout['uses'].startswith('actions/cache/save@') and pin['with']['path'] == pout['with']['path'] == 'cache/world/parts',
      'the checkpoints folder is cache/world/parts')
check("matrix.g.cmin != ''" in pin['if'] and "matrix.g.cmin != ''" in pout['if'] and "hashFiles('cache/world/parts/**') != ''" in pout['if'] and 'always()' in pout['if'],
      'slow (own-job) countries only; the save runs even after a stop, and only when something was written')
check(pin.get('continue-on-error') is True and pout.get('continue-on-error') is True, 'a cache problem never stops the build')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
