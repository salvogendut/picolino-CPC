#!/usr/bin/env python3
"""Execute assembled Z80 code against a CH376 protocol model (not a CPC timing test)."""
import argparse
import re
from collections import deque
from pathlib import Path
import z80

ROOT = Path(__file__).resolve().parents[1]
DATA, CMD = 0xFE80, 0xFE81
FORBIDDEN = {0x2C, 0x2D, 0x2E, 0x34, 0x35, 0x38, 0x3C, 0x3D, 0x40, 0x4C, 0x56, 0x57}


class CH376:
    def __init__(self, fixture, failure=None, chunk=64):
        self.file = fixture
        self.failure = failure
        self.chunk_size = chunk
        self.command = 0
        self.params = []
        self.response = deque()
        self.interrupt = None
        self.position = 0
        self.remaining = 0
        self.chunk = b""
        self.trace = []
        self.mounts = 0
        self.closes = 0
        self.opened = False

    def read(self, port):
        assert port in (DATA, CMD), hex(port)
        if self.failure == "absent": return 0xFF
        if port == CMD:
            if self.failure == "busy": return 0x90
            return 0 if self.interrupt is not None else 0x80
        return self.response.popleft() if self.response else 0

    def next_chunk(self):
        if self.failure == "disconnect":
            self.interrupt = 0x16
            return
        n = min(self.remaining, len(self.file) - self.position, self.chunk_size)
        if n <= 0:
            self.interrupt = 0x14
        else:
            self.chunk = self.file[self.position:self.position+n]
            self.position += n
            self.remaining -= n
            if self.failure == "zero_chunk": self.chunk = b""
            self.interrupt = 0x1D

    def write(self, port, value):
        assert port in (DATA, CMD), hex(port)
        if port == CMD:
            assert value not in FORBIDDEN, f"Media-writing command {value:02X}"
            self.trace.append(value)
            self.command = value
            self.params = []
            self.response.clear()
            if value == 0x05:
                self.interrupt = None
                self.opened = False
            elif value == 0x01: self.response.append(0x43)
            elif value == 0x22:
                self.response.append(self.interrupt if self.interrupt is not None else 0)
                self.interrupt = None
            elif value == 0x31:
                self.mounts += 1
                self.interrupt = 0x1F if self.failure == "mount" or (self.failure == "mount_retry" and self.mounts < 3) else 0x14
            elif value == 0x32:
                self.opened = self.failure != "missing"
                self.interrupt = 0x14 if self.opened else 0x42
                self.position = 0
            elif value == 0x27:
                self.response.extend([len(self.chunk), *self.chunk])
            elif value == 0x3B:
                self.next_chunk()
            elif value not in (0x06, 0x15, 0x2F, 0x3A, 0x36):
                raise AssertionError(f"Unsupported command {value:02X}")
        else:
            self.params.append(value)
            if self.command == 0x06:
                self.response.append(value if self.failure == "echo" else value ^ 0xFF)
            elif self.command == 0x15:
                if self.failure != "mode_timeout":
                    self.response.append(0x5F if self.failure == "mode" else 0x51)
                if value == 5 and self.failure != "no_usb": self.interrupt = 0x15
                if value == 6: self.interrupt = 0x15
            elif self.command == 0x2F:
                if value == 0: assert bytes(self.params) == b"/CYBOARD.TXT\0"
            elif self.command == 0x3A and len(self.params) == 2:
                assert self.opened
                self.remaining = self.params[0] + (self.params[1] << 8)
                self.next_chunk()
            elif self.command == 0x36:
                assert value == 0, "FILE_CLOSE must not update metadata"
                self.closes += 1
                self.opened = False
                self.interrupt = 0x14


def symbols(path):
    return {name.upper(): int(address, 16) for name, address in re.findall(r"(\w+)\s+#([0-9A-Fa-f]+)", path.read_text())}


