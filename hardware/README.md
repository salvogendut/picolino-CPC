# Picolino CPC revision A0 hardware

The editable [KiCad 10 project](kicad/picolino-cpc.kicad_pro) contains a cover
sheet and four circuit sheets: bus/power, Pico ROM interface, Ethernet/mouse and
RTC. The PCB is 150 × 120 mm, two copper layers, 1.6 mm nominal thickness, with
four 3.2 mm non-plated mounting holes on a 142 × 112 mm rectangle. Nominal signal
tracks are 0.25 mm; power distribution is 0.80 mm, with pad escapes where needed.
The project minimum is 0.20 mm track/clearance and 0.30 mm drilled vias; routed
vias use 0.70/0.35 mm diameter/drill. Ground pours occupy both layers.

![Assembled prototype preview](../docs/images/picolino-cpc-3d.png)

The preview uses Raspberry Pi's official Pico 2 STEP model, local KiCad models,
and an approximate W5100S module envelope. The W5100S connector pad positions
and outline come from Cyboard's EAGLE package; its component heights are
illustrative. Check the actual selected module before manufacture. CH376 is an
external module connected to J2, so it is not included in the rendering.

## Connectors and settings

| Reference | Connection / setting |
| --- | --- |
| J1 | CPC 50-contact expansion through a short, straight-through 50-way ribbon. Pin 1 is marked; check contact numbering at both ends. |
| J2 | Reference parallel CH376 module, 2 × 8 at 2.54 mm, via short straight-through ribbon. Pin 5 supplies fused 5 V; pin 7 is unused. |
| U8 | Cyboard parallel W5100S module, two 1 × 16 sockets, 2.54 mm pitch and 25.4 mm row spacing. RJ45 faces the top edge. |
| U1 | Original Pico 2 with fitted headers; two 1 × 20 sockets, 17.78 mm row spacing. Micro-USB faces the top edge. |
| J4 | PS/2-compatible mouse in a USB-A-shaped socket. This is not a USB HID host. |
| J3 | External **regulated 5 V**: pin 1 positive, pin 2 ground. |
| JP1 | **One shunt only:** 1–2 selects CPC power; 2–3 selects external power. Change only with all power disconnected. |
| JP2 | Both shunts removed: internal CPC ROM and input-only monitor. Fit 1–2 and 3–4 together only with working RP2350 ROM firmware. |
| BT1 | CR2032, positive face up, Keystone 103 holder. No charging circuit. |
| TP1 | RTC ALARM output for calibration/diagnostics; not connected to CPC interrupt. |

J1 contact 40 (`BUSRESET_N`) and contact 41 (`RESET_N`) are separate signals.
The exact contact maps are in [interfaces.json](interfaces.json) and the PDF.
Module orientation must be checked by pin number, not ribbon wire colour.
An SPI-only WIZ810Sio cannot be fitted to U8.

External 5 V is preferred during USB-drive bring-up. JP1 prevents the selected
external supply from feeding CPC 5 V; D1 prevents Pico USB from feeding the
board supply. With external power selected, power the CPC before the board and
turn the board off first: direct peripheral buses are not hot-swap interfaces.
Q1 also disables the Pico translators when CPC 5 V is absent. Measure the full
Pico/module/mouse/USB load before selecting CPC power. F1 protects the CH376
branch, not the whole board; its 500 mA hold rating is not a regulated USB current
limit. Validate USB inrush and voltage drop with the intended drive.

## Assembly

Use the [BOM](kicad/bom.csv) with the [assembly drawing](kicad/picolino-cpc-assembly.svg)
and [schematic PDF](kicad/picolino-cpc-schematic.pdf). The standard passives are
0805; translators are SOIC-20W, supervisor SOIC-8 and Q1 SOT-23. The GAL, PIC,
HCT logic and RTC use DIP sockets. Fit the exact SN74CB3T3245 level-translating
part; an ordinary HC245 or a similarly named bus switch is not equivalent.

Program U2 from the project's GAL source and U9 with the preserved Cyboard PIC
HEX. The Pico firmware currently supplied is an input-only monitor. Leave JP2
open; enabling ROMDIS without a working ROM service prevents normal CPC boot.
Fit one power-selection shunt only. Module sockets and removable shunts are
assembly items in addition to the populated-board BOM. J1 pin 2, U2 pin 12 and
the ground pads of C4/C5 use solid plane connections because surrounding traces
leave insufficient thermal spokes. These joints need adequate soldering heat;
other plane-connected component pads retain thermal reliefs.

U13 is **MAX690AESA+**, with VOUT on pin 1 and battery input on pin 8. Its power
fail output drives the active-high RTC CS input low during backup. WDI is open
to disable the watchdog, PFI is grounded, and PFO is unused. Only the RTC is
battery powered. R20–R30 bias the RTC's bus pins to ground when the board is off.

The original **RP5C01** uses a different oscillator network from RP5C01A:
32.768 kHz crystal, 100 kΩ series resistor, 30 pF at the crystal/resistor node,
56 pF at OSCOUT and an adjustable input load. Use C0G fixed capacitors. Set and
calibrate CV1 using ALARM output mode, avoiding a probe on the crystal pins.
Validate oscillation, trim range, supply transitions and retention current on
the assembled board. The selected crystal needs leads formed to the PCB pitch;
see its BOM note. Verify sourced trimmer and module dimensions before ordering.

## Editing and validation

The native CAD is the reviewable design. `tools/pcb_design.py` records the
circuit and placement; **running `--pcb` replaces all routing**. Preserve manual
edits before regeneration. `--schematic` also regenerates project constraints,
BOM and manifest. `--libraries` needs the KiCad library directory and preserves
the separately supplied Pico STEP model. The module envelope is generated by
`tools/module_model.py`. Routing uses a local Freerouting DSN/SES exchange through
`tools/pcb_route.py`; it does not upload the design to a routing service.
`tools/pcb_finish.py` records the post-route width, edge-clearance, ground-pad
and model corrections for this revision. Its removed-stub UUID belongs to this
particular routing result; review and rerun checks after any new routing pass.

Run from the repository root using KiCad 10:

```sh
kicad-cli sch export netlist hardware/kicad/picolino-cpc.kicad_sch \
  --format kicadxml --output hardware/kicad/checks/netlist.xml
kicad-cli sch erc hardware/kicad/picolino-cpc.kicad_sch --format json \
  --output hardware/kicad/checks/erc.json --exit-code-violations
python3 tools/check_hardware.py
kicad-cli pcb drc hardware/kicad/picolino-cpc.kicad_pcb --format json \
  --output hardware/kicad/checks/drc.json --schematic-parity \
  --refill-zones --save-board --exit-code-violations
```

See [validation](../docs/validation.md) for results and pending bench work,
and [library provenance](kicad/libraries/README.md) for copied assets. No board
has been manufactured or electrically tested. Gerbers are not a release
deliverable at this stage; export them only after reviewing the actual modules,
assembly choices and the outstanding prototype checks.
