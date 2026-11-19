# Hand-off: KPC App + the Lounges (Opus, Nov 19 2026, 2:20 PM)

Read this first in the new chat, then only the notes it points to.

## Where things stand (all live)
- **App 0.9.15** = KentuckyPortableClub/KPC-App main `bae702c`, built, `app/version.json` says 0.9.15. Full history: KPC-App `CLAUDE.md` (newest blocks: 0.9.13, 0.9.14, 0.9.15). Opus's round notes: KPC-App `notes/opus-*-nov19.md`.
- **Website bot** (build.yml release job): each app build copies www/ into KPC-Links `logger-beta/` on a branch + opens a DRAFT PR for Fable (LINKS_TOKEN has Pull requests: write). First run = PR #282, merged.
- **Park packs** carry WWFF + SOTA per state (PR #279); packs job ran once by hand (51 packs, 9 MB).
- **Lounges (website):**
  - Rounds 2 + 3 merged (#280, #283): FT8 tab HELD / never off its dial / Fox & Hound / FT8 review fixes, ON AIR + STOP ALL (kpc-onair.js), BIG RADIO PAGE (beta) link = the web logger, limiter on hold to talk.
  - Nov 19 noon: parks bar ✕ HIDE stays on screen; 📻 RADIO in the hero buttons on both.
  - **CARBON COPY (Brandon, Nov 19):** `kpc-hunt.html` (VIP) is the ONE master. `kpc-hunters.html` is WRITTEN from it: `python3 .claude/build/hunt/make_public.py` (`--check` = test). Edit only kpc-hunt.html, then run it. Differences live in `data-public="1"` (.mem-only / .pub-only in kpc-hunt.css, `PUB` in kpc-hunt.js): VIP-only = FT8/digi, ⭐ GET MY PARKS bookmark, badges, re-spot, PARKS I NEED, TOP 50, CAT & QRZ. Test: tests/test_lounges_carbon_nov19.py.
  - One tab row on both (kpc-lounge-tabs.js, `vip` set also on kpc-hunt-need / kpc-top50 / kpc-hunt-cat; the old .hl-ptabs pills are gone there). Same RADIO CONTROL card on both.
  - `.claude/build/hunt/main.html` is out of date: do not build from it.
  - Lounge notes: `.claude/notes/logger-lounge-digi.md` (last bullets).

## Waiting on Brandon (do not start without these)
1. **Radio cards 6, 7, 8, 12** (IC-7100, FT-891, FTX-1, Digirig; KPC-App `notes/radio-checks-for-brandon.md`). They unlock: split from spots in the Lounges + copying the app's kpc-cat.js to the site (both key a radio: Fable reviews).
2. **Two CW recordings** (strong + weak CQ, WAV; KPC-App `tools/cwlab/README.txt`). They unlock: the final CW decoder check, then the website CW/RTTY decoder port.
3. **Fable check (optional, Brandon's call):** the public Hunters Lounge now loads the same reviewed `kpc-logger-ft8.js?v=20261119b` as VIP (carbon copy); its FT8 tab stays hidden. Brandon was offered putting the old file back until Fable looks.
4. Confirm on his phone: parks bar closes, 📻 RADIO opens the card, both Lounges look alike.

## Parked (next build that happens anyway)
- Hidden "try the radio's own voice memory" test button (FT-710 `PB0n;`, IC-705/9700 `28 00 nn`; IC-7300 unconfirmed). Research: KPC-App `notes/opus-voicemem-research-nov19.md`. Keys a radio: Fable reviews.
- To-do list items still open: 7 WWFF/SOTA whole US list source, real-device test of 0.9.15, KiwiSDR on a real Kiwi (app only).

## House rules that bit this chat
- Pull first (`git fetch && git reset --hard origin/main`): bots and other chats push.
- Pinned `?v=` stamps live in tests (test_lounge_review_nov11.py etc.): bump them with the files.
- Browser tests need `python3 -m http.server 8795` (and 8799 for the logger tests) started fresh each turn.
- Anything that can key a radio, lose a contact or leak a password: note it for Fable, don't ship it.
