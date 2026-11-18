# Grade of the new matching rules: MD, MI, OH, TN (old key 052a24f0~1 vs new 052a24f0)

Activation counts are field 7 of the parkinfo rows. Full list: changes.csv (107 changed parks).

## Counts
| State | Changed | RIGHT | WRONG | UNSURE |
|---|---|---|---|---|
| MD | 16 | 13 | 0 | 3 |
| MI | 18 | 16 | 1 | 1 |
| OH | 44 | 23 | 14 | 7 |
| TN | 29 | 21 | 0 | 8 |

Only grade changes: MI 6 pin/approximate parks became official (Wild and Scenic rivers), TN Ozone Falls pin to official. No park went down to a pin. Every other change is a record swap inside an official park.

## What the rules got right (most of it)
- The contest works. Ohio, Maryland, Tennessee state parks, forests, wildlife areas and nature preserves that share a name were pulled apart by their type words (SP / SF / WA / DNP): Elk Neck SP vs SF, Pickett, Chickasaw, Standing Stone, Cedars of Lebanon, Delaware, Dillon, Hueston Woods and the rest. Bare-name records (the ODNR "e" layer, e.g. CAESAR CREEK 6806 ac) tied between two parks went to a person, and every park kept its own typed records, so no outline was lost.
- D9 / exact name: Harriet Tubman state records went back to the state park; Cheatham Lake and Cordell Hull exact-name records went back.
- D7: Big South Fork lost its two state compilation copies and kept the NPS record (83,326 ac).
- Park Service unit code: Harriet Tubman NHP vs state park fixed.
- Michigan game areas and the Wild and Scenic rivers gained their own records; Tennessee state parks gained the new "tnd" layer copies.

## WRONG rows (15)
All Ohio except one Michigan trail.

1. Ohio: a record coded for the STATE PARK was added to a wildlife area, nature preserve or state forest (it is still on the state park too). How it says: "name (second name field)". 12 parks:
   - US-7850 Caesar Creek Lake WA <- sgoha26 CaesarCrkSP 6953 ac (park US-1940)
   - US-8114 East Fork WA <- sgoha545 EastForkSP 7076 ac (US-1948)
   - US-8637 Deer Creek WA <- sgoha874 DeerCreekSP 3268 ac (US-1945)
   - US-9499 Salt Fork WA <- sgoha254 SaltForkSP 20716 ac (US-1989)
   - US-9458 Dillon WA <- sgoha935 DillonSP 2901 ac (US-1947)
   - US-9456 Delaware WA <- sgoha54 DelawareSP 2003 ac (US-1946)
   - US-8636 Paint Creek WA <- sgoha222 PaintCrkSP 1966 ac (US-1982)
   - US-9413 Hueston Woods Nature Preserve <- sgoha871 HuestnWdsSP 2373 ac (US-1959)
   - US-9438 Tinkers Creek Nature Preserve <- sgoha463 TnkrsCrkSP 397 ac (US-1997)
   - US-5435 Beaver Creek State Forest <- sgoha736 BeaverCrkSP 2170 ac (US-1935)
   - US-5444 Mohican-Memorial State Forest <- sgoha519 MohicanSP 1084 ac (US-1977)
   - US-5452 Tar Hollow State Forest <- sgoha298 TarHollowSP 213 ac (US-1996)
   The contest correctly removed the old SP-typed records from these parks, then the second-name join put the same SP land back under another id. The park is still outlined with its neighbour's land.
2. US-1977 Mohican State Park: gave up the forest records (right) but gained sgohc520 MOHICAN-MEMORIAL (MhcnMmrlFR) 4632 ac, a forest record. Same bug, other direction.
3. US-9420 Lawrence Woods Nature Preserve: gained sgohb823 (LwrncWdsWA, 160 ac), a wildlife-area record that a person had already joined to US-12057. Now on both.
4. MI US-4239 North Country Trail (6254 activations): the trail line (trl4239) was swapped for NPS record 3529 (code NOCO), only 81 acres. A whole trail cannot be 81 acres; it likely lost its real outline. Person: check the record before keeping.

