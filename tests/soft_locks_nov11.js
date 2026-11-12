/* Node check for the Nov 11 soft-lock change (run by tests/test_soft_locks_nov11.py). No network.
   For each lock it takes the page's OWN code (the slow() / sha() lines of the file), runs a made-up password through it with
   WebCrypto, and compares with the two steps done by node's crypto: PBKDF2-SHA256(hex SHA-256(prefix + password), salt, 200000, 32). */
const fs = require('fs'), path = require('path'), C = require('crypto');
const ROOT = process.argv[2]; let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const rd = f => fs.readFileSync(path.join(ROOT, f), 'utf8');
const two = (prefix, pw, salt, trimOnly) => { const t = trimOnly ? pw.trim() : prefix + pw.trim().toLowerCase();
  const h = C.createHash('sha256').update(t, 'utf8').digest('hex'); return C.pbkdf2Sync(Buffer.from(h, 'utf8'), Buffer.from(salt, 'utf8'), 200000, 32, 'sha256').toString('hex'); };
const sha = async t => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))].map(x => x.toString(16).padStart(2, '0')).join('');
const PW = 'Made-Up Test Pass 42', WRONG = 'made-up test pass 43';
(async () => {
  /* kpc-vip.js: enc / hex / slow lines, then sha(SALT + pw) -> slow(h, PS) */
  const v = rd('kpc-vip.js');
  const lines = ['var enc', 'var slow'].map(k => (v.split('\n').find(l => l.trim().startsWith(k)) || ''));
  const fn = new Function(lines.join('\n') + '\nreturn slow;')();
  for (const [lock, prefix, salt] of [['VIP', 'kpc-vip:', 'kpc-vip-pbkdf2-salt-v1'], ['beta', 'kpc-beta:', 'kpc-beta-pbkdf2-salt-v1'], ['room', 'kpc-room:', 'kpc-room-pbkdf2-salt-v1']]) {
    ok(v.includes("'" + salt + "'"), `kpc-vip.js ${lock}: salt ${salt} is the one in the file`);
    const want = two(prefix, PW, salt);
    ok(await fn(await sha(prefix + PW.trim().toLowerCase()), salt) === want, `kpc-vip.js ${lock}: right password -> the stored-value recipe`);
    ok(await fn(await sha(prefix + WRONG.trim().toLowerCase()), salt) !== want, `kpc-vip.js ${lock}: wrong password does not match`);
  }
  ok(/sha\(SALT \+ inp\.value\.trim\(\)\.toLowerCase\(\)\)\.then\(function \(h\) \{ return slow\(h, PS\); \}\)\.then\(function \(h\) \{\s*if \(h === HASH\)/.test(v), 'kpc-vip.js: the unlock compares slow(sha(...)) with HASH');
  /* kpc-maprep-gate.js and kpc-maprep.js */
  const g = rd('kpc-maprep-gate.js');
  const gs = new Function("var PS = 'kpc-maprep-pbkdf2-salt-v1';\n" + g.split('\n').find(l => l.trim().startsWith('function slow')) + '\nreturn slow;')();
  const wantR = two('kpc-maprep:', PW, 'kpc-maprep-pbkdf2-salt-v1');
  ok(g.includes("var PS = 'kpc-maprep-pbkdf2-salt-v1'") && await gs(await sha('kpc-maprep:' + PW.trim().toLowerCase())) === wantR, 'kpc-maprep-gate.js: right password -> the recipe');
  ok(await gs(await sha('kpc-maprep:' + WRONG.trim().toLowerCase())) !== wantR, 'kpc-maprep-gate.js: wrong password does not match');
  ok(g.includes(".then(slow).then(function (h) {") , 'kpc-maprep-gate.js: the unlock stretches before comparing');
  const m = rd('kpc-maprep.js'), i = m.indexOf('const slow = async h =>'), j = m.indexOf('\n  function start()', i);
  const ms = new Function("const PS = 'kpc-maprep-pbkdf2-salt-v1';\n" + m.slice(i, j) + '\nreturn slow;')();
  ok(m.includes("const PS = 'kpc-maprep-pbkdf2-salt-v1'") && await ms(await sha('kpc-maprep:' + PW.trim().toLowerCase())) === wantR, 'kpc-maprep.js inner lock: right password -> the recipe');
  ok(await ms(await sha('kpc-maprep:' + WRONG.trim().toLowerCase())) !== wantR, 'kpc-maprep.js inner lock: wrong password does not match');
  ok(m.includes("await slow(await sha('kpc-maprep:' + $('mrPw').value.trim().toLowerCase()))"), 'kpc-maprep.js: the unlock stretches before comparing');
  /* kpc-members.js (legacy door, idle while kpc-gate.js is on the page) */
  const k = rd('kpc-members.js'), ks = new Function(k.split('\n').find(l => l.startsWith('async function sha')) + '\nreturn sha;')();
  const wantM = two('', PW, 'kpc-members-legacy-pbkdf2-salt-v1', true);
  ok(await ks(PW) === wantM && await ks(WRONG) !== wantM, 'kpc-members.js: right password matches the recipe, wrong does not');
  /* an old remembered value (the fast SHA-256) still opens once: stretching it gives the stored value */
  const fast = await sha('kpc-vip:' + PW.trim().toLowerCase());
  ok(await fn(fast, 'kpc-vip-pbkdf2-salt-v1') === two('kpc-vip:', PW, 'kpc-vip-pbkdf2-salt-v1'), 'migration: stretching a remembered fast value gives the new stored value');
  console.log(fails ? 'SOME FAILED' : 'ALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL ' + e); console.log('SOME FAILED'); process.exit(1); });
