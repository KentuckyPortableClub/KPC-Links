# Preflight: run this before opening a PR

One command, offline, read-only (it changes no file):

    DATA=../kpc-data python3 .github/scripts/kpc_preflight.py          # everything
    python3 .github/scripts/kpc_preflight.py --quick                   # skips the full test suite

Each check prints one line. Exit code 1 means at least one FAIL.

| Line | Meaning |
|---|---|
| `suite vs baseline` | the full test suite has no new failure, no stale baseline entry (a listed test that now passes must be removed from `tests/known-fail-main.txt`). Skipped tests are listed, not counted as passed |
| `rules hashes` | each rules hash against `origin/main`. A moved hash needs the NEWEST line of `docs/key-rules-change.txt` to say `old -> new` and `APPROVED, decided_by KPC owner`, plus a scope entry whose `from` is the old hash. The old -> new pairs are printed: paste them in the PR body. `no rules hash moved` is the normal case |
| `workflows` | each changed workflow is YAML, has no `success()` / `failure()` / `always()` in a step `env`, and uses only declared `inputs.*` |
| `actionlint` | runs `actionlint` when installed; SKIP prints the install hint |
| `master check` | `kpc_master_cli.py check` is clear |
| `big / raw files` | nothing over 1 MB, no zip, no raw layer added |
| `hosts / WDPA` | no forbidden host in added code, no WDPA / Protected Planet outline URL |
| `names / callsigns / ticket ids` | WARN only: a person's name, callsign or ticket id in added text (false hits are possible; look, then ignore or fix) |
| `no new schedule` | no `cron:` or `schedule:` added to a workflow |

SKIP means the check could not run here (no `origin/main` in a shallow clone, no PyYAML, no actionlint). It is not a pass: say so in the PR.

## PR body checklist (what Quality looks for)

- Suite result against main: counts, and the preflight `suite` line.
- Rules hashes: the `old -> new` pairs, or the words "no hash moved".
- actionlint result (or "not installed, SKIP").
- One batched draft PR, on a `prep/*` branch.

## Writing tests that do not rot

1. No hash literals. Compare `kpc_key_freeze.rules_hash(kind)` with `kpc_preflight.newest_hash(kind)` (the newest hash in `docs/key-rules-change.txt`).
2. No pins on bot-written data (key files, layer lists, record ids, script version tags). Build a tiny fixture in a temp dir and test the logic on it. If a pin cannot be avoided, match a pattern (`v=\d{8}\w`), not the value.
3. A test that needs history or an optional module (a commit missing in a shallow clone, `origin/main`, PyYAML) prints `SKIP: <why>` as its LAST line and exits 0. The suite then lists it as skipped.
