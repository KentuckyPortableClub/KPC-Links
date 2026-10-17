#!/bin/sh
# Rebuild kpc-ft8.wasm (Brandon Oct 17: FT8 tab in the KPC Logger). Needs clang with the wasm32 target + wasm-ld.
# ft8_lib (Karlis Goba, MIT): git clone https://github.com/kgoba/ft8_lib $L
set -e
H=$(cd "$(dirname "$0")" && pwd); L=${L:-/tmp/ft8_lib}; O=$(mktemp -d)
[ -d "$L" ] || git clone -q https://github.com/kgoba/ft8_lib "$L"
for f in $L/ft8/*.c $L/fft/kiss_fft.c $L/fft/kiss_fftr.c $L/common/monitor.c $H/kpcft8.c $H/libc.c; do
  clang --target=wasm32 -O2 -nostdlib -ffreestanding -isystem $H/inc -I$L -Wno-everything -c $f -o $O/$(basename $f .c).o; done
wasm-ld --no-entry --allow-undefined -z stack-size=1048576 --initial-memory=8388608 -o $H/../../../kpc-ft8.wasm $O/*.o --export=malloc
echo built kpc-ft8.wasm
