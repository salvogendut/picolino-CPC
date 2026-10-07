#!/usr/bin/env python3
"""Exhaust all 65,536 addresses and eight IORQ/RD/WR combinations."""
import argparse
import ast
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from galasm_source import parse

ROOT = Path(__file__).resolve().parents[1]
MASK = (1 << 65536) - 1


def addresses(predicate):
    data = bytearray(8192)
    for address in range(65536):
        if predicate(address):
            data[address // 8] |= 1 << (address % 8)
    return int.from_bytes(data, "little")


def expression(text, values):
    tree = ast.parse(text.strip(), mode="eval")
    def visit(node):
        if isinstance(node, ast.Expression): return visit(node.body)
        if isinstance(node, ast.Name): return values[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert): return ~visit(node.operand) & MASK
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd): return visit(node.left) & visit(node.right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr): return visit(node.left) | visit(node.right)
        raise ValueError(f"Unsupported equation syntax: {ast.dump(node)}")
    return visit(tree)


def cupl(equations, values, name):
    return expression(" ".join(equations[name].replace("!", "~").replace("#", "|").split()), values)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", type=Path, default=ROOT / "build/legacy")
    a = p.parse_args()
    pins, equations = parse(ROOT / "firmware/gal/picolino.pld")
    _, old = parse(ROOT / "references/cyboard-original.pld")
    assert {n: v for n, v in pins.items() if n < 15 or n == 23} == {
        n: v for n, v in parse(ROOT / "references/cyboard-original.pld")[0].items() if n < 15 or n == 23}
    generated = (a.build / "picolino.pld").read_text()
    gal_equations = re.findall(r"^(/?)(\w+) = (.+)$", generated, re.M)
    assert len(gal_equations) == 8
    values = {f"A{i}": addresses(lambda addr, bit=i: bool(addr & (1 << bit))) for i in range(10)}
    values["A1X"] = addresses(lambda addr: addr >> 10 == 63)
    ch = addresses(lambda addr: addr in (0xFE80, 0xFE81))
    for cycle in range(8):
        iorq, rd, wr = (bool(cycle & (1 << i)) for i in range(3))
        values.update(IOREQ=MASK if iorq else 0, RD=MASK if rd else 0, WR=MASK if wr else 0)
        expected = {
            "CHCS": ch if iorq else 0, "CHLED": ch if iorq else 0, "RTCCS": addresses(lambda addr: iorq and addr == 0xFD14),
            "W5CS": addresses(lambda addr: iorq and 0xFD20 <= addr <= 0xFD23),
            "PINT": addresses(lambda addr: iorq and rd and not wr and addr == 0xFD10),
            "RTCAS": addresses(lambda addr: iorq and wr and not rd and addr == 0xFD15),
            "RTCWR": addresses(lambda addr: iorq and wr and not rd and addr == 0xFD14),
            "RTCRD": addresses(lambda addr: iorq and rd and not wr and addr == 0xFD14),
        }
        for name, want in expected.items():
            assert cupl(equations, values, name) == want, (cycle, name)
        for name in ("W5CS", "PINT", "RTCAS"):
            assert cupl(old, values, name) == cupl(equations, values, name), (cycle, name, "regression")
        physical = dict(values)
        for pin, (name, inverted) in pins.items():
            if name in physical and inverted:
                physical[name] ^= MASK
        for inv, name, eq in gal_equations:
            raw = expression(eq.replace("/", "~").replace("*", "&").replace("+", "|"), physical)
            pin_inverted = next(inverted for n, (v, inverted) in pins.items() if v == name)
            actual_level = raw ^ (MASK if inv else 0)
            assert actual_level == expected[name] ^ (MASK if pin_inverted else 0), (cycle, name, "GALasm polarity")
    jed = (a.build / "picolino.jed").read_bytes()
    text = jed.decode("ascii")
    count = int(re.search(r"\*?QF(\d+)", text).group(1))
    assert count == 2706
    default = int(re.search(r"\*?F([01])", text).group(1))
    fuses = [default] * count
    for start, bits in re.findall(r"L(\d+)\s+([01\s]+)\*", text):
        bits = [int(bit) for bit in bits if bit in "01"]
        fuses[int(start):int(start)+len(bits)] = bits
    packed = [sum(bit << j for j, bit in enumerate(fuses[i:i+8])) for i in range(0, count, 8)]
    assert sum(packed) & 0xFFFF == int(re.search(r"\*C([0-9A-Fa-f]{4})", text).group(1), 16)
    assert sum(jed[jed.index(b'\x02'):jed.index(b'\x03')+1]) & 0xFFFF == int(jed.split(b'\x03')[1].strip(), 16)
    pin_report = (a.build / "picolino.pin").read_text()
    for pin in range(15, 23):
        assert re.search(rf"\s{pin}\s+\|.*\| Output", pin_report)
    print("PASS: 524,288 bus states; preserved Ethernet/mouse decode; new RTC decode; GALasm pin polarity; JEDEC checksums")


if __name__ == "__main__":
    main()
