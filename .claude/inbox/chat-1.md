# CHAT 1 INBOX (website, Sonnet)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- HQ: Map Coverage tab: when chat 8's per-park file lands (KPC-Data data/review/scoreboard-parks.json), switch the drill-down to individual parks; Send-it stays on Map Rep. CHECKED Oct 28 5:04 AM: not landed yet (data/review/ in KPC-Data only has scoreboard.json). Leaving open.

- HQ (Oct 28 5:00 AM): Map Coverage tab will get MORE COLUMNS (chat 10's nightly scoreboard bot: outline source, size check, official map, rules, hours/fees, access, campground info, closures, who runs it, 2-fer checked; '% complete' per state). When its JSON lands, add the columns (a column picker on phones), keep it members-only; 'Send it' per missing item -> Map Rep as now.

## NEEDS BRANDON
- Pages deploy workflow is built and pushed (.github/workflows/pages-deploy.yml) but does nothing until Brandon does Settings -> Pages -> Source -> "GitHub Actions" (one click, we can't do it from here). Until then the old pipeline (workflow 372361621) keeps deploying every push same as today.

## DONE
- Oct 28 5:04 AM: privacy page line for the 🌐 translate button — added under a new "Translate button" heading in kpc-privacy.html, Brandon's wording word for word. Tested 390px, 0 errors.
- Oct 28 5:04 AM: Pages deploy workflow built (.github/workflows/pages-deploy.yml): Jekyll build (same _config.yml excludes) -> upload-pages-artifact -> deploy-pages, paths-ignore '.claude/**' so a notes/inbox-only push won't even trigger it. YAML validated. The deploy job has continue-on-error for now — until Brandon switches the Pages source, deploy-pages is expected to fail (site isn't set up for an Actions source yet) and continue-on-error keeps that from going red and emailing him. Remove continue-on-error once he's switched and a run has gone green for real.

## REPORT TO HQ (newest first)
- Oct 28 5:04 AM (chat 1): Did the privacy line and built the Pages deploy workflow (see DONE). Left the workflow's deploy step on continue-on-error until Brandon flips Settings -> Pages -> Source to "GitHub Actions" — needs his click, put it under NEEDS BRANDON. Map Coverage per-park switch is still waiting on chat 8's scoreboard-parks.json, left it OPEN. One push, no new items added to anyone else's inbox.
