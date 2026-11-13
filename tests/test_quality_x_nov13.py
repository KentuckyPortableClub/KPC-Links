#!/usr/bin/env python3
"""Quality X2-X5 (Nov 13): workflow order, release build() gates, SPREP/licence share_block,
and the key-check must-save path (no hidden || true, build id is material, postcheck does not skip)."""
import pathlib, re, sys, tempfile, json, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_release as R  # noqa: E402
import kpc_stamp_only as SO  # noqa: E402

ok = True
def check(msg, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + msg + (f' {extra}' if extra and not cond else ''))
    ok = ok and bool(cond)

# X2: outlines from the key after the far-join check
import yaml
wf = yaml.safe_load((ROOT / '.github/workflows/kpc-us-key.yml').read_text())
names = [s.get('name', '') for s in wf['jobs']['join']['steps']]
def at(word):
    return next(i for i, n in enumerate(names) if n.startswith(word))
check('X2: Join check (far-join hold) runs before Outlines from the key',
      at('Join check') < at('Outlines from the key') < at('Master check of the joined'))

# X3: build() itself refuses a blocked build id and uses the outlines-agree helper
src = (ROOT / '.github/scripts/kpc_release.py').read_text()
check('X3: build() calls build_source_refuse_why (blocked build + outlines agree)',
      'why = build_source_refuse_why(repo, area, sha, units)' in src
      and 'if why: raise ReleaseError(why)' in src
      and 'US-42797939226' in src
      and 'outline_refuse_why' in src)
check('X3: US-42797939226 stays on the refuse list', 'US-42797939226' in R.BLOCKED_BUILDS)

# X4
check('X4: WDPA_RE matches SPREP', bool(M.WDPA_RE.search('SPREP protected areas')) and bool(M.is_wdpa('a SPREP layer')))
why = M.share_block({'area': 'W-AS', 'layer': 'x', 'label': 'ok parks'})
check('X4/M6: share_block refuses a missing licence', 'licence' in (why or '').lower())
why_s = M.share_block({'area': 'W-AS', 'layer': 'x', 'label': 'SPREP islands', 'license': 'CC BY 4.0'})
check('X4: share_block refuses SPREP even with a licence', bool(why_s) and 'WDPA' in why_s or 'SPREP' in (why_s or '').upper() or bool(why_s))

# X5 stamp filter + postcheck save
sh = (ROOT / '.github/scripts/kpc_save_overwrite.sh').read_text()
check('X5: kpc_save_overwrite.sh stamp filter has no unmarked || true',
      "python3 - <<'KPC_STAMP_PY' || true" not in sh
      and "python3 - <<'KPC_STAMP_PY'" in sh
      and 'stamp filter failed' in sh)
check('X5: stamp filter does not ignore the build id',
      "IDS = set()" in sh and "IDS = {'build'}" not in sh
      and "IDS = set()" in (ROOT / '.github/scripts/kpc_stamp_only.py').read_text())
pc = (ROOT / '.github/scripts/kpc_key_postcheck.py').read_text()
check('X5: kpc_key_postcheck.py no longer returns early on an already-checked build',
      'nothing written' not in pc and 'writing the report again so the must-save can land' in pc)
yml = (ROOT / '.github/workflows/kpc-key-postcheck.yml').read_text()
save = yml[yml.find('- name: Save the report'):]
# only this step: no continue-on-error, no KPC_SAVE_RED=no
# stop at next step or eof
nxt = save.find('\n      - name:', 10)
body = save if nxt < 0 else save[:nxt]
check('X5: key-check Save step has no continue-on-error and no KPC_SAVE_RED=no',
      'continue-on-error' not in body and 'KPC_SAVE_RED=no' not in body
      and 'kpc_save_overwrite.sh' in body
      and 'Never red' not in yml)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
