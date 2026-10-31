# GPS download: build spec (chat 10, Oct 31 2026)

Brandon, Oct 31 6:45 PM: "instructions for using our parking and maps to build a download gps for people to use".

**Goal.** Anyone using our tools can download a file their GPS or phone map app opens. It holds:
- the park pin;
- the official parking / access points;
- the park's outline;
- the trail line (for trail parks);
- optionally the 2-fer overlap spots.

It comes in three sizes:
1. **one park**
2. **one trip** (the planner's stops)
3. **a whole state pack**

Who builds:
- **The site parts (A, B):** chat 3, the website chat, or the outside coder; the parts are small JavaScript.
- **The state packs (C):** a chat 10 bot.

Pieces that already exist:
- `finder.js` `gpx()` (KY rove file)
- the trip GPX in the planners
- `kpc-bounds.js` (draws every outline)
- the access points (`data/access/*.json`, Kentucky's `ap` in kpc-ky-data.json)

---

## The data that goes in (and its label, which must travel with it)

| Item | Where it comes from | Label in the file |
|---|---|---|
| Park pin | POTA's pin (data/parkinfo) | `<ref> <park name>` + "POTA pin (activations happen inside the boundary, not at the pin)" |
| Official parking / access | data/access/<area>.json (Kentucky: 'ap') | "Parking (from <agency>)", "Entrance", "Boat ramp", "Trailhead" (the text after the colon in the point label) |
| Nearby, not the park's own | points the access file marks outside the line | "Nearby public access, not the park's own" (rule 16) |
| Possible pull-off (later, after the pull-off finder + chat 11) | data/access candidates with YES | "Possible pull-off (aerial photo, not official)" |
| Outline | the same source the map draws: official / approximate / picture-map trace | "Official boundary (<agency>)", "Approximate outline (<why>)", never shown for "pin only" |
| Trail line | the trail layers the site already draws | "<trail name> (official line, <agency>)" |
| 2-fer spots (optional box, default OFF) | data/fers rows for that park | the SHORT 2-fer notice, word for word, in the description |

**Every file starts with the SHORT information notice in its description**, word for word: "ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go." It also gives the date the data was built and the site link. If 2-fers are included, the SHORT 2-fer notice follows: "⚠️ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it."

## Formats (offer all three; GPX is the default)

1. **GPX 1.1.** Garmin handhelds and car units, most phone apps.
   - **Points:** `<wpt>`; the name is ≤ 30 characters. Put the full name in `<desc>` because older Garmins cut names short.
   - **Symbols:** `<sym>Parking Area</sym>`, `Trail Head`, `Boat Ramp`, `Flag, Green` (park pin), `Information` (entrance).
   - **Lines:** outlines and trails go in as `<trk>`: one `<trkseg>` per ring or piece, closed. The track name is "<ref> boundary (Official)".
   - **Size limit:** many Garmins cap a track at 10,000 points and hold about 200 tracks. Simplify each outline for the GPX copy to ≤ 2,000 points, 5 m first, then coarser, and say the detail in `<desc>` ("simplified to ~N m for GPS units").
2. **KML.** For desktop map programs.
   - Outlines go in as real polygons (`<Polygon>`): light fill, yellow line for official, dashed for approximate.
   - Points get icons; there is one folder each for Parking / Trails / Outline / 2-fers.
   - The notice goes in the document description.
3. **GeoJSON.** For people who make their own maps: the same content and labels, as properties.

The file name is `KPC_<ref>_<short-name>_<YYYY-MM-DD>.gpx`, or `KPC_trip_<date>.gpx`, or `KPC_<state>_parks_<date>.gpx`.

## A. One-park download (site, small)

- **The shared builder.** A new small file, `kpc-gps.js`, the one place the files are made (no copies in other scripts):
  - `KPCGPS.park(ref, opts) → {gpx, kml, geojson}`
  - `KPCGPS.trip(stops, opts)`
  - `KPCGPS.download(text, filename, mime)`

  It reads the same data the cards read: `KPCB` for outlines; `KPC.dataUrl` for the access files (KPC-Data first, then the site's copy).
- **The button.** A "⬇ GPS" button on every park card: Park Info, Kit, the US / KY trip planner card, Am I in the Park, the Overlap Finder card. Tapping it shows a small chooser: GPX (Garmin / phone) · KML (Google Earth) · GeoJSON, plus a tick box "include 2-fer spots".
- **Pin-only parks:** the file still downloads, with the pin + parking and the line "No official outline yet".
- **No server:** the file is built in the browser, so it works offline once the page has loaded the park.

## B. Trip download (site)

The planners' existing trip GPX becomes `KPCGPS.trip()`: every stop's pin + its parking points + its outline (optional box), with the route order kept as a GPX `<rte>` (stops only, no turn-by-turn).

## C. State packs (bot, chat 10)

- **The bot.** A nightly KPC-Data job (only when a key or access file changed) builds `data/gps/<area>.gpx.zip` + `.kml.zip`: every park in the state with its pin, parking and outline. Trails are a separate pack, `data/gps/<area>-trails.gpx.zip`, so the main pack stays small.
- **Size target:** ≤ 5 MB a state zipped, with outlines simplified for GPS units as above. Kentucky first, then the US, Canada and the world.
- **Storage:** on the KPC-Data side branch `gps-packs` (rebuilt and squashed weekly, so it never grows the history). The site links to them through `KPC.dataUrl`.
- **A page that lists the packs:**
  - "GPS downloads", a new page;
  - **HOLD RULE:** Brandon's GO before it is public and before it goes in the menu; members-only until then;
  - the full information notice sits at the top.

## Testing (before Brandon's GO)

1. **Format check:** every GPX passes the GPX 1.1 schema check (xmllint against the topografix XSD) and every KML opens in a KML validator.
2. **Real devices:** import 3 files (one park, one trip, Kentucky's pack) into Garmin BaseCamp (or a Garmin unit) and one phone app. Points show with the right icons; outlines show as closed lines; names are readable.
3. **Labels:** the notice is there; official / approximate / pin-only are labelled correctly; "Nearby public access, not the park's own" is on the outside points. Check 10 parks against their cards.
4. **Phone:** the button and the chooser work at 390 px with no sideways scroll; the download works on Android Chrome and iPhone Safari (iPhone opens a share sheet: fine).
5. **Rules:** nothing from OpenStreetMap / Google is in any file. 2-fer spots appear only with the box ticked, and always with the 2-fer notice.

## Order of work

1. `kpc-gps.js` + the one-park button on Park Info (chat 3 or the outside coder).
2. The trip download.
3. The state-pack bot (chat 10).
4. The GPS downloads page (Brandon's GO).
5. The pull-off candidates join the files after the pull-off finder's rule sheet is ruled and chat 11 grades them.
