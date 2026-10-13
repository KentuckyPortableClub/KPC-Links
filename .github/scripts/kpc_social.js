// KPC social posts for Discord (webhook) and the KPC Facebook Page.
//   node kpc_social.js <task> [--dry]
// Tasks:
//   countdown  campout countdown (60, 30, 14, 7 and 1 days out)            Discord + Facebook
//   weekend    "this weekend" reminder for events starting Fri–Sun          Discord + Facebook
//   rarepark   rare park of the week (fewest valid activations in KY)       Discord + Facebook
//   milestones member milestones (parks, counties, activations)            Discord + Facebook
//   photos     new photo album on the site                                  Discord + Facebook
//   pages      new guide or tool page on the site (starts Oct 21, 2026)     Discord + Facebook
//   bandalert  NOAA radio blackout / geomagnetic storm alerts                Discord only
// --dry prints what would be posted without posting or saving anything.
// State lives in kpc-social-state.json so nothing is posted twice.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const task = process.argv[2];
const DRY = process.argv.includes('--dry') || process.env.DRY_RUN === 'true';
const SITE = 'https://kentuckyportableclub.github.io/KPC-Links/';
const STATE_FILE = 'kpc-social-state.json';
const DISCORD = (process.env.DISCORD_WEBHOOK_URL || '').trim();
const FB_ID = (process.env.FB_PAGE_ID || '').trim();
const FB_TOKEN = (process.env.FB_PAGE_TOKEN || '').trim();
const PAGES_START = '2026-10-21'; // same day the HOLD pages (campout, events, resources) go live
const API = 'https://api.pota.app';

const notice = m => console.log(`::notice title=Social ${task}${DRY ? ' (dry run)' : ''}::` + String(m).replace(/%/g, '%25').replace(/\r/g, '').replace(/\n/g, '%0A'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
let state = {};
try { state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch (e) { state = {}; }
const save = () => { if (!DRY) fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 1) + '\n'); };

const today = new Date();
const ymd = d => d.toISOString().slice(0, 10);
const localDate = () => { // Kentucky date (Eastern/Central both fine for whole-day logic): use America/Chicago
  const p = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  return p; // YYYY-MM-DD
};
const dayDiff = (a, b) => Math.round((Date.parse(a + 'T12:00:00Z') - Date.parse(b + 'T12:00:00Z')) / 864e5);

// ------------------------------------------------------------------ posting
async function postDiscord({ title, text, link, image, color }) {
  if (!/^https:\/\/(discord|discordapp)\.com\/api\/webhooks\//.test(DISCORD)) { notice('No Discord webhook; skipped Discord.'); return; }
  const embed = { title: title.slice(0, 250), description: (text + (link ? `\n\n[Open →](${link})` : '')).slice(0, 4000), color: color || 0xd5a63a };
  if (link) embed.url = link;
  if (image) embed.image = { url: image };
  const r = await fetch(DISCORD, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'KPC', embeds: [embed], allowed_mentions: { parse: [] } }) });
  if (!r.ok) throw new Error('Discord HTTP ' + r.status);
}
async function postFacebook({ title, text, link, image }) {
  if (!FB_ID || !FB_TOKEN) { notice('No Facebook secrets; skipped Facebook.'); return; }
  const message = `${title}\n\n${text}${link && image ? `\n\n${link}` : ''}`;
  const body = new URLSearchParams({ access_token: FB_TOKEN });
  let url;
  if (image) { url = `https://graph.facebook.com/${FB_ID}/photos`; body.set('url', image); body.set('caption', message); }
  else { url = `https://graph.facebook.com/${FB_ID}/feed`; body.set('message', message); if (link) body.set('link', link); }
  const r = await fetch(url, { method: 'POST', body });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error('Facebook: ' + ((j.error && j.error.message) || 'HTTP ' + r.status));
}
async function post(msg, where = ['discord', 'facebook']) {
  const plain = msg.text.replace(/\*\*/g, '');
  if (DRY) { notice(`[${where.join('+')}] ${msg.title}\n${plain}${msg.link ? '\n' + msg.link : ''}${msg.image ? '\n(image) ' + msg.image : ''}`); return; }
  const errs = [];
  if (where.includes('discord')) await postDiscord(msg).catch(e => errs.push(e.message));
  if (where.includes('facebook')) await postFacebook({ ...msg, text: plain }).catch(e => errs.push(e.message));
  notice(`Posted "${msg.title}"${errs.length ? ' with problems: ' + errs.join('; ') : ''}`);
  if (errs.length === where.length) throw new Error(errs.join('; '));
}

