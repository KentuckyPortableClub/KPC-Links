#!/usr/bin/env python3
"""kpc_fers_area_run.py: ONE list of steps for a 2-fer area run, the same on GitHub and on the PC (KPC owner, 2026-11-16; handoff
'proof of work', item 3). kpc-store-fers.yml (KPC-Store) and the PC runner both call this; the PC runner keeps only its own paths
(a small settings file) and its .bat files. Two PC runs measured nothing because copied steps were missing (overlay, last files,
saved cache): with one list there is nothing to copy.

The steps, in order (each one exactly as kpc-fers.yml in KPC-Data runs it today):
  overlay       lay KPC-Data's moved data over the KPC-Links checkout       bash .github/scripts/kpc_overlay.sh <kpcdata>
  last-files    the last 2-fer files: <kpcdata>/data/fers -> data/fers (unpacked), and this area's saved-live copy when given
  key-gate      refuse a stale or incomplete key for this region            <kpcdata>/.github/scripts/kpc_fers_key_gate.py
  seed          a one-state job starts from its area's saved pair answers   reuse-p<1-3>-<seed>.json -> reuse-p<1-3>-<tag>.json
  bot           the passes. A store run: ONE process (kpc_fers_store.py chain 1,2,3,5: the store is loaded once). Any other
                run: the separate passes (PASS=1, 2, 3, 5), the time split as today. Under the memory guard when KPC-Data has it.
                DONE IS DECIDED BY THE RECEIPT (kpc_fers_receipt.py check), never by the log: no receipt, a pass missing, an area
                not 'measured' or another rules hash = red, whatever the exit code said.
  expected      the missing check (Kentucky: kpc_fers_known.py first)       .github/scripts/kpc_fers_expected.py
  jump          the jump report (item 5): areas whose 2-fer count moved a lot, listed for a spot check before release; holds nothing
  pick          each state saved on its own (fail closed on a shared pair)  <kpcdata>/.github/scripts/kpc_fers_states.py pick
  annotate      the change notes on the new files                           <kpcdata>/.github/scripts/kpc_fers_annotate.py
  waiting-room  a changed live 2-fer file goes to the waiting room          <kpcdata>/.github/scripts/kpc_waiting_room.py divert
Not here (each caller keeps its own): the checkouts, the store copy's location, the push, the release of anything.
The POTA activation history step is not in the list (item 7, owner's rule of Nov 16): official boundaries are the proof; the
missing check reads the stored copies it already has. Nothing here calls POTA or any map server.

  python3 .github/scripts/kpc_fers_area_run.py --kpcdata kpcdata --region na --states US-RI --tag us-ri [--seed TAG] [--store on]
         [--minutes 320] [--settings pc-settings.json] [--only bot,expected] [--from bot] [--dry-run]
Exit: 0 every step done (the receipt says measured); 1 a step failed (its own line says which); 2 the receipt is red; 4 bad usage.
Standard library only. Not a rule file (it decides no pair; kpc_key_freeze.NOT_RULES)."""
import argparse, gzip, json, os, pathlib, shlex, shutil, subprocess, sys, time

STEPS = ('overlay', 'last-files', 'key-gate', 'seed', 'bot', 'expected', 'jump', 'pick', 'annotate', 'waiting-room')
PASSES = (1, 2, 3, 5)
HERE = pathlib.Path(__file__).resolve().parent
SETTINGS_KEYS = ('kpcdata', 'links', 'python', 'store_dir', 'store_kind', 'private_out', 'private_log', 'saved_live', 'minutes', 'mem_guard')


class StepFailed(Exception):
    def __init__(self, step, why, code=1):
        super().__init__(f'{step}: {why}'); self.step, self.why, self.code = step, why, code


def say(kind, title, msg):
    print(f'::{kind} title={title}::{msg}', flush=True)


