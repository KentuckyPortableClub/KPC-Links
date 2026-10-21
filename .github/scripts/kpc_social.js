// KPC social posts for Discord (webhook) and the KPC Facebook Page.
//   node kpc_social.js <task> [--dry]
// Tasks:
//   countdown  campout countdown (60, 30, 14, 7 and 1 days out)            Discord + Facebook
//   weekend    "this weekend" reminder for events starting Fri–Sun          Discord + Facebook
//   rarepark   rare park of the week (fewest valid activations in KY)       Discord + Facebook
//   milestones member milestones (parks, counties, activations)            Discord + Facebook
//   photos     new photo album on the site                                  Discord + Facebook
//   pages      new guide or tool page on the site (starts with the Oct 21, 2026 go-live)     Discord + Facebook
//   bandalert  NOAA radio blackout / geomagnetic storm alerts                Discord only
//   recaps     member activation recap (Kentucky parks, 10+ contacts) with a little map picture   Discord + Facebook
//   birthdays  'KPC is N years old' + members' license anniversaries (opt-in list kpc-birthdays.json)  Discord + Facebook
//   bandtimes  weekly best band times from Kentucky (WSPR beacon reports, last 7 days)            Discord + Facebook
// --dry prints what would be posted without posting or saving anything.
// State lives in kpc-social-state.json so nothing is posted twice.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const task = process.argv[2];
const DRY = process.argv.includes('--dry') || process.env.DRY_RUN === 'true';
const SITE = 'https://kentuckyportableclub.github.io/KPC-Links/';
const STATE_FILE = 'kpc-social-state.json';
// Which room each kind of post goes to (Brandon Oct 21: 'campout goes to announcements, milestones and recaps
// to general, new references parks... everything else general'). Falls back to the usual room when a webhook
// for that room has not been set up yet, so nothing ever goes missing.
const ROOM = { countdown: 'ANNOUNCE', rarepark: 'PARKS' };
const pick = t => (process.env[(ROOM[t] || 'GENERAL') + '_WEBHOOK_URL'] || '').trim()
  || (process.env.DISCORD_WEBHOOK_URL || '').trim();
