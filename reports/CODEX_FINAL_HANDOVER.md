# Codex final handover

**State:** The public repository `https://github.com/john35413/openwrt-archer-ax23-v2-build` has been created. The verified local baseline is being published to `main` and `dev`; confirm the live branch SHAs after push. The local build and offline validation are complete; physical use remains conditional. No router operation occurred.

## Revisions

- Starting Claude checkpoint: `9576d3ea680aabcf9a14eb905c97ad99a7d430b8`.
- Latest imported legacy branch commit: `6847cff6fc5a7bea141c42ccde19d0c4f9f972f4`; it adds `reports/final-validation-and-ram-load-conclusions.md`.
- Standalone repository: `https://github.com/john35413/openwrt-archer-ax23-v2-build` (public); default branch `main`; active development branch `dev`.
- Standalone local path: `/home/jfits/openwrt-archer-ax23-build`.
- File comparison: 305 source subtree paths, 147 raw-log exclusions, 158 non-log source paths; at the pre-publication checkpoint 152 files are blob-identical, six source files are intentionally adapted, five standalone-only files were added, and none are missing. See `reports/standalone-migration-verification.md`.
- Previous Codex firmware-source checkpoint: `8673c2e6a001fce6271d11700bfa1d27dc51edc9`.
- Current host-test correction checkpoint: `bd2326a5002eca746ce3edcdff5b7cb2913188ae` (`tests: decode dtc string-list encoded radio address cells`).
- Prepared OpenWrt tree: `d0e975060d5c71565e0a62abbddf48ef1312478c`; all 27 ordered patches applied. 0026 is inner commit `4f8bf04`; 0027 is `d0e9750`.

## Build and image

The existing WSL tree and caches were reused. `tools/build-dev.sh --variant dev --resume --jobs 4` completed. A WindowsApps path inherited by WSL initially caused GNU `find -execdir` to fail during package install; a Linux-only PATH scoped to the build process fixed it without changing system settings.

Local-only image: `/home/jfits/DuinoCoinUSB_ESP8266/AX23_V2_OPENWRT/artifacts/ram-only/dev/openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb` (13,330,704 bytes, SHA256 `6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff`). FIT `config@mp02.1`, kernel load/entry `0x41000000`. The image was not uploaded to GitHub. A local symlink in the standalone checkout will point to the preserved original artifact, without copying it. Raw build/test logs under `logs/dev/` are also local-only; GitHub has the concise validator report and build manifest, not the raw compiler log. Claude's earlier cloud image is a separate build. Raw build/test logs and all historical `logs/` paths were omitted from the standalone publication.

Artifact validator: 77 PASS, 1 INFO, 0 FAIL. It confirms 16 read-only DT partitions, target/FIT, EU board data, embedded modules/startup hooks and the compiled 0026/0027 objects. `qcom_q6v5_mpd.o` contains `q6_wcss_recover_userpds`; patched backports `ath11k/dp.o` compiled with exact allocation sizes.

Latest local rerun: 12 shell unit suites PASS, one SKIP (`ubireader_extract_images` unavailable); 31 Python unit tests PASS; two EU ART fixture subchecks SKIP; static runner PASS (53 development-DTB checks, baseline DTB SKIP). These are offline tests, not hardware tests. Two EU fixture subchecks in the calibration-region suite are SKIP. Mock recovery tests are not proof of kernel concurrency or hardware behavior.

## Findings and changes

- Validation uncovered a checker defect missed earlier: dtc renders the valid IPQ5018 BDF address `0x4c400000` as the string list `"L@", ""`; the parser mishandled string lists. Fixed `tests/static/check_dtb.py` and added three regression cases in `tests/unit/test_tools.py`. The FIT DTB now passes. Host test only; no firmware rebuild required.
- Standalone path audit found `tools/clean-dev.sh` could traverse the new checkout's `build/` and `upstream/` symlinks and delete the preserved original caches. Added a realpath containment preflight plus `tests/unit/test_clean_symlink_guard.sh`; the regression confirms an external cache sentinel is preserved. The fix is on `dev` only and does not affect firmware output.
- The earlier S2.4 stale-counter and S3.22 ART/BDF semantic corrections remain in `ec07e66` (`tests/hardware/ax23-selfdiag.sh`). This script is not embedded; stream it from the PC over SSH using `--bundle`.
- Source review found no closed root/user remoteproc workqueue wait cycle in examined paths. Runtime races, SCM behavior, repeated recovery and OFFLINE-state recovery remain unproven. DMA source cleanup and compiled patch 0027 checks pass.
- 2.5 G HSGMII endpoints are internally consistent. GPIO 26/39 switch reset mapping remains unresolved; do not boot until passively traced. No RF-power conclusions are supported. No intended NAND write path was found; runtime MTD/UBI state still needs read-only confirmation.

## Readiness and next action

**CONDITIONAL GO for RAM boot only after** confirming exact EU v2.0 hardware, measured UART voltage/pins, stock recovery availability, bootloader RAM/FIT/signature acceptance without bypass, and passive GPIO 26/39 wiring/polarity. Otherwise stop. No persistent image is authorized; never `saveenv`, flash or run sysupgrade.

Source comparison used original branch `6847cff6fc5a7bea141c42ccde19d0c4f9f972f4`; it has no commits newer than the known Claude checkpoint. See `reports/standalone-migration-verification.md` for the normalized tree counts and history audit. The artifact exists only on the Windows PC's WSL filesystem. Claude can access published source, handover, reports and manifests through GitHub, but cannot access that local image or private EU board data. Recompute the image hash locally before any later use. See `reports/build-manifest.json`, `reports/final-codex-adversarial-audit.md`, `reports/first-ram-boot-checklist.md` and root `ORIGIN-PROVENANCE.md`. The prepared `build/`, upstream source trees and private `board-data/` are local symlinks to the original project; they were not copied or published.
