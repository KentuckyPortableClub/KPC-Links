# Campground list builder from official campground layers (chat 10, Oct 31 2026)

Brandon, Oct 31 7:57 PM: "instructions for that?". This is the 162 official campground point layers in outside research E (`camping-us-oct31.json`, key `layers`).

Builder: the outside coder. Folder `kpc_camp_layers/`; it follows the KPC install contract (KPC_Install_Contract.md). Chat 10 installs it.

**What it is for.** Our campground bots only know the campgrounds already on our lists:
- federal ones from Recreation.gov (`data/campfed`)
- state ones (`data/campstate`, `data/campstate-manual`)
- Kentucky's hand-checked list

Many state parks, WMAs, county parks and national forests are missing. Their agencies publish campground POINT layers. This tool reads those layers and writes the missing campgrounds in the same row shape the other lists use. The bots that already exist then do the rest:
- the camp-and-activate bot (`kpc_campsites_bot.py`) decides which park each campground is in;
- the campground info bot (`kpc_campinfo_bot.py`) reads the facts from each campground's own page.

**This tool decides nothing about parks:** it only lists campgrounds.

---

## Input

- **The camping file(s).** Chat 10's intake reader puts them in `data/intake/_in/camping/camping-*.json`. `layers` = `{layer_url: parks_it_covers}`. The URL is either:
  - a plain layer (`…/MapServer/2`), or
  - a full query URL with a `where` (the Forest Service EDW "RecreationOpportunities" layer filtered to one forest and to the camping activities) and `f=html`.

  Keep the `where`. Replace `f=html` with `f=json`, and ask for `outSR=4326` and `returnGeometry=true`.
- `--states AK,AL,...`: the default is every state the layers cover. A layer's state is taken from the rows that name it, or from the points' position (the Census state outline).
- `--known data/campfed,data/campstate,data/campstate-manual`: already-listed campgrounds, used for dropping duplicates.

## What it does, per layer

1. Read the layer's metadata once: fields, geometry type, max record count, any code lists (domains).
2. Page through the features (`resultOffset`), using the query's own `where`, or `1=1`.
   - **Points** are taken as they are.
   - **Polygons** (campground loops): take the centre point, and keep the polygon too (simplified to 3 m) in `loop`.
3. **Sort each feature into one of three:**
   - **Campground (keep in the campground list):** the type, activity or name field says campground / campsite / camping / RV / tent / cabin / yurt / group camp / horse camp / primitive / backcountry / dispersed camping. Use the code lists when a field holds codes.
   - **Activating spot (keep in a SECOND list):** day-use area, picnic area, picnic shelter / pavilion, overlook. Brandon, Oct 31 8:00 PM: "might be good for points on the map ... for activating". These are often the easiest place to set up a station. They go to `<out>/dayuse/US-XX.json` with the same columns, `kind` = `day` (day-use / picnic area) or `shel` (shelter / pavilion). The access bot ties them to parks by place, like its parking points, and shows them as "Day-use area / picnic shelter (from <agency>)". A reservable shelter keeps its booking link.
   - **Leave out:** boat ramps and trailheads (the access bot already reads those from the agencies' own access layers), and anything closed for good ("decommissioned", "closed permanently").
4. **Fields per campground:**
   - `name`
   - `agency` (from the layer's service / owner text)
   - `kind` (`c` = campground, `cab` = cabins, `prim` = primitive / backcountry / dispersed, `grp` = group, `horse`)
   - `page`: the record's own URL field when there is one (e.g. `recareaurl`), else empty; never a made-up link
   - `reserve`: a booking link field when present
   - `open_status`: when present
   - `source_url`: the layer, and the record id
5. **Duplicates:** a campground within 150 m of an already-listed one with a similar name (name similarity ≥ 0.6) is a duplicate. Write it to the report and leave it out of the new rows. A name-only match more than 150 m away is not a duplicate (two campgrounds can share a name).

## Output

- `<out>/campgrounds/US-XX.json` → `{"src": "official campground layers (outside research E)", "read": "YYYY-MM-DD", "camps": [[id, name, lat, lon, kind, park, page, reserve, agency, source_url]]}`
  - The SAME first 8 columns as `data/campstate` rows, so the existing bots read it with one extra line.
  - `id` = `L-<short hash of source_url + record id>`.
  - `park` is left EMPTY: the camp-and-activate bot fills it by its own rules.
- `<out>/dayuse/US-XX.json`: the activating spots (day-use areas, picnic shelters, overlooks), in the same columns.
- `<out>/campgrounds/report.csv`: one line per layer (read OK / failed + why, features read, campgrounds kept, activating spots kept, left out, duplicates).

## Rules (from the house rules)

- **Sources:** official agency layers only (the 162). No OpenStreetMap, Google, Campendium, iOverlander or other app / crowd sources.
- **Places:** a point is a campground's location, never a park boundary.
- **Facts:** no booking availability, ever. Only the link.
- **Camping outside Kentucky:** it is shown on the site (Brandon Oct 30), but only after chat 11's YES, and it says "last checked <date>".

## Test

- **Small run:** the 5 layers that cover the most parks, then Minnesota DNR campsites and New York DEC points of interest.
- **Pass mark:** ≥ 95% of the kept features are really campgrounds (chat 11 checks a sample of 40). No picnic shelters get into the campground list (they go to the activating-spots list), and no boat ramps get in at all. The duplicates against `data/campfed` (Recreation.gov) are found.

## How chat 10 wires it

1. It runs weekly, after the intake reader. The output goes on the KPC-Data branch `tools-out` (`campgrounds/`), not main (BRANCH FIRST).
2. The camp-and-activate bot and the campground info bot read those rows like `data/campstate`.
3. Their results go through the waiting room as now, and chat 11 grades them.
4. New layers in later camping files are picked up by themselves.
