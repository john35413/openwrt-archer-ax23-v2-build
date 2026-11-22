> **Safety/status update (2026-11-22):** This is a historical source investigation, not an operator authorization. Do not press Reset/WPS, enter recovery mode, upload a file, change router settings, or power-cycle the AX23 based on this report alone. The current operator gate is `FINAL_PREBOOT_GATE.md`; the UART-free conclusion and current exact-unit blockers are in `ETHERNET_UART_FREE_FINAL_ASSESSMENT.md`. Any physical test needs the owner's explicit approval for that exact action. Do not use the Raspberry Pi for TFTP; prefer a separately approved, isolated Windows host setup.

# Boot, NAND and recovery feasibility: Archer AX23(EU) v2.0

Updates `nand-boot-safety.md` with TP-Link's **own U-Boot source** (GPL_AX23v2.tar.gz,
sha256 `b2bc4ecb…`, dated 2025-02-27; the U-Boot on the 3P unit reports
"Feb 24 2025, jenkins-Router-Archer_AX23v2-8" — same release window) and the
**official firmware images**. Labels as in `wifi-root-cause.md`. Nothing here was done
to any router.

## 1. Partition and boot flow

```
NAND 128 MiB (ESMT F50D1G41LB, 128 KiB blocks)
0x0000000 0:SBL1 ─┐
0x0080000 0:MIBIB │ Qualcomm boot chain, partition table, TrustZone, DDR config
0x0100000 0:BOOTCONFIG / 0x140000 0:BOOTCONFIG1 (not used for A/B on this board)
0x0180000 0:QSEE  0x280000 0:DEVCFG  0x2c0000 0:CDT
0x0300000 0:APPSBLENV  ← U-Boot env, 256 KiB at offset 0, CRC32, single copy  [STATIC]
0x0380000 0:APPSBL     ← U-Boot (contains HTTP recovery + RSA check)          [STATIC]
0x04c0000 0:ART        ← per-unit RF calibration (0x1000 2.4G, 0x26800 5G)
0x05c0000 0:TRAINING
0x0640000 rootfs   (53.5 MiB) ─ slot 0: UBI { kernel (FIT), ubi_rootfs (squashfs) }  [STATIC: official images]
0x3bc0000 rootfs_1 (53.5 MiB) ─ slot 1: same layout
0x7140000 tp_data  ← UBIFS: default-mac, device-id, pin, product-info, user-config
0x7980000 radio    0x7dc0000 data

Power-on → SBL1 → QSEE → U-Boot (APPSBL)
  U-Boot: env from APPSBLENV (bad CRC on 3P unit → built-in defaults; bootcmd "bootipq"
          is compiled in, autoboot.c falls back to CONFIG_BOOTCOMMAND under CONFIG_TP_IMAGE)
  "Hit any key to stop autoboot: 1"  (bootdelay 1 s under CONFIG_TP_IMAGE)
  bootipq:
   ├─ reset button (GPIO14) held? → "FW GPIO is pressed. Enter firmware recovery mode!"
   │      → U-Boot httpd at 192.168.0.1 (accepts ONLY TP-Link-signed images,
   │        writes slot 0 = rootfs, sets tp_boot_idx=0, saveenv)
   ├─ tp_boot_idx == "1" ? slot 1 (rootfs_1) : slot 0 (rootfs)
   ├─ "ubi part fs && ubi read <addr> kernel" + bootm (FIT config@mp02.1)
   ├─ load fails → try the OTHER slot
   └─ both fail → "Both image corrupted, Enter http firmware recovery mode!" → httpd
```
Sources: `board/qca/arm/common/cmd_bootqca.c: do_bootipq(), check_fw_gpio(), up_file_via_httpd()`,
`include/configs/ipq5018.h` (BOOT_IDX_FLAG "tp_boot_idx", QCA_ROOT_FS_ALT_PART_NAME "rootfs_1",
CONFIG_ENV_SIZE 256 KiB, CONFIG_BOOTDELAY 1), `common/autoboot.c`, `config.mk`
(CONFIG_RESET_KEY=14, CONFIG_UIP_HTTPD, CONFIG_NVRAMMANAGER), `lib/nvrammanager/nm_fwup.c`
(handle_fw_cloud RSA verify, nm_upgradeFwupFile, nm_setBootIdx).

## 2. Recovery-capability matrix

| Method | Needs | Can load OpenWrt? | Can restore stock? | Evidence |
|---|---|---|---|---|
| Stock web UI firmware upgrade | Ethernet | **No** (RSA signature required) | yes | STATIC (signature scheme verified on 4 official images) |
| **U-Boot HTTP recovery (hold reset at power-on)** | Ethernet + reset button, PC at 192.168.0.x | **No** (same RSA check; "Verify sig error!") | **yes** — writes slot 0 | **STATIC only**, not seen on HW |
| U-Boot HTTP recovery after both slots fail to load | Ethernet | No | yes | STATIC |
| U-Boot slot fallback (selected slot fails to load) | — | n/a | yes, if the other slot is intact | STATIC; **does not catch a kernel that loads then crashes** |
| UART + `tftpboot` + `bootm` (RAM boot) | 1.8 V UART, Ethernet, TFTP | **yes (RAM only)** | n/a (NAND untouched) | **3P on HW** (many boots, v0.2-v0.5) |
| UART + U-Boot `nand`/`ubi` commands | UART | yes (persistent) | yes | not attempted; dangerous |
| Ethernet-only TFTP client / RAM boot without UART | — | — | — | **does not exist**: autoboot runs only `bootipq`; `tftpboot` needs the console (1 s window) — STATIC |
| Stock root shell via a vulnerability | Ethernet | possibly | — | **not documented/verified; not used** |

