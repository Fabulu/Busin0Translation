#!/usr/bin/env python3
"""
MIPS R5900 disassembler focused on text renderer region of Busin 0 EXE.
Searches for display-width limits, glyph width lookups, and truncation logic.
"""
import struct
import sys
from collections import defaultdict

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
# Text renderer region
FILE_START = 0x202000
FILE_END   = 0x210000
VA_BASE    = 0x302000  # VA = file_offset - 0x80 + 0x00100000

# Extended search regions for width tables
WIDE_FILE_START = 0x1F0000
WIDE_FILE_END   = 0x220000

def file_to_va(foff):
    return foff - 0x80 + 0x00100000

def va_to_file(va):
    return va - 0x00100000 + 0x80

# MIPS instruction decode
def decode_r(inst):
    rs = (inst >> 21) & 0x1F
    rt = (inst >> 16) & 0x1F
    rd = (inst >> 11) & 0x1F
    sa = (inst >> 6)  & 0x1F
    fn = inst & 0x3F
    return rs, rt, rd, sa, fn

def decode_i(inst):
    rs = (inst >> 21) & 0x1F
    rt = (inst >> 16) & 0x1F
    imm = inst & 0xFFFF
    simm = imm if imm < 0x8000 else imm - 0x10000
    return rs, rt, imm, simm

def decode_j(inst):
    return inst & 0x03FFFFFF

REG_NAMES = [
    "zero","at","v0","v1","a0","a1","a2","a3",
    "t0","t1","t2","t3","t4","t5","t6","t7",
    "s0","s1","s2","s3","s4","s5","s6","s7",
    "t8","t9","k0","k1","gp","sp","fp","ra"
]

def reg(n):
    return "$" + REG_NAMES[n]

# Target constants we're interested in
INTERESTING_CONSTANTS = {
    0x04: "DISPLAY_TEXT opcode?",
    0x0C: "12px glyph width",
    0x0D: "13px width",
    0x0E: "14px width",
    0x10: "16px width",
    0x12: "18 chars/line",
    0x14: "20 chars",
    0xD8: "216px = 12*18",
    0xDA: "218px",
    0xE0: "224px",
    0xF0: "240px",
    0xFC: "252px",
    0x100: "256px",
    0x120: "288px",
    0x150: "336px",
    0x168: "360px",
    0x180: "384px display width?",
    0x1C0: "448px",
    0x1E0: "480px",
    0x200: "512px",
    0x02: "2 lines",
    0x03: "3 lines",
    0x04: "4 lines",
    0x05: "5 lines",
}

