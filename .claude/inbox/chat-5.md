# CHAT 5 INBOX (bots + Discord/Facebook, Opus)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- (Oct 28 7 AM, chat 5: READY; one-time workflow kpc-release-post.yml + data/release-post.txt (exact text) built; chat 5 starts it at 8:00 AM CDT; it records each place in data/kpc-club-posts-state.json 'release_post' so it can never post twice.)
- HQ (Oct 28 6:50 AM) — BRANDON'S GO, SEND AT 8:00 AM CDT (Brandon told chat 5 at 6:52): POST THE WEBSITE RELEASE STATEMENT ONCE to Discord (the general/announcements webhook) AND the Facebook Page (Page ID 1342190728983628, never Groups), text below EXACTLY as written (no additions, no logo). One post each, never twice (record it in the bot state); a text post (no picture needed; use the KPC logo card only if the posting code requires an image). Confirm both posted (post links/ids) in your report.
```
📻 The Kentucky Portable Club website is now open to everyone!

Whether you hunt parks from home or head out to activate, there's something here for you:

🎯 Hunters Lounge: who's on the air right now, spots, and a Park Checker to see which parks you still need.
🏕️ Activators Lounge: trip planning, park notes, campgrounds, and an Activation Board.
📍 Am I in the Park? and the Activation Kit: check where you are and get ready before you go.
📅 The Kentucky Radio Calendar: hamfests, contests, QSO parties and club events in one place.
⚠️ Park closure heads-ups for Kentucky, so you don't drive to a locked gate.

More is on the way.

ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.

👉 https://kentuckyportableclub.github.io/KPC-Links/

73 de N4KPC, the Kentucky Portable Club
KPC is an independent ham radio club, not part of Parks on the Air®, SOTA or WWFF.
```

- (Oct 28 8 AM, chat 5: BUILT in PREVIEW: 'ga-wrd' source in kpc_us_closures.py; first real read at the 8:23 AM KPC-Data closures run lands in KPC-Data data/alerts/us-parks.json sources['ga-wrd'].preview (nothing on cards yet); next inbox: compare with the live page, then switch GA_LIVE on.) HQ (Oct 28 7:09 AM): GEORGIA CLOSURES: Brandon ruled GA5-GA9 YES (website.md); chat 8's fixes GA-R1..R9 are in KPC_RuleSheet_GA_closures_desk.md. BUILD it (after the 8 AM release post), Kentucky's reader untouched, test on today's live page incl. chat 8's traps (negations, split sentences, end-dated Cohutta).

## NEEDS BRANDON

## DONE
- Oct 28 5 AM: hourly spotter watched: 3 runs (started 07:47, 08:39, 09:36 UTC; GitHub starts the :02 job ~40 min late), each ran its 12 checks for ~50 min and ended green; gaps between runs 2-6 min, covered by the 60-min look-back, so nothing is missed. No KPC operator was spotted overnight, so no alert went out and the state file did not change (no saves): a real alert is not seen yet; I'll look again at the next inbox.

## REPORT TO HQ (newest first)
- Oct 28 5 AM (chat 5): spotter = fine so far (3 hourly runs, green, ~50 min each, no gaps that matter, nothing double-posted, no alerts overnight to test with). Georgia closures: built nothing yet, waiting for chat 8's break of the sheet (Brandon's GA1-GA4 rulings noted). Also: KPC-Data's overnight EU warnings / US closures / merge runs fired green (B5).