**Which stock image to use for U-Boot recovery (STATIC, important):** `nm_upgradeFwupFile()`
writes the payload as-is after the signature check; `aes.o` is linked but never called from
`nm_fwup.c`, and `nm_api_getOSoffset()` parses a plaintext partition list. So per TP-Link's
source the U-Boot recovery can only restore the **plaintext RSA-1024 images**:
`Archer AX23(EU)_V2_250224` = 1.0.2 (EU) or 1.0.1. The encrypted 1.1.2/1.2.1 images are for
the web UI (which decrypts). After recovering with 1.0.2, update to 1.2.1 from the stock web UI.
Also: the support-list check in U-Boot recovery is commented out (`/*TODO partition,support-list check*/`)
— **it accepts any TP-Link-signed image, so use only the AX23 v2 EU file.** Caveat: the shipped
U-Boot binary cannot be proven identical to the GPL source (dates match: Feb 24 vs Feb 27 2025).

**Answers:**
- *Ethernet-only RAM boot of OpenWrt:* **not possible** on this firmware/bootloader. **STATIC.**
- *UART-free stock recovery:* **exists in TP-Link's source** (reset-held HTTP recovery + both-slots-failed path). Not yet observed on hardware → treat as **UNVERIFIED on HW** until a passive test (below) shows it.
- *UART-free OpenWrt installation:* **not possible** without an exploit; signatures are enforced everywhere (web UI and U-Boot).

## 3. RAM-boot-only test path (requires UART; supported)

1. Equipment (each with its purpose):
   - **USB-UART adapter that supports 1.8 V logic** (or 3.3 V adapter **plus** a bidirectional level shifter) — console to stop autoboot. Never drive the 1.8 V RX pin with 3.3 V.
   - Fine soldering tools / jumper wires — the AX23 v2 header JP1 lacks the level-shifter parts; testers bridged pads or used an off-board shifter (3P).
   - Ethernet cable, PC/Raspberry Pi with a TFTP server (`dnsmasq --enable-tftp` or Tftpd64).
2. At "Hit any key to stop autoboot" (1 s): `setenv serverip <pc>; setenv ipaddr 192.168.1.1; tftpboot 0x44000000 <itb>; bootm 0x44000000`. **No `saveenv`, no `nand`/`ubi`/`sf` writes.**
3. Image: `artifacts/ram-only/dev/…initramfs-uImage.itb` (sha256 in `SHA256SUMS`). Power-cycle → stock boots again from NAND.

## 4. Optional passive test without UART (verifies the recovery path; changes nothing)

PC on LAN with **192.168.0.10/24**, browser/`curl http://192.168.0.1/` ready, `tcpdump -ni eth0` running.
Hold reset, power on, keep holding ~5 s, release. Expected per source: power LED off, **WAN
LED orange** (`set_boot_led(FW_UP_VIA_HTTPD)`), and an HTTP page on 192.168.0.1.
**Do not upload anything.** (If a real stock restore is ever needed, the file to upload
is the plaintext EU 1.0.2 image, see §2.) Power-cycle → stock boots normally (the recovery only writes
after a signed image is uploaded). This single observation upgrades the stock-recovery path
from STATIC to HW.

## 5. STOP conditions (abort and power-cycle; do not improvise)

- Anything other than "Hit any key…" / normal U-Boot output on UART, or garbled 1.8 V console.
- `bootm` reports a hash/format error, or the kernel panics → power-cycle (NAND untouched).
- Any prompt or tool suggesting `saveenv`, `nand erase`, `nand write`, `ubi write`, `mtd write`, `sysupgrade`, `fw_setenv`.
- The OpenWrt RAM image shows root on UBI (H03 FAIL) → stop; it is not a RAM boot.
- Recovery page appears and asks for a file during the passive test → **close it; upload nothing**.

## 6. What must be validated before persistent installation is even considered

1. UART console working; `printenv` captured (built-in env, `bootcmd`, `tp_boot_idx`).
2. Read-only full flash backup verified (`tests/hardware/backup-flash-ro.sh`), stored off-device.
3. Passive U-Boot HTTP recovery test (§4) **and** a real stock re-flash through it on the user's
   unit with the official EU image — proves UART-free return to stock.
4. RAM-boot acceptance HW-01…HW-23 passed (Wi-Fi included).
5. `fw_printenv` from RAM-booted OpenWrt reads the same env as U-Boot `printenv` (layout check; patch 0011).
6. Install design reviewed: write the **inactive** slot (keep stock in the other), verify by
   read-back, only then set `tp_boot_idx`; include `bootcmd=bootipq` if the env CRC was bad
   (kuncy7's AX55 v4 lesson). The OpenWrt FIT must carry `config@mp02.1` and the UBI
   volume `kernel` (OpenWrt `UbiFit` already produces both — STATIC).
7. Rollback drill: set `tp_boot_idx` back to the stock slot from OpenWrt, and separately via the reset-held HTTP recovery.

Until 1-7 are done, `sysupgrade` stays refused in the image (patch 0005) and no persistent
image is offered.

## 7. Can a persistent OpenWrt install preserve OEM recovery and factory data?

**Yes, by design, if** U-Boot/APPSBL, ART, tp_data, BOOTCONFIG*, SBL/QSEE/CDT/MIBIB are never
written (all `read-only` in our DTS — STATIC) and OpenWrt occupies one slot. The reset-held
HTTP recovery lives in U-Boot and rewrites slot 0 with a signed stock image, independent of
what OpenWrt did to either slot (STATIC). Because U-Boot's fallback only catches *load*
failures, a broken-but-loadable OpenWrt kernel is recovered via the reset-held path, not
automatically. **All of this is STATIC/UNVERIFIED on hardware.**
