# μEFI Artifact Evaluation

## File Structure

```
.
├── README.md
├── test0
│   ├── aarch64
│   │   ├── bcm2711-rpi-4-b.dtb
│   │   ├── bcm2711-rpi-400.dtb
│   │   ├── bcm2711-rpi-cm4.dtb
│   │   ├── config.txt
│   │   ├── firmware
│   │   ├── fixup4.dat
│   │   ├── overlays
│   │   ├── RPI_EFI.fd
│   │   └── start4.elf
│   └── x64
│       └── bios.bin
├── test1
│   ├── analyze.py
│   └── x64
│       ├── boot_time_test.expect
│       ├── FV
│       │   ├── bios-1.bin
│       │   ├── bios0.bin
│       │   ├── bios1.bin
│       │   ├── bios2.bin
│       │   ├── bios3.bin
│       │   ├── bios4.bin
│       │   ├── bios5.bin
│       │   └── bios6.bin
│       └── grub_linux.img
├── test2
│   ├── aarch64
│   │   ├── baseline
│   │   │   └── RPI_EFI.fd
│   │   ├── fat
│   │   │   └── RPI_EFI.fd
│   │   └── fat_diskio
│   │       └── RPI_EFI.fd
│   ├── analyze.py
│   └── x64
│       ├── bios_baseline.bin
│       ├── bios_fat_diskio.bin
│       ├── bios_fat.bin
│       └── run.sh
└── test3
    ├── aarch64
    │   ├── RPI_EFI.fd
    │   ├── SandboxC.efi
    │   └── SandboxS.efi
    ├── analyze.py
    └── x64
        ├── bios.bin
        ├── root
        │   ├── SandboxC.efi
        │   └── SandboxS.efi
        └── run.sh
```

## 1 Getting Started Instructions

We provide a pre-configured testing environment for your convenience, please refer to HotCRP for more information.

### 1.1 Prerequisites

On x86_64 platform:

- Hardware virtualization support (VT-x/AMD-V) enabled.
- Linux KVM enabled.
- qemu-system-x86_64 installed (version 8.2.8 is verified).

On AArch64 platform:

- Raspberry Pi 4 Model B.

### 1.2 Boot with custom BIOS image with QEMU/KVM on x86_64 platform

The following commands are used to test if your environment is set up correctly.

Use the following command to boot into the UEFI shell with a provided bios image:

```bash
cd test0/x64

qemu-system-x86_64 -cpu host -enable-kvm \
          -m 1G \
          -drive format=raw,file=fat:rw:root \
          -drive if=pflash,format=raw,file=bios.bin \
          -debugcon file:debug.log \
          -global isa-debugcon.iobase=0x402 \
          -net none \
          -nographic
```

### 1.3 Running UEFI modules in UEFI shell on Raspi4

**Option1: Running on your own Raspberry Pi 4**

