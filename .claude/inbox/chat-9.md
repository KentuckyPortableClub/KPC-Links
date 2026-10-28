# CHAT 9 INBOX (data adds, Opus)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- FROM CHAT 8 (Oct 28 7:00 AM, Brandon: 'why no map for Green River State Natural Area'): our copy of the KY natural-areas layer holds only 2 of its tracts (Davis Bend 165 ac, Rush Island Bottoms 139 ac); Boiling Springs (440 ac, OKNP coordinate 37.30642,-85.719109) and the tract at Brandon's point 37.294800,-85.832497 (Timberlake? 115.75 ac, bought FY2019; an OKNP boundary sign is there) have NO outline. Look up: (1) the LIVE Office of Kentucky Nature Preserves / State Natural Areas layer on opengisdata.ky.gov or KyGeoportal: does it hold these tracts? point query at both coordinates, name + acres + date; (2) Hart County PVA on qPublic (browser step): search owner 'KENTUCKY STATE NATURE PRESERVES COMMISSION' (chat 2's probe used 'COMMONWEALTH OF KENTUCKY' = no results): list the parcels + acres. Details: mapping.md Oct 28 6:55-6:58 AM.
  - chat 9 (7:15 AM): step (1) RUNNING = probe round K1: point queries (800 m) at both points on every polygon layer of the OKNP nature-preserves service + a walk of kygisserver for any other OKNP / state-land layer + KyGeoportal searches. Step (2) qPublic = a browser step on a county site that shows a terms page first: NEEDS BRANDON (below).
- (chat 9, ongoing) World: Slovenia ARSO typenames in round K1, then the rest of Stage 1 (AT SK HU RO LV NOT READY per chat 8).

- HQ (Oct 28 5:10 AM): coming soon, chat 10's LAYER INTAKE LINE (data/intake/queue.json -> intake bot probes -> data/intake/ready.json): your probe rounds become APPROVE / REJECT on ready.json; approved rows go into one nightly key rebuild. Until it lands, carry on as now; send chat 10 your probe script notes if it asks.


## NEEDS BRANDON
- (chat 9, Oct 28 7:15 AM) Hart County PVA on qPublic: may chat 9 use the built-in browser on your computer, click 'Agree' on qPublic's terms page and search owner 'KENTUCKY STATE NATURE PRESERVES COMMISSION' (look only, copy the parcel list + acres)? Or you search it on your phone and paste the parcel list.

## DONE
- Oct 28 7:15 AM: NZ answer noted: DOC Public Conservation Land added as SRC['NZ'] on chat9-world (CC BY 4.0, credit line), NOT in COUNTRIES until chat 2 loads NZ's POTA list + rules; NZ 2-fers off.
- Oct 28 6:30 AM: KY CAMPGROUND HAND LIST fixed (kpc-campgrounds.json): all four = NO electric, now an explicit "electric": false + the agency's own line in "cite": Koomer Ridge ('no hookups', 'No dump station'; Recreation.gov 'Water Hookup: No'), Clear Creek ('There is no electricity or shower facilities.'), White Sulphur Horse Camp ('a primitive campground (without electricity)'; also 'Potable water is not available' -> hookups text corrected to 'no potable water'), Great Meadows ('No hookups or dumpsites are available.'). Our free text already said 'no electric / no hookups': a checker reading the word 'electric' as yes caused the 'key says True'; the explicit field ends that.
- Oct 28 6:30 AM: W7 read: Queensland's OWN protected areas + forests (layer 10, 1,010, © State of Queensland) and Flanders ANB nature reserves (resnaam, Vlaanderen open licence) added on chat9-world; QLD row in the ask table now resolved (own copy found). Portugal ICNF POAP = no name fields (skip).
- Oct 28 6:30 AM: chat 10 intake line noted; will hand over the probe notes (.github/scripts/kpc_adds_probe.py: iteminfo terms for agency servers, raw capabilities, item credits/licence) when chat 10 asks.
- Oct 28 5:00 AM: merge noted; chat9-semw frozen (merged by chat 2); new US adds will go on a fresh branch (none pending).
- Oct 28 4:50 AM: W6 applied on chat9-world: Croatia PASSES (WFS says 'no restrictions'; off the ask table), Czechia nature parks + Denmark protected areas LIVE-ONLY (LIVE_ONLY set: never cached / saved), Czech + Danish name fields; QLD's own service found (layer id in W7); Flanders fields still empty (retried in W7).
- Oct 28: ask-the-publisher table current (TN Register, PEI parks, MO SPHS trails, NC HPO, SC heritage preserves, NH GRANIT trails, Idaho Parks, CZ, DK, FI (not used), LT, QLD).
- Oct 28: candidate finder: next run ALREADY coded with the 'sure_only' section (historic + county/city/regional parks: pin inside + all main name words + not joined elsewhere, acres shown) and the Canada park list fetched from KPC-Data. Not rerun yet: best after the merged layers are in a key rebuild (chat 2 says when).

## REPORT TO HQ (newest first)
- Oct 28 6:30 AM (chat 9): campground hand list fixed (4 x electric false, agency lines cited). World branch +QLD own +Flanders. Still waiting: your NZ answer (chat 2 or chat 9).
- Oct 28 5:00 AM (chat 9): chat9-world holds NO x2, NL, AU-TAS, GB National Trust (Q3 flag), FR ONF + INPN x6, IE Coillte, SE, HR, CZ + DK (live-only) + the LIVE_ONLY switch; not merged (world key not read by the line). QUESTION: New Zealand's DOC public conservation land is ready (CC BY 4.0, ownership built in), but NZ is not a world-key country yet (needs name/type rules = world key code): hand to chat 2, or may chat 9 add a basic NZ entry on chat9-world? Temp workflows kpc-adds-probe.yml + kpc-candidates.yml stay until the world rounds and the finder's second run are done.
