/* KPC Voice Keyer (Brandon Oct 17 2026: 'record CQ POTA once and play it through the radio with PTT, repeat every X seconds… several
   buttons that can be renamed'). Shared by the KPC Logger and the VIP Hunters Lounge: any element with [data-vk-open] opens it.
   - 6 memory buttons, each recorded with the phone / computer microphone (up to 30 s), renamed with ✏️, kept on this device only
     (IndexedDB kpc-vk; names in localStorage kpcVk).
   - ▶ plays it out to the radio: same audio output and PTT (VOX / CAT / RTS / DTR) as the DIGI tab (localStorage kpcFt8 outDev / ptt).
   - 🔁 REPEAT: plays again every N seconds until STOP, Esc, or you start typing a call in the log.
   - Keyboard: Alt+1 … Alt+6 plays a memory, Esc stops. */
(function () {
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const DEF = (hunt) => hunt ? ['MY CALL', 'MY CALL x2', 'THANK YOU 73', 'QSL', 'AGAIN?', 'SPARE'] : ['CQ POTA', 'QRZ?', 'THANK YOU 73', 'MY CALL', 'PARK INFO', 'SPARE'];
  const V = Object.assign({ names: null, rep: false, sec: 15, lvl: 0.85, inDev: '' }, get('kpcVk', {}));
  const save = () => put('kpcVk', V);
  const hunt = () => { try { return !!(window.KPCLog && KPCLog.me().hunt); } catch (e) { return false; } };
  const names = () => V.names || DEF(hunt());
  const FT = () => get('kpcFt8', {});
  /* storage: IndexedDB keeps the recordings (Blobs) */
  function db() { return new Promise((ok, no) => { try { const r = indexedDB.open('kpc-vk', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => ok(r.result); r.onerror = no; } catch (e) { no(e); } }); }
  const idb = (mode, fn) => db().then(d => new Promise((ok, no) => { const t = d.transaction('kv', mode), s = t.objectStore('kv'), q = fn(s); t.oncomplete = () => ok(q && q.result); t.onerror = no; }));
  const getRec = i => idb('readonly', s => s.get('m' + i)).catch(() => null);
  const putRec = (i, v) => idb('readwrite', s => s.put(v, 'm' + i));
  const delRec = i => idb('readwrite', s => s.delete('m' + i));
  const LEN = {};
  /* screen */
  const css = `#kpcVk{position:fixed;inset:0;z-index:2147482000;display:flex;align-items:center;justify-content:center;padding:14px;background:rgba(0,0,0,.6)}
#kpcVk[hidden]{display:none}#kpcVk .vb{position:relative;width:min(560px,100%);max-height:calc(100vh - 28px);overflow:auto;padding:18px 16px 14px;border-radius:16px;background:rgba(20,13,6,.97);border:1px solid rgba(240,201,107,.6);box-shadow:0 0 34px rgba(240,201,107,.25);color:#f3e6c8;font:14px/1.45 Arial,sans-serif}
#kpcVk h3{margin:0 0 4px;font:900 15px Arial;letter-spacing:1.4px;color:#f6d58a}#kpcVk .x{position:absolute;top:10px;right:12px;padding:6px 11px;border-radius:999px;border:1px solid rgba(240,201,107,.5);background:#2a2310;color:#f6d58a;font-weight:900;cursor:pointer}
#kpcVk p{margin:4px 0 10px;color:#d9cba8;font-size:13px}#kpcVk .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
#kpcVk .m{border:1px solid rgba(240,201,107,.35);border-radius:12px;padding:8px;background:#100c06}#kpcVk .m.play{border-color:#ff5c5c;box-shadow:0 0 0 2px rgba(255,92,92,.35)}
#kpcVk .m .nm{display:flex;justify-content:space-between;align-items:center;gap:6px;font:900 12px Arial;letter-spacing:.6px;color:#f6d58a}#kpcVk .m .nm small{font-weight:700;color:#a99c80;letter-spacing:0}
#kpcVk .m .bt{display:flex;gap:6px;margin-top:6px}#kpcVk button{cursor:pointer}
#kpcVk .m .bt button{flex:1;padding:10px 6px;border-radius:10px;border:1px solid rgba(240,201,107,.45);background:#2a2310;color:#f6d58a;font:900 12.5px Arial}
#kpcVk .m .bt .pl{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;border-color:#d5a63a;flex:2}#kpcVk .m .bt .rc.on{background:#c0392b;color:#fff;border-color:#ff8a7a}
#kpcVk .m .bt button:disabled{opacity:.4;cursor:default}#kpcVk .row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px;font-size:13px}
#kpcVk .row select,#kpcVk .row input[type=range]{max-width:210px}#kpcVk select{padding:5px;border-radius:8px;background:#0d0904;color:#f3e6c8;border:1px solid rgba(240,201,107,.5)}
#kpcVk .stop{padding:11px 18px;border-radius:999px;border:0;background:#c0392b;color:#fff;font:900 13px Arial;letter-spacing:.6px}
#kpcVk .st{min-height:20px;margin-top:8px;color:#ffff9e;font:700 13px monospace}#kpcVk .note{font-size:12px;color:#a99c80}
@media(max-width:420px){#kpcVk .grid{grid-template-columns:1fr}}`;
  let box = null;
  function build() {
    if (box) return; const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    box = document.createElement('div'); box.id = 'kpcVk'; box.hidden = true; box.setAttribute('data-keep-light', ''); box.setAttribute('role', 'dialog'); box.setAttribute('aria-label', 'Voice keyer');
    box.innerHTML = `<div class="vb"><button type="button" class="x" data-vkx>✕</button><h3>🎙 VOICE KEYER</h3>
      <p>Record each button once with this phone or computer's microphone, then ▶ plays it to the radio and keys it. Tap ✏️ to rename a button.</p>
      <div class="grid" id="vkGrid"></div>
      <div class="row"><label><input type="checkbox" id="vkRep"> 🔁 Repeat every</label><select id="vkSec">${[5, 8, 10, 15, 20, 30, 45, 60].map(s => `<option value="${s}">${s} seconds</option>`).join('')}</select><span class="note">until STOP, or you start typing a call</span></div>
      <div class="row"><button type="button" class="stop" id="vkStop">■ STOP</button><label>LEVEL <input type="range" id="vkLvl" min="0.1" max="1" step="0.05"></label></div>
      <div class="st" id="vkSt" aria-live="polite"></div>
      <div class="row"><label>RECORD WITH <select id="vkIn"><option value="">Default microphone</option></select></label></div>
      <p class="note" id="vkOut"></p></div>`;
    document.body.appendChild(box);
    box.addEventListener('click', e => { if (e.target === box || e.target.closest('[data-vkx]')) close(); const b = e.target.closest('[data-vk]'); if (!b) return; const i = +b.dataset.i, a = b.dataset.vk;
      if (a === 'play') play(i); else if (a === 'rec') rec(i); else if (a === 'ren') ren(i); else if (a === 'del') del(i); });
    box.querySelector('#vkRep').onchange = e => { V.rep = e.target.checked; save(); };
    box.querySelector('#vkSec').onchange = e => { V.sec = +e.target.value; save(); };
    box.querySelector('#vkLvl').oninput = e => { V.lvl = +e.target.value; save(); };
    box.querySelector('#vkIn').onchange = e => { V.inDev = e.target.value; save(); };
    box.querySelector('#vkStop').onclick = stop;
  }
  async function draw() {
    const N = names(); for (let i = 0; i < 6; i++) { if (LEN[i] === undefined) { const r = await getRec(i); LEN[i] = r && r.len ? r.len : 0; } }
    box.querySelector('#vkGrid').innerHTML = N.map((n, i) => `<div class="m${PLAYING === i ? ' play' : ''}"><div class="nm"><span>${i + 1} · ${esc(n)}</span><small>${LEN[i] ? LEN[i].toFixed(1) + ' s' : 'empty'}</small></div>
      <div class="bt"><button type="button" class="pl" data-vk="play" data-i="${i}"${LEN[i] ? '' : ' disabled'}>▶ PLAY</button><button type="button" class="rc${RECI === i ? ' on' : ''}" data-vk="rec" data-i="${i}">${RECI === i ? '■ DONE' : '● REC'}</button><button type="button" data-vk="ren" data-i="${i}" title="Rename">✏️</button>${LEN[i] ? `<button type="button" data-vk="del" data-i="${i}" title="Erase">🗑</button>` : ''}</div></div>`).join('');
    box.querySelector('#vkRep').checked = !!V.rep; box.querySelector('#vkSec').value = String(V.sec); box.querySelector('#vkLvl').value = V.lvl;
    const f = FT(); box.querySelector('#vkOut').textContent = `Plays through: ${f.outDev ? 'the audio output picked in the DIGI tab' : 'this device\'s normal speaker / audio output'} · keys with ${({ vox: 'VOX (turn VOX on at the radio)', cat: 'CAT', rts: 'the RTS line', dtr: 'the DTR line' })[f.ptt || 'vox']}. Change both in the DIGI tab → ⚙ AUDIO, PTT & SETTINGS.`;
    try { const d = await navigator.mediaDevices.enumerateDevices(), sel = box.querySelector('#vkIn'); sel.innerHTML = '<option value="">Default microphone</option>' + d.filter(x => x.kind === 'audioinput').map((x, k) => `<option value="${esc(x.deviceId)}"${x.deviceId === V.inDev ? ' selected' : ''}>${esc(x.label || 'Microphone ' + (k + 1))}</option>`).join(''); } catch (e) {}
  }
  function open() { build(); box.hidden = false; draw(); }
  function close() { if (box) box.hidden = true; }
  const say = t => { if (box) box.querySelector('#vkSt').textContent = t; };
  function ren(i) { const N = names().slice(); const v = prompt('Name for button ' + (i + 1), N[i]); if (v === null) return; N[i] = v.trim().toUpperCase().slice(0, 18) || N[i]; V.names = N; save(); draw(); }
  async function del(i) { if (!confirm('Erase the recording on "' + names()[i] + '"?')) return; await delRec(i).catch(() => {}); LEN[i] = 0; draw(); }
  /* record */
  let REC = null, RECI = -1, recT = null;
  async function rec(i) {
    if (RECI === i && REC) { REC.stop(); return; } if (REC) return; stop();
    let stream; try { stream = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: V.inDev ? { exact: V.inDev } : undefined, echoCancellation: true, noiseSuppression: true, autoGainControl: true } }); }
    catch (e) { say('⚠️ The microphone is blocked: allow it for this site and try again.'); return; }
    const chunks = [], mr = new MediaRecorder(stream); REC = mr; RECI = i; const t0 = Date.now(); draw();
    mr.ondataavailable = e => { if (e.data && e.data.size) chunks.push(e.data); };
    mr.onstop = async () => { clearInterval(recT); stream.getTracks().forEach(t => t.stop()); REC = null; RECI = -1; const blob = new Blob(chunks, { type: mr.mimeType || 'audio/webm' }), len = (Date.now() - t0) / 1000;
      if (len < 0.4) { say('Too short: hold on a second longer.'); draw(); return; }
      try { await putRec(i, { blob, len, t: Date.now() }); LEN[i] = len; say(`✅ Saved "${names()[i]}" (${len.toFixed(1)} s). Tap ▶ PLAY to hear it on the radio.`); } catch (e) { say('⚠️ Could not save it on this device.'); }
      draw(); };
    mr.start(); say('● Recording "' + names()[i] + '"… speak now, then tap ■ DONE (stops by itself at 30 s).');
    recT = setInterval(() => { const s = (Date.now() - t0) / 1000; if (s >= 30 && mr.state === 'recording') mr.stop(); else say(`● Recording "${names()[i]}"… ${s.toFixed(0)} s  (tap ■ DONE)`); }, 250);
  }
  /* play */
  let AC = null, SRC = null, PLAYING = -1, repT = null, cdT = null, gen = 0;
  async function ptt(on) { const f = FT(), via = f.ptt || 'vox'; if (via === 'vox' || !window.KPCCat) return; try { await KPCCat.ptt(on, via); } catch (e) {} }
  async function play(i, again) {
    if (REC) return; const my = again ? gen : ++gen; clearTimeout(repT); clearInterval(cdT); if (!again) stopSound();
    const r = await getRec(i); if (!r || !r.blob) { say('Record this button first (● REC).'); return; }
    try { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); await AC.resume(); const f = FT(); if (f.outDev && AC.setSinkId) { try { await AC.setSinkId(f.outDev); } catch (e) {} } } catch (e) { say('⚠️ Audio is not available.'); return; }
    let buf; try { buf = await AC.decodeAudioData(await r.blob.arrayBuffer()); } catch (e) { say('⚠️ That recording could not be played. Record it again.'); return; }
    if (my !== gen) return;
    let pk = 0; for (let c = 0; c < buf.numberOfChannels; c++) { const d = buf.getChannelData(c); for (let k = 0; k < d.length; k += 4) pk = Math.max(pk, Math.abs(d[k])); }
    const g = AC.createGain(); g.gain.value = (pk > 0 ? 0.9 / pk : 1) * V.lvl; const src = AC.createBufferSource(); src.buffer = buf; src.connect(g); g.connect(AC.destination); SRC = src; PLAYING = i; if (box && !box.hidden) draw();
    await ptt(true); await new Promise(z => setTimeout(z, 180)); if (my !== gen) { ptt(false); return; }
    say(`▶ On the air: "${names()[i]}"`); window.KPCVKbusy = true;
    src.onended = async () => { if (SRC !== src) return; SRC = null; await new Promise(z => setTimeout(z, 120)); await ptt(false); PLAYING = -1; window.KPCVKbusy = false; if (box && !box.hidden) draw();
      if (V.rep && my === gen) { let left = V.sec; say(`🔁 Listening… "${names()[i]}" again in ${left} s (start typing a call to stop)`); cdT = setInterval(() => { left--; if (left > 0) say(`🔁 Listening… "${names()[i]}" again in ${left} s (start typing a call to stop)`); }, 1000);
        repT = setTimeout(() => { clearInterval(cdT); if (my === gen) play(i, true); }, V.sec * 1000); }
      else say(`✓ Sent "${names()[i]}".`); };
    src.start();
  }
  function stopSound() { if (SRC) { const s = SRC; SRC = null; try { s.stop(); } catch (e) {} ptt(false); } PLAYING = -1; window.KPCVKbusy = false; }
  function stop(quiet) { gen++; clearTimeout(repT); clearInterval(cdT); const was = !!SRC; stopSound(); if (REC) REC.stop(); if (box && !box.hidden) draw(); if (quiet !== true) say(was ? '■ Stopped.' : ''); }
  /* typing a call stops the repeat (someone answered) */
  document.addEventListener('input', e => { if (!e.target || !/^(eCall|dCall|cwCall|dgCall)$/.test(e.target.id)) return; if (repT || SRC) { stop(true); say('■ Stopped: you started logging a call.'); toastish('🎙 Voice keyer stopped: go get them!'); } });
  function toastish(t) { try { const n = document.createElement('div'); n.textContent = t; n.style.cssText = 'position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:2147482500;padding:10px 16px;border-radius:999px;background:#2a2310;color:#f6d58a;border:1px solid rgba(240,201,107,.6);font:900 13px Arial;box-shadow:0 6px 20px rgba(0,0,0,.4)'; document.body.appendChild(n); setTimeout(() => n.remove(), 2600); } catch (e) {} }
  addEventListener('keydown', e => { if (e.key === 'Escape' && (SRC || repT)) { stop(); return; } if (e.altKey && /^[1-6]$/.test(e.key)) { e.preventDefault(); play(+e.key - 1); } });
  document.addEventListener('click', e => { const b = e.target.closest('[data-vk-open]'); if (b) { e.preventDefault(); open(); } });
  window.KPCVK = { open, close, play, stop };
})();
