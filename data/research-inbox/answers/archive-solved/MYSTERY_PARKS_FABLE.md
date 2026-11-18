# Mystery parks — method and Fable (updated Nov 11, 2026)

This is the solving method the owner's outside agents used in early November 2026, **kept intact**, plus a short note on what changed after Nov 5.

Use the method below on the parks that are still open (`mystery-parks-open.csv`). Do not re-hunt parks in `solved-since.csv` — those now have an official grade in the released US or CA key. World parks that already have a Nov 5 official id stay open only because the world key is not released and has no official grade; reuse that id, don't start over.

---

# The method that cracked it (kept intact, from the Nov 5 handoff)

## 2. The method that cracked it (in one paragraph)
Stop searching park-by-park. Find the **agency's own queryable GIS service** (ArcGIS REST `/query` or OGC WFS `GetFeature`), ask it by name (`UPPER(NAME) LIKE '%kw%'` / `cql_filter=name ILIKE '%kw%'`), pull the polygon back in EPSG:4326, and run a **client-side point-in-polygon + distance-to-nearest-vertex** on the POTA pin. One service answers 20–300 rows at once. The pin test turns "I think this is the park" into "the pin is 3.2 km outside this exact official boundary." Distance also settles twins (two Lähdenevas 100 km apart; two Puertos de Beceites).

### Why the browser, not the sandbox
The cloud sandbox's web fetch strips query parameters and can only reach search-surfaced URLs, so it can read `?f=pjson` metadata but **cannot run `/query` or WFS GetFeature**. The desktop app's built-in browser pane can: `javascript_tool` + `fetch()` against the same origin. Pattern:
1. `request_access(url, scope="site")` → user approves (one prompt per host).
2. `navigate` / `preview_start` to the service's `?f=pjson` page.
3. Define helpers on `window` (they persist per tab/origin): `hav`, `pipE` (esri rings), `pipG` (GeoJSON), a `*q(kw, lat, lon)` query wrapper.
4. For >15 rows, **fire-and-forget**: `window.runQ(list)` starts an async loop storing into `window.US`, returns immediately; poll `window.Qdone`. A single call >45 s times out.
5. **Two-step query for big layers**: attributes first (`returnGeometry=false`), rank by name-token overlap, then fetch geometry only for the top 4 by `objectIds`, `geometryPrecision=5`.
6. **Hidden pane = ~1 query/4 s; pane in front = much faster.** A second worker tab on the same host, running the list in reverse, halves the time.
7. Dump results as compact JSON (`JSON.stringify`), paste to a file, triage in Python, write with `fill.py`.

### Triage rules used
- Exact unit name (or all POTA significant words present, ≥2 tokens) → **match**; note the pin distance / "PIN IS INSIDE".
- Name-related neighbour only, tract/unit piece, kind differs (urban park inside a natural park, reservoir vs "state fishing lake", pasture vs "recreation site") → **other = NEEDS-PERSON**, with the candidate and its id in the note (rules 5 & 7).
- Exact unique name but pin >25 km → **wrong pin**.
- Nothing within 15 km → **blank + note** naming what was searched.
- "If in doubt, NEEDS-PERSON. Never guess." was applied literally; the 183 "other" rows are the human queue.

## 3. Services proven this project (all in the CSV with fields + quirks). Highlights:
| Scope | Service | Rows cleared | Gotcha |
|---|---|---|---|
| **US** | USGS PAD-US 4.1 *Combined* `edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US_gaz_combined/MapServer/0` | 289 swept | `State_Nm` is the unit's state — pins near state lines need the neighbour state (Klamath, Caribou-Targhee). WSRs/NFs split per agency segment. Trails, historic sites, airstrips, byways, BLM rec sites, NPS affiliated areas are NOT units. |
| US | BLM `gis.blm.gov/.../recreation/BLM_Natl_Recs_poly/0`, `BLM_Natl_Recreation/9` (polys) `/3` (points) | 7 polys, ~30 point-only | No national SRMA/ERMA layer; those are in state RMP services. |
| US | USFS EDW `apps.fs.usda.gov/arcx/rest/services/EDW/*` | NRTs, NRA negatives | `national_trail_designation=2` = NRT. Rec-site points come back without geometry. |
| US | NPS `services1.arcgis.com/fBc8EJBxQRMcHlei/.../NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2` | confirms affiliated areas have no polygon | don't request `GIS_Notes` (query fails). |
| **CA** | ECCC CPCAD `maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0` | 49 swept | `LOC` is a numeric code, not a province; filter by distance instead. SK "Recreation Sites" appear only as Provincial Pastures. NHS, ZECs, biosphere reserves absent. |
| **EU** | EEA Natura 2000 `bio.discomap.eea.europa.eu/.../ProtectedSites/Natura2000Sites/MapServer` (layers 0 SCI, 1 SPA, 2 both) | 20 | some SITENAMEs UPPERCASE → use `UPPER()`. Twins exist. |
| EU | EEA CDDA v21 `.../ProtectedSites/CDDAv21_Dyna_WM/MapServer/1` | 27 (FI SE AT ES CH NO PL RO) | Romanian ș stored as `?` and ă stripped → use SQL `_` wildcards. Some `siteArea` values wrong — trust geometry. Same site in two inventories (CH03+CH52). |
| **FR** | IGN Géoplateforme WFS `data.geopf.fr/wfs/ows` — full PatriNat catalogue (`patrinat_znieff1`, `rnr`, `sic`, `zps`…) | 154/163 | Server-side `INTERSECTS` returns empty — do pip client-side. |
| **AU** | VIC DEECA PLM25 WFS `opendata.maps.vic.gov.au/geoserver/wfs` (CC BY 4.0) · QLD `spatial-gis.information.qld.gov.au/.../ParksTerrestrialProtectedAreas/MapServer/10` · NSW `mapprod3.environment.nsw.gov.au/.../EDP/Estate/MapServer/0` · WA SLIP `public-services.slip.wa.gov.au/.../Property_and_Planning/MapServer/15` (map service is *open*; only downloads need login; CC BY-NC) · CAPAD `gis.environment.gov.au/.../ogc_services/CAPAD/MapServer/0` | AU closed | No "state beach" tenure anywhere. NTWA covenants only in CAPAD, by exact number. |
| **NZ** | DOC PCL FeatureServer (CC BY 4.0) · Auckland Council Park_Extents `services1.arcgis.com/n4yPwebTjJCmXB6W/...` | — | ECan publishes no regional-park layer. |
| **ZA** | DFFE screening server `screening.environment.gov.za/.../OC_CV/Gazetted_Boundaries/MapServer/44` (SAPAD Q4 2025) | 4 | `dffeportal.environment.gov.za` has an **expired TLS cert** — not bypassed. |
| **GB** | Natural England AGOL `services.arcgis.com/JJzESW51TqeY9uat` (906 layers) · NatureScot WFS `ogc.nature.scot/geoserver/protectedareas/wfs` (OGL v3) | 3 + negatives | AONB layer has no section polygons (Bodmin Moor = Cornwall). |
| Others | GeoNB Socrata · SK PCAN · ICNF BDG · Azores SRAAC WFS · EELIS WFS · data.gouv.nc (NC) · Tokyo 緑のオープンデータ (CC BY per file, mainland only) | see CSV | |

