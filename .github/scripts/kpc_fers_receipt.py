#!/usr/bin/env python3
"""kpc_fers_receipt.py: the 2-fer bot's proof of work (KPC owner, 2026-11-16; handoff 'proof of work', item 1).

Every pass of an area run writes one small receipt file, OUT/receipt-<tag>.json (data/fers, or the private folder of a private
store run). One section per pass: parks expected, parks read, parks held (with reason counts), pairs tested, rules hash, store
date, engine version, seconds per stage, and the pass's verdict per area. Counts only: no park names, no record keys, no store
paths, so the file is safe in a public folder.

Verdicts (per area):
  measured                         the pass read the area's outlines and tested its pairs
  store empty                      the store holds the area but no outline of it could be read (0 of N parks)
  store missing: <why>             the store does not hold the area (or it was left out: stale, damaged, another format)
  measured nothing: 0 of N read    not a store run: pass 1 read no outline of an area that has official parks
  stopped early: <why>             the bot stopped before it measured anything (data missing, no ready area ...)
A border area whose store is missing is counted on the run's own area as 'neighbour store missing: N parks'. A receipt never says
that an area has no 2-fers: an area that was not measured is never 'measured'.

The workflow and the PC runner decide "done" from this file (check), never by searching the log:
  kpc_fers_receipt.py check --dir data/fers [--tag TAG] --passes 1,2,3,5 [--rules HASH]
    (no --tag: the tag the bot uses, from RUN_TAG / REGION / STATES in the environment, as kpc_fers.area_name())
    exit 0  every listed pass has a section, its every own area is 'measured', and (with --rules) the rules hash matches
    exit 2  anything else (one plain line per problem). No receipt = red.
    --allow-time-stop: a pass the step's time cut is not red (its unfinished areas keep their previous files and the next run
    carries on, as the workflow does today); a pass that did not run at all is left out of --passes by the caller.
Exit codes of kpc_fers.py that go with it: 84 stopped early, 85 an area of the run measured nothing (store empty / missing /
0 outlines read). Not a rule file: it decides no pair (kpc_key_freeze.NOT_RULES). Standard library only."""
import argparse, hashlib, json, os, pathlib, re, subprocess, sys, time

ENGINE_FILES = ('kpc_fers.py', 'kpc_fers_store.py')
EXIT_STOPPED = 84
EXIT_NOTHING = 85
HERE = pathlib.Path(__file__).resolve().parent


class StoppedEarly(Exception):
    """kpc_fers.main() stopped before it measured anything (exit 84, red; a receipt says why)."""


def receipt_path(out, tag):
    return pathlib.Path(out) / f'receipt-{tag or "run"}.json'


def engine_version(root=HERE):
    """sha256 (12 hex) of the engine files as they are on disk + the git commit when there is one."""
    h = hashlib.sha256()
    for n in ENGINE_FILES:
        f = pathlib.Path(root) / n
        h.update(n.encode() + b'\0' + (f.read_bytes().replace(b'\r\n', b'\n') if f.is_file() else b'missing') + b'\0')
    sha = ''
    try:
        r = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=10)
        if r.returncode == 0: sha = r.stdout.strip()
    except Exception: pass  # noqa: BLE001
    return {'files': h.hexdigest()[:12], 'commit': sha}


class Stages:
    """Seconds per stage of one pass: mark(name) closes the stage that ended now."""
    def __init__(self, t0=None):
        self.t = time.time() if t0 is None else t0; self.rows = []
    def mark(self, name, now=None):
        now = time.time() if now is None else now
        self.rows.append([re.sub(r'\s+', ' ', str(name))[:80], round(now - self.t, 1)]); self.t = now
    def table(self):
        out = {}
        for n, s in self.rows:   # the same stage name twice in one pass adds up
            k = re.sub(r'\s*\(.*$', '', n).strip() or n
            out[k] = round(out.get(k, 0.0) + s, 1)
        return out


REASON_RX = (('not in the outline store', 'not in the store'), ('not publishable|WDPA|private', 'held privately (licence / WDPA)'),
             ('world park', 'world park not read from the store'), ('could not be read|did not answer', 'outline could not be read'),
             ('saved copy', 'saved copy missing'), ('stale|old', 'store too old'), ('checksum|damaged|point count', 'store record damaged'))


