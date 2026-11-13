#!/bin/bash
# Oct 27 (chat 2): ONE safe save for the KPC-Data bots. The Kentucky river-bank run lost its whole result: its 'pull --rebase'
# save failed 5 times while other bots pushed. This keeps ONLY the files this job changed, puts them on top of a fresh copy of
# main (no rebase, no conflicts) and pushes; a failure prints the git error as a notice. Never fails.
# STRICT=1 = exit 1 when the save failed (the run goes red and emails: the assembly line). Otherwise never fails.
# usage: kpc_push_data.sh <repo dir> "<commit message>" <path> [path…]   (paths to look for changes in, e.g. data)
cd "$1" || exit 0; shift; MSG="$1"; shift
git config user.name 'github-actions[bot]'; git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
# PR2 (fewer saves, Nov 2): a save whose only changes are time stamps / run links is skipped (KPC_SAVE_STAMPS=keep = off).
# The same code is .github/scripts/kpc_stamp_only.py; it is inline here because the KPC-Data bots fetch only this one file.
kpc_stamp_filter() {
python3 - <<'KPC_STAMP_PY' || true
"""PR2 (fewer saves, Nov 2 2026): put back every STAGED file whose only change is a time stamp, so a quiet run commits nothing.
Run inside the repo after 'git add' and before 'git diff --cached --quiet' / 'git commit'.
A file counts as stamp-only when, compared with HEAD:
  JSON  - the only differences are in stamp keys (updated, updated_at, generated, generated_at, last_checked, checked_at, built, made, last_run; Nov 3) AND the
          stamp's DATE part did not change (so a file's 'updated' still moves once a day), or in GitHub run links (actions/runs/N);
  text  (.md .txt .log, ONLY status-type files: a path with /status/ or a name with board, flow, heartbeat, summary, watchdog,
          health) - the only differences are clock times (12:34, 2026-11-02T12:34Z, '3 h old', '5 min ago') or run links; the dates
          themselves still count as a change. (Other text files may hold real times, e.g. opening hours, so they are never touched.)
The files are only put back when EVERY changed file is stamp-only: a run with one real change saves everything as before.
Anything else (new file, deleted file, unreadable, a real change) is left alone. Never fails. KPC_SAVE_STAMPS=keep switches it off."""
import json, os, re, subprocess, sys

STAMP = {'updated', 'updated_at', 'generated', 'generated_at', 'last_checked', 'checked_at', 'built', 'made', 'last_run'}   # Nov 3: + built, made, last_run
IDS = {'build'}   # Nov 3: a build id (US-<run id>) changes on every run: ignored whole (it moves with the real changes)
# Nov 2 review (Quality 5b): the waiting room's verdicts.json says 'checked' and heartbeat.json says 'ok'. They count as stamps only
# when the value is a date / time, so a 'checked' or 'ok' that holds a real answer is still a change.
STAMP_IF_TIME = {'checked', 'ok'}
IS_TIME = re.compile(r'^\d{4}-\d\d-\d\d([T ]|$)')
RUN = re.compile(r'actions/runs/\d+(/jobs?/\d+)?(/attempts/\d+)?')
CLOCK = [(re.compile(r'(\d{4}-\d\d-\d\d)[T ]\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:?\d\d| ?UTC| ?CST| ?CDT| ?CT)?'), r'\1'),
         (re.compile(r'\b\d{1,2}:\d\d(:\d\d)?( ?[AaPp]\.?[Mm]\.?)?( ?(UTC|CST|CDT|CT|Z))?\b'), 'HH:MM'),
         (re.compile(r'\b\d+(\.\d+)? ?(min|mins|minutes|h|hrs|hours|s|sec|seconds)( old| ago)\b'), 'N ago'),
         (RUN, 'actions/runs/N')]
TEXT = ('.md', '.txt', '.log')
STATUSY = re.compile(r'(^|/)status/|(board|flow|heartbeat|summary|watchdog|health)[^/]*$', re.I)


def norm(x, key=None):
    if isinstance(x, dict): return {k: norm(v, k) for k, v in x.items()}
    if isinstance(x, list): return [norm(v) for v in x]
    if isinstance(x, str):
        if key in IDS: return 'ID'
        if key in STAMP or (key in STAMP_IF_TIME and IS_TIME.match(x)): return x[:10]   # the date part still counts
        return RUN.sub('actions/runs/N', x)
    return x


def text_norm(s):
    for rx, rep in CLOCK: s = rx.sub(rep, s)
    return s


def git(*a, binary=False):
    r = subprocess.run(['git', *a], capture_output=True)
    return r.returncode, (r.stdout if binary else r.stdout.decode('utf-8', 'replace'))


def stamp_only(f):
    rc, old = git('show', f'HEAD:{f}', binary=True)
    if rc != 0: return False
    rc, new = git('show', f':{f}', binary=True)   # the staged copy
    if rc != 0 or old == new: return False
    if len(old) > 60_000_000 or len(new) > 60_000_000: return False
    try: o, n = old.decode('utf-8'), new.decode('utf-8')
    except UnicodeDecodeError: return False
    if f.endswith(('.json', '.geojson')):
        try: return norm(json.loads(o)) == norm(json.loads(n))
        except ValueError: return False
    if f.endswith(TEXT) and STATUSY.search(f): return text_norm(o) == text_norm(n)
    return False


def main():
    if os.environ.get('KPC_SAVE_STAMPS') == 'keep': return
    rc, out = git('diff', '--cached', '--name-only', '-z', '--diff-filter=M')
    if rc != 0: return
    files = [f for f in out.split('\0') if f]
    if not files: return
    rc, other = git('diff', '--cached', '--name-only', '-z', '--diff-filter=ADRCT')   # added / deleted / renamed = a real change
    if rc != 0 or other.strip('\0'): return
    put_back = [f for f in files if stamp_only(f)]
    if len(put_back) != len(files):
        if put_back: print(f'stamp filter: {len(files) - len(put_back)} real change(s), so everything is saved as before')
        return
    for f in put_back:
        git('reset', '-q', 'HEAD', '--', f); git('checkout', '-q', 'HEAD', '--', f)
    if put_back:
        print(f"stamp filter: only time stamps changed ({len(put_back)} file(s): {' '.join(put_back)[:400]}), nothing to save")


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'stamp filter: left everything alone ({type(e).__name__}: {str(e)[:120]})')  # noqa: BLE001
    sys.exit(0)
