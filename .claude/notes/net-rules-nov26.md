# The club's rule for contacting a site (owner, 26 Nov 2026, 9:46 and 9:49 PM)
His words: "We only avoid if robots.txt say we can't." "Avoid servers if they say no plain and simple."
"for some reason that affects a lot of our tools: it thinks it's blocked but it's not."

ONE RULE: a site is BLOCKED only when its robots.txt has a real Disallow line that covers what we ask for. Nothing else is a block.
Everything else is "not now" at most, and "not now" is never saved as blocked:

| What happened | What it means | What the tool does |
|---|---|---|
| robots.txt has a real Disallow for us (or *) covering the path | the site says NO | do not ask; list it "needs a hand download / a hand look"; tell the owner |
| robots.txt answers 401, 403, 404 or any 4xx except 429; or there is no robots.txt | no rules | ALLOWED: carry on |
| robots.txt answers 429 or 5xx, or times out | the site is busy | not this run for that site; try again next run by itself |
| robots.txt answers 200 with something that is not a robots file (a web page, empty) | no rules | ALLOWED (a page is not a Disallow line) |
| the page or data request itself answers 401 or 403 (or the page is an "are you human" wall) | "not now" for that page or layer | no retry of it; the site carries on at its slow pace; try it again next run; never saved as blocked (owner 27 Nov 4:15 AM: "sure we are just polite") |
| 5 pages or layers IN A ROW from one site answer 401 / 403 / a wall, nothing read between | the site is refusing us today | stop asking THAT site for the rest of THIS run; try again next run; never saved as blocked (one number: `refusals_in_a_row` / `REFUSALS_IN_A_ROW`) |
| the page or data request itself answers 429 | the site says slow down | stop asking THAT site for the rest of THIS run (no retry, no hammering); try again next run; never saved as blocked |
| robots.txt gives a Crawl-delay | go slow | obey it by going slow, however long; never skip because it is long; say on the status page that the site is slow |
| an old note says a site is blocked | a note, not a rule | check robots.txt live before believing it |

Separate rule, unchanged: the key builders never contact a server at all; only the owner's PC downloader and page reader do.

**Confirmed by the owner, 27 Nov 2026, 4:15 AM:** a bot-check page or another site's page at the robots.txt address = no rules,
allowed ("yes what wrong with reading?"). The page reader's wall limit stays 3,000 characters. Both are single values in
`kpc_net_rule.py` (DECISIONS).
