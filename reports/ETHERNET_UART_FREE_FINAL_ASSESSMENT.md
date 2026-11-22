# AX23 V2 UART-free boot and first-boot assessment

**Scope:** offline/source review only. No router access, button press, network request, reboot, firmware upload, flash operation, UART connection, or build was performed for this assessment.

## 1. UART-free verdict

### C. NO SUPPORTED PATH FOUND

For the stock boot configuration described by TP-Link's AX23 V2 GPL U-Boot, autoboot selects `bootipq`, which reads the selected NAND FIT and attempts the alternate slot. It does not issue DHCP/BOOTP or request an image with TFTP. U-Boot has network/TFTP commands, but `tftpboot` is useful only after reaching the interactive prompt; interrupting autoboot requires the short serial-console window. A TFTP server on the PC does not cause the router to request an image.

The other inspected paths do not execute this OpenWrt image:

| Candidate | Evidence and requirement | Result for OpenWrt |
|---|---|---|
| Stock autoboot over Ethernet | OEM GPL flow calls `bootipq`; no network-load branch is in the recorded autoboot path. | No temporary RAM load. |
| U-Boot `tftpboot` + `bootm` | Network and boot commands are built in, but an operator must interrupt autoboot and enter commands. The exact shipped prompt/build remains unobserved on this unit. | Candidate only with serial-console access; no signature bypass should be attempted. |
| Stock web firmware update | Official guide describes selecting vendor firmware; local OEM flasher analysis finds TP-Link RSA verification. | Stock-signed update/recovery only; not this development FIT. No upload was attempted. |
| Reset-held U-Boot HTTP recovery | OEM U-Boot source has an HTTP recovery path and signature checks; it writes slot 0 after accepting an image. | Potentially restores supported stock firmware. Not RAM execution. Testing it requires a Reset/power sequence and is not authorized here. |
| Stock SSH/telnet/developer mode | Existing OEM analysis found locked root credentials, guest/visit shells set to false, telnet disabled, and no documented developer mode. Undocumented factory hooks are excluded. | No supported arbitrary program/kernel execution interface identified. |
| Other-device web-flash precedents | RE700X and MR80X mechanisms differ in their flasher/signature implementation. | Not evidence for AX23 V2. |

