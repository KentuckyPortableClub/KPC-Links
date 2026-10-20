# KPC FT8 APP: build plan (Brandon Oct 20 2026 3:57 AM: 'Private, make notes on what you need to do, Fable, GitHub and maybe even Sonnet')

START: Thursday Oct 22 2026 1:15 AM CDT. Nothing before that (boundary work until Thu 1:01 AM).
SCOPE: FT8 + FT4 (+ FT2) app WITH the KPC Logger and the other DIGI modes (CW, RTTY, PSK31, SSTV, WSPR, HELL). Highly polished, professional layout. Windows PC + Android phone + Android tablet (Brandon's Samsung tablet + FT-710 = main test rig). Technical must-haves: ideas.md 'FT8 APP BUILD NOTES' (1-8) + 'KPC FT8 ANDROID APP'. App look: logger-lounge-digi.md 'KPC APP LOOK'.

## GitHub (decided: PRIVATE repo)
- New PRIVATE repo, e.g. KentuckyPortableClub/kpc-ft8-app (create with gh under Brandon's account on Thursday; confirm the name with him). Own short CLAUDE.md in that repo (rules + where things are); do NOT pile app notes into the website notes.
- Code shared with the website: copy kpc-ft8.js / kpc-ft8.wasm / kpc-logger-ft8.js / kpc-digi.js / kpc-digi-ui.js / kpc-cat.js / logger parts into the app repo (record which website commit they came from); later fixes go both ways by hand.
- Builds on GitHub Actions (private repo: 2,000 free minutes/month; ~5-10 min per Android build, Windows a bit more):
  - Android: ubuntu runner, JDK 17 + Android SDK, Capacitor (WebView app) + Gradle → signed .apk (later .aab for Play Store).
  - Windows: windows runner, Electron (or Tauri) → .exe installer.
  - Releases: each tagged build attaches the .apk + .exe to a GitHub Release; Brandon downloads from there (repo is private, so he signs in to GitHub; or we post the file link in the members room).
- Signing: Claude creates the Android keystore on a runner/sandbox, stores it as repo secrets (ANDROID_KEYSTORE_B64, ANDROID_KEYSTORE_PASS, ANDROID_KEY_ALIAS, ANDROID_KEY_PASS). NEVER in the repo or chat. Losing it = updates can't install over the old app, so tell Brandon to keep a copy (he downloads it once from a private place, not chat).
- Email rule still applies: builds that fail email Brandon, so test locally first, keep build runs few.

## Who does what
- **Fable (claude-fable-5-1)**: the foundation, the hard parts. App skeleton (Capacitor Android + Electron Windows from one codebase), the NATIVE AUDIO BRIDGE (Android AudioTrack USAGE_MEDIA out + AudioRecord DEFAULT/UNPROCESSED in, output opened before input, never MODE_IN_COMMUNICATION, 48 kHz, foreground service so decoding survives screen off), the NATIVE USB SERIAL bridge for CAT (usb-serial-for-android: CP210x / FTDI / CH340 / CDC), first working FT8 decode + full-power TX on Brandon's tablet. Also any later bug that is about audio, USB, timing or Android itself.
- **Opus (claude-opus-5-5)**: porting the features and the screens. Logger inside the app, spots / self-spot / respot, QRZ, ADIF per park, offline park list + GPS grid, the other digi modes, tablet / phone / PC layouts in the KPC app look, settings, onboarding (radio setup helper: DATA mode, DATA MOD SOURCE = USB, media volume).
- **Sonnet (claude-sonnet-5-5)**: the cheaper, repetitive work. Wording and help text, icons and store graphics list, layout nudges from Brandon's screenshots, test scripts (Playwright for the web part), README / changelog, Play Store listing text (Part 97 note, 'not part of POTA/SOTA/WWFF', no program logos).
- Switch with /model. Hand-off between models = this file + the app repo's CLAUDE.md + a short 'where I stopped' line at the bottom of the app repo notes after every session.

## Order of work
1. (Fable) Repo + build pipeline green (empty app installs on Android + Windows).
2. (Fable) Native audio + USB; FT8 receive + full-power TUNE / TX on the FT-710 → Brandon confirms watts + ALC.
3. (Fable/Opus) A full FT8 + FT4 contact logged on the tablet.
4. (Opus) Logger + spots + offline park list + GPS grid.
5. (Opus) CW, RTTY, PSK31, SSTV, WSPR, HELL moved over.
6. (Opus, then Sonnet) Layouts: tablet side by side (waterfall + band activity + log), phone tabs, PC window; Night mode; polish rounds from screenshots.
7. Field test at a park (Brandon): screen-off 2-hour decode soak, battery, no-signal start, POTA log upload opens.
8. Optional: Google Play ($25 developer account in Brandon's name; review a few days).

## Brandon's part
- Thursday: say the repo name; keep the tablet + FT-710 + USB cable handy for step 2.
- Test builds when asked (watts, ALC, decodes), send screenshots for layout rounds.
- Keep a private copy of the signing key file when asked.

## MOST RADIOS, not just the FT-710 (Brandon Oct 20 4:00 AM: 'I want it to work and most radios not just 710')
- Every radio in KPCCat.RADIOS (59 now: Icom 18, Yaesu 16, Kenwood 6, Elecraft 6, Xiegu 5, QRP Labs/kits 4, Lab599, Flex) must work; the FT-710 is only the first test rig. Add any popular one missing (check the list against what POTA activators run: IC-705/7300/7100/9700, FT-891/991A/710/818/817/857/897/FTDX10/101, TS-590/890/480, KX2/KX3/K3/K4, X6100/G90/X5105, QMX/QDX/(tr)uSDX, Discovery TX-500, Flex 6000 via its own network API).
- CAT protocols (already in kpc-cat.js): Icom CI-V (+ USB-D data mode, address per model), Yaesu new 9-digit + 8-digit + old 5-byte (FT-817/857/897), Kenwood/Elecraft text, Xiegu (CI-V without data command), QRP Labs. Plus PTT by CAT, RTS or DTR, and VOX for radios with no CAT.
- USB-serial chips on Android (native driver, usb-serial-for-android): Silicon Labs CP210x (Yaesu, Icom), FTDI, CH340 / CH9102 (many Xiegu + cheap cables), Prolific PL2303 (old cables), CDC-ACM (QMX, QDX, truSDX, some newer radios). Windows uses the normal COM port.
- Bluetooth: IC-705 Bluetooth CAT + audio where Android allows; BT serial CAT dongles.
- Sound interfaces, not only built-in USB sound cards: Digirig, SignaLink, homebrew cables; pick the sound device by name, remember it per radio profile.
- RADIO PROFILES: user picks the radio once → baud, address, protocol, PTT method, data mode, sound device saved; several profiles (home rig, field rig).
- SETUP HELPER per brand (plain words + the menu name on that radio): Yaesu DATA MOD SOURCE = USB (+ USB MOD GAIN), Icom DATA MOD = USB/USB-D, Kenwood USB AUDIO/DATA VOX, Elecraft LINE IN, Xiegu audio levels; a 'radio check' button that reads the dial, mode and confirms data mode before the first TX.
- TEST MATRIX before calling it done: at least one radio of each family (Yaesu new, Yaesu old, Icom, Kenwood/Elecraft, Xiegu, QRP Labs) on Android AND Windows; ask club members (MEMBERS list) to lend time on their rigs and report watts, ALC and CAT.
