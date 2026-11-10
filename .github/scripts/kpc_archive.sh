#!/usr/bin/env bash
# KPC-Archive store (Nov 9 2026 evening; Brandon t909u + 4:52/4:59 PM CST). Outlines are big and change monthly, so they are
# compressed RELEASE ASSETS on KPC-Archive (outside git, so the archive's 500 MB git cap is never touched); git on KPC-Archive keeps
# only a small index per release (index/<tag>.json: name, bytes, sha256, date, run; for the 2-fer saved-live files also park, record
# ids, outline fingerprint, date). A refresh REPLACES the asset (--clobber), so no history of geometry builds up (Brandon t923u).
# Outline geometry is never committed to git.
#   kpc_archive.sh get <tag> <dest> <name-glob>...   download those assets of KPC-Archive release <tag> into <dest>
#   kpc_archive.sh put <tag> <message> <file>...     upload the files to release <tag> (made if missing) + update index/<tag>.json
# Exit 0 = done; 2 = not available (no KPC_ARCHIVE_TOKEN, no such release/asset, archive not reachable): the caller falls back to
# its old release copy with a warning, never a failure; 1 = the index push failed after 5 tries (the assets ARE uploaded).
# The token (repo secret KPC_ARCHIVE_TOKEN) needs Contents: Read and write on KPC-Archive only (releases + the index commit).
set -u
REPO="${KPC_ARCHIVE_REPO:-KentuckyPortableClub/KPC-Archive}"
cmd="${1:-}"; tag="${2:-}"; shift 2 2>/dev/null || { echo "usage: kpc_archive.sh get|put <tag> ..."; exit 2; }
if [ -z "${KPC_ARCHIVE_TOKEN:-}" ]; then
  echo "::warning title=KPC-Archive::secret KPC_ARCHIVE_TOKEN is not set in this repo; using the old release copy instead ($cmd $tag)"; exit 2
fi
export GH_TOKEN="$KPC_ARCHIVE_TOKEN"
case "$cmd" in
  get)
    dest="$1"; shift; mkdir -p "$dest"; args=()
    for g in "$@"; do args+=(-p "$g"); done
    if gh release download "$tag" -R "$REPO" "${args[@]}" -D "$dest" --clobber 2>/dev/null; then echo "KPC-Archive: got $* from release $tag"; exit 0; fi
    echo "::notice title=KPC-Archive::release $tag has no $* yet; using the old release copy"; exit 2 ;;
  put)
    msg="$1"; shift; files=()
    for f in "$@"; do [ -f "$f" ] && files+=("$f"); done
    [ "${#files[@]}" -gt 0 ] || { echo "KPC-Archive: nothing to save"; exit 0; }
    gh release view "$tag" -R "$REPO" >/dev/null 2>&1 || gh release create "$tag" -R "$REPO" --prerelease --title "$tag" --notes "Saved copies (index: index/$tag.json in git). Brandon Nov 9 2026." >/dev/null 2>&1
    if ! gh release upload "$tag" "${files[@]}" -R "$REPO" --clobber; then
      echo "::warning title=KPC-Archive::could not upload to release $tag on $REPO (check KPC_ARCHIVE_TOKEN: Contents read and write); using the old release copy"; exit 2
    fi
    W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
    if ! git -c credential.helper= clone -q --depth 1 --filter=blob:none --no-checkout "${KPC_ARCHIVE_URL:-https://x-access-token:${KPC_ARCHIVE_TOKEN}@github.com/${REPO}.git}" "$W/a" 2>/dev/null \
       || ! git -C "$W/a" sparse-checkout set --no-cone /index/ 2>/dev/null || ! git -C "$W/a" checkout -q 2>/dev/null; then
      echo "::warning title=KPC-Archive::assets uploaded to $tag, but the index could not be read (git)"; exit 1
    fi
    for i in 1 2 3 4 5; do
      python3 - "$W/a/index/$tag.json" "${GITHUB_RUN_ID:-local}" "${files[@]}" <<'PY'
import hashlib, json, os, pathlib, sys, time
p = pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True)
try: d = json.loads(p.read_text())
except Exception: d = {}
d.setdefault('about', 'Index of the saved copies on this release (the files are release assets, outside git). One row per file.')
fs = d.setdefault('files', {})
for f in sys.argv[3:]:
    b = open(f, 'rb').read()
    fs[os.path.basename(f)] = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'saved': time.strftime('%Y-%m-%d'), 'run': sys.argv[2]}
    if os.path.basename(f).startswith('saved-live-'):   # Brandon t923u: the small per-park index (park, record ids, fingerprint, date)
        import gzip
        try: P = json.loads(gzip.decompress(b)).get('parks') or {}
        except Exception: P = {}  # noqa: BLE001
        pk = d.setdefault('parks', {})
        for ref, v in P.items():
            pk[ref] = {'ids': v.get('ids'), 'fp': hashlib.sha1(json.dumps(v.get('g'), separators=(',', ':')).encode()).hexdigest()[:16], 'date': v.get('rd'), 'file': os.path.basename(f)}
d['total_bytes'] = sum(v['bytes'] for v in fs.values())
p.write_text(json.dumps(d, indent=1, sort_keys=True) + '\n')
PY
      git -C "$W/a" add -A index
      git -C "$W/a" diff --cached --quiet && { echo "KPC-Archive: $tag index unchanged"; exit 0; }
      git -C "$W/a" -c user.name='kpc-bot' -c user.email='kpc-bot@users.noreply.github.com' commit -qm "$msg"
      git -C "$W/a" push -q origin HEAD:main 2>/dev/null && { echo "KPC-Archive: saved ${#files[@]} file(s) to release $tag + index"; exit 0; }
      sleep $((i * 5)); git -C "$W/a" reset -q --hard HEAD~1; git -C "$W/a" pull -q --rebase origin main 2>/dev/null || true
    done
    echo "::error title=KPC-Archive::assets uploaded to $tag, but the index push failed 5 times"; exit 1 ;;
  *) echo "usage: kpc_archive.sh get|put <tag> ..."; exit 2 ;;
esac
