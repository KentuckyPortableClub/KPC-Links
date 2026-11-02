# Inbox: chat 2, Nov 2, 2026

## Before every push

- Take a FRESH clone; KPC-Data history was restarted this morning. Never push from an old checkout. Never force-push.
- Run `git apply --check <patch>` first.
  - If it passes, apply the patch.
  - If `git apply -R --check` passes instead, the patch is already in. Skip it and say so.
  - If neither passes, stop and tell chat 10.
- One patch, one commit, with the patch name in the message.
- Patches are in this folder under `patches/`. Paths below are relative to this folder (`H=/workspace/kpc_handoff_nov2`).

## Do

1. **G3** (KPC-Data): `G3-KPC-Data-docs-bot-scrub-keys.patch`. This stops the documents bot from saving map links that
   carry a Google API key. Then clean the file that already has one:
   ```
   python3 $H/tools/scrub_docs_keys.py .            # dry run: lists what it would change
   python3 $H/tools/scrub_docs_keys.py . --write    # then commit "G3: remove the saved Google key from W-GB.json"
   ```
   **Success:** `grep -c AIza data/docs/W-GB.json` gives 0 on main, and it stays 0 after the next documents-bot run.
2. **Hours preview (G10)**, after chat 8 has merged G10 and Brandon has said yes to a preview (DECISIONS.md #4):
   - Set `KPC_HOURS_PUBLISH=preview`.
   - Hand start "KPC 2-fer and hours publish (off until GO)" with `only=hours`.
   - Download the artifact and read `kpc-ky-hours.changes.md`.
   - Mark every generic or doubtful line. Example: US-4572 got a national free-days fee line in the local preview.
   - Do NOT set `on`. Brandon decides that.
3. Re-give the **Canada YES** with the held build id, once chat 10 has sorted the build-id question (DECISIONS.md #11).

## Needs Brandon's OK

- the hours preview, and later the hours going live (#4)

## Report back (CST)

- The G3 commit id and the scrub tool's dry-run list.
- The hours preview: how many parks, and which lines you would not publish.
