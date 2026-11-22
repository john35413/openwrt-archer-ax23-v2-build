# Hardware acceptance plan: Archer AX23 EU v2.0 (RAM boot only)

**Status: BLOCKED pending the physical and U-Boot gates.** This plan does not
authorize a boot by itself. Complete [`FINAL_PREBOOT_GATE.md`](../../reports/FINAL_PREBOOT_GATE.md)
in order. A failed or unknown prerequisite means STOP before `bootm`.

The firmware is an experimental RAM-only development image. Do not use the
stock web firmware updater, do not flash, and do not attempt persistent install.
No physical AX23 validation has been performed. Do not press Reset/WPS during
initial safety checks. Never run `saveenv`, flash/erase/UBI write commands, or
signature bypasses.

## 0. Prerequisites and safety gates

| Gate | Required evidence before proceeding |
|---|---|
| Exact unit | Chassis and PCB labels identify Archer AX23 EU V2.0. Stop on a revision/region mismatch. |
| Stock recovery | Owner confirms ordinary stock boot/recovery remains available without uploading, resetting, or writing anything. Verify normal stock boot before any RAM test; do not press buttons for this check. |
| UART | JP1 pin identities and voltage measured on this unit. GPIO28/GPIO29 and 1.8 V claims are unverified references, not wiring instructions. Begin receive-only, common GND + router TX to adapter RX only. |
| GPIO | Passively establish GPIO26/39 and RTL8367S-VB `nRESET` relationship before Linux is allowed to probe. Current DTS makes the kernel drive GPIO39; see `reports/rtl8367-reset-trace.md`. Unknown connection or waveform = STOP. |
| Bootloader | Observe exact U-Boot version, `help`, `printenv`, `bdinfo`, boot delay, bootargs, DRAM map, FIT/hash policy and load/relocation behavior. Unknown or inadequate memory map = STOP. No signature bypass. |
| Image | Independently recompute the staged ITB size/hash and verify local FIT metadata as documented in `reports/FINAL_PREBOOT_GATE.md`. The intended config is the FIT default `config@mp02.1`. |
| TFTP | Use a Windows-native TFTP server bound only to a dedicated physical Ethernet interface on an isolated direct link, or an explicitly reviewed equivalent. WSL2 default NAT is not assumed reachable. Do not change firewall, interface, or router network configuration without owner approval. |

`setenv` changes only the current volatile U-Boot environment unless `saveenv`
is issued. `saveenv` is prohibited. Use the temporary `rdinit=/bin/sh` first
kernel boot gate in `reports/first-ram-boot-checklist.md`; do not start normal
OpenWrt userspace/Wi-Fi until the early shell checks pass.

The current image already includes verified EU radio board data. Do not extract
board data from the router or rebuild after this RAM boot. Factory ART
calibration is a distinct read-only runtime input and remains unverified on the
physical unit.

## 1. Staged RAM boot (only after every gate passes)

1. Keep the router isolated from household/WAN networks; connect the PC's
   selected dedicated Ethernet interface to the chosen router LAN port.
2. At the observed U-Boot prompt, record `version`, `printenv`, `bdinfo`,
   `help bootm`, and the actual FIT verification policy. Confirm the actual
   DRAM map safely contains the proposed transfer region and the kernel / all
   bootm relocation regions. Stop if the bootloader's memory use overlaps.
3. Verify existing `bootargs`. Append `rdinit=/bin/sh` using temporary `setenv`
   syntax confirmed for this prompt, then `printenv bootargs` to verify. Keep
   all existing console tokens; do not guess or delete tokens. If this cannot
   be safely constructed, STOP before transfer.
4. Set temporary `serverip` and `ipaddr` only for the isolated network. Run
   `tftpboot 0x44000000 openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb`.
   Verify successful transfer and the reported byte count is exactly
   13,330,704. Do not assume the sample IPs in older notes are safe for this LAN.
5. `bootm 0x44000000` selects the FIT's verified default `config@mp02.1`.
   Proceed only if the actual bootloader accepts the image/hash without bypass.
   Do not add `#config@mp02.1` syntax unless that exact U-Boot supports it.
