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
static void ht_add(const char* callsign, uint32_t hash) {
  uint16_t h10 = (hash >> 12) & 0x3FFu; int i = (h10 * 23) % HT;
  while (ht[i].callsign[0]) { if (((ht[i].hash & 0x3FFFFFu) == hash) && !strcmp(ht[i].callsign, callsign)) { ht[i].hash &= 0x3FFFFFu; return; } i = (i + 1) % HT; }
  strncpy(ht[i].callsign, callsign, 11); ht[i].callsign[11] = 0; ht[i].hash = hash;
}
static bool ht_lookup(ftx_callsign_hash_type_t t, uint32_t hash, char* callsign) {
  uint8_t sh = (t == FTX_CALLSIGN_HASH_10_BITS) ? 12 : (t == FTX_CALLSIGN_HASH_12_BITS ? 10 : 0);
  uint16_t h10 = (hash >> (12 - sh)) & 0x3FFu; int i = (h10 * 23) % HT;
  while (ht[i].callsign[0]) { if (((ht[i].hash & 0x3FFFFFu) >> sh) == hash) { strcpy(callsign, ht[i].callsign); return true; } i = (i + 1) % HT; }
  callsign[0] = 0; return false;
}
static void ht_age(void) {
  for (int i = 0; i < HT; i++) if (ht[i].callsign[0]) { uint8_t age = ht[i].hash >> 24; if (age > 20) { ht[i].callsign[0] = 0; ht[i].hash = 0; } else ht[i].hash = (((uint32_t)age + 1u) << 24) | (ht[i].hash & 0x3FFFFFu); }
}
static ftx_callsign_hash_interface_t hif = { .lookup_hash = ht_lookup, .save_hash = ht_add };

static monitor_t mon; static int ready = 0; static int proto = 0;
static float inbuf[4096];
#define MAXC 200
#define MAXD 64
static ftx_candidate_t cands[MAXC];
static ftx_message_t dec[MAXD]; static ftx_message_t* dech[MAXD];
/* results: per message {snr, dt, freq} floats + text 36 chars */
static float rnum[MAXD * 3]; static char rtext[MAXD * 40];
extern float expf(float); static float p10(float db){ return expf(db*0.2302585f); }
static float lg10(float x){ extern float log10f(float); return log10f(x); }
/* rough WSJT-X style SNR (2500 Hz) from the waterfall: power in the sent tone vs. the other tones */
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
  if (!k || !kn) return -99; sg /= k; ns /= kn; float r = (sg - ns) / ns; if (r < 1e-4f) r = 1e-4f;
  return 10.0f * lg10(r) - 26.0f + (proto ? 5.2f : 0.0f); }
static char txt[64]; static uint8_t tones[128];

__attribute__((export_name("kft_init"))) int kft_init(int ft4) {
  proto = ft4 ? 1 : 0;
  monitor_config_t c = { .f_min = 100, .f_max = 3100, .sample_rate = 12000, .time_osr = 2, .freq_osr = 2, .protocol = proto ? FTX_PROTOCOL_FT4 : FTX_PROTOCOL_FT8 };
  if (!ready) { memset(ht, 0, sizeof ht); }
  monitor_init(&mon, &c); ready = 1; return mon.block_size;
}
__attribute__((export_name("kft_reset"))) void kft_reset(void) { monitor_reset(&mon); }
__attribute__((export_name("kft_in"))) float* kft_in(void) { return inbuf; }
__attribute__((export_name("kft_block"))) void kft_block(void) { monitor_process(&mon, inbuf); }
__attribute__((export_name("kft_blocks"))) int kft_blocks(void) { return mon.wf.num_blocks; }
__attribute__((export_name("kft_nums"))) float* kft_nums(void) { return rnum; }
__attribute__((export_name("kft_texts"))) char* kft_texts(void) { return rtext; }
__attribute__((export_name("kft_decode"))) int kft_decode(int min_score, int ldpc_iter) {
  const ftx_waterfall_t* wf = &mon.wf;
  int nc = ftx_find_candidates(wf, MAXC, cands, min_score > 0 ? min_score : 10);
  int nd = 0; for (int i = 0; i < MAXD; i++) dech[i] = 0;
  for (int k = 0; k < nc && nd < MAXD; k++) {
    const ftx_candidate_t* c = &cands[k];
    ftx_message_t m; ftx_decode_status_t st;
    if (!ftx_decode_candidate(wf, c, ldpc_iter > 0 ? ldpc_iter : 25, &m, &st)) continue;
    int h = m.hash % MAXD; bool empty = false, dup = false;
    do { if (!dech[h]) empty = true; else if (dech[h]->hash == m.hash && !memcmp(dech[h]->payload, m.payload, sizeof m.payload)) dup = true; else h = (h + 1) % MAXD; } while (!empty && !dup);
    if (!empty) continue;
    memcpy(&dec[h], &m, sizeof m); dech[h] = &dec[h];
    char text[FTX_MAX_MESSAGE_LENGTH]; ftx_message_offsets_t off;
    if (ftx_message_decode(&m, &hif, text, &off) != FTX_MESSAGE_RC_OK) continue;
    float f = (mon.min_bin + c->freq_offset + (float)c->freq_sub / wf->freq_osr) / mon.symbol_period;
    float t = (c->time_offset + (float)c->time_sub / wf->time_osr) * mon.symbol_period;
    rnum[nd * 3] = snr_of(wf, c, &m); rnum[nd * 3 + 1] = t; rnum[nd * 3 + 2] = f;
    strncpy(rtext + nd * 40, text, 39); rtext[nd * 40 + 39] = 0; nd++;
  }
  ht_age(); return nd;
}
__attribute__((export_name("kft_txt"))) char* kft_txt(void) { return txt; }
__attribute__((export_name("kft_tones"))) uint8_t* kft_tones(void) { return tones; }
/* returns number of tones (79 FT8 / 105 FT4), or -rc when the text can't be sent */
__attribute__((export_name("kft_encode"))) int kft_encode(int ft4) {
  ftx_message_t m; ftx_message_rc_t rc = ftx_message_encode(&m, &hif, txt);
  if (rc != FTX_MESSAGE_RC_OK) return -(int)rc - 1;
  if (ft4) { ft4_encode(m.payload, tones); return FT4_NN; }
  ft8_encode(m.payload, tones); return FT8_NN;
}
