#!/bin/bash
# R-LR2 (ruled 'full', KPC owner, 2026-11-17): ONE full-detail save of an area whose layer looks like it is going away, before it dies.
# usage: kpc_layer_full_save.sh us <ST> | world <CC|CA>      (run from the repo root by kpc-geo-cache.yml / kpc-world-cache.yml)
# It is the old cache bot's own read, not a new fetcher: the same key script, host rules, pacing and robots checks, run in
# GEO_CACHE_MODE=refresh at full detail (GEO_DETAIL / GEO_THIN from the workflow) into its own folder (GEO_CACHE, default
# cache/full). The ~110 m release copy is downloaded first: the layers on saved-copy-only hosts come from it, and save-check
# compares against it, so a full copy holding fewer records (in total or for any layer) is refused. The result goes up as the
# SEPARATE asset full-<area>.json.gz, uploaded once and never replaced (no --clobber); the ~110 m copy is never touched.
# Never fails the job: every stop is a ::warning / ::error line (kept green, listed by the hidden-failures step).
set -u
JOB="${1:-}"; U="${2:-}"
H="${RUNNER_TEMP:-/tmp}/kpc-hidden.txt"; HE="${RUNNER_TEMP:-/tmp}/kpc-hidden-errors.txt"
say() { echo "::$1 title=Full-detail save $U::$2"; echo "Full-detail save $U - $2" >> "$H"; [ "$1" = error ] && echo "Full-detail save $U - $2" >> "$HE"; return 0; }
case "$JOB" in
  us)    [[ "$U" =~ ^[A-Z]{2}$ ]] || { say error "not a state code: '$U'"; exit 0; }; STEM="US-$U" ;;
  world) if [ "$U" = CA ]; then STEM=CA-ALL; elif [[ "$U" =~ ^[A-Z]{2}$ ]]; then STEM="W-$U"; else say error "not a country code: '$U'"; exit 0; fi ;;
  *)     say error "usage: kpc_layer_full_save.sh us|world <code>"; exit 0 ;;
esac
FULL="full-$STEM.json.gz"; D="${GEO_CACHE:-cache/full}"; A=.against-full
export GEO_CACHE="$D" GEO_CACHE_MODE=refresh
mkdir -p "$D" "$A"
gh release view boundary-cache -R "$GITHUB_REPOSITORY" --json assets -q '.assets[].name' > "$A/ASSETS.txt" \
  || { say warning "the release asset list could not be read: no full-detail save this run"; exit 0; }
if grep -qx "$FULL" "$A/ASSETS.txt"; then echo "::notice title=Full-detail save $U::$FULL is already on the release (one save only): nothing to do"; exit 0; fi
grep -qx "$STEM.json.gz" "$A/ASSETS.txt" || { say warning "$STEM.json.gz is not on the release, so there is nothing to compare a full copy against: not saved"; exit 0; }
gh release download boundary-cache -R "$GITHUB_REPOSITORY" -p "$STEM.json.gz" -D "$A" --clobber \
  || { say warning "the release copy $STEM.json.gz could not be downloaded: not saved"; exit 0; }
cp "$A/$STEM.json.gz" "$D/"
touch "$A/T0"; sleep 1
if [ "$JOB" = us ]; then
  pip install --quiet --break-system-packages pyshp pyproj >/dev/null 2>&1 || true
  STATES="$U" python3 .github/scripts/kpc_us_key.py || say warning "kpc_us_key.py stopped with an error (exit $?)"
elif [ "$U" = CA ]; then
  python3 .github/scripts/kpc_ca_key.py || say warning "kpc_ca_key.py stopped with an error (exit $?)"
else
  pip install --quiet --break-system-packages pykakasi pyshp >/dev/null 2>&1 || true
  COUNTRIES="$U" python3 .github/scripts/kpc_world_key.py || say warning "kpc_world_key.py stopped with an error (exit $?)"
fi
F="$D/$STEM.json.gz"
[ "$F" -nt "$A/T0" ] || { say warning "the full-detail read saved nothing new (a source failed or was not read): not saved"; exit 0; }
python3 .github/scripts/kpc_master_cli.py save-check --against "$A" --assets "$A/ASSETS.txt" "$F" \
  || { say error "save-check refused the full-detail copy (named above): not uploaded"; exit 0; }
cp "$F" "$D/$FULL"
gh release upload boundary-cache "$D/$FULL" -R "$GITHUB_REPOSITORY" \
  || { say warning "the upload of $FULL failed (or it is already there): nothing replaced"; exit 0; }
echo "::notice title=Full-detail save $U::uploaded $FULL ($(du -h "$D/$FULL" | cut -f1)); the ~110 m copy $STEM.json.gz is left as it is"
