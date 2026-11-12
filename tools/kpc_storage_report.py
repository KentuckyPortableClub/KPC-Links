#!/usr/bin/env python3
"""Where are the bytes? A read-only storage report for a checkout of KPC-Links, KPC-Data or KPC-Archive.

  python3 tools/kpc_storage_report.py [REPO] [--rev HEAD] [--out DIR] [--compare OTHER] [--refs-from OTHER]
                                      [--cap 1000000] [--near 0.9] [--top 50] [--since "14 days ago"] [--all] [--history-objects]

REPO defaults to the current folder. It prints:
  - total tracked size and file count; size and count by top-level folder, by data/ subfolder and by file type
  - the biggest files; every file over the cap and every file within --near of it (default 1 MB and 90 %)
  - groups of files with the SAME content (by git blob id, or by sha1 when REPO is not a git checkout)
  - near-duplicates by name: x.json next to x.json.gz, -mobile pictures, dated copies (nov7, 2026-11-07), .claude/ notes
  - UNREFERENCED CANDIDATES: a simple heuristic, not proof. A file is 'referenced' when its name (or its name without .gz)
    appears in a page / script / style / workflow / test of this repo (or of --refs-from), 'folder only' when only its folder
    path appears (a name built in code, e.g. 'data/us-key/' + st + '.json'), and a CANDIDATE when neither appears.
    Check every candidate by hand before moving anything; this script never deletes or moves a file.
  - with git history: the paths rewritten most often since --since, ranked by bytes per day (current size x saves per day: the upper
    bound), and for the top --measure (10) the bytes git REALLY needs per save, measured by packing the local versions with
    'git pack-objects --stdout' (writes nothing). Compressed files (.gz .png .pdf ...) are flagged: a .gz rewritten all through
    is stored whole every save; an appended .gz written the same way each time deltas fine; the measured column tells which.
    On a shallow clone it says how far back the history it can see goes.
  - --history-objects: the biggest objects in ALL of the local history (git rev-list --objects --all), with their size on disk.
  - --compare OTHER: files with the same content in both checkouts (same path or another path), and same path / other content.

--out DIR writes the same as CSV files plus summary.txt. DIR must be OUTSIDE the measured repo (refused otherwise unless
--allow-inside), so the report never adds files to the tree. Without --out nothing is written anywhere.
--rev REV measures that commit's tree (works on a --no-checkout clone). Without it a git checkout is measured at HEAD (the
committed files: edits not yet committed are not counted).

Safe: standard library only, no network (git runs with GIT_ALLOW_PROTOCOL=kpc-none, i.e. no transport at all, and GIT_NO_LAZY_FETCH=1, so a blobless or
treeless clone never downloads a missing object: the report says what it could not see instead). Only read-only git commands
(ls-tree, ls-files, log, rev-list, cat-file, rev-parse, config --get). Hashes files only above --hash-min bytes when REPO is not
a git checkout (git checkouts use the blob ids git already has). KPC owner, 2026-11-11."""
import argparse, collections, csv, hashlib, io, os, re, subprocess, sys, time

