# KPC rollout handoff, Nov 2, 2026 (from the general system review)

Start with PLAN.md. Then read your own note (chat-2.md, chat-3.md, chat-7-HQ.md, chat-8.md, chat-10.md, chat-11.md).
DECISIONS.md lists what needs Brandon's OK. Nothing here is pre-approved.

- `patches/`: the patch files (G1-G11). Apply them with `git apply` at the root of the repo named in the file name.
- `PATCHES.md`: what each patch does. `tests/`, `tools/`, `reports/`, `orig/`: the checks and reports behind each patch
  (`tools/rebuild_stack.sh` only works in the original review folder).
- Everything was made and tested on a local copy only. Nothing has been pushed anywhere.

Copies the patches were made against: KPC-Data main e0c674ac (Nov 2, 8:45 AM CST), KPC-Links main 8e291ec2 (Nov 2,
8:40 AM CST).

**IMPORTANT: KPC-Data's history was restarted (squashed) this morning. Before every push, take a FRESH copy (a new clone,
not an old checkout). Run `git apply --check` on it first. If a check fails, stop and report it. Never force-push, and
never push from an old clone. Pushing from an old clone brings back the old history or loses newer work.**
