# Inbox: chat 3, Nov 2, 2026

## Before every push

- Take a FRESH clone; KPC-Data history was restarted this morning. Never push from an old checkout. Never force-push.
- Run `git apply --check <patch>` first.
  - If it passes, apply the patch.
  - If `git apply -R --check` passes instead, the patch is already in. Skip it and say so.
  - If neither passes, stop and tell chat 10.
- One patch, one commit, with the patch name in the message.
- Patches are in this folder under `patches/`. Paths below are relative to this folder (`H=/workspace/kpc_handoff_nov2`).

## Do

1. **G2** (KPC-Links): `G2-KPC-Links-honest-user-agent.patch`. kpc_ky_maps.py and kpc_linkcheck.py stop sending a browser
   User-Agent (the Oct 31 ruling).
   **Success:** the next run log of either script shows the KPC User-Agent, and no "Chrome" or "Safari".
2. **G6** (KPC-Links), only after Brandon's OK (DECISIONS.md #7):
   - Patch: `G6-KPC-Links-NEEDS-OK-no-key-fallback.patch`, which changes 120 pages.
   - Apply it last, after G1-G11. It also applies on top of them.
   - It removes the pages' fallback to held answer keys in KPC-Links. 51 world-key countries would disappear from the
     site until they are released.
   **Success:** a held country is gone from the site and a released one still shows. Spot-check 3 pages.
   **Rollback:** `git revert` on a fresh clone.
3. The T5 site checker still has 60 failed checks waiting on your 404 fixes (from the review).

## Needs Brandon's OK

- G6 (#7)

## Report back (CST)

- The commit ids and the run logs that show the User-Agent.
- For G6: Brandon's OK time, and the pages you checked.
