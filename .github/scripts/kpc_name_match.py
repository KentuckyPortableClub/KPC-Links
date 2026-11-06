#!/usr/bin/env python3
"""Same-place name matcher, ported from the KY GIS Workbench (BDW-Coils tools/ky-maprep-gis.html, FIND NEW: NAME_STOP / normName()
/ nameMatch(); Nov 6 2026 follow-up key / 2-fer patch, Brandon [pt449u]). REPORT HELPER ONLY: no key builder imports it, so it
never decides a join (it is in kpc_key_freeze.NOT_RULES).

normName: lower case, '&' -> ' and ', anything not a-z0-9 -> space, the workbench's stop words (kind words: state, park, wildlife,
          management, area, wma, forest, refuge ...) removed, spaces squeezed. One change for a worldwide program: accents are folded
          first (Triglavski, Mürz, Île), so a non-English name is not cut into pieces by the a-z0-9 rule.
same_place(a, b): the workbench rule. Exact match after the stop words, or the SHORTER name (at least two words) is a whole-word
          prefix or suffix of the longer ('Dale Hollow Lake WMA' ~ 'Dale Hollow State Park'). The workbench found a looser substring
          rule hid real parks (Jefferson Memorial Forest, Cumberland Forest WMA, Island Park), so this stays strict.
"""
import re, sys, unicodedata

NAME_STOP = re.compile(r'\b(the|of|and|at|state|national|natural|nature|historic(al)?|site|park|parks|wildlife|management|area|areas|wma|'
                       r'preserve|forest|recreation(al)?|refuge|sanctuary|center|fee|tract|unit|ky|resort|fishing|public|hunting|commission|'
                       r'corps|engineers|us|u s)\b')


def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c)).replace('ł', 'l').replace('ø', 'o').replace('ß', 'ss')


def norm_name(n):
    s = fold(n).lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = NAME_STOP.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def same_place(a, b):
    """True when two names say they are the same place (the workbench's nameMatch rule, for one pair)."""
    na, nb = norm_name(a), norm_name(b)
    if len(na) < 4 or len(nb) < 4: return False
    if na == nb: return True
    wa, wb = na.split(' '), nb.split(' ')
    sh, lo = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    if len(sh) < 2: return False
    return lo[:len(sh)] == sh or lo[-len(sh):] == sh


def best_match(name, names):
    """The first of `names` that same_place() accepts, or None (the workbench's nameMatch over a list)."""
    return next((x for x in names if same_place(name, x)), None)


def selftest():
    assert norm_name('Dale Hollow Lake WMA') == 'dale hollow lake'
    assert same_place('Dale Hollow Lake WMA', 'Dale Hollow Lake State Resort Park')
    assert same_place('Taylorsville Lake WMA', 'Taylorsville Lake State Park')
    assert not same_place('Jefferson Memorial Forest', 'Jefferson County Memorial')   # the substring rule the workbench dropped
    assert not same_place('Island Park', 'Big Island')                              # one word after the stop words: never a prefix match
    assert same_place('Triglavski narodni park', 'TRIGLAVSKI NARODNI PARK')
    assert norm_name('Mürzer Oberland') == 'murzer oberland'
    assert same_place('Ballard WMA', 'Ballard Wildlife Management Area')
    assert not same_place('Ky', 'Ky')
    print('name-match self-test OK')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('--test', '--selftest'): selftest()
