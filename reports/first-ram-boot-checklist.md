# First AX23 v2 RAM boot checklist

This checklist is subordinate to [`FINAL_PREBOOT_GATE.md`](FINAL_PREBOOT_GATE.md).
It is **not** authorization to boot. Do not flash, use the OEM firmware-update
page, save U-Boot environment changes, or press Reset/WPS during initial checks.

Before any transfer, complete the checklist in `FINAL_PREBOOT_GATE.md` through
the U-Boot observation gate. If any item is BLOCKED or STOP, do not run `bootm`.

## Offline image facts

- Artifact: `artifacts/ram-only/dev/openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb`
- Expected size: 13,330,704 bytes.
- Expected SHA256: `6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff`.
- FIT default: `config@mp02.1`; selected kernel and DTB are `kernel-1` / `fdt-1`.
- Kernel load and entry: `0x41000000`. The FIT transfer buffer is staged at
  `0x44000000` only after the actual U-Boot DRAM map has been checked.
- This is an initramfs image. EU radio board data is already embedded; no
  post-boot ART extraction or rebuild is needed for the planned first tests.

The FIT is hash-checked, not established as signed. Do not bypass any signature
policy. The built DTB has a zero-sized memory node that explicitly expects the
bootloader to supply RAM size. U-Boot's actual memory map, FIT relocation and
reserved-memory behavior remain hardware observations, not offline facts.

## Required early stop before Wi-Fi

The first boot must use a temporary U-Boot `bootargs` addition
`init=/bin/sh`, after recording the existing `bootargs` and confirming the
console syntax at the actual prompt. This overrides normal OpenWrt init so
procd and userspace module/radio startup do not begin. It does **not** prevent
kernel built-in probes, switch GPIO activity, or kernel UBI attachment; passive
GPIO checks and the NAND source/build evidence are still required before boot.
If the exact U-Boot does not pass this temporary argument or the early shell is
not reached, stop and do not proceed to normal startup. Do not remove existing
console or safety parameters by guessing. `setenv` is volatile for the current
boot; never run `saveenv`.

Once the early shell is reached, first capture serial output and verify RAM
root, the 16 MTD read-only flags, and every attached UBI read-only state. Do not
probe writability with a write. Do not run `/sbin/init` until the early checks
are accepted; that starts normal OpenWrt services and may initialize Wi-Fi.

## After approved normal startup only

Diagnostics are sourced from the PC and streamed over SSH; they are not inside
the image. Verify IP connectivity and SSH explicitly before using commands that
assume them. The board data is already present in the image. Do not back up raw
ART or firmware as a prerequisite; any optional read-only flash backup is a
separate, owner-approved action after live MTD/UBI read-only status is recorded.

Record source revision for `tests/hardware/ax23-selfdiag.sh` and keep logs
private until MACs, keys, serials and calibration identifiers are redacted.
Measure actual emitted RF power with suitable calibrated equipment; configured
or driver-reported power and client RSSI are different observations.
