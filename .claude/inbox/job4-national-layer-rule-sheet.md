# Rule sheet: national-layer records joined by name (job 4), 20 Nov 2026, about 7:25 AM Central
For the owner to rule on. Nothing is built. Real cases below have their names removed.

## What I read first, and why it isn't enough
- **Kind test.** `kpc_us_key.kinds()` and `same_kind()` (the `KINDS` table) put "recreation area" in the **state park** kind (`'sp': ... recreation(al)? area`). So a Forest Service *National* Recreation Area passes as the same kind as a *State Park*. The national record keeps `_k: ['sp']` in the saved copy. D3's `_is_it()` uses the same kinds, so the designation split lets it through as well.
- **Agency test.** `kpc_key_rules.agency_pick()` (`KPC_AGENCY_TIE`) only breaks a tie *between two parks* that share one record. It never asks whether one national record's manager fits the one park it joined. A state park that takes a federal record alone is never tested.
- **Size.** `kpc_key_rules.size_pick()` already says when a record is a copy (within 10%) of land the park already holds. Job 1, the size check, owns everything else about acres. This sheet doesn't add a size rule.

## The rule (proposed)
**What counts.** A record from a national layer (PAD-US, or the federal FWS / BLM / Forest Service / NPS-type layers) joined to a park by **name alone** counts when the record's manager level matches the park's level. For example, a park named "State ..." takes a record whose `Mang_Type` is `STAT`, and a park named "National ...", "NWR", "BLM ..." or "Federal ..." takes a `FED` record.

**What doesn't count.** The levels disagree. Examples: a state park with a `FED` record (Corps `REC`, Forest Service `FSOD`, BLM `RST` / `RMA`, Reclamation), or a national refuge with a state `SCA`. That record goes to **check**, with the reason "the record's manager is a different level of government from the park". A person's saved yes still stands.

**When unsure.**
- If the park's name names no level ("... Wildlife Area", "... Lake"), the rule says nothing and today's rules decide.
- If the name has both a state word and a national or federal word, the state word decides.
- If the other-level record is a copy (within 10%, `size_pick`) of land the park already holds, it **counts**. That's the state park on Corps-leased land, where the Corps and the state both draw the same ground.
- If it isn't a copy, it goes to check, never to a guess.

## Real cases (names removed), from the saved keys on main, 20 Nov
1. A state park whose own state and PAD-US records are 539 acres also took a **321,709-acre Forest Service National Recreation Area** by name. The kind test calls both "sp". Under the rule it goes to check. (This is the Nevada case in job 5.)
2. A Missouri state park took a **165,658-acre Corps `REC`** record by name. The levels differ and it isn't a copy, so it goes to check.
3. An Alaska national wildlife refuge took an **85,681-acre state DNR special-use area (`SCA`)**. The levels differ, so it goes to check.
4. A California state recreation area took a **70,258-acre Reclamation `REC`** record. It goes to check.
5. An Idaho state fishing lake took a **41,391-acre BLM recreation (`RST`)** record. It goes to check.
6. A Colorado state park on Corps land took a 7,079-acre Corps `REC` record beside its own 5,831-acre state record. That isn't within 10%, so it goes to check. A person can say yes with the lease page.
7. An Idaho state fishing lake took a BLM `RST` record of 31,737 acres beside its own record of the same 31,737 acres. That's a copy (`size_pick`), so it **counts**.

## Numbers
- **Real keys today (all US keys on main; not graded, so not right or wrong):** 23,555 joined national-layer records on 9,819 parks. 20,125 of them were joined by name alone. The level test flags **160 records on 129 parks**. Of those, `size_pick` keeps 51 as copies, so **109 records on 96 parks would go to check**. Fable's count of 25,612 records on 10,353 parks is a different cut (I didn't reproduce it). My count reads `m` on `data/us-key/US-XX.json`, using PAD-US plus the 13 federal layer prefixes (`wld`, `hma`, `hab`, `rma`, `rst`, `wsrc`, `fwsr`, `fsod`, `nca`, `wsa`, `wbl`, `fws`, `trl`). "Name alone" means a `name` or `words` join, not a reviewed, alias, trail-line or unit-code join.
- **On the 300-park sample:** the two numbers (wrong records caught, and right records taken away) are for Fable to run. The check takes a sample answers path and prints only those counts. No sample park is named here.
- **What the level test can't catch:** a wrong record with the same level as the park (for example, a state WMA record on a state fishing lake; see job 5's Georgia and Tennessee rows). Those need the size check (job 1) or a saved "no".

## The check
Read-only: `.github/scripts/kpc_national_level_check.py`. It does not change the builder or any rules file, so no rules hash moves.

```
python3 .github/scripts/kpc_national_level_check.py --keys data/us-key --cache cache/us
python3 .github/scripts/kpc_national_level_check.py --keys data/us-key --cache cache/us --answers PATH
```

`--answers` is a CSV, a folder, or a zip. The printed sample line is only counts: wrong records caught, and right records taken away.

Per-park detail stays box only: `national-layer-level-mismatch-nov20.csv` (160 rows). It is not in this branch.
