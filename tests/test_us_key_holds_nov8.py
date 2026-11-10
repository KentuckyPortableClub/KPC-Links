"""Nov 8 (Quality KEY NO on US-42487204632): kpc_join_check.py (not a rules file) now
 1. carries a person's NO across a record re-key (hma -> sgnvi, sgakh -> sgnvh): a NEW join on a park the previous key left as a
    pin, whose name (+ acres) matches the park's NO fingerprint or a previous 'a person said NO' record, puts the park back to a pin;
 2. holds a NEW join (record id not joined in the previous key) over 5 km (15 km stays the rule for the rest);
 3. exempts per id on a signed override: an unsigned record the previous key had out goes back to 'c'.
Rules hashes unchanged (us a066624520b4, ca 8feccbb7d9ee, world 6a5969a25d2c; world 6444287722b9 since the declared CH rename in #76)."""
import json, os, pathlib, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_join_check as J, kpc_key_freeze as KF
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)

check({k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')} == {'us-key': 'ee5fc3c49dd7', 'ca-key': '570b09c3cb52', 'world-key': '6444287722b9'},
      'rules hashes unchanged')
check('kpc_join_check.py' in KF.NOT_RULES, 'kpc_join_check.py is not a rules file')

T = pathlib.Path(tempfile.mkdtemp(prefix='kpc-holds-nov8-'))
def run(parks, prev, signed=None, nos=None):
    f = T / 'US-NV.json'; f.write_text(json.dumps({'parks': parks}), encoding='utf-8')
    J.SIGNED.clear(); J.SIGNED_BY.clear(); J.NOS.clear()
    for r, ids in (signed or {}).items(): J.SIGNED[r] = set(ids); J.SIGNED_BY[r] = 'Brandon'
    J.NOS.update(nos or {})
    rows, held, ch = J.mark_file(str(f), {}, True, 'hold', {}, False, None, str(T), prev)
    return json.loads(f.read_text(encoding='utf-8'))['parks'], held
try:
    hma = lambda i, km: {'n': 'Rocky Hills BLM HMA', 'g': 'official', 'm': [[i, 'Rocky Hills', 84432, 'name']], 'bk': [i, km, '', '-'], 'c': []}
    pin = {'n': 'Rocky Hills BLM HMA', 'g': 'pin', 'm': [], 'c': [], 'bk': [1, 0.0]}
    # 1. NO carried by fingerprint (nofp) across the re-key, even at 0.2 km
    p, h = run({'US-1': hma('sgnvi433', 0.2)}, {'US-1': pin}, nos={'US-1': [('Rocky Hills', 84050.8, 'hma12')]})
    check(p['US-1']['g'] == 'pin' and not p['US-1']['m'] and 'hma12' in h[0]['reason'], '1: NO on hma12 follows the land to sgnvi433 (pin again)')
    # 1. NO carried from the previous key's 'a person said NO' row (no nofp saved: US-13181 style)
    prev = dict(pin, c=[['sgakh1214', 'Pine Forest', 16227, 'a person said NO to this record (overrides.json no: ...)']])
    p, h = run({'US-2': {'n': 'Pine Forest', 'g': 'official', 'm': [['sgnvh1214', 'Pine Forest', 16227, 'name']], 'bk': ['sgnvh1214', .11], 'c': []}}, {'US-2': prev})
    check(p['US-2']['g'] == 'pin' and 'sgakh1214' in h[0]['reason'], '1: sgakh1214 NO follows to sgnvh1214')
    # 1. not carried: different acres, a park already joined before, a signed id, a reviewed join
    p, h = run({'US-3': dict(hma('sgnvi433', .2), m=[['sgnvi433', 'Rocky Hills', 5000, 'name']])}, {'US-3': pin}, nos={'US-3': [('Rocky Hills', 84050.8, 'hma12')]})
    check(p['US-3']['g'] == 'official', '1: same name, very different acres: not the same land, kept')
    p, h = run({'US-4': hma('sgnvi433', .2)}, {'US-4': hma('sgnvi999', .2)}, nos={'US-4': [('Rocky Hills', 84050.8, 'hma12')]})
    check(p['US-4']['g'] == 'official', '1: a park the previous key already joined is not re-judged (duplicate-record NOs)')
    p, h = run({'US-5': hma('sgnvi433', .2)}, {'US-5': pin}, signed={'US-5': ['sgnvi433']}, nos={'US-5': [('Rocky Hills', 84050.8, 'hma12')]})
    check(p['US-5']['g'] == 'official', '1: a person signed the new id: kept')
    # 2. 5 km for a new join; 15 km for a join the previous key had
    p, h = run({'US-6': hma('sgnvi448', 9.2)}, {'US-6': pin})
    check(p['US-6']['g'] == 'pin' and 'over 5 km for a new join' in h[0]['reason'], '2: a new join 9.2 km out is held')
    p, h = run({'US-7': hma('sgnvi448', 4.9)}, {'US-7': pin})
    check(p['US-7']['g'] == 'official', '2: a new join 4.9 km out is kept')
    p, h = run({'US-8': hma('sgnvi448', 9.2)}, {'US-8': hma('sgnvi448', 9.2)})
    check(p['US-8']['g'] == 'official', '2: the same join as the previous key at 9.2 km: only the 15 km rule applies, kept')
    p, h = run({'US-9': hma('sgnvi448', 9.2)}, {})
    check(p['US-9']['g'] == 'official', '2: no previous key to compare with (git cannot tell): only the 15 km rule')
    # 3. signed exemption per id
    pc = {'n': 'Little Pee Dee', 'g': 'official', 'ac': 10979, 'bk': ['sgscc11', 0.0], 'm': [['sgscc11', 'LPD HP/WMA', 10455, 'words'], [254041, 'LPD', 10168, 'reviewed'],
          [254043, 'LPD - Twin Bays Tract', 218, 'words']], 'c': []}
    pv = {'n': 'Little Pee Dee', 'g': 'official', 'm': [[254129, 'x', 298, 'name']], 'c': [['sgscc11', 'LPD HP/WMA', 10455, 'check (rule R-G8)'], [254043, 'Twin Bays', 218, 'held (rule G-1)']]}
    p, h = run({'US-3917': pc}, {'US-3917': pv}, signed={'US-3917': ['254041']})
    check([x[0] for x in p['US-3917']['m']] == [254041] and {str(x[0]) for x in p['US-3917']['c']} >= {'sgscc11', '254043'} and 'ac' not in p['US-3917'],
          '3: only the signed 254041 stays joined; sgscc11 and 254043 go back to c')
    # Nov 8: Quality KEY YES on US-42504172086 -> the us-key entry is gone; the join check compares with git HEAD again
    jb = (ROOT / 'data/key-join-base.json')
    check(not jb.is_file() or 'us-key' not in json.loads(jb.read_text(encoding='utf-8')), 'data/key-join-base.json has no us-key entry after the accepted rebuild')
    check(J.join_base(str(ROOT / 'data/us-key/US-NV.json'), str(ROOT), {}) == 'HEAD', 'us-key compares with HEAD again')
    check(J.join_base(str(ROOT / 'data/us-key/US-NV.json'), str(ROOT), {'KPC_JOIN_BASE': 'abc1234'}) == 'abc1234' and J.join_base(str(T / 'x.json'), str(ROOT), {}) == 'HEAD',
          'join_base: KPC_JOIN_BASE wins; no base file = HEAD')
    # real data: the US-42487204632 build (fbacca65) against the key before it
    have = subprocess.run(['git', 'cat-file', '-e', 'fbacca65^{commit}'], cwd=ROOT, capture_output=True).returncode == 0
    if have and os.environ.get('KPC_HOLDS_REAL', '1') == '1':
        ok, _ = J.approvals(str(ROOT), 'us', {}); res = {}
        for st in ('NV', 'SC'):
            f = f'data/us-key/US-{st}.json'
            cur = subprocess.run(['git', 'show', 'fbacca65:' + f], cwd=ROOT, capture_output=True).stdout
            prev = json.loads(subprocess.run(['git', 'show', 'fbacca65^:' + f], cwd=ROOT, capture_output=True).stdout or b'{}').get('parks') or {}
            t = T / f'real-{st}.json'; t.write_bytes(cur)
            J.mark_file(str(t), {}, True, 'hold', ok, False, None, str(ROOT), prev); res.update(json.loads(t.read_text(encoding='utf-8'))['parks'])
        far7 = ['US-10844', 'US-13024', 'US-13029', 'US-13034', 'US-13048', 'US-13128', 'US-13130']
        check(all(res[r]['g'] == 'pin' for r in far7 + ['US-13181']), 'real: the 7 far NV HMAs and US-13181 Pine Forest are pins again')
        hm = [r for r, p in res.items() if 'Herd Management' in str(p.get('t')) and 'a person said NO' in str((p.get('held') or {}).get('why'))]
        check(len(hm) >= 22, f'real: {len(hm)} NV HMAs held by a carried NO (Quality counted 22)')
        check([x[0] for x in res['US-3917']['m']] == [254041], 'real: US-3917 joins only the signed 254041')
    else: print('SKIP real-data check (fbacca65 not in this clone)')
finally:
    shutil.rmtree(T, ignore_errors=True)
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
