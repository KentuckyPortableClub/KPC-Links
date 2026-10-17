/* KPC log backup + sync with the member's OWN Google Drive (Brandon Oct 17 2026: 'log backup and sync… yes').
   Mounts into any <div data-kpc-drive="logger"> (KPC Logger, Download & files) or <div data-kpc-drive="hunt"> (Hunters Lounge, MY LOG FILES).
   - Google sign-in (Google Identity Services token, scope drive.file = this app can only see the files IT made in your Drive).
   - One file per app in your Drive: 'KPC Logger log.json' / 'KPC Hunters Lounge log.json'.
   - ☁ BACK UP NOW, ⇅ SYNC (merge what's in Drive with this device by contact id, then save both), and 'back up by itself' while signed in.
   - Needs the club's Google OAuth client ID in kpc-gdrive.json {"clientId": "…apps.googleusercontent.com"} (a public ID, not a secret).
     Until it's filled in, the box explains that backup is coming. Nothing goes to KPC: the file goes from this device to your Drive. */
(function () {
  const APPS = {
    logger: { key: 'kpcLogger', idb: ['kpc-logger', 'log'], file: 'KPC Logger log.json', label: 'KPC Logger', extra: ['kpcLgSet'] },
    hunt: { key: 'kpcHuntQSO', idb: ['kpc-hunt', 'qso'], file: 'KPC Hunters Lounge log.json', label: 'Hunters Lounge', extra: ['kpcHuntLog', 'kpcHuntCounts', 'kpcHuntFav', 'kpcHuntChase'] }
  };
  const SCOPE = 'https://www.googleapis.com/auth/drive.file';
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let CID = '', TOK = null, TOKexp = 0, tc = null, gisP = null;
  const css = `.kpc-drv{margin-top:12px;padding:12px 14px;border-radius:12px;border:1px solid rgba(240,201,107,.5);background:rgba(20,13,6,.6);color:#f3e6c8;font:13.5px/1.45 Arial,sans-serif}
.kpc-drv h4{margin:0 0 4px;font:900 12.5px Arial;letter-spacing:1.3px;color:#f6d58a}.kpc-drv p{margin:4px 0;color:#d9cba8}.kpc-drv .r{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:8px}
.kpc-drv button{padding:9px 13px;border-radius:999px;border:1px solid rgba(240,201,107,.55);background:#2a2310;color:#f6d58a;font:900 12px Arial;letter-spacing:.5px;cursor:pointer}
.kpc-drv button.g{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;border-color:#d5a63a}.kpc-drv label{display:inline-flex;gap:6px;align-items:center;font-size:12.5px}
.kpc-drv .st{font:700 12.5px monospace;color:#ffff9e;min-height:18px}`;
  function gis() { return gisP || (gisP = new Promise((ok, no) => { if (window.google && google.accounts && google.accounts.oauth2) return ok(); const s = document.createElement('script'); s.src = 'https://accounts.google.com/gsi/client'; s.async = true; s.onload = () => ok(); s.onerror = () => { gisP = null; no(new Error('Google sign-in did not load (no signal?)')); }; document.head.appendChild(s); })); }
  async function token(interactive) {
    if (TOK && Date.now() < TOKexp - 60e3) return TOK; if (!interactive) return null;
    await gis();
    return new Promise((ok, no) => { tc = google.accounts.oauth2.initTokenClient({ client_id: CID, scope: SCOPE, callback: r => { if (r && r.access_token) { TOK = r.access_token; TOKexp = Date.now() + (+r.expires_in || 3600) * 1000; ok(TOK); } else no(new Error((r && r.error) || 'sign-in cancelled')); }, error_callback: e => no(new Error((e && e.type) || 'sign-in closed')) });
      tc.requestAccessToken({ prompt: get('kpcDriveOK', 0) ? '' : 'consent' }); });
  }
  const api = async (url, opt) => { const r = await fetch(url, Object.assign({}, opt, { headers: Object.assign({ Authorization: 'Bearer ' + TOK }, (opt && opt.headers) || {}) })); if (r.status === 401) { TOK = null; throw new Error('Google sign-in ran out: tap again to sign in.'); } if (!r.ok) throw new Error('Google Drive answered ' + r.status); return r; };
  async function findFile(A) { const q = encodeURIComponent(`name='${A.file.replace(/'/g, "\\'")}' and trashed=false`); const r = await api(`https://www.googleapis.com/drive/v3/files?q=${q}&spaces=drive&fields=files(id,modifiedTime)&orderBy=modifiedTime desc`); const j = await r.json(); return (j.files || [])[0] || null; }
  async function readFile(id) { const r = await api(`https://www.googleapis.com/drive/v3/files/${id}?alt=media`); return r.json(); }
  async function writeFile(A, id, data) {
    const body = JSON.stringify(data);
    if (id) { await api(`https://www.googleapis.com/upload/drive/v3/files/${id}?uploadType=media`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body }); return id; }
    const b = 'kpc' + Math.random().toString(36).slice(2), meta = { name: A.file, mimeType: 'application/json', description: 'Backup of your ' + A.label + ' log (Kentucky Portable Club). Keep the name so the app can find it.' };
    const r = await api('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id', { method: 'POST', headers: { 'Content-Type': 'multipart/related; boundary=' + b }, body: `--${b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(meta)}\r\n--${b}\r\nContent-Type: application/json\r\n\r\n${body}\r\n--${b}--` });
    return (await r.json()).id;
  }
  function idbPut(db, k, v) { return new Promise(ok => { try { const r = indexedDB.open(db, 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => { try { const t = r.result.transaction('kv', 'readwrite'); t.objectStore('kv').put(v, k); t.oncomplete = () => ok(true); t.onerror = () => ok(false); } catch (e) { ok(false); } }; r.onerror = () => ok(false); } catch (e) { ok(false); } }); }
  const local = A => { const L = get(A.key, null); return L && Array.isArray(L.q) ? L : { v: 1, u: 0, q: [] }; };
  function pack(A) { const x = {}; A.extra.forEach(k => { const v = get(k, null); if (v != null) x[k] = v; }); return { app: A.label, v: 1, saved: new Date().toISOString(), log: local(A), extra: x }; }
  const qid = q => q.id || [q.call, q.d, q.tm, q.band, q.mode].join('|');
  function merge(a, b) { const M = new Map(); (a.q || []).forEach(q => M.set(qid(q), q)); let added = 0; (b.q || []).forEach(q => { if (!M.has(qid(q))) { M.set(qid(q), q); added++; } }); return { log: Object.assign({}, b, a, { q: [...M.values()].sort((x, y) => (x.t || 0) - (y.t || 0)), u: Date.now() + 1 }), added }; }
  function mount(el) {
    const A = APPS[el.dataset.kpcDrive]; if (!A || el.dataset.done) return; el.dataset.done = 1;
    if (!document.getElementById('kpc-drv-css')) { const s = document.createElement('style'); s.id = 'kpc-drv-css'; s.textContent = css; document.head.appendChild(s); }
    el.className = 'kpc-drv'; el.setAttribute('data-keep-light', '');
    if (!CID) { el.innerHTML = `<h4>☁ GOOGLE DRIVE BACKUP &amp; SYNC</h4><p>Coming soon: keep your ${esc(A.label)} log in your own Google Drive so it follows you from your phone to your computer. Until then, use the download buttons above now and then.</p>`; return; }
    const S = Object.assign({ auto: true, last: 0, id: '' }, get('kpcDrive:' + el.dataset.kpcDrive, {})), sv = () => put('kpcDrive:' + el.dataset.kpcDrive, S);
    el.innerHTML = `<h4>☁ GOOGLE DRIVE BACKUP &amp; SYNC</h4><p>Keeps a copy of your ${esc(A.label)} log in <b>your own</b> Google Drive (file "${esc(A.file)}"), so it follows you from phone to computer. On each device: sign in once, then tap ⇅ SYNC.</p>
      <div class="r"><button type="button" class="g" data-d="up">☁ BACK UP NOW</button><button type="button" data-d="sync">⇅ SYNC WITH MY DRIVE</button><label><input type="checkbox" data-d="auto"${S.auto ? ' checked' : ''}> Back up by itself while I'm signed in</label></div>
      <div class="st" aria-live="polite"></div>`;
    const st = t => { el.querySelector('.st').textContent = t; }, when = () => S.last ? 'Last backup ' + new Date(S.last).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + '.' : 'Not backed up to Drive yet.';
    st(when());
    async function up(interactive) { if (!(await token(interactive))) return false; put('kpcDriveOK', 1); if (!S.id) { const f = await findFile(A); S.id = f ? f.id : ''; } try { S.id = await writeFile(A, S.id, pack(A)); } catch (e) { if (/404/.test(e.message)) { S.id = ''; S.id = await writeFile(A, '', pack(A)); } else throw e; } S.last = Date.now(); S.u = local(A).u; sv(); st('✅ Backed up ' + local(A).q.length + ' contacts. ' + when()); return true; }
    el.addEventListener('click', async e => { const b = e.target.closest('button[data-d]'); if (!b) return;
      try {
        if (b.dataset.d === 'up') { st('☁ Backing up…'); await up(true); }
        if (b.dataset.d === 'sync') { st('⇅ Signing in and reading your Drive…'); if (!(await token(true))) return; put('kpcDriveOK', 1); const f = await findFile(A); S.id = f ? f.id : '';
          let added = 0; if (f) { const R = await readFile(f.id); const m = merge(local(A), (R && R.log) || {}); added = m.added; put(A.key, m.log); await idbPut(A.idb[0], A.idb[1], JSON.parse(JSON.stringify(m.log))); if (R && R.extra) Object.entries(R.extra).forEach(([k, v]) => { if (get(k, null) == null) put(k, v); }); }
          await up(false); st(added ? `✅ Synced: ${added} contact${added === 1 ? '' : 's'} came in from your Drive. Reloading…` : '✅ Synced: this device and your Drive match.'); if (added) setTimeout(() => location.reload(), 1200); }
      } catch (x) { st('⚠️ ' + (x.message || x)); } });
    el.querySelector('[data-d="auto"]').onchange = e => { S.auto = e.target.checked; sv(); };
    setInterval(() => { if (!S.auto || !TOK || Date.now() >= TOKexp - 60e3) return; const u = local(A).u || 0; if (u && u !== S.u) up(false).catch(() => {}); }, 45000);
  }
  function scan() { document.querySelectorAll('[data-kpc-drive]').forEach(mount); }
  fetch('kpc-gdrive.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : {}).catch(() => ({})).then(j => { CID = String((j && j.clientId) || '').trim(); if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan); else scan(); setTimeout(scan, 2500); });
  window.KPCDrive = { scan };
})();
