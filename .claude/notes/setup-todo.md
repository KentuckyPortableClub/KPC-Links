# Setup list: things only Brandon can do (keys, permissions, rooms)

Claude's sessions CANNOT set GitHub secrets (the proxy blocks that API), so every item here is a few taps
for Brandon. Nothing on this list is urgent; each one just turns on a bot that is already built and waiting.
Tick them off as they are done, newest notes at the bottom of each item.

## 1. Facebook token — lets the comment watcher see comments  (Oct 21)
WHY: kpc-fb-comments.yml is built and running, but Facebook says
  "(#10) This endpoint requires the 'pages_read_user_content' permission".
The saved token has pages_manage_posts, pages_read_engagement, pages_show_list, public_profile — it can POST
but not READ what people write underneath.
WHAT TO DO: make a new Page token that also has **pages_read_user_content**, then update the GitHub secret
`FB_PAGE_TOKEN` (GitHub → Settings → Secrets and variables → Actions). Nothing else changes; posting carries
on either way. Claude can walk through it step by step.
STATUS: waiting.

## 2. National Park Service key — adds the national parks to the closure watcher  (Oct 21)
WHY: kpc-park-alerts.yml already watches Kentucky State Parks. The NPS part is written and skipped until there
is a key, so Mammoth Cave, Cumberland Gap and Big South Fork are not covered yet.
WHAT TO DO: get a free key at developer.nps.gov (name + email, arrives by email in a minute), save it as the
secret `NPS_API_KEY`. No other change needed; the bot picks it up on its next run.
STATUS: waiting.

## 3. A quieter room for 'somebody is waiting on us' posts  (Oct 21, optional)
WHY: every bot post (park alerts, approvals, what's new, Facebook comments) goes to `KPC_DISCORD_WEBHOOK`,
the same room as recaps and milestones. Brandon may want the ones that need a person in their own room.
WHAT TO DO (only if he wants it): make a webhook for that room, save it as a new secret, tell Claude the name.
STATUS: not decided.

## 4. Watching the Discord rooms for questions nobody answered  (Oct 21, Brandon asked for this)
WHY: 'can discord also notify us if someone needs something from us' — he meant the club's own Discord rooms:
somebody asks for help in a member room, everyone is out at a park, nobody sees it for days.
WHAT TO DO: (a) Brandon says WHICH rooms to watch; (b) the relay bot account needs View Channel +
Read Message History in those rooms (it already has the Message Content intent for the posting channel).
No new secret: it reuses DISCORD_BOT_TOKEN.
THEN CLAUDE BUILDS: a job that flags a message that looks like a question with no reply after about an hour.
STATUS: waiting on the room list.

## Already done (do not redo)
- ANDROID_KEY_PASSWORD (app signing), FB_PAGE_ID + FB_PAGE_TOKEN (posting), KPC_DISCORD_WEBHOOK,
  KPC_YOUTUBE_WEBHOOK, RELAY_DISCORD_WEBHOOKS, DISCORD_BOT_TOKEN + KPC_RELAY_CHANNEL,
  RELAY_MAIL_URL + RELAY_MAIL_KEY (club mailer), GROUPSIO_TO, SUBSCRIBE_SHEET_CSV,
  the form sheets NOTES_SHEET_CSV, COMMUNITY_SHEET_CSV, CAMPGROUND_SHEET_CSV, KPC_REPORTS_CSV,
  KPC_ACTIVATIONS_CSV, KPC_GUESTBOOK_CSV, KPC_CWBOARD_CSV, RIDB_API_KEY,
  kpc-gdrive.json clientId (Google Drive backup).
- GitHub → Settings → Notifications → Actions → 'Only notify for failed workflows' (asked Oct 18; confirm it is ticked).
