# NAND write-protection audit of the RAM-boot image

**Codex update for the current dev series.** 0020 bypasses the generic UBI auto-attach on this board, superseding section 2. Explicit tp_data attachment still runs for factory reads. Require a read-only mount and read-only UBI; on the actual unit inventory every MTD node and flag, with no test writes. The checker now rejects extra physical partitions and diagnostics fail on unreadable flags.

Question: with patch 0015 (all 16 DT partitions `read-only`), can **any** Linux code
path in the RAM-boot image write the AX23's NAND? Labels as in `wifi-root-cause.md`.
Everything here is **SRC/BUILD** (our exact kernel 6.18.55 tree and the built
root filesystem). The lab results are **SIM**. Nothing was run on a router.

## 1. Layer-by-layer

| # | Path | Where it could write | Protection in our image | Evidence |
|---|---|---|---|---|
| 1 | Partition MTD devices `/dev/mtdN` | erase/write/OOB/markbad ioctls | DT `read-only` clears `MTD_WRITEABLE`; `mtd_erase()`, `mtd_write_oob()` (which `mtd_write()` calls), `mtd_block_markbad()`, `mtd_panic_write()` all return `-EROFS` without it | SRC `drivers/mtd/mtdcore.c` |
| 2 | Whole-chip master device (would bypass partition flags) | everything | **not registered**: `CONFIG_MTD_PARTITIONED_MASTER` unset | BUILD `.config` |
| 3 | `mtdparts=` on the kernel command line (would replace DT partitions, dropping `read-only`) | everything | **impossible**: `CONFIG_MTD_CMDLINE_PARTS` unset, `CONFIG_CMDLINE=""`; partitions come only from DT (`CONFIG_MTD_OF_PARTS`) | BUILD |
| 4 | On-flash bad-block table updates | BBT blocks | none: no `nand-on-flash-bbt`; SPI-NAND core keeps the BBT in RAM | SRC DTS + spi-nand core |
| 5 | Bad-block marking after an I/O error | OOB marker | via `mtd_block_markbad()` → `-EROFS` (row 1) | SRC |
| 6 | UBI auto-attach of `data` (pending 490) | UBI scrubbing, wear-levelling, erase worker | MTD not writeable → `ubi->ro_mode = 1` ("MTD device %d is write-protected, attach in read-only mode"); UBI I/O refuses writes in ro_mode, and the MTD layer refuses them again (two independent layers) | SRC `ubi/build.c:748-756`; HW-3P shows the same message for tp_data |
| 7 | `09_mount_tp_data` (`ubiattach` + `mount -o ro`) | UBI/UBIFS | same as 6, plus UBIFS mounted `ro` | SRC rootfs |
| 8 | Overlay discovery / `mount_root` / `firstboot` / `jffs2reset` | rootfs_data creation/format | **never runs** in initramfs: `80_mount_root` registers `do_mount_root` only when `INITRAMFS != 1`; `70_initramfs_test` leaves preinit early | SRC rootfs `/lib/preinit` |
| 9 | Boot-time env writers (`bootcount`, `mtd resetbc`) | U-Boot env | `bootcount` acts only on Linksys boards; no AX23 script calls `fw_setenv`; a manual `fw_setenv` fails with `-EROFS` | SRC rootfs |
| 10 | sysupgrade / `nand.sh` / `stage2` | slots | refused on this board (patch 0005, `platform_upgrade_blocked`); would hit `-EROFS` anyway | BUILD validator |
| 11 | SPI-NAND driver probe (`spinand_*`) | chip feature registers | writes only volatile configuration (ECC enable, quad mode), not the array; never OTP lock | SRC |
| 12 | `ubi.mtd=` from U-Boot `bootargs` on a manual `bootm` | attaches a slot | read-only (row 6); 3P RAM-boot command lines carry no `ubi.mtd` | SRC + HW-3P cmdline |

The AX23 DTS also appends `root=/dev/ubiblock0_1 coherent_pool=2M`; the exact
U-Boot environment and final command line on our unit are unverified. Do not
assume third-party bootargs. The first-boot procedure records `printenv
bootargs` and temporarily appends `rdinit=/bin/sh` to select `/bin/sh` before
the working initramfs `/init`, procd, services and Wi-Fi startup. `init=/bin/sh`
alone is not a guard because Linux tries the working `rdinit` command (`/init`)
first. If the expected shell is not reached, STOP; do not continue to `/init`. This does not disable kernel MTD
or UBI discovery/attachment, and it is not a substitute for checking runtime
read-only flags. Never use `saveenv`.

## 2. Can UBI auto-attach be disabled entirely?
Yes, but it is not needed. The generic auto-attach (pending 490) has no command-line
switch and only skips when `ubi.mtd=` is given. Disabling it would need a kernel patch
or a rename of the `data` partition, which buys nothing over rows 1+6 (attach is
read-only and the MTD layer refuses writes underneath) and would diverge from the
partition table a later install must match. **Decision: keep 0015 as the single,
smallest mechanism.** The self-diagnostic checks it on the device (S1.8 flags per
partition, S1.15 every attached UBI in read-only mode).

## 3. Why 0015 was necessary (SIM evidence)
`tests/nand` L08 shows a **read-write** UBI erasing and rewriting a PEB after nothing
but reads, once a read returns a correctable bitflip ("scrubbed PEB 43 ... data moved
to PEB 42"). Before 0015 the RAM image attached `data` read-write (HW-3P log:
`UBI: auto-attach mtd15`, no write-protected notice). So without 0015 a RAM boot could
erase NAND with no command given. After 0015 that path ends at rows 1+6.

## 4. What a persistent install must change, and only that
Rows 1/6/7 are exactly what an install would need to relax: the **two slot
partitions** and **0:APPSBLENV** (for `tp_boot_idx`). SBL1, MIBIB, BOOTCONFIG*, QSEE,
DEVCFG, CDT, APPSBL, ART, TRAINING, tp_data, radio and data stay read-only forever.
That is a Stage D item (`physical-hardware-test-plan.md`), behind owner authorization.

## 5. Verdict
**All RAM-boot NAND write paths we could identify are closed**, each by the kernel
(rows 1–6) or because the code path does not run in initramfs (rows 8–10).
VERIFIED BY SOURCE/BUILD ANALYSIS; the UBI behaviour is also VERIFIED IN SIMULATION.
The one thing the device must confirm is that the DT flags reach the running kernel:
`ax23-selfdiag.sh` S1.8 (all 16 partitions `writeable=no`) and S1.15 (read-only UBI
attach) on the first RAM boot.
