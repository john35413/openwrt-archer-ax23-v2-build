# AX23 V2 GPIO/UART preflight — instructions

**Status: NO-GO for bootm. No physical UART or GPIO electrical measurement has been performed.**

This directory contains a Windows PowerShell 5.1+ receive-only UART recorder. It does **not** test GPIO continuity, infer electrical safety, run `bdinfo`, write the U-Boot environment, load a FIT, or flash the router.

## Mandatory hardware preconditions

- Verify exact EU V2.0 PCB and revision.
- Obtain a genuine UART adapter with verified **1.8 V signal I/O** (not merely a 1.8 V VCC supply), a high-impedance meter and appropriate passive instrument for signal/transient checks. Example: FTDI `TTL-232RG-VREG1V8-WE` with its specific manufacturer wiring datasheet.
- On an **unpowered** router, identify JP1 GND by measurement, not pad order or a photo. Community reports indicate JP1 SMD series-resistor pads may be unpopulated. Do not randomly bridge or solder them.
- With the UART adapter **disconnected**, power the router in stock firmware and passively identify TX activity and measured 1.8 V signal levels. Verify the adapter's actual I/O requirements and isolated TXD voltage separately.
- For first logging only: router GND -> adapter GND; independently verified router TX -> adapter RXD. Leave adapter TXD, VCC, RTS, CTS disconnected and insulated. **Never connect 3.3 V/5 V UART outputs to an unverified 1.8 V router input.**
- Stock UART reported at 115200 baud, 8 data bits, no parity, 1 stop bit. JP1 physical pin order and logic voltage remain unverified on our exact unit.

## Windows receive-only logging

Identify COM ports:

```powershell
[System.IO.Ports.SerialPort]::GetPortNames()
```

After completing electrical checks and connecting **receive-only**, run from this directory:

```powershell
powershell.exe -NoProfile -File .\Capture-AX23-UART-RXOnly.ps1 -Port COM4 -ElectricalChecksConfirmed
```

Replace `COM4` with the real port. `-ElectricalChecksConfirmed` is an **operator declaration**, not an automatic measurement. The script opens a local serial port, reads bytes, prints ASCII and stores raw binary logs under `Documents\AX23-UART-Logs`; press Ctrl+C to stop. It never sends UART commands. Runtime on the actual Windows PC has **not** been verified.

**Keep raw serial logs private** until identifiers/MAC/serials/keys are removed.

## GPIO26/39 remains a separate hard gate

OEM U-Boot and switch source analysis implicate GPIO26 as the RTL8367 reset, while our *current* compiled DTS configures GPIO39 active-low and the Linux driver can assert it for 25 ms. This does **not** prove the GPIO39 net harmless on the exact PCB. Only correctly identified passive GPIO/net measurements can resolve this. Do not attempt `bootm` based solely on source-level evidence or this logger.

For the complete STOP criteria, exact FIT provenance, U-Boot memory requirements, early shell `rdinit=/bin/sh` procedure and the required owner approvals, read [FINAL_PREBOOT_GATE.md](../../reports/FINAL_PREBOOT_GATE.md).

See also [UPSTREAM-CONTRIBUTION-STATUS-2026-11-22.md](../../reports/UPSTREAM-CONTRIBUTION-STATUS-2026-11-22.md) for the independent PR #2 validation boundary. This script does not modify the firmware and requires no rebuild.
