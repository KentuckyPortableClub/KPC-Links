#!/usr/bin/env python3
"""27 Nov 2026: tests of the front-door button tools/pc-keys/V2-FRONT-DOOR.bat (job 5 of the small v2 jobs).
A .bat cannot be run here, so these are reading checks on its bytes and its labels (every goto has its label, every step calls a
quoted path, nothing downloads, the four buttons are named, a missing one is said plainly). Prints PASS / FAIL, ends ALL PASS."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


raw = (ROOT / 'tools' / 'pc-keys' / 'V2-FRONT-DOOR.bat').read_bytes()
txt = raw.decode('ascii')                                  # plain ASCII only: a non-ASCII byte would raise here
lines = txt.split('\r\n')
low = txt.lower()
check('front door: every line ends CRLF (no bare LF), plain ASCII, one screen of steps (under 90 lines)',
      b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n', b'') and raw.endswith(b'\r\n') and len(lines) < 90)
check('front door: the four buttons are named with their PC paths, store room and page reader by full path, state prep and build in 5-ANSWER-KEY-TEST',
      all(p in txt for p in (r'C:\KPC\3-MAP-STORE-US-CA\LAYER-RECORDS.bat', r'C:\KPC\6-TOOLS\PAGE-READER\PAGE-READER.bat',
                              r'C:\KPC\5-ANSWER-KEY-TEST\V2-STATE-PREP.bat', r'C:\KPC\5-ANSWER-KEY-TEST\V2-BUILD.bat')))
steps = [l for l in lines if re.match(r'\s*echo\s+\s*[1-4]\s{2}\S', l, re.I)]
check('front door: the steps are shown in order 1 store room, 2 page reader, 3 state prep, 4 build, each with its found / MISSING mark',
      [re.match(r'\s*echo\s+\s*(\d)', l, re.I).group(1) for l in steps] == ['1', '2', '3', '4'] and all(re.search(r'%S[1-4]%\s*$', l) for l in steps)
      and 'store room' in steps[0].lower() and 'page reader' in steps[1].lower() and 'state prep' in steps[2].lower() and 'build' in steps[3].lower())
check('front door: each mark is "found" by default and set to MISSING when `if not exist` says the file is not there',
      all(f'set "S{n}=found"' in txt and f'if not exist "%B{n}%" set "S{n}=MISSING"' in txt for n in range(1, 5)))
labels = {l[1:].strip().lower() for l in lines if l.startswith(':') and not l.startswith('::')}
gotos = {m.lower() for m in re.findall(r'(?i)goto\s+:?(\w+)', txt)}
check('front door: every goto has its label', gotos <= labels and {'menu', 'go', 'missing', 'end', 'step1', 'step2', 'step3', 'step4'} <= labels)
calls = [l[5:].strip() for l in lines if l.lower().startswith('call ')]
check('front door: it calls exactly one thing, the picked button, by a quoted variable, only after `if not exist` was checked',
      calls == ['"%TARGET%"'] and txt.index('if not exist "%TARGET%" goto :missing') < txt.index('call "%TARGET%"'))
check('front door: a missing button is said plainly, with its path, and nothing is started',
      'is MISSING. This file was not found:' in txt and 'Nothing was started.' in txt and '%TARGET%' in txt.split(':missing')[1])
# 27 Nov 2026 (manager's review): a typed answer (set /p) was not taken on the owner's PC that morning; the button asks with
# one key press (choice), the pattern LAYER-RECORDS.bat uses and that works there. Q leaves; the highest errorlevel is tested first.
check('front door: nothing starts by itself: it waits for one key press (choice, as LAYER-RECORDS.bat asks), and Q leaves',
      'choice /c 1234Q /n /m ' in txt and 'set /p' not in low and txt.index('choice /c 1234Q') < txt.index('call "%TARGET%"')
      and [l for l in lines if l.lower().startswith('if errorlevel')] ==
      ['if errorlevel 5 goto :end', 'if errorlevel 4 goto :step4', 'if errorlevel 3 goto :step3', 'if errorlevel 2 goto :step2', 'if errorlevel 1 goto :step1'])
check('front door: it downloads nothing itself (no web words, no pip, no powershell, no curl) and does not echo what was typed',
      not any(w in low for w in ('http', 'curl', 'powershell', 'pip ', 'bitsadmin', 'wget', 'invoke-web', 'urlmon')) and not re.search(r'echo[^\r\n]*%PICK%', txt, re.I))
check('front door: it says which choice goes to the internet (3 in the store room and the page reader) and that 1 only shows the status',
      'pick 1 first: it only shows the status' in low and 'only when you pick their download choice (3)' in low)
check('front door: the housekeeping lines are there (echo off, setlocal, cd to its own folder, pause at the end)',
      lines[0] == '@echo off' and 'setlocal' in lines and 'cd /d "%~dp0"' in lines and lines[-2] == 'pause')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
