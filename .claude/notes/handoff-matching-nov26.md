# Handoff: key builder, 26 Nov 2026 (NEWEST; the new PC takes over)

Owner (Brandon, 26 Nov 1:41 AM): "new pc is taking over tomorrow". The new PC's folder is `C:\KPC_Map_Builder_Program`. The old chat was tied to the old PC (D:\KPC GITHUB TOOL and MOre), so a new chat starts on the new PC.

## Who does what
- This chat is the **BUILDER**, not the grader. The owner said twice: "your the builder not the grader". For every grader handoff, give the owner a **zip**: FOR-THE-GRADER.md, the patches and the tests. The grader grades; the owner merges.
- **PC first, PR last** (agreed 25 Nov): a fix goes to the PC as a kit update and the owner tests it; one PR per batch that passed.
- Never ask the owner about a rules hash, a hold or a park (rule of 25 Nov 12:07 + 12:09 PM). No builds, dispatch, Release or keeper runs. Python 3.12 for the touched tests.
- Judge tests against the owner's **earlier PC tests**, never the website ("THE WEBSITE IS NOT GREAT THATS WHY WE ARE REBUILDING").
- **Don't write on a PC unless the owner says go.** The 26 Nov 1:10 AM rule was "dont save anything" while he copies files; GitHub is fine.

## Where things stand
- **#381 (batch 16) merged** into main as 56aff3bd: US daf204f039f0, CA d0352dfc270b. It passed the owner's START-HERE MN NY on kit 25x (old PC, reports\test-2026-11-25-2245).
  - MN: 313 of 323 parks outlined, check rows 391.
  - NY: 820 of 851 outlined, check rows 211.
  - Pin only: MN 3, NY 14.
- **Open draft PRs, stacked, each waiting for the grader:**
  - **#382** batch 17, base main. US -> 3b4a7d2fa8fb. Thin shapes are can't-tell (Old Croton), twin PAD-US copies are one land (Wertheim), same-ground records count once (Helen McNitt). Tool-only commits: each PC test keeps its keys and writes CHANGES-<area>.txt; kpc_padus_gdb.py (stays out of the kit until it has run once).
  - **#383** batch 18, base #382. US -> 2b181efdb282. MN DNR's own ids for state forests and parks; publish_keys clash fix (Florida sgflf had repeated keys); id file format 14. 26 more agency-id layers wait in AGENCY_ID_LATER until their state builds from the fresh store.
  - **#384** speed, base #383. US -> 5b6caa7b7e90. Same answers, much faster (MN PAD-US 300 records: 148 s -> 9 s). Rings filed by box, and grid points worked out once.
- **No kit holds #382–#384 yet.** The next kit (25y or 26a) should hold all three for the owner's test on the new PC.

## First jobs on the new PC
1. **Check what he copied** into C:\KPC_Map_Builder_Program against the old PC:
   - the 66 website keys + layers.json (sha256 list in links\.kit-website-keys\sha256.json)
   - kit version 25x
   - the store (kpc-outline-store-full\results\layer-files, plus have\)
   - originals\ (never written)
   - Python add-ons: shapely, pyproj, pyshp, numpy
2. **Make the next kit** (#382 + #383 + #384). The owner runs START-HERE MN NY. Compare with test-2026-11-25-2245, park by park.
3. **Hand files in the store's have\:**
   - US-MA-sgmaa.geojson.gz, US-OH-sgoha/b/c.geojson, US-ME-sgmec.geojson, each with a .kpc-source.json.
   - Made from the owner's own downloads (Sonnet on his PC). The grader settled them as his downloads.
   - Nothing reads them until he runs LAYER-RECORDS, and that is his decision.
   - Alaska PAD-US: the .gdb (785 MB) needs `py -3 -m pip install pyogrio`, then kpc_padus_gdb.py.

## Later (from the grader and the owner)
- The report compares with the website **by the proof, not by id**: 27 MN website rows carry an id the new spelling gives another parcel.
- Each test is judged against the owner's **best earlier test**. The keep-last-good guard and the join check use that test, not the website key (rule change, grader first).
- One report line per layer: "row numbers moved: yes/no, how many". Since 12 Nov they moved in MN sgmne 13,111, sgmnc 236, sgmnb 59 and NY sgnya 3,216; everything else stayed.
- Name variants (Artpark, Lock 32, Reinstein Woods, Ludlow Creek, Charles Flood, Schunnemunk); PAD-US Source_PAID as a same-land proof. Ideas only.
- Still missing layers: MS mszw/mszp, AZ and ID idw (behind terms); retired layers still joined: CO sgcod, WA sgwae, ID sgidb, sgaki, UT sgutc.
