# World W3: JAPAN (desk, Oct 27 2026)
Format note: HQ seven points map to sections: (1) = 1, (2) = 1 and 4 (tenure), (3) = 2, (4) = 4/5, (5) = NEW grey areas, (6) = 5 and 6, (7) = SUMMARY at the top.
Grades: A = opened, B = search only, C = inference. Read only. Key = data/world-key/JP.json: 1,217 parks, only 185 joined, **1,031 no outline**, 22 pin outside; sources in key: MoE national parks (Esri Japan), MLIT natural park areas A10 (national file). HQ asked me to look for newer maps first.

## SUMMARY (READY / GAPS)
**GAPS, with no clean newer layer found.** Everything official I could open is old or has unstated terms. Best path: keep MLIT A10 for the 34+58 nature parks, add per-prefecture open data for the ~750 prefectural "Parks" (city-park style), and treat the rest as NOT SURE. Japan has **no ownership data at all** (A10 spec has no private-land field), so nothing can pass the ownership step; the run must show only the "possible, no ownership data" kind of pair (W-2).

## 1. Newer maps: what I found
| Candidate | What it is | Date / licence | Verdict |
|---|---|---|---|
| **MLIT 国土数値情報 A10 自然公園地域 (v4.1 spec)** https://nlftp.mlit.go.jp/ksj/gml/product_spec/KS-PS-A10-v4_1.pdf | national, quasi-national, prefectural NATURE parks with zones (special protection, special 1-3, ordinary incl. sea, marine). **Spec dated 14 Mar 2014**; its "time range" is FY1985 and "compiled end of Aug 2002" (A). Our world script says the national file is FY2010 (A10-10); the two statements don't match: **ask chat 2 which year the downloaded file really is** | MLIT 国土数値情報 terms: usable with credit; **non-commercial note in our script header** (C) | KEEP (it is the only complete nationwide outline), but OLD |
| **MoE Biodiversity Center "Nature Environment Information GIS: shape data download, National Park areas etc."** (e-Gov dataset env_20140904_0435) https://data.e-gov.go.jp/data/en/dataset/env_20140904_0435 | MoE's own national park shape file | first listed 2014-09-19, **last modified 2023-06-01**, update irregular, **licence not stated** (A). The biodic page text says "29 areas as of April 2010" (A: https://www.biodic.go.jp/trialSystem/EN/info/nps.html) so the 2023 date may only be the page, not the data | CANDIDATE. Ask MoE; no direct file URL in the record |
| MoE → Google (Mar 2021) all 34 national parks' GIS shown on Google Maps | press release https://www.env.go.jp/press/108305.html (A) | boundaries "may be slightly inaccurate"; **no data link or licence** | data exists, not published |
| MoE site terms | https://www.env.go.jp/nature/nationalparks/terms/ (A) | default **Public Data License PDL1.0** with credit "出典：国立公園に、行ってみよう！サイト" and "state edits"; **Geospatial Authority of Japan map images need separate approval** | PDL1.0 allows redistribution with credit (C, check text) |
| 国土数値情報 P13 都市公園 (city parks, v1.1 spec, FY2011-ish) https://nlftp.mlit.go.jp/ksj/gml/product_spec/KS-PS-P13-v1_1.pdf (B) | points for city/national-government parks | old | partial help for "Prefectural Park" |
| Tokyo Metropolitan Government open data (green/parks list) https://data.storage.data.metro.tokyo.lg.jp/toshiseibi/green_filelist.pdf (B) | Tokyo parks | updated | prefecture-by-prefecture work |
| 林野庁 national forest GIS viewer (rinya.maff.go.jp kokuyurin viewer) (B) | national forests = agency land | viewer only, no download found | best ownership source if a download exists; ask Forestry Agency |
| 国土数値情報 A45 (national forest) and A13 (forest areas) (B) | national forest area boundaries | not opened | CHECK next |

## 2. No outline (1,031)
- **Prefectural Park 789 (746 none):** Makomanai Prefectural Park JP-1013, Hokkaido kodomo no kuni JP-1014, Nopporo Sports Prefectural Park JP-1015: 都道府県立都市公園 (prefectural city-type parks). They are NOT nature parks, so A10 can't hold them. Prefectures publish park lists, a few polygons (Tokyo). Mostly **pin only**.
- **Prefectural Nature Park 306 (216 none):** Furano-Ashibetsu JP-1002, Hiyama JP-1003, Esan JP-1004: in A10 (prefectural nature parks) but **names don't match** (romanization vs Japanese). The key joins by name; the jp-wikidata.json crosswalk (data/world-key/jp-wikidata.json) may fix many. This is the biggest cheap win.
- **Quasi-National Park 58 (42 none):** Shokanbetsu-Teuri-Yagishiri JP-0101, Abashiri JP-0102, Niseko-Shakotan-Otaru Kaigan JP-0103: in A10; name mismatch (romanization). Same fix.
- **National Government Park 21 (all none):** Takino Suzuran Hillside JP-0201, Michinoku Lakewood JP-0202, Hitachi Seaside JP-0203: 国営公園, managed by MLIT; polygons not in A10; MLIT publishes a park list; pin only for now.
- National Park 36 (2 none): Kawaminami Yugaku no Mori JP-2022, Hidakasanmyaku-Erimo-Tokachi JP-2107 (new 2024 park): too new for A10.
- Prefectural Forest JP-2005, 2093, 2128: pin only.

## 3. Trails and access: Nature trails (Tokai, Michinoku Coast, Kyushu): not researched; no official lines.

## 4. Tricky land
- **Nearly all Japanese national and nature parks are zoned over private land and villages** (the A10 spec has no ownership field): a spot must be on public land; no layer says which. Rule 14 cannot run. Per W-2: NOT SURE kept out.
- National forests (国有林) are agency land and sit inside many parks; viewer only.
- Prefectural/city parks are public by definition; the polygon is missing.
- Sea zones: A10 "ordinary zone including sea" and marine park zones: water-only (rule 9).

## 5. KNOWN-GOOD layers (answer key)
1. MLIT A10 natural park areas (outer polygon + zone polygons)
2. MoE national park shape (if the 2023 file is real)
3. 国土数値情報 P13 urban parks (points)
4. Prefecture open data portals (Tokyo first)
5. National forest layer (to be found)

## 6. 2-fers to expect
Few trustworthy: NOT SURE for all pairs because there is no ownership layer. Likely overlaps from zones: a National Park vs an overlapping Prefectural Nature Park or Quasi-National Park edge (A10 shows them side by side, no real overlap); National Government Park (Hitachi Seaside JP-0203) vs the Prefectural Nature Park around it (side by side).

## NEW grey areas
| # | Question | My lean |
|---|---|---|
| W3-1 | Japan has no ownership data: show nothing for Japan, or a members-only "possible" list? | Members-only "possible, no ownership data" list (W-2). |
| W3-2 | 746 prefectural city parks with no polygon: pin only? | Pin only; no 2-fer test. |
| W3-3 | Non-commercial MLIT terms vs public repo. | Link to MLIT and store our own simplified outline with the credit line; ask chat 2 to confirm the terms text. |
