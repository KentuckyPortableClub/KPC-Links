# Pull-off and parking finder: rule sheet + build spec (chat 10, Oct 31 2026)

Brandon, Oct 31 6:45 PM: "instructions for building a bot that can look for pull offs and parking areas … looking at our maps?"

**Short answer: yes, this is possible.** We already have the hard parts: official park outlines, official access points, and saved agency picture maps. Public aerial photos from the US government (USDA NAIP) are good enough, at about 0.6-1 m a pixel, to see a gravel or paved lot beside a road.

What the bot finds is a **CANDIDATE**, not an official parking spot. Because it decides what people see, the house RULES FIRST order applies:
1. **this sheet**
2. **chat 8 breaks it** (grey areas)
3. **Brandon rules**
4. **HQ records it**
5. **then build**

Builder: the outside coder (install contract = PART A of `KPC_10_Outside_Tools_Specs.md`). Folder `kpc_pulloffs/`. Chat 10 wires it.

---

## PART 1. RULE SHEET (draft for chat 8 + Brandon)

**1. What counts as a candidate.** A place a car can pull fully off a PUBLIC road and stop, seen on the aerial photo:
- a gravel or paved lot, a turnout, a wide shoulder bay, or a trailhead lot;
- at least about 300 m² (room for 3+ cars), touching a public road;
- **inside** the park's official outline, or **within 100 m** of it.

**2. What does not count:**
- driveways, farm lanes, house or business lots, and anything behind a gate seen on the photo;
- roads marked private in the road data, and closed or seasonal roads;
- spots on a divided highway or an interstate;
- spots with no public road to them;
- any spot near a park with no official outline (no outline = nothing to measure from).

**3. Sources, best first.** All of these are official or public-domain; never OpenStreetMap, Google, AllTrails or app maps.
1. the agency's own access points (already in `data/access`): if one is within 50 m, the candidate is a duplicate and is dropped;
2. the agency's own picture map (picture-maps branch): a P or parking symbol near the spot raises the confidence;
3. Census TIGER/Line roads (public domain): what is a public road and what it is called;
4. USGS National Map / state DOT layers (rest areas, scenic overlooks, trailheads, turnouts) where the state publishes them;
5. USDA NAIP aerial photos (public domain, `imagery.nationalmap.gov` USGSNAIPImagery ImageServer): the "is there a lot here" test.

**4. When unsure.**
- A candidate the photo test scores below the cut is **kept out**: written to the bot's own log only, never shown.
- Recent construction, or a photo older than 5 years, means the candidate is marked "photo is old (<year>)".

**5. What people see, and the wording.**
- **Only after chat 11's YES** (with the photo chip in front of them).
- **The label:**
  - Inside the outline: **"Possible pull-off (seen on an aerial photo, not official). Inside the park's official boundary."**
  - Within 100 m outside it: "… Just outside the park's boundary: walk in to activate."
- **Notice:** every card carries the SHORT information notice.
- **Never call it "parking" without the word "possible".** Never say parking is allowed there: signs on the ground win.
- Rule 16 (parking inside the line = inside the park) applies only to the "inside" ones.
- **Show it under** the official access points, never above them.

**6. Real examples to test on (Kentucky first: 1,360 hand-checked access pins are the answer sheet).**
- **Green River Lake WMA KY:** gravel lots on Hwy 55 shoulders. They should be found, and the ones already in the KY 'ap' list are dropped as duplicates.
- **Red River Gorge (Daniel Boone NF):** paved trailhead lots on KY-715. Found; they match the Forest Service trailheads.
- **Mammoth Cave NP:** visitor-center lots. Found, but already official, so they are dropped.
- **A WMA bordered by farms:** farm lanes off the county road must NOT be found (no road name, or a private road; the lane leads to buildings).
- **Land Between the Lakes:** long gravel shoulders on The Trace. A shoulder narrower than about 8 m is not a pull-off.
- **A city park with no official outline:** nothing at all is produced.

**Grey areas for Brandon** (please rule):
- **G-P1:** Should a road shoulder inside the park, with no lot, count?
- **G-P2:** Is 100 m outside the line the right distance?
- **G-P3:** Members can already submit parking. Should the bot's candidates go to the same review queue?

---

## PART 2. BUILD SPEC (`kpc_pulloffs/`)

**In.**
- `--parks <file>` = `[{ref, name, outline_url or outline_file, lat, lon}]` (chat 10 builds it: parks with an OFFICIAL or approximate outline; KY first).
- `--access data/access/*.json` (known points, for dropping duplicates)
- `--pictures <picture-maps index.json>`, optional

**Steps for each park.**
1. **Outline:** read it (simplified to 3 m) and make a 100 m outer band.
2. **Roads:** TIGERweb Transportation (`tigerweb.geo.census.gov`) for road lines crossing or inside the band. Keep the public road classes; drop "private" (MTFCC S1740 private roads, S1780 parking-lot roads only as hints) and interstates (S1100).
3. **Points to look at:**
   - every place a road enters the outline;
   - every 150 m along roads inside the band;
   - every DOT / USGS turnout, overlook or trailhead point in the band.
4. **Aerial photo:** for each point, fetch a NAIP chip (about 120 × 120 m, 0.6-1 m a pixel, 4 bands with near-infrared) from the ImageServer `exportImage`. Cache the chips; there is 1 request per 2 s per host.
5. **Lot test (simple and explainable, no black-box model needed for version 1):**
   - **pixels:** vegetation index low (NDVI < 0.15), not water (NIR not very dark), not a roof (no sharp rectangle with strong shadow on one side);
   - **shape:** the area has to be one connected patch of ≥ 300 m² touching the road line;
   - **score 0-1** from the patch size, how much of it touches the road, its shape (lots are compact; roads are long and thin), and a parking symbol on the picture map within 100 m.

   Version 2 may add a small trained model, but only if version 1 misses too much on Kentucky.
6. **Drop duplicates:** any candidate within 50 m of an official access point is dropped.
7. **Where it is:** inside the outline or outside it (and how far).

**Out.**
- `<out>/pulloffs/<area>.json` → `{ref: [{lat, lon, score, inside: true | false, dist_out_m, road_name, road_class, photo_year, chip: "<file>.jpg", why}]}`
- **chips:** JPEG 400 px with the park line drawn in yellow, the road in white and the patch outlined in red; this is what chat 11 looks at;
- `<out>/pulloffs/review.md`, best first.

**Acceptance (Kentucky).**
- **Recall:** it finds ≥ 60% of the KY hand-checked access pins (within 50 m) that sit next to a road. These are found before the duplicate drop, for the test only.
- **Precision:** in chat 11's sample of 50 new candidates, ≥ 80% are real pull-offs.
- **Farm lanes:** zero driveways or farm lanes on the 6 example parks.
- **Time:** the whole of Kentucky runs in ≤ 4 runs of 50 minutes.

**How chat 10 wires it.**
1. Run it monthly, one state per run.
2. Candidates and chips go on the KPC-Data side branch `tools-out` (`pulloffs/`), never on main (BRANCH FIRST, Brandon Oct 31 6:18 PM). Only the chat-11 YES points reach main, in the access file, through the waiting room.
3. Chat 11 grades it, with the chips.
4. A YES moves the point into the access file with `kind: "possible pull-off (aerial photo)"`.
5. The site shows it with the wording above.
6. Order: Kentucky first, then the rest of the US, then Canada (Canada's photos: the provinces' open orthophotos, not NAIP; later).
