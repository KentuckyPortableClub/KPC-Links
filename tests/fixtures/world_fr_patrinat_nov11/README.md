# SYNTHETIC test fixtures: not agency data

KPC owner, 2026-11-11 (job 6). Used only by `tests/test_world_fr_patrinat_layers_nov11.py` and
`tests/test_world_fr_patrinat_overrides_nov11.py` (through `tests/kpc_fr_patrinat_fixture.py`), offline.

- `wfs-*.json` are shaped like one GeoServer WFS 2.0 GeoJSON page from `https://data.geopf.fr/wfs/ows`
  (feature `id`, `nom_site`, `id_mnhn`, `url_fiche`). `eea-*.json` are shaped like the EEA ArcGIS answers.
- The ids, names and INPN links are the real ones named in `docs/mystery-joins-nov11-staged.json`
  (`znieff2_mer.7` / 93M000091, `cdl.502` / FR1100689, `pprnn.1` / FR9500105, the land zone `znieff1.16597`,
  the EEA records 5816, 3819 and 13497). The real `nom_site` text of the three new records was not re-read
  (no network): the names here are assumptions.
- Every geometry is a made-up rectangle placed relative to the POTA pin to reproduce the Nov 11 pin tests:
  the marine zone holds the FR-10548 pin, the land zone of the same name ends 2.61 km away, the CdL site is
  2.81 km from FR-10432, the RNN perimeter 3.50 km from FR-11106. Never use them as outlines.
- `parks-fr-subset.json` is a copy of POTA park rows from KPC-Data (real names and pins, never changed), used
  only when no KPC-Data checkout is present.
