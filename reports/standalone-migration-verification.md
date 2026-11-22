# Standalone migration verification

## Source and destination

- Original repository: `https://github.com/john35413/DuinoCoinUSB_ESP8266`
- Original branch: `claude/openwrt-archer-ax23-v2-5vtpoe`
- Latest remote source SHA, fetched and rechecked: `6847cff6fc5a7bea141c42ccde19d0c4f9f972f4`
- Last known Claude checkpoint: `6847cff6fc5a7bea141c42ccde19d0c4f9f972f4` (no newer commit exists on the branch)
- Standalone checkout before this verification update: `548abdbfd3ed070c8829354f66c4e1221b542ed2`
- Initial published source checkpoint on both branches: `308d692e4921bc061f3a3cabcc35b6b769405b37`
- Destination: `https://github.com/john35413/openwrt-archer-ax23-v2-build`
- Local standalone path: `/home/jfits/openwrt-archer-ax23-build`

## Normalized complete tree comparison

Compared every tracked file in `AX23_V2_OPENWRT/` at the fetched source SHA with the standalone `dev` tree, normalizing the AX23 subtree prefix away. Binary and text files were compared by Git blob identity; patch SHA256 values were also compared.

- Source subtree tracked files: **305**
- Intentional raw-log exclusions: **147**
- Source non-log files: **158**
- Standalone files before this report: **163**
- Published standalone files after the report was added: **164**
- Identical source files: **152**
- Source paths intentionally modified: **6** — `.gitignore` (private/generated exclusions), `README.md` (standalone docs/URL), `reports/CODEX_FINAL_HANDOVER.md` and `reports/project-state.json` (migration records), `tools/clean-dev.sh` (symlink containment safety), `tools/test-dev.sh` (runs the guard regression).
- Source paths missing: **0**
- Standalone-only additions: **6** — contribution/license/provenance documents, GPL license text, cleanup symlink regression test, and this verification report.
- New Claude changes since the last known checkpoint: **0 commits**. The complete latest source subtree is represented; no legitimate source, diagnostic, report, or research file was omitted.
- Latest diagnostic/research files: present in the normalized comparison; all source non-log paths accounted for.

All **27 numbered firmware patches** compare byte-for-byte (SHA256); patch series has exactly 27 entries. Patch 0023, 0024, 0025, 0026 and 0027 match the original source blobs. `patches/variants/trunk-1g-sgmii.patch` is present and not in the default series. The additional `patches/openwrt/files/960-...patch` is a supporting file patch and is not a numbered series entry.

Intentional history/tree differences: AX23 subtree promoted to repository root; DuinoCoin paths and unrelated commits excluded; 147 raw log files excluded from the source snapshot and all published branches; build products, private board data, toolchains and caches excluded; standalone README/licensing/provenance/guard-test additions; repository URLs updated. No other content differences were observed.

## Security and repository integrity

Scanned all named objects reachable from local `main` and `dev` before publication: **719** named objects; no raw log paths, build/cache/private-data paths, firmware/binary/credential file paths, or checked credential/private-key markers found. `git fsck --full --no-reflogs` passed. This is a targeted static scan, not a guarantee against every possible secret encoding. No firmware image or board-data blob is tracked. Post-publication, the same audit was rerun against main/dev at `80daab2744294e2a393b3a28a6ab9a5e3a483602`: **734** reachable named objects, the same zero findings, and fsck PASS.

## Tests and artifact (no rebuild)

- Static suite: PASS; 53 development-DTB checks; baseline DTB SKIP because it is unavailable. ShellCheck and Python compile checks passed; 27-patch series applies cleanly to its staged baseline.
- Unit runner: **12 PASS, 1 SKIP** (`ubireader_extract_images` unavailable); 31 Python unit cases PASS. The calibration-region suite reports two EU-fixture subchecks SKIP because private fixtures were absent.
- The artifact validator record remains **77 PASS, 1 INFO, 0 FAIL** from the completed local build; no firmware rebuild was performed for this migration.
- Local-only ITB: `/home/jfits/DuinoCoinUSB_ESP8266/AX23_V2_OPENWRT/artifacts/ram-only/dev/openwrt-qualcommax-ipq50xx-tplink_archer-ax23-v2-initramfs-uImage.itb`; **13,330,704 bytes**, SHA256 `6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff` (recomputed in this task). The symlink resolves into the preserved original build tree. Not uploaded.

This comparison records the verified public source checkpoint. GitHub reports the repository public with main as default; both main and dev were pushed and verified at the same source checkpoint, followed by identical status-only metadata updates. The final live branch SHA is verified from refs and returned in the task completion record. These documentation updates do not imply a new firmware build. Physical hardware validation was not performed.