class Run:
    def __init__(self, a):
        self.a = a
        self.links = pathlib.Path(a.links).resolve()
        self.kd = pathlib.Path(a.kpcdata).resolve() if a.kpcdata else None
        self.py = a.python or sys.executable
        self.tag = a.tag or (a.states or a.region).lower().replace(' ', '-')
        self.store = str(a.store or 'off').lower() in ('1', 'on', 'yes', 'true')
        self.out = self.links / 'data' / 'fers'
        self.log = []

    def env(self, **kw):
        e = dict(os.environ)
        e.update({'REGION': self.a.region, 'STATES': self.a.states or '', 'RUN_TAG': self.a.tag or '', 'KPCDATA': str(self.kd or ''), 'LINKS': str(self.links)})
        if self.store:
            e['KPC_FERS_FROM_STORE'] = 'on'
            for k, n in (('store_dir', 'KPC_FERS_STORE_DIR'), ('store_kind', 'KPC_FERS_STORE_KIND'), ('private_out', 'KPC_FERS_PRIVATE_OUT'), ('private_log', 'KPC_FERS_PRIVATE_LOG')):
                v = getattr(self.a, k, None)
                if v: e[n] = str(v)
            if e.get('KPC_FERS_PRIVATE_OUT'): self.out = pathlib.Path(e['KPC_FERS_PRIVATE_OUT']).resolve()
        e.update({k: str(v) for k, v in kw.items()})
        return e

    def sh(self, step, cmd, cwd=None, ok=(0,), **env):
        shown = ' '.join(shlex.quote(str(c)) for c in cmd)
        print(f'[{step}] {shown}', flush=True)
        if self.a.dry_run: return 0
        r = subprocess.run([str(c) for c in cmd], cwd=str(cwd or self.links), env=self.env(**env))
        if r.returncode not in ok: raise StepFailed(step, f'{pathlib.Path(str(cmd[1] if len(cmd) > 1 else cmd[0])).name} stopped with exit {r.returncode}', r.returncode)
        return r.returncode

    def data_script(self, name):
        if self.kd is None: raise StepFailed('setup', '--kpcdata is needed for this step', 4)
        return self.kd / '.github' / 'scripts' / name

    # ------------------------------------------------------------------ the steps
    def overlay(self):
        self.sh('overlay', ['bash', self.links / '.github/scripts/kpc_overlay.sh', self.kd or ''])

    def last_files(self):
        print(f'[last-files] {self.kd}/data/fers -> data/fers (unpacked)', flush=True)
        if self.a.dry_run: return
        for d in ('cache/us', 'cache/ca', 'cache/world', 'cache/fers'): (self.links / d).mkdir(parents=True, exist_ok=True)
        dst = self.links / 'data' / 'fers'
        if dst.exists(): shutil.rmtree(dst)
        src = (self.kd / 'data' / 'fers') if self.kd else None
        if src and src.is_dir(): shutil.copytree(src, dst)
        else: dst.mkdir(parents=True, exist_ok=True)
        for f in dst.glob('*.json.gz'):
            with gzip.open(f, 'rb') as i, open(f.with_suffix(''), 'wb') as o: shutil.copyfileobj(i, o)
            f.unlink()
        if self.a.saved_live:
            sl = pathlib.Path(self.a.saved_live)
            if sl.is_file(): shutil.copy(sl, self.links / 'cache' / 'fers' / sl.name)
            else: say('notice', '2-fer saved outlines', f'no saved-live copy at {sl.name} (a first run reads live and saves)')

    def key_gate(self):
        self.sh('key-gate', [self.py, self.data_script('kpc_fers_key_gate.py')])

    def seed(self):
        s, t = self.a.seed, self.a.tag
        if not (s and t): print('[seed] no seed for this job', flush=True); return
        for p in (1, 2, 3):
            a_, b_ = self.links / f'data/fers/reuse-p{p}-{s}.json', self.links / f'data/fers/reuse-p{p}-{t}.json'
            print(f'[seed] {a_.name} -> {b_.name} (only when {b_.name} is missing)', flush=True)
            if not self.a.dry_run and not b_.exists() and a_.exists(): shutil.copy(a_, b_)

    def _guarded(self, cmd):
        mg = self.a.mem_guard
        if mg in (None, '', 'auto'):
            g = self.data_script('kpc_mem_guard.py') if self.kd else None
            return ([self.py, g, '--'] + cmd) if g and g.is_file() else cmd
        return cmd if mg == 'off' else [self.py, mg, '--'] + cmd

    def bot(self):
        minutes = int(float(self.a.minutes or 320))
        # the step's own hard end (KPC_HARD_END, epoch seconds) is the caller's: the workflow sets it from its step limit, the PC has none
        if self.store:   # item 2: one process, the store loaded once
            self.sh('bot', self._guarded([self.py, self.links / '.github/scripts/kpc_fers_store.py', 'chain', ','.join(map(str, PASSES))]), MINUTES=minutes)
        else:            # shapes differ between passes (Kentucky's live layers, downloads): the separate passes, as today
            end = time.time() + minutes * 60
            for p in PASSES:
                left = int((end - time.time()) // 60)
                cap = minutes * 2 // 5 if p == 1 else left // 2 if p == 2 else left * 4 // 5 if p == 3 else left
                cap = min(cap, left)
                if cap < 5: say('notice', '2-fer bot', f'no time left for pass {p} (next run carries on)'); break
                self.sh('bot', self._guarded([self.py, self.links / '.github/scripts/kpc_fers.py']), PASS=p, MINUTES=cap)
        if self.a.region == 'ky': self.sh('bot', [self.py, self.links / '.github/scripts/kpc_fers_known.py'])
        if self.a.dry_run: return
        import kpc_fers_receipt as R
        sys.path.insert(0, str(HERE))
        try:
            import kpc_key_freeze as KFZ
            rules = KFZ.rules_hash('fers', self.links)
        except Exception: rules = None  # noqa: BLE001
        tag = self.a.tag or ('ky' if self.a.region == 'ky' else '-'.join(sorted((self.a.states or '').split())) or self.a.region)
        try: doc = json.loads(R.receipt_path(self.out, tag).read_text(encoding='utf-8'))
        except Exception: doc = None  # noqa: BLE001
        probs = R.check(doc, PASSES, rules)
        if probs:
            for x in probs: say('error', '2-fer receipt', f'{tag}: {x}')
            raise StepFailed('bot', f'the receipt is red ({len(probs)} problem(s))', 2)
        print(f'[bot] receipt {tag}: every pass measured', flush=True)

    def expected(self):
        if self.a.region == 'ky': self.sh('expected', [self.py, self.links / '.github/scripts/kpc_fers_expected.py'], AREA='ky')
        elif self.a.states and self.a.region == 'na': self.sh('expected', [self.py, self.links / '.github/scripts/kpc_fers_expected.py'])
        else: print('[expected] not for this region', flush=True)

    def jump(self):
        """Item 5 (KPC owner, 2026-11-16): after the run, before anything is released: the jump report. It lists, never holds or marks."""
        tag = self.a.tag or ('ky' if self.a.region == 'ky' else '-'.join(sorted((self.a.states or '').split())) or self.a.region)
        areas = 'US-KY' if self.a.region == 'ky' else ','.join((self.a.states or '').split())
        cmd = [self.py, self.links / '.github/scripts/kpc_fers_jump.py', '--old', (self.kd / 'data/fers') if self.kd else '', '--new', self.links / 'data/fers', '--tag', tag]
        if areas: cmd += ['--areas', areas]
        try: self.sh('jump', cmd)
        except StepFailed as e: say('warning', '2-fer jump report', f'not made ({e}); nothing is held by it')

    def pick(self):
        if self.a.dry_run: print('[pick] big files gzipped (over 20 MB); per-state pick into', self.kd, flush=True)
        else:
            for f in (self.links / 'data/fers').glob('*.json'):
                if f.stat().st_size > 20_000_000: subprocess.run(['gzip', '-9nf', str(f)], check=True)
        states = 'US-KY' if self.a.region == 'ky' else (self.a.states or '')
        if not self.a.dry_run and self.kd:   # a world area's own file is copied as it is (kpc-fers.yml does the same before pick)
            for st in states.split():
                if st.startswith('W-'):
                    for f in (self.links / f'data/fers/{st}.json', self.links / f'data/fers/{st}.json.gz'): self._copy_if_changed(f)
        rc = self.sh('pick', [self.py, self.data_script('kpc_fers_states.py'), 'pick'], ok=(0, 2), STATES=states, JOB=f'bot {self.tag}')
        if rc == 2: raise StepFailed('pick', 'two states of this job hold the same pair: nothing saved (fail closed)', 1)
        if not self.a.dry_run and self.kd:   # the area's own report / looked / missing / receipt files, and the shared ones (as kpc-fers.yml)
            fs = list((self.links / 'data/fers').glob(f'*-{self.a.tag}.json')) if self.a.tag else []
            for g in ('*-ky.json', 'known-answers.json', 'ky-outline-drift.json', 'report.json', 'same-outline.json', 'missing-na.json', 'looked-*.json', 'expected-*.json'):
                fs += list((self.links / 'data/fers').glob(g))
            for f in sorted(set(fs)): self._copy_if_changed(f)

    def _copy_if_changed(self, f):
        if not f.is_file(): return
        d = self.kd / 'data' / 'fers' / f.name
        if d.is_file() and d.read_bytes() == f.read_bytes(): return
        d.parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, d)

    def annotate(self):
        states = 'US-KY' if self.a.region == 'ky' else (self.a.states or '')
        self.sh('annotate', [self.py, self.data_script('kpc_fers_annotate.py'), '--new', 'data/fers', '--live', self.kd, '--states', states])

    def waiting_room(self):
        self.sh('waiting-room', [self.py, '.github/scripts/kpc_waiting_room.py', 'divert', 'data/fers'], cwd=self.kd, LINKS='..' if self.kd and self.kd.parent == self.links else str(self.links))


