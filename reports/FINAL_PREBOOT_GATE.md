# AX23 EU V2.0 final pre-hardware gate

**Verdict: NO-GO for `bootm` today.** PC-side image and source checks pass, but
passive board checks and actual U-Boot memory/network observations are still
blocked. This is not a general firmware audit or a physical validation claim.
Do not flash, use the stock web updater, write U-Boot environment, or access the
router as part of this preparation.

## 1. PASS — offline checks completed

- Source checkout was on `dev`, fetched `origin/dev` at
  `fa4783b7d8f4600e6e57a0ed471e1f54425a48c1`; no remote update was present at
  the start of this task. No existing semantic user changes were found before
  edits; seven pre-existing CRLF-only working-tree variants were copied to
  `/home/jfits/codex-preboot-preserved/fa4783/` with hashes before restoring the
  text-identical tracked forms.
- The prepared OpenWrt build manifest records the exact AX23 target, 27 applied
  patches, Linux 6.18.55, backports 7.2, both EU board-data sets, kernel patch
  0026, ath11k patch 0027, and the default 2.5 Gbps HSGMII trunk. No rebuild was
  performed in this task.
- Artifact path (local symlink):
  `/home/jfits/openwrt-archer-ax23-build/artifacts/ram-only/dev/openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb`.
  Resolved file is in the preserved old local build tree. Verified size is
  **13,330,704 bytes**; SHA256 is
  `6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff`.
- FIT inspection: default configuration `config@mp02.1`; AX23 v2 board DTB;
  Linux 6.18.55 AArch64 LZMA kernel; load/entry `0x41000000`; kernel payload
  13,302,700 bytes; DTB 26,591 bytes; CRC32 and SHA1 nodes validate. The
  initramfs is embedded in the kernel. `fit-verify.py` passed all FIT hashes,
  selected configuration and its offline extent checks. The FIT contains hash
  nodes, not a FIT signature claim.
- Offline address arithmetic: decompressed kernel extent is
  `[0x41000000, 0x42676008)` (23,552,008 bytes); TFTP FIT buffer at the planned
  `0x44000000` would occupy `[0x44000000, 0x44cb6910)` (13,330,704 bytes).
  Those ranges do not overlap and the FIT buffer ends below the first shown
  reserved region at `0x4a400000`. The built DTB's `/memory@40000000/reg` has
  zero size with a source comment expecting the bootloader to fill it. FIT
  relocation, working-FDT placement, U-Boot LMB reservations, and actual usable
  DRAM size are **not** established by this arithmetic; `bdinfo` and the exact
  bootloader's output are mandatory. Do not treat the validator's 48 MiB
  extent bound as a U-Boot relocation guarantee.
- Re-ran artifact validator: **77 checks PASS, 1 INFO, 0 FAIL** (three helper
  stdout PASS lines are not independent checks). It confirms target/FIT, all 16
  read-only partitions, EU board data and radio startup files, MTD configuration,
  compiled 0026/0027 evidence, and HSGMII default. Static suite: **PASS**, 53
  current DTB checks; baseline DTB comparison **SKIP**, because no baseline DTB
  was built and it is not needed to verify this current image.
- Unit tests: **14 suites PASS**, including synthetic UBI extraction using the
  existing private local `build/bdf-venv` tool, MPD recovery, DMA allocation,
  board-data extraction, calibration preservation, MAC, radio profiles,
  read-only diagnostics, OTP identities, ART region parsing, cleanup guard and
  SGMII variant. The two EU ART-region comparison subchecks remain **SKIP**:
  the private stock `bdwlan` fixture is not present at the test's expected local
  path; no fixture was copied or exposed. The tests use synthetic data for the
  other cases. No QEMU or hardware test ran.
