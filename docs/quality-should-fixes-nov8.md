# Quality should-fixes, Nov 8 regrade (US-42504172086 KEY YES; W-42509770852 CL/AX/CH YES)

1. **5 km new-join hold (fixed in this PR).** kpc_join_check.py now drops only the NEW far ids (they go back to 'c', with a held row)
   when the park still has its earlier joins. A join that is all new over 5 km, or anything over 15 km, still pins the whole park.
   This restores US-13132 Seven Mile, US-13134 Rock Creek, US-13138 Wassuk, US-4868 Annett SF and US-4886 Connecticut Lakes SF
   on the next US build. kpc_join_check.py is NOT a rules file, so the hashes are unchanged.
2. **sgnvh1238 "Mount Irish": for Brandon (not decided here).** It is joined to BOTH US-9268 Mount Irish Wilderness and US-13178
   Mt. Irish Archaeological Reserve. The US-13178 override (an automated BOT A commit, Nov 8) has no decided_by. A person picks which park the record is.
   If it is the Archaeological Reserve, US-9268 needs 'no' on sgnvh1238; if it is the Wilderness, the US-13178 override needs a decided_by NO.
3. **CL-0012 Paposo Norte Natural Monument: for a person.** The world key joins record 3000 "Paposo Norte" (MMA SIMBIO and
   Áreas Protegidas, the same id in both) with bk 23.83 km, far = "well outside", shadow check "pin 24 km away". It is not held,
   most likely because the join check measured a nearer saved part. Verify on the map that the monument is within 15 km
   of the pin, or hold it (overrides 'no' or a pin). Not changed here.
4. **AX: 9 Natura 2000 parks joined to same-name "naturreservat" records** (AX-0004, 0007, 0008, 0010, 0012 [naturskyddsområde], 0013,
   0014, 0016, 0019; all 0-0.17 km). Rule 18 (kpc_key_rules.py) covers a park that names a PIECE of a bigger area. "Natura 2000"
   and "naturreservat" are designation words, not piece names, so as written Rule 18 does not catch these. Open question for
   Brandon: does a Natura 2000 site count as the same land as the reserve of the same name? The boundaries can differ. Not changed here.
5. **World index.json failed / complete fields.** The CL/AX/CH hand run wrote index.json without 'failed' / 'complete'. The full world
   run 42513036075 (ETA 3:35 PM CST) rewrites them. Check after that run; no code change unless they are still missing.
