#!/usr/bin/env python3
"""PR rebuild level 1-5 (KPC owner, 2026-11-12). NOT a rule file: it never decides a join.

Every PR gets a level. The owner can override the auto level with a body line
`Rebuild-level: N` (wins) or a label `rebuild:N`. A full rebuild is only the monthly
run or an explicit owner full_rebuild; even level 5 is a verify, not KPC_FULL_BUILD.

  1  minor: tests, docs, workflows, NOT_RULES scripts — no key rebuild
  2  named-area data (a hand file, one country's outlines, one hold) — rebuild only those areas
  3  a declared rule-scope change that names some areas, not all
  4  shared data that can move many area hashes — rebuild areas whose hashes moved
  5  a rule-file change, an undeclared change, or a declared scope of all — verify existing
     keys against the new rules; rebuild only an area whose output actually changes

Usage:
  kpc_rebuild_level.py files PATH [PATH...]     print the auto level and a reason
  kpc_rebuild_level.py diff [--base SHA]        files changed vs base (default: origin/main)
  kpc_rebuild_level.py pr --body FILE --labels LABELS --files PATH...
      print the winning level (body, then labels, then auto) and write GITHUB_OUTPUT / GITHUB_ENV
"""
import os, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def notice(m):
    print(f'::notice title=Rebuild level::{m}', flush=True)


def _freeze(root=ROOT):
    sys.path.insert(0, str(pathlib.Path(root) / '.github/scripts'))
    import kpc_key_freeze as KF
    return KF


def _norm(path):
    p = str(path or '').replace('\\', '/').lstrip('./')
    return p


def _rule_files(KF, root=ROOT):
    out = set()
    for paths in KF.RULE_FILES.values():
        out.update(_norm(x) for x in paths)
    out.add(_norm(KF.VERSION_FILE))
    out.update(_norm(x) for x in KF.SCOPE_FILES.values())
    return out


def _not_rules(KF):
    return set(KF.NOT_RULES)


def _scope_level(files, KF, root=ROOT):
    """If a rule file changed, 3 when every touched kind has a declared named scope; else 5."""
    rules = _rule_files(KF, root)
    kinds = []
    for kind, paths in KF.RULE_FILES.items():
        if any(_norm(f) in {_norm(x) for x in paths} or _norm(f) == _norm(KF.VERSION_FILE) or _norm(f) == _norm(KF.SCOPE_FILES.get(kind) or '')
               for f in files):
            kinds.append(kind)
    if not kinds:
        return 0
    named = True
    for kind in kinds:
        try:
            ch = (KF.load_json if hasattr(KF, 'load_json') else None)
        except Exception:
            ch = None
        # pending_scope needs the previous hash; for a PR we only look at the scope file's 'changes'
        sp = pathlib.Path(root) / KF.SCOPE_FILES.get(kind, '')
        try:
            import json
            doc = json.loads(sp.read_text(encoding='utf-8')) if sp.is_file() else {}
        except Exception:
            return 5
        changes = doc.get('changes') or []
        if not changes:
            return 5  # undeclared
        scopes = []
        for c in changes:
            if not isinstance(c, dict):
                continue
            sc = c.get('states') or c.get('provinces') or c.get('countries') or c.get('scope') or c.get('areas')
            scopes.append(sc)
        if not scopes or any(s in (None, 'all', ['all'], 'ALL') or (isinstance(s, (list, tuple)) and any(str(x).lower() == 'all' for x in s)) for s in scopes):
            return 5
        if any(not s for s in scopes):
            return 5
    return 3


def file_level(path, KF, root=ROOT):
    f = _norm(path)
    base = pathlib.Path(f).name
    if f in _rule_files(KF, root) or f.startswith('.github/') and base in _rule_files(KF, root):
        return 5
    if base in _not_rules(KF):
        return 1
    if f.startswith('tests/') or f.endswith('.md') or f.startswith('.github/workflows/') or f == '.github/rebuild-levels.md':
        return 1
    if f.startswith('data/outlines/hand/') or re.search(r'data/outlines/hand/hand-(US|CA|W)-', f):
        return 2
    if f == 'data/outlines/world-expected-holds.approved.json' or f.endswith('world-expected-holds.approved.json'):
        return 2
    if re.search(r'data/(us-key|ca-key|world-key|parkinfo|outlines)/', f) and not f.endswith('area-tables.json'):
        # a named area file (US-XX.json, W-XX, one parkinfo country) is 2; a shared table is 4
        if re.search(r'/(US-[A-Z]{2}|CA-[A-Z]{2,3}|W-[A-Z]{2}|[A-Z]{2})\.json(\.gz)?$', f):
            return 2
        if f.endswith('layers.json') or f.endswith('download-sources.json') or f.endswith('extra-layers.json') or f.endswith('sheet-countries.json'):
            return 4
        if 'world-expected-holds' in f or 'world-baselines' in f:
            return 2
        return 4
    if f.startswith('.github/scripts/'):
        return 1 if base in _not_rules(KF) else 5
    if f.startswith('.github/'):
        return 1
    return 1


