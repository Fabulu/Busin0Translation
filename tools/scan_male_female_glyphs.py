"""Scan EXE for hardcoded references to glyph IDs 518 (male) and 349 (female)."""
import struct
import sys

ORIG = "extracted/SLPM_653.78"
PATCHED = "build/SLPM_653.78_patched"

TARGET_IDS = {518: "male-kanji (0x0206)", 349: "female-kanji (0x015D)"}
REPLACEMENT_IDS = {672: "male-sym (0x02A0)", 673: "female-sym (0x02A1)"}

def read_file(path):
    with open(path, "rb") as f:
        return f.read()

orig = read_file(ORIG)
patched = read_file(PATCHED)

print(f"Original EXE: {len(orig)} bytes")
print(f"Patched EXE:  {len(patched)} bytes")
print("=" * 80)

# --- 1. Full scan for LE u16 values in key regions ---
REGIONS = [
    ("Menu structs",        0x3C3000, 0x3C5300),
    ("Keyboard pages",      0x3C5550, 0x3C6C00),
    ("Glyph table @3B316C", 0x3B316C, 0x3B316C + 0x2000),
    ("Glyph table @3C0882", 0x3C0882, 0x3C0882 + 0x2000),
    ("Glyph table @3CA6DA", 0x3CA6DA, 0x3CA6DA + 0x2000),
    ("Glyph table @3D1384", 0x3D1384, 0x3D1384 + 0x2000),
    ("Cell data @3D8D10",   0x3D8D10, 0x3D8D10 + 0x4000),
    ("Chargen code",        0x1F2000, 0x1F3000),
    ("Chargen wider",       0x1F0000, 0x1F8000),
]

for target_val, target_name in TARGET_IDS.items():
    target_le = struct.pack("<H", target_val)
    print(f"\n{'='*80}")
    print(f"Scanning for glyph ID {target_val} = {target_name}")
    print(f"LE bytes: {target_le.hex()}")
    print(f"{'='*80}")

    for region_name, start, end in REGIONS:
        chunk = orig[start:end]
        pos = 0
        while True:
            idx = chunk.find(target_le, pos)
            if idx == -1:
                break
            file_off = start + idx
            # Show context
            ctx_start = max(0, idx - 8)
            ctx_end = min(len(chunk), idx + 10)
            ctx_bytes = chunk[ctx_start:ctx_end].hex()

            # Check if patched version differs
            patched_val = struct.unpack("<H", patched[file_off:file_off+2])[0]
            changed = " ** PATCHED **" if patched_val != target_val else ""
            patched_info = f" -> patched={patched_val} (0x{patched_val:04X}){changed}" if patched_val != target_val else ""

            # Alignment info
            aligned = "even" if idx % 2 == 0 else "ODD"

            print(f"  [{region_name}] offset 0x{file_off:06X} (align={aligned}) ctx: ...{ctx_bytes}...{patched_info}")
            pos = idx + 1

# --- 2. Detailed keyboard page table scan ---
print(f"\n{'='*80}")
print("KEYBOARD PAGE TABLE DETAILED SCAN")
print(f"{'='*80}")

# Each entry: flag:u16, gA:u16, dA:u16, gB:u16, dB:u16 = 10 bytes
KB_START = 0x3C5550
KB_END = 0x3C6C00
entry_size = 10
n_entries = (KB_END - KB_START) // entry_size

for i in range(n_entries):
    off = KB_START + i * entry_size
    flag, gA, dA, gB, dB = struct.unpack_from("<5H", orig, off)

    hit = False
    for tid, tname in TARGET_IDS.items():
        if gA == tid or gB == tid:
            hit = True
    for rid, rname in REPLACEMENT_IDS.items():
        if gA == rid or gB == rid:
            hit = True

    if hit:
        # Check patched
        p_flag, p_gA, p_dA, p_gB, p_dB = struct.unpack_from("<5H", patched, off)
        print(f"  Entry {i} @ 0x{off:06X}: flag={flag} gA={gA}(0x{gA:04X}) dA={dA} gB={gB}(0x{gB:04X}) dB={dB}")
        if (p_flag, p_gA, p_dA, p_gB, p_dB) != (flag, gA, dA, gB, dB):
            print(f"    PATCHED -> flag={p_flag} gA={p_gA}(0x{p_gA:04X}) dA={p_dA} gB={p_gB}(0x{p_gB:04X}) dB={p_dB}")

# --- 3. Menu struct scan (56-byte records) ---
print(f"\n{'='*80}")
print("MENU STRUCT SCAN (56-byte records)")
print(f"{'='*80}")

MENU_START = 0x3C3000
MENU_END = 0x3C5300
rec_size = 56
n_recs = (MENU_END - MENU_START) // rec_size

for i in range(n_recs):
    off = MENU_START + i * rec_size
    rec = orig[off:off+rec_size]

    # Check all u16 values in the record
    hits = []
    for j in range(0, rec_size - 1, 2):
        val = struct.unpack_from("<H", rec, j)[0]
        if val in TARGET_IDS:
            hits.append((j, val, TARGET_IDS[val]))

    if hits:
        # Also check patched
        p_rec = patched[off:off+rec_size]
        print(f"  Record {i} @ 0x{off:06X}:")
        print(f"    Raw: {rec.hex()}")
        for j, val, name in hits:
            p_val = struct.unpack_from("<H", p_rec, j)[0]
            changed = f" -> PATCHED to {p_val} (0x{p_val:04X})" if p_val != val else ""
            print(f"    byte-{j}: {val} = {name}{changed}")

