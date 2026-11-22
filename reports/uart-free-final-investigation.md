> **Safety/status update (2026-11-22):** This is a historical source investigation, not an operator authorization. Do not press Reset/WPS, enter recovery mode, upload a file, change router settings, or power-cycle the AX23 based on this report alone. The current operator gate is `FINAL_PREBOOT_GATE.md`; the UART-free conclusion and current exact-unit blockers are in `ETHERNET_UART_FREE_FINAL_ASSESSMENT.md`. Any physical test needs the owner's explicit approval for that exact action. Do not use the Raspberry Pi for TFTP; prefer a separately approved, isolated Windows host setup.

# UART-free install and recovery: final investigation

Labels as in `wifi-root-cause.md`. This closes the owner's P0 question: is there any
way to install OpenWrt, or recover stock, on the Archer AX23 v2 **without** a UART
console? It extends `boot-nand-feasibility.md` with the stock **userspace** firmware
flasher (disassembled this phase) and the RE700X web-flash precedent.

Nothing here was done to a router. No signatures were forged, no credentials tried,
no exploit deployed; the owner's constraints forbid all of that and we did not.

## 1. The three paths and the signature gate

| Path | Needs UART? | Enforces RSA? | Can load OpenWrt? | Evidence |
|---|---|---|---|---|
| Stock **web UI** firmware upgrade (`nvrammanager`) | No | **Yes** | **No** | **SRC: disassembly §3** |
| U-Boot **reset-held HTTP recovery** | No | **Yes** (same keys) | **No** | SRC (GPL U-Boot, `boot-nand-feasibility.md` §2) |
| U-Boot **UART** `tftpboot`+`bootm` (RAM boot) | **Yes** | No (RAM only, nothing written) | **Yes, RAM only** | **HW-3P** (many boots v0.2–v0.5) |

Every UART-free path is RSA-gated. The only UART-free *recovery* is restoring a
**TP-Link-signed stock** image; there is no UART-free way to make the device run an
**OpenWrt** image, because nothing without a valid TP-Link signature is accepted by
either the web flasher or U-Boot.

## 2. Why the RE700X precedent does NOT carry over (the key new finding)

OpenWrt main ships `tplink_re700x` with a **`factory-webflash.bin`** that the stock
RE700X web UI accepts **without UART** (`scripts/tplink-re700x-factory.py`). It works
because the RE700X stock flasher wraps the payload in the "tplink2022" container and
its loader does **not** RSA-verify it — a keyless path. The obvious question: does the
**AX23 v2** stock flasher have the same keyless path?

**Answer: no.** We extracted the AX23 v2 stock flasher from the official 1.2.1
rootfs and disassembled it (§3). Its default check hook calls the RSA verifier with
the same TP-Link keys as U-Boot. An AX23 keyless web-flash image **cannot** be built
the way the RE700X one is. So:
- RE700X: UART-free OpenWrt install **exists** (keyless web flasher) — though its own
  author marks it "not tested end to end, keep UART at hand."
- AX23 v2: UART-free OpenWrt install **does not exist** without defeating RSA, which
  the owner forbids and we will not attempt.

## 3. Disassembly evidence (SRC, this phase)

Extracted from `Archer AX23 _V2_1.2.1`'s `ubi_rootfs` squashfs
(`usr/bin/nvrammanager`, `usr/lib/libnvrammanager.so`), read-only; disassembled with
the dev build's own cross `objdump` (aarch64 toolchain reads the ARM32 .so):

1. **Same keys as U-Boot.** The two RSA public-key blobs embedded in
   `libnvrammanager.so` are **byte-identical** to the `RSA2048_BLOB` and
   `RSA1024_BLOB` our `tplink-fw-unpack.py` recovered from TP-Link's GPL U-Boot
   (`nm_fwup.c`). Verified by decoding both and comparing (1024-bit and 2048-bit
   Microsoft `PUBLICKEYBLOB`s match exactly). So the web UI and U-Boot trust the
   **same signer**.
