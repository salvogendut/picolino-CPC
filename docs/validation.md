# Prototype design validation — 2026-10-07

This report applies to revision A0 on `design/pico2-prototype`. It records
software and CAD checks. No physical prototype has been tested.

| Check | Result |
| --- | --- |
| GAL20V8 compilation | GALasm 2.1, simple combinatorial mode, successful |
| Address decoding | All 65,536 addresses × 8 IORQ/RD/WR states pass |
| Compatibility | Original Ethernet, mouse and RTC address-latch strobes preserved |
| New RTC signals | FD14 chip-select/read/write and FD15 address-latch decode pass |
| GAL conversion | Physical pin polarity and JEDEC checksums pass |
| CPC CH376 assembly | RASM 3.2.1: 993-byte diagnostic and 16 KiB extension ROM |
| CH376 emulation | 40 executed Z80 scenarios pass with z80 1.0.0 |
| Interface contract | Source pin maps and compiled Pico GPIO header agree |
| Pico 2 firmware | Builds with Pico SDK 2.2.0, Arm GCC 14.2.1, warnings treated as errors |
| UF2 inspection | picotool reports target RP2350, ARM Secure, board pico2 |

The GAL test compares inherited peripheral equations against the preserved
Cyboard source. It evaluates both CUPL logic and converted GALasm polarity;
it does not electrically exercise a programmed GAL or simulate its fuse matrix.

The CH376 tests execute the assembled RAM and ROM programs against a peripheral
model. They cover normal reads, varying chunk sizes, retries, absent/busy media,
timeouts, missing/corrupt files and disconnects. They verify that the ROM image
is unchanged and that the diagnostic sends no media-writing commands. The model
does not validate physical CH376 timing or broad USB-drive compatibility.

The Pico target is an input-only diagnostic. Its UF2 is approximately 30 KiB
of program payload, with no CPC ROM service or ROM images. USB serial supplies
slow snapshots, not a logic-analyser trace. The design must allow input sensing
while ROMDIS/data-output enable remain inactive for this diagnostic mode.

## Remaining validation

- Actual module/socket fit, cable orientation and full power budget.
- RTC software and register/timing checks against the original RP5C01.
- RP2350 ROM service timing and output-disable behavior on real CPC hardware.
- RTC switchover/current/time retention and each peripheral on the prototype.

## CAD checks

Toolchain: KiCad 10.0.6 (Fedora Flatpak), local Freerouting 2.5.0, Java 25.
The local router's optional optimization phase was disabled; acceptance uses
KiCad's filled-board DRC and schematic parity, not the router's score.

| CAD check | Result |
| --- | --- |
| Schematic ERC | 0 violations |
| Filled-board DRC | 0 violations |
| Unrouted connections | 0 |
| Schematic/PCB parity | 0 mismatches |
| Independent pin-map/topology checks | Pass |
| Schematic and 3D inspection | Completed; module fit still requires the physical parts |

Router-created sub-0.20 mm tracks were widened to 0.20 mm and rechecked.
A RESET trace was moved inward for 0.50 mm board-edge clearance, and a 0.06 mm
unused stub was removed. Four crowded through-hole ground pads now use solid
plane connections in place of incomplete thermals; the other pads retain
thermal relief. No DRC exclusions were added to hide these issues.

Independent checks compare the exported netlist to the imported CPC, PIC,
W5100S and CH376 pin maps, Pico GPIO allocation and GAL physical pins. They also
verify the RTC latch, supervisor, oscillator, reset diode and power jumpers,
and compare module pad coordinates to the source package. These checks help
catch pin-map mistakes that matching schematic and PCB files alone cannot find.

The schematic PDF and KiCad render were visually inspected. The project carries
local footprints/models and explicit track, clearance, drill and board-edge
rules. Final machine-readable reports are in `hardware/kicad/checks/`;
SHA-256 hashes bind them and the exported views to the delivered CAD.

The RTC access timing still needs measurement: the original RP5C01 requires
longer strobes than many modern bus devices, and the GAL does not stretch CPC
cycles. The ROM firmware currently monitors inputs only. RTC battery switching,
trim range/startup, USB inrush and powered/unpowered bus behaviour must be tested
on hardware. A clean ERC/DRC does not establish any of these behaviours.

Build outputs are local under `build/`; this is not a manufacturing release.