# --- 4. Broader scan: every aligned u16 in 0x3C0000-0x3E0000 ---
print(f"\n{'='*80}")
print("BROAD SCAN: 0x3C0000-0x3E0000 (all aligned u16)")
print(f"{'='*80}")

BROAD_START = 0x3C0000
BROAD_END = min(0x3E0000, len(orig))

for target_val, target_name in TARGET_IDS.items():
    count = 0
    for off in range(BROAD_START, BROAD_END - 1, 2):
        val = struct.unpack_from("<H", orig, off)[0]
        if val == target_val:
            p_val = struct.unpack_from("<H", patched, off)[0]
            changed = f" -> PATCHED={p_val}(0x{p_val:04X})" if p_val != target_val else ""
            # Identify which sub-region
            region = "unknown"
            for rn, rs, re in REGIONS:
                if rs <= off < re:
                    region = rn
                    break
            print(f"  0x{off:06X} = {target_val} ({target_name}) in [{region}]{changed}")
            count += 1
    print(f"  Total occurrences of {target_val}: {count}")

# --- 5. Check for LUI/ORI loading these values in code ---
print(f"\n{'='*80}")
print("MIPS INSTRUCTION SCAN: LUI/ADDIU loading 518 or 349")
print(f"{'='*80}")

# In MIPS, small values loaded via: addiu reg, $zero, imm16
# or li reg, imm (pseudo = lui + ori or just addiu)
# addiu rt, rs, imm: opcode 001001 rs(5) rt(5) imm(16)
# For addiu rt, $zero, 518: rs=0, imm=0x0206
# opcode field = 0x24000000 for addiu? No: addiu = 001001 = 0x24..
# Actually addiu opcode = 0x24000000 >> ... let me just search for the immediate

# Search code section (roughly 0x1000 to 0x200000) for MIPS instructions with immediate 518 or 349
CODE_START = 0x1000
CODE_END = 0x200000

for target_val, target_name in TARGET_IDS.items():
    print(f"\n  Looking for immediate value {target_val} (0x{target_val:04X}) in code...")
    found = 0
    for off in range(CODE_START, min(CODE_END, len(orig) - 3), 4):
        instr = struct.unpack_from("<I", orig, off)[0]
        imm16 = instr & 0xFFFF
        opcode = (instr >> 26) & 0x3F
        rs = (instr >> 21) & 0x1F

        if imm16 == target_val:
            # Filter to likely glyph-loading instructions
            # addiu (0x09), ori (0x0D), li (addiu with rs=0)
            if opcode in (0x09, 0x0D, 0x0F, 0x0A, 0x0B, 0x0C, 0x24, 0x25):
                rt = (instr >> 16) & 0x1F
                op_names = {0x09: "addiu", 0x0D: "ori", 0x0F: "lui", 0x0A: "slti",
                           0x0B: "sltiu", 0x0C: "andi", 0x24: "lbu", 0x25: "lhu"}
                op_name = op_names.get(opcode, f"op{opcode}")

                # Check patched
                p_instr = struct.unpack_from("<I", patched, off)[0]
                p_imm = p_instr & 0xFFFF
                changed = f" -> PATCHED imm={p_imm}(0x{p_imm:04X})" if p_imm != target_val else ""

                # Virtual address (EXE loads at 0x100000, file header 0x800 or so)
                vaddr = off + 0x100000 - 0x800  # approximate

                print(f"    0x{off:06X} (va ~0x{vaddr:08X}): {op_name} r{rt}, r{rs}, 0x{target_val:04X}{changed}")
                found += 1
    print(f"    Total: {found} instructions")

# --- 6. Specifically scan chargen area more carefully ---
print(f"\n{'='*80}")
print("CHARGEN CODE AREA: 0x1F0000-0x1F8000 - ALL instructions with relevant immediates")
print(f"{'='*80}")

for off in range(0x1F0000, min(0x1F8000, len(orig) - 3), 4):
    instr = struct.unpack_from("<I", orig, off)[0]
    imm16 = instr & 0xFFFF
    if imm16 in TARGET_IDS or imm16 in REPLACEMENT_IDS or imm16 in (672, 673):
        opcode = (instr >> 26) & 0x3F
        rs = (instr >> 21) & 0x1F
        rt = (instr >> 16) & 0x1F
        op_names = {0x09: "addiu", 0x0D: "ori", 0x0F: "lui", 0x24: "lbu", 0x25: "lhu",
                   0x29: "sh", 0x2B: "sw", 0x23: "lw", 0x21: "lh"}
        op_name = op_names.get(opcode, f"op{opcode:02X}")

        p_instr = struct.unpack_from("<I", patched, off)[0]
        p_imm = p_instr & 0xFFFF
        changed = f" -> PATCHED imm={p_imm}(0x{p_imm:04X})" if p_imm != imm16 else ""

        print(f"  0x{off:06X}: {op_name} r{rt}, r{rs}, 0x{imm16:04X} ({imm16}){changed}")

print("\nDone.")
