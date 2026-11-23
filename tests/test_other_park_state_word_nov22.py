#!/usr/bin/env python3
"""22 Nov 2026 (owner 3:47 PM): the "another park's name" check (kpc_match_checks check 4) leaves the word "state" out on BOTH
sides. A record named "<X> Natural Area" is ANOTHER park's record when the state holds "<X> State Natural Area" and this park is
"<X> Battlefield Park" (the Arkansas case). Invented names. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


names = {MC.full(n) for n in ('Invented Bluff State Natural Area', 'Invented Bluff Battlefield Park', 'Other Hollow State Park')}
check('a record named for another park, with "State" left out of the record, is that other park\'s',
      MC.other_park_name('Invented Bluff Natural Area', 'Invented Bluff Battlefield Park', names) is True)
check('the park whose own name it is (with or without "State") still keeps it',
      MC.other_park_name('Invented Bluff Natural Area', 'Invented Bluff State Natural Area', names) is False)
check('an exact other park\'s name is still caught', MC.other_park_name('Other Hollow State Park', 'Invented Bluff Battlefield Park', names) is True)
check('a record name no park carries is not another park\'s', MC.other_park_name('Invented Creek Natural Area', 'Invented Bluff Battlefield Park', names) is False)
names.add(MC.full('Invented Creek State Natural Area'))
check('a name added to the same set later is seen too', MC.other_park_name('Invented Creek Natural Area', 'Invented Bluff Battlefield Park', names) is True)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
