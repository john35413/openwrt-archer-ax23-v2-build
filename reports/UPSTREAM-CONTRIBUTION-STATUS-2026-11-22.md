# AX23 V2 — upstream contribution and pre-hardware update (2026-11-22)

This is a documentation-only status report. It does **not** amend our compiled firmware or constitute a physical hardware validation.

## Original author and proposal

- Original AX23 V2 port and reported hardware tests: [Sply-Dev/openwrt-archer-ax23-v2](https://github.com/Sply-Dev/openwrt-archer-ax23-v2).
- Our independent build and engineering reference: [john35413/openwrt-archer-ax23-v2-build](https://github.com/john35413/openwrt-archer-ax23-v2-build).
- Upstream-facing **Draft PR #2**: https://github.com/Sply-Dev/openwrt-archer-ax23-v2/pull/2
- Fork branch: [john35413/openwrt-archer-ax23-v2 / contrib/ax23-wifi-memory-recovery](https://github.com/john35413/openwrt-archer-ax23-v2/tree/contrib/ax23-wifi-memory-recovery).
- PR integration documentation commit: `dd10fb726f731f587adbf7df0659327ca9be6187`.
- Published standalone dev preboot-procedure fix: `9b4f39fbad88b043ddb7b62b5f17256333a029a8`.

## What was proposed, not merged

The fork contains seven patch wrappers derived from our 27-patch independent development series, covering ath11k low-memory RX/TX ring sizing, exact coherent DMA allocation sizing, error-path/descriptor and datapath cleanup, and Qualcomm IPQ5018 Q6 multi-power-domain recovery. It deliberately does not change Sply's DTS, GPIO mapping, switch initialization or existing reported hardware-tested Ethernet behavior. The detailed patch-by-patch inclusion/exclusion inventory is in the fork's `docs/CONTRIBUTION-INVENTORY.md`.

## New verification — integration build passed

On the isolated contribution build checkout, the seven wrappers applied in order to pinned OpenWrt `98b1185d039344553aaf8270d0661cfad4f0a54d`. The target used kernel 6.18.55 and backports 7.2. Kernel preparation/compilation and mac80211 preparation/compilation completed, producing `qcom_q6v5_mpd.o` with `q6_wcss_recover_userpds`, plus AArch64 ath11k objects and `ath11k.ko`. Thirteen Python host tests, the modeled DMA alignment/ring checks and eight modeled Q6 recovery scenarios passed. A transient host apk rebuild failure caused by stale copied staging metadata was corrected **in the isolated build tree only** before the successful retry. Some of Sply's older baseline patches applied with context fuzz/offset; the seven proposed wrappers themselves passed `git apply --check`.

**Limits:** This was an incremental target kernel/mac80211 integration build, **not a complete firmware build on the PR branch**, and not a physical test or proof of DMA hardware/concurrency safety. The separate standalone image has 77 artifact checks PASS, one informational check, zero FAIL; that validates a different artifact and must not be confused with the fork build. The existing QMI board-file error `-12` is not proven fixed.

## Latest standalone pre-hardware safety findings

The current standalone initramfs image contains `/init`. The previously documented `init=/bin/sh` would not reliably prevent normal startup: the correct early-initramfs shell argument is **`rdinit=/bin/sh`**. All active preboot instructions and regression checks were corrected on standalone `dev` at `9b4f39f`; **the image was not rebuilt**.

Source evidence shows the OEM U-Boot/stock switch initialization predominantly resets RTL8367S-VB via **GPIO26**, whereas the standalone compiled DTS assigns active-low **GPIO39**, which the Linux switch driver can drive low for 25 ms. Source analysis and other units' reports do **not** verify the physical GPIO39 net on this exact board. The shipped U-Boot's real memory map, FIT acceptance and UART electrical signals also remain unknown. **NO-GO for bootm** until the passive electrical checks and console gates in [FINAL_PREBOOT_GATE.md](FINAL_PREBOOT_GATE.md) pass. Source-derived U-Boot configuration values are not live observations.

A separate, **receive-only** Windows UART preflight tool was prepared for future measured 1.8 V UART access, but **was not tested on the physical router**. It does not transmit commands. Do not treat its existence as evidence of GPIO continuity, a working serial port, or safe boot.

## Requested upstream review

We welcome Sply's assessment of the selected ath11k/Q6 patches, the differences in GPIO26/39 reset evidence, and any measured UART/U-Boot or RF/board-data findings from his hardware. Please do not infer that the original author's device has our standalone GPIO problem: the reviewed trees and test configurations are different.

No firmware binary, private OEM board data, factory calibration, keys, raw UART logs, or router settings were published or changed in this status report. No NAND flashing, physical router access, or upstream merge occurred.
