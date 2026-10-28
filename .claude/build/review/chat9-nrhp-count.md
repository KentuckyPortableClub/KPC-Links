# National Register polygons vs POTA historic sites (chat 9, round 10, Oct 28 2026)
Source: NPS nrhp_locations/MapServer/1, asked at each POTA pin (read only, nothing added). Full rows: .claude/build/research/ADDS/round10-tested.json ('nrhp').

- Checked: 450 unmatched US historic-type parks. A Register polygon holds the pin: 129. Same name too: 41 = 19 NPS units (NPS boundary first, not from here) + **22 state/other sites**.
- **BUT 18 of those 22 polygons are 'Derived by XY event point or centroid generation'**: a shape generated around a point, not a drawn boundary, so they can never be a sure match = **pin only**. Across all 129, 112 are generated and 17 digitized.
- **4 digitized candidates** (all 'Circumscribed polygon' = a line drawn around the listed resource, so the size check against the park's published acres decides):

  - US-3454 La Purisima Mission State Historical Park (CA) -> Register 'La Purisima Mission', 931.3 acres
  - US-5748 Fort Abercrombie State Historic Site (ND) -> Register 'Fort Abercrombie', 16.2 acres
  - US-8555 Oscar-Zero Missile Alert Facility State Historic Site (ND) -> Register 'Oscar-Zero Missile Alert Facility', 17.0 acres
  - US-13183 Walking Box Ranch Historic Site (NV) -> Register 'Walking Box Ranch', 39.8 acres

- The 5 name tests (Perryville, Boonesborough, Harrod, Etowah, Stones River) returned NO rows by name: the layer's State field is probably not a 2-letter code; KY's sites are not in the US key's unmatched list (KY has its own files). Round 13 re-tests them by pin.
- 18 generated-shape same-name sites (pin only): US-6972 Historic New Harmony State Historic Site, US-9190 Marais des Cygnes Massacre State Historic Site, US-8532 Chateau De Mores State Historic Site, US-8535 Double Ditch Indian Village State Historic Site, US-8536 Fort Buford State Historic Site, US-8559 Welk Homestead State Historic Site, US-3374 Neligh Mill State Historic Site, US-3492 Willa Cather Memorial Prairie State Historic Site, US-11859 Lincoln State Historic Site, US-13280 Austin State Historical Monument, US-13282 Eureka State Historical Monument, US-12735 Saline Courthouse State Historic Site, US-6335 Cabin Creek Battlefield State Historic Site, US-6336 Honey Springs Battlefield State Historic Site, US-10273 Charles and Mary Ann Goodnight Ranch State Historic Site, US-10274 Palmito Ranch Battlefield State Historic Site, US-10275 Presidio la Bahia State Historic Site, US-6602 San Felipe de Austin State Historic Site
