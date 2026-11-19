#!/bin/sh
# Rebuild kpc-ft8.wasm (Brandon Oct 17: FT8 tab in the KPC Logger). Needs clang with the wasm32 target + wasm-ld.
# App copy (Nov 10): the same files as the website's .claude/build/ft8 + kpcdx.inc. After a build: refresh www/kpc-ft8-wasm.js (base64 line, see its header) and run node tools/tests/ft8-dx.js
# ft8_lib (Karlis Goba, MIT): git clone https://github.com/kgoba/ft8_lib $L
set -e
H=$(cd "$(dirname "$0")" && pwd); L=${L:-/tmp/ft8_lib}; O=$(mktemp -d)
[ -d "$L" ] || git clone -q https://github.com/kgoba/ft8_lib "$L"
# Nov 10: message.c gets kpcdx.inc on its end (a door to its static unpack28 for the Fox / Hound DXpedition message)
cat $L/ft8/message.c $H/kpcdx.inc > $O/message_kpc.c
# Nov 18 (outside FT8 review #5): ft8_lib looks for a start from 10 symbols early to 20 late: 1.6 / 3.2 s on FT8, but only
# 0.48 / 0.96 s on FT4 (0.048 s symbols), so an FT4 station half a second late was not heard at all. FT4 now looks about
# as far in SECONDS as FT8 (−21 … +42 symbols). FT8 unchanged.
sed 's/for (candidate.time_offset = -10; candidate.time_offset < 20; ++candidate.time_offset)/for (candidate.time_offset = (wf->protocol == FTX_PROTOCOL_FT4 ? -21 : -10); candidate.time_offset < (wf->protocol == FTX_PROTOCOL_FT4 ? 42 : 20); ++candidate.time_offset)/' $L/ft8/decode.c > $O/decode_kpc.c
grep -q 'FTX_PROTOCOL_FT4 ? -21' $O/decode_kpc.c || { echo 'decode.c patch did not apply'; exit 1; }
for f in $(ls $L/ft8/*.c | grep -v '/message.c$' | grep -v '/decode.c$') $O/decode_kpc.c $O/message_kpc.c $L/fft/kiss_fft.c $L/fft/kiss_fftr.c $L/common/monitor.c $H/kpcft8.c $H/libc.c; do
  clang --target=wasm32 -O2 -nostdlib -ffreestanding -isystem $H/inc -I$L -I$L/ft8 -Wno-everything -c $f -o $O/$(basename $f .c).o; done
wasm-ld --no-entry --allow-undefined -z stack-size=1048576 --initial-memory=8388608 -o ${OUT:-$H/../../www/kpc-ft8.wasm} $O/*.o --export=malloc
echo built ${OUT:-kpc-ft8.wasm} from ft8_lib $(git -C $L rev-parse --short HEAD 2>/dev/null)
