#!/usr/bin/env python3
"""Search for name entry labels - phase 12.
Search for MIPS lui/addiu pairs that construct VAs to key data tables.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()

def find_lui_addiu(target_va, label):
    """Find MIPS lui/addiu pairs that construct the given VA."""
    hi = (target_va >> 16) & 0xFFFF
    lo = target_va & 0xFFFF
    # If lo is negative (sign-extended), adjust hi
    if lo >= 0x8000:
        hi += 1
        lo_signed = lo - 0x10000
    else:
        lo_signed = lo
    lo_u = lo & 0xFFFF

    print("\n=== %s: VA=0x%08X, lui=0x%04X, addiu=0x%04X ===" % (label, target_va, hi, lo_u))

    hits = []
    for off in range(0x80, min(len(exe)-8, 0x300000), 4):
        insn = struct.unpack_from('<I', exe, off)[0]
        op = (insn >> 26) & 0x3F
        rt = (insn >> 16) & 0x1F
        imm = insn & 0xFFFF

        if op == 0x0F and imm == hi:  # lui rt, hi
            # Search next 20 instructions for matching addiu
            for d in range(1, 20):
                off2 = off + d * 4
                if off2 >= len(exe) - 4:
                    break
                insn2 = struct.unpack_from('<I', exe, off2)[0]
                op2 = (insn2 >> 26) & 0x3F
                rs2 = (insn2 >> 21) & 0x1F
                rt2 = (insn2 >> 16) & 0x1F
                imm2 = insn2 & 0xFFFF

                if op2 == 0x09 and rs2 == rt and imm2 == lo_u:  # addiu rt2, rt, lo
                    hits.append((off, off2, rt, rt2))
                    if len(hits) <= 10:
                        print("  lui at 0x%06X ($%d), addiu at 0x%06X ($%d)" %
                              (off, rt, off2, rt2))
                    break

    if len(hits) > 10:
        print("  ... total %d hits" % len(hits))
    elif len(hits) == 0:
        print("  No hits found")

    return hits

# Key data tables
tables = [
    (0x3C99B0 - 0x80 + 0x100000, "kana_ptr_table_0x3C99B0"),
    (0x3CA690 - 0x80 + 0x100000, "alnum_grid_0x3CA690"),
    (0x3CA770 - 0x80 + 0x100000, "mode_index_0x3CA770"),
    (0x3C93B0 - 0x80 + 0x100000, "preset_name_0x3C93B0"),
    (0x3C93C0 - 0x80 + 0x100000, "preset_name2_0x3C93C0"),
    (0x3C9600 - 0x80 + 0x100000, "symbol_ptrs_0x3C9600"),
]

for va, label in tables:
    find_lui_addiu(va, label)
