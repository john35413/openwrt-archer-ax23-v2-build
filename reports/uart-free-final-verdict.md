> **Safety/status update (2026-11-22):** This is a historical source investigation, not an operator authorization. Do not press Reset/WPS, enter recovery mode, upload a file, change router settings, or power-cycle the AX23 based on this report alone. The current operator gate is `FINAL_PREBOOT_GATE.md`; the UART-free conclusion and current exact-unit blockers are in `ETHERNET_UART_FREE_FINAL_ASSESSMENT.md`. Any physical test needs the owner's explicit approval for that exact action. Do not use the Raspberry Pi for TFTP; prefer a separately approved, isolated Windows host setup.

# UART-free installation: final verdict

Extends `uart-free-final-investigation.md`, which showed that both the stock web flasher
and U-Boot recovery enforce TP-Link's RSA signatures. This phase did **not** stop at
that conclusion. It examined every *legitimate, documented* access mechanism the stock
firmware might offer. Labels as in `wifi-root-cause.md`. Everything is **OEM/SRC**
static analysis of the official 1.2.1 image and TP-Link's GPL U-Boot. Nothing was sent
to a router and no credential was tried.

## 1. Mechanisms examined

| Mechanism | Present in stock? | Gives the owner a shell or a way to run OpenWrt? | Evidence |
|---|---|---|---|
| Web UI firmware upgrade | yes | **no**: RSA-verified (same keys as U-Boot) | disassembly, `uart-free-final-investigation.md` §3 |
| U-Boot reset-held HTTP recovery | yes | **no** for OpenWrt (RSA, plaintext images only); **yes** for stock restore | GPL `cmd_bootqca.c`, `nm_fwup.c` |
| U-Boot TFTP client / network boot at power-on | **no**: autoboot runs only `bootipq`; `tftpboot` needs the console | GPL `autoboot.c`, `bootipq` |
| **Stock SSH server** (Dropbear, `S50dropbear`, port 22, password auth on) | **yes** | **no shell**: `root` (shell `/bin/ash`) has a **locked** password in the image, and no stock script or daemon sets it (only BusyBox carries `/etc/shadow`/`passwd` strings). The accounts with empty passwords (`visit`, `guest`) have shell `/bin/false`, which allows tunnels for TP-Link's app and guest portal but no commands | OEM `/etc/config/dropbear`, `/etc/passwd`, `/etc/shadow` (locked/empty status only, no hash read), strings sweep |
| Stock telnet | script present, **disabled** (`#START=50`, no rc.d link) | no | OEM `/etc/init.d/telnet` |
| Official developer/engineering mode | none documented by TP-Link for this model | no | — |
| Factory debug protocol (TDDP, `tddp_hook_*`) | factory test hooks present | **excluded**: an undocumented factory interface, and using it would mean relying on undocumented, security-relevant behaviour, which the owner's constraints forbid | OEM file list |
| RE700X-style keyless web flash | **no**: AX23 flasher's default check hook is the RSA verifier | — | disassembly |
| MR80X-style fw-type-selected verifier | AX23 U-Boot/web flasher pick RSA-1024 vs RSA-2048 by type byte; both are signature checks | no keyless type found in TP-Link's GPL `nm_fwup.c` | GPL |

## 2. Why the sibling methods do not transfer
- **RE700X** (OpenWrt main, `factory-webflash.bin`): its stock `nvrammanager` accepts the
  "tplink2022" container with an MD5-with-salt checksum and **no RSA check** on that
  path. The AX23 1.2.1 `libnvrammanager.so` embeds the two TP-Link RSA keys and its
  default check hook calls `rsaVerify*`. That is a different implementation, so the
  container is rejected.
- **MR80X v2** (Mercusys `factory.bin`): the Mercusys web loader selects its verifier
  from a fw-type string, and the OpenWrt container uses a type that loader accepts;
  the AX23 (TP-Link) loader has no such keyless type, and the MR80X author notes its own
  **U-Boot** recovery is RSA-gated with "no keyless path", which matches the AX23.

## 3. Verdict
**No legitimate UART-free OpenWrt installation route exists for the Archer AX23 v2.**
VERIFIED BY OEM/SOURCE ANALYSIS (web flasher disassembly, GPL U-Boot, stock rootfs
configuration). Additional time spent looking would not change this without defeating
a security mechanism, which is out of scope.

UART-free **stock recovery** remains available by design (reset-held HTTP recovery
with the signed plaintext EU 1.0.2 image). It is UNVERIFIED on hardware until the
passive Stage-0 test (`physical-hardware-test-plan.md`).

## 4. Easiest physically safe alternative: Raspberry Pi as TFTP + serial host
The Pi 4 GPIO UART is **3.3 V**. The AX23 console is reported as **1.8 V** (HW-3P: the
JP1 header lacks its level-shifter parts). **Never connect the Pi's GPIO UART directly.**
Options, safest first:
1. **USB-UART adapter that supports 1.8 V I/O** (e.g. FTDI-based adapters with a
   selectable or 1.8 V VCCIO), plugged into the Pi's USB port: the Pi only sees
   `/dev/ttyUSB0`. Connect **TX, RX, GND only**, never VCC.
2. A 3.3 V adapter or the Pi GPIO UART **through a bidirectional 1.8 V ↔ 3.3 V level
   shifter** (e.g. a TXS0108E-class or BSS138 MOSFET board with its low side powered
   from a 1.8 V reference on the router and its high side from 3.3 V). Verify with a
   multimeter that the router's TX idles at ~1.8 V before connecting.
3. On the Pi, in a dedicated directory, without touching Pi-hole/OASA/Tailscale/Docker:
   `picocom -b 115200 /dev/ttyUSB0 --logfile ax23-console.log` for logging, and a
   **throwaway** TFTP server bound only to the bring-up interface/subnet (for example a
   user-run `dnsmasq --port=0 --enable-tftp --tftp-root=$PWD/tftp --interface=<usb-eth>`
   on a separate USB-Ethernet adapter, so the Pi's existing DNS/DHCP are untouched).
The router-side steps are Stages 1–2 of `physical-hardware-test-plan.md` (stop
autoboot within 1 s, `tftpboot` + `bootm` the dev `.itb`, **no `saveenv`**).
