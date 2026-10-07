#!/usr/bin/env python3
"""Translate this POC's combinational CUPL subset to GALasm; no implicit pins."""
import re
from pathlib import Path


def parse(path):
    text = re.sub(r"/\*.*?\*/", "", Path(path).read_text(), flags=re.S)
    pins = {}
    for number, inverted, name in re.findall(r"PIN\s+(\d+)\s*=\s*(!?)(\w+)\s*;", text):
        pins[int(number)] = (name, bool(inverted))
    equations = dict(re.findall(r"^\s*(\w+)\s*=\s*([^;]+);", text, re.M))
    return pins, equations


def convert(source, dest):
    pins, equations = parse(source)
    names = {name: inverted for name, inverted in pins.values()}
    def token(match):
        neg, name = match.groups()
        if name not in names:
            raise ValueError(f"Unknown equation input: {name}")
        return ("/" if bool(neg) ^ names[name] else "") + name
    result = ["GAL20V8", "CYBCH376", ""]
    for start in (1, 13):
        result.append(" ".join("GND" if n == 12 else "VCC" if n == 24
                               else pins[n][0] for n in range(start, start + 12)))
    result.append("")
    for name, equation in equations.items():
        if name not in names:
            raise ValueError(f"Equation has no physical output: {name}")
        translated = re.sub(r"(!?)([A-Za-z_]\w*)", token, equation)
        translated = " ".join(translated.replace("&", "*").replace("#", "+").split())
        result.append(("/" if names[name] else "") + name + " = " + translated)
    result.extend(["", "DESCRIPTION", "Generated from cyboard-ch376.pld by tools/galasm_source.py.",
                   "CF disabled; /CHCS on pin 22, /CHLED on pin 21; FE80/FE81.", ""])
    Path(dest).write_text("\n".join(result))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("dest", type=Path)
    a = p.parse_args()
    convert(a.source, a.dest)
