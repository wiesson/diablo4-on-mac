#!/usr/bin/env python3
"""Inspect a crash address inside a 32-bit PE, without running it.

Answers three questions that decide whether chasing more flags is worthwhile:

  * which section / file offset does the faulting address map to?
  * does the instruction match an immediate-crash pattern (`cc 0f 0b` = int3; ud2)
    whose preceding condition needs investigation?
  * which imported API does a given call site call (IAT lookup)?

Usage:
  pe-inspect.py libcef.dll --addr 0x6DE900E1 --base 0x6C7C0000
  pe-inspect.py libcef.dll --rva 0x16D00E1 --disasm 64
  pe-inspect.py libcef.dll --iat 0x197BC9E0          # VA at the PREFERRED base

Disassembly needs `pip install capstone`; everything else is stdlib only.
"""
import argparse, struct, sys


class PE:
    def __init__(self, path):
        self.d = d = open(path, 'rb').read()
        e = struct.unpack_from('<I', d, 0x3c)[0]
        if d[e:e + 4] != b'PE\0\0':
            sys.exit('not a PE file')
        self.e = e
        nsec = struct.unpack_from('<H', d, e + 6)[0]
        optsz = struct.unpack_from('<H', d, e + 20)[0]
        self.magic = struct.unpack_from('<H', d, e + 24)[0]
        off = 28 if self.magic == 0x10b else 24
        self.base = (struct.unpack_from('<I', d, e + 24 + off)[0] if self.magic == 0x10b
                     else struct.unpack_from('<Q', d, e + 24 + off)[0])
        self.sections = []
        for i in range(nsec):
            o = e + 24 + optsz + i * 40
            vs, va, rs, raw = struct.unpack_from('<IIII', d, o + 8)
            self.sections.append((d[o:o + 8].rstrip(b'\0').decode(), va, max(vs, rs), raw, rs))
        self.dirs = e + 24 + (96 if self.magic == 0x10b else 112)

    def off(self, rva):
        for name, va, size, raw, rs in self.sections:
            if va <= rva < va + size:
                return name, rva - va + raw
        return None, None

    def cstr(self, rva):
        _, o = self.off(rva)
        return self.d[o:self.d.index(b'\0', o)].decode('latin1')

    def imports(self):
        """yield (dll, symbol, iat_rva)"""
        imp = struct.unpack_from('<I', self.d, self.dirs + 8)[0]
        _, i = self.off(imp)
        while True:
            olt, ts, fc, nm, fta = struct.unpack_from('<IIIII', self.d, i)
            if not nm:
                return
            dll = self.cstr(nm)
            _, t = self.off(olt or fta)
            slot = fta
            while True:
                v = struct.unpack_from('<I', self.d, t)[0]
                if not v:
                    break
                if v & 0x80000000:
                    name = '#%d' % (v & 0xffff)
                else:
                    _, no = self.off(v)
                    name = self.d[no + 2:self.d.index(b'\0', no + 2)].decode('latin1')
                yield dll, name, slot
                t += 4
                slot += 4
            i += 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dll')
    ap.add_argument('--addr', type=lambda x: int(x, 0), help='faulting address at runtime')
    ap.add_argument('--base', type=lambda x: int(x, 0), help='module load base at runtime')
    ap.add_argument('--rva', type=lambda x: int(x, 0))
    ap.add_argument('--iat', type=lambda x: int(x, 0), help='IAT slot, as VA at the preferred base')
    ap.add_argument('--disasm', type=int, default=0, metavar='N', help='disassemble N bytes')
    a = ap.parse_args()
    pe = PE(a.dll)
    print('preferred image base %#x, %d sections' % (pe.base, len(pe.sections)))

    if a.iat is not None:
        slot = a.iat - pe.base if a.iat > pe.base else a.iat
        for dll, name, s in pe.imports():
            if s == slot:
                print('IAT %#x -> %s!%s' % (a.iat, dll, name))
                return
        print('IAT %#x: no match (delay-imported or not an import slot)' % a.iat)
        return

    rva = a.rva
    if rva is None:
        if a.addr is None or a.base is None:
            sys.exit('give --rva, or --addr together with --base')
        rva = a.addr - a.base
        print('address %#x - base %#x = RVA %#x' % (a.addr, a.base, rva))
    name, o = pe.off(rva)
    if o is None:
        sys.exit('RVA %#x is not inside any section' % rva)
    print('RVA %#x -> section %s, file offset %#x' % (rva, name, o))
    print('bytes: ' + pe.d[o:o + 16].hex(' '))
    if pe.d[o:o + 3] == b'\xcc\x0f\x0b':
        print('\n>>> cc 0f 0b = int3; ud2, consistent with an immediate-crash path.')
        print('>>> These bytes alone do not identify the failed check or its cause.')
        print('>>> Disassemble from a known function boundary to find the condition,')
        print('>>> then verify the relevant API result. See docs/technical-notes.md.')
    if a.disasm:
        try:
            from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_MODE_64
        except ImportError:
            sys.exit('\n--disasm needs: pip install capstone')
        mode = CS_MODE_32 if pe.magic == 0x10b else CS_MODE_64
        start = max(o - a.disasm // 2, 0)
        for ins in Cs(CS_ARCH_X86, mode).disasm(pe.d[start:o + a.disasm // 2], rva - (o - start)):
            mark = '   <<< FAULT' if ins.address == rva else ''
            print('%08x  %-20s %s %s%s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))


if __name__ == '__main__':
    main()
