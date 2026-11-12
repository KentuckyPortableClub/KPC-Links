# Open questions for the KPC owner (Nov 11, 2026, 8:35 PM CT)

## Answers recorded

Brandon accepted all 10 recommendations in chat on Wednesday, Nov 11, 2026, at about 9:16 PM CT (America/Chicago), with the widget choice **Yes, go with your answers**. The accepted recommendations, verbatim, are filed at `OWNER-ANSWERS-nov11.md` in this folder. Citation form used in the ledger: `owner chat 2026-11-11 21:16 CT, OWNER-ANSWERS-nov11.md item N`.

| Item | Question | Status | Citation |
|---|---|---|---|
| 1 | 101 Ranch (US-11820) and Saline Courthouse (US-12735) | Answered: keep both held | item 1 |
| 2 | Vallée du Cousin / FR-14979 (keep the live join, or apply the staged no?) | Answered: take it off the live key (apply the staged no) | item 2 |
| 3 | Who saves the outlines read live tonight? | Answered: the layer intake bot saves them from the allowed hosts | item 3 |
| 4 | CA/TX Park Service wiring (keep or drop)? Add Chavez (CECH, US-0915)? | Answered: keep the wiring (saved copies only); add Chavez | item 4 |
| 5 | KPC-Data trail patch (apply or not)? | Answered: apply the 21 parks, hold the weak Utah rows. Covers the nine by-text rewrites in KPC-Data #70; the 11 UT UGRC rows stay held | item 5 |
| 6 | Names that differ (US-10184, US-10195, US-7374, US-13474) | Answered: yes to the two Wisconsin renames and to Wysong (fee record 135 only); hold Kyle Ranch | item 6 |
| 7 | Parks the jobs left off (Palmito US-10274, Manhattan, 39 wild rivers) | Answered: Palmito and Manhattan stay off; the 39 wild rivers later as a separate corridor job | item 7 |
| 8 | Three more French layers? | Answered: yes, in the hash-bump batch at the end | item 8 |
| 9 | Oversized overrides.json | Answered: split it in a small PR first | item 9 |
| 10 | Smaller checks (56 Nov 5 confirms; ZA-0085/0156/0157; job 4 person checks) | Answered: count the 56 Nov 5 matches as settled; ZA-0085/0156/0157 go back to unsolved; job 4 person checks stay held | item 10 |

The original questions below are kept for the record. Each is marked Answered at its heading.

---

## 1. Miller Brothers 101 Ranch (US-11820) and Saline Courthouse (US-12735) — owner YES needed

**Answered** (OWNER-ANSWERS-nov11.md item 1, owner chat 2026-11-11 21:16 CT): keep both held. A historic-register outline is not the park. They stay pending on the ledger.

- Both are on the Nov 9 hold list (`needs-another-look.json`) as agency-alias holds that need an owner YES.
- New evidence from Nov 11: each has a National Register of Historic Places listing outline (Park Service layer) and the POTA pin is inside it.
- Neither is what POTA calls it. Saline Courthouse is run by the Cherokee Nation. The 101 Ranch record is a National Register site, and the only state record found was a highway marker.
- A National Register listing outline is official evidence of the site's extent. It is not automatically the park boundary.

**The question:** is that a YES to join each park on its National Register outline, or do they stay held?

**Handled for now:** held. No join is written into the live key for either park.

## 2. Vallée du Cousin aval (FR-14979) — 13 km from the pin

**Answered** (OWNER-ANSWERS-nov11.md item 2, owner chat 2026-11-11 21:16 CT): take it off the live key until someone explains the pin. Apply the staged no (`znieff2.828`).

- The official French zone matches by exact name: ZNIEFF type 2, id 260014888, "Vallée du Cousin aval, Romanée et leurs abords", 8,863 ha.
- It lies 13.1 km from the POTA pin (13.24 km in the current key).
- It may be a long river-valley zone that simply does not reach the pin, or the pin may be wrong. That was not settled.

**The question:** join it anyway if the geometry is clearly the named valley, or leave it off until the pin is explained?

**Handled for now:** not joined. It is reported with the distance and the reason.

## 3. Outlines read live in the browser on Nov 11 — who saves them?

**Answered** (OWNER-ANSWERS-nov11.md item 3, owner chat 2026-11-11 21:16 CT): the layer intake bot saves them from the allowed hosts.

These official outlines were read live through the owner's browser on Nov 11. They are probably not saved in either repo, so a join that depends on one can only be staged, not applied.

| Parks | Source (host) |
|---|---|
| US-10184 Johnson, US-10195 Sette | Wisconsin DNR managed lands (dnrmaps.wi.gov) |
| US-7374 Wysong | Southwest Florida Water Management District lands (www25.swfwmd.state.fl.us) |
| The nine French parks | IGN Géoplateforme, PatriNat layers (data.geopf.fr) |
| RO-0880 Pădurea Homița | EEA Natura 2000 (bio.discomap.eea.europa.eu) |
| US-13474, US-11820, US-12735, US-10274 | NPS National Register locations (mapservices.nps.gov) |

None of these hosts is on the never-contact list.

**The question:** will the owner hand-download them, or should the box save them from these allowed hosts?

**Handled for now:** nothing was fetched. Each affected join is staged outside the live key and listed as a hand-download item with host, layer and record id.

---

# Added after the three jobs came back (Nov 11, 2026, about 9:40 PM CT)

Updates to the three questions above:
- **Question 1 (101 Ranch, Saline Courthouse):** Answered, item 1: keep both held. Job 1 keeps both on the owner list with their holds; job 2 staged held entries (National Register records 386945 and 379303) and lifted nothing.
- **Question 2 (FR-14979):** Answered, item 2: take it off the live key (apply the staged no for znieff2.828). New fact from the jobs: the live world key already joined this park to the 13 km zone; the staged no is what the owner accepted.
- **Question 3 (who saves the live-read outlines):** narrower than first thought. Eight of the nine French parks and the Romanian park are already joined in the live world key from saved copies. The outlines still not saved are listed in `job2/hand-downloads.csv`.

