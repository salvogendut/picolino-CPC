#!/usr/bin/env python3
"""Import reference pin maps, with their source hashes, from sibling checkouts.

Run only when deliberately updating the reference snapshot. This does not
generate a PCB or establish that a purchased module matches the reference.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cyboard", type=Path, required=True)
    args = p.parse_args()
    source = args.cyboard / "hardware/cyboard.brd"
    tree = ET.parse(source)
    names = ["CON1", "IC1", "IC2", "IC3", "W5100S-MODULE", "R1", "R2",
             *[f"R{i}" for i in range(4, 12)], "D1", "D2"]
    maps = {name: {} for name in names}
    for signal in tree.findall(".//signals/signal"):
        for ref in signal.findall("contactref"):
            if ref.get("element") in maps:
                maps[ref.get("element")][ref.get("pad")] = signal.get("name")
    snapshot = {"source": "Cyboard hardware/cyboard.brd",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "pin_maps": maps}
    (ROOT / "references/cyboard-pinmap.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    gpio_pins = dict(zip(list(range(23)) + [26, 27, 28],
        [1,2,4,5,6,7,9,10,11,12,14,15,16,17,19,20,21,22,24,25,26,27,29,31,32,34]))
    gpio_signals = {**{i: f"A{i}" for i in range(14)},
                    **{14+i: f"D{i}" for i in range(8)},
                    22: "/ROMEN", 26: "A15", 27: "ROM_LATCH", 28: "RESET_PULLDOWN"}
    ch = {"1": "GND", "3": "GND", "5": "+5V_USB", "7": "NC",
          "9": "A0", "11": "/CHCS", "13": "/RD", "15": "/WR"}
    ch.update({str(2+2*i): f"D{i}" for i in range(8)})
    interfaces = {
        "status": "Electrical reference contract; not a board netlist or fabrication release",
        "selection": {"modules": "Reference parallel modules confirmed by user 2026-10-07",
                      "rtc": "RP5C01 (not A), DIP-18 confirmed by user 2026-10-07"},
        "cpc": {"source": "Cyboard CON1 plus CPC_PICOROM J1 ROM signals",
                "pins": {**maps["CON1"], "42": "/ROMEN", "43": "ROMDIS"}},
        "pico2": {
            "source": "Pico 2 datasheet pinout; CPC_PICOROM GPIO allocation",
            "gpio": [{"gpio": g, "module_pin": gpio_pins[g], "signal": n,
                      "interface": "External 5V/3V3 translation required"}
                     for g, n in gpio_signals.items()],
            "ground_pins": [3,8,13,18,23,28,33,38], "vsys_pin": 39,
            "vbus_pin": 40, "3v3_pin": 36, "rows_mm": 17.78, "size_mm": [21,51]},
        "ch376": {"source": "CPC_PICOROM J2", "pins": ch,
                  "interface": "16-pin 2x8 parallel module; not serial-only modules"},
        "w5100s": {"source": "Cyboard W5100S-MODULE", "pins": maps["W5100S-MODULE"],
                   "unconnected_supply_outputs": [23,24],
                   "interface": "32-pin parallel module with onboard 3.3V regulator",
                   "data_series_ohms": 470,
                   "notes": "Pin 28 mode high, pin 30 mode low. Preserve Cyboard RD/WR diodes. 3.3V outputs are not connected to 5V."},
        "mouse_pic": {"source": "Cyboard IC1", "part": "PIC16F84A", "pins": maps["IC1"]},
        "mouse_buffer": {"source": "Cyboard IC3", "part": "74HCT244", "pins": maps["IC3"]},
        "rp5c01": {
            "source": "Ricoh 1993 General-Purpose IC Data Book, RP5C01 section 3",
            "package": "DIP-18", "pins": {
                "1": "/CS", "2": "CS", "3": "ADJ", "4": "A0", "5": "A1",
                "6": "A2", "7": "A3", "8": "/RD", "9": "GND", "10": "/WR",
                "11": "D0", "12": "D1", "13": "D2", "14": "D3",
                "15": "/ALARM", "16": "OSCIN", "17": "OSCOUT", "18": "VCC"},
            "proposed_connections": {"1": "/RTCCS", "2": "RTC_POWER_GOOD",
                "3": "GND", "4": "RTC_A0", "5": "RTC_A1", "6": "RTC_A2", "7": "RTC_A3",
                "8": "/RTCRD", "9": "GND", "10": "/RTCWR", "11": "D0", "12": "D1",
                "13": "D2", "14": "D3", "15": "RTC_ALARM_TEST", "16": "RTC_OSCIN",
                "17": "RTC_OSCOUT", "18": "RTC_BACKUP_VCC"},
            "address_latch": "74HCT373; D0-D3 captured on FD15 write, enable=RTCAS",
            "data_port": "FD14", "index_port": "FD15", "data_mask": "0F"}}
    (ROOT / "hardware/interfaces.json").write_text(json.dumps(interfaces, indent=2) + "\n")
    print("Imported reference maps; review changes before using them in CAD.")


if __name__ == "__main__":
    main()