def disassemble_one(inst, va):
    """Return (mnemonic, operands_str, annotation)"""
    op = (inst >> 26) & 0x3F
    ann = ""

    if inst == 0:
        return "nop", "", ""

    if op == 0:  # SPECIAL
        rs, rt, rd, sa, fn = decode_r(inst)
        specials = {
            0x00: "sll", 0x02: "srl", 0x03: "sra",
            0x04: "sllv", 0x06: "srlv", 0x07: "srav",
            0x08: "jr", 0x09: "jalr",
            0x0C: "syscall", 0x0D: "break",
            0x10: "mfhi", 0x11: "mthi", 0x12: "mflo", 0x13: "mtlo",
            0x18: "mult", 0x19: "multu", 0x1A: "div", 0x1B: "divu",
            0x20: "add", 0x21: "addu", 0x22: "sub", 0x23: "subu",
            0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor",
            0x2A: "slt", 0x2B: "sltu",
        }
        mnem = specials.get(fn, f"special_{fn:02x}")
        if fn == 0x08:  # jr
            return mnem, reg(rs), ""
        elif fn == 0x09:  # jalr
            return mnem, f"{reg(rd)}, {reg(rs)}", ""
        elif fn in (0x00, 0x02, 0x03):  # shifts
            if sa in INTERESTING_CONSTANTS:
                ann = f"shift by {sa} ({INTERESTING_CONSTANTS[sa]})"
            return mnem, f"{reg(rd)}, {reg(rt)}, {sa}", ann
        elif fn in (0x18, 0x19, 0x1A, 0x1B):  # mult/div
            return mnem, f"{reg(rs)}, {reg(rt)}", ""
        elif fn in (0x10, 0x12):  # mfhi/mflo
            return mnem, reg(rd), ""
        else:
            return mnem, f"{reg(rd)}, {reg(rs)}, {reg(rt)}", ""

    elif op == 1:  # REGIMM
        rs, rt, imm, simm = decode_i(inst)
        target = va + 4 + (simm << 2)
        regimm = {0: "bltz", 1: "bgez", 16: "bltzal", 17: "bgezal"}
        mnem = regimm.get(rt, f"regimm_{rt}")
        return mnem, f"{reg(rs)}, 0x{target:08X}", ""

    elif op == 2:  # j
        tgt = decode_j(inst)
        addr = (va & 0xF0000000) | (tgt << 2)
        return "j", f"0x{addr:08X}", ""

    elif op == 3:  # jal
        tgt = decode_j(inst)
        addr = (va & 0xF0000000) | (tgt << 2)
        return "jal", f"0x{addr:08X}", ""

    elif op in (4, 5, 6, 7):  # BEQ, BNE, BLEZ, BGTZ
        rs, rt, imm, simm = decode_i(inst)
        target = va + 4 + (simm << 2)
        names = {4: "beq", 5: "bne", 6: "blez", 7: "bgtz"}
        mnem = names[op]
        if op in (4, 5):
            return mnem, f"{reg(rs)}, {reg(rt)}, 0x{target:08X}", ""
        else:
            return mnem, f"{reg(rs)}, 0x{target:08X}", ""

    elif op == 8:  # ADDI
        rs, rt, imm, simm = decode_i(inst)
        ann = INTERESTING_CONSTANTS.get(simm & 0xFFFF, INTERESTING_CONSTANTS.get(simm, ""))
        return "addi", f"{reg(rt)}, {reg(rs)}, {simm}", ann

    elif op == 9:  # ADDIU
        rs, rt, imm, simm = decode_i(inst)
        ann = INTERESTING_CONSTANTS.get(imm, INTERESTING_CONSTANTS.get(simm, ""))
        return "addiu", f"{reg(rt)}, {reg(rs)}, {simm}", ann

    elif op == 0x0A:  # SLTI
        rs, rt, imm, simm = decode_i(inst)
        ann = INTERESTING_CONSTANTS.get(simm & 0xFFFF, INTERESTING_CONSTANTS.get(simm, ""))
        return "slti", f"{reg(rt)}, {reg(rs)}, {simm}", ann

    elif op == 0x0B:  # SLTIU
        rs, rt, imm, simm = decode_i(inst)
        ann = INTERESTING_CONSTANTS.get(imm, "")
        return "sltiu", f"{reg(rt)}, {reg(rs)}, {simm}", ann

    elif op == 0x0C:  # ANDI
        rs, rt, imm, simm = decode_i(inst)
        return "andi", f"{reg(rt)}, {reg(rs)}, 0x{imm:04X}", ""

    elif op == 0x0D:  # ORI
        rs, rt, imm, simm = decode_i(inst)
        ann = INTERESTING_CONSTANTS.get(imm, "")
        return "ori", f"{reg(rt)}, {reg(rs)}, 0x{imm:04X}", ann

    elif op == 0x0F:  # LUI
        rs, rt, imm, simm = decode_i(inst)
        return "lui", f"{reg(rt)}, 0x{imm:04X}", f"= 0x{imm:04X}0000"

    elif op in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26):  # loads
        rs, rt, imm, simm = decode_i(inst)
        names = {0x20:"lb", 0x21:"lh", 0x22:"lwl", 0x23:"lw", 0x24:"lbu", 0x25:"lhu", 0x26:"lwr"}
        mnem = names[op]
        return mnem, f"{reg(rt)}, {simm}({reg(rs)})", ""

    elif op in (0x28, 0x29, 0x2A, 0x2B, 0x2E):  # stores
        rs, rt, imm, simm = decode_i(inst)
        names = {0x28:"sb", 0x29:"sh", 0x2A:"swl", 0x2B:"sw", 0x2E:"swr"}
        mnem = names[op]
        return mnem, f"{reg(rt)}, {simm}({reg(rs)})", ""

    else:
        return f"op_{op:02x}", f"0x{inst:08X}", ""

    return f"unk", f"0x{inst:08X}", ""


