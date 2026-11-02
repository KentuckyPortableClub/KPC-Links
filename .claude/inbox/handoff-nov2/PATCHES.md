# KPC general review patches (Nov 2, 2026). LOCAL ONLY, NOT APPLIED, NOTHING PUSHED

Made against the fresh read-only copies in /workspace/fresh_nov2 (KPC-Data e0c674ac, 8:45 AM CST; KPC-Links 8e291ec2,
8:40 AM CST). Each patch applies with `git apply` (-p1) at the root of its repo; `git apply --check` passed for all of them.
`orig/` holds the exact files they were made against. Tests: `python3 -m pytest -q tests` (66 pass, 1 skipped: the
2-fer guide PDF build needs the Carlito/Caladea fonts, which this box does not have).

| Patch | Repo | What it fixes | Needs Brandon's OK? |
|---|---|---|---|
| G1-KPC-Data-watchdog-restart-inputs.patch / G1-KPC-Links-… (same file in both repos) | both | A watchdog restart uses the dispatch defaults, so it did NOT do what the scheduled run does: the waiting room restarted in `replay` (no release, no key doctor), closures restarted as a Kentucky-only TEST, discovery always OH, Sunday helpers ran `match` instead of linkfix/sitecheck, world key pinned JP, approvals would force an extra email, discord-watch would list to admin. Now each restart sends the schedule's inputs (per cron for helpers). Posting bots whose dispatch is a practice run (youtube comments, social, club posts, what's new, park alerts, fb comments, discord relay, research helpers) are listed as skipped, not restarted. | No (bug fix) |
| G2-KPC-Links-honest-user-agent.patch | KPC-Links | kpc_ky_maps.py and kpc_linkcheck.py sent a Chrome/Safari browser User-Agent (Oct 31 ruling: always the honest KPC UA). | No (rule fix) |
| G3-KPC-Data-docs-bot-scrub-keys.patch + tools/scrub_docs_keys.py | KPC-Data | The documents bot saved a council roadworks map link with an embedded Google API key (data/docs/W-GB.json, 2 places). save() now replaces keys/tokens with REMOVED; the tool cleans the existing file (dry run by default). | No (rule fix) |
| G4-KPC-Data-key-doctor-every-release-run.patch | KPC-Data | The key doctor ran only at 5:13 AM; now on every scheduled waiting-room run (still report-only) and it also copies the v0.5.1 resources report. | No (report only) |
| G5-KPC-Data-waiting-tidy-docstring.patch | KPC-Data | The docstring said WAITING_TIDY / WAITING_KEEP_GENS default 0; the code defaults are 1 / 2. | No |
| G6-KPC-Links-NEEDS-OK-no-key-fallback.patch (tools/make_g6_key_fallback.py) | KPC-Links | 120 pages: KPC.dataUrl no longer falls back to KPC-Links for data/us-key, ca-key, world-key (it showed HELD keys, incl. 51 world-key countries only in KPC-Links). Those countries would vanish from the site until released. | YES |
| G7-KPC-Links-save-by-overwrite-everywhere.patch (tools/make_g7_saves.py) | KPC-Links | The ~30 workflows still on `git pull --rebase --autostash \|\| true` (a lost save looked green) now use the shared save-by-overwrite helper (`kpc_save_overwrite.sh`): this run's files are copied on top of the newest main; word lists and inbox lines are merged; a lost save prints `::error` and goes red only if `KPC_SAVE_RED=yes` (the default for converted bots is `no` = a loud notice). `KPC_SAVE_MODE=rebase` puts back the old way. | No (bug fix); the red setting is a DECISION |
| G8-KPC-Data-loud-hidden-failures.patch / G8-KPC-Links-… (tools/make_g8_loud.py + make_g8_review.py) | both | Every `\|\| true` is either loud or says why it is fine; every `continue-on-error` step has an id and a last "Report hidden failures" step lists the ones that failed; save loops say when every try failed; pipelines report the script's own exit status. See reports/G8-*.md. Board notices, not red. | No |
| G9-KPC-Data-spread-schedules.patch / G9-KPC-Links-… (tools/make_g9_crons.py) | both | Start times spread: shared start minutes per week KPC-Data 67 → 8, KPC-Links 389 → 0. Only the minute moves, by 7 at most; crons that other lines compare against are never moved. Each moved line says what it was. See reports/G9-schedule-collisions.md. | No |
| G10-KPC-Links-NEEDS-OK-publish-2fers-hours-off-by-default.patch | KPC-Links | New hand-started workflow `kpc-fers-publish.yml` + `kpc_fers_publish.py`: the 2-fer map layer (reviewed list only), the 2-fer guide PDF, the GPX and the park hours on pages. Four switches (`KPC_FERS_LAYER`, `KPC_FERS_PDF`, `KPC_FERS_GPX`, `KPC_HOURS_PUBLISH`) = off / preview / on, all **off** by default. Preview only uploads files to look at. | YES (each switch) |
| G11-KPC-Data-restart-as-the-missed-schedule.patch / G11-KPC-Links-… (tools/make_g11_restart.py) | both | A watchdog restart now runs as the missed scheduled run: 21 workflows get an optional `as_schedule` input; their schedule tests read it, and the watchdog sends it. | No (bug fix) |

Apply order (each repo, at its root): KPC-Data G1, G3, G4, G5, G8, G9, G11 (G6: KPC-Links only, after Brandon's OK).
KPC-Links G1, G2, G7, G8, G9, G10, G11, then G6 if approved. G7, G9, G10 and G1-G6 also apply on their own; G8 needs G7 in
KPC-Links (and G1-G5 under it), G11 needs everything before it. `tools/rebuild_stack.sh` rebuilds G8-G11 from the local stack.

Engine: /workspace/kpc_engine_v0.5.1.zip adds the report-only `resources` task (config/resources.json), 164 tests pass.
