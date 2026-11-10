#!/usr/bin/env python3
"""Nov 10: Hunters Lounge + VIP Lounge logger round (kpc-hunt-x.js and the hooks in kpc-hunt.js / kpc-lounge-radio.js / kpc-cat.js).
Static + node checks (no browser): calls split one QSO each (comma, space, semicolon), QRZ uploads one at a time, the class filter's
band plan, the ⚙ gear + radio window on both pages, voice / CW keyers hidden without CAT, the CW keyer protocols, and that every
original dock field and script is still on both pages. The full browser check is tests/lounge_logger_nov10_browser.js."""
import pathlib, re, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
rd = lambda p: (ROOT / p).read_text(encoding='utf-8')
hunt, x, lr, cat = rd('kpc-hunt.js'), rd('kpc-hunt-x.js'), rd('kpc-lounge-radio.js'), rd('kpc-cat.js')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
def node(code):
    r = subprocess.run(['node', '-e', code], capture_output=True, text=True); return (r.stdout + r.stderr).strip()

# 4: several calls = one QSO each, and one QRZ upload each, one at a time
m = re.search(r"  function splitCalls\(v\) \{.*\n", hunt)
check(bool(m), 'splitCalls present')
out = node(m.group(0) + "console.log([splitCalls('KZ4CP,N4KPC'), splitCalls('KZ4CP N4KPC'), splitCalls(' kz4cp , n4kpc ;w1aw'), splitCalls('KZ4CP, KZ4CP')].map(a => a.join('|')).join(' / '))")
check(out == 'KZ4CP|N4KPC / KZ4CP|N4KPC / KZ4CP|N4KPC|W1AW / KZ4CP', 'calls split on comma, space or semicolon, repeats dropped: ' + out)
check('for (const call of CS)' in hunt and 'await afterLog(rec' in hunt, 'each call is its own record in the log')
check('function qzOne(one)' in hunt and 'qzOne(one).then' in hunt and 'KPCQrz.send(a.slice' not in hunt, 'QRZ uploads go through the one-at-a-time queue (log + edit paths)')
check("await new Promise(z => setTimeout(z, 600))" in hunt, 'a gap between QRZ uploads')
check('👥 ${CSW.length} calls: one contact each' in hunt, 'the who-box shows each call, not "No public listing for A,B"')

# 2: class filter
check("(!window.KPCHuntX || KPCHuntX.pass(s))" in hunt, 'the spots filter asks the class filter')
plan = re.search(r"  const PLAN = \[.*?\n  \];\n", x, re.S); iscw = re.search(r"  const isCwData = .*\n", x); allw = re.search(r"  function allowed\(khz, cls, mode\) \{.*?\n  \}\n", x, re.S)
check(bool(plan and iscw and allw), 'band plan + allowed() present')
out = node(plan.group(0) + iscw.group(0) + allw.group(0) + "console.log([allowed(7150,'G','SSB'),allowed(7150,'E','SSB'),allowed(14250,'G','USB'),allowed(14160,'G','SSB'),allowed(14010,'G','CW'),allowed(14030,'G','CW'),allowed(7030,'T','CW'),allowed(7200,'T','SSB'),allowed(28400,'T','SSB'),allowed(14074,'G','FT8')].map(Number).join(''))")
check(out == '0110011011', 'US band plan by class (General 7.150 no, Extra yes, General 14.250 yes, 14.160 no, 14.010 CW no, 14.030 CW yes, Tech 7.030 CW yes, 7.200 no, 28.400 yes, General FT8 14.074 yes): ' + out)
check("'kpcHuntCls'" in x and '📜 IN MY CLASS ONLY' in x, 'class + on/off remembered in localStorage')

# 3: scan
check('▶ SCAN' in x and 'scStop' in x and "/^FT[48]$/i.test(s.mode" in x, 'SCAN steps the shown spots, skips FT8 / FT4')
check('window.KPCHuntShown = ' in hunt, 'kpc-hunt.js hands SCAN the shown list')
check("'kpcHuntScan'" in x, 'scan seconds remembered')

# 6 / 7: gear + window, audio / mic
for t in ["['radio', '📻 Radio']", "['meters', '📊 Meters']", "['band', '📍 Bands · Tune · SWR']", "['audio', '🎧 Audio · Mic']", "['more', '🎛 More']", "['cw', '📟 CW']"]:
    check(t in x, 'window tab ' + t)