2. **The upgrade path calls the verifier.** `upgradeFirmware()` →
   `CheckUpgradeFile()`; the default "check" function pointer (installed via
   `setCheck()`, stored in `.data`) resolves to the routine that calls
   `rsaVerifyPSSSignByBase64EncodePublicKeyBlob` (RSA-2048-PSS/SHA-256) and
   `rsaVerifySignByBase64EncodePublicKeyBlob` (RSA-1024). `nm_buildUpgradeStruct()`
   additionally calls `nm_checkSupportList()`/`nm_checkSoftVer()`. There is **no
   code path in the stock flasher that writes the payload without the signature
   check** (unlike the RE700X `nvrammanager`, whose container path skips it).
3. **AES is present but for decryption of signed images, not a bypass.**
   `libnvrammanager.so` links `AES_cbc_encrypt`/`AES_set_decrypt_key`; the 1.1.2/1.2.1
   images are AES-encrypted *and* RSA-signed. The AES key is derived from the PSS
   salt (our `tplink-fw-unpack.py` §AES) — it is obfuscation layered **on top of**,
   not instead of, the RSA signature.

Conclusion: **SRC** — on the AX23 v2, both the web UI and U-Boot enforce the same
RSA signatures; there is no vendor keyless path like the RE700X's.

## 4. What UART-free recovery *does* exist (stock only)

Per TP-Link's GPL U-Boot (`boot-nand-feasibility.md` §2), the **reset-held HTTP
recovery** (hold reset at power-on → httpd at 192.168.0.1) accepts a TP-Link-signed
image and rewrites slot 0. For the AX23 v2 this can only restore the **plaintext
RSA-1024 images** (1.0.1 / 1.0.2 EU), because U-Boot's `nm_upgradeFwupFile()` writes
the payload raw after the RSA check and never calls AES. The AX23 MR80X v2 sibling's
OpenWrt commit independently states the same for its board: "U-Boot web recovery ...
verifies an RSA1024 signature and has no keyless path. Use the stock web UI." **REL.**

**A passive, no-upload test** (`boot-nand-feasibility.md` §4) can confirm this
recovery path exists on the owner's unit without writing anything: PC at
192.168.0.10, hold reset at power-on, observe the WAN LED go orange and an HTTP page
at 192.168.0.1, then power-cycle (nothing is written until a signed file is
uploaded). This upgrades the stock-recovery claim from SRC to HW. **Recommended as
the first physical step** because it needs no UART and no soldering and proves the
owner can always return to stock.

## 5. Final answers to the owner

1. **UART-free OpenWrt install?** **No.** Signatures are enforced on every UART-free
   path (web UI and U-Boot), and the AX23 flasher has no keyless path (unlike the
   RE700X). SRC, strong.
2. **UART-free stock recovery?** **Yes, by design** (reset-held HTTP recovery with a
   signed EU 1.0.2 image), **UNVERIFIED on HW** until the passive test (§4) and a
   real re-flash are done on the owner's unit.
3. **Therefore first OpenWrt boot needs UART** (1.8 V, or 3.3 V adapter **plus** a
   level shifter — never 3.3 V onto the 1.8 V RX pin) for the RAM-boot bring-up. This
   matches the AX23 3P method and the RE700X/MR80X "keep UART at hand" advice.
4. **No exploit, no forged signature, no header tampering** was used or is proposed;
   the owner forbids them and they are unnecessary for the (RAM-boot) validation plan.

## 6. Reproduce
```
tools/bdf/board-data-from-tplink-firmware.sh   # downloads+verifies 1.2.1 (signed)
# extract usr/lib/libnvrammanager.so from ubi_rootfs (unsquashfs), then:
$OWRT/staging_dir/toolchain-*/bin/*-objdump -d libnvrammanager.so | \
  grep -E 'rsaVerify|CheckUpgradeFile|setCheck'   # verifier in the check path
tools/bdf/tplink-fw-unpack.py <firmware> out.ubi  # same keys verify the images
```