// FACEBOOK_ONLY: for putting right a post that reached Discord but was refused by Facebook (Oct 21: the
// recap that landed while the Page token was being replaced). Leaves Discord alone so there is no repeat.
const DISCORD = process.env.FACEBOOK_ONLY ? '' : pick(task).split(/\s+/)[0];
// REDO: one state key (e.g. 'KQ4HZK|20261020') to send again even though it is recorded as done.
const REDO = (process.env.REDO || '').trim();
const FB_ID = (process.env.FB_PAGE_ID || '').trim();
const FB_TOKEN = (process.env.FB_PAGE_TOKEN || '').trim();
const PAGES_START = '2026-10-22'; // the first announcement is sent by the go-live job (Oct 21, 5 PM Central) right after the HOLD pages go live
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
async function postDiscord({ title, text, link, image, color, file }) {
  if (!/^https:\/\/(discord|discordapp)\.com\/api\/webhooks\//.test(DISCORD)) { notice('No Discord webhook; skipped Discord.'); return; }
  const embed = { title: title.slice(0, 250), description: (text + (link ? `\n\n[Open →](${link})` : '')).slice(0, 4000), color: color || 0xd5a63a };
  if (link) embed.url = link;
  if (image) embed.image = { url: image };
  let r;
  if (file) { // a picture made by the job (no web address yet): send it with the post
    embed.image = { url: 'attachment://' + path.basename(file) };
    const fd = new FormData();
    fd.append('payload_json', JSON.stringify({ username: 'KPC', embeds: [embed], allowed_mentions: { parse: [] } }));
    fd.append('files[0]', new Blob([fs.readFileSync(file)], { type: 'image/png' }), path.basename(file));
    r = await fetch(DISCORD, { method: 'POST', body: fd });
  } else r = await fetch(DISCORD, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'KPC', embeds: [embed], allowed_mentions: { parse: [] } }) });
  if (!r.ok) throw new Error('Discord HTTP ' + r.status);
}
async function postFacebook({ title, text, link, image, file }) {
  if (!FB_ID || !FB_TOKEN) { notice('No Facebook secrets; skipped Facebook.'); return; }
  const message = `${title}\n\n${text}${link && (image || file) ? `\n\n${link}` : ''}`;
  let body = new URLSearchParams({ access_token: FB_TOKEN });
  let url;
  if (file) {
    url = `https://graph.facebook.com/${FB_ID}/photos`;
    body = new FormData(); body.append('access_token', FB_TOKEN); body.append('caption', message);
    body.append('source', new Blob([fs.readFileSync(file)], { type: 'image/png' }), path.basename(file));
  } else if (image) { url = `https://graph.facebook.com/${FB_ID}/photos`; body.set('url', image); body.set('caption', message); }
  else { url = `https://graph.facebook.com/${FB_ID}/feed`; body.set('message', message); if (link) body.set('link', link); }
  const r = await fetch(url, { method: 'POST', body });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error('Facebook: ' + ((j.error && j.error.message) || 'HTTP ' + r.status));
}
async function post(msg, where = ['discord', 'facebook']) {
  const plain = msg.text.replace(/\*\*/g, '');
  if (DRY) { notice(`[${where.join('+')}] ${msg.title}\n${plain}${msg.link ? '\n' + msg.link : ''}${msg.image ? '\n(image) ' + msg.image : ''}${msg.file ? '\n(picture made: ' + msg.file + ')' : ''}`); return; }
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
async function history() { // cached for 3 hours so milestones + recaps in the same job only ask POTA once
  const C = '/tmp/kpc-history.json';
  try { const st = fs.statSync(C); if (Date.now() - st.mtimeMs < 3 * 36e5) return JSON.parse(fs.readFileSync(C, 'utf8')); } catch (e) { /* none yet */ }
  const h = await history0();
  try { fs.writeFileSync(C, JSON.stringify(h)); } catch (e) { /* fine */ }
  return h;
}
async function history0() {
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
  if (localDate() < PAGES_START && process.env.FORCE_PAGES !== '1') return notice(`New-page announcements start with the Oct 21 go-live.`);
  const skip = /HOLD|^members|^contact-card|^kpc-privacy|^index|^404/i;
  const info = f => {
    const t = fs.readFileSync(f, 'utf8');
    if (/name="robots"[^>]*noindex/i.test(t)) return null;
    const title = ((t.match(/<title>([^<]*)<\/title>/i) || [])[1] || f).replace(/\s*\|\s*(KPC|Kentucky Portable Club)\s*$/i, '').replace(/\s*:\s*$/, '').replace(/&amp;/g, '&');
    const desc = ((t.match(/<meta name="description" content="([^"]*)"/i) || [])[1] || '').replace(/&amp;/g, '&').replace(/&quot;/g, '"');
    return { f, title, desc };
  };
  const all = fs.readdirSync('.').filter(f => f.endsWith('.html') && !skip.test(f));
  if (!state.pages) {
    // Kickoff (go-live day): one hand-written roundup of what's new, then each new page gets its own post.
    state.pages = all;
    const U = f => SITE + f;
    const text = [
      '**Antennas & building**',
      `• Ununs, baluns & chokes: ${U('kpc-transformers.html')}`,
      `• Ladder line, doublets & the G5RV: ${U('kpc-doublets.html')}`,
      `• Loops & delta loops: ${U('kpc-loops.html')}`,
      `• VHF/UHF: J-pole, Slim Jim, yagi: ${U('kpc-vhf-uhf.html')}`,
      `• Receive-only antennas (Loop on Ground): ${U('kpc-receive-antennas.html')}`,
      `• Radial calculator: ${U('kpc-radials.html')}`,
      '',
      '**Learn & practice**',
      `• New to SOTA? ${U('kpc-new-to-sota.html')}`,
      `• New to WWFF? ${U('kpc-new-to-wwff.html')}`,
      `• CW practice (hunt & activate in Morse): ${U('kpc-cw.html')}`,
      `• Digital modes: ${U('kpc-digital.html')}`,
      `• Fox hunting: ${U('kpc-foxhunt.html')}`,
      `• Get your license: ${U('kpc-license.html')}`,
      '',
      '**Tools**',
      `• Power, dB & S-units: ${U('kpc-power-db.html')}`,
      `• Ham calculators: ${U('kpc-calc.html')}`,
      `• SOTA activation zone check: ${U('kpc-sota-az.html')}`,
      `• RF exposure check: ${U('kpc-rf-exposure.html')}`,
      `• Printable quick reference card: ${U('kpc-reference.html')}`,
      `• Club videos: ${U('videos.html')}`,
      '',
      '**Stay & activate**',
      `• Campgrounds & cabins inside Kentucky POTA parks (POTA, WWFF & SOTA on one card, maps, booking links, reviews): ${U('kpc-campgrounds.html')}`,
      '',
      'Plus a new events calendar, campout page and resources page. All free, all built for Kentucky portable operators.',
    ].join('\n');
    await post({ title: '🆕 New on the KPC website', text, link: SITE + 'toolbox.html' });
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

// Member activation recap: a member finished a valid activation (10+ contacts) at a Kentucky park.
// One post per call per UTC day (every park that day in one post, counted as activations), with a map picture. Only the last 3 days.
const STN = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'D.C.', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
tasks.recaps = async () => {
  const h = await history(), calls = new Set(members());
  const park = Object.fromEntries(KY.parks.map(p => [p.c, p]));
  const groups = {};
  for (const [ref, list] of Object.entries(h)) for (const [c, d0, q] of list) {
    const d = String(d0).replace(/\D/g, '').slice(0, 8);
    if (!calls.has(c) || q < 10 || !/^\d{8}$/.test(d)) continue;
    (groups[c + '|' + d] = groups[c + '|' + d] || { call: c, date: d, parks: [], qsos: 0 }).parks.push({ ref, q });
  }
  /* Oct 20 (Brandon: 'Yes members yes'): members' activations OUTSIDE Kentucky too, from each member's POTA profile (recent activity) */
  for (const c of calls) {
    let pr; try { pr = await getJSON(`${API}/profile/${c}`); } catch (e) { notice(`Recaps: no POTA profile for ${c} (${e.message})`); continue; }
    for (const a of ((pr.recent_activity || {}).activations || [])) {
      const ref = String(a.reference || '').toUpperCase(), d = String(a.date || '').replace(/\D/g, '').slice(0, 8), q = +a.total || 0;
      if (!ref || park[ref] || q < 10 || !/^\d{8}$/.test(d)) continue;   // Kentucky parks come from the park history above
      const g = (groups[c + '|' + d] = groups[c + '|' + d] || { call: c, date: d, parks: [], qsos: 0 });
      if (g.parks.some(x => x.ref === ref)) continue;
      const loc = String(a.location || ''), st = /^US-([A-Z]{2})/.exec(loc);
      g.parks.push({ ref, q, name: a.park || ref, st: st ? (STN[st[1]] || st[1]) : (loc || '') });
    }
    await sleep(400);
  }
  const iso = d => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
  const keys = Object.keys(groups).sort();
  const first = !state.recaps;
  state.recaps = state.recaps || [];
  const done = new Set(state.recaps);
  if (first) { state.recaps = keys.slice(-2000); save(); return notice(`First run: remembered ${keys.length} past member activations. Recaps post from now on.`); }
  /* Oct 20 (Brandon: 'missed K4ZSR and KQ4HZK'): activators often upload their log days later, so look back 10 days, not 3 */
  const fresh = keys.filter(k => (k === REDO || !done.has(k)) && dayDiff(localDate(), iso(groups[k].date)) <= 10);
  if (!fresh.length) { notice('No new member activations.'); return; }
  /* an evening activation runs past 0000 UTC, so POTA splits it into two days (Brandon Oct 17, N4BDW): when the same call has
     the next UTC day waiting too, post them together as one recap */
  const nextDay = d => { const t = new Date(iso(d) + 'T12:00:00Z'); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 10).replace(/-/g, ''); };
  const joined = new Set();
  for (const k of fresh) { const g = groups[k], k2 = g.call + '|' + nextDay(g.date); if (joined.has(k) || !fresh.includes(k2)) continue;
    const g2 = groups[k2]; joined.add(k2); g.also = k2; g.acts = g.parks.length + g2.parks.length;
    for (const p of g2.parks) { const m = g.parks.find(x => x.ref === p.ref); if (m) m.q += p.q; else g.parks.push(Object.assign({}, p)); } }
  for (const k of fresh) {
    if (joined.has(k)) continue;
    const g = groups[k];
    const dt0 = new Date(iso(g.date) + 'T12:00:00Z');
    const day = `${['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][dt0.getUTCDay()]}, ${MN[dt0.getUTCMonth()]} ${dt0.getUTCDate()}`;
    const ps = g.parks.map(p => ({ q: p.q, ref: p.ref, name: (park[p.ref] || {}).n || p.name || p.ref, la: (park[p.ref] || {}).la, lo: (park[p.ref] || {}).lo, co: (park[p.ref] || {}).co, st: p.st || '' }));
    for (const p of ps) if (p.la == null && !park[p.ref]) {   // outside Kentucky: ask POTA where the park is (for the map pin)
      try { const j = await getJSON(`${API}/park/${p.ref}`); if (j && isFinite(+j.latitude)) { p.la = +j.latitude; p.lo = +j.longitude; } } catch (e) { /* no pin */ }
      await sleep(300);
    }
    // no '2-fer' wording (Brandon Oct 17: 'just number of activations'); overlapping parks share the same contacts, so don't add them twice
    const over = ps.length > 1 && ps.every((p, i) => ps.every((q, k) => i === k || ((park[p.ref] || {}).tf || []).includes(q.ref)));
    g.qsos = over ? Math.max(...ps.map(p => p.q)) : ps.reduce((a, p) => a + p.q, 0);
    const file = `/tmp/recap-${g.call}-${g.date}.png`;
    let pic = null;
    try { execSync(`python3 .github/scripts/kpc_recap_map.py ${file}`, { input: JSON.stringify({ call: g.call, date: day, qsos: g.qsos, parks: ps }), stdio: ['pipe', 'ignore', 'inherit'] }); pic = file; }
    catch (e) { notice('Map picture failed: ' + e.message); }
    const n = g.acts || ps.length, ago = dayDiff(localDate(), iso(g.date));
    // the post goes out in the morning; POTA dates are UTC, so an evening activation can carry today's date: call it yesterday
    const when = ago <= 1 ? 'yesterday' : 'on ' + day;
    const title = `📻 ${g.call} activated ${ps.length > 1 ? ps.length + ' parks' : ps[0].name}`;
    // Brandon Oct 17: a friendly note in the club's voice, and 'not the same thing every time: mix it up' (he OK'd these lines).
    // One line is picked from each group; the pick is steady for the same call + day (a re-run says the same thing).
    let seed = 0; for (const ch of k) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
    const pick = (A, salt) => A[(seed + salt * 7919) % A.length];
    const C = `**${g.call}**`, acts = `**${n} activation${n > 1 ? 's' : ''}**`, Q = `**${g.qsos} contacts**`;
    const OPEN = [`Good morning! ${C} had a good day ${when} enjoying the parks`, `Rise and shine, KPC! ${C} was out in the parks ${when}`,
      `Morning, hunters! ${C} put ${ps.length > 1 ? 'some parks' : 'another park'} on the air ${when}`, `Coffee's on! Here's what ${C} was up to ${when}`, `Another great day in the parks for ${C} ${when}`];
    const MID = over ? [`: two parks at once, ${acts} and ${Q} in the log.`] : g.qsos >= 50 ? [`: what a pileup! ${acts} and ${Q} in the log.`, `: ${acts} and ${Q} in the log. Busy day!`]
      : [`: ${acts} and ${Q} in the log.`, `, and **${g.qsos} of you** made it into the log (${acts}).`];
    const CLOSE = [`${g.call} was happy to hear so many of you. Hope to catch you next time.`, 'Thanks to every hunter who called in. See you down the log!',
      'If you got them, thanks for the call. If you didn\'t, there\'s always next time.', 'Great signals and great company. Thanks, everyone!', 'Keep an eye on the spots, there\'s more where that came from.'];
    const text = pick(OPEN, 1) + pick(MID, 2) + '\n\n' +
      ps.map(p => `🌲 ${p.ref} · ${p.name}${p.co ? ` (${p.co} County)` : p.st ? ` (${p.st})` : ''} · ${p.q} contacts`).join('\n') +
      '\n\n' + pick(CLOSE, 3) + '\n\n73,\nKPC';
    await post({ title, text, link: `${SITE}${park[ps[0].ref] ? 'kpc-park-notes.html' : 'kpc-park-notes-us.html'}#${ps[0].ref}`, file: pic || undefined });
    state.recaps.push(k); if (g.also) state.recaps.push(g.also); state.recaps = state.recaps.slice(-2000); save();
    await sleep(2000);
  }
};

// Weekly best band times from Kentucky: WSPR beacon reports heard from / by stations in Kentucky's grid squares,
// last 7 days, counted per band and Eastern-time hour. The best 3-hour stretch per band is posted.
tasks.bandtimes = async () => {
  const wk = localDate();
  state.bandtimes = state.bandtimes || [];
  if (!DRY && state.bandtimes.includes(wk)) return notice('Already posted today.');
  const BN = [[3, '80m'], [5, '60m'], [7, '40m'], [10, '30m'], [14, '20m'], [18, '17m'], [21, '15m'], [24, '12m'], [28, '10m'], [50, '6m']];
  const SQ = ['EM66', 'EM67', 'EM76', 'EM77', 'EM78', 'EM86', 'EM87', 'EM88', 'EM96', 'EM97', 'EM68', 'EM79', 'EM89'];
  const IN = "('" + SQ.join("','") + "')";
  const sql = `SELECT band, toHour(toTimeZone(time,'America/New_York')) AS h, count() AS c, max(distance) AS d, uniqExact(if(substring(tx_loc,1,4) IN ${IN}, rx_sign, tx_sign)) AS u FROM wspr.rx WHERE time > now() - INTERVAL 7 DAY AND band IN (${BN.map(b => b[0]).join(',')}) AND (substring(tx_loc,1,4) IN ${IN} OR substring(rx_loc,1,4) IN ${IN}) GROUP BY band, h ORDER BY band, h FORMAT JSON`;
  const j = await getJSON('https://db1.wspr.live/?query=' + encodeURIComponent(sql));
  const by = {};
  for (const r of j.data || []) { const b = +r.band; (by[b] = by[b] || { h: Array(24).fill(0), d: 0, n: 0 }); by[b].h[+r.h] += +r.c; by[b].d = Math.max(by[b].d, +r.d); by[b].n += +r.c; }
  const hr = h => { const x = ((h % 24) + 24) % 24; return (x % 12 || 12) + (x < 12 ? ' AM' : ' PM'); };
  const lines = [];
  let total = 0;
  for (const [b, name] of BN) {
    const B = by[b]; if (!B || B.n < 40) continue;
    total += B.n;
    let best = -1, at = 0;
    for (let i = 0; i < 24; i++) { const v = B.h[i] + B.h[(i + 1) % 24] + B.h[(i + 2) % 24]; if (v > best) { best = v; at = i; } }
    lines.push(`**${name}**: best ${hr(at)}–${hr(at + 3)} · ${B.n.toLocaleString('en-US')} reports`);
  }
  if (!lines.length) return notice('Not enough WSPR reports this week to post.');
  const title = '📡 Best band times from Kentucky this week';
  const text = `From ${total.toLocaleString('en-US')} WSPR beacon reports heard to and from Kentucky over the last 7 days (Eastern time):\n\n` + lines.join('\n') +
    `\n\nWSPR beacons run just a few watts, so when they get through, your SSB or CW signal from the park can too. Bands change with the sun: check the live conditions bar before you head out.`;
  await post({ title, text, link: SITE + 'kpc-live.html', color: 0x3a8dd5 });
  if (!DRY) { state.bandtimes.push(wk); state.bandtimes = state.bandtimes.slice(-20); save(); }
};

// Club birthday + license anniversaries. Only members listed in kpc-birthdays.json (they said yes) are mentioned.
tasks.birthdays = async () => {
  let B = {}; try { B = JSON.parse(fs.readFileSync('kpc-birthdays.json', 'utf8')); } catch (e) { return notice('No kpc-birthdays.json.'); }
  const d = localDate(), md = d.slice(5), yr = +d.slice(0, 4);
  state.birthdays = state.birthdays || [];
  if (state.birthdays.includes(d)) return notice('Already posted today.');
  const lines = []; let club = 0;
  if (/^\d{4}-\d{2}-\d{2}$/.test(B.club || '') && B.club.slice(5) === md && yr > +B.club.slice(0, 4)) club = yr - +B.club.slice(0, 4);
  for (const m of B.members || []) {
    if (!m || !/^\d{4}-\d{2}-\d{2}$/.test(m.licensed || '') || m.licensed.slice(5) !== md) continue;
    const n = yr - +m.licensed.slice(0, 4); if (n < 1) continue;
    lines.push(`📜 **${String(m.call).toUpperCase()}** got their ham license **${n} year${n > 1 ? 's' : ''}** ago today!`);
  }
  if (!club && !lines.length) return notice('No birthdays or anniversaries today.');
  const title = club ? `🎂 Kentucky Portable Club is ${club} year${club > 1 ? 's' : ''} old today!` : '📜 Ham radio anniversary';
  const text = (club ? `Thank you to every member, hunter and friend who has gotten outside and on the air with us. Here's to many more years in the parks!${lines.length ? '\n\n' : ''}` : '') + lines.join('\n') + (lines.length ? '\n\nCongratulations and 73!' : '');
  await post({ title, text, link: SITE + (club ? 'about.html' : 'members.html') });
  if (!DRY) { state.birthdays.push(d); state.birthdays = state.birthdays.slice(-30); save(); }
};

if (!tasks[task]) { console.error('Unknown task. Use: ' + Object.keys(tasks).join(', ')); process.exit(2); }
tasks[task]().catch(e => { notice('Error: ' + e.message); process.exit(1); });
