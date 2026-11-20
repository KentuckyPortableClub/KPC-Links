#!/usr/bin/env python3
"""Named-parks drop guard (Fable sitting 3 item 20, owner 10:12 AM '1-4 I agree with your thoughts for now'; key-quality.md section 19
item 21c). A state on the approved list (.github/key-drop-approved.json) is judged park by park: every outline it lost must be named
there, else the state is held, whatever its percent or KPC_DROP_OK. A state not on the list keeps the old percent rule.
Real park numbers from the 19 Nov fact check (lost.json): MT US-4548 Pompeys Pillar (D3), AK US-0026 Gates of the Arctic.
Runs on a throwaway git repo; tests both ways."""
import json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUARD = ROOT / '.github' / 'scripts' / 'kpc_key_drop_guard.py'
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


def park(outline, g='official'):
    return {'n': 'x', 'g': g if outline else 'pin', 'm': [[1, 'rec', 10, 'name']] if outline else [], 'c': []}


def key(st, parks):
    return {'st': st, 'parks': parks}


def git(repo, *a):
    return subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', *a], cwd=repo, capture_output=True, text=True)


def setup(td):
    k = td / 'data' / 'us-key'; k.mkdir(parents=True)
    main = {'AK': {f'US-00{i:02d}': park(True) for i in range(20, 30)},
            'MT': {'US-4548': park(True), 'US-4501': park(True), **{f'US-46{i:02d}': park(True) for i in range(10)}},
            'NV': {f'US-90{i:02d}': park(True) for i in range(10)}}
    for st, p in main.items(): (k / f'US-{st}.json').write_text(json.dumps(key(st, p), indent=1))
    (k / 'index.json').write_text(json.dumps({'states': {st: {'parks': len(p)} for st, p in main.items()}}, indent=1))
    git(td, 'init', '-q'); git(td, 'add', '-A'); git(td, 'commit', '-q', '-m', 'main')
    return k, main


def write_now(k, main, lose):
    for st, p in main.items():
        q = {r: (park(False) if r in lose.get(st, ()) else v) for r, v in p.items()}
        (k / f'US-{st}.json').write_text(json.dumps(key(st, q), indent=1))


def run(td, approved=None, env=None, restore=False):
    e = dict(os.environ, KPC_DROP_PCT='0', KPC_DROP_MIN='0', KPC_DROP_OK=''); e.update(env or {})
    e.pop('KPC_DROP_APPROVED', None)
    cmd = [sys.executable, str(GUARD), '--repo', str(td), '--ref', 'HEAD', '--approved', str(approved or td / 'none.json')]
    if restore: cmd += ['--restore', '--failed-out', str(td / 'failed.txt')]
    # Nov 20 (job 7): run in the throwaway repo, so kpc_save's status file (data/status/, relative to the working folder) lands there, not in this checkout
    r = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=td)
    return r.returncode, r.stdout + r.stderr


