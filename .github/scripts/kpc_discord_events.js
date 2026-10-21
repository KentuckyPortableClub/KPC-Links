// Posts the next few weeks of Kentucky radio events to the KPC Discord.
// Uses the same event list as the website: kpc-events.js (hand-made) + kpc-events-auto.json (found weekly).
const fs = require('fs');
const path = require('path');
const K = require(path.resolve('kpc-events.js'));

const DAYS_AHEAD = Number(process.env.DAYS_AHEAD || 35);
const webhook = ((process.env.GENERAL_WEBHOOK_URL || '').trim() || (process.env.DISCORD_WEBHOOK_URL || '').trim()).split(/\s+/)[0];
const PAGE = 'https://kentuckyportableclub.github.io/KPC-Links/events.html';

let auto = null;
try { auto = JSON.parse(fs.readFileSync('kpc-events-auto.json', 'utf8')); } catch (e) { /* hand-made list only */ }

const today = new Date();
const until = new Date(today.getFullYear(), today.getMonth(), today.getDate() + DAYS_AHEAD);
const list = K.upcoming(K.merge(K.EVENTS, auto), today).filter(e => !e.tba && K.pd(e.start) <= until);

const DN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function when(e) {
  const s = K.pd(e.start), en = e.end ? K.pd(e.end) : null;
  let t = `${DN[s.getDay()]} ${MN[s.getMonth()]} ${s.getDate()}`;
  if (en && +en !== +s) t += en.getMonth() === s.getMonth() ? `–${en.getDate()}` : ` – ${MN[en.getMonth()]} ${en.getDate()}`;
  return t;
}
const notice = m => console.log('::notice title=Discord events post::' + String(m).replace(/%/g, '%25').replace(/\n/g, '%0A'));
const clean = s => String(s || '').replace(/[*_`~|>]/g, '').split(' — ')[0].slice(0, 90);

const lines = list.map(e => {
  const kpc = e.tags.includes('KPC') ? ' 🟢 **KPC**' : '';
  const auto = e.auto ? ' _(found automatically, confirm with organizer)_' : '';
  return `**${when(e)}** · [${clean(e.name)}](${e.local ? PAGE : e.url})${kpc}\n${clean(e.where)}${auto}`;
});

console.log(`${list.length} event(s) in the next ${DAYS_AHEAD} days`);
lines.forEach(l => console.log(' -', l.split('\n')[0]));

if (!list.length) { notice('Nothing in the next ' + DAYS_AHEAD + ' days; no post.'); process.exit(0); }
if (!/^https:\/\/(discord|discordapp)\.com\/api\/webhooks\//.test(webhook)) {
  notice('No Discord webhook set (secret KPC_DISCORD_WEBHOOK); skipping the post.');
  process.exit(0);
}

let desc = '';
for (const l of lines) { if ((desc + l).length > 3800) break; desc += l + '\n\n'; }
desc += `[Full Kentucky radio calendar →](${PAGE})`;

fetch(webhook, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'KPC Events',
    embeds: [{ title: '📅 Coming up in Kentucky ham radio', description: desc, color: 0xd5a63a }],
    allowed_mentions: { parse: [] },
  }),
}).then(r => {
  notice('Discord replied HTTP ' + r.status + ' after posting ' + list.length + ' event(s)');
  if (!r.ok) process.exit(1);
}).catch(e => { console.error(e); process.exit(1); });
