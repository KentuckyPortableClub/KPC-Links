# Keyed parking pull, accuracy check (chat 11, Oct 29 ~11:50 AM)
File: KPC-Data data/access-leads/keyed-pull-hold.json (771 parks, 2,818 points, 25 A / 362 C / 1,879 B / 552 D). Nothing here is live.
How I checked: 30 random points over 17 states (4 A, 8 C, 10 B, 8 D, seed 1129) judged by park name vs facility name, distance from the park pin, and what the thing is; plus whole-file counts. I did NOT open each agency map (30 pages); where I was unsure it says so.

## VERDICT: FAIL as one batch (HQ bar 28/30 and no wrong-park point). Two rules are good, one is mixed, one must go.
| rule | rows | my sample | verdict |
|---|---|---|---|
| A nps-own-park | 25 | 4/4 real park parking lots (3 Cuyahoga Valley lots, Old Slater Mill at Blackstone River) | PASS, but ONE SIGN BUG: Acadia 'Cadillac Mountain' lon is +68.2251 (should be -68.2251, 9,256 km away). Only positive longitude in the whole file. |
| C ridb-facility-name | 362 | 8/8 right place (Rim Rock, Redmond Caves, Mineral Ridge, Hidden Splendor, Cryptobiotic, Spring Creek boat ramp, Rainbow Basin camp, Linville Gorge info cabin) | PASS on place. Kind caveat: 71 are campgrounds, 15 labels are offices/cabins/centers (Linville 'Info. Cabin', 13.6 km from the pin) |
| B ridb-recarea-name | 1,879 | 9/10 in the right national forest or trail, but 8 of the 10 are campgrounds, rental lookouts/cabins or interpretive sites, not parking; 2 'Underground Railroad' facilities (Hoosier, Shawnee) look unrelated | MIXED. Place is believable (the rec area name matches), but 94% sit 5-30 km from the park pin, 673 are campgrounds, 172 labels hold office/lookout/cabin/visitor-center words. Cannot be called 'parking'. |
| D ridb-near-pin-only | 552 | 2-3/8 | FAIL, drop. Wrong things: The Willard InterContinental and The Mayflower hotels, Dept. of the Interior Museum, Hirshhorn / Air and Space / Natural History museums (all hung on Constitution Gardens, WWII Memorial, National Mall, President's Park); 'High Grade Trail' on Cordura Trail; Ranger District office on Angel Lake Road; Cotton Hill camp on Bagby State Park (unsure, other lake). 420 of 552 share NO name word with the park; 124 labels hold hotel/museum/office/visitor words. |

## Whole-file counts
- Same facility on several parks: 208 sources used on 2+ parks (552 point entries); worst 15 parks share one facility (RIDB 225589 'Bureau of Engraving and Printing' sits on World War I Memorial, George Mason, Constitution Gardens, FDR, MLK ...; 204085 DOI Museum on 5+). Almost all are D rows in Washington DC.
- Far off: 1 point (Acadia sign bug). Everything else is within 30 km of the pin by construction; I could not test 'inside the outline' without the outlines (use the waiting room's pin-in-outline check).
- Kentucky camps: the file holds ONE (Houchin Ferry Campground, NPS API 37.20169, -86.23772). That is right: Green River at Mammoth Cave. HQ asked for 4 KY camps: 3 missing.
- Kind mix: 25 parking, 735 camps/campgrounds, 2,058 'Facility:' rows (mixed).

## What I recommend (for chat 9, then Brandon's GO)
1. Fix the Acadia sign (check: any lon > 0 in the US = flip or drop).
2. Keep A (24 after the fix) and C (drop labels with office / cabin / visitor center / museum / hotel / headquarters words).
3. B only as 'Campground' or 'Parking/Trailhead/Boat ramp' and only for parks that have NO point at all; label campgrounds as camps, not parking; drop the office / lookout / cabin / interpretive rows. Run B through the waiting room (pin-in-outline).
4. DROP all of D (and add a stop rule: a facility may attach to ONE park, the nearest by name).
5. Re-send a 30-sample on what is left; I expect PASS for A + C.
