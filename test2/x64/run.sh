#!/bin/bash

target=${1:-baseline}
log_file=$target.log

qemu-system-x86_64 -cpu host -enable-kvm \
    -m 1G \
    -drive format=raw,file=fat:rw:root \
    -drive if=pflash,format=raw,file="bios_${target}.bin" \
    -debugcon file:$log_file \
    -global isa-debugcon.iobase=0x402 \
    -net none \
    -nographic