with tempfile.TemporaryDirectory() as t:
    td = pathlib.Path(t); k, main = setup(td)
    ap = td / 'approved.json'
    # AK loses two outlines, both named; MT loses Pompeys Pillar (named) AND Custer Gallatin (not named); NV loses one, not listed
    write_now(k, main, {'AK': {'US-0026', 'US-0027'}, 'MT': {'US-4548', 'US-4501'}, 'NV': {'US-9001'}})
    ap.write_text(json.dumps({'states': {'AK': {'parks': ['US-0026', 'US-0027'], 'decided_by': 'KPC owner, test'},
                                         'MT': {'parks': ['US-4548'], 'decided_by': 'KPC owner, test'}}}))
    rc, out = run(td, ap)
    check(rc == 1, f'a held state fails the run without --restore (rc {rc})')
    check('US-AK::2 park(s) lost their outline or their official grade, every one on the approved list' in out, 'AK: every lost outline is named: let through')
    check('US-MT::1 park(s) lost their outline or their official grade and are NOT on the approved list: US-4501' in out, 'MT: one lost outline is not named (US-4501): held, and it is named in the message')
    check('title=Drop guard US-NV::official parks 10 -> 9' in out, 'NV, not on the list: the old percent rule still holds it')
    check('KPC_DROP_OK to "MT"' not in out and 'KPC_DROP_OK to "AK"' not in out, 'a named state never gets the "set KPC_DROP_OK" advice')

    # KPC_DROP_OK does not let a named state through, and still works for a state not on the list
    rc, out = run(td, ap, env={'KPC_DROP_OK': 'MT NV'})
    check('US-MT::1 park(s) lost their outline or their official grade and are NOT on the approved list' in out, 'KPC_DROP_OK=MT does not override the named list for MT')
    check('US-NV::official parks 10 -> 9 (-10.0%), let through by KPC_DROP_OK' in out, 'KPC_DROP_OK still lets a state that is not on the list through')

    # --restore: MT and NV are put back byte for byte, AK is kept as built
    ak_now = (k / 'US-AK.json').read_bytes()
    rc, out = run(td, ap, restore=True)
    check(rc == 0, f'--restore: exit 0, the other states are saved (rc {rc})')
    check((k / 'US-MT.json').read_bytes() == git(td, 'show', 'HEAD:data/us-key/US-MT.json').stdout.encode(), 'MT restored to main byte for byte')
    check((k / 'US-AK.json').read_bytes() == ak_now, 'AK kept as built (let through by the list)')
    check((td / 'failed.txt').read_text().split() == ['MT', 'NV'], 'the stamp names MT and NV failed')

    # the other way: every lost outline named -> no state held
    write_now(k, main, {'AK': {'US-0026'}, 'MT': {'US-4548'}})
    rc, out = run(td, ap)
    check(rc == 0 and 'Drop guard US-MT::1 park(s) lost their outline or their official grade, every one on the approved list' in out, 'all lost outlines named: nothing held, exit 0')

    # Fable's review (1): a park that keeps its rows but is no longer graded official must be named too (real case: Flathead NF
    # US-4502, same record sgmtd744, official -> approximate by D7 'only a copy' in run 44528656941's Montana file)
    write_now(k, main, {'MT': {'US-4548'}})
    d = json.loads((k / 'US-MT.json').read_text()); d['parks']['US-4501']['g'] = 'approximate'; (k / 'US-MT.json').write_text(json.dumps(d, indent=1))
    rc, out = run(td, ap)
    check(rc == 1 and 'NOT on the approved list: US-4501' in out, 'a park that keeps its outline but loses its official grade, not named: held')
    ap3 = td / 'approved3.json'
    ap3.write_text(json.dumps({'states': {'MT': {'parks': ['US-4548', 'US-4501'], 'decided_by': 'KPC owner, test'}}}))
    rc, out = run(td, ap3)
    check(rc == 0 and 'US-MT::2 park(s) lost their outline or their official grade, every one on the approved list' in out, 'the same grade drop, named: let through')

    # NEVER WORSE, PARK BY PARK (the real event: run US-44567326912 saved Idaho and Oregon because evidence batch 01's regained
    # outlines offset the lost ones in the net count). NV, on no list, loses one outline and gains another: official 10 -> 10.
    write_now(k, main, {})
    d = json.loads((k / 'US-NV.json').read_text()); d['parks']['US-9001'] = park(False); d['parks']['US-9999'] = park(True)
    (k / 'US-NV.json').write_text(json.dumps(d, indent=1))
    rc, out = run(td)
    check(rc == 1 and 'US-NV::1 park(s) lost their outline or their official grade: US-9001' in out and 'official parks 10 ->' not in out,
          'limit 0: one outline lost, one gained (net 0): the state is HELD by the park, where the count rule saw nothing')
    rc, out = run(td, env={'KPC_DROP_PCT': '3', 'KPC_DROP_MIN': '1'})
    check(rc == 0, 'outside store mode (3%, more than 1 park) the percent rule is unchanged: not held')
    rc, out = run(td, env={'KPC_DROP_OK': 'NV'})
    check(rc == 0 and 'US-NV::1 park(s) lost their outline or their official grade (US-9001), let through by KPC_DROP_OK' in out, 'KPC_DROP_OK still lets an unlisted state through')
    ap4 = td / 'approved4.json'; ap4.write_text(json.dumps({'states': {'NV': {'parks': ['US-9001'], 'decided_by': 'KPC owner, test'}}}))
    rc, out = run(td, ap4)
    check(rc == 0 and 'US-NV::1 park(s) lost their outline or their official grade, every one on the approved list' in out, 'the same loss, named by the owner: let through')

    # STOP: a state named in "stop" is held whatever its list says (Montana: Custer Gallatin keeps an outline but loses two thirds
    # of its land, which no list of lost outlines can see); a stopped state that was not rebuilt is left alone; approve refuses it
    write_now(k, main, {'MT': {'US-4548'}})
    ap5 = td / 'approved5.json'
    ap5.write_text(json.dumps({'states': {'MT': {'parks': ['US-4548'], 'decided_by': 'KPC owner, test'}}, 'stop': {'MT': 'US-4501 waits for rule R-FJ1.'}}))
    rc, out = run(td, ap5)
    check(rc == 1 and 'US-MT::STOP: US-4501 waits for rule R-FJ1.' in out, 'STOP holds a state even when every lost park is named')
    write_now(k, main, {})
    rc, out = run(td, ap5)
    check(rc == 0 and 'STOP' not in out, 'a stopped state that this run did not change is not reported')

    # a list entry with no decided_by is ignored: MT goes back to the percent rule
    write_now(k, main, {'MT': {'US-4548'}})
    ap2 = td / 'approved2.json'
    ap2.write_text(json.dumps({'states': {'MT': {'parks': ['US-4548']}}}))
    rc, out = run(td, ap2)
    check('approved list has no decided_by: ignored' in out and rc == 1 and 'US-MT::official parks 12 -> 11' in out and 'US-MT::1 park(s) lost their outline or their official grade: US-4548' in out,
          'an entry with no decided_by is ignored (held by the count and by the park)')

    # no list at all = exactly the old guard
    write_now(k, main, {})
    rc, out = run(td)
    check(rc == 0 and '0 failed' in out, 'no list and no drop: the old guard passes')

    # approve: written from a fact check's lost.json for the named states only
    lj = td / 'lost.json'
    lj.write_text(json.dumps([{'area': 'US-MT', 'ref': 'US-4548'}, {'area': 'US-AK', 'ref': 'US-0026'}, {'area': 'US-NV', 'ref': 'US-9001'}]))
    out_f = td / 'written.json'
    gj = td / 'grade-drops.json'; gj.write_text(json.dumps([{'area': 'US-MT', 'ref': 'US-4502'}]))
    r = subprocess.run([sys.executable, str(GUARD), 'approve', '--lost', str(lj), str(gj), '--states', 'MT AK', '--decided-by', 'KPC owner, test', '--out', str(out_f)],
                       capture_output=True, text=True)
    d = json.loads(out_f.read_text())
    st_f = td / 'stopfile.json'; st_f.write_text(json.dumps({'states': {}, 'stop': {'MT': 'US-4501 waits for rule R-FJ1.'}}))
    r2 = subprocess.run([sys.executable, str(GUARD), 'approve', '--lost', str(lj), str(gj), '--states', 'MT AK', '--decided-by', 'KPC owner, test', '--out', str(st_f)],
                        capture_output=True, text=True)
    d2 = json.loads(st_f.read_text())
    check('MT: NOT WRITTEN, the state is on STOP' in r2.stdout and 'MT' not in d2['states'] and d2['states']['AK']['parks'] == ['US-0026'] and d2['stop'].get('MT'),
          'approve refuses a stopped state, writes the others and keeps the stop')
    check(r.returncode == 0 and d['states']['MT']['parks'] == ['US-4502', 'US-4548'] and d['states']['AK']['parks'] == ['US-0026'] and 'NV' not in d['states'],
          'approve writes the lost outlines and the grade drops of the named states only, with decided_by')

check(not (ROOT / '.github' / 'key-drop-approved.json').exists() or
      json.loads((ROOT / '.github' / 'key-drop-approved.json').read_text()).get('states') in ({}, None),
      'the repo carries no approved state today (nothing is let through before the owner\'s yes)')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
