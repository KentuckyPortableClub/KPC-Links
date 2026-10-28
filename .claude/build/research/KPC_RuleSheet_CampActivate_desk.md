# Chat 8 breaks RULE SHEET E: Camp & Activate (desk, Oct 28 2026)
Verdict: the idea is right and the Kentucky examples are good. The sheet breaks mainly on POINT ACCURACY (a 15 m edge test cannot be trusted with most campground points). 8 numbered fixes first, then edge cases, then leans.

## FIXES (E-R1 ... E-R8)
- **E-R1 Tolerance by source, not 15 m.** The sheet uses one 15 m margin. Campground points come from three sources of very different accuracy: an agency's own campground GIS layer (about 30 m), RIDB facility coordinates (often an entrance, office or loop centre: hundreds of metres; B/C, I did not test RIDB points), and street-address geocodes (street level). Rule: the 'inside' margin = the source's tolerance: agency layer 30 m, RIDB 150 m, geocode = never inside (already rule 8). A point closer to the edge than its margin goes to 'check first'. Within the margin the row never says 'inside'.
- **E-R2 Same for 'activate both'.** A 50-yard patch is only ~46 m across; with a 150 m RIDB error almost every RIDB point is 'check first'. Only agency-layer points (or members' field-confirmed points) can make an 'activate both' row. RIDB-only campground inside a patch = 'check first: point too rough'. (This is honest: it will make the list short at first.)
- **E-R3 Merge rule (rule 6) is wrong.** 'Two campgrounds with one name 2 miles apart = one row' will merge real different places ('Lake Shore Campground', 'Camp Ground A'). Rule: merge only when names match AND points are within 300 m; same name 300 m - 5 miles apart = two rows and a line in chat 8's list.
- **E-R4 Loops.** Where RIDB gives loops or sites, use them: any loop inside = 'some sites inside', all loops inside = 'inside'. A campground that straddles the edge says 'part of this campground is inside' (resolves E1: point first, loops when we have them).
- **E-R5 Line-park band.** 100 ft (30.5 m) is tighter than trail-line accuracy (the official line itself is often ±15-30 m). Rows between 70 and 130 ft go to 'check first'; only under 70 ft say 'within 100 ft'.
- **E-R6 Lake and river edges.** NHD shoreline moves with pool level (Cave Run, Green River Lake). The row says 'at normal pool' and the 'check first' band is 100 ft + 30 m.
- **E-R7 Closed or seasonal campground.** A campground closed for the season (Sheet D class d) stays on the list, labelled 'closed <dates>', and its 'activate both' row is hidden for those dates; reservations-only/walk-in = shown with that word. (E5 extended)
- **E-R8 Counts and caps.** A forest with 60 campgrounds is fine; 'nearby' is capped to the 10 nearest per park so a card stays short; line parks measure 'nearby' from the line.

## Example checks (Kentucky)
1. **Zilpo (Ex. 1):** Works if the Daniel Boone owned layer and Pioneer Weapons WMA both cover the point and the patch is ruled. Two hazards: Pioneer Weapons is a hunting WMA, so Sheet D HUNT dates must hide the row (E5); and the patch is the WHOLE WMA only if the WMA sits fully inside the owned forest. Check: the WMA's own outline should be the Forest Service land KDFWR manages. If Zilpo's RIDB point is 120 m from the patch edge, E-R2 makes it 'check first'. I would run Zilpo as the first manual test with a member standing there. (C)
2. **Otter Creek (Ex. 2):** Fine. Note the transferred park keeps its outline (Brandon rule). The 'river-bank overlap 0.6 mi away' wording is good.
3. **Houchin Ferry (Ex. 3):** DEPENDS on the truth checker. Our US-10105 outline is the Kentucky state Wild River corridor (6,984 ac), not an NPS Wild and Scenic corridor; the 2-fer patch in ky-overlaps (Mammoth Cave × Green River Wild River, 7,005 ac) only holds if that designation is the one POTA means. Until Brandon rules (see the Truth Checker file), campgrounds in that patch = 'check first'.
4. **Sheltowee (Ex. 4):** point rule is clean; the polygon question (E1) is solved by E-R4 + the 'check first' list.
5. **Blue Heron (Ex. 5):** good. Ruled pairs beat geometry. Make that a numbered rule: E-R9 'a pair ruled DROPPED never produces an activate-both row, even if geometry overlaps'.
6. **Cumberland Falls (Ex. 6):** good, same rule.
7. **Address geocodes (Ex. 8):** good rule. Add: the row says 'location approximate' in words, and members can confirm a point (the confirmed point replaces it).
8. **Land Between the Lakes (Ex. 9):** hardest. The park is Forest Service land (from TVA) and Kentucky Lake WMA says TVA-owned. Layered ownership (rule 14) decides; if PAD-US says TVA fee for the same ground, the pair is NOT SURE and the campground stays 'inside LBL' only.
9. **Canada (Ex. 10):** fine. Provincial park campgrounds almost never have a point in the open data: they are 'nearby/NOT SURE' until the province gives a point.

## More edge cases
- **Camp inside a SOTA/WWFF reference** (not a POTA 2-fer): show 'Also:' only, never 'activate both' (house rule).
- **3-fer patch** (three parks share one patch): label 'activate three' with the same notice; one row.
- **Concession campground on public land** (private operator, public ground): counts if the point is inside owned land. A fully private campground bordering the park never counts.
- **Walk-in/hike-in/backcountry sites** (E2): include with their kind; add 'walk-in' and distance from parking if the agency gives it.
- **Reservation booking links:** link only the agency or Recreation.gov/state system, never a third-party reseller.
- **POTA activation vs camping:** the row never says 'you can activate from your site' (already so); it says we think the spot is inside, plus the notices.

## Leans on the grey areas (Brandon rules)
- **E1** Points first, loops when available, straddling = 'part inside'. YES.
- **E2** All kinds shown with their kind (tent, RV, group, horse, walk-in, cabin, shelter); day-use shelters and picnic areas out. YES.
- **E3** Straight-line 5 miles from the edge; fine for now, road miles later. YES.
- **E4** Dispersed camping zones: a park note, never a row. YES.
- **E5** Hide 'activate both' for HUNT dates, keep 'inside' with the closure. YES.
- **E6** Within a state first; a 'top 50' list only after the first bot run is graded. YES.
- **New E7** Source tolerance (E-R1/E-R2): confirm that RIDB-only rows can never be 'activate both'. Lean YES (it protects the club's name).
- **New E8** Members confirming points in the field (Sheet 10 idea): lean YES later, with a photo-free simple form.
- **New E9** Should 'check first' show to everyone or members only? Lean members only, with the reason.
