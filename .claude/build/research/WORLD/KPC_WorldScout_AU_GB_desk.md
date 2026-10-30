# World 2-fer scout: W2 Australia, W1 United Kingdom (chat 8, Oct 30 2026)
Per Brandon's 5:51 AM GO (notes/world-stages.md, RESUMED), chat 2's 5:55 AM ask. Same format as a US state source book: official public/Crown land layer, licence, grey areas, known-good 2-fers to expect, new W-rule gaps. Grade B (service pages + metadata read; not yet point-tested against park pins — that's chat 9/11's P-2 step once chat 11's AU world-finder key is live).

## AUSTRALIA (W2) — public-land source = state Crown land tenure layers, one per state/territory
Australia has NO single national Crown-land layer; each state runs its own cadastre/tenure dataset. All found so far are official government sources, CC-BY licensed (W-5 clear).

| State | Layer | Licence | How it marks public/Crown land | Access |
|---|---|---|---|---|
| NSW | NSW Land Tenure (SEED, data.nsw.gov.au) | CC-BY | `Tenure Class` field: Crownland-Leasehold / Crownland-Other / Private / Indigenous Owned / National Park / State Forest / Unresolved — use everything NOT "Private" | GDB download (SEED); no REST found yet |
| Victoria | Vicmap Crown Land Tenure (data.vic.gov.au / discover.data.vic.gov.au) | CC-BY 4.0 | the dataset itself IS Crown land (tenure types = Agricultural/Lease/Licence/Reserve etc., all held by the Crown) | DWG/DXF/GDB/SHP download via datashare.maps.vic.gov.au; a WFS (`CL_TENURE_VIEW`) is referenced in the Discover Data Vic catalogue |
| Queensland | Queensland land tenure (data.qld.gov.au / QSpatial) | to confirm | tenure classification incl. Crown/reserve/freehold | to confirm (search turned up a 1937 mining-tenure historical map first; need the current QSpatial layer, not yet pinned down — **leave as a to-do for chat 9's P-2 pass, not a dead end** |
| WA | Land Tenure (data.wa.gov.au, dataset id 226) | to confirm | tenure classification | catalogue page found, fields not yet read |
| Tasmania | LIST Land Tenure + LIST Crown Leases + LIST Crown Licences (thelist.tas.gov.au) | to confirm | separate Crown-leases/licences datasets from the general tenure layer | `services.thelist.tas.gov.au/arcgis/rest/services/Public/CadastreAndAdministrative/MapServer` — a LIVE ArcGIS REST endpoint exists, best of the six for machine point-tests |
| SA, NT | not found yet this pass | — | — | next scout pass |
| National fallback | ABARES "Tenure of Australia's Forests 2018/2021" (`gis.environment.gov.au/gispubmap/rest/services/abares/AustLandTenure2021/MapServer`) | Commonwealth, to confirm | forest-only, coarse tenure classes (not every park is forest) | LIVE ArcGIS REST — useful only where a state layer is missing/unclear, forest parks only |

**Known-good 2-fers to expect (AU):** chat 11 already answered the AU slice of the world-finder (268 YES overall, mostly Victoria). Real examples from that batch (Victoria small reserves sharing a boundary or adjacent, per chat 11's Oct 29 11:56 PM note): expect several Streamside Reserve / Bushland Reserve / Gippsland Lakes Reserve pairs once the rebuilt key is live — exact pairs are chat 11/2's to name once the key lands; I have not independently verified specific pairs this pass (grade C on examples, grade B on the layers).

**Grey areas (AU):**
- **G-W-AU1:** Queensland and WA layer schemas not yet confirmed (field names, whether REST exists) — needs one more pass before chat 9 can P-2 test those two states. Not a blocker for Victoria/NSW/Tasmania to start.
- **G-W-AU2 (existing W-2):** National Park / State Forest classes inside a Crown-tenure layer are clearly public — straightforward. "Indigenous Owned" (NSW) sits in a grey zone: publicly gazetted but not Crown-held in the usual sense — recommend treating as NOT SURE unless Brandon rules otherwise (same spirit as W-3's "right to roam ≠ public" caution: ownership type matters, not just "not private").

## UNITED KINGDOM (W1) — public-land source splits by country; England ≠ Scotland
**England: CRoW Act 2000 Open Access Mapping Areas (Natural England/DEFRA).** LIVE ArcGIS FeatureServer: `https://services.arcgis.com/JJzESW51TqeY9uat/ArcGIS/rest/services/CRoW_Act_2000_Open_Access_Mapping_Areas/FeatureServer` (related layers at the same host: `CRoW_Act_2000_Section_15_Land`, `CRoW_Act_2000_Section_16_Dedicated_Land`, Section 4 Conclusive Registered Common Land / Open Country). Government dataset, open licence (Open Government Licence, standard for data.gov.uk/Natural England layers). This is genuinely "the public may walk here," set in law — works as England's public-land source under W-3 as written.

**Scotland: open-access land is NOT the right source — new grey area, flag to Brandon.** notes/world-stages.md's plan ("England/Scotland open-access land = public-land source") runs into our own rule W-3 ("right to roam is NOT public land"). Scotland's Land Reform (Scotland) Act 2003 gives a statutory right of responsible access to almost ALL land and inland water, regardless of who owns it (with narrow carve-outs: gardens, buildings, some operational land). So "open access land" in Scotland isn't a public-land layer at all — it's close to everywhere, exactly the W-3 trap. **Recommend instead:** Forestry and Land Scotland's **National Forest Estate Legal Boundary Scotland** (spatialdata.gov.scot, record `cb43b17d-9127-4b1d-9d17-d58ce1ab122b`) — this IS actual public ownership (FLS is the Scottish Government agency that owns/manages it), a proper W-2-style public-land polygon layer, same idea as a US state forest layer. There's also a companion "National Forest Estate Ownership Scotland 2019" layer and "National Forest Estate Forest Parks GB" (covers forest parks specifically, which is likely where most Scottish POTA 2-fers would sit). All on spatialdata.gov.scot (Scottish Government's own geonetwork), licence not yet confirmed — check for Open Government Licence before use (W-5).

| Country | Layer | Licence | Notes |
|---|---|---|---|
| England | CRoW Act 2000 Open Access Mapping Areas | OGL (to confirm exact wording) | LIVE FeatureServer, ready for P-2 now |
| Scotland | National Forest Estate Legal Boundary Scotland 2019 (FLS) | to confirm | recommended REPLACEMENT for "open access land" — see G-W-GB1 below |
| Wales | not scouted yet | — | Natural Resources Wales runs its own open-data portal (datamap.gov.wales); next pass |
| Northern Ireland | not scouted yet | — | DAERA; next pass |

**Grey areas (GB):**
- **G-W-GB1 (new, for Brandon):** Scotland's "open access land" is not usable as a public-land source under our own W-3 rule — it's closer to a universal right than a land-ownership marker. Recommend swapping Scotland's source to FLS's National Forest Estate (actual public ownership) instead, same approach as a US state-forest layer, and treating Scottish Natural Heritage / NatureScot reserves as additional (smaller) public-land spots. Needs Brandon's yes before chat 2 wires it in, since it changes the plan world-stages.md already wrote down.
- Wales and Northern Ireland are not yet scouted; England + Scotland cover the bulk of UK POTA activity (42,831 activations) so I'd start there and come back for Wales/NI before calling W1 "done," per Brandon's one-country-at-a-time pace.

## Bottom line
Australia: ready to start on Victoria + NSW + Tasmania now (all three have a real Crown-land layer with a licence); QLD/WA/SA/NT need one more scouting pass, not blocking. United Kingdom: England is ready now (live FeatureServer); Scotland needs Brandon's ruling on G-W-GB1 before chat 2 wires anything, since the obvious source (open-access land) fails our own W-3 test; Wales/NI still to scout.
