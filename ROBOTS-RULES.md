# KPC robots rules — read this, don't ask Brandon

The owner set these rules. They are final. Agents must not ask him about robots rules again.

## The standard

[RFC 9309 (Robots Exclusion Protocol)](https://www.rfc-editor.org/rfc/rfc9309).

Parse `robots.txt` with our own parser. Never use `urllib.robotparser` internals.

## Club rule R-NET1 (Brandon, 24 Nov 2026)

Check `robots.txt` first on every host.

**When robots.txt answers:**

- **401, 403, 404, or any other 4xx except 429:** no rules are posted. Fetching is allowed. Only a real `Disallow` line that matches our user agent and path is a no.
- **429 or 5xx, or no answer at all** (timeout, connection refused or reset, DNS failure): treat the host as unreachable for this run, per [RFC 9309 section 2.3.1.4](https://www.rfc-editor.org/rfc/rfc9309#section-2.3.1.4). Skip that host this run. Try again next run.
- Some government GIS firewalls silently drop `/robots.txt` while the data endpoint still works. If a host repeatedly times out on `robots.txt` only, but its data endpoint works, flag it to the owner. Do not guess.
- **The file loads but cannot be parsed:** do not fetch from that host.
- **Redirects:** follow up to 5 hops (RFC 9309).
- **Cache:** keep `robots.txt` up to 24 hours (RFC 9309). One robots read per host per run.

**When the page itself answers:**

- **401, 403, or 429:** stop hitting that host for the rest of the run. A 403 may be retried once after a delay (the 3 Nov 2026 manners patch).
- A skipped or resting host keeps earlier saved data exactly as it was. Never wipe it or overwrite it with a "host resting" placeholder.

**Blocked official sources:** if a free-use official source blocks bots in `robots.txt`, do not silently skip it. List it for the owner to hand-download in a normal browser.

**Site terms still apply.** A path that robots allows is not automatically a path the site's terms allow. Agency lists may be fetched if robots allows and the terms do not forbid automated use (stay private, matching only). Never use a sign-in, a proxy, or any other trick to get around a block.

## Be polite

- Use an honest User-Agent that names KPC and gives a contact. The existing club string (discovery bot in `.github/scripts/kpc_leadtest.py`) is `KPC discovery bot (kentuckyportableclub.github.io; ham radio club; 1 request a second)`. If a fetcher has no string of its own, use `KPC-bot (Kentucky Portable Club; https://github.com/KentuckyPortableClub)`.
- Obey `Crawl-delay`. If none is set, wait at least 1 second between requests to the same host, and send only one request at a time per host.
- Honor `Retry-After`. Back off on errors. Stop at the first sign the host is struggling.
- Download whole layers once. The PC's LAYER-RECORDS program does downloads. Keys never download layers.
- Use paging and caching. Never re-download unchanged data.
- Run big pulls off-peak when possible.

## Where this is enforced

There is no file named `kpc_manners.py`. The manners live here:

- Research inbox manners: [`.github/scripts/kpc_inbox_manners.py`](.github/scripts/kpc_inbox_manners.py) (class `Manners`; our own RFC 9309 parser; one robots read per host per run; `Crawl-delay` and `Retry-After`). That code already uses a 2-second floor between requests to one host, which is stricter than the 1-second minimum above.
- Host never-contact list: [`.github/scripts/kpc_net_guard.py`](.github/scripts/kpc_net_guard.py).
- Store / LAYER-RECORDS engine in the private KPC-Store repo: `engine/kpc_outline_store.py` and `engine/fetch-settings.json`. The inbox manners were copied from that engine.

Keys never contact agency servers. They read saved copies only.