check('id="hxGear"' in x and "'kpcHuntPop'" in x, 'gear on the dock; last tab + place remembered')
check("const K = G.KPCCat; if (!K) return;" in lr and "if ($('ctCat')) $('ctCat').appendChild(box);" in lr and 'box, home:' in lr, 'kpc-lounge-radio.js no longer needs #ctCat; its box can live in the window')
check("if (!box.isConnected) return;" in lr, 'the radio box does not draw while it is put away')
check(all(k in x for k in ["natural: { hp: 80", "punch: { hp: 250", "contest: { hp: 350"]), 'NATURAL / PUNCH / CONTEST voice shaper (the KPC app\'s presets)')
check("lr.send('mic', TX.mg)" in x and "lr.send('power', TX.pw)" in x and "mic: p => [icom([0x14, 0x0B" in lr, 'radio MIC GAIN + RF POWER over CAT')
check("const me = TK = { key: k.ptt(true, 'cat') }" in x, 'HOLD TO TALK keys at once (does not wait for the microphone)')
check('PTTW++' in cat and 'if (PTTW) return null;' in cat, 'a waiting PTT makes queued meter reads step aside (no late key / unkey)')
check('@media (max-width:520px)' in x, 'phone-width layout for the window')

# 8 / 9: keyers hidden without CAT; CW protocols
check("cwb.hidden = !(on && k.cwCan && k.cwCan())" in x and 'id="hxCwB"' in x and 'hidden>📟' in x, 'CW button hidden without a CAT radio that can key CW')
check("Connect the radio first (📻 Radio tab). The CW keyer" in x, 'CW tab says connect first')
check("const YKY = { ft710: 1, ft991: 1, ftdx10: 1, ftx1: 1" in cat and "'KY0 ' + text.slice(i, i + 48).padEnd(48, ' ')" in cat and 'KM5' in cat, 'newer Yaesu typed CW (KY0 / KM5 + KYA)')
check("icom([0x17, ...asc(" in cat and "'KY ' + text.slice(i, i + 24)" in cat, 'Icom 0x17 + Kenwood KY kept')
check(x.count('data-cwm=') >= 1 and "'kpcHuntCw'" in x and '{CALL}' in x and '{MY}' in x, 'CW memories (editable, {CALL} / {MY}) remembered')

check("document.querySelector('.hl-viewbar')" in x and "$('hlRtabs')" not in x, '▶ SCAN sits on the list bar, not the full tab row (tab row unchanged)')

# both lounges (and the beta rooms that share the dock): nothing taken away
IDS = ['dkForm', 'dFreq', 'dMode', 'dBand', 'dRef', 'dName', 'dCall', 'dRs', 'dRr', 'dSt', 'dNote', 'dkClr', 'dkLog', 'dkRad', 'dkClk', 'hlFilters', 'hlRtabs']
for p in ['kpc-hunters.html', 'kpc-hunt.html', 'kpc-beta-room.html', 'kpc-beta-need.html', 'kpc-hunters-need.html', 'kpc-hunt-need.html']:
    h = rd(p)
    check(all(f'id="{i}"' in h for i in IDS), p + ': every dock / filter / spots-bar id still there')
    check('data-vk-open' in h, p + ': voice keyer button still in the page')
    check('hl-viewbar' in h and 'class="hl-vt"' in h, p + ': list bar (where ▶ SCAN goes, before CARDS / TABLE) still there')
    srcs = re.findall(r'<script src="(kpc-[a-z0-9-]+\.js)\?v=', h)
    for s in ['kpc-cat.js', 'kpc-hunt.js', 'kpc-hunt-x.js', 'kpc-lounge-radio.js', 'kpc-nr.js', 'kpc-meters.js']:
        check(s in srcs, p + ': loads ' + s)
    check(srcs.index('kpc-hunt-x.js') > srcs.index('kpc-hunt.js'), p + ': kpc-hunt-x.js after kpc-hunt.js')
for f in ['kpc-hunt.js', 'kpc-hunt-x.js', 'kpc-lounge-radio.js', 'kpc-cat.js']:
    r = subprocess.run(['node', '--check', str(ROOT / f)], capture_output=True, text=True)
    check(r.returncode == 0, 'node --check ' + f + (' ' + r.stderr[:120] if r.returncode else ''))

print('ALL PASS' if ok else 'SOME FAILED')
raise SystemExit(0 if ok else 1)
