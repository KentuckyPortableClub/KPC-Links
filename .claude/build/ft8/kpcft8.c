/* KPC FT8 / FT4 engine for the browser (Brandon Oct 17: 'add the wsjtx version into the logger').
   Built on ft8_lib by Karlis Goba (MIT license). JS feeds 12 kHz audio one block at a time, asks for a decode at the end
   of each slot, and asks for the 79 (FT8) / 105 (FT4) tones of a message to transmit. */
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <ft8/decode.h>
#include <ft8/encode.h>
#include <ft8/message.h>
#include <ft8/constants.h>
#include <common/monitor.h>

#define HT 256
static struct { char callsign[12]; uint32_t hash; } ht[HT];
/* Nov 18 (outside FT8 review #1): with all 256 places taken the search went round for ever and froze the app on a busy band
   (~5–10 min). Now every search stops after one lap; a full table overwrites the oldest call (biggest age, hash bits 24+). */
static void ht_add(const char* callsign, uint32_t hash) {
  uint16_t h10 = (hash >> 12) & 0x3FFu; int i = (h10 * 23) % HT, n = 0, old = -1, oldAge = -1;
  while (ht[i].callsign[0] && n < HT) {
    if (((ht[i].hash & 0x3FFFFFu) == hash) && !strcmp(ht[i].callsign, callsign)) { ht[i].hash &= 0x3FFFFFu; return; }
    int age = (int)(ht[i].hash >> 24); if (age > oldAge) { oldAge = age; old = i; }
    i = (i + 1) % HT; n++; }
  if (n >= HT) i = old < 0 ? i : old;   /* full: the oldest goes */
  strncpy(ht[i].callsign, callsign, 11); ht[i].callsign[11] = 0; ht[i].hash = hash;
}
static bool ht_lookup(ftx_callsign_hash_type_t t, uint32_t hash, char* callsign) {
  uint8_t sh = (t == FTX_CALLSIGN_HASH_10_BITS) ? 12 : (t == FTX_CALLSIGN_HASH_12_BITS ? 10 : 0);
  uint16_t h10 = (hash >> (12 - sh)) & 0x3FFu; int i = (h10 * 23) % HT;
  for (int n = 0; ht[i].callsign[0] && n < HT; n++) { if (((ht[i].hash & 0x3FFFFFu) >> sh) == hash) { strcpy(callsign, ht[i].callsign); return true; } i = (i + 1) % HT; }
  callsign[0] = 0; return false;
}
static void ht_age(void) {
  for (int i = 0; i < HT; i++) if (ht[i].callsign[0]) { uint8_t age = ht[i].hash >> 24; if (age > 20) { ht[i].callsign[0] = 0; ht[i].hash = 0; } else ht[i].hash = (((uint32_t)age + 1u) << 24) | (ht[i].hash & 0x3FFFFFu); }
}
static ftx_callsign_hash_interface_t hif = { .lookup_hash = ht_lookup, .save_hash = ht_add };

/* Nov 18 (review #4): one monitor per protocol, set up once. monitor_init() mallocs and free() is a no-op here (bump
   allocator), so setting it up every slot leaked ~241 KB a slot (8 MB → ~457 MB over 8 hours). */