def settings(a):
    """The PC runner's own paths (a small JSON file); a command-line value wins."""
    if not a.settings: return a
    try: s = json.loads(pathlib.Path(a.settings).read_text(encoding='utf-8'))
    except Exception as e: raise SystemExit(f'--settings: {e}')  # noqa: BLE001
    for k in SETTINGS_KEYS:
        if getattr(a, k, None) in (None, '') and s.get(k) not in (None, ''): setattr(a, k, s[k])
    return a


def parse(argv=None):
    ap = argparse.ArgumentParser(description='One list of steps for a 2-fer area run (GitHub and the PC).')
    ap.add_argument('--region', default='na', choices=('na', 'ky', 'world'))
    ap.add_argument('--states', default=''); ap.add_argument('--tag', default=''); ap.add_argument('--seed', default='')
    ap.add_argument('--store', default='off', help='on = a store run (one process, the store loaded once)')
    ap.add_argument('--kpcdata', default=None); ap.add_argument('--links', default=None); ap.add_argument('--python', default=None)
    ap.add_argument('--store-dir', dest='store_dir', default=None); ap.add_argument('--store-kind', dest='store_kind', default=None)
    ap.add_argument('--private-out', dest='private_out', default=None); ap.add_argument('--private-log', dest='private_log', default=None)
    ap.add_argument('--saved-live', dest='saved_live', default=None); ap.add_argument('--minutes', default=None)
    ap.add_argument('--mem-guard', dest='mem_guard', default=None, help="auto (KPC-Data's kpc_mem_guard.py when present), off, or a path")
    ap.add_argument('--settings', default=None, help="the PC runner's paths (JSON: " + ', '.join(SETTINGS_KEYS) + ')')
    ap.add_argument('--only', default='', help='comma list of steps'); ap.add_argument('--from', dest='start', default='')
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--list', action='store_true')
    a = settings(ap.parse_args(argv))
    a.links = a.links or str(HERE.parent.parent)
    return a


def main(argv=None):
    a = parse(argv)
    if a.list: print('\n'.join(STEPS)); return 0
    steps = list(STEPS)
    if a.start:
        if a.start not in STEPS: print(f'unknown step {a.start!r}: {", ".join(STEPS)}'); return 4
        steps = steps[steps.index(a.start):]
    if a.only:
        want = [x.strip() for x in a.only.split(',') if x.strip()]
        bad = [x for x in want if x not in STEPS]
        if bad: print(f'unknown step(s) {bad}: {", ".join(STEPS)}'); return 4
        steps = [x for x in steps if x in want]
    if a.region != 'world' and a.region != 'ky' and not a.states and a.store in ('on', '1', 'yes', 'true'):
        print('a store run names its areas (--states)'); return 4
    r = Run(a)
    sys.path.insert(0, str(HERE))
    for s in steps:
        t = time.time()
        try: getattr(r, s.replace('-', '_'))()
        except StepFailed as e:
            say('error', f'2-fer area run: {e.step}', e.why)
            return 2 if e.code == 2 else 1
        print(f'[{s}] done in {time.time() - t:.0f} s', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
