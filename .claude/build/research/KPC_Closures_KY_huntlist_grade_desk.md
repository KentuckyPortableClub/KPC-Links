# KY closures super-bot with Brandon's hunt list (chat 11, Oct 29 ~11:15 AM; run 40892099744 / 40900304302, data/closures/US-KY.json)

RESULT: PASS on content, ONE data fault to fix before the ONE CLOSURES READER switch.

- Hunt list: **34 of 34 rows present** with the right start/end dates (I matched ref + from-date). 33 quota notes + 1 Tract 1 'whole' closure, as Brandon checked. Class counts: note 80, whole 1, hunt 0 (right: area-stays-open hunts are notes).
- Random 12 of 81 items: 12/12 read correctly (quota dates, 'parts of the park may be closed', Jenny Hole boats, Sinclair goose refuge, Hematite / Honker Lakes, Dog Slaughter Falls trail, fox-trial WMA). Wording stays a note, not a closure, as ruled. Bar met (100%).
- Agencies: Fish and Wildlife 62, Daniel Boone NF 7, LBL 5, Park Service 3, State Parks 3, US Fish and Wildlife 1. Nothing outside Kentucky.

FAULTS (for chat 10):
1. **10 ids appear twice with DIFFERENT dates** (e.g. US-1259 Dec 10-13 and Dec 17-20 share one id; US-1261, 1278, 1282, 1284, 3809, 3816 quota pairs; US-3793, 3808, 3828 'Part closed' pairs). If the card or the reader keys on id, one of each pair is lost or overwritten. Fix: put the from-date in every id (the 'Part closed' ones already do for some).
2. One row starts **2027-09-09** (US-10124, 'main tract closed to non-hunters Sept 9-12'). Fine as data, but make sure the card shows only items whose window is near (starts within ~14 days) so September 2027 never shows in October 2026.
3. Two rows (US-3830 x2, US-10170/10171) have no start date and expire 2026-11-05: check they are the same note counted twice.

OK to flip the ONE CLOSURES READER switch once fault 1 is fixed (no new grade needed, I will recount ids on the next Inbox).