def main():
    with open(EXE_PATH, "rb") as f:
        # Read the renderer region
        f.seek(FILE_START)
        data = f.read(FILE_END - FILE_START)

        # Also read wider region for context
        f.seek(WIDE_FILE_START)
        wide_data = f.read(WIDE_FILE_END - WIDE_FILE_START)

    print(f"=== MIPS Disassembly of Text Renderer Region ===")
    print(f"File: {FILE_START:#x} - {FILE_END:#x}")
    print(f"VA:   {file_to_va(FILE_START):#x} - {file_to_va(FILE_END):#x}")
    print(f"Size: {len(data)} bytes = {len(data)//4} instructions")
    print()

    # ---- PASS 1: Find all interesting instructions ----
    interesting_hits = []
    branch_targets = set()
    jal_targets = set()
    lui_values = {}  # track LUI for building full addresses

    for i in range(0, len(data), 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        mnem, ops, ann = disassemble_one(inst, va)

        op = (inst >> 26) & 0x3F
        rs, rt, imm, simm = decode_i(inst)

        # Track JAL targets
        if op == 3:
            tgt = decode_j(inst)
            addr = (va & 0xF0000000) | (tgt << 2)
            jal_targets.add(addr)

        # Track branch targets
        if op in (4, 5, 6, 7, 1):
            target = va + 4 + (simm << 2)
            branch_targets.add(target)

        # Track LUI
        if op == 0x0F:
            lui_values[va] = (rt, imm)

        # Check for interesting immediates in ADDI/ADDIU/SLTI/SLTIU/ORI
        is_interesting = False
        if op in (8, 9, 0x0A, 0x0B):
            val = simm if op in (8, 9, 0x0A) else imm
            uval = imm
            # Check pixel width constants
            if uval in (0x0C, 0x0D, 0x0E, 0x10, 0x12, 0x14,
                        0xD8, 0xDA, 0xE0, 0xF0, 0xFC,
                        0x100, 0x120, 0x150, 0x168, 0x180, 0x1C0, 0x1E0, 0x200):
                is_interesting = True
            # Check small line counts
            if op in (0x0A, 0x0B) and uval in (2, 3, 4, 5, 6):
                is_interesting = True

        # Check comparisons (SLTI) specifically
        if op == 0x0A:
            is_interesting = True  # all SLTI are interesting in renderer

        # Check SLL by 1 (multiply by 2 for halfword index)
        if op == 0 and (inst & 0x3F) == 0:
            sa = (inst >> 6) & 0x1F
            if sa in (1, 2, 3, 4):
                pass  # common, skip unless near other interesting code

        if is_interesting and ann:
            interesting_hits.append((va, inst, mnem, ops, ann))

    # ---- Print interesting immediate hits ----
    print("=" * 80)
    print("INTERESTING CONSTANTS IN RENDERER REGION")
    print("=" * 80)
    for va, inst, mnem, ops, ann in interesting_hits:
        print(f"  0x{va:08X}: {inst:08X}  {mnem:8s} {ops:40s} ; {ann}")
    print(f"\nTotal: {len(interesting_hits)} hits")
    print()

    # ---- PASS 2: Find SLTI instructions (comparison/limit checks) ----
    print("=" * 80)
    print("ALL SLTI / SLTIU INSTRUCTIONS (limit checks)")
    print("=" * 80)
    slti_hits = []
    for i in range(0, len(data), 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        op = (inst >> 26) & 0x3F
        if op in (0x0A, 0x0B):
            mnem, ops, ann = disassemble_one(inst, va)
            rs, rt, imm, simm = decode_i(inst)
            val = simm if op == 0x0A else imm
            print(f"  0x{va:08X}: {inst:08X}  {mnem:8s} {ops:40s} ; compare {reg(rs)} < {val}")
            slti_hits.append((va, val, rs, rt))
    print(f"\nTotal SLTI/SLTIU: {len(slti_hits)}")
    print()

    # ---- PASS 3: Find LUI + ADDIU/ORI pairs that build addresses ----
    print("=" * 80)
    print("LUI + lower pairs (potential table/data addresses)")
    print("=" * 80)
    for i in range(0, len(data) - 4, 4):
        inst1 = struct.unpack_from("<I", data, i)[0]
        inst2 = struct.unpack_from("<I", data, i + 4)[0]
        va1 = file_to_va(FILE_START + i)
        op1 = (inst1 >> 26) & 0x3F
        op2 = (inst2 >> 26) & 0x3F

        if op1 == 0x0F:  # LUI
            rt1 = (inst1 >> 16) & 0x1F
            hi = inst1 & 0xFFFF

            if op2 in (9, 0x0D):  # ADDIU or ORI
                rs2 = (inst2 >> 21) & 0x1F
                rt2 = (inst2 >> 16) & 0x1F
                lo = inst2 & 0xFFFF
                if rs2 == rt1:
                    if op2 == 9:  # ADDIU (sign-extended)
                        slo = lo if lo < 0x8000 else lo - 0x10000
                        full_addr = (hi << 16) + slo
                    else:  # ORI
                        full_addr = (hi << 16) | lo
                    # Only show addresses in plausible EXE/RAM range
                    if 0x100000 <= full_addr <= 0x500000 or 0x00300000 <= full_addr <= 0x00500000:
                        print(f"  0x{va1:08X}: lui+{'addiu' if op2==9 else 'ori'} {reg(rt1)} = 0x{full_addr:08X} (file ~0x{va_to_file(full_addr):06X})")
    print()

    # ---- PASS 4: Find function prologues (addiu sp, sp, -N) in region ----
    print("=" * 80)
    print("FUNCTION PROLOGUES (addiu $sp, $sp, -N)")
    print("=" * 80)
    functions = []
    for i in range(0, len(data), 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        op = (inst >> 26) & 0x3F
        if op == 9:  # ADDIU
            rs, rt, imm, simm = decode_i(inst)
            if rs == 29 and rt == 29 and simm < 0:  # sp, sp, -N
                functions.append((va, -simm))
                # Check if this is also a JAL target
                is_target = "<<< CALLED" if va in jal_targets else ""
                print(f"  0x{va:08X}: frame size {-simm:4d} bytes  {is_target}")
    print(f"\nTotal functions: {len(functions)}")
    print()

    # ---- PASS 5: Detailed disassembly around interesting SLTI values ----
    # Focus on SLTI with pixel-width-like values
    WIDTH_LIKE = set()
    for va, val, rs_reg, rt_reg in slti_hits:
        if 10 <= abs(val) <= 600 or val in (2, 3, 4, 5, 6):
            WIDTH_LIKE.add(va)

    print("=" * 80)
    print("CONTEXT AROUND WIDTH/LIMIT COMPARISONS")
    print("=" * 80)
    for target_va in sorted(WIDTH_LIKE):
        foff = target_va - file_to_va(FILE_START)
        start = max(0, foff - 40)  # 10 instructions before
        end = min(len(data), foff + 44)  # 10 instructions after
        print(f"\n--- Around 0x{target_va:08X} ---")
        for j in range(start, end, 4):
            inst = struct.unpack_from("<I", data, j)[0]
            va = file_to_va(FILE_START + j)
            mnem, ops, ann = disassemble_one(inst, va)
            marker = ">>>" if va == target_va else "   "
            ann_str = f" ; {ann}" if ann else ""
            print(f"  {marker} 0x{va:08X}: {inst:08X}  {mnem:8s} {ops}{ann_str}")
    print()

    # ---- PASS 6: Search for opcode 0x0004 dispatch ----
    print("=" * 80)
    print("SEARCHING FOR OPCODE 0x0004 (DISPLAY_TEXT) DISPATCH")
    print("=" * 80)
    # Look for: comparison with 4, followed by branch
    for i in range(0, len(data) - 8, 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        op = (inst >> 26) & 0x3F

        # ADDIU rX, rY, 0xFFFC (-4) — common pattern: sub 4 then check zero
        if op == 9:
            rs, rt, imm, simm = decode_i(inst)
            if simm == -4 and rs != 29:  # not stack
                next_inst = struct.unpack_from("<I", data, i + 4)[0]
                next_op = (next_inst >> 26) & 0x3F
                if next_op in (4, 5):  # BEQ/BNE
                    print(f"  0x{va:08X}: addiu+beq/bne pattern (subtract 4, branch)")
                    # Show context
                    for j in range(max(0, i-12), min(len(data), i+24), 4):
                        ci = struct.unpack_from("<I", data, j)[0]
                        cva = file_to_va(FILE_START + j)
                        m, o, a = disassemble_one(ci, cva)
                        print(f"    0x{cva:08X}: {ci:08X}  {m:8s} {o}")

        # SLTI rX, rY, 5 — checking if opcode < 5 (opcodes 0-4)
        if op == 0x0A:
            rs, rt, imm, simm = decode_i(inst)
            if simm in (4, 5, 8, 16, 32):
                # Could be switch table bound check
                next_inst = struct.unpack_from("<I", data, i + 4)[0]
                next_op = (next_inst >> 26) & 0x3F
                if next_op in (4, 5):
                    print(f"  0x{va:08X}: slti {reg(rt)}, {reg(rs)}, {simm} + branch (switch bound?)")
    print()

    # ---- PASS 7: Search for jump tables (SLL $rX, $rY, 2 + ADDU + JR) ----
    print("=" * 80)
    print("JUMP TABLE PATTERNS (sll+addu+jr or sll+addu+lw+jr)")
    print("=" * 80)
    for i in range(0, len(data) - 16, 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        op = (inst >> 26) & 0x3F
        if op == 0 and (inst & 0x3F) == 0:  # SLL
            sa = (inst >> 6) & 0x1F
            if sa == 2:  # SLL by 2 = multiply by 4 (word index)
                # Check next few instructions for ADDU + LW + JR pattern
                for k in range(1, 5):
                    if i + k*4 >= len(data):
                        break
                    check = struct.unpack_from("<I", data, i + k*4)[0]
                    check_op = (check >> 26) & 0x3F
                    if check_op == 0 and (check & 0x3F) == 0x08:  # JR
                        print(f"  0x{va:08X}: SLL by 2 ... JR at +{k}")
                        for j in range(max(0, i-8), min(len(data), i+(k+2)*4), 4):
                            ci = struct.unpack_from("<I", data, j)[0]
                            cva = file_to_va(FILE_START + j)
                            m, o, a = disassemble_one(ci, cva)
                            print(f"    0x{cva:08X}: {ci:08X}  {m:8s} {o}")
                        print()
                        break

    # ---- PASS 8: Multiplication by 12 patterns ----
    print("=" * 80)
    print("MULTIPLY BY 12 PATTERNS (glyph width * index)")
    print("=" * 80)
    for i in range(0, len(data) - 8, 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        mnem, ops, ann = disassemble_one(inst, va)

        # ADDIU rX, rY, 12 or ADDI rX, rY, 12
        op = (inst >> 26) & 0x3F
        if op in (8, 9):
            rs, rt, imm, simm = decode_i(inst)
            if simm == 12 and rs != 29:  # not stack adjustment
                print(f"  0x{va:08X}: {inst:08X}  {mnem:8s} {ops} ; ADD 12")
                # Show context
                for j in range(max(0, i-8), min(len(data), i+16), 4):
                    ci = struct.unpack_from("<I", data, j)[0]
                    cva = file_to_va(FILE_START + j)
                    m, o, a = disassemble_one(ci, cva)
                    marker = ">>>" if cva == va else "   "
                    print(f"    {marker} 0x{cva:08X}: {ci:08X}  {m:8s} {o}")
                print()

    # ---- PASS 9: Look for LBU/LHU (byte/halfword load) patterns ----
    # This is how a width table lookup would work: load byte from table[glyph_index]
    print("=" * 80)
    print("BYTE/HALFWORD LOADS (potential glyph width table lookups)")
    print("=" * 80)
    load_byte_count = 0
    for i in range(0, len(data), 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        op = (inst >> 26) & 0x3F
        if op in (0x20, 0x24):  # LB, LBU
            rs, rt, imm, simm = decode_i(inst)
            load_byte_count += 1
    print(f"  Total LB/LBU instructions in region: {load_byte_count}")

    # More specifically, look for LBU followed by addition to X cursor
    for i in range(0, len(data) - 16, 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        op = (inst >> 26) & 0x3F
        if op in (0x20, 0x24):  # LB/LBU
            rs, rt, imm, simm = decode_i(inst)
            # Check next few instructions for ADDU (add loaded width to position)
            for k in range(1, 6):
                if i + k*4 >= len(data):
                    break
                next_inst = struct.unpack_from("<I", data, i + k*4)[0]
                next_op = (next_inst >> 26) & 0x3F
                if next_op == 0:
                    fn = next_inst & 0x3F
                    if fn == 0x21:  # ADDU
                        nrs, nrt, nrd, _, _ = decode_r(next_inst)
                        if nrs == rt or nrt == rt:
                            # The loaded byte is being added to something
                            print(f"\n  Potential width lookup at 0x{va:08X}:")
                            for j in range(max(0, i-12), min(len(data), i+(k+4)*4), 4):
                                ci = struct.unpack_from("<I", data, j)[0]
                                cva = file_to_va(FILE_START + j)
                                m, o, a = disassemble_one(ci, cva)
                                marker = ">>>" if cva == va else "   "
                                print(f"    {marker} 0x{cva:08X}: {ci:08X}  {m:8s} {o}")
                            break
    print()

    # ---- PASS 10: Find specific pixel-width constants in wider region ----
    print("=" * 80)
    print("PIXEL WIDTH CONSTANTS IN WIDER REGION")
    print("=" * 80)
    target_widths = [216, 252, 288, 336, 360, 384, 448, 480, 512]
    for tw in target_widths:
        print(f"\n  Searching for {tw} (0x{tw:X}):")
        for i in range(0, len(wide_data), 4):
            inst = struct.unpack_from("<I", wide_data, i)[0]
            va = file_to_va(WIDE_FILE_START + i)
            op = (inst >> 26) & 0x3F
            if op in (8, 9, 0x0A, 0x0B):  # ADDI/ADDIU/SLTI/SLTIU
                rs, rt, imm, simm = decode_i(inst)
                if imm == (tw & 0xFFFF):
                    mnem, ops, ann = disassemble_one(inst, va)
                    print(f"    0x{va:08X}: {inst:08X}  {mnem:8s} {ops}")
            elif op == 0x0D:  # ORI
                rs, rt, imm, simm = decode_i(inst)
                if imm == (tw & 0xFFFF):
                    mnem, ops, ann = disassemble_one(inst, va)
                    print(f"    0x{va:08X}: {inst:08X}  {mnem:8s} {ops}")
    print()

    # ---- PASS 11: Full disassembly dump of first 200 instructions for manual review ----
    print("=" * 80)
    print("FULL DISASSEMBLY: First 400 instructions of renderer region")
    print("=" * 80)
    for i in range(0, min(1600, len(data)), 4):
        inst = struct.unpack_from("<I", data, i)[0]
        va = file_to_va(FILE_START + i)
        mnem, ops, ann = disassemble_one(inst, va)
        ann_str = f" ; {ann}" if ann else ""
        called = " <<FUNC>>" if va in jal_targets else ""
        branched = " <<TARGET>>" if va in branch_targets else ""
        print(f"  0x{va:08X}: {inst:08X}  {mnem:8s} {ops}{ann_str}{called}{branched}")


if __name__ == "__main__":
    main()
