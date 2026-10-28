# Southeast Source Book: SUMMARY (chat 8 desk, Oct 27 2026)
Nine state files in this folder (KPC_SE_<ST>_desk.md). Read only; I changed no data. Evidence: A = I opened the page, B = search result only, C = inference. I could not query polygons, so every "covers" is from the publisher's own description. Names are not matched yet: some "unjoined" parks may just be name mismatches that chat 2 can fix with a fuzzy match.

## State by state
| State | Parks / no outline | Verdict | Main reason |
|---|---|---|---|
| TN | 277 / 25 | READY (small gaps) | state parks, natural areas, TWRA, forests all read; tnmap TWRA layer 3 has an OWNERSHIP field not yet used; two parks too new (US-13364, US-13567) |
| NC | 253 / 34 | GAPS | key has only Managed Areas + game lands; no state park, forest or trail layer; game lands are partly by agreement |
| VA | 184 / 29 | READY after one add | DWR WMA boundaries (with Owner field) not in key; the 29 are mostly trails |
| WV | 172 / 12 | READY | add WVSRA_RailTrails; hatcheries are pin-only |
| GA | 237 / 17 | READY | good Land Access ownership chart; Corps/USFS WMAs everywhere |
| AL | 155 / 29 | GAPS | 10+ TVA-managed parks have no layer; no forests or trails |
| SC | 167 / 8 | READY | two new state parks to wait for |
| FL | 460 / 20 | GAPS (one cluster) | SFWMD / SWFWMD / NWFWMD conservation sites (about 15 parks) |
| MS | 155 / 66 | GAPS (biggest) | no state layer in key at all; MARIS has them, all unread |

## Top 10 layers chat 2 should add before the run
1. **MS WMAs** – MARIS …/Vector/WildL_Areas (66 → about 10 left)
2. **MS State Parks** – …/Vector/State_Parks
3. **MS national forest OWNERSHIP** – …/Vector/NatFor_OwnerBnd (not proclamation)
4. **VA WMAs** – services.dwr.virginia.gov HUB_Layers/DWR_WMA_Boundaries/FeatureServer/0 (Owner field)
5. **TN TWRA Lands** – tnmap …/TWRA/MapServer/3 (OWNERSHIP + OWNCODE for rule 14)
6. **FL FWC WMAs** – gis.myfwc.com …/Wildlife_Management_Areas_Florida/MapServer/1
7. **WV protected lands** (cross-check) + **WVSRA_RailTrails** for trails
8. **NC Managed Areas OWNER_TYPE** – already read, but start using Owner/Category for rule 14; plus NCWRC GLtrails_roads
9. **FL SFWMD + SWFWMD + NWFWMD conservation lands** (find live URLs; the SWFWMD server was down)
10. **TVA reservoir/public land boundaries** (AL, NC, TN): not found; find TVA's own layer

## Fix before the run (not new layers)
- Name matching: TN natural areas (7 SNAs), TN WMAs, GA Okefenokee SP, SC/AL WMAs look "unjoined" though their layers are in the key.
- US-8313 Mountains to Sea State Trail is NC but the pack listed it under TN. Check the join by state.

## Grey areas for Brandon to rule on
| # | Question | My lean |
|---|---|---|
| SE-1 | WMAs run by a state on **TVA / Corps / national forest** land (AL, TN, GA, VA, MS, NC) – the land is federal. Does the WMA count as its own park, a 2-fer with the federal park, or "same land, two park numbers"? | Follow rule 14: federal owner + both listed = "same land, two park numbers". |
| SE-2 | **NC game lands on Duke / timber land by agreement.** Park land? | Not park land except its own POTA number (your private-by-agreement ruling). |
| SE-3 | **MS 16th Section** (school-trust land leased to the state). | Treat as by-agreement; ask. |
| SE-4 | **Georgia Power / timber-lease WMAs** (Oconee, Rum Creek, Little Satilla…). | Same as SE-2. |
| SE-5 | **State parks that are leased TVA/Corps land** (Joe Wheeler, Lake Guntersville…). | Count as park, but NOT as a 2-fer with the owner agency's own park. |
| SE-6 | **Water management district "conservation area" sites** (FL, 15 numbers). Parks or not? Many are stormwater areas. | Include only if public and open (rule 3); else NOT SURE list. |
| SE-7 | **National Heritage Areas** (GA US-7139, US-7893), Wild & Scenic corridors (Chattooga, Wekiva), Frontier Culture Museum. | No boundary rule: pin only. |
| SE-8 | **Hatcheries** (WV five, NC): pin only? | Pin only. |

## What is solid, what is not
Solid (A): TN TWRA Lands fields, TN natural areas service, WV protected lands + rail trails, VA DWR WMA fields, NC Managed Areas fields and owner types, MS metadata for WMAs and state parks, GA Land Access ownership chart, FL FWC WMA service, MARIS REST paths.
Not solid: most 2-fer predictions (B/C), anything about agency ownership beyond the GA chart, TVA data, SC folders (I did not open the SCDNR server folders), the NC state parks layer (not found), and the VA "publicly accessible" layer (needed a token when I opened it).
