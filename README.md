# Archer AX23 EU v2.0 OpenWrt build project

> **Experimental firmware — RAM-only development image.** Physical operation on the exact TP-Link Archer AX23 EU V2.0 has not been verified. Do not use the OEM web-interface firmware upgrade, do not flash, and do not attempt persistent installation. A first RAM boot requires the documented serial, GPIO, bootloader and stock-recovery safety checks.

This repository contains a reproducible OpenWrt build pipeline, an ordered 27-patch series, offline validation tools and a hardware test plan for one exact target: **TP-Link Archer AX23 EU V2.0**. It is an experimental community project, not an official OpenWrt release and not supported by TP-Link.

The port builds on [Sply-Dev’s Archer AX23 v2 project](https://github.com/Sply-Dev/openwrt-archer-ax23-v2) and credits Sply as the original port and hardware-documentation author. This repository is a separate build and engineering project; it does not replace or speak for Sply’s work.

## Hardware target

- Qualcomm IPQ5018 SoC, 256 MiB RAM, integrated 2.4 GHz radio.
- External QCN6122 5 GHz radio using the shared Qualcomm Q6 multi-PD architecture.
- RTL8367S-VB Ethernet switch and IPQ5018 UNIPHY/PCS Ethernet path.
- Default device-tree profile uses the 2.5 Gbps HSGMII CPU link.

Do not use this target profile on AX23 v1 or other regional/hardware revisions. The optional 1 Gbps SGMII diagnostic variant is kept separately at `patches/variants/trunk-1g-sgmii.patch` and is not part of the default build.

## Current status

The latest recorded local build used 27 project patches and produced an initramfs FIT image for `config@mp02.1`. Offline artifact validation recorded **77 PASS, 1 INFO, 0 FAIL**. The report explains the helper output lines that can make raw output counts appear higher. Latest local tests recorded **12 shell unit suites PASS, 1 SKIP**, **31 Python unit tests PASS**, and static checks PASS with **53 development-DTB checks**. The skipped BDF extractor suite needs `ubireader_extract_images`; two EU ART-fixture subchecks were also skipped because private stock fixtures were not available. Static checks passed (53 DTB checks; no baseline DTB was available). See `reports/artifacts-dev.txt`, `reports/build-manifest.json`, and `reports/final-validation-and-ram-load-conclusions.md`.

The build validated source, FIT structure, selected DTB policy, embedded firmware/modules and compiled changes. It does **not** establish physical boot, RF calibration acceptance, emitted RF power, Ethernet traffic, GPIO wiring, cold-boot stability, NAND runtime state or recovery behavior.

The most recent workstation image was 13,330,704 bytes, SHA256 `6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff`. It is deliberately **not included** in this public repository. It remains only at the developer’s local WSL path documented in `reports/CODEX_FINAL_HANDOVER.md`. Do not treat its hash as proof of hardware readiness.

## Engineering changes

The patch series and supporting reports cover:

- AX23 v2 device integration, EU board-data identity selection, radio startup profiles and calibration-preserving extraction.
- Qualcomm Q6 multi-power-domain recovery and failure unwinding.
- ath11k low-memory mode-2 ring sizing, exact DMA allocation sizes and partial-start cleanup.
- IPQ5018 clock/UNIPHY/PCS sequencing and RTL8367S-VB reset/SerDes settling.
- Read-only MTD partitions, UBI attach restrictions, RAM-only image policy and sysupgrade interlock.
- Offline FIT/DTB/artifact checks, unit tests, network simulations and read-only, redacting hardware diagnostics.

The diagnostics are streamed from a PC over SSH and are not embedded in the firmware image. Configured/driver-reported transmit power is not a measurement of emitted RF power. The S2.4 traffic check requires fresh endpoint counters; ART byte counts do not establish BDF target-power semantics.

## Build prerequisites

- Linux x86_64, WSL2 Ubuntu/Debian on the WSL filesystem (not `/mnt/c`), or a compatible Linux container.
- OpenWrt build prerequisites; `tools/build-dev.sh` checks the host tools.
- Network access for source/feed downloads on a fresh build.
- At least 25 GB free for a fresh baseline; 30 GB is recommended. Four or more CPU cores are recommended. A prepared cached build needs substantially less space.
- Private, legally obtained EU board data for both radios to build a Wi-Fi-capable image. The extraction tools place it in ignored `board-data/`. Do not commit or redistribute OEM firmware, board data or factory calibration.

### Reproducible build

```sh
git clone https://github.com/john35413/openwrt-archer-ax23-v2-build.git
cd openwrt-archer-ax23-v2-build
# Supply locally extracted EU board-data files as described by tools/bdf/.
bash tools/build-dev.sh --variant dev --jobs 4
```

For an already prepared tree, use `bash tools/build-dev.sh --variant dev --resume --jobs 4`. The pinned OpenWrt, Sply-Dev and feed revisions are in `configs/sources.lock`; the complete firmware patch order is `patches/openwrt/series`. Build by-products are local and ignored. The pipeline creates experimental factory/sysupgrade by-products for analysis only; **they are not supported installation images and must not be flashed**.

### Validation

```sh
bash tools/validate-artifacts.sh build/dev/openwrt dev
bash tests/static/run-static.sh
bash tools/test-dev.sh all
```

Individual unit suites live in `tests/unit/`. Some suites require optional tools or private EU fixtures and report SKIP when those inputs are absent. Network and full-system twin tests are simulations; they are not hardware validation. Do not weaken a failed check to obtain a pass.

## Repository structure

- `patches/openwrt/` — ordered firmware series and patch list.
- `patches/variants/` — optional, non-default hardware diagnostic variants.
- `configs/` — pinned source/feed revisions, target fragments and UCI examples.
- `tools/` — build, board-data extraction, FIT/artifact validation and U-Boot analysis.
- `tests/unit/`, `tests/static/`, `tests/network/`, `tests/nand/`, `tests/twin/` — offline suites and simulations.
- `tests/hardware/` — read-only diagnostics and physical test plan.
- `reports/` — engineering audits, provenance, handover and first-boot checks.
- `artifacts/ram-only/` — text manifests/checksums; firmware binaries are not distributed here.

## Safety and unresolved hardware checks

Before any RAM boot, confirm the exact EU V2.0 board, measured UART voltage and pins, a stock recovery path, bootloader RAM/FIT behavior and passive GPIO 26/39 reset mapping/polarity. The FIT has hashes but no signature node; never bypass a bootloader signature policy. Stop if the exact bootloader rejects it or requires a bypass.

No physical AX23 test has yet verified radio/BDF acceptance, live MTD/UBI flags, GPIO reset wiring, 2.5 G frame transfer, cold-boot stability, measured RF output or Q6 recovery under real memory pressure. See `reports/first-ram-boot-checklist.md` and `tests/hardware/HARDWARE-TEST-PLAN.md`. No persistent installation procedure is supported.

## Contributions

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep fixes narrowly scoped and evidence-backed; preserve OpenWrt/Linux license and copyright notices; add focused regression tests; update the patch series and reports. Never submit proprietary OEM firmware, private board data/calibration, credentials, raw device logs with identifiers, build caches or generated firmware images.

## Licensing and attribution

See [LICENSES.md](LICENSES.md) and `licenses/GPL-2.0.txt`. Existing SPDX identifiers and upstream copyright notices are retained. This repository does not claim to relicense OpenWrt, Linux, Sply-Dev or other third-party work.
