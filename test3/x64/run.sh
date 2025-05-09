#!/bin/bash

# Get BIOS file path from input argument, or use default
bios_file=${1:-bios.bin}

qemu-system-x86_64 -cpu host -enable-kvm \
    -m 1G \
    -drive format=raw,file=fat:rw:root \
    -drive if=pflash,format=raw,file="$bios_file" \
    -debugcon file:debug.log \
    -global isa-debugcon.iobase=0x402 \
    -net none \
    -nographic