def execute(image, origin, entry, device, protected=False):
    machine = z80.Z80Machine()
    machine.set_memory_block(origin, image)
    machine.pc = entry
    machine.sp = 0x7FF0
    machine.memory[0x7FF0:0x7FF2] = bytes((0, 1))
    machine.memory[0xBB5A] = 0xC9  # firmware TXT OUTPUT return
    machine.set_breakpoint(0x100)
    machine.set_breakpoint(0xBB5A)
    machine.set_input_callback(device.read)
    machine.set_output_callback(device.write)
    output = []
    for _ in range(20000):
        machine.ticks_to_stop = 1000000
        machine.run()
        if machine.pc == 0x100:
            if protected: assert bytes(machine.memory[origin:origin+len(image)]) == image
            assert machine.sp == 0x7FF2
            return machine.a, bool(machine.f & 1), "".join(output)
        if machine.pc == 0xBB5A:
            output.append(chr(machine.a))
            # Emulate RET from the firmware entry without executing it again.
            machine.pc = machine.memory[machine.sp] | machine.memory[machine.sp+1] << 8
            machine.sp += 2
    raise AssertionError("Diagnostic did not return within instruction budget")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", type=Path, default=ROOT / "build/legacy")
    a = p.parse_args()
    fixture = (ROOT / "firmware/cpc/CYBOARD.TXT").read_bytes()
    binary = (a.build / "CYBUSB.BIN").read_bytes()
    header, payload = binary[:128], binary[128:]
    assert payload == (a.build / "CYBUSB.raw").read_bytes()
    assert header[1:12] == b"CYBUSB  BIN" and header[18] == 2
    assert int.from_bytes(header[67:69], "little") == sum(header[:67])
    for offset in (19, 24): assert int.from_bytes(header[offset:offset+2], "little") == len(payload)
    for offset in (21, 26): assert int.from_bytes(header[offset:offset+2], "little") == 0x8000
    rom = (a.build / "CYBUSB.ROM").read_bytes()
    assert len(rom) == 16384 and rom[0] == 1
    assert rom[6] == rom[9] == 0xC3  # init and RSX jump entries
    cases = [(None, fixture), ("mount_retry", fixture), ("absent", fixture),
             ("busy", fixture), ("echo", fixture), ("mode", fixture),
             ("mode_timeout", fixture), ("no_usb", fixture), ("mount", fixture),
             ("missing", fixture), ("disconnect", fixture), ("zero_chunk", fixture),
             ("corrupt", b"!" + fixture[1:]), ("short", fixture[:-1]), ("long", fixture + b"!")]
    for filename, origin, syms in (("CYBUSB.raw", 0x8000, "CYBUSB.sym"),
                                   ("CYBUSB.ROM", 0xC000, "CYBUSB-ROM.sym")):
        image = (a.build / filename).read_bytes()
        entry = symbols(a.build / syms)["DIAGNOSTIC"]
        for failure, data in cases:
            device = CH376(data, failure)
            result, carry, output = execute(image, origin, entry, device, origin == 0xC000)
            expected_success = failure in (None, "mount_retry")
            assert carry != expected_success, (filename, failure, result, output)
            assert ("PASS" in output) == expected_success, (filename, failure, output)
            if expected_success:
                assert result == 0 and device.closes == 1 and device.position == len(fixture)
                assert device.trace.count(0x3B) >= 3
            if failure == "mount_retry": assert device.mounts == 3
            if failure == "mount": assert device.mounts == 10
            print(f"PASS: {filename}: {failure or 'normal multi-chunk read'}")
        for chunk in (1, 17, 63, 128, 255):
            result, carry, output = execute(image, origin, entry, CH376(fixture, chunk=chunk), origin == 0xC000)
            assert not carry and result == 0, (filename, chunk, output)
    print("PASS: 40 executed diagnostic scenarios, including ROM immutability and no media-writing commands")


if __name__ == "__main__":
    main()
