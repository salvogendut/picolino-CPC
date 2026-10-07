# Sources and provenance

## Reused code

- **Cyboard for CPC**, Dimitris Kefalas, GPL-3.0-or-later.
  Local reference `../cyboard-for-cpc`, commit
  `ea19deeaf382e87b5bdd129c7dc76c5ac7fbb5a8`.
  [Repository](https://github.com/salvogendut/cyboard-for-cpc/tree/ea19deeaf382e87b5bdd129c7dc76c5ac7fbb5a8).
  The PIC source/HEX are unmodified; the reference GAL source is preserved in
  `references/`; Picolino's GAL is a derivative. The CH376 diagnostic and GALasm
  converter come from the implemented wired POC. The prior uncommitted carrier
  layout is not imported.
- **CPC_PICOROM**, Matt Callow,
  [commit ac607717b0a1ef35dfba8c50eb952f311bbf4505](https://github.com/mattcallow/CPC_PICOROM/tree/ac607717b0a1ef35dfba8c50eb952f311bbf4505).
  Reference for ROM signal allocation, firmware architecture and CH376 header.
  No RP2040 UF2, system ROM, upstream linker script or flash filesystem is
  redistributed as Pico 2 firmware. Any later source import must preserve its
  BSD/dependency notices.

New project code is GPL-3.0-or-later. The imported code retains its own notices.
The Pico SDK and external build tools remain separately obtained dependencies.
GALasm has a commercial-use restriction in its own license; it is not vendored.

## Primary technical references

- [Raspberry Pi Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf):
  module pinout, dimensions, supply and RP2350 GPIO restrictions.
- [Pico SDK](https://github.com/raspberrypi/pico-sdk/tree/2.2.0): native `pico2` target.
- [WIZnet W5100S](https://docs.wiznet.io/Product/Chip/Ethernet/W5100S): parallel host bus.
- [WIZ810Sio](https://docs.wiznet.io/Product/ioModule/WIZ810Sio): an example of an
  SPI-only module that cannot replace the selected parallel module unchanged.
- [WCH CH376 datasheet, archived by Akizuki](https://akizukidenshi.com/goodsaffix/CH376.pdf):
  parallel host protocol.
- [Ricoh 1993 General-Purpose IC Data Book, archived manufacturer publication](https://manuals.plus/m/128c28c72f864f3fdbf796c4a3b285e4149d90ba4c0854695583d874f50037de):
  original RP5C01, section 3 pages 3-1 to 3-14, and section 8 application manual.
  This is the selected RTC variant's electrical reference.
- [Ricoh RP/RF5C01A manufacturer datasheet, archived copy](https://map.grauw.nl/resources/rtc/ricoh_rp5c01.pdf):
  comparison only, including oscillator differences. The A variant is not the
  user's selected chip; do not substitute its recommended supply/oscillator data.
- [RP5C01 RTC project by Dean Netherton](https://www.dinoboards.com.au/rtc-and-f4.html):
  reference for CR2032-backed RTC integration. Circuit reference only; no layout
  or source from this project is copied.
- [Analog Devices ADM691A](https://www.analog.com/en/products/adm691a.html):
  reference backup-supervisor function; last-time-buy status checked 2026-10-07.
- [TI SN74CB3T3245](https://www.ti.com/lit/ds/symlink/sn74cb3t3245.pdf): selected
  translation/isolation part retained from the POC architecture.
- [Original Ricoh databook PDF](https://ftpmirror.your.org/pub/misc/bitsavers/components/ricoh/1993_Ricoh_General-Purpose_IC_Data_Book.pdf):
  oscillator application circuit, printed page 3-6 / PDF page 35.
- [MAX690A](https://www.analog.com/en/products/max690a.html) and
  [manufacturer datasheet](https://www.analog.com/MAX692A/datasheet): selected
  backup switch and power-fail inhibition, including exact eight-pin map.
- [Keystone 103](https://www.keyelco.com/product.cfm/THM-20mm-Holders-All-sizes/103/product_id/719):
  CR2032 holder, verified 20.49 mm terminal pitch.
- [Abracon AB38T](https://abracon.com/Resonators/AB38T.pdf): crystal load,
  lead diameter and can dimensions. PCB uses gently formed leads.
- [Kingtronics KKT trimmers](https://www.kingtronics.com/pdf/KKT-SMD-3mm-Ceramic-Trimmer-Capacitor.pdf):
  KKT330TR capacitance limits and land pattern.
- [Bourns MF-NSMF](https://www.bourns.com/docs/product-datasheets/mfnsmf.pdf):
  USB branch resettable fuse, 1206 footprint.

CAD library and 3D-model sources, local modifications and licence notices are
recorded in [the local-library README](../hardware/kicad/libraries/README.md).

Datasheets are linked, not bundled. Reuse of additional designs must include
their exact revision, verified pin map and license.

`references/import-manifest.json` records SHA-256 hashes of the unmodified
imports. `references/cyboard-pinmap.json` is extracted from the original EAGLE
board, whose SHA-256 is recorded with it. Re-import intentionally with
`python3 tools/import_interfaces.py --cyboard /path/to/cyboard-for-cpc`.
The original PIC source/HEX and GAL snapshot retain their upstream CRLF and
trailing whitespace for byte-for-byte comparison. Whitespace checks apply to
authored files; the preserved imports are checked against their hashes.
