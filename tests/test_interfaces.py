#!/usr/bin/env python3
"""Check inherited pin maps and compile the firmware GPIO contract on the host."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "hardware/interfaces.json").read_text())
source = json.loads((ROOT / "references/cyboard-pinmap.json").read_text())["pin_maps"]
for name, ref in (("mouse_pic", "IC1"), ("mouse_buffer", "IC3"), ("w5100s", "W5100S-MODULE")):
    assert data[name]["pins"] == source[ref], (name, "reference drift")
for pin, net in source["CON1"].items():
    assert data["cpc"]["pins"][pin] == net
assert data["cpc"]["pins"]["40"] == "/BUSRESET"
assert data["cpc"]["pins"]["41"] == "/RESET"
pico = data["pico2"]["gpio"]
assert len({p["gpio"] for p in pico}) == len({p["module_pin"] for p in pico}) == 26
assert not ({p["module_pin"] for p in pico} & set(data["pico2"]["ground_pins"]))
assert data["rp5c01"]["pins"]["1"] == "/CS" and data["rp5c01"]["pins"]["2"] == "CS"
assert data["rp5c01"]["proposed_connections"]["2"] == "RTC_POWER_GOOD"
assert data["w5100s"]["unconnected_supply_outputs"] == [23,24]
assert all(data["w5100s"]["pins"][str(p)] != "VCC" for p in (23,24))
assert data["ch376"]["pins"]["7"] == "NC"
assert [data["ch376"]["pins"][str(2+2*i)] for i in range(8)] == [f"D{i}" for i in range(8)]
# Compile, rather than regex-parse, the actual firmware header used by RP2350.
with tempfile.TemporaryDirectory() as tmp:
    program = Path(tmp) / "contract.c"
    program.write_text('''#include <stdio.h>
#include "board_pins.h"
int main(void) {
 printf("%u %u %u %u %u %u %u %u %u\\n", PICOLINO_ADDRESS_FIRST,
 PICOLINO_ADDRESS_COUNT, PICOLINO_DATA_FIRST, PICOLINO_DATA_COUNT,
 PICOLINO_ROMEN_GPIO, PICOLINO_A15_GPIO, PICOLINO_LATCH_GPIO,
 PICOLINO_RESET_GPIO, (unsigned)PICOLINO_BUS_MASK);
}
''')
    exe = Path(tmp) / "contract"
    subprocess.run(["cc", "-std=c11", "-Wall", "-Werror", "-I" + str(ROOT / "firmware/pico2"), str(program), "-o", str(exe)], check=True)
    a, an, d, dn, re, a15, latch, reset, mask = map(int, subprocess.check_output([str(exe)], text=True).split())
    expected = {**{a+i:f"A{i}" for i in range(an)}, **{d+i:f"D{i}" for i in range(dn)},
                re:"/ROMEN", a15:"A15", latch:"ROM_LATCH", reset:"RESET_PULLDOWN"}
    assert {p["gpio"]:p["signal"] for p in pico} == expected
    assert mask == sum(1 << g for g in expected)
print("PASS: reference peripheral maps; distinct resets; RTC select polarity; 26 Pico 2 GPIOs match compiled firmware")