// ------------------------------------------------------------------ shared data
const K = require(path.resolve('kpc-events.js'));
const KY = JSON.parse(fs.readFileSync('kpc-ky-data.json', 'utf8'));
function events() {
  let auto = null;
  try { auto = JSON.parse(fs.readFileSync('kpc-events-auto.json', 'utf8')); } catch (e) { /* hand list only */ }
  return K.upcoming(K.merge(K.EVENTS, auto), today).filter(e => !e.tba);
}
const DN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function when(e) { const s = K.pd(e.start), en = e.end ? K.pd(e.end) : null; let t = `${DN[s.getDay()]} ${MN[s.getMonth()]} ${s.getDate()}`; if (en && +en !== +s) t += en.getMonth() === s.getMonth() ? `–${en.getDate()}` : ` – ${MN[en.getMonth()]} ${en.getDate()}`; return t; }
const link = e => (e.local ? SITE + e.url : e.url);
const short = w => String(w || '').split(' — ')[0];

async function getJSON(url, tries = 3) {
  let last;
  for (let i = 0; i < tries; i++) {
    try { const r = await fetch(url, { headers: { 'User-Agent': 'KPC-social-bot (kentuckyportableclub.github.io)' } }); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.json(); }
    catch (e) { last = e; await sleep(1500 * (i + 1)); }
  }
  throw last;
}
// Activation history for every Kentucky park: {ref: [[call, yyyymmdd, qsos], ...]}
async function history() {
  const refs = KY.parks.map(p => p.c), out = {};
  let i = 0, fails = 0;
  async function worker() {
    while (i < refs.length) {
      const ref = refs[i++];
      try { const j = await getJSON(`${API}/park/activations/${ref}?count=all`); out[ref] = (Array.isArray(j) ? j : []).map(a => [String(a.activeCallsign || '').toUpperCase().replace(/\/.*$/, ''), String(a.qso_date || ''), +a.totalQSOs || 0]); }
      catch (e) { fails++; }
      await sleep(150);
    }
  }
  await Promise.all([worker(), worker(), worker(), worker()]);
  if (fails > refs.length * 0.1) throw new Error(`POTA API: ${fails} of ${refs.length} parks failed`);
  return out;
}
function members() {
  const t = fs.readFileSync('kpc-tools.js', 'utf8');
  const m = t.match(/MEMBERS\s*=\s*\[([^\]]*)\]/);
  return m ? [...m[1].matchAll(/'([A-Z0-9]+)'/g)].map(x => x[1]) : [];
}

// ------------------------------------------------------------------ tasks
const tasks = {};

tasks.countdown = async () => {
  const camp = K.EVENTS.find(e => e.tags.includes('CAMPOUT'));
  if (!camp) return notice('No campout on the calendar.');
  const left = dayDiff(camp.start, localDate());
  const marks = { 60: '2 months', 30: '30 days', 14: '2 weeks', 7: '1 week', 1: 'Tomorrow' };
  state.countdown = state.countdown || [];
  const key = camp.start + ':' + left;
  if (!marks[left] || state.countdown.includes(key)) return notice(`${left} days to the campout; nothing to post today.`);
  const title = left === 1 ? `🏕️ The ${camp.name} starts TOMORROW!` : `🏕️ ${marks[left]} to the ${camp.name}!`;
  const text = `${when(camp)} at ${short(camp.where)}.\n\n` + (left >= 30 ? 'Camping, POTA activations, a fox hunt, a community meal and good friends. Grab a campsite and get your gear ready.' : left >= 7 ? 'Time to check your gear, charge the batteries and plan your antenna. Group sites are filling up.' : 'Pack the radio, the batteries and the coax. See you at camp!');
  await post({ title, text, link: SITE + 'campout.html' });
  state.countdown.push(key); save();
};

tasks.weekend = async () => {
  const d = localDate(), dow = new Date(d + 'T12:00:00Z').getUTCDay(); // 4 = Thursday
  const fri = dayDiff(d, d) + ((5 - dow + 7) % 7), sun = fri + 2;
  const list = events().filter(e => { const a = dayDiff(e.start, d), b = dayDiff(e.end || e.start, d); return b >= fri && a <= sun; });
  state.weekend = state.weekend || [];
  const key = d.slice(0, 10);
  if (!list.length) return notice('Nothing this weekend.');
  if (state.weekend.includes(key)) return notice('Already posted this weekend.');
  const text = list.map(e => `📍 **${when(e)}**: ${e.name}${e.tags.includes('KPC') ? ' (KPC event!)' : ''}\n${short(e.where)}`).join('\n\n') + '\n\nHave fun, be safe, and post your pictures!';
  await post({ title: '📻 This weekend in Kentucky ham radio', text, link: SITE + 'events.html' });
  state.weekend.push(key); state.weekend = state.weekend.slice(-20); save();
};

