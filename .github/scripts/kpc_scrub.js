// Nov 11 2026 (bots review, package E): keep secrets out of log lines. Same rules as kpc_scrub.py.
// GitHub hides a secret's exact text in the log, but not a piece of it, a URL-encoded copy, or an error body that repeats it.
//   scrub(text)           -> text with webhook links, tokens, API keys, sheet links and this run's secret env values replaced by ***
//   noticeText(m, limit)  -> scrub + the one-line ::notice escaping
// Standard library only, no network, never throws.
const NAMES = ['DISCORD_BOT_TOKEN', 'DISCORD_WEBHOOK_URL', 'KPC_DISCORD_WEBHOOK', 'KPC_PARKS_WEBHOOK', 'KPC_ADMIN_WEBHOOK',
  'KPC_GENERAL_WEBHOOK', 'KPC_ANNOUNCE_WEBHOOK', 'KPC_CAMPOUT_WEBHOOK', 'KPC_YOUTUBE_WEBHOOK', 'KPC_DISCORD_STAFF_WEBHOOK',
  'GENERAL_WEBHOOK_URL', 'CAMPOUT_WEBHOOK_URL', 'ANNOUNCE_WEBHOOK_URL', 'PARKS_WEBHOOK_URL', 'FB_PAGE_TOKEN', 'NPS_API_KEY',
  'YOUTUBE_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN'];
const LOOKS = /(TOKEN|SECRET|PASSWORD|WEBHOOK|API_KEY|_KEY$|_CSV$|SHEET)/i;
const PATTERNS = [
  [/https?:\/\/(?:[\w-]+\.)?discord(?:app)?\.com\/api(?:\/v\d+)?\/webhooks\/\S+/gi, 'https://discord.com/api/webhooks/***'],
  [/(access_token|client_secret|input_token|refresh_token|api_key|apikey|key|token|hash_value)=([^&\s"'<>]+)/gi, '$1=***'],
  [/("(?:access_token|token|key|api_key)"\s*:\s*")[^"]+(")/gi, '$1***$2'],
  [/\b(Bearer|Bot)\s+[A-Za-z0-9._~+/=-]{12,}/g, '$1 ***'],
  [/\bEAA[A-Za-z0-9]{30,}/g, '***'],
  [/\bAIza[0-9A-Za-z_-]{30,}/g, '***'],
  [/\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}/g, '***'],
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

function scrub(text, limit) {
  let s;
  try {
    s = String(text);
    for (const v of secretValues()) s = s.split(v).join('***');
    for (const [rx, rep] of PATTERNS) s = s.replace(rx, rep);
  } catch (e) { s = '(message hidden: it could not be checked for secrets)'; }
  return limit ? s.slice(0, limit) : s;
}

const noticeText = (m, limit = 800) => scrub(m, limit).replace(/%/g, '%25').replace(/\r/g, '').replace(/\n/g, '%0A');

module.exports = { scrub, noticeText };
