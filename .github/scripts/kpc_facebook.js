// Posts to the KPC Facebook Page (not Groups; Facebook doesn't allow automatic posts to Groups).
//   node kpc_facebook.js events  -> the next five weeks of Kentucky radio events (Mondays)
//   node kpc_facebook.js videos  -> any new public video on the club YouTube channels
// Needs two GitHub secrets: FB_PAGE_ID and FB_PAGE_TOKEN (a Page access token with pages_manage_posts).
// Without them it does nothing.
const fs = require('fs');
const path = require('path');

const mode = process.argv[2] || 'events';
const PAGE_ID = (process.env.FB_PAGE_ID || '').trim();
const TOKEN = (process.env.FB_PAGE_TOKEN || '').trim();
const SITE = 'https://kentuckyportableclub.github.io/KPC-Links/';
const POSTED = 'kpc-fb-posted.json';
const notice = m => console.log('::notice title=Facebook ' + mode + '::' + String(m).replace(/%/g, '%25').replace(/\n/g, '%0A'));

if (!PAGE_ID || !TOKEN) { notice('FB_PAGE_ID / FB_PAGE_TOKEN secrets not set yet; nothing posted.'); process.exit(0); }

async function post(message, link) {
  const body = new URLSearchParams({ message, access_token: TOKEN });
  if (link) body.set('link', link);
  const r = await fetch(`https://graph.facebook.com/${encodeURIComponent(PAGE_ID)}/feed`, { method: 'POST', body });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) {
    const e = j.error || {};
    notice(`Facebook said no (HTTP ${r.status}): ${e.message || 'unknown error'}${e.code === 190 ? ' (the Page token expired or was revoked; make a new one)' : ''}`);
    process.exit(1);
  }
  return j.id;
}

async function events() {
  const K = require(path.resolve('kpc-events.js'));
  let auto = null;
  try { auto = JSON.parse(fs.readFileSync('kpc-events-auto.json', 'utf8')); } catch (e) { /* hand-made list only */ }
  const today = new Date();
  const until = new Date(today.getFullYear(), today.getMonth(), today.getDate() + Number(process.env.DAYS_AHEAD || 35));
  const list = K.upcoming(K.merge(K.EVENTS, auto), today).filter(e => !e.tba && K.pd(e.start) <= until);
  if (!list.length) { notice('Nothing coming up; no post.'); return; }
  const DN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const when = e => { const s = K.pd(e.start), en = e.end ? K.pd(e.end) : null; let t = `${DN[s.getDay()]} ${MN[s.getMonth()]} ${s.getDate()}`; if (en && +en !== +s) t += en.getMonth() === s.getMonth() ? `–${en.getDate()}` : ` – ${MN[en.getMonth()]} ${en.getDate()}`; return t; };
  const lines = list.map(e => `📍 ${when(e)}: ${e.name}${e.tags.includes('KPC') ? ' (KPC event!)' : ''}\n${String(e.where || '').split(' — ')[0]}`);
  const msg = `📅 Coming up in Kentucky ham radio\n\n${lines.join('\n\n')}\n\nDates come from each organizer, so check their site before you go. Full calendar with "add to calendar" buttons:`;
  const id = await post(msg, SITE + 'events.html');
  notice(`Posted ${list.length} event(s) to the Page (post ${id}).`);
}

async function videos() {
  let yt;
  try { yt = JSON.parse(fs.readFileSync('kpc-youtube.json', 'utf8')); } catch (e) { notice('No kpc-youtube.json yet.'); return; }
  const all = [];
  for (const ch of yt.channels || []) for (const v of ch.videos || []) all.push({ ...v, channel: ch.name });
  let done = null;
  try { done = JSON.parse(fs.readFileSync(POSTED, 'utf8')); } catch (e) { /* first run */ }
  if (!done) {
    // First run: remember what's already there so the Page isn't flooded with old videos.
    fs.writeFileSync(POSTED, JSON.stringify({ videos: all.map(v => v.id) }, null, 1) + '\n');
    notice(`First run: marked ${all.length} existing video(s) as already shared. New ones will post from now on.`);
    return;
  }
  const seen = new Set(done.videos || []);
  const fresh = all.filter(v => !seen.has(v.id)).sort((a, b) => String(a.published).localeCompare(String(b.published))).slice(-3);
  for (const v of fresh) {
    const url = v.short ? `https://www.youtube.com/shorts/${v.id}` : `https://www.youtube.com/watch?v=${v.id}`;
    await post(`🎥 New from ${v.channel}: ${v.title}\n\nMore club videos: ${SITE}videos.html`, url);
    seen.add(v.id);
    notice('Shared video: ' + v.title);
  }
  all.forEach(v => seen.add(v.id));
  fs.writeFileSync(POSTED, JSON.stringify({ videos: [...seen] }, null, 1) + '\n');
  if (!fresh.length) notice('No new videos.');
}

(mode === 'videos' ? videos() : events()).catch(e => { notice('Error: ' + e.message); process.exit(1); });
