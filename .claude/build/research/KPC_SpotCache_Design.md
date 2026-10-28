# Shared spot cache: DESIGN ONLY (chat 5 for chat 3, Oct 28 2026; Fable's limits plan item 7)

**Status:** design, not built. Build only when the visitor counter (GoatCounter) shows the Lounges with ~100 people on at once, or POTA asks us to call less. Until then each open Lounge tab keeps polling POTA itself, like pota.app does.

## The idea
One bot fetches POTA's live spot list (`https://api.pota.app/spot/activator`) every 2 minutes and puts a trimmed copy in ONE small public JSON file. The Hunters Lounge, Activators Lounge, Happening Now, Spot Me and the CW spots read that file first, so 100 open tabs make 100 cheap requests to a CDN instead of 100 calls to POTA. If the file is missing or stale, the page falls back to POTA live, exactly as it does today.

## Where the file lives (the part that matters)
- **NOT in git.** Rewriting a file every 2 min would be 720 pushes a day. KPC-Links is aiming for under 60, and KPC-Data has the same 10-builds-an-hour soft limit, because each push rebuilds that repo's site.
- **Not a GitHub Release asset either.** Browsers can't read release downloads from our pages (no CORS header), and the URL changes on re-upload.
- **Recommended: a public GitHub Gist** (one file `spots.json`), updated through the Gist API. `gist.githubusercontent.com/<user>/<id>/raw/spots.json` is served with `Access-Control-Allow-Origin: *`, so pages can read it. GitHub's CDN may hold a copy for a few minutes, which is fine because the file carries its own time stamp (see "Freshness" below). A Gist edit is not a repo push and does not build any site.
  - Needs ONE new secret in KPC-Links (Brandon adds it in Settings → Secrets; never in chat): `KPC_GIST_TOKEN` (a token with only the `gist` permission), plus the Gist ID as a plain repo variable `KPC_SPOT_GIST`.
- Fallback option if the Gist route is ever slow or limited: a free Cloudflare Worker / R2 bucket. That is an outside account, so it's Brandon's call and not part of this design.

## Who writes it
- The **spotter job** (`kpc-pota-discord.yml`) is already ONE job an hour that checks POTA every 5 minutes (12 polls). The cache writer goes in the same loop, so ONE POTA fetch feeds both the Discord alerts and the cache. Its poll gap drops from 5 min to 2 min (about 28 polls an hour), which is still far gentler than one open pota.app tab (60 s).
- The Hunters bot (`kpc-hunters.yml`, every 15 min) stays as it is. Later it could read the Gist instead of POTA, saving one more call.
- Each write is skipped when nothing changed since the last one (same spot IDs and times).

## The file
```json
{"t": "2026-10-28T14:02:00Z", "src": "api.pota.app/spot/activator", "n": 143,
 "spots": [["K4TEST", "US-1271", "14285.0", "SSB", "2026-10-28T13:59:12", "Taylorsville Lake State Park", "US-KY", "QRT soon"], ...]}
```
- Rows are arrays with a fixed order, written down in the file's own `cols` key: activator, reference, frequency (kHz), mode, spotTime (UTC), park name, locationDesc, comments (cut to 60 letters). Nothing else is copied: no spotter call or spotter location.
- Expected size: about 40-80 KB plain, about 10 KB gzipped (the CDN gzips it).

## How the pages read it (one shared helper, chat 3)
- `KPC.spots()` in a shared script: fetch the Gist URL with `?m=<current minute>` so the browser doesn't keep an old copy.
- **Freshness:** if `t` is older than 6 minutes, or the fetch fails or takes more than 4 s → fetch POTA live (today's code path). The page shows "spots as of 2 min ago" from `t`.
- Tabs keep their own 60 s refresh timer; with the cache, each refresh is one CDN hit.
- The app (chat 4) can use the same URL later; Spothole calls stay as they are.

## Rules (RULES FIRST, short)
1. The cache only ever COPIES POTA's public list; no ranking, no filtering beyond the trimmed fields.
2. Unsure (bad feed, POTA down) → don't write. Pages then fall back to live by themselves once `t` is old.
3. Never more often than every 2 minutes; never at the same time as another POTA call from our bots (same job).
4. No secret, token or member data in the file (it is public).
5. Pages never show cached spots older than 6 minutes as "live".

## Work when it's built (later)
- Chat 5: the writer step in the spotter loop + secret names for Brandon.
- Chat 3: the `KPC.spots()` helper and switching the Lounge, Happening Now, Spot Me and CW spot readers to it; test on one page first.
- Chat 1: nothing (the helper can live in an existing shared script).
