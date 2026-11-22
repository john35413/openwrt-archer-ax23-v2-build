#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Regression checks for the ordered first-boot safety documentation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GATE = (ROOT / "reports/FINAL_PREBOOT_GATE.md").read_text()
CHECKLIST = (ROOT / "reports/first-ram-boot-checklist.md").read_text()
HARDWARE = (ROOT / "tests/hardware/HARDWARE-TEST-PLAN.md").read_text()
GPIO = (ROOT / "reports/rtl8367-reset-trace.md").read_text()


class PrebootGate(unittest.TestCase):
    def test_four_evidence_sections_and_default_no_go(self):
        for heading in (
            "PASS — offline checks completed",
            "BLOCKED — passive hardware checks still needed",
            "BLOCKED — U-Boot console observations still needed",
            "NOT TESTED — OpenWrt runtime functionality",
        ):
            self.assertIn(heading, GATE)
        self.assertIn("Verdict: NO-GO for `bootm` today", GATE)

    def test_current_gpio39_output_is_a_preboot_blocker(self):
        self.assertRegex(GATE, r"asserts it physically low for\s+\*\*25 ms\*\*")
        self.assertIn("not proven to be a no-op", GPIO)
        self.assertIn("hard pre-boot", GPIO)
        self.assertIn("If GPIO39 is tied to", GATE)

    def test_image_facts_and_early_shell_guard_are_documented(self):
        self.assertIn("13,330,704 bytes", GATE)
        self.assertIn("6d85f2a82117008fc991ffdea54a7fc64a77f2616bdf02f5b9bcabd7a059a9ff", GATE)
        self.assertIn("config@mp02.1", GATE)
        self.assertIn("0x44000000", GATE)
        self.assertIn("rdinit=/bin/sh", CHECKLIST)
        self.assertNotRegex(CHECKLIST, r"(?m)^.*(?:Use|append|setenv).*init=/bin/sh")
        self.assertNotIn("setenv bootargs " + "$" + "{bootargs} init=/bin/sh", GATE)
        self.assertIn("never run saveenv", CHECKLIST)

    def test_rdinit_guard_stop_rule_and_real_continuation_are_documented(self):
        for document in (GATE, CHECKLIST, HARDWARE):
            self.assertIn("rdinit=/bin/sh", document)
        self.assertRegex(CHECKLIST, r"STOP\s+immediately")
        self.assertIn("Do not run `exec /init`", CHECKLIST)
        self.assertIn("built-in kernel probes/initcalls", CHECKLIST)
        self.assertIn("does not prevent switch GPIO activity", CHECKLIST)
        self.assertIn("exec /init", HARDWARE)
        self.assertIn("switch_root", HARDWARE)
        self.assertIn("procd", HARDWARE)

    def test_bootloader_addresses_are_labeled_as_source_not_device_measurements(self):
        self.assertIn("CONFIG_SYS_BOOTM_LEN", GATE)
        self.assertIn("0x4000000", GATE)
        self.assertIn("CONFIG_IPQ_NO_RELOC", GATE)
        self.assertIn("0x4A920000", GATE)
        self.assertIn("0x44000000", GATE)
        self.assertIn("0x42676008", GATE)
        self.assertIn("not measurements of", GATE)

    def test_eu_board_data_is_not_an_after_boot_rebuild_prerequisite(self):
        self.assertIn("image includes the intended EU board data already", GATE)
        self.assertIn("Do not dump ART", GATE)
        self.assertNotIn("extract-oem-bdf.sh", HARDWARE)
        self.assertNotIn("--region <EU dir>", HARDWARE)

    def test_no_initial_reset_or_wps_button_instruction(self):
        self.assertIn("Do not press Reset/WPS", GATE)
        self.assertIn("do not press reset/wps", HARDWARE.casefold())
        self.assertIn("Deferred", HARDWARE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