def auto_level(files, root=ROOT):
    KF = _freeze(root)
    files = [_norm(f) for f in files if f and not str(f).startswith('.git/')]
    if not files:
        return 1, 'no changed files (level 1)'
    # rule-file / scope first
    sl = _scope_level(files, KF, root)
    per = [(f, file_level(f, KF, root)) for f in files]
    mx = max((n for _, n in per), default=1)
    if sl:
        mx = max(mx, sl)
        # a rule file's raw file_level is 5; a declared named scope caps it at 3 unless something else is 4+
        if sl == 3 and mx == 5 and all(n < 5 or _norm(f) in _rule_files(KF, root) or pathlib.Path(f).name in _rule_files(KF, root) or _norm(f) in {_norm(x) for x in KF.SCOPE_FILES.values()} or _norm(f) == _norm(KF.VERSION_FILE) for f, n in per):
            mx = 3
    why = ', '.join(f'{f}={n}' for f, n in per if n == mx) or 'auto'
    return mx, f'auto from changed files: {why}'


def body_level(text):
    if not text:
        return None
    m = re.search(r'(?im)^rebuild-level:\s*([1-5])\s*$', text)
    return int(m.group(1)) if m else None


def labels_level(labels):
    if not labels:
        return None
    if isinstance(labels, str):
        labels = re.split(r'[\s,]+', labels)
    hit = []
    for lab in labels:
        m = re.fullmatch(r'rebuild:([1-5])', str(lab).strip(), re.I)
        if m:
            hit.append(int(m.group(1)))
    return max(hit) if hit else None


def decide(files, body=None, labels=None, root=ROOT):
    auto, why = auto_level(files, root)
    body_n = body_level(body)
    lab_n = labels_level(labels)
    if body_n is not None:
        return body_n, f'owner override in the PR body (Rebuild-level: {body_n}); auto was {auto}'
    if lab_n is not None:
        return lab_n, f'owner override by label rebuild:{lab_n}; auto was {auto}'
    return auto, why


def git_diff_files(base, root=ROOT):
    r = subprocess.run(['git', '-C', str(root), 'diff', '--name-only', f'{base}...HEAD'], capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(['git', '-C', str(root), 'diff', '--name-only', base], capture_output=True, text=True)
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


def _write_out(level, why):
    notice(f'level {level}: {why}')
    for dest, fmt in ((os.environ.get('GITHUB_OUTPUT'), 'level={}\nreason={}\n'),
                      (os.environ.get('GITHUB_ENV'), 'REBUILD_LEVEL={}\nREBUILD_LEVEL_REASON={}\n')):
        if dest:
            with open(dest, 'a', encoding='utf-8') as f:
                f.write(fmt.format(level, why.replace('\n', ' ')))
    print(level)
    return 0


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    root = ROOT
    if a[:1] == ['files']:
        lv, why = auto_level(a[1:], root)
        print(f'{lv}\t{why}')
        return _write_out(lv, why)
    if a[:1] == ['diff']:
        base = 'origin/main'
        if '--base' in a:
            i = a.index('--base')
            base = a[i + 1]
        files = git_diff_files(base, root)
        lv, why = auto_level(files, root)
        print(f'{lv}\t{why}')
        return _write_out(lv, why)
    if a[:1] == ['pr']:
        body, labels, files, base = '', '', [], 'origin/main'
        i = 1
        while i < len(a):
            if a[i] == '--body' and i + 1 < len(a):
                body = pathlib.Path(a[i + 1]).read_text(encoding='utf-8') if a[i + 1] != '-' else sys.stdin.read(); i += 2
            elif a[i] == '--body-text' and i + 1 < len(a):
                body = a[i + 1]; i += 2
            elif a[i] == '--labels' and i + 1 < len(a):
                labels = a[i + 1]; i += 2
            elif a[i] == '--base' and i + 1 < len(a):
                base = a[i + 1]; i += 2
            elif a[i] == '--files':
                files = a[i + 1:]; break
            else:
                files.append(a[i]); i += 1
        if not files:
            files = git_diff_files(base, root)
        lv, why = decide(files, body=body, labels=labels, root=root)
        print(f'{lv}\t{why}')
        return _write_out(lv, why)
    print(__doc__)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
