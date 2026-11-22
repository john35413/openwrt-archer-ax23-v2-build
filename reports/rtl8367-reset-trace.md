# RTL8367S-VB reset and initialisation: traced consumers

Scope: the Realtek switch reset line, its sequencing, and the 2500BASE-X trunk set-up
on the Archer AX23 EU V2.0. No router was touched and nothing extracted was executed.
Labels:
- **OEM-BIN**: static ARM disassembly of the signed TP-Link 1.2.1 image (`qca-ssdk.ko`).
- **OEM-SRC**: TP-Link's GPL tarball for this model (`GPL_AX23v2.tar.gz`, U-Boot 2016).
- **SOURCE**: our compiled kernel 6.18.55.
- **REL**: related hardware.
- **UNV**: unverified.

Nothing here is **VERIFIED ON OUR PHYSICAL AX23**.

## 1. Which GPIO resets the Realtek switch
| Consumer | GPIO and sequence | Evidence |
|---|---|---|
| TP-Link U-Boot `ipq5018_gmac.c: rtl8367_sw_init()` | `reset_rtl8367_switch_gpio(CONFIG_SWITCH_RESET)`, with `config.mk: -DCONFIG_SWITCH_RESET=26`. TLMM CFG = `0x203` (GPIO function, OE, pull-up, 2 mA); OUT = 0 for **500 ms**, then 1, wait **500 ms**; then `rtk_switch_init()` and `MODE_EXT_HSGMII` 2500 forced on EXT0/EXT1. Runs from `board_eth_init` → `initr_net` on every boot; U-Boot's `ipq5018-mp02.1.dts` sets `rtl_switch_enable = <1>`. | OEM-SRC |
| Stock kernel `qca-ssdk.ko`, function at `.text 0xa8d20` (called from module init) | Hard-coded **GPIO 26**: output high, 500 ms; **low** 200 ms; high, 200 ms; logs "GPIO%d reset switch done" with 26. It runs unconditionally after the ISISC/SCOMPHY device loop, then `rtk_switch_init` (up to 5 tries) and VLAN init. | OEM-BIN |
| Stock kernel `/proc/driver/rtl8367s` `rtl8367_gpio_reset` | "gpio reset: resetting RTL8367 via GPIO%d" with **26** | OEM-BIN |
| Stock kernel ISISC branch (`.init.text 0x2e8–0x47c`) | `reset_gpio` from DT (= **39**, inside the `qcom,ess-switch-qca83xx` node with `ar8327-initvals`): low 200 ms, high | OEM-BIN. This is the **QCA8337** driver path; the AX23 has no QCA8337. |
| Stock DT pinmux | `mdio@90000` `pinctrl-0 = phy_pins` muxes **gpio26 = GPIO**, pull-down, output-low (`phy-reset-gpio = <&tlmm 26 0>`). The `blsp1_uart_cts` alternative on gpio26 sits in a pin group no node uses. No pinctrl state touches gpio39. | OEM-BIN (DTB) |

**Conclusion (OEM-BIN + OEM-SRC):** TP-Link's bootloader and TP-Link's kernel, the only
two pieces of software written for this board, both reset the RTL8367 on **GPIO 26**,
**active low**, muxed as a plain GPIO. GPIO 39 is consumed only by the QCA8337 code path.
Sply's GPIO 39 was read from that QCA8337 node of the live DT (`upstream/ax23/docs/DEVICE-TREE.md`),
which is a label, not a consumer. PCB continuity remains **UNV**.

## 2. What that means for our image (SOURCE)
- On every boot, cold or warm, U-Boot pulses GPIO 26 for 500 ms and initialises the switch
  before Linux starts (OEM-SRC).
- Linux then **hardware-resets the chip through `CHIP_RESET`** in `rtl8365mb_setup()`
  (1 s wait for family D, 0025) and programs it from scratch. HW-3P's working 2.5 G
  trunk therefore already comes from a chip initialised from reset by Linux, not from
  U-Boot's configuration.
- Our current DTS declares `reset-gpios = <&tlmm 39 GPIO_ACTIVE_LOW>` on the
  RTL8367S-VB node. This is **not proven to be a no-op**. The compiled Linux
  `rtl83xx_probe()` requests that descriptor with `GPIOD_OUT_LOW`; the common
  Realtek driver then asserts reset, sleeps 25 ms, deasserts it, sleeps 100 ms,
  and keeps the device-managed GPIO request for the lifetime of the device.
  With `GPIO_ACTIVE_LOW`, logical asserted means physical low and deasserted
  means physical high. OEM evidence establishes GPIO 26 as the vendor reset
  line, but does not establish that GPIO 39 is unconnected or electrically
  harmless on this PCB. The current image can actively drive GPIO 39 during
  Linux device probe; passive board measurement is therefore a hard pre-boot
  gate, not an after-boot diagnostic.
