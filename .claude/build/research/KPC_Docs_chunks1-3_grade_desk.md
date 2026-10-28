# Documents bot, chunks 1-3 (NC VA WV GA AL SC FL MS IN) — chat 11, Oct 28 12:30 PM CDT
Random 12 maps (seed 77, 1,208 parks with a map link): **A 6, B 4, C 2 = 83% (bar 90): FAIL on maps.** Rules pages are worse (see counts).
A: General Coffee GA, Teter Creek WV, Dunkard Fork WV (file names carry the park), Hawks SF VA, Big Oaks IN, Jimmy Carter NHS GA.
B (honest but generic): Southern Nantahala (forest-level NC page), Sapelo Island WMA (WRD home page), Hilochee (FWC planning page), Owl Creek Mounds (forest-level MS page).
C: Lake W.F. George WMA (map link HTTP 403, kept); Mountain Lake Wilderness VA (map = inciweb.wildfire.gov).

## Whole-file counts (the same errors repeat, so these matter more than the 12)
- WV: **83 parks** have the rules page "wvdnr.gov/.../whitewater-commission/state-law-and-regulation" (a whitewater rules page, wrong for WMAs/forests).
- GA: **130 parks** have one publuu.com flip-book as the rules page (a single hunting-regs booklet, not each park's rules).
- FL: **53 parks** have a "shooting-ranges/safety-rules" page as rules.
- VA: **26 parks** have inciweb.wildfire.gov as the map (a fire-news site; status "robots").
- Map link that returned an HTTP error but is kept: 31 (FL 10, GA 6, AL 4, ...).
- Forest-level "maps-guides" page used as a park's map: 32 (MS 10, NC 10, AL 4, ...); Google Maps pin as the map: 5.
Good: Florida is now 460 parks / 160 map ok (was 6/12 right in run 1); names-the-park flag is honest on the 12 (Teter, Dunkard, Sapelo labelled "does not name").

## Fixes (to chat 2)
1. Reject a rules URL that 20+ parks share in a state unless the host is the park's own agency page (WV whitewater, GA publuu, FL shooting ranges): "no rules page" beats a wrong one.
2. Never keep a map URL that returned an HTTP error; never accept inciweb / fire-news hosts; Google Maps pins are not maps.
3. A forest-level maps page for a wilderness/sub-unit = label "forest map only", not "map ok".
