/* KPC holiday picture on the home page (Brandon Oct 26 2026: 'show the holiday picture from a few days before through the day, then back
   to normal by itself'). Everything comes from data/holidays.json (dates, picture, text, effect). Nothing to edit each year.
   - A holiday shows only when its entry has "go": true (HQ / Brandon's switch), today is between (date - show_days) and the date,
     in the visitor's own clock. Rule dates (easter, 'last monday of 05', 'fourth full weekend of 06'…) are worked out here.
   - Preview for Brandon: index.html?holiday=halloween (any id) shows that picture whatever the date or switch. Nothing links to it.
   - Light effect over the picture (leaves, bats, snow, hearts, petals, clovers): canvas, ~30 frames/s, pauses when the tab or the
     picture is off screen, off with reduced motion and when printing, a small button stops it (remembered), and on phones it stops by
     itself after ~30 s. 'none' = no effect. sparks / fireworks are not drawn yet (picture only). */
(function () {
  'use strict';
  var DOW = { sunday: 0, monday: 1, tuesday: 2, wednesday: 3, thursday: 4, friday: 5, saturday: 6 };
  var NTH = { first: 1, second: 2, third: 3, fourth: 4, fifth: 5 };

  function nthDow(y, m, dow, n) { var off = (dow - new Date(y, m, 1).getDay() + 7) % 7; return new Date(y, m, 1 + off + 7 * (n - 1)); }
  function lastDow(y, m, dow) { var last = new Date(y, m + 1, 0); return new Date(y, m, last.getDate() - ((last.getDay() - dow + 7) % 7)); }
  function easter(y) {   /* Gregorian computus */
    var a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25),
      g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4,
      l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451),
      mo = Math.floor((h + l - 7 * m + 114) / 31), da = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(y, mo - 1, da);
  }
  /* -> {date, span}: the day of the holiday and how many extra days it lasts (Field Day = Saturday + Sunday) */
  function when(h, y) {
    if (h.date) { var p = h.date.split('-'); return { date: new Date(y, +p[0] - 1, +p[1]), span: 0 }; }
    var r = String(h.rule || '').toLowerCase().trim(), m;
    if (r === 'easter') return { date: easter(y), span: 0 };
    if ((m = r.match(/^(first|second|third|fourth|fifth) full weekend of (\d\d)$/))) {   /* Saturday AND Sunday both in the month */
      var mo = +m[2] - 1, n = NTH[m[1]], cnt = 0;
      for (var d = 1; d <= 31; d++) {
        var s = new Date(y, mo, d); if (s.getMonth() !== mo) break;
        if (s.getDay() === 6 && new Date(y, mo, d + 1).getMonth() === mo && ++cnt === n) return { date: s, span: 1 };
      }
      return null;
    }
    if ((m = r.match(/^(first|second|third|fourth|fifth|last) (sunday|monday|tuesday|wednesday|thursday|friday|saturday) of (\d\d)$/))) {
      var mm = +m[3] - 1, dw = DOW[m[2]];
      return { date: m[1] === 'last' ? lastDow(y, mm, dw) : nthDow(y, mm, dw, NTH[m[1]]), span: 0 };
    }
    return null;
  }
  function inWindow(h, today) {
    var w = when(h, today.getFullYear()); if (!w) return false;
    var start = new Date(w.date.getFullYear(), w.date.getMonth(), w.date.getDate() - (h.show_days || 3));
    var end = new Date(w.date.getFullYear(), w.date.getMonth(), w.date.getDate() + (w.span || 0));
    return today >= start && today <= end;
  }
  window.KPCHoliday = { when: when, easter: easter, inWindow: inWindow };   /* exposed for testing */

  var q = ''; try { q = new URLSearchParams(location.search).get('holiday') || ''; } catch (e) {}
  var now = new Date(), today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  function start(list) {
    var pick = null;
    if (q) { for (var i = 0; i < list.length; i++) if (list[i].id === q) pick = list[i]; }
    else {
      for (var j = 0; j < list.length; j++) if (list[j].go === true && list[j].img && inWindow(list[j], today)) { pick = list[j]; break; }
    }
    if (pick && pick.img) show(pick);
  }

  function esc(s) { return String(s || '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function show(h) {
    var main = document.querySelector('main'); if (!main) return;
    var css = document.createElement('style');
    css.textContent = '.kpc-hol{background:#0b0b0b;padding:18px 16px 22px;text-align:center;border-bottom:1px solid #2a2a2a}' +
      '.kpc-hol figure{margin:0 auto;max-width:980px}' +
      '.kpc-hol-box{position:relative;display:block;border:2px solid #d5a63a;border-radius:14px;overflow:hidden;background:#070707;box-shadow:0 10px 34px rgba(0,0,0,.6),0 0 0 1px rgba(240,201,107,.25)}' +
      '.kpc-hol-box img{display:block;width:100%;height:auto;max-height:78vh;object-fit:contain;margin:0 auto}' +
      '.kpc-hol-box canvas{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}' +
      '.kpc-hol-stop{position:absolute;right:8px;bottom:8px;z-index:2;font:700 11px/1 Arial,Helvetica,sans-serif;letter-spacing:.6px;color:#f3e6c8;background:rgba(10,10,10,.72);border:1px solid rgba(240,201,107,.55);border-radius:999px;padding:8px 12px;cursor:pointer;min-height:32px}' +
      '.kpc-hol-stop:hover,.kpc-hol-stop:focus-visible{background:#2d5440;outline:none}' +
      '.kpc-hol figcaption{margin:14px auto 0;max-width:760px;color:#f3e6c8;font:italic 18px/1.5 Georgia,"Times New Roman",serif}' +
      '@media(max-width:600px){.kpc-hol{padding:12px 10px 16px}.kpc-hol figcaption{font-size:16px}}' +
      '@media print{.kpc-hol canvas,.kpc-hol-stop{display:none!important}}';
    document.head.appendChild(css);
    var sec = document.createElement('section');
    sec.className = 'kpc-hol'; sec.setAttribute('data-keep-light', ''); sec.setAttribute('aria-label', h.name || 'Holiday greeting');
    var fx = parseFx(h.effect);
    sec.innerHTML = '<figure><div class="kpc-hol-box"><img src="' + esc(h.img) + '" alt="' + esc((h.name || 'Holiday') + ' greeting from the Kentucky Portable Club') + '" decoding="async">' +
      (fx.length ? '<canvas aria-hidden="true"></canvas><button type="button" class="kpc-hol-stop" aria-pressed="false">STOP ANIMATION</button>' : '') +
      '</div>' + (h.post ? '<figcaption>' + esc(h.post) + '</figcaption>' : '') + '</figure>';
    main.insertBefore(sec, main.firstChild);
    if (fx.length) effects(sec, fx);
  }

  function parseFx(s) {
    var ok = { leaves: 1, bats: 1, snow: 1, hearts: 1, petals: 1, clovers: 1 }, out = [];
    String(s || '').split('+').forEach(function (x) { x = x.trim(); if (ok[x]) out.push(x); });
    return out;
  }

  function effects(sec, fx) {
    var reduce = false; try { reduce = matchMedia('(prefers-reduced-motion:reduce)').matches; } catch (e) {}
    var btn = sec.querySelector('.kpc-hol-stop'), cv = sec.querySelector('canvas'), box = sec.querySelector('.kpc-hol-box');
    if (reduce) { btn.hidden = true; cv.hidden = true; return; }
    var stored = ''; try { stored = localStorage.getItem('kpcHolFx') || ''; } catch (e) {}
    var on = stored !== 'off', phone = false, visible = true, raf = 0, last = 0, t0 = 0, W = 0, H = 0, dpr = 1;
    try { phone = matchMedia('(max-width:760px),(pointer:coarse)').matches; } catch (e) {}
    var ctx = cv.getContext('2d'); if (!ctx) { btn.hidden = true; return; }
    var parts = [], bat = null, nextBat = 1800, wantLeaf = fx.indexOf('leaves') >= 0, wantBat = fx.indexOf('bats') >= 0;
    var shape = null; ['snow', 'hearts', 'petals', 'clovers'].forEach(function (k) { if (fx.indexOf(k) >= 0) shape = k; });
    var rnd = function (a, b) { return a + Math.random() * (b - a); };
    var COL = { leaves: ['#d9531e', '#e8812b', '#f0b429', '#b5381c', '#c9702a'], snow: ['#ffffff', '#e8f1ff'], hearts: ['#e0506e', '#ff8fa8', '#c2284d'],
      petals: ['#f7c6d9', '#fff1b8', '#ffd6e8', '#e6d6ff'], clovers: ['#2e9a4f', '#46b865', '#1f7a3b'] };

    function size() {
      var r = box.getBoundingClientRect(); dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      W = Math.max(1, Math.round(r.width)); H = Math.max(1, Math.round(r.height));
      cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function mk(kind, initial) {
      var s = kind === 'snow' ? rnd(1.5, 4) : rnd(7, 15), cols = COL[kind];
      return { k: kind, x: rnd(0, W), y: initial ? rnd(-H * .1, H) : rnd(-30, -6), s: s, vy: kind === 'snow' ? rnd(18, 40) : rnd(22, 48),
        amp: rnd(14, 38), ph: rnd(0, 6.28), fr: rnd(.5, 1.3), rot: rnd(0, 6.28), vr: rnd(-1.6, 1.6), c: cols[(Math.random() * cols.length) | 0] };
    }
    function fill() {
      parts = []; var n = phone ? 10 : 16;
      for (var i = 0; i < n; i++) {
        if (wantLeaf) parts.push(mk('leaves', true));
        else if (shape) parts.push(mk(shape, true));
      }
      if (wantLeaf && shape) for (var j = 0; j < n; j++) parts.push(mk(shape, true));
    }
    function drawPart(p) {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillStyle = p.c; ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = .8; var s = p.s;
      if (p.k === 'leaves') {
        ctx.beginPath(); ctx.moveTo(0, -s); ctx.quadraticCurveTo(s * .95, -s * .1, 0, s); ctx.quadraticCurveTo(-s * .95, -s * .1, 0, -s); ctx.fill();
        ctx.beginPath(); ctx.moveTo(0, -s * .8); ctx.lineTo(0, s * 1.25); ctx.stroke();
      } else if (p.k === 'snow') { ctx.beginPath(); ctx.arc(0, 0, s, 0, 6.283); ctx.fill(); }
      else if (p.k === 'hearts') {
        ctx.beginPath(); ctx.moveTo(0, s * .9); ctx.bezierCurveTo(-s * 1.4, -s * .2, -s * .6, -s * 1.1, 0, -s * .35); ctx.bezierCurveTo(s * .6, -s * 1.1, s * 1.4, -s * .2, 0, s * .9); ctx.fill();
      } else if (p.k === 'petals') { ctx.beginPath(); ctx.ellipse(0, 0, s * .55, s, 0, 0, 6.283); ctx.fill(); }
      else if (p.k === 'clovers') {
        for (var a = 0; a < 4; a++) { ctx.beginPath(); ctx.arc(Math.cos(a * 1.571) * s * .5, Math.sin(a * 1.571) * s * .5, s * .5, 0, 6.283); ctx.fill(); }
      }
      ctx.restore();
    }
    function drawBat(b, t) {
      var f = Math.sin(t * 0.022 + b.ph) , w = b.s;   /* wing flap */
      ctx.save(); ctx.translate(b.x, b.y); if (b.dir < 0) ctx.scale(-1, 1); ctx.fillStyle = '#0a0a0a'; ctx.strokeStyle = 'rgba(255,170,70,.35)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.ellipse(0, 0, w * .16, w * .3, 0, 0, 6.283); ctx.fill();                       /* body */
      ctx.beginPath(); ctx.moveTo(-w * .08, -w * .28); ctx.lineTo(-w * .04, -w * .42); ctx.lineTo(0, -w * .3); ctx.lineTo(w * .04, -w * .42); ctx.lineTo(w * .08, -w * .28); ctx.fill();   /* ears */
      [-1, 1].forEach(function (sd) {
        ctx.beginPath(); ctx.moveTo(sd * w * .1, -w * .05);
        ctx.quadraticCurveTo(sd * w * .6, -w * (.55 + f * .35), sd * w * 1.05, -w * (.1 + f * .55));
        ctx.quadraticCurveTo(sd * w * .85, w * .05, sd * w * .68, w * .12);
        ctx.quadraticCurveTo(sd * w * .5, w * .02, sd * w * .38, w * .22);
        ctx.quadraticCurveTo(sd * w * .24, w * .06, sd * w * .1, w * .2);
        ctx.closePath(); ctx.fill(); ctx.stroke();
      });
      ctx.restore();
    }
    function spawnBat() {
      var dir = Math.random() < .5 ? 1 : -1, s = Math.max(22, Math.min(46, W * .05));
      bat = { dir: dir, x: dir > 0 ? -s * 1.5 : W + s * 1.5, y0: rnd(H * .08, H * .42), y: 0, v: rnd(W * .16, W * .26), s: s, ph: rnd(0, 6.28), t: 0 };
    }
    function frame(ts) {
      raf = 0; if (!on || !visible || document.hidden) return;
      raf = requestAnimationFrame(frame);
      if (ts - last < 33) return; var dt = Math.min(.1, (ts - (last || ts)) / 1000); last = ts;
      if (!t0) t0 = ts;
      if (phone && ts - t0 > 30000) { stop(true); return; }
      ctx.clearRect(0, 0, W, H);
      parts.forEach(function (p) {
        p.y += p.vy * dt; p.ph += p.fr * dt; p.x += Math.sin(p.ph) * p.amp * dt; p.rot += p.vr * dt;
        if (p.y > H + 20 || p.x < -40 || p.x > W + 40) { var n = mk(p.k, false); p.x = n.x; p.y = n.y; p.vy = n.vy; p.c = n.c; p.s = n.s; }
        drawPart(p);
      });
      if (wantBat) {
        if (!bat) { nextBat -= dt * 1000; if (nextBat <= 0) { spawnBat(); nextBat = rnd(8000, 14000); } }
        if (bat) {
          bat.t += dt; bat.x += bat.dir * bat.v * dt; bat.y = bat.y0 + Math.sin(bat.t * 3.1) * H * .035;
          drawBat(bat, ts);
          if ((bat.dir > 0 && bat.x > W + bat.s * 1.6) || (bat.dir < 0 && bat.x < -bat.s * 1.6)) bat = null;
        }
      }
    }
    function run() { if (on && visible && !document.hidden && !raf) { last = 0; raf = requestAnimationFrame(frame); } }
    function stop(auto) {
      on = false; if (raf) { cancelAnimationFrame(raf); raf = 0; } ctx.clearRect(0, 0, W, H);
      btn.textContent = auto ? 'PLAY ANIMATION' : 'PLAY ANIMATION'; btn.setAttribute('aria-pressed', 'true');
    }
    btn.addEventListener('click', function () {
      if (on) { stop(false); try { localStorage.setItem('kpcHolFx', 'off'); } catch (e) {} }
      else { on = true; t0 = 0; btn.textContent = 'STOP ANIMATION'; btn.setAttribute('aria-pressed', 'false'); try { localStorage.removeItem('kpcHolFx'); } catch (e) {} run(); }
    });
    var go = function () {
      size(); fill();
      if (!on) { btn.textContent = 'PLAY ANIMATION'; btn.setAttribute('aria-pressed', 'true'); }
      if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; if (visible) run(); }, { threshold: .05 }).observe(box);
      document.addEventListener('visibilitychange', run);
      window.addEventListener('resize', function () { size(); });
      run();
    };
    var img = box.querySelector('img');
    if (img.complete && img.naturalWidth) go(); else img.addEventListener('load', go, { once: true });
    window.KPCHolidayFx = { frame: function () { return { parts: parts.length, bat: !!bat, on: on }; }, bat: function () { spawnBat(); } };   /* test hooks */
  }

  function init() {
    fetch('data/holidays.json?t=' + Math.floor(Date.now() / 36e5), { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) { start((d && d.holidays) || []); })
      .catch(function () {});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