tasks.rarepark = async () => {
  const h = await history();
  const recent = new Set((state.rare || []).slice(-26).map(x => x.ref));
  const rows = KY.parks.filter(p => h[p.c]).map(p => {
    const valid = h[p.c].filter(a => a[2] >= 10);
    const last = valid.map(a => a[1]).sort().pop() || '';
    return { p, n: valid.length, last };
  }).sort((a, b) => a.n - b.n || a.last.localeCompare(b.last));
  const pool = rows.filter(r => !recent.has(r.p.c)).slice(0, 15);
  if (!pool.length) return notice('No candidates.');
  const week = Math.floor(Date.now() / 6048e5), pick = pool[week % pool.length], p = pick.p;
  const fmt = s => s ? `${MN[+s.slice(4, 6) - 1]} ${+s.slice(6, 8)}, ${s.slice(0, 4)}` : '';
  const text = `**${p.c} · ${p.n}**\n${p.co ? p.co + (String(p.co).includes('/') ? ' Counties' : ' County') : ''}${p.t ? ' · ' + p.t : ''}\n\n` +
    (pick.n === 0 ? 'It has **never** been activated. Be the first!' : `Only **${pick.n}** valid activation${pick.n === 1 ? '' : 's'} ever. Last one: ${fmt(pick.last)}.`) +
    '\n\nActivators: go put it on the air. Hunters: watch the spots for it.' + (p.web ? `\nPark info: ${p.web}` : '');
  const mapLink = `${SITE}finder.html?lat=${p.la}&lon=${p.lo}&radius=25`;
  await post({ title: '🌲 Rare Park of the Week', text, link: mapLink });
  state.rare = (state.rare || []).concat({ ref: p.c, date: localDate() }).slice(-60); save();
};

tasks.milestones = async () => {
  const h = await history(), calls = members();
  const county = Object.fromEntries(KY.parks.map(p => [p.c, String(p.co || '').split('/').map(x => x.trim()).filter(Boolean)]));
  const now = {};
  for (const c of calls) {
    const parks = new Set(), counties = new Set(); let acts = 0;
    for (const [ref, list] of Object.entries(h)) for (const a of list) if (a[0] === c && a[2] >= 10) { acts++; parks.add(ref); (county[ref] || []).forEach(x => counties.add(x)); }
    now[c] = { parks: parks.size, counties: counties.size, acts };
  }
  const prev = state.milestones;
  state.milestones = now;
  if (!prev) { save(); return notice('First run: saved everyone\'s current totals. Milestones post from now on. ' + JSON.stringify(now)); }
  const steps = {
    parks: [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100, 110, 120, 125, 130, 140, 150, 160, 170, 175, 180, KY.parks.length],
    counties: [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120],
    acts: [10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000],
  };
  const words = { parks: 'different Kentucky parks activated', counties: 'Kentucky counties activated', acts: 'Kentucky activations' };
  const lines = [];
  for (const c of calls) {
    const a = prev[c] || { parks: 0, counties: 0, acts: 0 }, b = now[c];
    for (const k of Object.keys(steps)) {
      const hit = steps[k].filter(s => a[k] < s && b[k] >= s).pop();
      if (hit) lines.push(hit === KY.parks.length && k === 'parks' ? `🏆 **${c}** has activated **every park** in the KPC guide! (${hit})` : `🎉 **${c}**: **${hit}** ${words[k]}!`);
    }
  }
  if (!lines.length) { save(); return notice('No new milestones.'); }
  await post({ title: '🎉 KPC Milestones', text: lines.join('\n') + '\n\nCongratulations! Keep getting outside and getting on the air.', link: SITE + 'kpc-club.html' });
  save();
};

tasks.photos = async () => {
  const P = JSON.parse(fs.readFileSync('kpc-photos.json', 'utf8'));
  const ids = (P.albums || []).map(a => a.id);
  if (!state.photos) { state.photos = ids; save(); return notice('First run: remembered the current albums: ' + ids.join(', ')); }
  const fresh = (P.albums || []).filter(a => !state.photos.includes(a.id));
  if (!fresh.length) return notice('No new albums.');
  for (const a of fresh) {
    const cover = a.cover || (a.photos && a.photos[0] && a.photos[0].f);
    await post({ title: `📸 New photos: ${a.title}`, text: `${a.text || ''}${a.place ? `\n📍 ${a.place}` : ''}${a.photos ? `\n${a.photos.length} photos` : ''}`, link: `${SITE}photos.html#${a.id}`, image: cover ? SITE + cover : undefined });
    state.photos.push(a.id); save();
  }
};