## 4. Japan — how to finish it on the box
All 70 JP rows were `name_differs`: the box's candidates are its own romaji of A10_005 (中部山岳 → "chuubu sangaku"). `JP_A10_crosswalk.csv` gives the exact 漢字 key per row. Join `A10_005 = key` (and `A10_001` prefecture where two prefectures share a name — 多良岳 in 41 & 42), then pin-test. 23 already written as match, 21 as other (都市公園 / 県民の森 inside natural parks), 26 notes with keys. Tokyo mainland urban parks and 都民の森 are in the Tokyo shapefiles; the island parks (大島/多幸湾/羽伏浦/大神山) are not — ask 東京都建設局. Three names flagged unverified (join will simply miss if wrong).

## 5. Open items for the owner (decisions / emails — recorded in the CSV too)
- Licence decisions: **WA DBCA CC BY-NC 4.0**; **MX CONANP "cite the source"**.
- Email: Agrárminisztérium (HU) for the public WMS + reuse terms. Optional courtesy email to Tokyo 緑地景観課 (park files are CC BY; the PDF asks to be told when quoted).
- The 183 **NEEDS-PERSON** rows — mostly kind/piece differences; each note names the candidate and id.
- Box jobs still queued: JP join; PL GDOŚ WFS (Wełtyń); ES ENP_ES zip (6 regional parks are now answered via CDDA anyway); MX CONANP IDEFOR layer (11 rows); corrected pins from matched polygons.

## 6. Dead ends (don't retry)
Parks Canada NHS layer (none) · MX INAH (per-request) · Hungary vector data (ministry only) · catalogo-irig.madeira.gov.pt and ideserver.sma.gob.cl (won't load) · serverags1.economia.gob.mx (won't load in pane) · Oregon/ECan regional parks (not published) · BZ/DO/KE/PA/PY/LK/GA/GT/LR/SV/UY (no official GIS surfaced in 3 searches each) · GUGiK for Polish PAs (wrong agency; GDOŚ).

## 7. Rules we worked under (keep them)
Official agency data only · OSM/WDPA/Google/Wikipedia/hiking sites are leads, never sources · obey robots/bot-checks/logins (WA downloads, DBCA) · never bypass a cert error · nothing saved to the user's PC without asking · never take the bigger place (rule 5) · kind differences go to a person (rule 7) · if in doubt, NEEDS-PERSON.


---

# What changed since Nov 5, 2026

Written Wednesday, Nov 11, 2026, evening, America/Louisville (Eastern Time, UTC-5). Box-only cross-check against the just-released US and CA keys.

## Keys now released (map tools read these copies only)

- Source sha on main: `addf5c4e23d864a95a5c3fa7848819c93295034a`.
- US released 5:10 PM ET, run 43109409415 (the US key content is from FL run 43056604383 — **not** failed run US-42797939226, which is never released).
- CA released 5:10 PM ET, run 43109466490 (regrade of 43049790907 / 43003880140).
- Advertised totals (per-state sums, so a park that sits in more than one state file is counted in each): **US 13,107 parks — 11,271 official, 414 approximate, 1,422 pin**. Unique refs in the released US key: 12,857. There is no US-KY.json (Kentucky is the club state). **CA 5,901 parks — 4,348 official, 39 approximate, 1,514 pin**.
- World was not released. The working world key has no official grades at all (approx or pin only). A Nov 5 `match` on a world park is **not** solved.
- This release copied US outlines + the US key, and the CA key. It did not copy CA outline files.

## The 832 mystery parks, re-checked

- **178 solved since** (official grade in the released key): **115 US**, **63 CA**. See `solved-since.csv` for how each one was solved (key join, sources, and the Nov 5 answer if any). 103 of the 115 US official parks also have a polygon in the released US outlines; 11 are official lines (trails) with no polygon file; 1 (US-10281 White Mountains NRA / SRMA) is official in the key but has no released polygon yet.
- **654 still open**: 192 US (189 pin, 3 approximate), 16 CA (all pin), 446 world (working world key, not released: 328 with no official grade, 80 approx, 38 pin).
- 108 of the 178 solved parks were already a Nov 5 `match` and were in the 395-row intake fed to the bots (not overrides). 50 had been left as `other` / NEEDS-PERSON and a later rebuild still joined an official record — read the notes before treating the piece/kind question as closed. 19 had been blank; 1 (US-4894 Davis-White State Forest) was flagged wrong pin and stayed official under the standing name-match rule (the pin is not moved).
- 17 US/CA parks were a Nov 5 `match` and are **still pin** in the released key (8 CA, mostly NB PNAs with pin >15 km, plus US-0754, US-11297, US-8422, US-10389, US-4376, US-13155, US-6259, US-6261, US-11900). Reuse the official id; find out why the join did not become official; don't search from scratch.
- 311 world parks were a Nov 5 `match` and stay open only because the world key is not released. Keep the official id/url. Do not treat working `approx` as official. WDPA stays private and never feeds a public outline.

