# Inbox: chat 11, Nov 2, 2026

You apply no patches. You give the verdicts and run the checks that make the rollout count.

## Do

1. **Quote the build id in every key verdict** (YES or NO).
   - The held US and CA builds carry `f3d48d30899`. A verdict without the id is skipped by the release step.
   - Wait for chat 10 to confirm the id is real before giving a new YES (DECISIONS.md #9).
2. **Fresh YES needed.** Any YES from before this morning's history restart (7:28 AM CST) should be given again, with the
   build id (DECISIONS.md #10).
3. After **G1 + G11** are live (chat 10), check the next waiting-room restart:
   - it runs the release and the key doctor (the scheduled path), not `replay`;
   - your NOs from Nov 1 2:28 PM and Nov 2 2:16 AM landed in overrides.json (the key doctor's `nos` report says so).
4. After **G8** is live, a lost save shows as a notice. If you see `::error title=Save::` on a run that touched your
   inbox, tell chat 10.

## Needs Brandon's OK

- whether a pre-restart YES still counts (#10)

## Report back (CST)

- Your verdict lines, with build ids.
- The waiting-room restart you checked (link and time) and what it did.