tasks.pages = async () => {
  if (localDate() < PAGES_START) return notice(`New-page announcements start ${PAGES_START}.`);
  const skip = /HOLD|^members|^contact-card|^kpc-privacy|^index|^404/i;
  const info = f => {
    const t = fs.readFileSync(f, 'utf8');
    if (/name="robots"[^>]*noindex/i.test(t)) return null;
    const title = ((t.match(/<title>([^<]*)<\/title>/i) || [])[1] || f).replace(/\s*\|\s*KPC\s*$/, '').replace(/&amp;/g, '&');
    const desc = ((t.match(/<meta name="description" content="([^"]*)"/i) || [])[1] || '').replace(/&amp;/g, '&').replace(/&quot;/g, '"');
    return { f, title, desc };
  };
  const all = fs.readdirSync('.').filter(f => f.endsWith('.html') && !skip.test(f));
  if (!state.pages) {
    // Kickoff: one roundup of the guides added in the last couple of weeks, then announce each new page as it appears.
    let recent = [];
    try { recent = execSync('git log --since=2026-10-09 --diff-filter=A --name-only --format=', { encoding: 'utf8' }).split('\n').filter(f => all.includes(f)); } catch (e) { /* no history */ }
    const items = [...new Set(recent)].map(info).filter(Boolean);
    state.pages = all;
    if (items.length) {
      await post({ title: '🆕 New on the KPC website', text: items.map(i => `• **${i.title}**: ${SITE}${i.f}`).join('\n') + '\n\nAll free, all built for Kentucky portable operators.', link: SITE + 'toolbox.html' });
    } else notice('Kickoff: no recently added pages found; remembering the current list.');
    save(); return;
  }
  const fresh = all.filter(f => !state.pages.includes(f)).map(info).filter(Boolean);
  if (!fresh.length) return notice('No new pages.');
  for (const i of fresh.slice(0, 3)) {
    await post({ title: `🆕 New on the KPC site: ${i.title}`, text: i.desc, link: SITE + i.f });
    state.pages.push(i.f); save();
  }
};

tasks.bandalert = async () => {
  const alerts = await getJSON('https://services.swpc.noaa.gov/products/alerts.json');
  state.alerts = state.alerts || { seen: [], last: {} };
  const seen = new Set(state.alerts.seen);
  const first = state.alerts.seen.length === 0;
  const fresh = [];
  for (const a of alerts) {
    const msg = String(a.message || '');
    const serial = (msg.match(/Serial Number:\s*(\d+)/) || [])[1] || (a.product_id + a.issue_datetime);
    if (seen.has(serial)) continue;
    seen.add(serial);
    const sc = msg.match(/NOAA Scale:\s*([RGS])([1-5])/);
    if (!sc || /^(CANCEL|SUMMARY)/m.test(msg)) continue;
    const kind = sc[1], lvl = +sc[2];
    if ((kind === 'R' && lvl < 3) || (kind === 'G' && lvl < 3) || (kind === 'S' && lvl < 3)) continue;
    const ageH = (Date.now() - Date.parse(String(a.issue_datetime).replace(' ', 'T') + 'Z')) / 36e5;
    if (ageH > 6) continue;
    fresh.push({ kind, lvl, msg, head: (msg.match(/^(ALERT|WARNING|WATCH|EXTENDED WARNING)[^\n]*/m) || [''])[0] });
  }
  state.alerts.seen = [...seen].slice(-300);
  if (first) { save(); return notice(`First run: remembered ${seen.size} existing NOAA alerts.`); }
  const words = {
    R: lvl => ({ title: `📡 HF radio blackout (R${lvl})`, text: `A strong solar flare is knocking out HF on the sunlit side of the Earth. Expect weak or no signals, especially on the lower bands, for up to an hour or so. If you're activating, wait it out or try a higher band.` }),
    G: lvl => ({ title: `🌌 Geomagnetic storm (G${lvl})`, text: `The bands may be noisy and weak, especially on northern paths. The fun side: **aurora is possible**. Listen on 6 m and 2 m (CW and SSB) for that buzzy aurora sound, and look north after dark.` }),
    S: lvl => ({ title: `☢️ Solar radiation storm (S${lvl})`, text: `HF over the poles is likely blacked out. Paths to Europe and Asia may suffer. Paths within the US are usually OK.` }),
  };
  let posted = 0;
  for (const f of fresh) {
    const last = state.alerts.last[f.kind];
    if (last && Date.now() - last.t < 6 * 36e5 && last.lvl >= f.lvl) continue; // no repeats for 6 hours unless it gets worse
    const w = words[f.kind](f.lvl);
    await post({ title: w.title, text: `${w.text}\n\n_NOAA: ${f.head.trim()}_`, link: SITE + 'kpc-space-weather.html', color: 0xd2693c }, ['discord']);
    state.alerts.last[f.kind] = { t: Date.now(), lvl: f.lvl }; posted++;
  }
  save();
  if (!posted) notice('No new strong alerts.');
};

if (!tasks[task]) { console.error('Unknown task. Use: ' + Object.keys(tasks).join(', ')); process.exit(2); }
tasks[task]().catch(e => { notice('Error: ' + e.message); process.exit(1); });