KPC_STAMP_PY
}
# >>> kpc_quiet_gate: inline copy of .github/scripts/kpc_quiet_gate.py (a test keeps them equal; the KPC-Data bots fetch only this file)
kpc_quiet_gate() {
python3 - <<'KPC_QUIET_PY'
#!/usr/bin/env python3
"""Nov 10 2026 (quiet runs): skip a save that only carries BOOKKEEPING when this bot saved a little while ago.

Run inside the repo after 'git add' and the stamp filter, before 'git diff --cached --quiet' / 'git commit'.
Exit code 0 = go on and save as before. Exit code 3 = skip this save (everything staged is put back).
Nothing here ever fails a run: any doubt = save as before.

A staged change is BOOKKEEPING when it is only:
  - a file under data/status/ (boards, bot lines, grade queue, inbox lists),
    except data/status/key-check/last-<key>.json and data/status/key-check/<key>-<build>.json/.md
    (the key-check save the 2-fer run waits on; these always land)
  - data/waiting/heartbeat.json, verdicts-last.json, held-since.json (the waiting room's own notes; NOT the append-only verdicts log)
  - data/waiting/verdicts.json when no file's verdict changed (same path -> same verdict; only the check time / re-test counts moved)
Anything else staged (data, answer keys, waiting-room files, a new or deleted file) is MATERIAL: the save goes ahead at once,
and the bookkeeping rides along.
An ALARM also goes at once: a board line / bot line that turns red or amber.
The skip only happens when the same bot (the commit message up to the first ':') already saved within KPC_QUIET_HOURS hours
(default 3; 0 = off). The recent-save look is 'git log --since' on a shallow-since fetch; if it cannot be read, the save goes ahead.
Env: KPC_QUIET_MSG = the commit message, KPC_QUIET_HOURS."""
import json, os, re, subprocess, sys

# data/waiting/verdicts.jsonl(.gz) is NOT on this list: it is an append-only log, a skipped save would lose its new lines
BOOK = re.compile(r'^data/status/|^data/waiting/(heartbeat|verdicts-last|held-since)\.json$')
# Nov 13: last-<key>.json and the <key>-<build> report must always save. Yesterday the 3-hour
# bookkeeping skip dropped last-us.json for US-43293787778 and the US 2-fers sat waiting.
# Other key-check files (pin-cover, also-in, health, dropped) stay bookkeeping.
KEY_CHECK_MUST_SAVE = re.compile(
    r'^data/status/key-check/(last-(?:us|ca|world)\.json|(?:us|ca|world)-[^/]+\.(?:json|md))$')



def git(*a):
    r = subprocess.run(['git', *a], capture_output=True)
    return r.returncode, r.stdout.decode('utf-8', 'replace')


def load(spec):
    rc, out = git('show', spec)
    try: return json.loads(out) if rc == 0 else None
    except ValueError: return None


def verdicts(d):
    if not isinstance(d, dict): return None
    return {r.get('path'): r.get('verdict') for r in d.get('results') or [] if isinstance(r, dict)}


def is_book(f):
    if KEY_CHECK_MUST_SAVE.match(f): return False
    if BOOK.match(f): return True
    if f == 'data/waiting/verdicts.json':
        a, b = verdicts(load(f'HEAD:{f}')), verdicts(load(f':{f}'))
        return a is not None and a == b
    return False


def alarm(files):
    for f in files:
        if not (f.endswith('board.json') or '/status/bots/' in f): continue
        old, new = load(f'HEAD:{f}') or {}, load(f':{f}') or {}
        ro = old.get('bots', {'_': old}) if isinstance(old, dict) else {}
        rn = new.get('bots', {'_': new}) if isinstance(new, dict) else {}
        for k, r in rn.items():
            if isinstance(r, dict) and r.get('result') in ('red', 'amber') and (ro.get(k) or {}).get('result') != r.get('result'):
                return k
    return ''


def saved_recently(prefix, hours):
    if not prefix: return False
    rc, _ = git('fetch', '-q', f'--shallow-since={int(__import__("time").time() - hours * 3600)}', 'origin', 'main')
    if rc != 0: return False
    # the bot's own saves only: a subject that IS the prefix or starts with '<prefix>:' ('board' must not match 'flow board' / 'scoreboard')
    rc, out = git('log', '--format=%s', f'--since={int(hours * 3600)} seconds ago', 'FETCH_HEAD')
    if rc != 0: return False
    return any(s == prefix or s.startswith(prefix + ':') for s in out.splitlines())


def main():
    try: hours = float(os.environ.get('KPC_QUIET_HOURS', '3'))
    except ValueError: hours = 3.0
    if hours <= 0: return 0
    rc, out = git('diff', '--cached', '--name-only', '-z')
    files = [f for f in out.split('\0') if f] if rc == 0 else []
    if not files: return 0
    rc, other = git('diff', '--cached', '--name-only', '-z', '--diff-filter=ADRCT')
    if rc != 0: return 0
    # a new or deleted file is only bookkeeping when it is itself on the bookkeeping list
    if not all(is_book(f) for f in files): return 0
    a = alarm(files)
    if a:
        print(f'quiet gate: bookkeeping with an alarm ({a} turned amber/red): saved at once')
        return 0
    msg = os.environ.get('KPC_QUIET_MSG', '')
    prefix = msg.split(':', 1)[0].strip()
    if not saved_recently(prefix, hours): return 0
    print(f"::notice title=Quiet save::only bookkeeping changed ({len(files)} file(s)) and '{prefix}' saved within {hours:g} h: not saved this time")
    return 3


if __name__ == '__main__':
    try: rc = main()
    except Exception as e:  # noqa: BLE001
        print(f'quiet gate: left everything alone ({type(e).__name__}: {str(e)[:120]})'); rc = 0
    sys.exit(rc)
KPC_QUIET_PY
}
# <<< kpc_quiet_gate
# Nov 2 review (Quality 5a): files that several bots write are MERGED with main's copy instead of copied over it whole:
#   data/waiting/*.jsonl (append-only)  main's lines + this job's lines that main does not have yet (no line is lost)
#                                       a .jsonl.gz is the same log (KPC-Data stores verdicts.jsonl.gz); .gz wins when both exist
#   data/waiting/verdicts.json          results by file path: this job's result wins; main's result is kept while that file is still held
#   data/waiting/verdicts-last.json     by path, this job wins
#   data/waiting/held-since.json        by path, the EARLIER date wins; a file that is gone from data/waiting/in/, or that this job
#                                       judged and did not hold, drops out
# Anything that cannot be read is copied as before (this job's copy). KPC_SAVE_MERGE=off switches it off.
kpc_merge_shared() {   # $1 = dir holding main's copies; run in the repo after this job's files are copied on top
KPC_MAIN="$1" python3 - "${CH[@]}" <<'KPC_MERGE_PY' || true
import gzip, json, os, sys
M = os.environ['KPC_MAIN']
def load(p):
    with open(p, encoding='utf-8') as fh: return json.load(fh)
def read_text(path):
    # Nov 6: verdicts.jsonl is stored as verdicts.jsonl.gz. Opening the gz bytes as text drops every line.
    # .gz wins when both the plain path and the .gz sibling are on disk.
    gz = path if path.endswith('.gz') else path + '.gz'
    plain = path[:-3] if path.endswith('.gz') else path
    use = gz if os.path.isfile(gz) else plain
    if not os.path.isfile(use):
        raise FileNotFoundError(path + ' (plain or .gz)')
    if use.endswith('.gz'):
        with gzip.open(use, 'rt', encoding='utf-8') as fh: return fh.read()
    with open(use, encoding='utf-8') as fh: return fh.read()
def write_text(path, text):
    if path.endswith('.gz'):
        with gzip.open(path, 'wt', encoding='utf-8') as fh: fh.write(text)
    else:
        with open(path, 'w', encoding='utf-8') as fh: fh.write(text)
def held(path): return os.path.exists(os.path.join('data/waiting/in', path))
n = 0
for f in sys.argv[1:]:
    mf = os.path.join(M, f)
    if not os.path.isfile(mf) or not os.path.isfile(f): continue
    try:
        logical = f[:-3] if f.endswith('.gz') else f
        if logical.startswith('data/waiting/') and logical.count('/') == 2 and logical.endswith('.jsonl'):
            main = read_text(mf).splitlines(); ours = read_text(f).splitlines()
            have = set(main); add = [l for l in ours if l not in have]
            out = main + add
            if out != ours:
                write_text(f, '\n'.join(out) + ('\n' if out else ''))
                n += 1
        elif f == 'data/waiting/verdicts.json':
            a, b = load(mf), load(f)
            mine = {r.get('path'): r for r in b.get('results') or [] if isinstance(r, dict)}
            extra = [r for r in a.get('results') or [] if isinstance(r, dict) and r.get('path') not in mine and held(r.get('path') or '')]
            if extra:
                b['results'] = list(b.get('results') or []) + extra
                with open(f, 'w', encoding='utf-8') as fh: json.dump(b, fh, indent=1, ensure_ascii=False)
                n += 1
        elif f == 'data/waiting/verdicts-last.json':
            a, b = load(mf), load(f)
            c = {**a, **b}
            if c != b:
                with open(f, 'w', encoding='utf-8') as fh: json.dump(c, fh, ensure_ascii=False, separators=(',', ':'))
                n += 1
        elif f == 'data/waiting/held-since.json':
            a, b = load(mf), load(f)
            try: mine = {r.get('path'): r.get('verdict') for r in load('data/waiting/verdicts.json').get('results') or [] if isinstance(r, dict)}
            except Exception: mine = {}  # noqa: BLE001
            c = {}
            for k in set(a) | set(b):
                if not held(k): continue
                if k not in b and mine.get(k) not in (None, 'HOLD'): continue   # judged here and not held any more
                v = [x for x in (a.get(k), b.get(k)) if x]
                if v: c[k] = min(v)
            if c != b:
                with open(f, 'w', encoding='utf-8') as fh: json.dump(c, fh, indent=1)
                n += 1
    except Exception as e:  # noqa: BLE001
        print(f'::error title=Save merge::{f} could not be read ({type(e).__name__}: {str(e)[:120]}); this job\'s copy was kept')
if n: print(f'merge: {n} shared file(s) merged with the newest main instead of overwritten')
KPC_MERGE_PY
}
for p in "$@"; do git add -A -- "$p" 2>/dev/null; done   # Nov 1 (chat 10): one path at a time: ONE missing path (data/intake/found-layers-stage2.json) made git add nothing at all, so the world finder saved nothing since Oct 30
# B7 (Oct 30): file names are read NUL-separated, so a path with a space is one path, not two
mapfile -d '' CH < <(git diff --cached --name-only -z --diff-filter=AMR); mapfile -d '' DEL < <(git diff --cached --name-only -z --diff-filter=D)
[ ${#CH[@]} -eq 0 ] && [ ${#DEL[@]} -eq 0 ] && { echo "nothing changed"; exit 0; }
T=$(mktemp -d)
for f in "${CH[@]}"; do mkdir -p "$T/$(dirname "$f")" && cp -a "$f" "$T/$f"; done
for i in 1 2 3 4 5 6; do
  if git fetch -q --depth=1 origin main && git reset -q --hard FETCH_HEAD; then
    M=$(mktemp -d)
    if [ "${KPC_SAVE_MERGE:-on}" != off ]; then
      for f in "${CH[@]}"; do case "$f" in data/waiting/*.jsonl|data/waiting/*.jsonl.gz|data/waiting/verdicts.json|data/waiting/verdicts-last.json|data/waiting/held-since.json)
        [ -f "$f" ] && mkdir -p "$M/$(dirname "$f")" && cp -a "$f" "$M/$f" ;; esac; done
    fi
    cp -a "$T"/. . 2>/dev/null
    for f in "${DEL[@]}"; do git rm -q --ignore-unmatch -- "$f" >/dev/null 2>&1; done
    [ "${KPC_SAVE_MERGE:-on}" != off ] && kpc_merge_shared "$M"
    rm -rf "$M"
    [ ${#CH[@]} -gt 0 ] && git add -A -- "${CH[@]}" 2>/dev/null
    kpc_stamp_filter
    git diff --cached --quiet && { echo "nothing new to save"; exit 0; }
    # Nov 10 (quiet runs): bookkeeping-only and this bot saved a few hours ago -> not saved this time (KPC_QUIET_HOURS=0 = off)
    KPC_QUIET_MSG="$MSG" kpc_quiet_gate; [ $? -eq 3 ] && { git reset -q --hard FETCH_HEAD; exit 0; }
    git commit -qm "$MSG"
    ERR=$(git push -q origin HEAD:main 2>&1) && { echo "saved: ${#CH[@]} files"; exit 0; }
  else ERR="fetch failed"; fi
  WHY=$(echo "$ERR" | grep -v "Trace:" | grep -v "^remote: *$" | tr "\n" " "); echo "::notice title=Save try $i::${WHY:0:600}"   # Oct 29: the Alaska save hid its reason behind 6 Trace lines
  sleep $((i * 10))   # Oct 30: this wait had slipped into the comment above, so the 6 tries ran back to back
done
echo "::notice title=Save FAILED::${#CH[@]} files not saved"
[ "$STRICT" = 1 ] && exit 1   # the assembly line: a failed save = a red run (HQ Oct 27)
exit 0