- Local TFTP staging copy:
  `C:\Users\jfits\Documents\AX23-TFTP-fa4783\openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb`.
  The directory contains only this ITB; the copied size/hash match the WSL
  artifact. Windows has Tftpd64 at `C:\Program Files\Tftpd64\tftpd64.exe`.
  The read-only adapter snapshot showed Wi-Fi up, Intel Ethernet up at 100 Mbps,
  WSL virtual Ethernet up, and no present VirtualBox host-only link. The Intel
  NIC is currently active; do not repurpose it until its present network is
  identified and disconnected by the owner. A spare USB Ethernet adapter is
  the cleanest isolated-link option.
  A temporary TFTP RRQ/DATA/ACK loopback smoke using the staged file passed on
  `127.0.0.1:6970`; transferred 13,330,704 bytes with the expected SHA256 and
  stopped immediately. It used a local test harness, not Windows Tftpd64.
  The Windows Tftpd64 interface-bound GET is still untested; no persistent
  server was started and no Windows network/firewall setting was changed.
  Neither local check proves U-Boot reachability.

The image includes the intended EU board data already. Do not dump ART, extract
board data, or rebuild after boot as an initial prerequisite. ART calibration
is a separate read-only runtime input. The 16 DT partitions are marked
read-only, whole-chip master and command-line repartitioning are disabled,
UBI attachment should be read-only, and sysupgrade is blocked by source/build
evidence; live running-kernel MTD/UBI flags still need observation before any
optional read-only backup. Never test writability by attempting a write.

## 2. BLOCKED — passive hardware checks still needed

No physical measurements have been made on this AX23. Use a meter/probe with
high input impedance; never inject a signal into either GPIO.

### UART electrical and wiring check

JP1 and GPIO28/GPIO29 are references only; their pin order and 1.8 V levels are
unverified on this unit.

1. With router power disconnected, identify GND by continuity to a known board
   ground plane/shield point. Verify the candidate header contact is ground;
   do not infer it from pin order or a photo.
2. Leave the USB-UART adapter disconnected. Power the stock router normally and
   measure candidate TX idle voltage with a high-impedance DC meter referenced
   to the verified ground. Use a high-impedance scope/logic analyzer to identify
   boot activity if needed. Record idle/high level and any overshoot/negative
   excursion against the router IO specification; a meter alone cannot verify
   fast transients.
3. Verify the adapter's **signal I/O** voltage from its schematic/datasheet and
   actual TX waveform. A selectable 1.8 V power/VCC output does not prove TX
   logic is 1.8 V. With the adapter disconnected from the router, test TX idle
   and data levels using an appropriate high-impedance instrument. Confirm its
   input thresholds accept the measured router TX level.
4. First connection is receive-only: adapter GND to confirmed router GND and
   router TX to adapter RX. Leave adapter TX and all VCC/VREF pins disconnected.
   Use 115200 baud, 8 data bits, no parity, 1 stop bit, no flow control.
5. Connect adapter TX to router RX only after the actual RX pin and both sides'
   logic-level limits are independently confirmed. Never connect 3.3 V UART
   output to an unverified 1.8 V input. Never connect router VCC to adapter VCC:
   it can back-power the router rail or cause contention; the router is powered
   normally and signal ground is the only reference needed.

**UART STOP:** unknown ground/pin, non-stable or out-of-spec level, adapter
logic not proven compatible, any 3.3 V signal, negative/overshoot beyond the
device limits, unexpected back-power, heating, or inability to isolate adapter
TX. Do not connect TX or attempt a console command until these pass.

### GPIO 26/39 passive check

OEM U-Boot and OEM switch-kernel evidence identify GPIO26 as the RTL8367 reset;
GPIO39 was associated with the OEM QCA8337 path. This does not prove GPIO39 is
unconnected or safe on the physical PCB. The current image's DTS names GPIO39
as an active-low reset. The actual compiled common Realtek driver requests it
as an output, asserts it physically low for **25 ms**, then releases it high,
waits **100 ms**, and retains the GPIO request. Do not rely on the prior claim
that GPIO39 is a no-op. No production DTS change was made and the validated
image is unchanged.

