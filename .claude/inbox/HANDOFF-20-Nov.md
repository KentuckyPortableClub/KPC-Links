# KPC map keys: hand-off of every open issue and the plan (20 Nov 2026, 7:00 AM Central)

From Fable (the reviewer chat) to the owner's outside agent. The owner is Brandon White, KZ4CP. He works from a phone and wants short, plain answers.

Each fact below is marked **[read]** (Fable looked at it in the repo today) or **[notes]** (taken from another chat's report, not re-checked). Treat **[notes]** as unconfirmed. Several things said from notes this week were wrong; section 8 lists them.

## 1. The owner's standing orders (do not break these)

1. **No building.** No key build (US, Canada, world, Kentucky), no outline rebuild, no Release, no 2-fer run, until he says GO. Reading, comparing saved files, tests and draft pull requests are fine.
2. **Only these bots run** (20 Nov 6:34 AM): social posts, bots that feed the website, bots that collect data for the map. Everything else is switched off.
3. **One master copy.** Only the keeper (private repo KPC-Store) fetches from agency servers. The key builder reads saved copies only. Never plan a key-side download.
4. **Look before you build.** Before writing a new bot, check or switch, read the code map and say what already exists. Fix or switch on what is there.
5. **Done needs proof** he could check: a commit on main, a number in a named file. "Pushed", "built" and "tests pass" are not proof. A switch that is OFF is not done.
6. **Say what a test ran on.** Most tests here use invented parks. Only a check on real saved park data says anything about the map.
7. **Usage is short.** One owner per job. Do not rerun what another chat already ran; read its result.
8. **Privacy.** Never name a held or withheld park, or a park from the graded sample, in a public file. Sample and gold answers live only in KPC-Store.

His full rules: `.claude/CLAUDE.md` in KPC-Links.

## 2. Where things are

| What | Where |
|---|---|
| The live to-do list, with proof on each line | KPC-Links (public), `.claude/inbox/REPAIRS.md` |
| Promises to the owner | KPC-Links, `.claude/inbox/LEDGER.md` |
| The code map (what every bot is) | KPC-Store (private), `docs/code-map/`. Last updated 15 to 17 Nov, so it is behind |
| Bot reports and lists | KPC-Data, branch `tools-out`, folder `key-quality/2026-11-19/` |
| The keys | KPC-Links, `data/us-key/US-XX.json` |
| Switches for the key builder | KPC-Links, `.github/key-switches.json` |

## 3. Where it stands today

**The stop**
- All four key builders start by hand only: no timer left in `kpc-us-key.yml`, `kpc-ca-key.yml`, `kpc-world-key.yml`, `kpc-ky-key.yml` (commit 0b58c44a). **[read]**
- A Canada key build ran after the stop, 20 Nov 5:45 AM (commit 3c7362fa, 23 files in `data/ca-key`). It is left in place. Nothing public changed. **[read]**
- No Canada or world run was queued at 6:15 AM; KPC-Data has no timer that runs a 2-fer build. **[notes, from you]**

**Merged on main**
- 2-fer rules: #289, #290, #292. Release guards: #302, #303. Quiet runs and the layers report: #294, #300. Fact check: #298, #299. Key builder: #295, #297. **[read]**
- Rules fingerprints on main: US `7e4883bfbb45`, Canada `dfef94b3dfd3`, world `b1f23bf0deea`, 2-fers `6a9d67ea4100`. **[read]**
- #296 is a parked draft, on purpose. By its own count it would change no park.
- Store draft #25 (the push check) and a follow-up test are in KPC-Store (a4b6f8d). **[notes; Fable read the commit title only]**

**The numbers we have on real parks**
- Sample of 300 random parks, graded blind on 19 Nov: 71% right, 8% only part of the park, 5.0% hold a record that is not the park, 14% cannot be told. **[read]**
- A size rule tested on that sample: it catches 7 of 24 wrong parks and wrongly flags 9 right ones. **[read]**
- Where the wrong records come from: 20 of 29 were joined by name; a few small state layers are wrong most of the time. **[read]**
- Montana information run: 254 parks read; it confirms 16 of the 81 parks settled by hand and contradicts none. **[notes]**
- Official sizes collected by the acreage bot: 1,788 parks. **[notes]**

**The public map**
- Frozen on the 11 Nov release. Four map tools show "Down for maintenance". **[read]**
- With the new guard, a Release would refuse 29 states on the working files and 48 of 50 on the public files. **[read]**

## 4. The issues, most important first

**A. Matching by name, checked against itself.** Parks are joined to land records mostly by name. The checks meant to confirm a join read the same record the name came from, so they agree by construction. Result: about 1 park in 20 holds land that is not the park.

**B. The size check exists and would do nothing if switched on.** Built 2 Nov (`_selfchk` in `kpc_us_key.py`, `self_checks` in `kpc_key_rules.py`). Three faults **[read]**:
1. It reads official sizes from `data/acres.json`, which does not exist. The 1,788 sizes are elsewhere (KPC-Data `tools-out`, `acres/acres.json`).
2. The switch file can only set it to report. The word "hold" cannot be reached from the switch file, and `setting()` is called without the state.
3. It adds up every joined row, so land held from two layers counts twice.

**C. Boundary lines joined as park land.** Some layers are legal or outer boundaries, not land an agency owns. The sample found them wrong most of the time (ids `sgmnb`, `mid`, `sggaa`, `sgiac`). New York's `sgnyc` is the Adirondack Blue Line and is the same kind of thing. The owner's own rule says a park is agency-owned land, never a proclamation line.

**D. One public outline in three was never built from the key.** 3,862 public outlines were made by a second, looser matcher (pin inside the shape and the names agree). Only the one build replaces them. The guard refuses them meanwhile. **[read]**

**E. The store is not connected to anything.** **[read in the store's code, plus Opus's count]**
- The store holds each park's own matched records, not whole layers. It cannot refill the key builder's layer copies.
- A job already publishes the clean part to a public shelf (`public-shelf` in `kpc-store-keeper.yml`, release `store-shelf` on KPC-Data). The key builder never reads that shelf.
- The map hook is merged and off. The 2-fer bot from the store is built and never run.

**F. The layer gap is small.** After the report fix: 96 rows open, 34 states the gate would hold. The rows that can be counted cover 28 parks (25 without the Blue Line), and their shapes are already saved, so no download is needed. The other 65 rows cannot be counted; at most 1,097 no-outline parks live in those states. **[notes; Fable reviewed the report fix and it passes]**

**G. The stop leaked.** Only the US timers were turned off on 19 Nov, and the watchdog restarts any timer it finds. Fixed for keys. Two side doors to a 2-fer run remain: the hourly key copy tries to start `kpc-fers-chain.yml` (off in GitHub), and the 2-fer gate in KPC-Data's watchdog and Sunday audit can start `kpc-fers-line.yml`. **[notes, from you]**

**H. The information bot speaks for 1 park in 5.** For the rest it lands on list pages and menus, not the park's own page.

**I. How work was done.** The pattern behind the wasted months:
- Fixes built, tested and left switched off.
- Tests on invented parks only.
- The main test gate is red, and its known-failures list is from 7 Nov.
- Each chat starts with no memory and built copies of what existed.
- Notes repeated without being checked.
- The code map is private and out of date, so most helpers cannot read it.

**J. Saved answers.** A "no" does not follow a renumbered record. 15 parks hold one record as both yes and no. 472 are saved by name only. At least 64 saved answers fit two records. 70 records are held by an answer in one park and by name in another with no winner.

**K. 2-fers.** The 2,379 public rows are old and unstamped. Nothing has been rerun with the new rules.

**L. Cost.** 83 bots run on a timer (39 in KPC-Links, 43 in KPC-Data, the keeper).

## 5. The plan

One owner per step. Nothing gets added in between without the owner.

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | GitHub-side clean-up (section 6) | You | Each item reported done |
| 2 | Fix the three faults in the size check (B). The owner has ruled: on, and hold parks that fail. A park with no official size is not held | One fresh Fable chat writes; Opus reads | A draft pull request with the list of parks it would hold, and two numbers from the real sample: wrong parks caught, right parks held |
| 3 | A rule for boundary-line layers (C), tested on the sample before it is built | Fable writes the rule sheet; the owner rules | Catch and false alarms counted on the sample; then a draft pull request |
| 4 | Fill the 25 parks from shapes already saved. No download | Opus | The layers report shows those rows closed |
| 5 | Plain wrong cases fixed by a saved "no" with evidence: Nevada US-2635, the 8 rows and 12 disagreements listed in #296 | A grading agent | On main, each with who, source and date |
| 6 | One list per switch that goes on at the build: size check, leased land (D5), the piece rule, hold-on-error, saved-answers-say | ONE agent, from saved files | One file per switch naming the parks that change |
| 7 | The owner approves the saved copies as they are for the states the layers gate still holds | The owner | His word, recorded |
| 8 | The one build, every passed switch on, outlines rebuilt from the key | Opus, on the owner's GO | The parks that change are exactly the lists of step 6 |
| 9 | A fresh sample of 300, graded blind, same method | One grading agent | New numbers beside 71% / 5.0% / 14% |
| 10 | Better = release state by state through the guard. Not better = stop, no more patches | The owner presses the button | — |

**Not before step 9 is read:** connecting the store (E), a page finder for the information bot (H), the saved-answer faults (J), any 2-fer run (K), the world, the repo history restart.

## 6. What only you can do (GitHub side)

Fable cannot see the runs list or the Actions page, and cannot open or close pull requests. Opus's connection is refused (403) for the same.

1. Switch off in the Actions page the 17 bots marked STOP in `KPC-bots-keep-or-stop-20-Nov.csv` (also listed in REPAIRS under "Bots: keep or stop"), after the owner's yes. Change no file.
2. Switch off `kpc-fers-line.yml` in KPC-Data.
3. Close #297 and #299 as landed (their code is on main).
4. Open a pull request for branch `prep/nov20-ready-builder-ids` (4f42412a4) and merge it. Fable has read it and it passes. No rule file.
5. Read the repo variable `KPC_KEY_SOURCE`. It must be `store`. Nobody has confirmed it.
6. Check whether the keeper's timer and its `public-shelf` job are really running, and whether the secret it needs is set.
7. Keep doing what found the Canada build: check claims against the repos and say when a line in REPAIRS is wrong.

**Remember when the stop is lifted:** `kpc-fers-chain.yml`, `kpc-fers-line.yml` and every bot you switch off are GitHub switches, not in any file. They come back only by hand, on the owner's word.

## 7. Waiting on the owner

- Yes or no on the 17 bots, and two calls: the nightly park-info engine in KPC-Data (it reads agency layers itself, against the one-fetcher design) and the Europe weather warnings.
- The Army Corps layer needs its licence terms read before the store will publish it (6 parks).
- The 2,379 old public 2-fer rows: pull them now, or leave them until a fresh run?
- Whether to roll back this morning's Canada build. Fable's advice: leave it.
- Whether the code map may be copied into the public repo so every helper can read it, with or without its page about the store.
- Whether chats may install packages (a network setting). Without it they cannot run the full test gate.

## 8. Things said this week that were wrong (so they do not spread)

| Said | True |
|---|---|
| "The keeper already holds the two missing layers" | It holds only records matched to parks. The owner's Park Service download (108 MB) is the only whole copy of that layer anyone has. Keep it |
| "The key bots should be allowed to fetch the changed layers" | No. Only the keeper fetches |
| "The measured-acres switch is off" | It has been on in all 50 states since 17 Nov |
| "122 layer rows are open" | 96, once layers are counted by the builder's own ids |
| "The builder's copies are old" | No evidence of that. They are short or missing in places |
| "No bot moves the store's records out" | The public-shelf job does. The key builder just does not read the shelf |
| "A size check will fix the key" | It catches about a third of the wrong parks |

## 9. Do not

- Do not start any build, Release or 2-fer run, or turn any timer or switch back on.
- Do not write a new measuring routine, size check or matcher. Five size tools already existed when two more were drafted.
- Do not report a count you did not read yourself without saying so.
- Do not ask the owner to download a layer by hand.
