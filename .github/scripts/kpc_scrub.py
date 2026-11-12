#!/usr/bin/env python3
"""Nov 11 2026 (bots review, package E): keep secrets out of log lines.

GitHub hides a secret's exact text in the log, but not a piece of it, a URL-encoded copy, or a Facebook / Discord error body
that repeats it. Every bot that prints an error, an HTTP answer or an exception goes through scrub() first.

  scrub(text)      -> text with webhook links, access tokens, API keys, bot tokens, sheet links and the exact values of the secret
                      environment variables of this run (and their URL-encoded copies) replaced by ***
  host_of(url)     -> 'discord.com' (the host only, for a log line that has to say where it went)
  notice_text(m, limit) -> scrub + the one-line ::notice escaping (% and line breaks)

Pure standard library, no network, never raises."""
import os, re, urllib.parse

# environment variables whose VALUE is a secret (exact names used by the workflows) + any name that looks like one
NAMES = ('DISCORD_BOT_TOKEN', 'DISCORD_WEBHOOK_URL', 'KPC_DISCORD_WEBHOOK', 'KPC_PARKS_WEBHOOK', 'KPC_ADMIN_WEBHOOK',
         'KPC_GENERAL_WEBHOOK', 'KPC_ANNOUNCE_WEBHOOK', 'KPC_CAMPOUT_WEBHOOK', 'KPC_YOUTUBE_WEBHOOK', 'KPC_DISCORD_STAFF_WEBHOOK',
         'GENERAL_WEBHOOK_URL', 'CAMPOUT_WEBHOOK_URL', 'ANNOUNCE_WEBHOOK_URL', 'PARKS_WEBHOOK_URL', 'FB_PAGE_TOKEN',
         'NPS_API_KEY', 'YOUTUBE_API_KEY', 'RIDB_API_KEY', 'FCC_BDC_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN', 'RELAY_MAIL_URL',
         'RELAY_MAIL_KEY', 'APPROVAL_EMAIL', 'KPC_ACTIVATIONS_CSV', 'KPC_GUESTBOOK_CSV', 'KPC_CWBOARD_CSV', 'COMMUNITY_SHEET_CSV',
         'NOTES_SHEET_CSV', 'CAMPGROUND_SHEET_CSV', 'KPC_REPORTS_CSV')
LOOKS = re.compile(r'(TOKEN|SECRET|PASSWORD|WEBHOOK|API_KEY|_KEY$|_CSV$|SHEET)', re.I)

PATTERNS = [
    (re.compile(r'https?://(?:[\w-]+\.)?discord(?:app)?\.com/api(?:/v\d+)?/webhooks/\S+', re.I), 'https://discord.com/api/webhooks/***'),
    (re.compile(r'(access_token|client_secret|input_token|refresh_token|api_key|apikey|key|token|hash_value)=([^&\s"\'<>]+)', re.I), r'\1=***'),
    (re.compile(r'("(?:access_token|token|key|api_key)"\s*:\s*")[^"]+(")', re.I), r'\1***\2'),
    (re.compile(r'\b(Bearer|Bot)\s+[A-Za-z0-9._~+/=-]{12,}'), r'\1 ***'),
    (re.compile(r'\bEAA[A-Za-z0-9]{30,}'), '***'),                      # Facebook tokens
    (re.compile(r'\bAIza[0-9A-Za-z_-]{30,}'), '***'),                   # Google API keys
    (re.compile(r'\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}'), '***'),
    (re.compile(r'\b[MNO][A-Za-z0-9_-]{23,25}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}'), '***'),   # Discord bot tokens
    (re.compile(r'(docs\.google\.com/(?:spreadsheets|forms)/d/e/)[A-Za-z0-9_-]{20,}'), r'\1***'),   # a published sheet / form link
]


def _secret_values():
    vals = set()
    for k, v in os.environ.items():
        if not v or not (k in NAMES or LOOKS.search(k)): continue
        for piece in str(v).split():          # a webhook secret may hold several links, one per line
            if len(piece) >= 8: vals.add(piece)
            tail = piece.rstrip('/').rsplit('/', 1)[-1]   # the token part of a webhook link on its own
            if len(tail) >= 16 and '/api/webhooks/' in piece: vals.add(tail)
    out = set(vals)
    for v in vals:
        out.add(urllib.parse.quote(v, safe='')); out.add(urllib.parse.quote_plus(v))
    return sorted(out, key=len, reverse=True)


def scrub(text, limit=None):
    try:
        s = str(text)
        for v in _secret_values(): s = s.replace(v, '***')
        for rx, rep in PATTERNS: s = rx.sub(rep, s)
    except Exception:  # noqa: BLE001
        s = '(message hidden: it could not be checked for secrets)'
    return s[:limit] if limit else s


def host_of(url):
    try: return urllib.parse.urlsplit(str(url)).hostname or ''
    except Exception: return ''  # noqa: BLE001


def notice_text(m, limit=800):
    return scrub(m, limit).replace('%', '%25').replace('\r', '').replace('\n', '%0A')