CAP = 1_000_000
NO_DELTA = ('.gz', '.png', '.jpg', '.jpeg', '.pdf', '.zip', '.webp', '.gif', '.pbf', '.mbtiles', '.br', '.xz', '.7z', '.woff2', '.mp3', '.mp4')
REF_EXT = ('.html', '.htm', '.js', '.mjs', '.css', '.yml', '.yaml', '.py', '.sh', '.webmanifest', '.xml', '.toml')
REF_JSON = re.compile(r'(^|/)(RELEASED|manifest|index|tiles|files|sources|catalog|[^/]*-manifest)[^/]*\.json$', re.I)
DATED = re.compile(r'(^|[-_.])((jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{1,2}[a-z]{0,4}|20\d\d-?[01]\d-?[0-3]\d)(?=[-_.]|$)', re.I)
TOKEN = re.compile(r'[A-Za-z0-9_\-./]+')
GITENV = dict(os.environ, GIT_ALLOW_PROTOCOL='kpc-none', GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', LC_ALL='C')


def git(root, *a, binary=False, inp=None):
    try:
        r = subprocess.run(['git', '-C', root, *a], capture_output=True, input=inp, env=GITENV, timeout=900)
    except (OSError, subprocess.TimeoutExpired):
        return 1, b'' if binary else ''
    return r.returncode, (r.stdout if binary else r.stdout.decode('utf-8', 'replace'))


def ext_of(p):
    b = os.path.basename(p).lower()
    for two in ('.json.gz', '.geojson.gz', '.jsonl.gz', '.csv.gz', '.tar.gz'):
        if b.endswith(two): return two
    e = os.path.splitext(b)[1]
    return e or '(none)'


def mb(n): return f'{n / 1_000_000:,.1f} MB' if n >= 100_000 else f'{n / 1000:,.1f} KB'


class Tree:
    """The tracked files of one checkout: {path: (size or None, content id or None)} plus notes about what could not be seen."""

    def __init__(self, root, rev=None, hash_min=4096, hash_all=False):
        self.root = os.path.abspath(root); self.rev = rev; self.notes = []; self.files = {}
        self.is_git = git(self.root, 'rev-parse', '--is-inside-work-tree')[0] == 0 or git(self.root, 'rev-parse', '--git-dir')[0] == 0
        if self.is_git:
            self.partial = bool(git(self.root, 'config', '--get-regexp', r'remote\..*\.promisor')[1].strip() or
                                git(self.root, 'config', '--get', 'extensions.partialclone')[1].strip())
            self.shallow = git(self.root, 'rev-parse', '--is-shallow-repository')[1].strip() == 'true'
            if self.partial: self.notes.append('partial (blobless/treeless) clone: objects that are not local are never fetched; they show as unknown')
            if self.shallow: self.notes.append('shallow clone: history only goes back as far as it was fetched')
            self._from_git(rev or 'HEAD', rev is not None)
        else:
            self.partial = self.shallow = False
            self._from_walk(hash_min, hash_all)

    def _from_git(self, rev, rev_given):
        rc, out = git(self.root, 'ls-tree', '-r', '-l', '-z', rev)
        if rc == 0:
            for rec in out.split('\0'):
                if not rec or '\t' not in rec: continue
                meta, path = rec.split('\t', 1); f = meta.split()
                if len(f) < 4 or f[1] != 'blob': continue
                self.files[path] = (int(f[3]) if f[3].isdigit() else None, f[2])
            return
        # a partial clone with missing blobs makes 'ls-tree -l' stop: take names + ids, sizes from the work tree when it is that commit
        rc, out = git(self.root, 'ls-tree', '-r', '-z', rev)
        if rc != 0:
            self.notes.append(f'git ls-tree {rev} failed (missing objects in a partial clone?): nothing measured'); return
        wt = not rev_given and os.path.isdir(self.root) and git(self.root, 'rev-parse', '--is-inside-work-tree')[1].strip() == 'true'
        miss = 0
        for rec in out.split('\0'):
            if not rec or '\t' not in rec: continue
            meta, path = rec.split('\t', 1); f = meta.split()
            if len(f) < 3 or f[1] != 'blob': continue
            size = None
            if wt:
                try: size = os.path.getsize(os.path.join(self.root, path))
                except OSError: size = None
            if size is None:
                rc2, s = git(self.root, 'cat-file', '-s', f[2])
                size = int(s) if rc2 == 0 and s.strip().isdigit() else None
            miss += size is None
            self.files[path] = (size, f[2])
        self.notes.append(f'sizes read from the work tree / local objects; {miss} file(s) of unknown size (blob not local)')

    def _from_walk(self, hash_min, hash_all):
        self.notes.append('not a git checkout: every file under the folder is measured (.git skipped); content ids are sha1 of files'
                          + ('' if hash_all else f' of {hash_min} bytes or more (--all hashes every file)'))
        for d, subs, names in os.walk(self.root):
            subs[:] = [s for s in subs if s != '.git']
            for n in names:
                p = os.path.join(d, n); rel = os.path.relpath(p, self.root).replace(os.sep, '/')
                try: size = os.path.getsize(p)
                except OSError: continue
                cid = None
                if hash_all or size >= hash_min:
                    h = hashlib.sha1()
                    try:
                        with open(p, 'rb') as fh:
                            for chunk in iter(lambda: fh.read(1 << 20), b''): h.update(chunk)
                        cid = 'sha1:' + h.hexdigest()
                    except OSError: cid = None
                self.files[rel] = (size, cid)

    def read(self, paths, limit=2_000_000):
        """{path: text} for the given paths (only files up to `limit` bytes). Uses the commit's blobs when --rev was given."""
        out = {}
        want = [p for p in paths if (self.files.get(p, (None,))[0] or 0) <= limit]
        if self.is_git and self.rev:
            ids = [self.files[p][1] for p in want]
            rc, raw = git(self.root, 'cat-file', '--batch', binary=True, inp=('\n'.join(ids) + '\n').encode())
            if rc != 0 and not raw: self.notes.append('could not read file contents from git (missing objects?)'); return out
            buf = io.BytesIO(raw)
            for p in want:
                head = buf.readline().split()
                if len(head) < 3 or head[1] == b'missing':
                    if len(head) == 2 and head[1] == b'missing': continue
                    break
                n = int(head[2]); data = buf.read(n); buf.read(1)
                out[p] = data.decode('utf-8', 'replace')
            return out
        for p in want:
            try:
                with open(os.path.join(self.root, p), 'rb') as fh: out[p] = fh.read().decode('utf-8', 'replace')
            except OSError: pass
        return out


def group_size(files, key):
    s = collections.defaultdict(lambda: [0, 0])
    for p, (size, _) in files.items():
        k = key(p)
        if k is None: continue
        s[k][0] += size or 0; s[k][1] += 1
    return sorted(([k, v[0], v[1]] for k, v in s.items()), key=lambda r: -r[1])


def top_folder(p): return p.split('/', 1)[0] + '/' if '/' in p else '(root files)'


def data_sub(p):
    if not p.startswith('data/'): return None
    rest = p[5:]
    return 'data/' + rest.split('/', 1)[0] + '/' if '/' in rest else 'data/(files)'


def duplicates(files, min_size=1):
    by = collections.defaultdict(list)
    for p, (size, cid) in files.items():
        if cid and (size or 0) >= min_size: by[cid].append(p)
    groups = [(files[v[0]][0] or 0, sorted(v)) for v in by.values() if len(v) > 1]
    return sorted(groups, key=lambda g: -(g[0] * (len(g[1]) - 1)))


def near_duplicates(files):
    rows = []
    for p, (size, _) in files.items():
        if p.endswith('.gz') and p[:-3] in files:
            rows.append(['plain and .gz copy', p[:-3], files[p[:-3]][0] or 0, p, size or 0])
        b = os.path.basename(p)
        if re.search(r'-mobile\.(png|jpe?g|webp)$', b, re.I):
            twin = p[:-len(b)] + re.sub(r'-mobile(?=\.)', '', b)
            rows.append(['mobile picture', twin if twin in files else '', (files.get(twin) or (0,))[0] or 0, p, size or 0])
        if DATED.search(os.path.splitext(b.replace('.gz', ''))[0]):
            rows.append(['dated file name', '', 0, p, size or 0])
    for pref, why in (('.claude/', '.claude/ notes'), ('docs/', 'docs/ folder')):
        n = [(p, s) for p, (s, _) in files.items() if p.startswith(pref)]
        if n: rows.append([why + ' (whole folder)', pref, 0, f'{len(n)} files', sum(s or 0 for _, s in n)])
    return sorted(rows, key=lambda r: -(r[4] or 0))


def ref_texts(tree):
    # pages, scripts, styles, workflows, tests, index-like JSON, and any small JSON / text list (data/holidays.json names pictures)
    per_dir = collections.Counter(os.path.dirname(p) for p in tree.files)   # a folder of hundreds of data files is data, not a list of names
    paths = [p for p in tree.files if p.lower().endswith(REF_EXT) or REF_JSON.search(p) or p.startswith(('.github/', 'tests/'))
             or (p.lower().endswith(('.json', '.txt', '.webmanifest')) and (tree.files[p][0] or 0) <= 300_000 and per_dir[os.path.dirname(p)] <= 100)]
    return tree.read(paths)


def ref_index(texts):
    names, folders, prefixes = set(), set(), set()
    for src, t in texts.items():
        for tok in TOKEN.findall(t):
            tok = tok.strip('./') if tok.startswith(('./', '/')) else tok
            names.add(os.path.basename(tok))
            if len(tok) >= 3 and tok[-1] in '-_' and '/' not in tok: prefixes.add(tok)   # 'bg-' + name + '.jpg' style names
            if '/' in tok:
                parts = tok.split('/')
                for i in range(1, len(parts) + 1): folders.add('/'.join(parts[:i]).strip('/'))
    return names, folders, prefixes


def references(tree, extra_trees=()):
    texts = ref_texts(tree)
    for t in extra_trees: texts.update({f'{t.root}::{k}': v for k, v in ref_texts(t).items()})
    names, folders, prefixes = ref_index(texts)
    out = {}
    for p in tree.files:
        b = os.path.basename(p); stem = b[:-3] if b.endswith('.gz') else b
        if b in names or stem in names or (stem + '.gz') in names: out[p] = 'name'; continue
        if any(b[:k] in prefixes for k in range(3, min(len(b), 40))): out[p] = 'prefix'; continue
        d = os.path.dirname(p)
        if d and d in folders: out[p] = 'folder'; continue   # its own folder is named: a name built in code is likely
        while d and d not in folders: d = os.path.dirname(d)
        out[p] = 'ancestor' if d else 'none'   # only a parent folder further up is named (weak), or nothing at all
    return out, len(texts)


def churn(tree, since, rev='HEAD'):
    """[(path, saves, size, bytes/day, delta label, [new blob ids])], window note."""
    if not tree.is_git: return [], 'not a git checkout: no history'
    rc, out = git(tree.root, 'log', '--format=@%ct %P', '--raw', '--no-abbrev', '--no-renames', f'--since={since}', rev)
    if rc != 0: return [], 'git log failed (a treeless clone cannot list changed files without fetching): no churn measured'
    touches = collections.Counter(); blobs = collections.defaultdict(list); times = []; skip = False
    for line in out.splitlines():
        if line.startswith('@'):
            f = line[1:].split()
            # a commit with no parent (the first commit, or the cut-off end of a shallow clone) lists EVERY file: not a save
            skip = len(f) < 2
            if not skip: times.append(int(f[0]))
            continue
        if not line.startswith(':') or skip or '\t' not in line: continue
        meta, path = line.split('\t', 1); m = meta.split()
        if len(m) < 5 or m[4] == 'D': continue
        touches[path] += 1; blobs[path].append(m[3])
    if not times: return [], f'no commits since {since}'
    span = max((max(times) - min(times)) / 86400, 1 / 24)
    note = f'{len(times)} commits between {time.strftime("%Y-%m-%d %H:%M", time.gmtime(min(times)))} and {time.strftime("%Y-%m-%d %H:%M", time.gmtime(max(times)))} UTC ({span:.1f} days)'
    if tree.shallow:
        rc, b = git(tree.root, 'rev-list', '--count', rev)
        rc2, bt = git(tree.root, 'rev-list', '--count', f'--since={since}', rev)
        if b.strip() == bt.strip(): note += f'; SHALLOW: the clone ends inside the window ({b.strip()} commits fetched), so older saves are not seen'
    rows = []
    for p, n in touches.items():
        size = (tree.files.get(p) or (None,))[0]
        if size is None: continue   # deleted since, or unknown
        per_day = n / span
        label = ('maybe not (compressed: deltas only when the start of the file stays the same, e.g. an appended log; a rewrite all through is stored whole)'
                 if p.lower().endswith(NO_DELTA) else 'yes if the order is stable')
        rows.append((p, n, size, int(size * per_day), label, blobs[p]))
    return sorted(rows, key=lambda r: -r[3]), note


def measured_cost(tree, blob_ids):
    """Bytes git needs to keep these versions together (git pack-objects --stdout: nothing is written). None if a version is not local."""
    ids = sorted(set(blob_ids))
    if getattr(tree, 'local_objects', None) is None:
        # the objects this clone HAS (asking git about one it lacks would try to fetch it in a partial clone, or fail)
        rc, have = git(tree.root, 'cat-file', '--batch-all-objects', '--batch-check=%(objectname)')
        tree.local_objects = set(have.split()) if rc == 0 else set()
    local = [i for i in ids if i in tree.local_objects]
    if len(local) < 2: return None, len(local)

    def packed(objs):
        try:
            r = subprocess.run(['git', '-C', tree.root, 'pack-objects', '--stdout', '-q', '--window=50', '--depth=50'],
                               input=('\n'.join(objs) + '\n').encode(), capture_output=True, env=GITENV, timeout=600)
        except (OSError, subprocess.TimeoutExpired): return None
        return len(r.stdout) if r.returncode == 0 else None
    every, one = packed(local), packed(local[:1])
    if every is None or one is None: return None, len(local)
    return max(every - one, 0), len(local) - 1   # what the EXTRA versions cost on top of one stored copy


def history_objects(tree, top):
    if not tree.is_git: return [], 'not a git checkout'
    rc, out = git(tree.root, 'rev-list', '--objects', '--all', '--missing=print')
    if rc != 0: return [], 'git rev-list failed'
    names, missing = {}, 0
    for line in out.splitlines():
        if line.startswith('?'): missing += 1; continue
        f = line.split(' ', 1)
        names[f[0]] = f[1] if len(f) > 1 else ''
    rc, info = git(tree.root, 'cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize) %(objectsize:disk)', inp=('\n'.join(names) + '\n').encode())
    rows, total = [], 0
    for line in info.splitlines():
        f = line.split()
        if len(f) < 4 or not f[3].isdigit(): continue
        total += int(f[3])
        if f[1] == 'blob': rows.append((names.get(f[0], ''), f[0], int(f[2]), int(f[3])))
    rows.sort(key=lambda r: -r[3])
    by_path = collections.defaultdict(lambda: [0, 0])
    for p, _, _, d in rows: by_path[p][0] += d; by_path[p][1] += 1
    note = f'{len(names)} local objects, {mb(total)} on disk' + (f'; {missing} objects NOT local (partial clone): the true history is bigger' if missing else '')
    return rows[:top], note, sorted(([p, v[0], v[1]] for p, v in by_path.items()), key=lambda r: -r[1])[:top]


def compare(a, b):
    ida = collections.defaultdict(list); rows = []
    for p, (s, c) in a.files.items():
        if c: ida[c].append(p)
    same_path = other_path = 0
    for p, (s, c) in b.files.items():
        if not c: continue
        if c in ida:
            kind = 'same path' if p in ida[c] else 'other path'
            same_path += (s or 0) if kind == 'same path' else 0; other_path += (s or 0) if kind == 'other path' else 0
            rows.append([kind, s or 0, p, ' '.join(ida[c][:3])])
        elif p in a.files and a.files[p][1] and a.files[p][1] != c:
            rows.append(['same path, other content', s or 0, p, p])
    rows.sort(key=lambda r: -r[1])
    return rows, same_path, other_path


def inside(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('--rev', default=None, help='measure this commit instead of HEAD / the work tree')
    ap.add_argument('--out', default=None, help='write CSVs + summary.txt here (must be outside the repo)')
    ap.add_argument('--allow-inside', action='store_true', help='allow --out inside the measured repo')
    ap.add_argument('--compare', default=None, help='another checkout: same-content files in both')
    ap.add_argument('--compare-rev', default=None)
    ap.add_argument('--refs-from', action='append', default=[], help='another checkout whose pages / scripts may name files of this one')
    ap.add_argument('--cap', type=int, default=CAP); ap.add_argument('--near', type=float, default=0.9)
    ap.add_argument('--top', type=int, default=50)
    ap.add_argument('--since', default='14 days ago', help='history window for the churn table (git log --since)')
    ap.add_argument('--hash-min', type=int, default=4096); ap.add_argument('--all', action='store_true', help='hash every file (not a git checkout)')
    ap.add_argument('--history-objects', action='store_true', help='also list the biggest objects in all local history')
    ap.add_argument('--no-refs', action='store_true', help='skip the unreferenced-candidate scan')
    ap.add_argument('--measure', type=int, default=10, help='measure the real history cost (git pack-objects --stdout) of the top N churners (0 = off)')
    a = ap.parse_args(argv)
    t0 = time.time()
    if not os.path.isdir(a.repo): print(f'no such folder: {a.repo}'); return 2
    if a.out and inside(a.out, a.repo) and not a.allow_inside:
        print(f'refused: --out {a.out} is inside the measured repo (the report never adds files to the tree; use a folder outside it, or --allow-inside)')
        return 2
    tree = Tree(a.repo, a.rev, a.hash_min, a.all)
    F = tree.files
    L = []; say = L.append
    total = sum(s or 0 for s, _ in F.values())
    say(f'KPC storage report: {tree.root}' + (f' at {a.rev}' if a.rev else ''))
    if tree.is_git:
        say('commit: ' + git(tree.root, 'log', '-1', '--format=%H %ci', a.rev or 'HEAD')[1].strip())
    for n in tree.notes: say('note: ' + n)
    say(f'tracked: {len(F):,} files, {mb(total)} ({total:,} bytes)')
    tables = {}
    tables['by_folder'] = (['folder', 'bytes', 'files'], group_size(F, top_folder))
    tables['by_data_subfolder'] = (['folder', 'bytes', 'files'], group_size(F, data_sub))
    tables['by_type'] = (['type', 'bytes', 'files'], group_size(F, ext_of))
    for name, title in (('by_folder', 'by top-level folder'), ('by_data_subfolder', 'by data/ subfolder'), ('by_type', 'by file type')):
        rows = tables[name][1]
        if not rows: continue
        say(f'\n{title} (top 15 of {len(rows)}):')
        for k, s, n in rows[:15]: say(f'  {mb(s):>11}  {n:>6} files  {k}')
    big = sorted(((p, s) for p, (s, _) in F.items() if s is not None), key=lambda r: -r[1])
    tables['biggest'] = (['path', 'bytes'], [list(r) for r in big[:a.top]])
    say(f'\nbiggest {min(a.top, len(big))} files (first 15 shown):')
    for p, s in big[:15]: say(f'  {mb(s):>11}  {p}')
    over = [r for r in big if r[1] > a.cap]; near = [r for r in big if a.cap * a.near < r[1] <= a.cap]
    refs, nref = ({}, 0)
    if not a.no_refs:
        extra = [Tree(r) for r in a.refs_from]
        refs, nref = references(tree, extra)
    tables['over_and_near_cap'] = (['state', 'path', 'bytes', 'referenced'], [['over', p, s, refs.get(p, '?')] for p, s in over] + [['near', p, s, refs.get(p, '?')] for p, s in near])
    say(f'\nover the cap ({a.cap:,} bytes): {len(over)} file(s), {mb(sum(s for _, s in over))}; within {int(a.near * 100)} % of it: {len(near)} file(s)')
    for p, s in over[:25]: say(f'  OVER {mb(s):>11}  {p}  [{refs.get(p, "?")}]')
    for p, s in near[:10]: say(f'  near {mb(s):>11}  {p}')
    dups = duplicates(F)
    waste = sum(s * (len(g) - 1) for s, g in dups)
    tables['duplicates'] = (['bytes_each', 'copies', 'extra_bytes', 'paths'], [[s, len(g), s * (len(g) - 1), ' | '.join(g)] for s, g in dups])
    say(f'\nsame content more than once: {len(dups)} group(s), {mb(waste)} in the extra copies (git stores one blob; Pages and checkouts carry every copy)')
    for s, g in dups[:12]: say(f'  {mb(s):>11} x{len(g)}  ' + ' | '.join(g[:3]) + (' ...' if len(g) > 3 else ''))
    nd = near_duplicates(F)
    tables['near_duplicates'] = (['kind', 'twin', 'twin_bytes', 'path', 'bytes'], nd)
    kinds = collections.Counter(r[0] for r in nd)
    say('\nnear-duplicates by name: ' + (', '.join(f'{k} {v}' for k, v in kinds.items()) or 'none'))
    for r in nd[:12]: say(f'  {r[0]:<26} {mb(r[4]):>11}  {r[3]}' + (f'  (twin {r[1]})' if r[1] and not r[0].endswith('folder)') else ''))
    if refs:
        cand = sorted(((p, F[p][0] or 0, k) for p, k in refs.items() if k in ('none', 'ancestor')), key=lambda r: -r[1])
        tables['unreferenced_candidates'] = (['path', 'bytes', 'folder', 'evidence'], [[p, s, top_folder(p), 'nothing names it' if k == 'none' else 'only a folder further up is named'] for p, s, k in cand])
        say(f'\nUNREFERENCED CANDIDATES (heuristic: neither the name nor its own folder appears in {nref} page/script/style/workflow/test files'
            + (f' here or in {", ".join(a.refs_from)}' if a.refs_from else '') + f'): {len(cand)} file(s), {mb(sum(s for _, s, _ in cand))}. Check by hand; never delete on this list alone.')
        for k, s, n in group_size({p: (s, None) for p, s, _ in cand}, top_folder)[:10]: say(f'  {mb(s):>11}  {n:>6} files  {k}')
        fo = [p for p, k in refs.items() if k == 'folder']
        say(f'  ({len(fo)} more file(s) are named only through their own folder path: a name built in code, or not read at all)')
    rows, note = churn(tree, a.since, a.rev or 'HEAD')
    say(f'\nchurn since {a.since}: {note}')
    meas = {}
    for r in rows[:a.measure]:
        cost, n = measured_cost(tree, r[5])
        if cost is not None: meas[r[0]] = (cost, n)
    tables['churn'] = (['path', 'saves', 'bytes_now', 'bytes_per_day', 'git_delta', 'extra_versions_measured', 'measured_bytes_for_them', 'measured_bytes_per_save'],
                       [list(r[:5]) + ([meas[r[0]][1], meas[r[0]][0], int(meas[r[0]][0] / meas[r[0]][1])] if r[0] in meas else ['', '', '']) for r in rows])
    if rows:
        say(f'  top churners by bytes per day (size now x saves per day = the upper bound before git deltas; "kept" = what git really needs per save,')
        say(f'  measured with git pack-objects on the versions that are local, for the top {a.measure}):')
        for p, n, s, d, dl, _ in rows[:15]:
            k = f'  kept {mb(meas[p][0] / meas[p][1])}/save (measured on {meas[p][1] + 1} local versions)' if p in meas else ''
            say(f'  {mb(d):>11}/day  {n:>4} saves  {mb(s):>10}  {p}' + ('  [COMPRESSED]' if dl.startswith('maybe') else '') + k)
        gz = [r for r in rows if r[4].startswith('maybe')]
        say(f'  compressed files saved in the window: {len(gz)} ({mb(sum(r[3] for r in gz))}/day before deltas); check them with the "kept" column')
    if a.history_objects:
        r = history_objects(tree, a.top)
        if len(r) == 3:
            objs, note, by_path = r
            say(f'\nhistory objects: {note}')
            tables['history_biggest_blobs'] = (['path', 'blob', 'bytes', 'bytes_on_disk'], [list(x) for x in objs])
            tables['history_by_path'] = (['path', 'bytes_on_disk_all_versions', 'versions'], by_path)
            for p, d, n in by_path[:15]: say(f'  {mb(d):>11} on disk  {n:>4} versions  {p}')
        else: say(f'\nhistory objects: {r[1]}')
    if a.compare:
        other = Tree(a.compare, a.compare_rev, a.hash_min, a.all)
        rows, sp, op = compare(tree, other)
        tables['compare'] = (['kind', 'bytes', 'path_in_other', 'path_here'], rows)
        c = collections.Counter(r[0] for r in rows)
        say(f'\ncompared with {other.root}: same content at the same path {c["same path"]} file(s) ({mb(sp)}), at another path {c["other path"]} ({mb(op)}), '
            f'same path with other content {c["same path, other content"]}')
        for k, s, n in group_size({r[2]: (r[1], None) for r in rows if r[0] == 'same path'}, data_sub)[:10]: say(f'  same path {mb(s):>11}  {n:>6} files  {k}')
    say(f'\n(done in {time.time() - t0:.1f} s; read-only, nothing written' + (f' except the report in {a.out})' if a.out else ')'))
    text = '\n'.join(L)
    print(text)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        for name, (head, rows) in tables.items():
            with open(os.path.join(a.out, name + '.csv'), 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh); w.writerow(head); w.writerows(rows)
        with open(os.path.join(a.out, 'summary.txt'), 'w', encoding='utf-8') as fh: fh.write(text + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
