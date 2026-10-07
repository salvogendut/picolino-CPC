#!/usr/bin/env python3
"""Build Picolino GAL and inherited CPC CH376 diagnostics."""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path
from galasm_source import convert

ROOT = Path(__file__).resolve().parents[1]


def amsdos(data):
    h = bytearray(128)
    h[1:9] = b"CYBUSB  "
    h[9:12] = b"BIN"
    h[18] = 2
    for offset, value in ((19, len(data)), (21, 0x8000), (24, len(data)), (26, 0x8000)):
        struct.pack_into("<H", h, offset, value)
    h[64:67] = len(data).to_bytes(3, "little")
    struct.pack_into("<H", h, 67, sum(h[:67]))
    return h + data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rasm", default="rasm")
    p.add_argument("--galasm", default="galasm")
    p.add_argument("--out", type=Path, default=ROOT / "build/legacy")
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for tool in (a.rasm, a.galasm):
        if shutil.which(tool) is None:
            p.error(f"Tool not found: {tool}; see README.md for installation/build instructions")
    convert(ROOT / "firmware/gal/picolino.pld", out / "picolino.pld")
    subprocess.run([a.galasm, str(out / "picolino.pld")], check=True)
    for source, binary, symbols in (("diagnostic.asm", "CYBUSB.raw", "CYBUSB.sym"),
                                    ("rom.asm", "CYBUSB.ROM", "CYBUSB-ROM.sym")):
        subprocess.run([a.rasm, str(ROOT / "firmware/cpc" / source), "-amper", f"-I{ROOT / 'firmware/cpc'}",
                        "-ob", str(out / binary), "-s", "-os", str(out / symbols)], check=True)
    raw = (out / "CYBUSB.raw").read_bytes()
    binary = amsdos(raw)
    assert len(binary) == 128 + len(raw)
    (out / "CYBUSB.BIN").write_bytes(binary)
    shutil.copyfile(ROOT / "firmware/cpc/CYBOARD.TXT", out / "CYBOARD.TXT")
    files = ["CYBUSB.BIN", "CYBUSB.ROM", "CYBOARD.TXT", "picolino.jed"]
    manifest = {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in files}
    (out / "SHA256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Picolino legacy artifacts: {out}")


if __name__ == "__main__":
    main()
