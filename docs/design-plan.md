# Revision A implementation plan

## Accepted product requirements

- New repository and a new combined PCB, not an add-on requiring a Cyboard.
- Pico 2 / RP2350 module, carrying forward the ROM-emulation objective.
- CH376 USB storage module, W5100S Ethernet module, PIC mouse controller.
- Original RP5C01 in DIP-18 with replaceable CR2032 holder.
- Reference parallel CH376 and W5100S modules, confirmed 2026-10-07.
- Reuse proven interfaces where compatible, with source/license attribution.

## Current deliverables

- [x] Record architecture, compatibility changes and reference pin assignments.
- [x] Import the original PIC source/HEX and CH376 diagnostic with provenance.
- [x] Implement RP5C01-oriented GAL decode without changing mouse/Ethernet ports.
- [x] Add a Pico 2 native input-only bring-up firmware target.
- [x] Confirm reference parallel modules and RP5C01 DIP-18 with the user.
- [x] Select backup supervisor, crystal, battery holder and power architecture.
- [x] Create complete native KiCad schematic and local part libraries.
- [ ] Review RTC power-fail/write inhibition and CPC bus timing.
- [ ] Port and validate ROM serving on RP2350; do not reuse the RP2040 UF2.
- [ ] Implement/test RP5C01 CPC driver and diagnostic.
- [x] Place and route the combined PCB using reference connector geometry.
- [x] Pass ERC, DRC, schematic parity and independent pin-map checks.
- [x] Export schematic PDF, BOM, assembly drawing, 3D views and hashes.
- [ ] Check actual module fit and issue a reviewed Gerber/drill package.
- [ ] Bench-test power, ROM timing, USB, Ethernet, mouse and battery retention.

The checked boxes describe repository implementation, not physical validation.
Manufacturing or ordering boards is not part of this CAD deliverable.