def reason_class(why):
    w = str(why or '')
    for rx, name in REASON_RX:
        if re.search(rx, w, re.I): return name
    return 'other'


def area_verdicts(own, expected, read, store_rows=None, store_on=False):
    """own: the run's own areas; expected / read: {area: n}; store_rows: kpc_fers_store.AREA_ROWS. -> {area: verdict}."""
    out = {}
    for a in sorted(own):
        row = (store_rows or {}).get(a) or {}
        e, r = int(expected.get(a, 0)), int(read.get(a, 0))
        if store_on and row and row.get('verdict') not in (None, 'READY'):
            out[a] = f"store missing: {str(row.get('why') or row.get('verdict'))[:160]}"
        elif e and not r:
            out[a] = 'store empty' if store_on else f'measured nothing: 0 of {e} read'
        else:
            out[a] = 'measured'
    return out


def tag_from_env(env=None):
    """The receipt tag kpc_fers.py uses (RUN_TAG or area_name()), from the same environment."""
    env = os.environ if env is None else env
    tag = re.sub(r'[^a-z0-9-]', '', (env.get('RUN_TAG') or '').lower())
    region = (env.get('REGION') or 'na').strip().lower()
    only = set((env.get('STATES') or '').upper().replace(',', ' ').split())
    if tag: return tag
    if region == 'ky': return 'ky'
    return '-'.join(sorted(only)) if only else region


def merge(out, tag, pass_no, section, fresh=False):
    """One pass's section merged into the receipt (pass 1, or fresh=True, starts a new receipt). -> (path, doc); the caller writes
    it (kpc_fers.py through its guarded save_json)."""
    p = receipt_path(out, tag)
    doc = {}
    if not fresh and int(pass_no) != 1:
        try: doc = json.loads(p.read_text(encoding='utf-8'))
        except Exception: doc = {}  # noqa: BLE001
    doc['about'] = ('Proof of work of the 2-fer bot, one section per pass (kpc_fers_receipt.py). Counts only. '
                    'No receipt, or an area that is not "measured", means the area is red.')
    doc['tag'] = tag
    doc.setdefault('passes', {})[str(pass_no)] = section
    return p, doc


def check(doc, passes, rules=None, allow_time_stop=False):
    """-> list of problems (empty = done)."""
    if not isinstance(doc, dict) or not doc.get('passes'): return ['no receipt: the run measured nothing it can prove']
    bad = []
    for p in passes:
        s = (doc.get('passes') or {}).get(str(p))
        if not s: bad.append(f'pass {p}: no receipt section (the pass did not finish)'); continue
        if s.get('stopped'): bad.append(f"pass {p}: stopped early: {s['stopped']}")
        areas = s.get('areas') or {}
        if not areas and not s.get('stopped'): bad.append(f'pass {p}: no area measured')
        for a, v in sorted(areas.items()):
            if v != 'measured': bad.append(f'pass {p}: {a}: {v}')
        if rules and s.get('rules_hash') != rules: bad.append(f"pass {p}: rules hash {s.get('rules_hash')} is not {rules}")
        if s.get('stopped_for_time') and not allow_time_stop: bad.append(f'pass {p}: stopped for time (unfinished areas keep their previous files)')
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('check'); c.add_argument('--dir', default='data/fers'); c.add_argument('--tag', default='')
    c.add_argument('--passes', default='1,2,3,5'); c.add_argument('--rules', default='')
    c.add_argument('--allow-time-stop', action='store_true', help="a pass cut by the step's time is not red (its unfinished areas keep their files; the next run carries on)")
    a = ap.parse_args(argv)
    a.tag = a.tag or tag_from_env()
    p = receipt_path(a.dir, a.tag)
    try: doc = json.loads(p.read_text(encoding='utf-8'))
    except Exception: doc = None  # noqa: BLE001
    probs = check(doc, [x for x in a.passes.replace(' ', ',').split(',') if x], a.rules or None, a.allow_time_stop)
    for x in probs: print(f'::error title=2-fer receipt::{a.tag}: {x}', flush=True)
    if probs: return 2
    print(f'2-fer receipt {a.tag}: every pass measured ({a.passes})', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
