# PRE-RELEASE READ, PART 2 (Research desk, chat 8, Mon Oct 26 ~7 PM)

Scope (HQ): SOTA rule lines, then chat 1's finished pages: About our information, Club Room, Parks, POTA / WWFF / SOTA rooms, New to POTA / WWFF / SOTA (plus Rules You Should Know to confirm the part-1 fixes). Repo at origin/main b4ae90f5 (17:21). The desk edited no page.

Method: read every page's text; checked rules against the programs' own documents; counted real call signs, local links, members-only links and notices; REHEARSED the release scripts on a scratch copy (not the repo): `release_public.py A`, `menu_release.py`, `info_line_release.py`, then opened the pages as a guest at 390 px and 1280 px with Playwright.

## 1. SOTA lines: CONFIRMED
Source opened: SOTA General Rules v1.20 (copy hosted by SOTA Germany: https://www.sota-dl.de/media/SOTA-General-Rules-v1.20.pdf). SOTA's own announcement of the 2022 edition is https://reflector.sota.org.uk/t/general-rules-2022/29309 (it says the rules are reached from SOTAwatch > Joining In; sota.org.uk itself could not be opened). Not confirmed that v1.20 is the newest issue.
- "4 contacts with 4 different stations to claim the points": RIGHT. Rule 3.7.1 item 8: at least one QSO makes an activation, "a minimum of four QSOs must be made, each of which must be with a different station" for the points.
- "One contact still logs a valid activation": RIGHT (same rule).
- Also right: 25 m vertical zone (3.5); no operating in or near a motor vehicle and nothing connected to one (3.7.1 item 3); non-motorised bikes or animals allowed to enter the zone (matches "walking, cycling"); no generators or permanently installed power (3.7.1 item 6); activator points once per calendar year (3.7.2); chaser points once per summit per UTC day (3.8).
- One wording nit (low): New to SOTA and Rules You Should Know say "Simplex only". The rules only say terrestrial repeater contacts do not count; satellite and balloon contacts are allowed. Safer: "No repeaters".

## 2. POTA rules page opened (docs.pota.app/docs/rules.html): all rule cards RIGHT, one QUOTE WRONG
Confirmed: 10 QSOs in one UTC day; activator and all equipment inside the boundary and on public property; vehicles parked on public property inside; no land repeaters; no relays; no fully automated contacts; separate log for each park in a multi-park activation.
**Fix (chat 1): the quoted 2-fer rule is not word for word.** New to POTA (twice), Rules You Should Know and the POTA Room print, inside quote marks and "POTA's rules say": Activations of multiple references ('two-fer,' 'three-fer,' etc.) are permitted... POTA's page reads: Activations of multiple references ("Multi-loc" or "two-fer," "three-fer," etc.) are permitted with Parks on the Air. Second sentence ("Such a multi-park activation requires an overlapped area where all activated parks' boundaries intersect") matches. The third sentence on our pages ("The intersection must entirely contain the activator and the station equipment.") was not in what the desk could read of the POTA page (the fetch tool may have trimmed it). Either paste the exact text from the page, or drop the quote marks and say "POTA's rules say, in short". A wrong word inside a quote is the kind of thing the overlap notice is meant to avoid.

## 3. Part-1 fixes: all six applied
Red River Gorge permit line · K4TEST / N4TEST in the sample QSO · KFF satellite sentence removed · nature-preserve audio wording · SOTA UTC rollover (both zones). WWFF log file name now follows rule 6.8 literally: `callsign@referenceYYYYMMDD`, example `K4TEST@KFF-123420261013.adi`. That reads as one long number; the desk could not see whether the rule has a space before the date (the fetch tool collapses spacing). Someone should look at 6.8 in the PDF once (https://wwff.co/wwff_cont/uploads/2025/09/WWFF-Global-Rules-V_5.10.pdf) and show the example with the space if it has one.

## 4. About our information: RIGHT
All 478 words of the required text are on the page, in order (the page adds only a hero line and a closing button row). Has a contact link. noindex is still on; the release script drops it (checked in the rehearsal). Footer link "About our information" appears on every page after the menu script (checked at 390 and 1280).

## 5. REHEARSAL RESULT (scratch copy, Plan A scripts applied, guest view)
Clean for About, Parks, the three rooms, the three New-to pages, Rules, Lounge: no members door, no locked link visible, no members-only wording (Map Rep, Spot Me, Logger, VIP, Club Room, Monthly Recap, Top 50, 2-fer guide), no sideways scroll, no page errors. Club Room and members.html show the sign-in door to a guest. kentucky-parks.html redirects to parks.html. Map Rep appears only in the Club Room (plus its own page and kpc-maprep.js / kpc-warn.js). No real call signs on any page in scope (N4KPC = club call in the header, K4TEST, N4TEST, W4K = SOTA association code). Local links: none broken. External links not tested (shell cannot reach them; chat 5's Sunday link check covers them).
Notes from the rehearsal:
- The old full Map Room page is still in the repo. The retired pointer is prepared (`.claude/build/release/map-room-retired-main.html`); chat 2 must put it in place (step 9) BEFORE chat 1's public-list step, or guests would see the old page (it mentions Spot Me).
- menu_release.py lists four pages for a hand check (contact-card, kentucky-parks, kpc-maprep, members); finder.html already has the About link and the independence line.

## 6. NOTICES: gaps (owner in brackets)
**2-fer / overlap notice missing on tools that show overlaps (word-for-word rule):**
- KY Trip Planner kpc-planner.html: "PARK OVERLAPS" layer and "2-fers flagged", no notice at all (chat 2).
- Park Commander finder.html: has its own "POTA 2-fer notice" paragraph, not the required wording, and it mentions WWFF (the required notice is POTA only). Needs the FULL notice (chat 2).
- kpc-park-control.html (public today): only a rule sentence about 2-fers, no notice; add the SHORT if it shows overlap areas (chat 2).
- kpc-multi-park-spots.html (members-only): a similar sentence ("not confirmed activation spots") but not the required FULL notice (chat 2 or 1).
- One-line mentions of "2-fers" in the Kit, Park Sheet and US Trip Planner blurbs (Kentucky parks "add 2-fers"): decide whether the SHORT line is needed there (HQ).
- OK: Club Room FULL notice is exact; parks.html and the Lounge carry the exact SHORT; the Kentucky POTA guide has both.
**Short information line ("planning aid, not a guarantee") after the release scripts, public pages without it:** POTA / WWFF / SOTA rooms, New to POTA / WWFF / SOTA, On The Air Now (kpc-spots), Band Plan, Field Weather, Radio Conditions, plus the old Map Room page. The script's list does not include the rooms, the New-to guides or On The Air Now; they mention park boundaries, park numbers and Kentucky guides. Recommend adding the rooms, New to POTA and kpc-spots (HQ decides; the weather and conditions pages are covered by the footer link and the LIVE INFORMATION paragraph).

## 7. Small items
- SOTA Room says "25 m (about 80 ft)"; the guides say 82 ft. 25 m is 82 ft: use 82 everywhere.
- Club Room (members): leftover builder sentence under Park of the Month: "To choose the park yourself, add it to PICKS at the top of the Club Room script." Take it out.
- Counts not checked against SOTA's own list: Parks says "216 Kentucky W4K SOTA summits", New to SOTA says "more than 200" (consistent with each other). "193 POTA parks" matches our data.
- Plan B: not tested.

## Summary for HQ
Must fix before release: (1) the POTA 2-fer quote on 4 pages, (2) overlap notice on KY Trip Planner and Park Commander (and park-control if it shows overlaps), (3) Map Room pointer in place before the public-list step. Nice to fix: WWFF file name spacing, "Simplex only", 82 ft, rooms + New to POTA + On The Air Now short line, Club Room leftover sentence. Everything else in scope checked out.
