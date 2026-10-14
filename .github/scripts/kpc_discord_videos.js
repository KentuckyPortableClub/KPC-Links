// Shares new videos from the club YouTube channels (kpc-youtube.json) in the KPC Discord.
// Needs the GitHub secret KPC_DISCORD_WEBHOOK; without it it does nothing.
// Remembers what it shared in kpc-discord-videos.json. The first run only marks the videos already
// there, so Discord isn't flooded with old ones; at most 3 new videos post per run.
const fs = require('fs');
const SITE = 'https://kentuckyportableclub.github.io/KPC-Links/';
const POSTED = 'kpc-discord-videos.json';
const webhook = (process.env.KPC_DISCORD_WEBHOOK || '').trim();
const notice = m => console.log('::notice title=Discord videos::' + String(m).replace(/%/g, '%25').replace(/\n/g, '%0A'));

(async () => {
  if (!/^https:\/\/(discord|discordapp)\.com\/api\/webhooks\//.test(webhook)) { notice('No Discord webhook set (secret KPC_DISCORD_WEBHOOK); nothing posted.'); return; }
  let yt;
  try { yt = JSON.parse(fs.readFileSync('kpc-youtube.json', 'utf8')); } catch (e) { notice('No kpc-youtube.json yet.'); return; }
  const all = [];
  for (const ch of yt.channels || []) for (const v of ch.videos || []) all.push({ ...v, channel: ch.name });
  let done = null;
  try { done = JSON.parse(fs.readFileSync(POSTED, 'utf8')); } catch (e) { /* first run */ }
  if (!done) {
    fs.writeFileSync(POSTED, JSON.stringify({ videos: all.map(v => v.id) }, null, 1) + '\n');
    notice(`First run: marked ${all.length} existing video(s) as already shared. New ones will post from now on.`);
    return;
  }
  const seen = new Set(done.videos || []);
  const fresh = all.filter(v => !seen.has(v.id)).sort((a, b) => String(a.published).localeCompare(String(b.published))).slice(-3);
  for (const v of fresh) {
    const url = v.short ? `https://www.youtube.com/shorts/${v.id}` : `https://www.youtube.com/watch?v=${v.id}`;
    const title = String(v.title || '').replace(/[*_`~|>@]/g, '');
    const r = await fetch(webhook, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'KPC Videos', content: `🎥 **New from ${v.channel}:** ${title}\n${url}\nMore club videos: <${SITE}videos.html>`, allowed_mentions: { parse: [] } }),
    });
    if (!r.ok) { notice('Discord replied HTTP ' + r.status + ' for ' + title); break; }
    seen.add(v.id); notice('Shared video: ' + title);
    await new Promise(res => setTimeout(res, 1500));
  }
  if (!fresh.length) notice('No new videos.');
  // Only mark everything as seen when every new video went out; otherwise retry next run.
  if (fresh.every(v => seen.has(v.id))) all.forEach(v => seen.add(v.id));
  fs.writeFileSync(POSTED, JSON.stringify({ videos: [...seen] }, null, 1) + '\n');
})().catch(e => { notice('Error: ' + e.message); process.exit(1); });