static monitor_t mons[2]; static int made[2]; static monitor_t* mp = &mons[0]; static int ready = 0; static int proto = 0;
#define mon (*mp)
static float inbuf[4096];
#define MAXC 200
#define MAXD 64
static ftx_candidate_t cands[MAXC];
static ftx_message_t dec[MAXD]; static ftx_message_t* dech[MAXD];
/* results: per message {snr, dt, freq} floats + text 36 chars */
#define TW 48   /* Nov 10: 48 chars a line (was 40): a Fox message with long calls is up to 47 */
static float rnum[MAXD * 3]; static char rtext[MAXD * TW];
extern float expf(float); static float p10(float db){ return expf(db*0.2302585f); }
static float lg10(float x){ extern float log10f(float); return log10f(x); }
/* rough WSJT-X style SNR (2500 Hz) from the waterfall: power in the sent tone vs. the other tones */
static float SLOTN = 0, SLOTC = 0;
/* the slot's noise per bin: the median of every waterfall value (a sample of them), as power; median → mean of noise power = ÷ ln 2 */
static float slot_noise(const ftx_waterfall_t* wf) {
  static int hist[256]; for (int i = 0; i < 256; i++) hist[i] = 0;
  long n = (long)wf->num_blocks * wf->time_osr * wf->freq_osr * wf->num_bins, cnt = 0;
  for (long i = 0; i < n; i += 5) { hist[WF_ELEM_MAG_INT(wf->mag[i]) & 255]++; cnt++; }
  if (cnt < 100) return 0; long half = cnt / 2, acc = 0; int med = 0; for (; med < 256; med++) { acc += hist[med]; if (acc >= half) break; }
  return p10(med * 0.5f - 120.0f) / 0.6931f;
}
static float snr_of(const ftx_waterfall_t* wf, const ftx_candidate_t* c, const ftx_message_t* m){
  uint8_t tn[128]; int n = proto ? FT4_NN : FT8_NN, nt = proto ? 4 : 8;
  if (proto) ft4_encode(m->payload, tn); else ft8_encode(m->payload, tn);
  int off = ((c->time_offset * wf->time_osr + c->time_sub) * wf->freq_osr + c->freq_sub) * wf->num_bins + c->freq_offset;
  int stride = wf->time_osr * wf->freq_osr * wf->num_bins; float sg = 0, ns = 0; int k = 0, kn = 0;
  for (int i = 0; i < n; i++) { int b = c->time_offset + i; if (b < 0 || b >= wf->num_blocks) continue;
    const WF_ELEM_T* p = wf->mag + off + i * stride; if (c->freq_offset + nt + 3 > wf->num_bins || c->freq_offset < 3) { for (int j = 0; j < nt; j++) { if (j == tn[i]) sg += p10(WF_ELEM_MAG(p[j])); } k++; continue; }
    sg += p10(WF_ELEM_MAG(p[tn[i]])); k++;
    for (int j = -3; j < 0; j++) { ns += p10(WF_ELEM_MAG(p[j])); kn++; }
    for (int j = nt; j < nt + 3; j++) { ns += p10(WF_ELEM_MAG(p[j])); kn++; } }
  if (!k || !kn) return -99; sg /= k; ns /= kn;
  /* Nov 18 (FT8 review 4.3): the noise next to a STRONG signal is its own spill, so reports stopped rising at about +2 (FT4 +8).
     Above about −8 dB the noise now comes from the whole slot (the median bin: SLOTN, set in kft_decode); weak signals keep the
     neighbour bins, which the review measured within 1–2 dB of the truth. */
  if (SLOTN > 0 && sg > 8.0f * ns) ns = SLOTN;
  float r = (sg - ns) / ns; if (r < 1e-4f) r = 1e-4f;
  return 10.0f * lg10(r) - 26.0f + (proto ? 5.2f : 0.0f) + (ns == SLOTN ? SLOTC : 0.0f); }
static char txt[64]; static uint8_t tones[128];
/* Nov 10 (Brandon: Fox & Hound): ft8_lib does not decode the DXpedition message (i3=0 n3=1) the Fox uses to finish one Hound and call
   the next in ONE message: 'K1ABC RR73; W9XYZ <KH1/KH7Z> -08'. Bits: c28 (RR73 to) c28 (next Hound) h10 (the Fox's call, hashed) r5 n3 i3. */
extern int kpc_unpack28(uint32_t n28, const ftx_callsign_hash_interface_t* hash_if, char* result);
static int dx_decode(const ftx_message_t* m, char* out) {
  if (ftx_message_get_i3(m) != 0 || ftx_message_get_n3(m) != 1) return 0;
  const uint8_t* b = m->payload; char c1[16], c2[16], fx[16];
  uint32_t n1 = ((uint32_t)b[0] << 20) | ((uint32_t)b[1] << 12) | ((uint32_t)b[2] << 4) | (b[3] >> 4);
  uint32_t n2 = ((uint32_t)(b[3] & 0x0F) << 24) | ((uint32_t)b[4] << 16) | ((uint32_t)b[5] << 8) | b[6];
  uint16_t h10 = ((uint16_t)b[7] << 2) | (b[8] >> 6); int r = 2 * ((b[8] >> 1) & 0x1F) - 30;
  if (kpc_unpack28(n1, &hif, c1) < 0 || kpc_unpack28(n2, &hif, c2) < 0) return 0;
  if (!ht_lookup(FTX_CALLSIGN_HASH_10_BITS, h10, fx)) strcpy(fx, "...");
  char rs[8]; rs[0] = r < 0 ? '-' : '+'; int a = r < 0 ? -r : r; rs[1] = '0' + a / 10; rs[2] = '0' + a % 10; rs[3] = 0;
  out[0] = 0; strcat(out, c1); strcat(out, " RR73; "); strcat(out, c2); strcat(out, " <"); strcat(out, fx); strcat(out, "> "); strcat(out, rs);
  return 1;
}

