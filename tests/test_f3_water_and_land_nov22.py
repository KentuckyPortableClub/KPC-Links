#!/usr/bin/env python3
"""F3 (22 Nov 2026, owner-approved form). Invented names only. Offline.

A name join is dropped only when:
  (1) the RECORD's last type word is a water body or beach (lake/pond/ponds/reservoir/beach)
      and the PARK does not already carry that water kind (lake/pond/reservoir are one kind), or
  (2) one name is a park (state park / SP / SRA / recreation area) and the other is a wildlife
      area (WMA / wildlife area / game land / refuge / NWR) or a state forest.
Reserve, preserve, CA/conservation area, complex, memorial and area are not different kinds.

Fail without the fix: 'Silver Creek SP' vs 'Silver Creek WMA' would still join, because kinds()
does not see the 'SP' abbreviation.

Run: python3 -B tests/test_f3_water_and_land_nov22.py
"""
import os, pathlib, sys, types
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
os.chdir(ROOT)

STOP = '\nidx = {}\n'
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
if STOP not in src:
    raise SystemExit('kpc_us_key.py: stop marker not found')
us = types.ModuleType('kpc_us_key_f3')
us.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_us_key.py')
exec(compile(src.split(STOP)[0], 'kpc_us_key.py', 'exec'), us.__dict__)

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


def joined(park, rec):
    a = {'OBJECTID': 1, 'Unit_Nm': rec, 'Loc_Nm': '', '_k': us.kinds(rec)}
    return bool(us.join_how(park, us.kinds(park), a, True))


# --- drops ---
check(not joined('Silver Creek State Park', 'Silver Creek Lake'),
      'F3 a state park and a lake of the same words stay apart')
check(not joined('Cedar Hollow State Park', 'Cedar Hollow Pond'),
      'F3 a state park and a pond of the same words stay apart')
check(not joined('Silver Creek State Park', 'Silver Creek Beach'),
      'F3 a state park and a beach of the same words stay apart')
check(not joined('Silver Creek Wildlife Management Area', 'Silver Creek Lake'),
      'F3 a wildlife area and a lake of the same words stay apart')
check(not joined('Silver Creek State Park', 'Silver Creek State Forest'),
      'F3 a state park and a state forest of the same words stay apart')
check(not joined('Silver Creek State Forest', 'Silver Creek State Park'),
      'F3 a state forest and a state park of the same words stay apart')
check(not joined('Silver Creek State Park', 'Silver Creek WMA'),
      'F3 a state park and a WMA of the same words stay apart')
check(not joined('Silver Creek State Park', 'Silver Creek NWR'),
      'F3 a state park and a refuge of the same words stay apart')
check(not joined('Silver Creek Recreation Area', 'Silver Creek Game Land'),
      'F3 a recreation area and a game land of the same words stay apart')

# Fail without: kinds() misses the SP / SRA abbreviations, so only F3 stops this join.
check(us.kinds('Silver Creek SP') == set() and us.kinds('Silver Creek SRA') == set(),
      'F3 fail-without: kinds() does not see the SP or SRA abbreviation')
check(not joined('Silver Creek SP', 'Silver Creek WMA'),
      'F3 an SP abbreviation and a WMA of the same words stay apart (kinds() would have joined them)')
check(not joined('Silver Creek SRA', 'Silver Creek WMA'),
      'F3 an SRA and a WMA of the same words stay apart (kinds() would have joined them)')
check(not joined('Silver Creek SP', 'Silver Creek State Forest'),
      'F3 an SP abbreviation and a state forest of the same words stay apart')
check("if f3_apart(a, b): return False" in src,
      'F3 fail-without: name_ok refuses a pair that f3_apart flags')

# --- keeps ---
check(joined('Cedar Lake State Park', 'Cedar Lake'),
      'F3 a park that already carries lake still matches the lake record')
check(joined('Oak Ridge State Marine Reserve', 'Oak Ridge State Marine Park'),
      'F3 a marine reserve and a marine park of the same words still match')
check(joined('Maple Ridge State CA', 'Maple Ridge Lake CA'),
      'F3 a record ending in CA (not a water word) still matches, even with lake in the name')
check(joined('Pine Ridge SRA', 'Pine Ridge Lake Complex'),
      'F3 a record ending in Complex (not a water word) still matches the SRA')
check(joined('Maple Ridge State CA', 'Maple Ridge Reserve'),
      'F3 a conservation area and a reserve of the same words still match')
check(joined('Silver Creek WMA', 'Silver Creek Wildlife Area'),
      'F3 a WMA and a wildlife area of the same words still match')

print(f'{len(FAILS)} failed' if FAILS else 'ALL PASS')
sys.exit(1 if FAILS else 0)
