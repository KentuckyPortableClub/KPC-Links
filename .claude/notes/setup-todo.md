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
STATUS: **DONE Oct 21 08:46.** Token now: right Page (KPC), type PAGE, scopes pages_manage_posts +
pages_read_engagement + pages_read_user_content + pages_show_list, **expires never**, and comments read fine.
WHAT WENT WRONG ON THE WAY, so nobody repeats it: (1) the permission has to be picked from the 'Add a Permission'
list in the Explorer's right-hand column, not typed; (2) 'Generate Access Token' gives a USER token, which cannot
post as the Page — switch to a Page token, or run `me/accounts` in the Explorer and take the token from the list;
(3) `me/accounts` lists EVERY page the account runs, and the first block was KZ4CP, not the club — match on
"name": "Kentucky Portable Club" / "id": "1342190728983628" and take the access_token from that same block;
(4) a page token only lives as long as the user token behind it, so it must be run through
developers.facebook.com/tools/debug/accesstoken → Extend Access Token, or it dies within the hour.
A posts-only token cannot read comments, and a wrong-page token will happily post to the wrong page, so the
check in kpc_fb_comments.py now prints the page name, the token type, the scopes and the expiry every run.

## 2. National Park Service key — adds the national parks to the closure watcher  (Oct 21)
WHY: kpc-park-alerts.yml already watches Kentucky State Parks. The NPS part is written and skipped until there
is a key, so Mammoth Cave, Cumberland Gap and Big South Fork are not covered yet.
WHAT TO DO: get a free key at developer.nps.gov (name + email, arrives by email in a minute), save it as the
secret `NPS_API_KEY`. No other change needed; the bot picks it up on its next run.
STATUS: waiting.

## 3. A room for the 'somebody is waiting on us' posts  (Oct 21 — NEEDED, not optional)
WHY: KPC_DISCORD_WEBHOOK turns out to point at **#kpc-pota-spots**, the spots room. On Oct 21 the Facebook
comment bot's 'one permission short' note landed there in front of everyone. Admin posts do not belong there.
DONE ALREADY (Claude, Oct 21): kpc_fb_comments.py and kpc_approvals.py now use **KPC_ADMIN_WEBHOOK** when it
exists and fall back to KPC_DISCORD_WEBHOOK when it does not. Park alerts and 'what's new' stay in the normal
room on purpose: they are news for members, not admin.
WHAT TO DO: pick or make a staff room in Discord, make a webhook for it (room → Edit Channel → Integrations →
Webhooks → New Webhook → Copy URL), save it as the secret `KPC_ADMIN_WEBHOOK`. Until then those two bots keep
posting to the spots room.
STATUS: **DONE Oct 21 09:05.** KPC_ADMIN_WEBHOOK is set and tested (Discord replied 204). Note for next time:
**Discord webhooks cannot be made from the phone app** — Server Settings → Integrations → Webhooks → New Webhook
on a computer.

## 4. Watching the Discord rooms for questions nobody answered  (Oct 21, Brandon asked for this)
WHY: 'can discord also notify us if someone needs something from us' — he meant the club's own Discord rooms:
somebody asks for help in a member room, everyone is out at a park, nobody sees it for days.
WHAT TO DO: (a) Brandon says WHICH rooms to watch; (b) the relay bot account needs View Channel +
Read Message History in those rooms (it already has the Message Content intent for the posting channel).
No new secret: it reuses DISCORD_BOT_TOKEN.
THEN CLAUDE BUILDS: a job that flags a message that looks like a question with no reply after about an hour.
STATUS: half done. BUILT Oct 21: kpc-discord-watch.yml + .github/scripts/kpc_discord_watch.py (hourly;
mode 'test' posts a hello, mode 'list' posts every room the bot can see, mode 'watch' is the job). Still needed:
Brandon picks the rooms, then they go in data/discord-watch.json "rooms". A room missing from the list means the
bot has no View Channel / Read Message History there.

## 5. APPROVAL_EMAIL — where the daily 'waiting for approval' email lands  (Oct 21, optional)
WHY: kpc_approvals.py sends to the secret `APPROVAL_EMAIL`. If it is empty the email goes to the club mailer's
own Gmail inbox (kpcwebhost), which Brandon does not read. Nothing has been waiting lately, so no email has gone
out to prove it either way.
WHAT TO DO: check the secret exists and holds Brandon's address; set it if not. Less urgent now the same list
also goes to Discord (Oct 21).
STATUS: unconfirmed.

## Already done (do not redo)
- ANDROID_KEY_PASSWORD (app signing), FB_PAGE_ID + FB_PAGE_TOKEN (posting), KPC_DISCORD_WEBHOOK,
  KPC_YOUTUBE_WEBHOOK, RELAY_DISCORD_WEBHOOKS, DISCORD_BOT_TOKEN + KPC_RELAY_CHANNEL,
  RELAY_MAIL_URL + RELAY_MAIL_KEY (club mailer), GROUPSIO_TO, SUBSCRIBE_SHEET_CSV,
  the form sheets NOTES_SHEET_CSV, COMMUNITY_SHEET_CSV, CAMPGROUND_SHEET_CSV, KPC_REPORTS_CSV,
  KPC_ACTIVATIONS_CSV, KPC_GUESTBOOK_CSV, KPC_CWBOARD_CSV, RIDB_API_KEY,
  kpc-gdrive.json clientId (Google Drive backup).
- GitHub → Settings → Notifications → Actions → 'Only notify for failed workflows' (asked Oct 18; confirm it is ticked).