__attribute__((export_name("kft_init"))) int kft_init(int ft4) {
  proto = ft4 ? 1 : 0;
  monitor_config_t c = { .f_min = 100, .f_max = 3100, .sample_rate = 12000, .time_osr = 2, .freq_osr = 2, .protocol = proto ? FTX_PROTOCOL_FT4 : FTX_PROTOCOL_FT8 };
  if (!ready) { memset(ht, 0, sizeof ht); }
  mp = &mons[proto]; if (!made[proto]) { monitor_init(mp, &c); made[proto] = 1; } else monitor_reset(mp); ready = 1; return mon.block_size;
}
__attribute__((export_name("kft_reset"))) void kft_reset(void) { monitor_reset(&mon); memset(mon.last_frame, 0, mon.nfft * sizeof(float)); }   /* + the leftover sound from the last slot (it was fresh when set up each slot) */
__attribute__((export_name("kft_in"))) float* kft_in(void) { return inbuf; }
__attribute__((export_name("kft_block"))) void kft_block(void) { monitor_process(&mon, inbuf); }
__attribute__((export_name("kft_blocks"))) int kft_blocks(void) { return mon.wf.num_blocks; }
__attribute__((export_name("kft_nums"))) float* kft_nums(void) { return rnum; }
__attribute__((export_name("kft_texts"))) char* kft_texts(void) { return rtext; }
static void put(const ftx_waterfall_t* wf, const ftx_candidate_t* c, const ftx_message_t* m, const char* text, int nd) {
  float f = (mon.min_bin + c->freq_offset + (float)c->freq_sub / wf->freq_osr) / mon.symbol_period;
  float t = (c->time_offset + (float)c->time_sub / wf->time_osr) * mon.symbol_period;
  rnum[nd * 3] = snr_of(wf, c, m); rnum[nd * 3 + 1] = t; rnum[nd * 3 + 2] = f;
  strncpy(rtext + nd * TW, text, TW - 1); rtext[nd * TW + TW - 1] = 0;
}
__attribute__((export_name("kft_decode"))) int kft_decode(int min_score, int ldpc_iter) {
  const ftx_waterfall_t* wf = &mon.wf;
  int nc = ftx_find_candidates(wf, MAXC, cands, min_score > 0 ? min_score : 10);
  SLOTN = slot_noise(wf);
  int nd = 0, npd = 0; ftx_message_t pdm[16]; int pdc[16]; for (int i = 0; i < MAXD; i++) dech[i] = 0;
  for (int k = 0; k < nc && nd < MAXD; k++) {
    const ftx_candidate_t* c = &cands[k];
    ftx_message_t m; ftx_decode_status_t st;
    if (!ftx_decode_candidate(wf, c, ldpc_iter > 0 ? ldpc_iter : 25, &m, &st)) continue;
    int h = m.hash % MAXD; bool empty = false, dup = false;
    /* Nov 18 (review #2): stop after one lap: with 64 places taken (busy slot + lines it cannot print) it went round for ever */
    for (int n = 0; n < MAXD && !empty && !dup; n++) { if (!dech[h]) empty = true; else if (dech[h]->hash == m.hash && !memcmp(dech[h]->payload, m.payload, sizeof m.payload)) dup = true; else h = (h + 1) % MAXD; }
    if (!empty) continue;
    memcpy(&dec[h], &m, sizeof m); dech[h] = &dec[h];
    char text[64]; ftx_message_offsets_t off;
    if (ftx_message_decode(&m, &hif, text, &off) != FTX_MESSAGE_RC_OK) {
      /* a Fox message waits until every other line of this slot is read, so the Fox's own CQ / reports have put its call in the hash table */
      if (ftx_message_get_i3(&m) == 0 && ftx_message_get_n3(&m) == 1 && npd < 16) { pdm[npd] = m; pdc[npd] = k; npd++; continue; }
      /* Nov 18 (FT8 review 4.6): a message ft8_lib cannot print (Field Day, RTTY Roundup, WW Digi / EU VHF …) still shows, so a busy
         contest band does not look empty. The screen reads a line starting with '~' as 'not a station to answer'. */
      { int i3 = ftx_message_get_i3(&m), n3 = ftx_message_get_n3(&m);
        const char* what = (i3 == 0 && (n3 == 3 || n3 == 4)) ? "~ FIELD DAY message" : i3 == 3 ? "~ RTTY ROUNDUP message" : i3 == 5 ? "~ WW DIGI / EU VHF message" : i3 == 0 && n3 == 0 ? "~ free-text message" : "~ a message this app can't read";
        put(wf, c, &m, what, nd++); }
      continue; }
    put(wf, c, &m, text, nd++);
  }
  for (int i = 0; i < npd && nd < MAXD; i++) { char text[64]; if (dx_decode(&pdm[i], text)) put(wf, &cands[pdc[i]], &pdm[i], text, nd++); }
  ht_age(); return nd;
}
__attribute__((export_name("kft_width"))) int kft_width(void) { return TW; }
__attribute__((export_name("kft_txt"))) char* kft_txt(void) { return txt; }
__attribute__((export_name("kft_tones"))) uint8_t* kft_tones(void) { return tones; }
/* returns number of tones (79 FT8 / 105 FT4), or -rc when the text can't be sent */
__attribute__((export_name("kft_encode"))) int kft_encode(int ft4) {
  ftx_message_t m; ftx_message_rc_t rc = ftx_message_encode(&m, &hif, txt);
  if (rc != FTX_MESSAGE_RC_OK) return -(int)rc - 1;
  if (ft4) { ft4_encode(m.payload, tones); return FT4_NN; }
  ft8_encode(m.payload, tones); return FT8_NN;
}
/* Nov 10, for the builders' tests: the tones of a RAW 77-bit payload (10 bytes put in kft_txt()), e.g. a pretend Fox's DXpedition message */
__attribute__((export_name("kft_encode_raw"))) int kft_encode_raw(int ft4) {
  uint8_t pl[10]; memcpy(pl, txt, 10); if (ft4) { ft4_encode(pl, tones); return FT4_NN; } ft8_encode(pl, tones); return FT8_NN;
}