- **Moving the DTS to GPIO 26 is not adopted yet.** It gives no cold-boot gain (U-Boot
  already pulses 26 on every boot), and `rtl83xx_probe()` would assert it for only
  25 ms and read the chip ID 100 ms after release. Stock waits 200 ms (kernel) or
  500 ms (U-Boot) before the first access, and still retries `rtk_switch_init`.
  Switching the line without matching timing could turn a working HW-3P path into a
  probe failure. GPIO 39 is kept, as required, until the measurement in §5.

## 3. 2500BASE-X trunk: differences from stock
| Item | Stock | Ours | Evidence / status |
|---|---|---|---|
| SerDes table (`HSGCfg`, 9 SDS writes incl. `0x0410 = 0x0002`, the "HSGMII signal" fix that U-Boot's comment says moved into API 1.4.2) | applied | **identical 9 values** + `{0x0004, 0x074F}` (from the 777-07 series) | OEM-SRC vs SOURCE. The extra entry's provenance is the 777 author's vendor driver version, not this tarball. |
| `SDSNctrlPatch`: 129 writes, applied before the table on every SerDes-0 set-up | applied | **not applied**. Linux's `CHIP_RESET` erases U-Boot's copy. | OEM-SRC. It is an **NCTL controller ROM patch** (§6), not a SerDes tuning table. **Not imported:** Realtek proprietary, no open implementation, purpose of the patched code UNV. HW-3P passes traffic without it. |
| Embedded DW8051 | vendor loads firmware | held in reset by design (it would race with phylink) | SOURCE |
| CPU-port flow control | `txpause = rxpause = DISABLED` (U-Boot) | `pause` on both fixed links | OEM-SRC vs SOURCE. HW-3P works with pause. Measurable variable, not changed. |
| CPU port mode | HSGMII 2500 forced, nway disabled; stock DT `switch_mac_mode = 0x0c`, `forced-speed 2500` | 2500base-x fixed-link, in-band AN off | matches |

Patches **0024** (CMN PLL bus clocks) and **0025** (family-D reset/SerDes waits) were
re-read against the vendor sequence. No defect was found: the vendor's longer waits
point the same way. Kept unchanged.

## 4. Sibling fixes (not repeating Codex's 777/778 comparison)
- **AX55 v1:** GPIO 33 on the switch (an LED on the AX23). Not applicable.
- **EX511 v2:** GPIO 33, 1 G SGMII shipped. No further reset fix applies.
- **MR80X v2:** upstream uses GPIO 26 on `&mdio1`; the separately tested fork puts 26 on the switch. Both agree that **26 belongs to the switch reset on IPQ5018+RTL8367S boards built from this reference**. REL, consistent with §1.
- There is no open-source fix for `SDSNctrlPatch` to import.

## 5. The physical measurement that closes it
Passive and read-only, in this order:
1. **UART, stock cold boot (Stage 0/1 wiring, logic-level verified):** capture U-Boot's
   `rtk_switch_init ret = …` / `Set RTL8367S SGMII 2.5Gbps` lines. That confirms the
   shipped U-Boot runs §1's code.
2. **Before any RAM boot, unpowered continuity:** map RTL8367S-VB `nRESET` to
   GPIO 26 and GPIO 39 using a board-ground-referenced, high-impedance method.
   Alternatively, passively observe both nets during a stock boot with a
   high-impedance probe. Never drive either line. If GPIO 39 is connected to
   `nRESET`, another reset, or an unknown circuit, stop: this image drives it.
   A post-boot S2.8 readout is corroborating evidence only; it cannot establish
   safety before the GPIO has already been driven.
3. **After a separately approved RAM boot only:** `ax23-selfdiag.sh` S2.8 records
   the kernel's GPIO ownership/mux state alongside S2.1/S2.2/S2.4/S2.5.
4. **Only if (2) confirms 26:** a one-variable variant image with
   `reset-gpios = <&tlmm 26 GPIO_ACTIVE_LOW>` on the switch node, a pinctrl state
   `gpio26: function "gpio", bias-pull-up`, and a reset assert ≥ 200 ms / release-to-access
   ≥ 200 ms (stock timing). Repeat the 20× cold/warm boot test against the GPIO 39 baseline.
5. **Only if S2.4 fails at 2.5 G:** check S2.5 (777-08 re-latch events), then the 1 G SGMII
   variant `patches/variants/trunk-1g-sgmii.patch` (§7), then pause off, one variable at a time.

## 6. The vendor SerDes-0 sequence (`SDSNctrlPatch`): what it is
No table values are reproduced here or anywhere in the project.

| Question | Answer | Evidence |
|---|---|---|
| Which subsystem? | The **NCTL** block, not the SerDes analog registers. The writes target `RTL8367D_REG_NCTL_0` (`0x6100`: `CPU_EN` 13:12, `PATCH_MODE_EN` 11, `PC_SPECIFY_EN` 10, `PC_SPECIFY` 9:0), `NCTL_RAM_INDACS_0/1` (`0x6135/0x6136`, an indirect window into NCTL RAM) and the breakpoint slots `NCTL_Pnn_0/1` (`BP_EN` + 10-bit `BP_ADDR`, 10-bit target). The sequence enables patch mode, loads a short program into NCTL RAM and installs breakpoint redirects over NCTL ROM code: a **ROM patch for an embedded SerDes-control sequencer**. It is separate from the DW8051 (`DW8051_RDY` 0x1336, `DW8051_EN`), which our driver holds in reset. | OEM-SRC (`rtl8367d_reg.h` field names) |
| When is it applied? | Unconditionally, with no chip-revision gate, whenever SerDes 0 is put into service: extension port 1 in any SerDes mode (`_dal_rtl8367d_setAsicPortExtMode`) and port 4 in fiber combo media (`dal_rtl8367d_port_phyComboPortMedia_set`). | OEM-SRC |
| What does the patched code do? | **UNV.** No public documentation names NCTL: the register map kept by the in-kernel rtl8365mb maintainer (luizluca, `Realtek_Registers_n_Structure_Mapping.md`) documents the DW8051 but not NCTL. The program was not decoded (proprietary). | public source search |
| Do open drivers reach the same behaviour another way? | For the documented failure, **yes, by different steps.** 777-08 (in our base) identifies the family-D cause of "2.5G/Full on both sides, no frames, no CRC/FIFO errors": the receiver latches on the `SDS_MISC` DISABLE → HSGMII edge only once the far-end MAC is up. It re-drives that edge after the conduit comes up. 0006–0009 bring the IPQ5018 UNIPHY up at GMAC probe (SoC end first, as the vendor bootloader orders it). 777-07 writes the vendor-identical SerDes table in vendor order. Whether the NCTL patch adds anything beyond that is **UNV**. | SOURCE + REL (777-08 IPQ5018 log; kuncy7 AX55) |
| Could its absence explain the sibling failures? | **Not shown.** AX55 v1 (family C, no NCTL patch path) is explained and fixed by ordering (kuncy7 `930-09`/`778`). Family-D "carrier up, no frames" is explained by the latch-edge mechanism above (777-08). HW-3P runs family D without the NCTL patch and passes NAT traffic. NCTL remains a **candidate** only if S2.4 fails with 777-08 events logged (S2.5). | SOURCE + REL + HW-3P |

### Other public fixes checked (none adoptable)
- **`930-09` / `778`** "bring the SerDes up once the conduit is up": every hunk returns early for family D ("Family D keeps its own re-latch work"). Not applicable to the RTL8367S-VB.
- **OpenWrt main since our base:** UNIPHY fixes `ee6860ee0f`, `59f295f58f`, `62792fff96` are already in 0006–0008. `a41558d2d3` fixes ipq6018/ipq8074 clock names "as ipq5018 already does". `b7afc4baab` was already rejected (cross-device inventory). The rest are other SoCs.
- **0024 / 0025:** they address boot-time CMN PLL gating and family-D reset/settle intervals. The carrier-up-no-frames mechanism is covered by 777-08 and 0006–0009, not by them. No defect found; kept.

## 7. 1 Gbps trunk diagnostic fallback (prepared, not built, not in the image)
`patches/variants/trunk-1g-sgmii.patch` moves both trunk ends to `phy-mode = "sgmii"`
with a 1000 fixed link, as MR80X v2 and EX511 v2 ship (REL). Everything else is
unchanged (pause, GPIO 39, all patches). It is useful because it splits a 2.5 G failure
into "HSGMII/latch path" vs "everything else" with one variable. 1 G per direction
still carries a 1 G WAN. Our driver already has the vendor-identical family-D SGMII
table, and 0006 clears the UNIPHY0 SGMII mode select.

`tests/unit/test_trunk_variant.sh` (`unit-trunk-variant`) checks four things:
- The variant is not in the default series.
- It applies to the prepared tree.
- Compiled with the build's own cpp/dtc flow, the unmodified DTS reproduces the shipped DTB byte for byte (control), and the variant compiles.
- Exactly four properties change: `phy-mode` and `speed` on both trunk ends.

**BUILD only.** The variant has not run on any hardware. Use it only after S2.4 fails on the default 2.5 G image:
`patch -p1 -d build/dev/openwrt < patches/variants/trunk-1g-sgmii.patch`, rebuild, and revert before any other build.

## 8. Status of S2.8 and the image
- `ax23-selfdiag.sh` is **not part of the firmware image**: it is streamed from the checkout at test time (`ssh … sh -s < tests/hardware/ax23-selfdiag.sh`).
- S2.8 therefore needs **no rebuild** and works with the current RAM image (`f9aeb698…`, patches 0001–0027).
- It was **not part of the test set validated with that image**. Record the selfdiag git revision alongside every bundle.
- The variant and S2.8 changed no executable firmware code, so no rebuild was done.
