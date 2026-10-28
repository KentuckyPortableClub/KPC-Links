# CHAT 1 INBOX (website, Sonnet)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- HQ: Map Coverage tab: when chat 8's per-park file lands (KPC-Data data/review/scoreboard-parks.json), switch the drill-down to individual parks; Send-it stays on Map Rep. CHECKED Oct 28 5:04 AM: not landed yet (data/review/ in KPC-Data only has scoreboard.json). Leaving open.

- HQ (Oct 28 5:00 AM): Map Coverage tab will get MORE COLUMNS (chat 10's nightly scoreboard bot: outline source, size check, official map, rules, hours/fees, access, campground info, closures, who runs it, 2-fer checked; '% complete' per state). When its JSON lands, add the columns (a column picker on phones), keep it members-only; 'Send it' per missing item -> Map Rep as now.

## NEEDS BRANDON

## DONE
- Oct 28 5:04 AM: privacy page line for the 🌐 translate button — added under a new "Translate button" heading in kpc-privacy.html, Brandon's wording word for word. Tested 390px, 0 errors.
- Oct 28 5:04 AM: Pages deploy workflow built (.github/workflows/pages-deploy.yml): Jekyll build (same _config.yml excludes) -> upload-pages-artifact -> deploy-pages, paths-ignore '.claude/**'.
- Oct 28 5:09 AM: Brandon switched Settings -> Pages -> Source -> "GitHub Actions". Ran pages-deploy.yml by hand (workflow_dispatch, run 40669294821): build + deploy both succeeded for real this time (deploy had failed, as expected, on the earlier continue-on-error test run before the switch). Confirmed live via the Deployments API: latest deployment state=success, sha matched HEAD, environment_url=the live site (direct curl/WebFetch to the live site is blocked from this sandbox, so I used GitHub's own deployment record instead). Confirmed a notes-only push does NOT rebuild: chat 10's inbox commit (touched only .claude/inbox/chat-10.md) landed with no new workflow run at all. Removed continue-on-error from the deploy job — it's load-bearing now. Updated CLAUDE.md's pushing section to point at `gh run list --workflow=pages-deploy.yml` instead of the retired `-w 372361621`.

## REPORT TO HQ (newest first)
- Oct 28 5:09 AM (chat 1): Pages Actions switch confirmed working end to end — manual run deployed for real, live site updated (via Deployments API, not a direct fetch — this sandbox can't reach the live github.io site), notes-only push confirmed skipped. continue-on-error removed. CLAUDE.md pushing section updated to the new workflow. Nothing needs Brandon right now. One push.
- Oct 28 5:04 AM (chat 1): Did the privacy line and built the Pages deploy workflow (see DONE). Left the workflow's deploy step on continue-on-error until Brandon flips Settings -> Pages -> Source to "GitHub Actions" — needs his click, put it under NEEDS BRANDON. Map Coverage per-park switch is still waiting on chat 8's scoreboard-parks.json, left it OPEN. One push, no new items added to anyone else's inbox.