## 4. Job 2, commit 2 — wire the NPS boundary layer for California and Texas (keep or drop)

**Answered** (OWNER-ANSWERS-nov11.md item 4, owner chat 2026-11-11 21:16 CT): keep the CA/TX wiring, since it uses saved copies only. Add Cesar E. Chavez (CECH, US-0915) to the California row.
- Rosie the Riveter (US-0754) and Blackwell School (US-11900) have signed Nov 9 overrides that never took effect, because `data/state-gis.json` lists the NPS boundary layer for ten other states only.
- Commit 2 adds one California row and one Texas row. It moves no rules hash and joins nothing by itself.
- The rows carry the layer's address on `services1.arcgis.com`, a never-contact host. The same row already exists for the ten other states and is treated as saved-copy only; the existing net-guard test passes. It is flagged here because it adds two more mentions of that host.
- After it, the owner packs two hand files from the copy already in KPC-Data and runs the CA and TX keys.
- Should Cesar E. Chavez (CECH, US-0915) be added to the California row at the same time?

## 5. Job 4 — the KPC-Data trail patch (apply or not)

**Answered** (OWNER-ANSWERS-nov11.md item 5, owner chat 2026-11-11 21:16 CT): apply the 21 parks, but hold the weak Utah rows. That covers the nine by-text rewrites in KPC-Data #70; the 11 UT UGRC rows stay held.
- 21 trail parks pass every test but can only go official through KPC-Data's trail index. The proposed patch is in `job4/data-proposal/`.
- It rewrites the source text on 20 rows so the text names the agency in words the official-line gate recognises. Each new text names the same source the row already cited. Because the wording is what opens the gate, confirm each source is that agency's own line first. The Utah rows are the weakest: a state clearinghouse trails layer for BLM trailheads.
- It also sends Canadian trail lines to the index the Canada key reads (fixes CA-5506).

## 6. Names that differ — YES or NO needed before these can be applied

**Answered** (OWNER-ANSWERS-nov11.md item 6, owner chat 2026-11-11 21:16 CT): yes to the two Wisconsin renames (US-10184, US-10195) and to Wysong (fee record 135 only, US-7374). Hold Kyle Ranch (US-13474).
- US-10184 Johnson = "Deer Park SHA-WPRA"; US-10195 Sette = "New Richmond SHA-WPRA" (Wisconsin DNR renames; records are in the saved copy).
- US-7374 Wysong Park = "Wysong Lock And Dam" (fee record 135 only; record 136 is an easement).
- US-13474 Kyle Ranch = National Register record 378910 (listing boundary not yet confirmed as the park).

## 7. Parks the jobs left off — is that right?

**Answered** (OWNER-ANSWERS-nov11.md item 7, owner chat 2026-11-11 21:16 CT): that is right (Palmito US-10274 and Manhattan stay off). The 39 wild rivers later as a separate corridor job.
- **US-10274 Palmito Ranch Battlefield:** the National Register record is the whole 6,908-acre battlefield, which is the bigger place, so it was not joined. This reverses the Nov 11 answer, which called it a match. It needs the Texas Historical Commission's own site outline.
- **US-4376 Manhattan Project:** no saved copy holds any of its three units. The New Mexico and Washington pieces cannot be reached by an override at all without a code change that moves the US rules hash.
- **39 wild and scenic rivers:** a saved line cannot make them official under the club's own rule (the corridor is the park). Do them as corridor-outline joins in a separate job?

## 8. Should the world key read three more French layers?

**Answered** (OWNER-ANSWERS-nov11.md item 8, owner chat 2026-11-11 21:16 CT): yes, in the hash-bump batch at the end.
Marine zones, Conservatoire du littoral sites and reserve protection perimeters. FR-10548 cannot be joined without the first; FR-10432 and FR-11106 stay "approximate" without the other two. Adding them moves the world rules hash.

## 9. Repo problems found on main (not caused by these jobs)

**Answered** for the oversized overrides file (OWNER-ANSWERS-nov11.md item 9, owner chat 2026-11-11 21:16 CT): split it in a small PR first.
- `data/us-key/overrides.json` is 1,527,615 bytes, over the 1 MB cap. Nobody can add an override without breaking the rule until it is split. This is why job 2 staged its entries in a separate file.
- `data/research-inbox/needs-another-look.json` is about 2.5 MB, also over the cap, and it and the Nov 9 world batch files still hold WDPA data. Job 1's test caps them so they cannot grow but did not rewrite them.
- Two tests fail on untouched main: `test_maprep_state_search_fast_nov8.py` and `test_tracts_nov7.py`.

## 10. Smaller person checks

**Answered** (OWNER-ANSWERS-nov11.md item 10, owner chat 2026-11-11 21:16 CT): count the 56 Nov 5 owner-to-confirm matches as settled. ZA-0085, ZA-0156 and ZA-0157 go back to unsolved. Job 4 person checks stay held.
- From job 1: count the 56 Nov 5 "owner to confirm" matches as settled? Three South African parks (ZA-0085, ZA-0156, ZA-0157) lost their WDPA-derived ids and are unsolved again.
- From job 4: US-9163 (is the Lake Saracen walking loop the park?), US-5818, US-11745 / US-6020 (one shared line), US-5901 (Nov 9 point decision), the name-mismatch holds on US-10714, US-10884, US-10929 (their lines pass the pin test), and CA-5993 (saved line is in Toronto, 131 km away).
