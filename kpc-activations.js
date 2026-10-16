/* Activation Board (kpc-activations.html): planned activations, who's on the air now, and hunters' park requests.
   Data: kpc-activations.json (copied from the Google Form by .github/scripts/kpc_activations.py every 20 minutes).
   Form link: kpc-activations-form.json {url, parkEntry, needEntry}. Filter choice remembered in localStorage kpcAbF. */
(function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const TZ = { eastern: 'America/New_York', central: 'America/Chicago', mountain: 'America/Denver', pacific: 'America/Los_Angeles', utc: 'UTC' };
  let F = { prog: 'all', ky: false, q: '' };
  try { Object.assign(F, JSON.parse(localStorage.getItem('kpcAbF') || '{}')); } catch (e) {}
  let ITEMS = [], FORM = {};

  // wall-clock time in a time zone -> real moment (ms)
  function zoneOffset(ms, zone) {
    const p = {}; new Intl.DateTimeFormat('en-US', { timeZone: zone, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
      .formatToParts(new Date(ms)).forEach(x => p[x.type] = x.value);
    return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute, +p.second) - ms;
  }
  function at(date, hhmm, zone) {
    const [y, m, d] = date.split('-').map(Number), [h, mi] = (hhmm || '00:00').split(':').map(Number);
    const guess = Date.UTC(y, m - 1, d, h, mi);
    return guess - zoneOffset(guess - zoneOffset(guess, zone), zone);
  }
  function times(it) {
    const zone = TZ[(it.tz || 'eastern').toLowerCase()] || 'America/New_York';
    const s = it.start ? at(it.date, it.start, zone) : at(it.date, '00:00', zone);
    let e = it.end ? at(it.date, it.end, zone) : it.start ? s + 3 * 3600e3 : at(it.date, '23:59', zone);
    if (e < s) e += 24 * 3600e3;                                     // ends after midnight
    return { s, e, zone, timed: !!it.start };
  }
  const fmt = (ms, zone, o) => new Intl.DateTimeFormat('en-US', Object.assign({ timeZone: zone }, o)).format(new Date(ms));
  const hm = (ms, zone) => fmt(ms, zone, { hour: 'numeric', minute: '2-digit' });
  const myZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const zoneName = (ms, zone) => (fmt(ms, zone, { timeZoneName: 'short' }).split(' ').pop());

  function refLink(r) {
    const ref = r.ref;
    if (ref.includes('/')) return 'https://sotl.as/summits/' + ref;
    if (/^[A-Z0-9]+FF-\d+$/.test(ref)) return 'https://wwff.co/directory/?showRef=' + encodeURIComponent(ref);
    return 'https://pota.app/#/park/' + encodeURIComponent(ref);
  }
  const progOf = it => {
    const p = new Set((it.prog || []).map(x => /sota/i.test(x) ? 'sota' : /wwff|kff/i.test(x) ? 'wwff' : /pota/i.test(x) ? 'pota' : 'other'));
    (it.refs || []).forEach(r => p.add(r.ref.includes('/') ? 'sota' : /FF-/.test(r.ref) ? 'wwff' : 'pota'));
    return p;
  };
  const inKY = it => (it.refs || []).some(r => KYSET.has(r.ref));
  let KYSET = new Set();

  function formUrl(entry, val) {
    if (!FORM.url) return '';
    return FORM.url + (entry && val ? (FORM.url.includes('?') ? '&' : '?') + 'usp=pp_url&' + encodeURIComponent(entry) + '=' + encodeURIComponent(val) : '');
  }

  function card(it, now) {
    const req = it.kind === 'req';
    let when = '', live = false, tag = '';
    if (!req) {
      const t = times(it); live = (t.s <= now && now <= t.e) || (it.now && now <= t.e);
      const day = fmt(t.s, t.zone, { weekday: 'short', month: 'short', day: 'numeric' });
      const theirs = t.timed ? `${hm(t.s, t.zone)}${it.end ? ' – ' + hm(t.e, t.zone) : ''} ${zoneName(t.s, t.zone)}` : 'time not given';
      const mine = t.timed && zoneName(t.s, myZone) !== zoneName(t.s, t.zone) ? `<small>Your time: ${hm(t.s, myZone)}${it.end ? ' – ' + hm(t.e, myZone) : ''} ${zoneName(t.s, myZone)}</small>` : '';
      when = `<p class="kb-when">${live ? '📡 On the air now · ' : '🗓 ' + esc(day) + ' · '}${esc(theirs)}${mine}</p>`;
      tag = live ? '<span class="kb-tag live">● ON THE AIR</span>' : '<span class="kb-tag plan">PLANNED</span>';
    } else {
      tag = '<span class="kb-tag req">🎯 PARK REQUEST</span>';
      when = `<p class="kb-when">Needs ${it.refs.length > 1 ? 'these' : 'this one'}${it.when && it.when.length ? '<small>Best time: ' + esc(it.when.join(', ')) + '</small>' : ''}</p>`;
    }
    const refs = '<ul class="kb-refs">' + it.refs.map(r => `<li><a href="${esc(refLink(r))}" target="_blank" rel="noopener"><b>${esc(r.ref)}</b></a> ${esc(r.name)}</li>`).join('') + '</ul>';
    const pills = [...(it.prog || []), ...(it.bands || []), ...(it.modes || [])].map(x => `<span>${esc(x)}</span>`).join('') + (it.extras || []).map(x => `<span class="x">${esc(x)}</span>`).join('');
    const freqs = it.freqs ? `<p class="kb-small">Frequencies: <b>${esc(it.freqs)}</b> MHz</p>` : '';
    const notes = it.notes ? `<p class="kb-note">${esc(it.notes)}</p>` : '';
    const call = esc(it.call);
    let acts = '';
    if (req) {
      const u = formUrl(FORM.parkEntry, it.refs.map(r => r.ref).join(', '));
      acts = (u ? `<a class="kb-btn green sm" href="${esc(u)}" target="_blank" rel="noopener">📻 I CAN ACTIVATE IT</a>` : '') +
        `<a class="kb-btn line sm" href="kpc-kit.html?ref=${encodeURIComponent(it.refs[0].ref)}">🎒 ACTIVATION KIT</a>`;
    } else {
      acts = `<a class="kb-btn line sm" href="kpc-live.html?spot=${encodeURIComponent(it.call.split('/')[0])}">🔎 FIND ON THE AIR</a>` +
        `<a class="kb-btn line sm" href="kpc-kit.html?ref=${encodeURIComponent(it.refs[0].ref)}">🎒 PARK KIT</a>`;
    }
    return `<article class="kb-card${live ? ' live' : ''}${req ? ' req' : ''}"><div class="kb-top"><h3 class="kb-call"><a href="https://www.qrz.com/db/${encodeURIComponent(it.call.split('/')[0])}" target="_blank" rel="noopener">${call}</a></h3>${tag}</div>${when}${refs}<div class="kb-pills">${pills}</div>${freqs}${notes}<div class="kb-acts">${acts}</div></article>`;
  }

  function match(it) {
    if (F.prog !== 'all' && !progOf(it).has(F.prog)) return false;
    if (F.ky && !inKY(it)) return false;
    if (F.q) {
      const hay = [it.call, ...(it.refs || []).flatMap(r => [r.ref, r.name]), ...(it.bands || []), ...(it.modes || []), it.notes].join(' ').toLowerCase();
      if (!F.q.toLowerCase().split(/\s+/).every(w => hay.includes(w))) return false;
    }
    return true;
  }

  function draw() {
    const now = Date.now();
    const acts = ITEMS.filter(i => i.kind === 'act').filter(i => times(i).e >= now - 15 * 60e3);
    const live = acts.filter(i => { const t = times(i); return (t.s <= now && now <= t.e) || (i.now && now <= t.e); });
    const plan = acts.filter(i => !live.includes(i));
    const reqs = ITEMS.filter(i => i.kind === 'req');
    const L = live.filter(match), P = plan.filter(match), R = reqs.filter(match);
    const none = (txt) => `<div class="kb-empty">${txt}</div>`;
    $('abLive').innerHTML = L.length ? '<div class="kb-grid">' + L.map(i => card(i, now)).join('') + '</div>' : none(live.length ? 'Nobody on the air matches your filter.' : 'Nobody has posted that they are on the air right now.');
    if (P.length) {
      let html = '', day = '';
      P.forEach(i => {
        const t = times(i), d = fmt(t.s, t.zone, { weekday: 'long', month: 'long', day: 'numeric' });
        if (d !== day) { html += (day ? '</div>' : '') + `<h3 class="kb-day">${esc(d)}</h3><div class="kb-grid">`; day = d; }
        html += card(i, now);
      });
      $('abPlan').innerHTML = html + '</div>';
    } else $('abPlan').innerHTML = none(plan.length ? 'No planned activations match your filter.' : 'No planned activations yet. Be the first: tap POST MY ACTIVATION.');
    $('abReq').innerHTML = R.length ? '<div class="kb-grid">' + R.map(i => card(i, now)).join('') + '</div>' : none(reqs.length ? 'No park requests match your filter.' : 'No park requests right now. Need a park? Tap REQUEST A PARK.');
    $('abCount').textContent = `${live.length} on the air · ${plan.length} planned · ${reqs.length} park request${reqs.length === 1 ? '' : 's'}`;
    document.querySelectorAll('#abProg .kb-chip').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.p === F.prog)));
    $('abKY').setAttribute('aria-pressed', String(F.ky));
  }
  function save() { try { localStorage.setItem('kpcAbF', JSON.stringify({ prog: F.prog, ky: F.ky })); } catch (e) {} }

  async function init() {
    document.querySelectorAll('#abProg .kb-chip').forEach(b => b.addEventListener('click', () => { F.prog = b.dataset.p; save(); draw(); }));
    $('abKY').addEventListener('click', () => { F.ky = !F.ky; save(); draw(); });
    $('abQ').addEventListener('input', () => { F.q = $('abQ').value.trim(); draw(); });
    const [d, f, ky] = await Promise.all([
      fetch('kpc-activations.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
      fetch('kpc-activations-form.json').then(r => r.json()).catch(() => ({})),
      fetch('kpc-ky-data.json').then(r => r.json()).catch(() => ({}))]);
    ITEMS = d.items || []; FORM = f || {};
    KYSET = new Set(['parks', 'kff', 'summits'].flatMap(k => (ky[k] || []).map(p => p.c)));
    if (FORM.url) {
      document.querySelectorAll('[data-ab-form]').forEach(a => { a.href = FORM.url; a.hidden = false; });
    }
    if (d.updated) $('abUpd').textContent = 'Board updated ' + new Date(d.updated.replace('Z', ':00Z')).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + ' (new posts show up within about 20 minutes).';
    draw();
    setInterval(draw, 60e3);                                       // "on the air" changes as time passes
  }
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();
