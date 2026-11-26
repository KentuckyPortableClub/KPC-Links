#!/usr/bin/env python3
"""26 Nov 2026 (owner 4:18 PM: 'your only job is to find and fix problems with keys ... accuracy ... more confirmed matches'),
Fable's review findings 3, 4 and the DEVIL'S note, plus the state forest outer line:
  A  a 'thin' shape must be LONG: a compact 30-acre square is measurable, so two different side-by-side parcels are told apart;
     a 25 m strip and anything under the saved copy's 90 m step stay can't-tell.
  B  a possessive is one word: DEVIL'S TRACK = Devils Track (US-12389).
  C  a Minnesota state forest's statutory line (sgmnb) never draws: MN DNR says it holds private land (rule 1b: the agency's own
     land only); the gate takes it off every park, whatever proved the park.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_same_land as SL  # noqa: E402
import kpc_match_checks as MC  # noqa: E402
import kpc_key_rules as KR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def rect(x, y, w, h): return [[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]


sq30 = rect(-92.8, 44.8, 0.0036, 0.0036)   # about 284 m x 400 m: 28 acres, under 40 (grade of #388: a true small parcel)
check(f'A: a compact {SL.acres_of(sq30):.0f}-acre parcel (under 40) is not thin; a 25 m strip is; a 4-acre square (under the 90 m step) is',
      SL.acres_of(sq30) < 40 and 0 < SL.mean_width_m(sq30) < SL.THIN_M and not SL.too_thin(sq30) and SL.too_thin(rect(-73.9, 41.1, 0.0003, 0.2)) and SL.too_thin(rect(-92.8, 44.8, 0.0015, 0.0015)))
a = {'Unit_Nm': 'Smith WMA', 'GIS_Acres': 28, '_g': {'rings': sq30}}
b = {'Unit_Nm': 'Smith WMA', 'GIS_Acres': 28, '_g': {'rings': rect(-92.7964, 44.8, 0.0036, 0.0036)}}   # the next parcel east
k, lv, why = SL.pick(a, {'b': b})
check(f'A: two different side-by-side 28-acre parcels of one name and size are NOT the same land ({k}, {lv}, {why})', k is None)
same = {'Unit_Nm': 'Smith WMA', 'GIS_Acres': 28, '_g': {'rings': rect(-92.80002, 44.80001, 0.0036, 0.0036)}}
k, lv, _ = SL.pick(a, {'s': same})
check(f'A: the same parcel read again still proves ({k}, {lv})', k == 's')

check("B: DEVIL'S TRACK FALLS is the exact name of Devils Track Falls (a second try); Knox's keeps 'knox s' for the single-letter rule",
      MC.exact_name('Devils Track Falls', "DEVIL'S TRACK FALLS") and MC.exact_name("Devil's Track Falls State Park", 'Devils Track Falls', 'State Park')
      and MC.full("Knox's Headquarters") == 'knox s headquarters' and not MC.exact_name('Devils Lake', "Devil's Track"))

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('C: the state forest statutory line is an outer line, and the gate removes it first, for every park',
      "'sgmnb': \"a state forest's statutory line" in src and src.index('if _sl_layer(rid) in OUTER_LINE:') < src.index("elif fresh_on and rec is not None and rec.get('_nostore'):"))

check('D: KPC_FRESH_ONLY skips the old-to-fresh proof loop; the outer line is also taken off after the match checks (gate or not)',
      "for _pgn, a in enumerate([] if _fresh_only else recs, 1):" in src and src.index('_mc = match_checks_pass(st, parks, recs, P, used)') < src.index("outer-line row(s) taken off"))
fr_ = src[src.index('def fresh_records('):src.index('def fresh_old_parks(')]
check('D: with KPC_FRESH_ONLY an old record of a complete layer is never offered to the matcher (no hints)',
      "if _fresh_only:" in fr_ and "return out + nostore, alias" in fr_)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
