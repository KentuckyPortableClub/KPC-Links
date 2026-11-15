# Synthetic outline store, index contract kpc-outline-store-index/4 (format 4)

Made-up squares and made-up park refs (US-99001 to US-99006); no real park outline, record or tile is in these files. One area, US-RI:
- US-99001 Test Forest and US-99002 Test Inner Park: area records, the inner park inside the forest (an overlap on land);
- US-99003 Test Lake Park and US-99004 Test Lake Area: area records whose overlap lies wholly in the one water tile (water only);
- US-99005 Test Trail: a `line` record (trail_100ft) across the forest;
- US-99006 Test Pin: a `pin` record only (never a boundary);
- `water/us-nhdplus-hr/-716_416.json.gz`: one water tile (the bot's own tile form), listed with its sha256 in `water/index.json`.
Used by tests/test_fers_store_switch_nov15.py.