6. Capture complete UART output to a private local file. Expect the /bin/sh selected by rdinit, not /init or normal OpenWrt startup. Check RAM root, all 16 MTD partitions
   `writeable=no`, and all attached UBI devices read-only. Do not attempt a test
   write. If unexpected storage or GPIO activity appears, remain at the shell,
   do not run `/init` or `/sbin/init`, and collect the UART evidence. Do not issue flash
   commands. If the expected shell is not reached, /init or normal services start, or
   the console is ambiguous, STOP immediately. Do not run `exec /init`,
   `/sbin/init`, Wi-Fi tests or any continuation command.
7. Only after the early checks pass, an owner may approve `exec /init` to perform
   the image's initramfs `switch_root` sequence and start `/sbin/init` (procd)
   and normal OpenWrt services. Confirm Linux networking and SSH access before
   any streamed diagnostics. The PC must stream `tests/hardware/ax23-selfdiag.sh`
   from this source checkout; diagnostics are not embedded in the firmware.

At any pre-`bootm` failure, stop at the U-Boot prompt without changing persistent
state. After kernel start, do not issue further boot commands or storage writes;
preserve the log. Do not power-cycle while any flash activity is observed.
After activity has ceased, stock recovery behavior is still a physical
observation, not an assumption.

## 2. Acceptance tests (after the gated early shell and owner-approved startup)

Record each result **PASS / FAIL / BLOCKED / NOT TESTED** with time-stamped
evidence. A command that did not run is not a PASS. Verify network access and
SSH before every remote command. Keep raw logs private; redact identifiers and
keys before sharing.

| # | Test | Pass evidence |
|---|---|---|
| HW-01 | Linux boot | UART reaches early shell then, only after approval, normal init; no panic/oops. |
| HW-02 | State snapshot | Read-only self-diagnostic and router snapshot after IP connectivity and SSH are confirmed. |
| HW-03 | Switch and trunk | RTL8367S-VB probe; 2.5 Gbps full duplex; fresh bidirectional frames and counters, not carrier alone. |
| HW-04 | LAN 1–4 | Link and DHCP on each port; no reset/WPS button use. |
| HW-05 | LAN switching | Two clients; record TCP throughput and loss. |
| HW-06 | WAN | Verified WAN connection; DHCP and controlled reachability. |
| HW-07 | DHCP/DNS/NAT | Lease, DNS and routed traffic, with firewall enabled. |
| HW-08 | Load/latency | RTT and loss before/during traffic. |
| HW-09 | Trunk gap | Ten-minute fresh traffic/counter run; no unexplained periodic drops. |
| HW-10 | IPv6 | Only if ISP provides it; global address and reachability. |
| HW-11 | PPPoE | Only if the ISP uses PPPoE. |
| HW-12 | Radios/BDF | Two PHYs, expected EU identities, firmware/BDF acceptance and regulatory state. Image already has the EU board data. |
| HW-13 | AP and channels | Correct EU country set by supported OpenWrt configuration; expected channels and beacons. |
| HW-14 | WPA2/WPA3 | Association and traffic on both bands. |
| HW-15 | Wi-Fi networking | DHCP, DNS, Internet/LAN traffic on each radio. |
| HW-16 | Wi-Fi performance | Record throughput; no performance claim without measurements. |
| HW-17 | Reconnect stability | Reconnect test after initial stability; no ath11k errors/recovery loops. |
| HW-18 | LEDs | Observe PHY-to-LED mapping; do not infer radio identity from LEDs alone. |
| HW-19 | Buttons | **Deferred**; do not press Reset/WPS during initial acceptance. Later test only with recovery procedure and explicit owner approval. |
| HW-20 | MAC addresses | Compare reported interfaces with label; keep identifiers private. |
| HW-21 | Watchdog/thermal | Record readings and plausibility; no overheating. |
| HW-22 | VLAN isolation | Apply guest/IoT test config only after baseline; verify isolation and firewall. |
| HW-23 | Memory | Record `MemAvailable`, buddyinfo and OOM logs at idle and load. |
| HW-24/25 | Soak | 24/48-hour stability only after earlier gates pass; monitor traffic, memory and errors. |
| HW-26 | Reboot stability | Repeated controlled boots only after first boot/recovery pass. Never persist environment changes. |
| HW-27 | Stock recovery | Confirm normal stock boot after RAM test; do not infer from no-write source analysis alone. |
| HW-28 | WAN interruption | Controlled WAN reconnect observation after stable baseline. |

## 3. Reporting

Use `reports/final-validation.md` for measured results. Preserve logs locally;
do not publish raw UART, calibration or device-identifying data. No physical
test is claimed by the source, build, FIT validation or simulations.
