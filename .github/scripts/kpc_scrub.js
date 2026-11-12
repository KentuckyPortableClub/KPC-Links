// Nov 11 2026 (bots review, package E): keep secrets out of log lines. Same rules as kpc_scrub.py.
// GitHub hides a secret's exact text in the log, but not a piece of it, a URL-encoded copy, or an error body that repeats it.
//   scrub(text)           -> text with webhook links, tokens, API keys, sheet links and this run's secret env values replaced by ***
//   noticeText(m, limit)  -> scrub + the one-line ::notice escaping
//   clip(text, n)         -> scrub first, then cut (Nov 12: a cut-off secret's leading or trailing 8+ characters are hidden too)
// Standard library only, no network, never throws.
const NAMES = ['DISCORD_BOT_TOKEN', 'DISCORD_WEBHOOK_URL', 'KPC_DISCORD_WEBHOOK', 'KPC_PARKS_WEBHOOK', 'KPC_ADMIN_WEBHOOK',
  'KPC_GENERAL_WEBHOOK', 'KPC_ANNOUNCE_WEBHOOK', 'KPC_CAMPOUT_WEBHOOK', 'KPC_YOUTUBE_WEBHOOK', 'KPC_DISCORD_STAFF_WEBHOOK',
  'GENERAL_WEBHOOK_URL', 'CAMPOUT_WEBHOOK_URL', 'ANNOUNCE_WEBHOOK_URL', 'PARKS_WEBHOOK_URL', 'FB_PAGE_TOKEN',
  'NPS_API_KEY', 'YOUTUBE_API_KEY', 'RIDB_API_KEY', 'FCC_BDC_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN', 'RELAY_MAIL_URL',
  'RELAY_MAIL_KEY', 'APPROVAL_EMAIL', 'KPC_ACTIVATIONS_CSV', 'KPC_GUESTBOOK_CSV', 'KPC_CWBOARD_CSV', 'COMMUNITY_SHEET_CSV',
  'NOTES_SHEET_CSV', 'CAMPGROUND_SHEET_CSV', 'KPC_REPORTS_CSV', 'FB_PAGE_ID'];   // Nov 12: same list as kpc_scrub.py
const LOOKS = /(TOKEN|SECRET|PASS|WEBHOOK|API_KEY|_KEY$|_CSV$|SHEET)/i;   // Nov 12: PASS (was PASSWORD) also covers *_PASS
const MIN_PIECE = 8;   // a leading or trailing piece of a secret this long (or longer) is hidden too (Nov 12, cut-off copies)
const PATTERNS = [
  [/https?:\/\/(?:[\w-]+\.)?discord(?:app)?\.com\/api(?:\/v\d+)?\/webhooks\/\S+/gi, 'https://discord.com/api/webhooks/***'],
  [/(access_token|client_secret|input_token|refresh_token|api_key|apikey|key|token|hash_value)=([^&\s"'<>]+)/gi, '$1=***'],
  [/("(?:access_token|token|key|api_key)"\s*:\s*")[^"]+(")/gi, '$1***$2'],
  [/\b(Bearer|Bot)\s+[A-Za-z0-9._~+/=-]{12,}/g, '$1 ***'],
  [/\bEAA[A-Za-z0-9]{30,}/g, '***'],
  [/\bAIza[0-9A-Za-z_-]{30,}/g, '***'],
  [/\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}/g, '***'],
  [/\b[MNO][A-Za-z0-9_-]{23,25}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}/g, '***'],   // Discord bot tokens (as in kpc_scrub.py)
  [/(docs\.google\.com\/(?:spreadsheets|forms)\/d\/e\/)[A-Za-z0-9_-]{20,}/g, '$1***'],
];

function secretValues() {
  const vals = new Set();
  for (const [k, v] of Object.entries(process.env)) {
    if (!v || !(NAMES.includes(k) || LOOKS.test(k))) continue;
    for (const piece of String(v).split(/\s+/)) {
      if (piece.length >= 8) vals.add(piece);
      const tail = piece.replace(/\/+$/, '').split('/').pop();
      if (tail.length >= 16 && piece.includes('/api/webhooks/')) vals.add(tail);
    }
  }
  const out = new Set(vals);
  for (const v of vals) { out.add(encodeURIComponent(v)); out.add(encodeURIComponent(v).replace(/%20/g, '+')); }
  return [...out].sort((a, b) => b.length - a.length);
}

// the public start of a link-shaped value ('https://discord.com/api/webhooks/' -> 33); 0 for a plain token
function publicStart(v) {
  let raw = v; try { raw = decodeURIComponent(v.replace(/\+/g, ' ')); } catch (e) { raw = v; }
  if (!raw.includes('/')) return 0;
  let n = 0;
  for (const seg of raw.split('/').slice(0, -1)) { if (!/^[A-Za-z.:-]*$/.test(seg)) break; n += seg.length + 1; }
  return raw === v ? n : encodeURIComponent(raw.slice(0, n)).length;
}

// hide a cut-off copy of secret v: a leading piece (MIN_PIECE+ chars, past the public start) or a trailing piece (MIN_PIECE+)
function hidePieces(s, v) {
  if (v.length < MIN_PIECE) return s;
  const head = Math.max(MIN_PIECE, publicStart(v) + 1);
  if (v.length >= head) {
    const seed = v.slice(0, head); let out = '', i = 0;
    for (;;) {
      const j = s.indexOf(seed, i); if (j < 0) { out += s.slice(i); break; }
      let k = head; while (k < v.length && j + k < s.length && s[j + k] === v[k]) k++;
      out += s.slice(i, j) + '***'; i = j + k;
    }
    s = out;
  }
  const seed = v.slice(-MIN_PIECE); let out = '', i = 0;
  for (;;) {
    const j = s.indexOf(seed, i); if (j < 0) { out += s.slice(i); break; }
    let k = MIN_PIECE; while (k < v.length && j - (k - MIN_PIECE) - 1 >= i && s[j - (k - MIN_PIECE) - 1] === v[v.length - k - 1]) k++;
    out += s.slice(i, j - (k - MIN_PIECE)) + '***'; i = j + MIN_PIECE;
  }
  return out;
}

function scrub(text, limit) {
  let s;
  try {
    s = String(text);
    const vals = secretValues();
    for (const v of vals) s = s.split(v).join('***');
    for (const v of vals) s = hidePieces(s, v);
    for (const [rx, rep] of PATTERNS) s = s.replace(rx, rep);
  } catch (e) { s = '(message hidden: it could not be checked for secrets)'; }
  return limit ? s.slice(0, limit) : s;
}

// scrub FIRST, then cut: the safe form of String(e).slice(0, n) for a log line
const clip = (text, n) => scrub(text, n);

const noticeText = (m, limit = 800) => scrub(m, limit).replace(/%/g, '%25').replace(/\r/g, '').replace(/\n/g, '%0A');

module.exports = { scrub, noticeText, clip };