Before any RAM boot, with router unpowered, use board documentation and a
high-impedance continuity method to map RTL8367 `nRESET` to GPIO26 and GPIO39.
If continuity cannot be performed safely, use a high-impedance scope on the
identified `nRESET` and candidate nets during an ordinary stock cold boot; do
not drive either net. Record polarity, levels, pulse widths and whether GPIO39
is shared with another circuit. Do not press buttons. If GPIO39 is tied to
`nRESET`, another reset, an unknown signal, or a line whose voltage/polarity is
not established safe for the SoC and switch, **STOP: do not boot this image**.
S2.8 diagnostics run only after Linux has already driven GPIO39 and cannot
substitute for this gate. Any future DTS correction requires a separate review
and firmware rebuild; it is not authorized here.

Also record the exact board/PCB revision and stock Wi-Fi baseline (band,
channel, country, client RSSI at a fixed location) before changing router state.
Confirm an ordinary stock boot and a recovery path that requires no upload or
write. Do not press Reset/WPS for the initial checks.

## 3. BLOCKED — U-Boot console observations still needed

After UART and passive checks pass, but before TFTP or `bootm`, use receive-only
logging first. At a naturally available stock U-Boot prompt, observe and record:

- Exact U-Boot version/build and prompt; `help`, `help bootm`, and availability
  of `bdinfo`, `tftpboot`, `bootm`, and `setenv`.
- `bdinfo` DRAM base/size and bootloader relocation/reservation details. The
  actual DRAM size must cover the FIT load, decompressed kernel, FIT-selected
  DTB and U-Boot's relocation/work regions without overlap. Stop if the memory
  map is absent or ambiguous.
- `printenv bootargs bootcmd bootdelay ipaddr serverip`; record original values
  before temporary changes. Inspect the command line; DTS appends
  `root=/dev/ubiblock0_1 coherent_pool=2M`. Do not assume environment or bootargs
  from other AX23 units.
- Whether this exact U-Boot has the ordinary `bootm` path and does not require a
  signature bypass for manual RAM boot. The FIT has default configuration
  `config@mp02.1`; `bootm 0x44000000` selects that default according to FIT
  metadata. `bootm` performs FIT hash checks before transferring control to the
  kernel; if it reports any hash, configuration or authentication error, leave
  the prompt and stop. Never bypass security.
- Whether U-Boot will pass a temporary `init=/bin/sh` argument. At the prompt,
  preserve/record the full original `bootargs`; only append the early-shell
  argument using syntax confirmed for that build, then print it back. Do not
  remove existing console tokens by guesswork. `setenv` is a volatile change;
  `saveenv` is forbidden. The early shell stops normal init/procd (and therefore
  normal userspace radio startup), but cannot prevent built-in kernel probes,
  the possible GPIO39 pulse, or kernel UBI attach. Passive GPIO gate remains
  required first.
- TFTP reachability from U-Boot to the selected physical interface. Do not infer
  it from a Windows-to-WSL transfer or a local server test.

Before loading, verify the staged ITB's Windows SHA256 again. Use an isolated
direct Ethernet segment only. Example addressing is allowed only if the
selected interface is physically disconnected from other networks and no
address conflict exists: Windows host `192.168.1.10/24`, no gateway or DNS;
U-Boot/router `192.168.1.1/24`. Select only the dedicated Ethernet interface in
Tftpd64; serve only the staging directory and only the named ITB. First perform
a local TFTP GET from that server to a temporary file on the same PC and compare
hashes; stop the server after the smoke test. A local smoke test does not prove
U-Boot reachability.

Example U-Boot commands, **only after** the actual prompt, network isolation,
addresses and memory map are verified:

```text
printenv bootargs
setenv bootargs "${bootargs} init=/bin/sh"
printenv bootargs
setenv serverip 192.168.1.10
setenv ipaddr 192.168.1.1
setenv netmask 255.255.255.0
tftpboot 0x44000000 openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb
bootm 0x44000000
```

Use the `setenv bootargs` line only if this exact U-Boot supports the shown
expansion/quoting and the printed result retains all existing tokens. Do not
issue `bootm` if it does not. The example IPs are not a claim about the unit's
saved environment or the host's current networks. Never issue `saveenv`.

