# KPC App readiness review (Fable, Oct 28 2026, ~2:30 AM CDT; app 0.7.7 + tonight's polish)

How it was checked: the whole test suite (186 checks through the pretend radio: a made-up FT8 contact end to end, CW / RTTY / PSK31 round trips, the remote link with PTT, watchdog, talk limit, WebRTC audio, revoke), synthetic FT8 signals at known SNR through the real decoder, 12 s of radio-filtered noise through the CW decoder, a headless run of the real PC sound path (capture, lost-device restart, hear-here monitor), every screen and every mode at 390 / 1024 / 1426 px in both looks (no page errors, no sideways scroll), the Android plugin's wake-lock / service lifecycle read line by line, and every 'BRANDON TESTED' list in ft8-app.md against what shipped.

## FIX NOW (done tonight, rides the 3:17 AM build)
- **FT8 'deeper decoding' on by default on the PC.** Measured: normal copies 6/6 to −16 dB, 4/6 at −18, 2/6 at −19, ~nothing past −20; deep (6/40) copies 6/6 at −18, 4/6 at −19, for ~45 ms a pass on a PC. Deeper still (3/90) gains nothing: the limit is the candidate / sync stage, not the LDPC. A phone keeps it off (battery). One-time switch `S.dpv`.
- **The builders' report** now carries the 'dial put back after a mode change' log, the voice setting (VOICE FROM THIS DEVICE, VOICE LEVEL, hear-here) and the CW way (send with / park / WPM) — what tomorrow's SSB and CW test needs.
- (Earlier tonight, same build: the 700 Hz dial jump on a mode change, CW listen-in-CW / send-in-DATA, no false E's with a narrow radio filter, hear the radio on the PC, VOICE LEVEL, typed CW over CAT on the FT-710 family, the per-radio setup sheet, spots on this band.)

## Verdict per area
| Area | State | Notes |
|---|---|---|
| FT8/FT4 decode | GOOD, ~2 dB behind WSJT-X | Timing tolerance −0.5 … +2.4 s DT (all copied at −12 dB). WSJT-X reaches −20/−21 with a second pass after subtracting decoded signals + a-priori; ours is single-pass. LATER: a subtraction pass in the wasm (ft8_lib has no API for it; ~2 days). |
| CAT FT-710 | GOOD, needs Brandon's test tomorrow | Two ports probed, CAT on Enhanced, DTR key on the Standard port, typed CW over CAT (KY0), dial put back after every mode change, tune read-back + log. |
| CAT IC-7300 | UNTESTED by Brandon since 0.6.9 | Icom path exercised only through the pretend radio's shape; 'IC-7300 lock-up' report still waiting. The new mode(k, keep) + DATA-L paths for Icom are from the CI-V manual, not a radio. |
| Sound in/out + recovery | GOOD | Worklet capture with an honest clock, lost device → restart, 6 s no-block watchdog, hear-here on a second output. |
| Remote link | GOOD | Watchdog 2.5 s, talk limit, one phone holds the key, levelled audio to the phone, MY VOICE + PC SETTINGS. Tailscale still untested by Brandon. |
| Log store | GOOD | Merge by id/v/u, tombstones, safety copy written first, ADIF round trips every band / mode, uploads retried; MY LOGS / BREAK / clock hold. |
| Android battery | GOOD | Foreground service + partial wake lock (12 h cap, non-ref-counted, released on destroy); held only while sound runs or the link is on; dropped when the link closes. |
| Crashes / console | CLEAN | No page errors on any screen or mode; one harmless 404 for capacitor.js on the plain web server (it exists inside the app). |
| Screens | CLEAN | 390 / 1024 / 1426, dark lodge + light, every tab incl. RADIO and MAP, all 9 modes. |

## POLISH (next batches, safe, each small)
1. 📜 RADIO LOG sheet (what was sent / what the radio answered) — how-to in kpc-app CLAUDE.md 'TO DO — BORROWED FROM POTACAT' #1.
2. 'Share the radio with WSJT-X / HRD' line on the setup sheet (#2 there).
3. capacitor.js script tag: `onerror` silent so the web/Electron console stays clean.
4. FT8: a second decode pass over the slot with the first pass's signals subtracted (the real sensitivity gain, ~2 dB).
5. HOLD TO TALK through a phone's own mic when the phone is plugged into the radio (native streaming play; today it says 'use the radio's mic').
6. The remote in a plain phone browser (HTTPS + a generated cert) for members without the APK.

## LATER (planned list, unchanged)
Google Drive backup/sync (Brandon's two OAuth clients), park outlines outside KY (shape download build), JS8, PSKReporter/WSJT-X spot sources, DXCC, live log to Log4OM/HRD/N3FJP, contest scoring, LoTW/POTA upload, IC-705 WiFi / Flex / OmniRig, club stats → Lounge (HQ + privacy first), FreeDV, KiwiSDR.

## Reported by Brandon and never closed (needs the radio, not code)
- SSB voice from the app: fixed in code (mode left alone + VOICE LEVEL + dial put back); needs the FT-710's SSB MOD SOURCE = REAR and his test.
- IC-7300: no report since the Oct 23 lock-up; untested on 0.7.x.
- Tailscale (away-from-home) remote: never tested.
- 'Phone volume more than the limiter allows' = turn the PC's RX audio up (hear-here loudness / the radio's AF).

## What is left for KPC Lite
The Lite build = the same www/ with the digital modes, remote, APRS, parks packs and uploads left out: LOG + MY LOGS + SPOTS (POTA/SOTA/WWFF) + SPOT ME + MAP + the call-box commands + ADIF/backup. Everything it needs already runs without a radio or sound (the suite's P page). To make it: a build flag that skips kpc-digi / kpc-modes5 / kpc-dsp / kpc-aprs / kpc-ax25 / kpc-remote / kpc-voice / kpc-radio / kpc-meters and hides the DIGI / RADIO tabs (one `LITE` constant in index.html + a second APK name in build.yml). Half a day, once Brandon says go.

## What Brandon should test tomorrow (0.7.6 + 0.7.7 build)
1. SSB from the app on 40 m: radio SSB MOD SOURCE = REAR, voice keyer memory re-recorded from the PC mic, 🎙 VOICE LEVEL up until ALC moves; the dial must stay put. Then 20 m USB.
2. CW: ⚙ CW → SEND WITH = the radio's own keyer (typed + F1–F6, radio in CW-U), then SEND WITH = sound with 'listen in CW' (tap-to-key should go out at once; no stray E's between overs).
3. From the desk: 🔊 HEAR THE RADIO HERE + 🎙 HOLD TO TALK on the RADIO tab.
4. From the tablet: 🔊 VOLUME, 🎙 MY VOICE, ⚙ PC SETTINGS.
5. Copy a builders' report after the SSB test either way.
