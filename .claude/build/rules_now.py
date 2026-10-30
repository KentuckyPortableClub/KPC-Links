#!/usr/bin/env python3
"""Copy the rules in force WORD FOR WORD from .claude/notes/mapping.md into .claude/RULES-NOW.md (HQ, Oct 30 2026).
Finds blocks by their headings, not line numbers. Run from the repo root after any new ruling in mapping.md."""
import pathlib, sys
M = pathlib.Path('.claude/notes/mapping.md').read_text(encoding='utf-8').split('\n')
def find(prefix, start=0):
    for i in range(start, len(M)):
        if M[i].startswith(prefix): return i
    sys.exit('not found: ' + prefix)
BLOCKS = [("- **POTA'S OWN RULES = THE TIEBREAKER", "- Oct 27 (chat 8, research desk): 2-FER GRAY AREAS", "POTA'S OWN RULES + 2-FER RULES (FINAL) + WHOLE WORLD"),
          ("## RULE SHEET G: ONE BOUNDARY PIPELINE", None, "RULE SHEET G (US) + POTA PLAIN ANSWERS + R-G8 + METHOD (R-G9..11, P-1..5) + CANADA + HUNTER TIERS + AUTO-1..4 + everything after")]
out = ["# RULES IN FORCE (copied WORD FOR WORD from .claude/notes/mapping.md by .claude/build/rules_now.py; HQ Oct 30, Brandon 8:42 AM 'yes to all')",
       "Read THIS file for the rules, not all of mapping.md (390 KB of history). Nothing here is changed: if this file and mapping.md ever differ, mapping.md wins. New rulings go in mapping.md first (as always), then run `python3 .claude/build/rules_now.py`.",
       "Other rule sheets (A closures, B near-miss, C type words, D closures bot, E camp, F waiting room, MAP DATA) stay in mapping.md: `grep -n '^## RULE SHEET' .claude/notes/mapping.md` and read only the one you need.", ""]
for a, b, t in BLOCKS:
    i = find(a); j = find(b, i) if b else len(M)
    out += [f"## {t}", ""] + M[i:j] + [""]
pathlib.Path('.claude/RULES-NOW.md').write_text('\n'.join(out), encoding='utf-8')
print('RULES-NOW.md', sum(len(x) + 1 for x in out), 'bytes')
