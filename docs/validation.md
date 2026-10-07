# Initial implementation validation — 2026-10-07

This report applies to the software and interface contract in the initial
`design/pico2-prototype` branch. It is not a PCB or bench-test report.

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

- Full schematic, RTC backup components, power budget and module mechanics.
- KiCad ERC, board DRC, schematic parity and routed-connectivity checks.
- RTC software and register/timing checks against the original RP5C01.
- RP2350 ROM service timing and output-disable behavior on real CPC hardware.
- RTC switchover/current/time retention and each peripheral on the prototype.

Build outputs are local under `build/`; they are not a manufacturing release.
