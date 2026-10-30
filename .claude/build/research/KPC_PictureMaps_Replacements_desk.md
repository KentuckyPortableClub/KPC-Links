# Picture map replacement links (Oct 30, chat 8)

Chat 10 asked (4:30 AM inbox): find new official links for 7 of 11 picture-map saves that failed.

## Fixed (3 of 7) — file as save-map requests
- **US-9652 Granada & Deadman SWA (CO)** — not dead, just a typo in our notes: it's "Granada," not "Grenada." Same URL still live: https://cpw.state.co.us/sites/default/files/dam/twchy9qgiw/granadadeadmanswa_geo.pdf (confirmed via fetch; shows an "SWA Boundary" legend line).
- **US-11944 Dankworth Pond (AZ)** — azstateparks.com blocks bots, but the park's own map PDF is also hosted on a second AZ State Parks host that isn't blocked: https://arizona-content.usedirect.com/storage/DAPO_Park Map_8-2023.pdf (confirmed, fetched successfully).
- **US-3390 River Island (AZ)** — same host, same fix: https://arizona-content.usedirect.com/storage/Park%20Map-RIIS.pdf (confirmed, fetched successfully).

## Still broken (5 of 7) — Wisconsin, systemic, not just these 5
- US-1458 Kohler-Andrae State Park
- US-4242 Fenley State Recreation Area
- US-4260 Long Lake Recreation Area (Kettle Moraine SF - Northern Unit)
- US-4261 Mauthe Lake Recreation Area (Kettle Moraine SF - Northern Unit)
- US-10644 Love and Strutt Creeks State Fish and Wildlife Area

Checked every DNR page for all 5: Wisconsin DNR hosts **every single park/forest/wildlife-area map PDF** — state park maps, Kettle Moraine unit maps, fishery-area maps, all of it — on `widnr.widen.net` / `p.widencdn.net`. That's the one host whose robots.txt we already obey (house rule: we obey robots.txt). There is no second, unblocked DNR host the way Colorado and Arizona happen to have. Kohler-Andrae doesn't even have a distinct maps page — just an `/info` page; the only PDF found anywhere for it is a third-party (trailmeister.com) copy, not an official source, so it doesn't qualify.

**Conclusion: this isn't "not found yet," it's a dead end for all Wisconsin parks, not just these 5.** Any other WI park on our picture-map or GIS-needed lists will hit the same wall. Worth flagging to HQ/Brandon once: either we accept WI picture maps stay unseeded until DNR changes hosts, or someone finds a Wisconsin open-data/GIS portal copy of the same boundary (worth a separate P-2/P-3-style GIS pass on WI DNR's ArcGIS org rather than more map-PDF hunting).
