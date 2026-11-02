# Decisions that need Brandon (Nov 2, 2026)

Nothing here is approved yet. Each line gives the recommended default. Until Brandon says otherwise, leave it at the safe
setting shown.

| # | Decision | Recommended | Safe setting until then | Who asks |
|---|---|---|---|---|
| 1 | G10 switch `KPC_FERS_LAYER` (the 2-fer map layer from the HQ reviewed list) | `preview` first, `on` after HQ reviews the preview | `off` | chat 8 |
| 2 | G10 switch `KPC_FERS_PDF` (the 2-fer guide PDF) | `preview`, then `on` | `off` | chat 8 |
| 3 | G10 switch `KPC_FERS_GPX` (the 2-fer GPX; it never drops a pin) | `preview`, then `on` | `off` | chat 8 |
| 4 | G10 switch `KPC_HOURS_PUBLISH` (bot hours onto park pages) | `preview` only. The local preview found 15 parks, and some lines are generic (e.g. US-4572 got a national free-days fee line). Brandon reads the changes list before `on`. | `off` | chat 2 |
| 5 | Which 2-fer list is the truth: KPC-Data data/fers (bot) or ky-overlaps.geojson (site) | data/fers is the source; the site layer is written from it, reviewed rows only (that is what G10 does) | both stay as they are | HQ (chat 7) |
| 6 | The HQ reviewed list (kpc-fers-reviewed.json) is empty | HQ fills it. G10 publishes nothing until then | empty | HQ (chat 7) |
| 7 | G6: pages stop showing held keys | Yes. 51 world-key countries disappear until they are released, so release them first, or accept the gap | not applied | chat 3 + chat 10 |
| 8 | `KPC_SAVE_RED` (a lost save turns the run red and sends GitHub's failure email) | `no`: a loud notice on the run page (the Oct 22 rule). Set `yes` only for the key releases. | `no` for the converted bots | chat 10 |
| 9 | Held US/CA builds stamped `f3d48d30899`, which no verdict quotes | Chat 10 finds where the id came from, then re-stamps. Chat 11 gives fresh verdicts that quote the build id. | no release | chat 10 + chat 11 |
| 10 | YES verdicts from before this morning's history restart (7:28 AM CST) | Ask for a fresh YES with the build id (stricter) | treat them as not yet given | chat 11 |
| 11 | The Canada YES (Nov 1) has no build id | Re-give it with the build id | skipped | chat 2 / chat 11 |
| 12 | Watchdog restarts of posting bots (G11 makes a restart do what the schedule does; e.g. the hunters' Friday run would post) | Allow it for the hunters' Friday post. Keep the practice-run bots (social, comments, relays) skipped, as G1 does | as in G1 | chat 10 |
| 13 | Research helpers pick their job by the hour, so a late restart would pick a different job | Keep them out of watchdog restarts (they already are) | skipped | chat 10 |
| 14 | Bots that email | A ruling: list the approved exceptions, turn the rest off | unchanged | HQ (chat 7) |
| 15 | OSM / Wikidata / Nominatim use | A ruling: an approved exception with the honest User-Agent and their rate limits, or off | unchanged | HQ (chat 7) |
| 16 | Delete the leftover branch test-keyfix-0102 (KPC-Links) | Yes, by hand | keep | chat 10 |
| 17 | `set -o pipefail` in every workflow step (follow-up to G8) | Later, one repo at a time; G8 already covers the bot scripts | not done | chat 10 |
| 18 | Move the KPC-Data save loops onto one shared helper (follow-up to G7/G8) | Later. They are loud now | not done | chat 10 |

How to set a switch: on the GitHub site, open KPC-Links, then Settings, Secrets and variables, Actions, Variables. Add or
edit the variable (for example `KPC_FERS_LAYER` = `preview`). Only do this after Brandon's OK, and note the time in your inbox.

## ANSWERS (Brandon Nov 2 9:51 AM: 'Yes implement it 100%, the ship is sinking and we must get it straight'; recorded by HQ 10:05 AM)
1-3 G10 2-fer layer / PDF / GPX: `preview` now (members / beta only), `on` after HQ checks the preview; public stays hidden until Brandon's GO. Acts: chat 10 sets the variables, chat 8 checks the preview.
4 KPC_HOURS_PUBLISH: `preview`, KENTUCKY ONLY (scope rule); Brandon reads the changes list before `on`. Acts: chat 10 + chat 2.
5 data/fers (bot) is the truth; the site layer is written from it, reviewed rows only. Acts: chat 10 (G10).
6 Reviewed list FILLED by HQ (KPC-Links kpc-fers-reviewed.json: 335 spots from the 11 files chat 11 said YES to). Acts: done; G10 preview reads it.
7 G6 yes, AFTER the world key's 4,330 YES are released (no blank countries). Acts: chat 10 releases, then chat 3 + 10 apply G6.
8 KPC_SAVE_RED = yes only for key releases; elsewhere a loud notice, no email. Acts: chat 10.
9-11 Chat 10 finds the stray build id (boundary-check bot first), re-stamps; chat 11 gives fresh YES quoting the build id (pre-restart YES = not yet given; Canada YES re-given with the id). Acts: chat 10, then chat 11 (+ chat 2).
12-13 Watchdog may restart the hunters' Friday post (never-twice state holds); practice / research bots stay out. Acts: chat 10.
14 Bots email ONLY on a real failure; every other email path off. Acts: chat 10.
15 OpenStreetMap / Wikidata / place-name lookups OFF for facts and shapes; only the outlines already labelled 'OpenStreetMap outline (unofficial)' stay. Acts: chat 10 + chat 2.
16 Delete branch test-keyfix-0102: yes. Acts: chat 10.
17-18 Later (after the rollout). 
G1-G11 patches: APPLY ALL, in PLAN.md order, each after `git apply --check` on a FRESH clone and its test; done = live (a real run / the site shows it), proof in LEDGER.md.
