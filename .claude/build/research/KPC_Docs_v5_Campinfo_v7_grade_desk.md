# Documents bot v5 + campground info v7 (Kentucky) — chat 11, Oct 28 ~4:20 PM CDT
## DOCUMENTS v5 (KY TN NC VA WV GA AL SC all ver 5; FL 318 of 460 done): maps PASS, recall fell
- All four bulk faults are GONE: WV whitewater rules 83->0, GA publuu 130->0, FL shooting-range 53->0, VA inciweb maps 26->0; map links shared by >20 parks: 0 (VA's 26 are now 'no map (one file shared by 2...)'); error-link maps kept: 0-1 per state.
- Random 12 maps (seed 123, 487 with a map): **A 9, B 2, C 1 = 92% PASS.** A: Beaman Park, Rockfish Creek SGL, Wright Brothers, Little River Canyon, Channels SF, Rhodes Pond SGL, Yadkin River Trail, SW Virginia Museum SP, Little River Canyon-style NPS pages; B: St. Stephens (a local historic-site website, not the agency), Pike County Pocosin (agency 'hunting maps' page); **C: Little River State Forest = forestry.alabama.gov 'Wildfires' page.**
- Rules pages: the remaining 'shared' ones are an agency's own page for its parks (floridastateparks rules x175, TWRA WMA rules x175, parks.ky.gov x47, gastateparks x53): FINE if labelled 'agency rules'. Still wrong: Beaman Park (Nashville) -> 'athletics/court-rules'; LBL -> usda.gov policies page; AL forest -> state admin code.
- **Recall regression:** maps with a link: VA 162->91, WV 163->36, GA 218->108, NC 112->121(+), KY 83. 127 WV and 109 GA parks now say 'no working map link (tried: opened, a readable map that does not name this park)'. Those are the WV WMA PDFs (Teter Creek, Dunkard Fork: file name carries the park) that I graded A on Oct 28 and nothing wrong. Fix: a readable map whose FILE NAME or heading carries the park name = 'ok (name in file)'; keep it.
- TN 245 and SC 129 parks: 'no map link on file and none' (recall gap, honest).

## CAMPGROUND INFO v7 (Kentucky, 100 camps; own gate PASS): accuracy FAIL on facts, recall thin
Random 10 (seed 31): 6 are federal USACE/FS rows with ONLY an elevation (no sites, hookups, fee, phone, booking) = empty, not wrong. 4 hand-key rows with facts: 
- Kentucky Horse Park: **fee = "$5 Million Renovation to Enhance Visitor Experience"** (a dollar figure from a news headline; the campground_page is that news article) = C.
- Energy Lake: 'cabin 13' (looks like the old '13 sites' copy bug) and its campground_page is the **Hillman Ferry** page = C.
- Wranglers: 'cabin 12' (same pattern; sewer/water true, amps 30/50 plausible) = suspect.
- Self-service lakeside: $12/$26/$10 per night, 30 amp = plausible A.
Score on records WITH facts: 1 A of 4 (25%). All 100 records carry the cell block 'FCC 0 mobile coverage files for the state (point lookup = step 2, not built)' = useless field on every record.
## Fixes (chat 10)
1. Docs: keep a readable map when the file name/heading carries the park name; reads in WV WMAs/GA WMAs should recover ~230 maps. Label agency-wide rules pages 'agency rules' and drop pages whose URL has court-rules / policies-and-links / admin code.
2. Campground: a fee must come from the camp's own fee table/section, never a headline (reject '$ N Million', 'Renovation'); a news/blog URL is never campground_page; 'cabin' count only from a sentence with the word cabin; Energy Lake/Piney/Wranglers pages must be their own LBL pages (not Hillman Ferry); the 60 federal rows with only elevation need the RIDB/NPS read; drop the cell block until the point lookup exists.
