/* KPC CW Info & Links: plays the example exchanges ([data-say] buttons) as Morse.
   Small and self-contained (the full simulator lives in kpc-cw.js on the Practice Room page).
   Speed and tone come from the #saySpeed / #sayTone pickers when present. */
(function () {
  var CODE = {A:'.-',B:'-...',C:'-.-.',D:'-..',E:'.',F:'..-.',G:'--.',H:'....',I:'..',J:'.---',K:'-.-',L:'.-..',M:'--',N:'-.',O:'---',P:'.--.',Q:'--.-',R:'.-.',S:'...',T:'-',U:'..-',V:'...-',W:'.--',X:'-..-',Y:'-.--',Z:'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',
    '/':'-..-.','?':'..--..','.':'.-.-.-',',':'--..--','=':'-...-','-':'-....-'};
  var ctx = null, playing = null;
  function ac() { if (!ctx) { var A = window.AudioContext || window.webkitAudioContext; if (!A) return null; ctx = new A(); } if (ctx.state === 'suspended') ctx.resume(); return ctx; }
  function val(id, d) { var e = document.getElementById(id); var n = e ? Number(e.value) : NaN; return isFinite(n) && n > 0 ? n : d; }
  function stop() { if (playing) { try { playing.g.gain.cancelScheduledValues(0); playing.g.gain.setValueAtTime(0, ctx.currentTime); playing.o.stop(); } catch (e) {} if (playing.btn) playing.btn.classList.remove('on'); playing = null; } }
  function play(text, btn) {
    var c = ac(); if (!c) return;
    stop();
    var wpm = val('saySpeed', 20), hz = val('sayTone', 600), u = 1.2 / wpm;
    var o = c.createOscillator(), g = c.createGain();
    o.type = 'sine'; o.frequency.value = hz; g.gain.value = 0; o.connect(g); g.connect(c.destination);
    var t = c.currentTime + 0.08, r = 0.005;
    String(text).toUpperCase().split(' ').forEach(function (word, wi) {
      if (wi) t += 4 * u;   // 7 units between words (3 already added after the last letter)
      word.split('').forEach(function (ch) {
        var m = CODE[ch]; if (!m) return;
        m.split('').forEach(function (s) {
          var d = s === '.' ? u : 3 * u;
          g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(0.5, t + r);
          g.gain.setValueAtTime(0.5, t + d - r); g.gain.linearRampToValueAtTime(0, t + d);
          t += d + u;
        });
        t += 2 * u;
      });
    });
    o.start(); o.stop(t + 0.05);
    if (btn) btn.classList.add('on');
    playing = { o: o, g: g, btn: btn };
    o.onended = function () { if (playing && playing.o === o) { if (btn) btn.classList.remove('on'); playing = null; } };
  }
  document.querySelectorAll('[data-say]').forEach(function (b) {
    b.addEventListener('click', function () { if (playing && playing.btn === b) { stop(); return; } play(b.dataset.say, b); });
  });
})();