## Method additions (they don't replace the Nov 5 method; they tighten it)

The Nov 5 method still stands: stop searching park-by-park when an agency GIS will answer a batch; official agency data only; client-side pin test; never guess; NEEDS-PERSON if in doubt; never take the bigger place; kind/piece differences go to a person; never invent pins.

What is new or now explicit:

- **KISS ownership.** The owner comes from the official record or agency. No live ownership-layer calls. Don't phone USFS/BLM ownership services to decide a join.
- **Official documents first.** When a wetland, refuge, or far-pin case is in doubt, trust the official document and official registry record ahead of the pin or a secondary compilation.
- **Owner record wins on duplicates.** If two official records cover the same land, keep the owner agency's record, not a later copy or a manager-name fallback unless the owner has already decided otherwise (Canada manager-name fallback is YES when the CPCAD owner is blank).
- **County parcel is OK for Kentucky lakes.** For KY fishing lakes, a county parcel may be used where it is the official land record. (KY is the club state and is not in the released US key.)
- **Pins are not proof.** A POTA pin does not prove a boundary, a join, or a 2-fer. Never move a POTA pin. If the official name matches and the pin is off, keep the official outline and flag the pin. If the name or area does not support the match, leave it a pin and send it to a person.
- **Traces and the picture placer are approximate only.** A picture trace, a parcel trace, or the by-hand picture placer never becomes official. The same gates apply: the pin must sit inside the shape, the name and website must check out, and the size must be sane for the park type. An approximate 2-fer is allowed only when that shape sits inside a bigger park, and only after the usual gates.

## What not to redo

- Don't hunt parks listed in `solved-since.csv`.
- Don't retry the dead ends in the handoff (section 6): Parks Canada NHS, MX INAH, Hungary vectors, catalogo-irig.madeira.gov.pt, ideserver.sma.gob.cl, serverags1.economia.gob.mx, Oregon/ECan regional parks, the BZ/DO/KE/PA/PY/LK/GA/GT/LR/SV/UY "no official GIS" set unless a new official source is in the hand-download list, or GUGiK for Polish PAs.
- Licence holds stay: WA DBCA CC BY-NC, ZA SAPAD/DFFE, Newfoundland, and Tokyo parks are matching-only or approximate-id only — no public outlines from those.
- Check saved copies and `research-sources-all.csv` before asking for a file or a hand download. Hosts we must never contact live are in HOUSE_RULES.md.

---

# Fable — pass-by-pass log (kept intact, as written Nov 4–5, 2026)

The log below is the original `MYSTERY_PARKS_PASS9_FABLE.md`. It is the record of how the earlier agents actually solved the rows, including ZNIEFF, Géoplateforme, PAD-US, CPCAD, and the state-cluster close-out. Do not rewrite it.

# Mystery parks – pass 9 (Fable, Wed Nov 4 2026, ~20:20 CST) – short, budget-limited

Input v8 (125 answered). Output `mystery-parks_answered_v9.xlsx`: 6 new ZNIEFF matches → **131 of 832** (124 match, 7 other, 701 blank).

| ref | ZNIEFF | official name |
|---|---|---|
| FR-11218 | 220013818 | Forêt de Rémy et Bois de Pieumelle |
| FR-11230 | 910030627 | Versant sud du Massif du Madres (type 2) |
| FR-11644 | 930020021 | Plateau de la Grau de Courchon et de la montagne de l'Aup |
| FR-11649 | 410030273 | Etang de Haraigne à Dieppe-sous-Douaumont |
| FR-11879 | 230030974 | L'Île Motelle à la Roquette |
| FR-11931 | 230031188 | La cavité des moulins de Mérey |

6 of 6 this batch — all exact-name hits, each page opened before writing. ~116 ZNIEFF rows left; same method keeps working, or the box can bulk-join INPN's ZNIEFF download (data.gouv.fr, licence 'Other (Open)').

## Addendum – batch 2 (6 tried, 4 answered) → book at 135 of 832
Answered: FR-11912 Les Grandes Côtes (230009123), FR-11913 Bois des Prés et des Maladreries (230009119), FR-11914 Bois des Plaisirs/Vaux/Coqueline (230004507), FR-11941 Les Coutumelles (230015806) — all Eure, exact names.
Blank with notes: FR-11889 (nearest record has a different name, 'Le Bois et les Prairies du Hom'), FR-11650 (the Dieppe-sous-Douaumont bat-roost record didn't surface; its sibling étang record is 410030273, so check INPN's commune page).

## Addendum – batch 3 (5 tried, 3 answered) → book at 138 of 832
Answered: FR-12129 L'Isole à Pont Croac'h (530020116), FR-12257 La Fontaine de l'Ille (530030135), FR-5616 Cap Sizun face nord = 'Îlots, falaises et landes de la côte nord du Cap Sizun' (530030106 -- paraphrase, flagged in the note).
Blank with notes: FR-12255 Étang du Boulet (no Feins record surfaced; check the INPN commune page), FR-16532 Agriates (several Corsican candidates, right one not yet identified).
**v9 is the merged book**: 138 answered = every pass 1-9 (spot-checked one row per pass).

## Addendum – rounds 4+5 (12 tried, 7 answered) → book at 145 of 832
Round 4: FR-12419 Vallon du Nascouil... (730012018), FR-12420 Etang des Treffoux (830005427), FR-12432 Collines du Bas Razès (910030417), FR-12439 Pechs et vallées autour de Mayronnes (910030422), FR-12464 Garrigues de Vingrau (910030470).
Round 5: FR-12448 Crête du Ramaret et de la Serre de Massac (910030104), FR-12279 Ruisseau de Saint Jean (530015494).
Blank with notes: FR-12401 Vicdessos (probable successor record 'Montcalm et Vicdessos' 730012010 -- rename/merge, person confirms, rule 5), FR-12299 Guérande partie amont (nearest record is the larger Pen-Bron zone).
**Totals: 145 answered (138 match, 7 other), 687 blank. Fable 24, Opus 71, Sonnet 50. v9 remains the single merged book.**