1. Make sure your eeprom is up-to-date with the latest version. Refer to this [documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#bootloader_update_stable) if needed.
2. Repartition the sdcard with fat16 or fat32.
3. Copy the base firmwares for Raspi4 into the sdcard. (files under test0/aarch64)
4. Boot the Raspi4 with the sdcard.
5. Normally a UEFI shell will be prompted for input.

To use the custom BIOS image, replace the `RPI_EFI.fd` with provided custom binary. Initiate Minicom and multiplex the stdout log.

```bash
minicom -D /dev/ttyUSBX -C output.log
```

**Option2: Using the provided Raspberry Pi 4**

For the convenience of Artifact Evaluation, a Raspberry Pi was connected to the host machine and pre-configured to enter the UEFI Shell. Note that Test2 cannot be executed in this way as it requires replacing the bios image.

The Raspberry Pi can be accessed using the following command:

```bash
# After ssh into the machine for AE
minicom -D /dev/ttyUSB0 -b 115200 -C output.log
```

```shell
# In UEFI shell
fs0:

ls
```

You should see the files in the root directory of the SD card.

You can reboot the Raspberry Pi by running the following command in the UEFI shell:

```shell
# In UEFI shell
reset
```

After rebooting, you can enter the UEFI shell by pressing `F1` or `Fn + F1` when you see following output:

```shell
[Bds]=============End Load Options Dumping============
[Bds]BdsWait ...ZzzzzzzzzzzZ...
[Bds]BdsWait(5)..Zzzz...
```

Or you can under the UEFI shell via Boot Manager.

## 2 Boot Performance Test (Test 1)

**Description**: This test is corresponding to Figure 8 in the paper.

In the boot performance test, the baseline is defined as the BIOS image compiled with EDK II that does not run the Sandbox Manager (bios-1.bin). The image bios0.bin includes only the Sandbox Manager, without sandboxing any UEFI modules. Starting from this configuration, we incrementally increase the number of UEFI modules executed inside the sandbox from bios1.bin to bios6.bin.

**Test Goal**: This test demonstrates that the boot-time overhead introduced by μEFI is minimal: the overhead of running only the Sandbox Manager is less than 1%, and even with six sandboxed modules, the total overhead remains under 2%.

The boot performance is only tested on the x86_64 platform as we failed to configure to boot Linux with GRUB on Raspi4.

### 2.1 Run the test

You need to download `grub_linux.img` ([Link](https://ipads.se.sjtu.edu.cn:1313/seafhttp/f/7101333915ec4461ac0a/?op=view)) and move it under `test1/x64`

```bash
cd test1/x64

./boot_time_test.expect
```

### 2.2 Analyze the results
```bash
# under test1 directory
python3 analyze.py x64/results.log
```

You should see the output in following format:

```
Baseline (bios-1): 9920918729
Growth relative to bios-1:
bios0: +75997830 (0.7660%)
bios1: +86610585 (0.8730%)
bios2: +88136049 (0.8884%)
bios3: +102482316 (1.0330%)
bios4: +118177375 (1.1912%)
bios5: +124704339 (1.2570%)
bios6: +143379182 (1.4452%)
```

## 3 Module Execution Performance Test (Test 2)

**Description**: This test is corresponding to Figure 9 and Figure 10 in the paper. Each execution includes both end-to-end (E2E) test (Figure 9), and interface-level test for individual file operations (Figure 10).

In this test, the baseline is defined as the BIOS image compiled with EDK II that does not run the Sandbox Manager. The test revolves around the efficiency of FAT operations on a file. Starting from this configuration, we incrementally move FAT and DiskIO into the sandbox mode from bios_baseline.bin (Baseline), bios_fat.bin (FAT) to bios_fat_diskio.bin (FAT + DiskIO). Each test with different filesize is conducted under 16 iterations. 

Note that the TSC on x86_64 and aarch64 is sometimes skewed (the timestamp readed after the operation is smaller than the timestamp before the operation) , it's necessary to remove theses abnormalities (larger than 1e9 cycles) from the data points.

**Test Goal**: This test demonstrate that the overhead introduced by μEFI in module execution is small.
  * End-to-end test: On x86_64, the overhead of running two relevant modules in sandboxes is less than 1.5%. On aarch64, the overhead is less than 10%.
  * Interface-level test: The overhead of FAT interfaces when modules are executed in sandboxes are small compared to the original execution time. The overheads of Open/Delete/Flush operations primarily reflect the natural fluctuations in the interface execution times, which are less than 5% compared to the baseline.

### 3.1  Run the test

Execute the given bios image.

* On QEMU

  ```bash
  cd test2/x64

  # Replace baseline with fat or fat_diskio when testing other cases
  bash run.sh baseline
  ```

* On Raspi4
  
  Replace `RPI_EFI.fd` in the SD card with `test2/aarch64/baseline/RPI_EFI.fd` (replace `baseline` with `fat` or `fat_diskio` when testing other cases). Then boot Raspi4 and enter UEFI shell.

  ```bash
  minicom -D /dev/ttyUSB0 -b 115200 -C test2/aarch64/baseline.log
  ```

After entering the UEFI shell:

```shell
# in UEFI shell
fs0:

fs_test 16
```

The execution results will be recorded in corresponding log files.

### 3.2 Analyze the results

```bash
python3 analyze.py --base x64/baseline.log --test x64/fat.log
```

Expected outcome is as follows.
```
=== End-to-End Performance Comparison ===

--- Average End-to-End Cycles (128 bytes) ---
Base Mean(E2E)  Test Mean(E2E)  Diff(E2E)       Diff %
1.024898e+08    1.052756e+08    2.785812e+06    2.718135

--- Average End-to-End Cycles (4096 bytes) ---
Base Mean(E2E)  Test Mean(E2E)  Diff(E2E)       Diff %
1.285343e+08    1.327137e+08    4.179431e+06    3.251607

--- Average End-to-End Cycles (16384 bytes) ---
Base Mean(E2E)  Test Mean(E2E)  Diff(E2E)       Diff %
2.198812e+08    2.278494e+08    7.968246e+06    3.623887

=== File Interfaces Performance Comparison ===

--- Average Operation Cycles (128 bytes) ---
Base Mean(O2O)  Test Mean(O2O)  Diff(O2O)       Diff %
Type
DeleteFile      6.252264e+07    6.454247e+07    2.019826e+06    3.230552
FlushFile       7.507569e+07    7.948698e+07    4.411295e+06    5.875797
GetFileInfo     3.391750e+03    1.687693e+05    1.653775e+05    4875.875777
OpenFile        2.356547e+07    2.290368e+07    -6.617859e+05   -2.808287
ReadFile        1.930375e+03    7.774520e+04    7.581482e+04    3927.466166
SetFilePosition 4.954667e+02    6.526127e+04    6.476580e+04    13071.676534
WriteFile       2.898067e+03    7.968987e+04    7.679180e+04    2649.759610
```

## 4 Micro-test (Test 3)

**Description**: This test is corresponding to Figure 11 in the paper.

In this test, we examine the latency of interface calls involving different parameter types.

**Test Goal**: This test analyzes the sources of overhead in μEFI.

### 4.1 Run the test

Execute the given bios image.

* On QEMU

  ```bash
  cd test3/x64

  bash run.sh
  ```

* On Raspi4
  
  1. Replace `RPI_EFI.fd` in the SD card with `test3/aarch64/RPI_EFI.fd`.
  2. Copy `test3/aarch64/SandboxC.efi` and `test3/aarch64/SandboxS.efi` into the SD card.
  3. Boot Raspi4 and enter UEFI shell.

After entering the UEFI shell, run the following command to execute the test:

```shell
# in UEFI shell
fs0:

load SandboxS.efi

load SandboxC.efi
```

The output is saved in `debug.log` and you can exit qemu by pressing `Ctrl+A` and then `X`.

### 4.2 Analyze the result of micro-test.

```bash
# under test3 directory
python3 analyze.py x64/debug.log
```

You should see the output in following format:

```
Results of micro tests.

Simple Call Test
DBQuery: 98.15
ParamsCopy: 79.01
ContextSwitch: 1021.28
ParamsSync: 87.96

Input Object Test
DBQuery: 97.64
ParamsCopy: 1189.66
ContextSwitch: 1033.03
ParamsSync: 502.72

Input Buffer Test
DBQuery: 101.79
ParamsCopy: 1448.50
ContextSwitch: 1042.21
ParamsSync: 510.64

Output Buffer Test
DBQuery: 109.50
ParamsCopy: 887.50
ContextSwitch: 1416.14
ParamsSync: 2029.21
```

In Output Buffer test, the execution time of callee logic is also included in `ContextSwitch` and can be manually computed.