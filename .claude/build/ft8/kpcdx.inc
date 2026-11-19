
/* ---- appended by KPC's build.sh (Nov 10): a door to the static unpack28() for DXpedition (Fox / Hound, i3=0 n3=1) messages ---- */
int kpc_unpack28(uint32_t n28, const ftx_callsign_hash_interface_t* hash_if, char* result) { ftx_field_t ft; return unpack28(n28, 0, 1, hash_if, result, &ft); }