Windows 11 WSL2 is normally NAT-connected; its WSL address is not automatically
reachable from a router on the physical LAN, and ordinary TCP `portproxy` is not
a TFTP solution. Prefer Windows-native Tftpd64 bound to a dedicated physical
adapter. A separate USB Ethernet adapter is safest if the built-in Ethernet is
currently in use. Do not alter the firewall, adapter address, current networks,
Pi services or Tailscale/Docker configuration in this preparation. If a narrow
firewall allowance or temporary NIC reconfiguration is required, owner approval
is needed. References: [Microsoft WSL networking](https://learn.microsoft.com/en-us/windows/wsl/networking),
[Tftpd64 interface selection](https://github.com/PJO2/tftpd64/wiki/Tftpd64-setup).
A Raspberry Pi 4 with its own dedicated USB-Ethernet link can also serve TFTP,
but adds setup and could affect existing Pi services; it is a fallback only if
the PC cannot provide an isolated interface. No Pi service was changed.

Only after all previous gates pass may an owner-approved operator use temporary
`setenv`, TFTP the exact byte count to `0x44000000`, and issue
`bootm 0x44000000`. U-Boot must report successful FIT hash/config checks before
control is handed to the kernel; a failure aborts the boot and is a STOP. Do not
run `saveenv`. Stop on any transfer, size, FIT, signature, memory-map or
bootargs surprise.

After the kernel enters the guarded shell, inspect serial output first. If
`/proc` or `/sys` is not mounted, mount only those pseudo-filesystems read-only
(`mount -t proc -o ro proc /proc`; `mount -t sysfs -o ro sysfs /sys`). Read
`/proc/cmdline`, `/proc/mounts`, `/proc/mtd`, and confirm `/` is the RAM initramfs
root with no overlay. Read each
`/sys/class/mtd/mtdN/flags` and every attached UBI's backing MTD flag. The
`MTD_WRITEABLE` bit is `0x400`; it must be clear on exactly 16 MTD partitions
and on every attached UBI backing MTD. Read UBI `ro_mode` where exposed. Review
`dmesg` for unexpected NAND/UBI write activity. If a flag is missing, writable,
or cannot be read, stop at the shell; do not start `/sbin/init` or test writes.

## 4. NOT TESTED — OpenWrt runtime functionality

No router has been accessed, booted, reset, flashed or modified. The following
remain **NOT TESTED ON OUR PHYSICAL AX23**: early shell argument behavior;
live RAM root and MTD/UBI read-only flags; absence of flash writes; GPIO reset
electrical behavior; switch probe and real bidirectional Ethernet traffic;
radio/OTP/BDF/regulatory acceptance; actual RF output; DHCP/DNS/firewall/NAT;
Q6 crash recovery; memory pressure; thermals; stock recovery after RAM boot;
and long-term/cold-boot reliability. Configure no radio or network test until
the early-shell storage checks pass and the owner deliberately continues with
`/sbin/init`.

Diagnostics are streamed from the PC after Linux networking and SSH have each
been verified; they are not embedded in the FIT. Never assume the router has
booted, is reachable, or accepts SSH. Raw factory calibration and identity data
must remain private; diagnostic measurements distinguish configured power,
driver-reported power, emitted RF power, and client RSSI.

## Exact ordered operator checklist

| Order | Action and observation | PASS evidence | STOP criterion | Device state change? | Approval needed? |
|---|---|---|---|---|---|
| 1 | Read labels; confirm stock recovery path without upload/reset; record current stock Wi-Fi RSSI baseline. | Exact EU V2.0 labels, normal stock boot/recovery path understood, dated baseline. | Revision mismatch or recovery unknown. | No configuration change; observation only. | Owner must approve any stock reboot needed to observe. |
| 2 | Power disconnected: verify ground/header candidates; inspect adapter data sheet/actual logic levels with adapter isolated. | Ground and adapter I/O limits established. | Unknown pin/GND or any incompatible output. | No router state change. | No, provided router remains unpowered. |
| 3 | Powered stock measurement with high-impedance instruments: identify TX idle/activity and measure voltage. | Signal within confirmed router and adapter RX limits. | Out-of-spec, unstable or unknown level. | Stock router powered, no configuration change. | Owner approval to power/open unit and probe. |
| 4 | Passive GPIO measurement: continuity while unpowered and/or high-impedance stock waveform; map 26, 39, switch `nRESET`. | GPIO39 proven electrically safe for the current image's low/high output, with 26/39 relationship recorded. | Any unknown/shared/unsafe line; inability to establish safe voltage/polarity. | No driven GPIO; unpowered continuity or passive observation only. | Owner approval to open/probe; never drive. |
| 5 | Receive-only UART: verified GND and router TX -> adapter RX; 115200 8N1; cold-start stock once if approved. Do not connect adapter TX. | Clean serial capture and actual U-Boot identity/prompt observed. | Electrical anomalies, no reliable prompt, unsafe voltage. | Power cycle only; no env change. | Yes, for power cycle/opening. |
| 6 | At U-Boot, record version/help/env/bdinfo/bootargs; inspect memory, bootm/security path, and temporary early-shell support. | Sufficient non-overlapping DRAM/LMB regions, generic bootm path with no bypass, valid temporary `init=/bin/sh` command. FIT hashes are checked by bootm before kernel handoff. | Unknown memory map, signature rejection/bypass request, unsupported early shell. | Read-only commands; no writes. | Owner approval to interrupt autoboot/console access. |
| 7 | Prepare isolated Windows Ethernet/Tftpd64; select dedicated NIC only; static host addressing only after approval; local TFTP GET to temp file and SHA compare; stop server. | TFTP GET succeeds; staged and retrieved hashes match; server bound to intended NIC. | Interface shared with other network, address conflict, firewall change needed without approval, hash mismatch. | PC network config/service changes; router untouched. | Yes, for NIC/address/firewall and server start. |
| 8 | Verify staged ITB Windows SHA/size; only after all gates, temporary U-Boot `setenv`; TFTP exact named image to `0x44000000`; verify byte count. | 13,330,704 bytes; U-Boot map confirms buffer safe; no server/network mismatch. | Any prior gate unresolved, wrong bytes/size, transfer error. | Volatile U-Boot env and RAM transfer only. | Yes, explicit owner go-ahead for first RAM boot. |
| 9 | `bootm 0x44000000` selects default `config@mp02.1`; capture UART and stop at early shell. | FIT hash/config accepted before handoff; early shell reached; no panic, unexpected storage/GPIO activity. | FIT/auth failure, memory/relocation warning, normal userspace startup instead of early shell, unexpected writes/GPIO. | Executes kernel from RAM; kernel probes may drive GPIO39 and attach UBI read-only. | Yes, same first-boot approval. |
| 10 | In early shell only, mount `/proc` and `/sys` read-only if not already mounted; inspect RAM root, all 16 MTD flags and attached UBI read-only status; no writes. | All expected read-only facts observed, no flash write indication. | Any writable partition/UBI, unexpected write message, missing early shell. | Mounts pseudo-filesystems read-only; read-only queries. | Owner approval to continue. |
| 11 | Only after step 10 passes, `exec /sbin/init`; then verify Linux IP/SSH before streaming diagnostics. | Normal startup intentionally begins; SSH independently verified before diagnostics. | Unexpected interface, missing protection, radio/GPIO issue. | Starts services and may initialize Wi-Fi. | Yes, owner approval. |
| 12 | Collect read-only diagnostic bundle and perform limited acceptance tests. | Fresh evidence and source revision recorded. | Sensitive output exposure, any write-capable tool requested, instability. | Diagnostics read only; tests may change RAM/runtime config. | Yes for each test that changes config or restarts services. |

### Failure / STOP procedure

- Before `bootm`: leave U-Boot without `saveenv` or storage commands. Preserve
  the UART log and stop; do not retry blindly.
- During/after `bootm`: do not run flash, erase, UBI write, sysupgrade or
  recovery-upload commands. At the early shell, do not execute `/sbin/init` if
  any check is unexpected. Leave the device at the shell while capturing logs;
  only power down after confirming no flash activity is occurring. If that
  cannot be confirmed, keep power stable and seek a hardware review.
- Never press Reset/WPS as a troubleshooting step in these initial stages.
  Never bypass bootloader signature verification. Do not treat silence or
  link-up as a PASS.