## Addendum – rounds 6+7 (10 tried, 8 answered) → book at 153 of 832
Round 6: FR-12472 Garrigues de Sournia et Grotte du Desix (910010882), FR-12495 Pic de Bénal (910030123), FR-12513 Parois calcaires et quiès de la haute vallée de l'Ariège (730011919), FR-12518 Basse Cerdagne (910030617, type 2), FR-12520 Capcir (910030619, type 2).
Round 7: FR-12522 Vallée du Conflent (910010885, type 2), FR-12528 Petit plateau de Sault (910030632, type 2), FR-12540 Coteaux de la Lauze et de l'Arrats (730030397).
Blank with note: FR-12491 Soulane des gorges de l'Aude au Clat — no record carries 'au Clat'; nearest is 'Soulane de la vallée de l'Aude à Fontanès-de-Sault' (910030134); person picks.
**Totals: 153 answered (146 match, 7 other), 679 blank. Fable 32, Opus 71, Sonnet 50. v9 is the merged book.**

## Addendum – rounds 6+7 (10 tried, 8 answered) → book at 153 of 832
Round 6: FR-12472 Garrigues de Sournia et Grotte du Desix (910010882), FR-12495 Pic de Bénal (910030123), FR-12513 Parois calcaires et quiès de la haute vallée de l'Ariège (730011919), FR-12518 Basse Cerdagne (910030617, type 2), FR-12520 Capcir (910030619, type 2).
Round 7: FR-12522 Vallée du Conflent (910010885, type 2), FR-12528 Petit plateau de Sault (910030632, type 2), FR-12540 Coteaux de la Lauze et de l'Arrats (730030397).
Blank with note: FR-12491 Soulane des gorges de l'Aude au Clat — no record carries 'au Clat'; nearest is 'Soulane de la vallée de l'Aude à Fontanès-de-Sault' (910030134); person picks.
**Totals: 153 answered (146 match, 7 other), 679 blank. Fable 32, Opus 71, Sonnet 50. v9 is the merged book.**

## Addendum – round 8, Azores WFS (5 of 5) → book at 158 of 832
The new SRAAC INSPIRE WFS answered every blank Azores row, each with official name, legal act (DLR) and INSPIRE id, and a pin check:
PT-0137 Terra Brava e Criação das Lagoas (PT0700057), PT-0146 Biscoito das Fontinhas habitat-management area (PT1500033), PT-0262 Morro de Castelo Branco (PT0700037), PT-0263 Monumento Natural do Vulcão dos Capelinhos (PT0900020), PT-0283 Monumento Natural da Rocha dos Bordões (PT0900017).
All five pins fall 1.4–6.9 km OUTSIDE their polygons — the familiar pattern. Madeira (PT-0318 Machico) remains the only island row open.
**Totals: 158 answered (151 match, 7 other), 674 blank. Fable 37, Opus 71, Sonnet 50.**