## UNSURE rows (19)
Maryland
- US-4556 Appalachian Trail (6015): line replaced by NPS record 3518 (APPA, 1565 ac). Probably fine, check it follows the trail in MD.
- US-10781 Calvert Cliffs Natural Area, US-10766 Swallow Falls Natural Area: the SP records correctly went to the state parks, but each natural area now holds only a 0-acre record (sgmdb6, sgmdb34) and still shows "official". Is a 0-acre record a real outline? Probably should show as a pin until a person looks.
Michigan
- US-1522 Milliken State Park (403): mid778 "Milliken State Park and Harbor" 20 ac was held back by rule G-1 (more than 2 km from the pin). The name is exact and the park is 3 other pieces already. Person: look at where mid778 is.
Tennessee
- US-7578 Cheatham Lake WMA and US-3933 Cheatham WMA; US-7581 Cordell Hull Refuge WMA and US-7580 Cordell Hull WMA: the contest split the records well, but a record a person joined ("reviewed") to one park stays on the other park too: sgtnc23 (19769 ac) is still on the 2000-ac Lake WMA; sgtnc687 (20238 ac) still on the 2600-ac refuge; sgtnc308 (2152 ac) still on the big Cheatham WMA. Person: remove from the wrong park. (Better than before, but not finished.)
- US-3960 Reelfoot State Wildlife Area: correctly lost 255640 and 255740. It gained sgtne260 "Reelfoot SNA" 207 ac and 255741 169 ac, and keeps sgtne324 "Reelfoot Lake" 7160 ac (a lake, D4). Person: is an SNA record part of the WMA?
- US-6259 Ozone Falls SNA (pin to official) and US-6270 Stinging Fork Falls SNA: joined only to "Ozone Falls (Cumberland Trail)" 45 ac and "Stinging Fork Falls (Cumberland Trail)" 776 ac by a second name. Person: are these the natural areas or Cumberland Trail segment corridors?
- US-2952 Hiwassee Ocoee: kept tnd84 but sgtnf84 (the same park, same 91 ac) went to check as shared with US-12663. Inconsistent; the park still has an outline. US-12663 Ocoee River SP is RIGHT (it lost records that are not its name).
Ohio
- US-9462 Fallsville South WA: 71724 went to US-9461, but the twin sgohb74 (1785 ac) still sits on both parks.
- Added with a different type word but harmless duplicates of land already held: US-1999 West Branch SP (+WA 1947, 966 ac), US-5641 Jesse Owens SP (+WA 4836 ac), US-1962 Jackson Lake SP (+WA 1 ac), US-5453 Vinton Furnace SF (+WA 3533 ac). Tiny or odd adds: US-1961 Indian Lake SP (+FA 9 ac), US-5443 Maumee SF (+SR 5 ac).

## Patterns (rules that misfire)
1. SECOND NAME FIELD JOIN SKIPS THE CONTEST (Ohio, 15 parks). The "(CaesarCrkSP)" name in brackets in the sgoha/sgohb/sgohc/sgohd layers is a type code; joining by that second name ignores it and does not go through the contest. Fix: run the contest on these joins too, and let the type code (SP, SF, WA, NP, FR) count as the record's own type word.
2. A record a person joined (how = "reviewed") is not treated as owned. It stays on a second park (Lawrence Woods, Cheatham, Cordell Hull, Fallsville). Fix: a reviewed join should win the contest and leave the other park.
3. "Official" with only 0-acre records (Calvert Cliffs NA, Swallow Falls NA): after the contest the grade is not lowered. Fix: a park with no record over ~1 acre should be a pin until a person looks.
4. NPS unit-code join on trails (AT, North Country) swaps a trail line for an NPS polygon, which may be a fragment. Fix: keep the line and add the NPS record beside it, or compare the acres to the line length.
5. G-1 (far from the pin) dropped an exact-name Milliken piece. Worth a look at how it measures distance for city parks.
6. Small thing: bare "PIKE" 11270 ac is called shared between Pike Lake SP and Pike SF; it is only the forest. Harmless (the typed records stay).

## Not a worry
Bare names left to a person (the "e" layer) never cost a park its outline, because the typed SP/SF/WA records stayed. The activation-heavy changes (Caesar Creek, Delaware, Hueston Woods, Deer Creek, East Fork, Beaver Creek) are RIGHT for the SP side; only the wildlife-area or forest side that got the SP record is WRONG.
