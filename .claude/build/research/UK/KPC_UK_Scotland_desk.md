# United Kingdom: SCOTLAND (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only; I could not query polygons. UK RULES: official sources first; WDPA never; a whole-line park (National Park, National Landscape/AONB, NSA, SSSI, SAC/SPA) is mostly private land, so a spot needs public land (World rules W-2/W-3: right to roam does NOT make land public); forests/MoD/charity land = "agency land" only with an ownership layer. Key = data/world-key/GB.json (7,074 parks, 2,804 with no outline, 1,073 pin outside the outline, 982 to check).
## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| Country parks, NNR, LNR, SSSI, Ramsar, SAC, SPA | NatureScot (WFS) via spatialdata.gov.scot / data.spatialhub.scot | NatureScot | OGL (B) | IN KEY (cpk, nnr, lnr, sssi, rp, sac, spa) |
| **National Parks (Cairngorms, Loch Lomond & The Trossachs) and National Scenic Areas** | NatureScot "National Parks" and "National Scenic Areas" layers (B, not opened) | NatureScot | OGL (B) | **NOT IN KEY.** Loch Lomond and The Trossachs National Park GB-0930 is NONE; Cairngorms NP GB-0835 is joined (via another layer, C). The 136 Scenic Sites (Ben Nevis and Glen Coe GB-0825, Jura GB-0912, North Arran GB-0953) are National Scenic Areas |
| **Forestry and Land Scotland national forest estate** | https://spatialdata.gov.scot/geonetwork/srv/api/records/cb43b17d-9127-4b1d-9d17-d58ce1ab122b (A) | FLS (via Forest Research) | **OGL**, annual, but **coverage 2008-2019 on the record (old)**, "current land holdings", cost centre + district only; OS acknowledgement required (A) | NO. Galloway Forest Park GB-1370 (NONE) |
| Scotland\'s Great Trails | NatureScot "Scotland\'s Great Trails" line layer (B) | NatureScot | OGL (B) | NO (West Highland Way GB-1472, Great Glen Way GB-1459, Loch Lomond & Cowal Way GB-1463, Mull of Galloway Trail GB-1464 joined?) |
| Core paths | council by council | | | NO |
## 2. No outline
- GB-0930 Loch Lomond and The Trossachs NP; Galloway Forest Park GB-1370; Biosphere Reserve (Galloway and Southern Ayrshire GB-0885, UNESCO zone: pin); North West Highlands Geopark GB-3366 (pin).
- National Scenic Trails and Great Trails (Scotland uses "Great Trail" labels): lines.
- Moffat Community Nature Reserve GB-6865: community-owned, small.
## 3. Trails / access
**Scottish Outdoor Access Code (Land Reform (Scotland) Act 2003): statutory right of responsible access over most land** (B). Per W-3 this does NOT make private land public for rule 2, but means "check you may be there" notes fit.
## 4. Tricky land
- **Estates and stalking:** closures in stalking season (Aug 20 to Oct 20 for deer) are in no layer. SHORT notice only.
- **Community ownership (land reform buy-outs):** public use but private body: ask Brandon (UK-1).
- **Forest Park (FLS) is public land with a statutory owner (Scottish Ministers):** a clear case where the 2-fer test can use ownership.
- **National Park (LLTNP) contains FLS land (Queen Elizabeth Forest Park) and loch water (Loch Lomond NNR GB-0929, Ramsar GB-3076, RSPB reserve GB-2926):** water + land mix, rule 9.
## 5. KNOWN-GOOD
1. NatureScot NNR, LNR, SSSI, country parks (in key)
2. NatureScot National Parks + NSA (add)
3. FLS national forest estate (OGL, **check it is current**)
4. Scotland\'s Great Trails
5. OS Open Rivers / NHN equivalent for lochs (see Summary)
## 6. 2-fers
Confident (C): Loch Lomond NNR GB-0929 vs Loch Lomond Ramsar GB-3076 vs Loch Lomond RSPB GB-2926 vs the National Park GB-0930 (same shore; water-only parts). Cairngorms NP GB-0835 vs Cairngorms NNR GB-0836 (layered; NNR is public). Hard: Ben Nevis SSSI GB-1739 vs Ben Nevis and Glen Coe Scenic Site GB-0825.