## Addendum – round 9: Madeira + mainland Natura (3 answered) → book at 161 of 832
- PT-0318 Machico = Natura 2000 PTMAD0014 (IFCN's own standard data form; 11 ha; pin ~4.9 km from centre).
- PT-0015 Alvito/Cuba = PTCON0035 (ZEC, 921.9 ha) and PT-0063 Azabuxo/Leiria = PTCON0046 (ZEC, 136.8 ha) — from ICNF's BDG/SIC query layer, pins 4.6 / 2.1 km outside.
- ICNF's BDG directory turns out to carry ALL mainland designation layers (SIC, ZEC, ZPE, RN2000, RAMSAR, BIOSFERA) — recorded in research-sources-all.csv.
Portugal is now fully answered except PT-0382 Litoral Norte (kind question for the owner).
**Totals: 161 answered (154 match, 7 other), 671 blank. Fable 40, Opus 71, Sonnet 50.**

## Addendum – round 10: the Géoplateforme breakthrough (16 answered) → book at 177 of 832
Found the official national ZNIEFF WFS on IGN's Géoplateforme (PatriNat layers patrinat_znieff1/znieff2, 17,626 type-1 zones, fields nom_site + id_mnhn + inpn url). Two browser batches of name+pin checks answered 16 rows at once, including three that web search had failed on:
- **Vallée de l'Automne** (the exact-name record is the TYPE-2, 220420015 — pass 4 had only found the type-1 'Haute Vallée')
- **Le Bois des Planches, le Hom et la Côte du Hom** (230030886) and **Marais de Thun-Saint-Amand** (310030002)
- **Moyenne vallée de Vicdessos, Pic de Tristagne** exists after all as type-1 730012112 (the 'Montcalm' zone is its type-2 parent)
- Étang du Boulet, Partie amont des marais salants, plus 10 Gers/Landes/Hérault/Var/Meuse zones (Guiroue, Castelnau-Barbarens, Lasserre, Sainte-Dode, Escoubillon, Monbel, Hartaou, Estagnol, Barre de Saint-Quinis, Oeil de Boeuf à Lamorville).
Every pin tested: all OUTSIDE by 1.7–14 km except none inside — the familiar pattern.
New notes: Cap de Saint-Tropez '2' (marine znieff?), Chaudefour (POTA names the protection perimeter, a different legal object), Rebenty (valley records only), Agriate(s) spelling.
**Totals: 177 answered (170 match, 7 other), 655 blank. Fable 56, Opus 71, Sonnet 50. FR is now 77 answered. ~75 FR rows remain, all doable with this WFS.**

## Addendum – round 11: Géoplateforme mass batch (59 answered) → book at 236 of 832
Three WFS batches (~90 lookups) swept the remaining French ZNIEFF rows: **59 new matches**, every one an exact-name record with id_mnhn and a client-side pin test (pins 0.2–10 km outside; Hourdel and Lison pins INSIDE their zones). Highlights: the whole Forez tourbière series (Braveix, Gorces, Viallevieille, Balayoux, Malmotte, Egaux, Seychal...), the Gers coteaux series, Corsican Porto-Vecchio sites, and FR-6682 Source du Lison.
19 rows got explanatory notes instead: 5 are DIFFERENT REGISTRIES (RNR Schoubrouck + Pibeste; Natura Bresse jurassienne ×2 + Aspretto gull colony — one INPN fetch each next pass), 2 are renamed-section questions (Oze, Cousin aval), and 12 are not-found-within-10-km cases pointing at INPN commune pages (accents: Montréal, Génieux, Hébécourt...).
**France is done for ZNIEFF: 136 of 163 FR rows answered, 27 blank and every blank carries a note. Book totals: 236 answered (229 match, 7 other), 596 blank. Fable 115, Opus 71, Sonnet 50.**

## Addendum – round 12 (final): the other French registries (5 answered) → book at 241 of 832
The Géoplateforme turns out to carry EVERY PatriNat registry (rnr, rnn, apb, sic, zps, parc national, pnr, ramsar, biosphère, conservatoire du littoral...). The five different-registry rows fell at once:
- FR-1954 RNR251 'Prairies du Schoubrouck' (INPN FR9300097)
- FR-3773 RNR241 'Massif du Pibeste - Aoulhet' (FR9300101) — pin 15 km out, flag it
- FR-3912 / FR-4414 'Bresse jurassienne' = habitats FR4301306 + birds FR4312008 (pairing arbitrary, swappable; shared pin 22 km out = wrong pin)
- FR-4445 ZPS FR9412001 'Colonie de Goélands d'Audouin d'Aspretto/Ajaccio'
**FINAL TOTALS: 241 answered (234 match, 7 other), 591 blank. France 141/163. Fable 120, Opus 71, Sonnet 50. v9 = the merged book; research-sources-all.csv = the merged GIS file (131 rows).**

## Addendum – round 13 (the real final): accent retries (13 answered) → book at 254 of 832
Re-running the not-founds with accented/alternate spellings cracked 13 more, incl. the night's stragglers: Haute vallée de la Grave, Soulane au Clat, Désert des Agriate (= POTA 'agriates'), Tourbière de l'Oule, Marais du Gand, Prairies de Mons, Forêt de Génieux, Brosse-Dieu, Chatillon/Mont-Aigre, château du Marais, subéraies de Montréal, Hébécourt/Prés Valloires, and Picquigny (pin INSIDE the Somme-marsh stretch record, flagged like Hourdel).
**FRANCE: 154 of 163.** The 9 left: Tannes d'Arceau, Cap de Saint-Tropez 2 (marine?), Chaudefour perimeter (kind), Dieppe-sous-Douaumont bat roost, Rebenty, Oze + Cousin (renamed sections), Carrière de la Côte de l'étang, Peyre-Mayou/Pierre-sur-Haute — each with a note.
**NIGHT-END TOTALS: 254 answered (247 match, 7 other), 578 blank — from 29 this morning. Fable 133, Opus 71, Sonnet 50.**

## Round 14 addendum (EEA Natura 2000 sweep, post-compaction)
New service: **EEA Natura2000Sites MapServer** (bio.discomap.eea.europa.eu, 2024 release, CC-BY 4.0) — queryable; `UPPER(SITENAME) LIKE` + client-side pip, same method as the Géoplateforme. Recorded in research-sources-all.csv (now 133 rows).

**20 rows answered (19 match, 1 other):**
- AT-0308 Tiefer-Wald → AT3316000 (3.2 km)
- ES-0785 Efesa de la Villa → ES2430033 (6.3); ES-0832 Costa central y Ría de Ajo → ES1300006 (5.0); ES-1717 Tamanca → ES7020022 (3.3); ES-1740 Los Sables → ES7020064 (3.5)
- ES-0737 Puertos de Beceite → **other/NEEDS-PERSON**: twin same-name sites, SPA ES0000307 + SCI ES2420036, pin outside both (19.9/31.1 km)
- FI-0100 LIVOJÄRVI → FI1301103 (2.8; name stored uppercase — the reason the first LIKE missed); FI-0103 → FI1101642; FI-0108 → FI1301907; FI-0528 → FI0200152; FI-0590 → FI0325008; FI-1086 → FI1200736; FI-1417 → FI0309008; FI-1519 → FI1000036 (100-km namesake FI1103401 ruled out); FI-1582 Kiiminkijoki → FI1101202 (17.2 km, long river site); FI-1723 → FI1200511
- SE-0266 Kragenäs → SE0520155; SE-1575 Skansen Läckö → SE0540110; SE-2138 Norra Kvill → SE0330050; SE-2180 Brattforsheden → SE0610178

Every pin outside its polygon (1.1–17.2 km) — the night's pattern holds, 43/44 service-checked pins now outside.

**Night totals: 274 of 832 answered (266 match, 8 other), 558 blank.** Fable 153 / Opus 71 / Sonnet 50.

Still service-reachable without US/CA/JP: FI national-designation rows (4: Sipoonkorpi NP, Oukkulanlahti MPA, 2 soidensuojelualue + Hangasneva), SE nature reserves (5), AT national designations (6), ES regional parks (6) — the CDDA service on the same EEA host may cover several of these in one more sweep.

## Round 15 addendum (EEA CDDA sweep — national designations)
Same EEA host, **CDDAv21_Dyna_WM/MapServer layer 1** (polygons) — the "decision (a)" route, now proven. Recorded as its own row in research-sources-all.csv (now 134 rows).

**27 rows answered (23 match, 3 other, 1 wrong pin):**
- FI-0238 Sipoonkorpi NP → KPU010036 **pin INSIDE**; FI-1461 Hangasneva SSA100051; FI-1593 Jänessuo SSA110096; FI-0378 Oukkulanlahti → other (11 private YSA fragments, no single MPA polygon)
- SE-0199 Pessinki fjällurskog NVR 2001055 **pin INSIDE** (97,226 ha); SE-1574 Skansen Läckö NVR 2000570; SE-2042 Västanå NVR 2001378
- AT-0102 NSG Gösselsdorfer See Süd natId 2131 **pin INSIDE**; AT-0196 Sandberge Oberweiden 3050; AT-0388 Soboth-Radlpass 6059; AT-0414 Altausseer See 6207; AT-0190 Donauinsel → other (two LSG halves, pin inside Nord); AT-0029 Kaunergrat → **wrong pin** (LSG is 61.6 km away in a different range — first true wrong-pin of the night)
- ES-0033 Enebrales ES615004; ES-0044 Moncayo ES243001; ES-0058 Sierra de Santo Domingo ES243004 (18 km, flagged); ES-0198 Serra da Enciña da Lastra ES113004 **pin INSIDE**; ES-1477 Laguna del Rincón → other (name diff vs POTA 'del Muerto')
- CH-0225 Unteres Ghögg CH03_0011 **pin INSIDE** (twin CH52 record); CH-0226 Ghöggerhütte CH03_0012 (pin 0.06 km — on the edge)
- NO-2977 Hjerkinn/Kongsvoll/Drivdalen VV00001894 **pin INSIDE**
- PL-1474 PK Góra Św. Anny PK.47 **pin INSIDE**
- RO-0322 Pădurea Roşoşa B8. (area FIELD wrong, geometry fine); RO-0450 Călugărească 2.666.; RO-0573 Stuhoasa 2.233.; RO-0883 Tătăruși 2.546.; RO-1019 Buciaș IV.7.
- RO-0880 Pădurea Homița: **not in CDDA** — note written, left blank. PL-1911 Wełtyń ZPK: not in CDDA, left blank (GDOŚ WFS box job).

Seven pins INSIDE their polygons this round — the first inside pins of the whole night. Quirks (RO '?' diacritics, bad siteArea fields, twin-inventory duplicates) recorded in the CSV row.

**Night totals: 301 of 832 answered (289 match, 11 other, 1 wrong pin), 531 blank.** Fable 180 / Opus 71 / Sonnet 50. Europe is now essentially closed except GB (11), PL-1911, RO-0880, SE heritage x2 (RAÄ), and the 9 noted FR blanks; the rest of the blanks are US/CA/JP box work plus AU/MX/CL/KE/ZA/BZ/DO/NC/PA/PY/LK singles.

## Round 16 addendum (morning 2026-11-05 — AU / ZA / GB services)
Six new official queryable services, all recorded in research-sources-all.csv (now 140 rows):
- **Victoria DEECA PLM25 WFS** (CC BY 4.0) — 14 rows, **all 14 pins INSIDE** (Big Desert WP, Gerang Gerung N/S, Strzelecki Devon North + Middle Creek, Macedon/Crawford River/Mt Mitta Mitta RP, Ararat/Wail/Beenak G180 BR, Mitta Mitta River K26-28 SSR). 5 "state beach" rows → other (no beach tenure exists; land under them is council foreshore reserve). Beenak G183 does not exist in PLM25 → note only.
- **Queensland protected-areas MapServer** — Dan Dan / Wietalaba / Mount Binga SF, all pins inside. North Johnstone wild river → other (Wild Rivers Act repealed 2014). Turtle Creek beach → other.
- **NSW NPWS Estate MapServer** (CC BY 3.0 AU) — Mooball NP N0145, 8 km.
- **DFFE SAPAD Q4 2025** (screening.environment.gov.za; dffeportal has an EXPIRED CERT — not bypassed) — Anysberg Provincial NR pin inside; New Germany NR; Waters Meeting NR (20 km, flagged); Baviaanskloof → other.
- **Natural England AGOL** (906 layers) — Shire Brook LNR match; Bodmin Moor → other (only whole-Cornwall AONB polygon, pin inside it); Roding Valley / Northlands → other (name/kind); RSPB ×2 → other (NGO land, not a designation); Hirsel → note.
- **NatureScot WFS** (OGL v3) — Cairngorms NNR 5013, Inverneil Burn SSSI 816 match; Cromarty Firth/Conan Islands → other (sub-part of a multi-part SSSI/SPA/Ramsar).

**Totals: 339 of 832 answered (313 match, 25 other, 1 wrong pin), 493 blank.** Fable 218 / Opus 71 / Sonnet 50.
Remaining non-box blanks: WA (DBCA login), MX 11, BZ 5, DO 5, KE 4, CL 4, NC 3, PA 3, PY 3, LK 2, PL-1911, RO-0880, SE heritage ×2, FR noted 9, Beenak G183, Hirsel.

## Round 17 addendum — New Caledonia + closed negatives
- **data.gouv.nc / Province Sud aires protégées** (Licence Ouverte v2.0): NC-0023 Rivière Bleue, NC-0025 Haute Pourina, NC-0049 Mont Do → match, with official province-sud.nc per-site pages. Geometry served is simplified (geomsimplify) — flagged.
- **MX** serverags1.economia.gob.mx (CONANP layer mirror): readable metadata but the host will not load in the browser pane → recorded as lead/blocked, no queries run.
- **PA / DO**: no official ArcGIS/WFS services surfaced in search (only Colombian/third-party hits). Not pursued further.
- Not attempted (no official service known): KE (KWS), LK, BZ, PY, CL (closed earlier), WA rows (DBCA login).

**Totals: 342 of 832 answered (316 match, 25 other, 1 wrong pin), 490 blank.** Fable 221 / Opus 71 / Sonnet 50. CSV: 142 sources.

## Round 18 addendum — Western Australia unlocked + stragglers
- **WA SLIP public map service (DBCA-011)** — explicitly "Open - available for use by everyone" (only file downloads need the login). Waychinicup NP (R 27502/R 25865), Morton NR (R 31360, 10.9 km flagged), Mount Manning NR (R 53855, ex "Mount Manning Range"), Ellis Creek SF (F 17, 43 parcels). Licence CC BY-NC 4.0 — owner decision still pending.
- **CAPAD 2024 (DCCEEW, federal)** — all 7 NTWA Bushland covenant rows by exact covenant number: 4 pins inside, 3 within 0.05 km. The rows' earlier "best candidates" were *different* covenant numbers — that was the whole mystery.
- **Auckland Council Park Extents** — Te Arai Regional Park (pin 0.22 km). ECan has no regional-park layer → NZ-0051 note.
- EEA: SI-0361 Dolina Reke SPA SI5000003; ES-1665 Barranco Oscuro (found yesterday, written today); SK-0300 Hrádok → other.
- Notes only: FR-14049, NZ-0051.

**Totals: 357 of 832 answered (330 match, 26 other, 1 wrong pin), 475 blank.** Fable 236 / Opus 71 / Sonnet 50. CSV: 145 sources.
AU is now closed except Beenak G183 (absent from PLM25). Remaining reachable: MX 11 (server won't load), FR 9 noted, NZ 4 noted, plus singles (GA, GT, LR, NL, SV, UY, PL-1911, RO-0880, SE heritage x2, GB Fair Isle/Hirsel).

## Round 19 — THE BIG LEVERS (US PAD-US + Canada CPCAD), 2026-11-05 morning
Both national registers turned out to be queryable ArcGIS services on the agencies' own servers, so the "box job" became a browser job.

**Canada — ECCC CPCAD** (`maps-cartes.ec.gc.ca`, "authoritative source"): all 49 CA rows swept. 18 match (Roche Lake Park pin INSIDE), 3 wrong pin (Shell Lake 72 km, Butternut Island 34 km, Ulittaniujalik NP 45 km), 16 NEEDS-PERSON (7 SK "Recreation Sites" exist in CPCAD only as Provincial *Pastures*; Denetiah pin inside the Park not the Corridor; name/kind mismatches), 12 confirmed-absent notes (ZECs, biosphere reserve, Marconi NHS, Kananaskis Country, some MB/NB WMAs, AB PRA).

**United States — USGS PAD-US 4.1 Combined** (`edits.nationalmap.gov`): all 289 US rows swept with two browser workers (~45 min). Triage rule: exact/full-name unit → match (56; pins inside for Blue Springs SP, Anza-Borrego, Deep Creek x2, Brush Mountain, Tule Springs, Lower Rio Grande Valley NWR, Choke Canyon, Beaver Dam (North)…); name-related neighbour only → NEEDS-PERSON (66: tract/unit pieces, USACE reservoirs vs "state fishing lakes", WSR segments, state-line pins for Klamath/Caribou-Targhee/Rogue River-Siskiyou); nothing within 15 km → note (166 — trails, historic sites, airstrips, scenic byways, BLM rec sites and NPS affiliated areas are simply not PAD-US units). 1 wrong pin (Davis-White SF, NH, 55.6 km).

**Japan** stays a box job: no official queryable service exists for 国土数値情報 A10; 70 rows need the shapefile + romaji↔漢字 reconciliation.

**Totals: 517 of 832 answered (404 match, 108 other, 5 wrong pin), 315 blank** — every blank now carries a note except the 70 JP rows. Fable 396 / Opus 71 / Sonnet 50. CSV: 147 sources.

## Round 20 — Japan crosswalk
Diagnosis: all 70 JP rows were `name_differs`/`pin_far`, and every "candidate" is the box's own romaji of A10_005 (中部山岳 → "chuubu sangaku"). So Japan is a **name join**, not a GIS gap. Built `JP_A10_crosswalk.csv` (ref → exact A10_005 漢字 key, A10_002 class, prefecture code, proposed answer).
- 23 **match**: candidate romaji decodes to the POTA park (Chubusangaku, Zao, Funagatarenpo, Tashirodake, Ota, Hikikyuryo, Tainai Ninoji, Aganogawa Line, Naomine Matsunoyama Oike, Chomonkyo, Iwakisan, Sasayama, Yokogurayama, Taradake ×2, Shotaizan, Ashikita Kaigan; Akita Shirakami = A10's predecessor name 八森岩館; plus the 5 pin-far rows whose names the box had already matched).
- 21 **other**: 都市公園 / 県民の森 / facilities sitting inside a natural park (Kairakuen, Senba, zoo park, embassy villas, Ako, Kinrin, Yoshino…) — kind differs, rule 7; or the polygon at the pin is the bigger neighbour (Rakanzan vs 西中国山地, Hokusho vs 西海).
- 26 **notes** with the exact join key for the box (Saitama 奥武蔵/黒山/長瀞玉淀/上武, 大洗, 大村湾, 津江山系, 金峰山…) or the right non-A10 source (Tokyo 緑のオープンデータ for 奥多摩湖畔公園 and the two 都民の森 — mainland only, so the island parks 大島/多幸湾/羽伏浦/大神山 need Tokyo 建設局).
Caveat: 3 Japanese names are flagged unverified (Niigata 青少年の森, Miyagi 縄文の森, Akita 県民の森).

**Totals: 561 of 832 answered (427 match, 129 other, 5 wrong pin), 271 blank — every blank annotated.** Fable 440 / Opus 71 / Sonnet 50.

## Round 21 — the three federal gaps (BLM, USFS, NPS)
- **BLM national recreation services** (gis.blm.gov): 54 BLM rows. 7 polygon matches (Bangs SRMA pin INSIDE, Rio Bonito Tract 1 pin INSIDE, Pipeline campground pin INSIDE, Johnson (Gordy's) Hill N/S, White Mountains SRMA 1.0M ac (pin 23 km out), Boulder Lake SRMA, Baker Archaeological). ~30 sites exist only as POINTS, 0.01–0.5 km from their pins — POTA's BLM pins are excellent, but BLM publishes no polygon for trailheads/overlooks/interpretive sites → NEEDS-PERSON (point-only = probably "no boundary exists"). 17 absent (airstrips, designated-route areas, several UT/NV/WY sites) → state RMP services. No national SRMA/ERMA layer exists.
- **USFS EDW** (apps.fs.usda.gov): Cascades NRT (trail 70) and Cornelius Creek NRT (trail 18) found 10 m from pins — line features, match. Black River / Lake Michigan "NRAs" are USFS recreation *sites*, not designated areas → other.
- **NPS Land Resources boundary layer**: 22 rows. NACA + Blackwell confirmed earlier; the rest are **affiliated areas / designations with no NPS polygon** (Chimney Rock, OKC Memorial, Gloria Dei, Glen Echo, Campobello, Maine Acadian, Ice Age Floods NGT, Inupiat, Rohwer, WWI Museum, Desert Storm, Kyle Ranch, Leonard Rockshelter, Fort Washita, Nine Mile Prairie, Weldon Spring [probably a POTA naming error — it's a Missouri conservation area]) → other, owner named. Alaska WSRs (John, Tinayguk, Mulchatna) live inside their parent parks → other.

**Totals: 621 of 832 answered (436 match, 180 other, 5 wrong pin), 211 blank — all annotated.** Fable 500 / Opus 71 / Sonnet 50. CSV: 150 sources.
Remaining US 106 blanks = state historic sites (OK/NV/ND), state fishing lakes (OK/TN/MS), Michigan state harbors, Idaho airstrips, Nevada scenic byways, FL water-district tracts, MN/WI WMA units — state-agency services, 5–15 each. The federal lever is spent.

## Round 22 — state clusters + close-out (2026-11-05 ~08:00)
- WI DNR Managed Lands: Wolf River Bottoms WA pin INSIDE (no LaSage sub-unit → other); Johnson/Sette/Swinging Gate/Pleasant Valley/Adell are NOT DNR properties (likely county) → notes.
- VT ANR unit layer: Boulder Beach SP and Little River SP have no own polygon — pins inside Groton SF / Mt. Mansfield SF → other (rule 5).
- Remaining 47 un-noted blanks (BZ/DO/KE/PA/PY/LK/GA/GT/LR/SV/UY/MX/NL/GB-6967/PL-1911/SE heritage ×2) annotated with the search negative and the agency to ask.
- Handoff written: `HANDOFF_METHODS_AND_TRICKS.md`.

**FINAL at handoff: 624 of 832 answered (436 match, 183 other, 5 wrong pin); 208 blank, all annotated.** Fable 503 / Opus 71 / Sonnet 50. CSV 151 sources. Tab consistency: 0 mismatches.


---

# Appendix — official-polygon evidence idea (kept intact, still parked)

The note below is the Nov 4 idea for turning the method into a pile-solver rule. It was parked; it is not a built rule. The quirks and service table are still useful.

# IDEA (parked for a later round): "official-polygon evidence" rule for the pile solver
Source: the owner's outside agent, mystery-park passes Nov 4 2026. Not built. No estimate made (scope cut).

## Method
1. Query the agency's own GIS service by name (ArcGIS REST /query `where=UPPER(SITENAME) LIKE '%X%'`, or WFS `cql_filter=nom_site ILIKE '%x%'`).
2. Take back the official polygon, registry id and area.
3. Run point-in-polygon and distance-to-boundary on the POTA pin, on our side (some servers refuse spatial filters).
4. When two sites share a name, the nearest boundary wins. If they are too close to call, a person decides.
5. Pattern seen: POTA pins are nearly always on the right land but 2-15 km outside the official line. the owner decision is still pending on that band. Suggestion: 0-15 km is a join with a flag, and over 15 km goes to a person as a possible wrong pin.

## Services proven Nov 4 (no robots.txt on these hosts, so no robot limits; keep the KPC manners rules: rate limit, honest UA)
| service | url | id / name fields | covers |
|---|---|---|---|
| EEA Natura 2000 | bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer (0 SCI, 1 SPA, 2 both) | SITECODE / SITENAME, SITETYPE, MS, Area_ha | all EU Natura (UK needs the JNCC licence) |
| EEA CDDA v21 | .../ProtectedSites/CDDAv21_Dyna_WM/MapServer layer 1 | nationalId / siteName, designationTypeCode | national designations in 38 countries |
| FR Géoplateforme (PatriNat) | data.geopf.fr/wfs/ows (patrinat_znieff1:znieff1, znieff2, rnr, rnn, sic, zps, pn, pnr, apb...) | id_mnhn / nom_site, url_fiche | every French registry |
| PT ICNF BDG | sigservices.icnf.pt/server/rest/services/BDG/ (RNAP, SIC, ZEC, ZPE...) | id, sigla / nome_ap | mainland PT |
| PT Azores SRAAC | wssig3.azores.gov.pt/geoserver/ps/wfs | INSPIRE id | Azores (licence differs by layer) |
| SK PCAN | gis.saskatchewan.ca/arcgis/rest/services/Planning/MapServer/20 | NAME_E, TYPE_E | SK all kinds |
| NB PNA | gnb.socrata.com/resource/bv9d-7nra.json | name, class | NB |
| EE EELIS | gsavalik.envir.ee/geoserver/ows (eelis:kr_kaitseala...) | type code | EE (CC BY 4.0) |
| NZ DOC | services1.arcgis.com/3JjYDyG3oajxU6HO/.../DOC_Public_Conservation_Land/FeatureServer/0 | NaPALIS_ID / Name, Type | NZ (CC BY 4.0). services1.arcgis.com has to pass our ArcGIS robots check first |

## Quirk table
| source | quirk | workaround |
|---|---|---|
| EEA Natura (FI and others) | some SITENAMEs stored in ALL CAPS (LIVOJARVI) | UPPER(SITENAME) LIKE |
| EEA Natura | duplicate same-name sites (two FI Lähdeneva 100 km apart; ES Puertos de Beceite SPA+SCI) | always run the distance check |
| EEA CDDA (RO) | ș stored as '?', ă stripped | use '_' wildcards |
| EEA CDDA | siteArea field can be wrong (RO B8: 38,062 ha vs a ~300 ha polygon) | trust the geometry |
| EEA CDDA | the same site appears in two inventories (CH03+CH52; SE NVR+Natura) | pick by POTA kind, cite nationalId |
| FR Géoplateforme | server-side INTERSECTS returns nothing | fetch by name, then do point-in-polygon on our side |
| FR ZNIEFF | the exact name can be type-2 while a near-name is type-1 (Vallée de l'Automne) | check both layers |
| FR | POTA names are often in CAPS without accents | accent-insensitive ILIKE |
| web-fetch sandbox | strips query strings | run from the box with curl (works; spot-checked Nov 4) |

## Ruling needed before a build
The 2-15 km band, whether CDDA counts as official (already yes under decision a), and the UK JNCC licence.
