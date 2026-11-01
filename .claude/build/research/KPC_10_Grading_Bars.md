# Grading bars, misses and contacts for the outside coder (chat 10, Nov 1 2026)

## 1. The bars (what chat 11 passes or fails; use the same rules in your graders)

**Outlines / layers (Rule G).** An outline is accepted only on a SURE official match. All three of these must hold:
- the POTA pin is INSIDE the record, or within 150 m of it with a name match (R-G12);
- the NAME matches;
- the SIZE is similar.

Tiers (`kpc_tiers.py`, also in the club's notes as T-1..T-6):
- **SURE:** the proper words are equal both ways once kind words are stripped (park, reserve, WMA, state, national ...). It is not a line park matched to a polygon, not a container (one record under several parks' pins), and its size fits or is unknown. → bot YES allowed, with chat 11's 1-in-10 sample.
- **LIKELY:** the proper words overlap (2+ words, or the whole shorter name). It is not a line and not a container. → chat 11 grades.
- **UNLIKELY:** everything else (one shared word, no shared word, container, line vs polygon, size far off). → evidence only, NEVER a question.

The kind must match too: a WMA only matches a WMA, a state park only a state park. "X Lake WMA" ≠ "X Lake State Park".
- **Size:** within 1.5× is PASS, 1.5-5× is OFF (a person looks), over 5× is WAY OFF (no). The parcel tracer holds anything outside 0.2-2×.
- **Map-match (T1) band:** STRONG = bot YES. It scored 100% YES on 200 held-out answered rows. CONFLICT is only ~67% NO, so it is never an auto-NO.
- **A whole key file** (one state / province / country): chat 11 samples 30 joins and needs 30/30 (names / kinds / acres; outlines lost = safe pins). One wrong join → that row is pinned, then the file passes.

**Official maps / pages (documents):**
- the link OPENS (HTTP 200, a real PDF / image / map page);
- it NAMES THE PARK (PDF first page, page text, file name or link text);
- it is NOT a file shared by more than 3 parks;
- it is NOT a sign / logo / letterhead;
- it never replaces a map already marked `status: ok`;
- Wikipedia / tourism / app pages are never "official".

**Parking / access points:** chat 11 samples about 30 points. The bar is 27-28/30 right, with 0 points on the wrong park, 0 west longitudes written as positive, 0 shared facilities, and no wilderness / office / hotel / road-number labels.

**Campground facts (campinfo):** about 97% of the sampled facts must match the agency page. A fact taken from another business's line (golf course, marina, pool, picnic shelter) is a FAIL row: the Nov 1 fixes (Pennyrile season, Kentucky Dam Village phone, TN S-Tree 'reservable').

**Hours / fees (Kentucky only):** a 12-row sample, 12/12 to pass. Oct 31 was 9/12 and failed: marina / scuba hours filed as park hours, bare '10 AM - 4 PM' fragments, 'Open seasonally' under hunting hours.

**2-fers** (never auto; chat 8 + chat 11 by hand):
- a public, owned overlap patch at least 50 yards across;
- lines (trails / rivers) count within 100 ft of the edge;
- parks that only touch = not a 2-fer;
- proclamation lines are not land;
- two owners claiming the same ground = 'likely map mistake' unless one is a designation / lease on the other.

**Spec pass marks for new tools:**
- pull-offs: precision ≥ 80% on 50 candidates, recall ≥ 60% of KY hand pins;
- camp layers: ≥ 95% of kept features really campgrounds, with 0 picnic shelters and 0 boat ramps among them;
- acres: ≥ 95% within 10% of the Kentucky answer key, with 0 WMAs matched to a state park;
- finder: ≥ 95% of past YES found again, ≥ 25% more parks, ≥ 85% YES in a sample of 40.

## 2. Misses worth testing (real parks)

| park | what went wrong | the lesson |
|---|---|---|
| US-10476 Monument BLM RMA (OR) | joined to "Monument GS", a 1-acre record of another kind | the size + kind check, not the name alone |
| US-0686 Big South Fork NRRA (KY / TN) | the KY outline also held a 30,138-acre "same land" copy inside the main one | merge same-land copies, don't count them twice |
| Yatesville Lake SP vs Yatesville Lake WMA (KY) | the state park took the WMA's outline (same lake name) | kind words decide: SP ≠ WMA |
| Little South Fork SNA (KY) | took the Little South Fork Wild River corridor | a wild-river corridor only matches a wild / scenic river park |
| US-10172 Salato Wildlife Refuge (KY) | the parcel trace took the KDFWR headquarters land next door: 921 ac vs 229.85 ac | hold anything over 2×; same owner ≠ same park |
| US-3118 Halfmoon Pond (VT), US-8388 Great Falls Discovery Ctr (MA) | the parcels sit inside another park's official outline (Bomoseen SP, CT River Greenway SP) | never absorb another POTA park's land |
| US-10389 Hiwassee Dam | the same-owner land ran past 10 km (9.8× size) | cut-offs are held back, never drawn |
| Oxford Slough WMD vs WPA; Halfbreed Lake vs Grass Lake NWR | chat 11 NO: a district / a different unit of the same refuge system | "management district" is a container, not the park |
| Prairie Coulees NA (AB) = Hargrave Coulees NA since 2020 | the checker REJECTED the right record as "a different place" | look for renames (order in council) before rejecting |
| Colony Farm (BC) = ƛ̓éxətəm; Mount Douglas = Pkols | no name match at all | Indigenous / French / renamed variants |
| Denys Fort NHS (Shippagan) vs "Nicholas Denys Site" (Bathurst) | same person's name, different place | distance check always |
| Green Gables (PEI) | the pin's parcel = all of PEI National Park's parcel | never the parent parcel (size check) |
| Lighthouse Park (BC) | the greenspaces layer labels its shape "Trails Park" | cross-check mislabelled layers with ParcelMap BC |
| Fort Providence (NT) | POTA pin 111 km off (latitude 62 for 61) | R-G13: use the official point, list the typo, pin never moves |
| Cedar Creek Lake WMA (KY) | a known answer held the whole KY file: 789 vs 796 acres was "off" | known answers need a size tolerance and get updated when the agency changes |
| Ganaraska / ABCA / SNC / RRCA records (ON) | false "no hit": the pin sat 7-107 m outside on the road | R-G12: the 150 m near-test + name |
| Alberta parks layer | queries on PARK_NAME returned nothing: the field is NAME | read `?f=json` field names first; an empty answer ≠ "no record" |
| BLM_Natl_SMA | whole-state surface-manager polygons matched to parks | never match against that layer |

## 3. Agency contacts
- **None.** The club has not contacted agency staff for layers. Every source came from public pages, services and portals.
- So the README should NOT list people. List the agency's own GIS / open-data contact page only when the agency publishes one, and never send email from a bot.
- The Agency Atlas files (`tips/agency-atlas/` in the sources zip) hold everything known per agency: portals, servers, folders, page patterns, which sites block bots.
