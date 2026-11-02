# Inbox: chat 8, Nov 2, 2026

## Before every push

- Take a FRESH clone; KPC-Data history was restarted this morning. Never push from an old checkout. Never force-push.
- Run `git apply --check <patch>` first.
  - If it passes, apply the patch.
  - If `git apply -R --check` passes instead, the patch is already in. Skip it and say so.
  - If neither passes, stop and tell chat 10.
- One patch, one commit, with the patch name in the message.
- Patches are in this folder under `patches/`. Paths below are relative to this folder (`H=/workspace/kpc_handoff_nov2`).

## Do

1. **G10** (KPC-Links): `G10-KPC-Links-NEEDS-OK-publish-2fers-hours-off-by-default.patch`. Apply it after G7 (the save
   helper it uses).
   - It adds the hand-started workflow "KPC 2-fer and hours publish (off until GO)" and `.github/scripts/kpc_fers_publish.py`.
   - It builds four things:
     - the 2-fer map layer, from the HQ reviewed list ONLY;
     - the 2-fer guide PDF;
     - the 2-fer GPX, which never has fewer pins than today's 116;
     - the hours on park pages.
   - Each has a switch: `KPC_FERS_LAYER`, `KPC_FERS_PDF`, `KPC_FERS_GPX`, `KPC_HOURS_PUBLISH`. Values are off, preview or on.
   - **All are off by default. Merging it changes nothing on the site.**
   **Success (merge):** the workflow is listed. A hand start with no switches set writes nothing and saves nothing.
2. **After Brandon's OK for a preview** (DECISIONS.md #1-#3):
   - Set the switch to `preview` and hand start the workflow.
   - Download the artifact. Check the layer, the PDF (it needs the Carlito/Caladea fonts, which the workflow installs) and the GPX.
   - Preview never saves anything to main.
3. **"Done"** only when Brandon says `on` AND the site shows it: the layer on the map, and the new PDF and GPX downloads work.
   **Rollback:** set the switch back to `off`, and revert the content commit on a fresh clone.

Note: the HQ reviewed list (kpc-fers-reviewed.json) is empty today, so the layer has nothing to add yet. Chat 7 (HQ) fills it.

## Needs Brandon's OK

- each of the 3 switches (#1-#3)
- which 2-fer list is the truth (#5)

## Report back (CST)

- The G10 commit id.
- For each preview: the artifact contents, the number of features or pins added, and anything that looks wrong.
