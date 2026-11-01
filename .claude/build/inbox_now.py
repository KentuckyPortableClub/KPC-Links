#!/usr/bin/env python3
"""INBOX, ONLY WHAT IS NEW (chat 10, Oct 31 2026; Brandon 10:00 PM 'make it happen': save usage).
  python3 .claude/build/inbox_now.py <chat number>
Prints ONLY your NEW items (no DONE / NOTED / WIRED ... mark yet) in full, your in-progress items (RUNNING / PARTLY / NEXT / WAITING / TODO)
as one short line each, and, for the graders, the waiting room's grade list (KPC-Data data/status/grade-queue.md: only new + changed rows).
Read THIS instead of the whole inbox file. Open the file itself only to mark items (Edit by a unique piece of the item's text)."""
import re, subprocess, sys, pathlib, signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

n = (sys.argv[1:] or ['?'])[0]
f = pathlib.Path(__file__).resolve().parents[1] / 'inbox' / f'chat-{n}.md'
text = f.read_text(encoding='utf-8')
CLOSED = re.compile(r'^- (?:\(\w\) )?(?:\*\*)?(?:DONE|NOTED|ANSWERED|MOVED|BUILT|RELEASED|CLOSED|WIRED|SUPERSEDED)\b', re.I)
BUSY = re.compile(r'^- (?:\*\*)?(?:RUNNING|PARTLY|PART DONE|NEXT|WAITING|TODO|STARTED|HELD|PREP ONLY|DECIDED)\b', re.I)
HIST = re.compile(r'^- (?:\*\*)?(?:REPORT TO HQ \()?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}\b[^:]{0,40}:')   # history / report lines
import datetime as dt
DATED = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2},? \d{1,2}(?::\d\d)? ?[AP]M|^- (?:\*\*)?(?:FROM|HQ|REPORT)\b')   # an item header: a date WITH a time, or FROM / HQ
MON = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}


def age(b):
    ds = [dt.date(dt.date.today().year, MON[m.group(1)], int(m.group(2))) for m in re.finditer(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b', b.split('\n')[0][:400]) if int(m.group(2)) <= 31]
    ds += [dt.date(int(y), int(m), int(d)) for y, m, d in re.findall(r'\b(20\d\d)-(\d\d)-(\d\d)\b', b.split('\n')[0][:200])]   # bot lines carry ISO dates
    return (dt.date.today() - max(ds)).days if ds else 0

new, busy, stale = [], [], []
for sec in re.split(r'(?m)^(?=## )', text):
    if not sec.startswith('## OPEN') and not sec.startswith('# '): continue
    cur = []
    for l in sec.split('\n')[1:] + ['- ']:
        sub = l.startswith('- ') and cur and not (CLOSED.match(l) or BUSY.match(l) or DATED.search(l[:400]))   # an undated, unmarked bullet = a sub-point of the item above
        if l.startswith('- ') and cur and not sub:
            b = '\n'.join(cur).strip(); cur = []
            if not b or b.startswith('- **DAILY HABITS') or CLOSED.match(b) or HIST.match(b): pass
            elif BUSY.match(b): busy.append(b.split('\n')[0][:220])
            elif age(b) > 1: stale.append(b.split('\n')[0][:220])
            else: new.append(b if len(b) < 3000 else b[:3000] + ' …(cut: open the file for the rest)')
        if l.startswith('- ') or cur: cur.append(l)
print(f'# chat {n}: {len(new)} NEW item(s), {len(busy)} in progress ({len(text) // 1024} KB file not read)\n')
for b in new: print(b + '\n')
if busy:
    print('## In progress (one line each)')
    for b in busy: print(b)
if stale:
    print('\n## STALE? (older than a day, no mark: mark DONE / NOTED, or do it)')
    for b in stale: print(b)
if n in ('2', '8', '11'):
    q = subprocess.run(['gh', 'api', 'repos/KentuckyPortableClub/KPC-Data/contents/data/status/grade-queue.md', '-H', 'Accept: application/vnd.github.raw'], capture_output=True, text=True).stdout
    if q: print('\n## Waiting room grade list (only NEW + CHANGED rows need a look)\n' + q[:6000])