OEM GPL source and static OEM firmware analysis strongly support the designed paths, but this unit's running U-Boot build, fuse/policy state, environment and prompt behavior have not been observed. TP-Link's official V2 support page lists stock firmware and normal local updates, not a third-party RAM boot or developer mode ([official AX23 V2 support page](https://www.tp-link.com/uk/support/download/archer-ax23/v2/), [AX23 V2 user guide](https://static.tp-link.com/upload/manual/2025/202503/20250310/1910013875_Archer%20AX23_2.0%20UG_REV2.0.0.pdf)).

### New community evidence and its limits

The current Sply-Dev public README reports a v0.4-3 physical AX23 V2 RAM boot through U-Boot/TFTP, a 2.5 Gbps switch link, LAN forwarding and router-originated WAN connectivity. This supports that serial/TFTP and much of the Ethernet path have worked on at least one community unit. It is not UART-free and does not validate this project's image or this owner's EU unit. The same README says Wi-Fi is unvalidated and board-data fetching fails with `-12`. Its current `docs/TESTING.md` still says no functional physical boot has been demonstrated, while `docs/HARDWARE.md` labels GPIO39 as switch reset; this conflicts with the README status and this project's OEM U-Boot/switch-driver analysis identifying GPIO26. Treat the positive hardware claims as reported community results, not a substitute for raw logs or local tests ([Sply-Dev project](https://github.com/Sply-Dev/openwrt-archer-ax23-v2/), [README](https://github.com/Sply-Dev/openwrt-archer-ax23-v2/blob/main/README.md), [testing status](https://github.com/Sply-Dev/openwrt-archer-ax23-v2/blob/main/docs/TESTING.md), [hardware notes](https://github.com/Sply-Dev/openwrt-archer-ax23-v2/blob/main/docs/HARDWARE.md)).

## 2. Ethernet-only tests and what they prove

None of these tests was run against the router. Every physical test requires the owner's explicit approval for that specific action.

| Test | Requirements / evidence | Risk or state change | Loads OpenWrt? / approval |
|---|---|---|---|
| Read stock status in authenticated TP-Link UI | Existing LAN; record exact model, hardware/region and firmware version. | Read-only if no controls are activated. | No; proves identity/version only. Owner approval to open status pages. |
| Observe normal stock traffic | Wireshark on selected wired NIC during an owner-scheduled ordinary stock boot; record ARP/DHCP/TFTP/HTTP if present. | Power cycle interrupts service; capture may include private identifiers. | No. No packet does not prove protocol impossibility; OEM source predicts no TFTP request. Owner approval for capture and power cycle. |
| View stock recovery page without upload | Requires separately approved reset-held recovery test and statically addressed PC; view page then close without selecting/uploading. | Button/power sequence changes boot mode and interrupts service; source analysis says no flash write unless an image is submitted. | No; stock recovery only. Owner approval for exact button/power sequence. Not part of initial passive checks. |
| PC-only TFTP staging smoke | Windows Tftpd64 bound to dedicated isolated NIC; TFTP only, one-file root; GET to temporary file; compare size/hash. | Temporary host process/file, no router state. Firewall/NIC reconfiguration excluded absent approval. | No; tests host transport/file only. Approval to start temporary server if not already tested. |
| Watch for unsolicited U-Boot RRQ | Packet capture during separately approved ordinary boot; correct physical port/path required. An RRQ shows a request, not FIT acceptance. | Power cycle interrupts service; capture only. | No proof of usable boot. Owner approval for exact capture/boot. Do not induce recovery or upload. |
| Stock LAN link/ping | Existing stock connection and known address. | Read-only traffic. | No; confirms normal stock connectivity only. Owner approval to connect/test. |

Do not use the stock firmware-update form as a compatibility probe. Do not upload the ITB to the normal updater or recovery service. No aggressive scan, credential attempt, reset/WPS action, or update/rollback request is part of this plan.

### Windows 11 / WSL2 TFTP arrangement

For a later approved host-only smoke, prefer Windows-native Tftpd64 bound to the chosen physical Ethernet adapter. WSL2 NAT reachability from a directly connected router is not established; the previous WSL loopback TFTP test exercised only the local harness. Do not use the Raspberry Pi, which runs important services.

After approval for the PC-only smoke: use a dedicated spare Ethernet adapter if available; isolate it from other networks; set a temporary host address only after checking conflicts; disable Tftpd64 DHCP; select the intended NIC explicitly; serve only the validated ITB; perform a local TFTP GET and compare byte count/SHA256; stop Tftpd64. Do not change Windows firewall, routes, other NICs, Wi-Fi, WSL, Pi services or router settings here. Later U-Boot addresses and `bdinfo` must come from the exact console; sample addresses in older notes are not observations for this unit.


### Read-only PC-side readiness snapshot (2026-11-22)

Windows staging file `C:\Users\jfits\Documents\AX23-TFTP-fa4783\openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb` exists at 13,330,704 bytes and its independently recomputed SHA256 matches the WSL artifact. `C:\Program Files\Tftpd64\tftpd64.exe` exists. Windows `tftp.exe`, Wireshark and tshark were not found in the current command search, so the prior WSL loopback TFTP smoke is the only local transport test; no Windows Tftpd64 transfer has been tested. The physical Wi-Fi and Intel Ethernet adapters both currently report Up; Ethernet link speed is 100 Mbps. Their current network use was not changed or inferred. Do not repurpose the active NIC; use a dedicated spare adapter and owner-approved isolation.

## 3. Existing image and offline evidence

| Check | Result |
|---|---|
| Artifact | Symlink `artifacts/ram-only/dev/openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb` resolves into the preserved original build tree. |
| Size / SHA256 | **13,330,704 bytes**; `6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff` (recomputed now; byte-identical to the recorded build). |
| FIT | Re-ran `tools/fit-verify.py`: kernel and DTB CRC32/SHA1 pass; `config@mp02.1` exists. `dumpimage -l` reports AX23 V2 description, Linux 6.18.55 AArch64 LZMA kernel, load/entry `0x41000000`, kernel payload 13,302,700 bytes, selected DTB payload 26,591 bytes. |
| DTB | Extracted selected DTB is 26,591 bytes and identifies `tplink,archer-ax23-v2`. Memory node is `reg=<0x40000000, 0>` (bootloader-populated size), so actual DRAM size is not determined offline. Reserved memory begins at `0x4a400000`. |
| Address extents | Prior validator computed decompressed kernel `[0x41000000,0x42676008)` and proposed FIT staging `[0x44000000,0x44cb6910)`: no mutual overlap and the FIT ends below the first declared reserved-memory base. This does not prove safety against U-Boot relocation/LMB/work regions, firmware reservations or physical DRAM bounds. Exact `bdinfo` is mandatory before transfer/`bootm`. |
| Build provenance | `reports/build-manifest.json`: firmware source `8673c2e6a001fce6271d11700bfa1d27dc51edc9`; prepared OpenWrt tree `d0e975060d5c71565e0a62abbddf48ef1312478c`; Linux 6.18.55; backports 7.2; patches 0001–0027 recorded applied; initramfs FIT `config@mp02.1`; EU board-data payloads were local build inputs. No rebuild here. |
| Compiled patches | Manifest records compiled object evidence for 0026 in `qcom_q6v5_mpd.o` and 0027 in ath11k `dp.o`; prior artifact validator recorded 77 PASS, 1 INFO, 0 FAIL. |
| Ethernet | Default image is 2.5 Gbps HSGMII. Optional `patches/variants/trunk-1g-sgmii.patch` is outside the default series. No physical frame transfer has been demonstrated for this local image. |
| NAND | Prior offline validator checked 16 DT partitions read-only, MTD configuration restrictions, no implicit UBI attach path and sysupgrade interlock. These establish build intent, not live MTD/UBI flags. No write test/router access occurred. |
| Radio | Manifest records IPQ5018/QCN6122 startup files and EU-scoped board data; expected identities 36/255 and 96/255. This does not prove this unit's calibration is accepted or either radio operates. Community report also leaves Wi-Fi unvalidated. |

### GPIO 26/39 gate

The compiled selected DTB names GPIO39 as active-low `reset-gpios`. The reviewed Realtek driver requests that descriptor as an output, asserts logical reset (physical low) for 25 ms, releases it high, waits 100 ms and retains the GPIO request. OEM GPL U-Boot and OEM switch-driver analysis identify GPIO26 as RTL8367 reset. The Sply-Dev hardware page's GPIO39 claim conflicts with those sources and is not accompanied here by a directly inspected measurement for this EU unit. Neither source set proves GPIO39 is electrically harmless on this PCB. Do not change the production DTS or drive either line.

Before any RAM boot, require unpowered, board-ground-referenced high-impedance continuity mapping of switch `nRESET` to GPIO26/GPIO39, or an approved high-impedance waveform observation during ordinary stock boot. Determine polarity, voltage and any shared load. If GPIO39 is tied to reset, another control, or an unknown net, **STOP**; this image may affect it during kernel probe. This is a pre-boot gate, not a post-boot diagnostic.

## 4. UART and first RAM boot prerequisites

JP1 pin order and voltage are not measured on the owner's AX23. GPIO28/29 and 1.8 V are reported references only. Before wiring: with router unpowered, identify ground by continuity to a known board ground; measure candidate TX idle voltage with a high-impedance meter/scope; verify adapter signal I/O level from its schematic and measured TX waveform (selectable VCC alone proves nothing); then connect only router TX -> adapter RX and common ground. Leave adapter TX and all VCC/VREF disconnected. Initial terminal: 115200, 8 data bits, no parity, 1 stop bit, no flow control. Connect adapter TX to router RX only after pin and logic limits are established. Never connect router VCC to adapter or drive an unverified 1.8 V input with 3.3 V.

First `bootm` is not ready today. Before it, require: exact EU V2.0/PCB identity and known stock recovery; UART pin/level checks; GPIO26/39 resolution; exact U-Boot build and `help`/`bdinfo`/bootargs/bootdelay and FIT acceptance observations; actual DRAM and relocation map with no overlap; isolated host TFTP smoke and confirmed U-Boot network settings; temporary `setenv` only, never `saveenv`; verified `init=/bin/sh` pass-through; then check RAM root and live MTD/UBI read-only state before `/sbin/init` or Wi-Fi.

On any pre-`bootm` failure, stop at U-Boot without persistent changes. If the kernel starts but unexpected flash/GPIO behavior, panic or missing early shell occurs, do not run `/sbin/init` or flash commands. Preserve the private UART log and seek review; do not improvise recovery uploads. Never use the OEM updater for this ITB.

## 5. Gaps and test results

### Tests run now

- **PASS:** local ITB size/hash recomputed; matches the recorded artifact.
- **PASS:** FIT kernel/DTB CRC32/SHA1 and `config@mp02.1` checked by `fit-verify.py`; `dumpimage -l` confirms component metadata.
- **PASS:** synthetic `tests/unit/test_bdf_extract.sh` using the existing project-local `ubireader_extract_images`, `ubinize` and squashfs tools: 8 checks passed. Random synthetic data only, not OEM calibration.
- **PASS:** synthetic self-diagnostic region parser: 4 checks passed.
- **SKIP:** two factory EU BDF region comparisons: raw `bdwlan.b24`/`bdwlan.b60` fixtures were not found in searched checkout/build paths or expected private fixture location. Do not publish or create outputs from private calibration for this test. Embedded EU board payload is not an independent OEM fixture.
- **SKIP (not relevant to this artifact):** historical baseline-DTB comparison. No baseline DTB exists; building an old image would not validate the current FIT.
- **NOT RUN:** full artifact validator/test runner in this task; its wrapper recreates `build/validate-dev`, which was preserved. Previously recorded applicable results remain 77 PASS / 1 INFO / 0 FAIL, 14 unit suites PASS, 53 current-DTB static checks PASS, with private-fixture and baseline skips.
- **NOT RUN:** Windows Tftpd64, packet capture, stock UI/recovery, UART, router boot, QEMU or any hardware test.

### Findings by priority

| Priority | Finding | Status/action |
|---|---|---|
| P1 | Stock autoboot has no supported OpenWrt Ethernet RAM boot; a PC TFTP server cannot initiate it. | Source review closes candidate. Use serial U-Boot prompt; no signature bypass/undocumented interfaces. |
| P1 | Image drives GPIO39 at switch probe while OEM analysis points to GPIO26 and current community docs claim GPIO39. | Unresolved physical safety gate. No DTS/image change; map/measure passively first. |
| P1 | This unit's U-Boot memory map, FIT policy and command-line behavior are unknown. | Observe exact console before transfer/`bootm`. |
| P2 | Local-image Ethernet and both radios remain untested; community evidence is not local validation and their Wi-Fi report remains negative/unvalidated. | Requires staged physical acceptance after safety gates; no daily-use claim. |
| P2 | Runtime NAND/UBI flags are unmeasured. | Read state in early shell before normal init; no write probe. |

No verified executable-code defect was found. No firmware source, DTS, patch, config or artifact changed, so no rebuild is needed. Older reset-held recovery procedures in the UART-free investigation and NAND feasibility reports are historical source guidance, not authorization to press Reset or enter that mode; any physical test needs separate explicit approval.

## 6. Recommendation and verdict

The highest-value next step is obtaining a 1.8 V-safe USB-UART adapter and, after specific owner approval, a receive-only stock-console measurement/logging session. First identify JP1 ground, measure signal levels and verify adapter compatibility. This yields exact-unit evidence about bootloader, stock boot and network behavior without uploading or writing firmware. Resolve GPIO26/39 passively before allowing Linux to start.

**Current verdict: NO-GO for the first `bootm`.** The software artifact is offline-validated, but UART electrical/pin checks, GPIO safety and exact U-Boot memory/acceptance remain unverified. Once those gates pass, a RAM boot may be considered conditionally; this is not a claim of full hardware compatibility or daily-use stability.
