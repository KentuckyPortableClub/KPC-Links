#!/usr/bin/env python3
"""THREE-WAY MERGE FOR HAND-KEPT LISTS (Nov 2 2026 review, used by kpc_save_overwrite.sh).

Save by overwrite copies this run's files on top of the newest main. That is right for files only a bot writes, but wrong for
the few files that people (or other bots) also edit while the run is going:
  words  a space-separated list such as data/world-key/answers-countries.txt ('rebuild tonight'): the result is the newest
         main's list, minus the words THIS run took off, plus the words THIS run put on. Sorted, one line.
  lines  an inbox such as .claude/inbox/chat-11.md: the lines THIS run added are put into the newest main's copy right after
         the same line they followed in this run's copy (or at the end). Nothing else in the inbox changes.

  kpc_save_merge.py keep  <dir> words|lines <file>...   before the save: remember the start copy (HEAD) and this run's copy
  kpc_save_merge.py apply <dir>                          after the newest main is checked out: write the merged files
Loud: a file it cannot merge prints ::error and keeps the newest main's copy (never this run's copy)."""
import difflib, json, os, pathlib, subprocess, sys


def merge_words(base, ours, main):
    b, o, m = set(base.split()), set(ours.split()), set(main.split())
    out = (m - (b - o)) | (o - b)
    return (' '.join(sorted(out)) + '\n') if out else ''


def merge_lines(base, ours, main):
    bl, ol, ml = base.splitlines(), ours.splitlines(), main.splitlines()
    adds = []   # (the line before the added block in ours, [added lines])
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=bl, b=ol, autojunk=False).get_opcodes():
        if tag in ('insert', 'replace'):
            adds.append((ol[j1 - 1] if j1 > 0 else None, ol[j1:j2]))
    out = list(ml)
    for before, block in adds:
        block = [l for l in block if l not in out or not l.strip()]   # already there (a re-run): do not add twice
        if not any(l.strip() for l in block): continue
        if before is not None and before in out:
            k = out.index(before) + 1
        elif before is None:
            k = 0
        else:
            k = len(out)
        out[k:k] = block
    return '\n'.join(out) + ('\n' if main.endswith('\n') or not main else '')


def _head(path):
    r = subprocess.run(['git', 'show', f'HEAD:{path}'], capture_output=True)
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else ''


def keep(d, kind, files):
    d = pathlib.Path(d); d.mkdir(parents=True, exist_ok=True)
    plan = json.loads((d / 'merge.json').read_text()) if (d / 'merge.json').exists() else []
    for f in files:
        if not f: continue
        p = pathlib.Path(f)
        if not p.exists() and not _head(f): continue
        i = len(plan)
        (d / f'base{i}').write_text(_head(f), encoding='utf-8')
        (d / f'ours{i}').write_text(p.read_text(encoding='utf-8') if p.exists() else '', encoding='utf-8')
        plan.append({'file': f, 'kind': kind, 'i': i})
    (d / 'merge.json').write_text(json.dumps(plan))


def apply(d):
    d = pathlib.Path(d)
    if not (d / 'merge.json').exists(): return 0
    for row in json.loads((d / 'merge.json').read_text()):
        f, i = row['file'], row['i']
        base, ours = (d / f'base{i}').read_text(encoding='utf-8'), (d / f'ours{i}').read_text(encoding='utf-8')
        if base == ours: continue          # this run did not change it: the newest main's copy stays
        p = pathlib.Path(f)
        main = p.read_text(encoding='utf-8') if p.exists() else ''
        try:
            new = merge_words(base, ours, main) if row['kind'] == 'words' else merge_lines(base, ours, main)
        except Exception as e:  # noqa: BLE001
            print(f'::error title=Save merge::{f} could not be merged ({type(e).__name__}); the newest main copy is kept'); continue
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(new, encoding='utf-8')
        print(f'::notice title=Save merge::{f} merged ({row["kind"]}) on top of the newest main')
    return 0


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'keep': keep(a[1], a[2], a[3:]); sys.exit(0)
    if len(a) == 2 and a[0] == 'apply': sys.exit(apply(a[1]))
    print(__doc__); sys.exit(2)
