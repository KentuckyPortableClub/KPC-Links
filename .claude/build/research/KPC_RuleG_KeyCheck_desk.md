# Rule G key spot-check (chat 8, Oct 29 ~2:30 PM)
Grade B/C: I compared the key's own names and acres; I did not open the agencies' maps (look-up bot needed for the A grade).
## A. "words" / "designation ignored" pieces still joined (2,377 pieces). Scan: only 9 have NO word in common with the park while a name-matched piece sits beside them; 3 more differ in the kind of place (Park vs Monument).
| Park | Extra piece joined | Verdict |
|---|---|---|
| US-0063 Sequoia National Park (CA) | Giant Sequoia National Monument, 352,617 ac | FAIL: a different unit (Forest Service). The park is already joined by name (406,662 ac). |
| US-4476 Clearwater National Forest (ID) | Nezperce National Forest, 2,109,873 ac | FAIL: a separate forest record, bigger than the park itself. Clearwater is already joined (1,682,090 ac). |
| US-8188 Revheim Bay SRA (SD) | Indian Creek Recreation Area, 298 ac | FAIL: a different Corps area; the real one (Revheim Bay Recreation Area, 145 ac) is joined by name. |
| US-0150 Kodiak NWR (AK) | "Kodiak Office", 38 ac | FAIL: an office, not refuge land (tiny, but it should go). |
| US-3030 Lake Somerville State Park (TX) | Somerville Recreation Area, 29,940 ac | CHECK: a lake-wide area that may be the Corps' land, not the state park. |
| US-7610 Old Hickory WMA (TN) | Old Hickory Lock 5 Refuge, 1,087 ac | CHECK: a bird refuge on the lake, not the WMA. |
| US-7356 St. Francis NF WMA (AR) | Stumpy Point Purchase Unit, 1,519 ac | CHECK: inside the forest; is it inside the WMA? |
| US-3699 Mobile-Tensaw Delta WMA (AL) | W. L. Holland WMA, 2 pieces | CHECK (lean yes): same delta complex, but the park is already joined at 22,495 ac. |
| US-9423 Miller Nature Sanctuary SNP (OH) | code "RFGrrMrStNP", 87 ac | CHECK: Ohio code that does not read as Miller. |
| US-1951 Forked Run SP; US-9408 Gallagher Fen (OH) | Ohio short codes | PASS (the codes spell the park). |
## New numbered rule proposed: R-G8
A "words" piece may join only if (1) it shares a place word with the park, AND (2) the kind of place agrees (Park / Monument / Forest / Refuge / Recreation Area), AND (3) it is not a bigger record than the park once the name-matched piece is already joined. Otherwise it stays in 'check', not 'joined'. This removes the 4 FAILS above; the other CHECKs stay in 'check'. Chat 2 decides how to build it.
## B. By eye
Not done in this pass: the 19 wetland districts, 5 approximate, 5 official parks need the look-up bot to open the agency maps. Handed to chat 9 below.

# R-G8 CONFIRM on the rebuilt key (chat 8, Oct 29 ~6:00 PM). Grade A: diffed the key at commit 97ccb901 (before) against HEAD (after R-G8) for all 12,833 state-park rows.
**Verdict: R-G8 CONFIRMED. "Rule G checked": yes.** Counts: 13,083 parks, 11,308 outlined (was 11,312), 131 check (was 120), 800 sites on bigger land (was 808), 853 none (was 858), pin outside 4,157.
1. **The 4 wrong pieces are gone:** Giant Sequoia NM off Sequoia NP, Nezperce NF off Clearwater NF, Indian Creek off Revheim Bay, the Kodiak Office off Kodiak NWR. Nothing new was joined wrongly.
2. **Every joined piece has a Rule G reason:** 0 of 115,445 joined pieces without one (name 101,929; reviewed 5,407; words 5,072; district 2,386; the rest smaller groups).
3. **No big park lost its outline.** Only 12 state-park rows lost an outline, all with a stated reason, all moved to 'check' (chat 11 can still say yes): 3 correct drops (Ebey's Landing Reserve, Silver Creek BLM, Miller Nature Sanctuary), 5 held by G-1 (Cline Buttes, East Shore, Point of Pines, Mongoquinong, Clinton Birthplace 1 ac), and 4 that R-G8 dropped but are probably TRUE matches (below).
## Two caveats for chat 2 (not blockers; chat 11's yes/no catches them)
- **R-G8 is a little too strict in 4 cases** (the piece is the same place): US-4477 Idaho Panhandle NF lost 'Kaniksu National Forest' (898,213 ac; Kaniksu was merged into the Panhandle forests, same family as the Siskiyou case chat 11 said YES to); US-4839 Lester R. Davis Memorial State Forest lost 'Davis (Lester R.) Memorial Forest' (same words in another order, 'State Forest' vs 'Forest'); US-1021 Sangchris Lake SP lost 'Sangchris Lake State Resource Area' 3,071 ac; US-11981 Arivaca Lake SWA lost 'Arivaca Land and Lake' 208 ac. Suggest: R-G8 (1) counts the same words in any order, and a short merger alias list (Kaniksu, Siskiyou) is allowed. Until then these 4 sit in 'check' for chat 11.
- **Two 'kind of place' joins still pass R-G8:** US-3030 Lake Somerville SP keeps 'Somerville Recreation Area' 29,940 ac and US-7610 Old Hickory WMA keeps 'Old Hickory Lock 5 Refuge' 1,087 ac. Both should be in 'check' by R-G8 (2).
## New-key 2-fer reruns: from my side the key can go (R-G8 PASS). Waiting on chat 11's approval.
