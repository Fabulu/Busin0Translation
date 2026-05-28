"""Build the comprehensive opcode format table based on verified patterns.

CONFIRMED:
- Section 1 is a stream of big-endian 16-bit words
- Values reference Section 2 as GLYPH INDICES (multiply by 2 for byte offset)
- Opcode 0x0004 0x0000 GOFF 0x0000 GLEN = display text (GOFF=glyph offset, GLEN=glyph count)
- Opcode 0x000C 0x0002 GOFF = set/reference character name at glyph position
- Opcode 0x000D 0x0002 GOFF = cleanup/release character name reference

Now let me try to walk the instruction stream from offset 0x2000 onwards
(the "epilogue" / dialogue section) to verify instruction lengths.
"""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# From the hex dump analysis, hypothesized instruction lengths:
# Each entry: opcode -> (name, num_params, total_words_including_opcode)
# Some opcodes have variable length depending on sub-type

OPCODES = {
    0x0003: ("BRANCH/SETUP?", 2, 3),       # 0003 XX YY
    0x0004: ("DISPLAY_TEXT", 4, 5),          # 0004 0000 GOFF 0000 GLEN
    0x0006: ("COND_TEST", 6, 7),             # 0006 TARGET MASK_HI MASK_LO BITMASK_HI BITMASK_LO ADDR
    0x0007: ("COND_TEST2", 6, 7),            # 0007 TARGET MASK_HI MASK_LO BITMASK_HI BITMASK_LO ADDR
    0x0008: ("JUMP_ELSE", 2, 3),             # 0008 0000 ADDR
    0x000B: ("JUMP", 2, 3),                  # 000B 0000 ADDR
    0x000C: ("SET_NAME", 2, 3),              # 000C TYPE GOFF
    0x000D: ("CLEAR_NAME", 2, 3),            # 000D TYPE GOFF
    0x000E: ("UNK_0E", 2, 3),
    0x0010: ("WAIT/DELAY", 1, 2),            # 0010 FRAMES
    0x0012: ("SET_REG", 2, 3),               # 0012 0000 REGID
    0x0014: ("CMP_REG", 2, 3),               # 0014 PARAM VALUE
    0x0016: ("SWITCH_CASE", 5, 6),           # 0016 TYPE P1 P2 P3 ADDR
    0x0017: ("SETUP_ENTITY", 4, 5),          # 0017 P1 P2 P3 P4
    0x001A: ("SET_STATE", 2, 3),             # 001A REGID VALUE
    0x001B: ("UNK_1B", 1, 2),
    0x0021: ("UNK_21", 3, 4),               # 0021 P1 P2 P3
    0x0022: ("UNK_22", 2, 3),
    0x0027: ("UNK_27", 1, 2),
    0x002B: ("LOOP_START", 1, 2),            # 002B COUNT
    0x002C: ("LOOP_VAR", 1, 2),              # 002C VAR
    0x003C: ("NOP/SYNC", 0, 1),
    0x0043: ("SET_FLAG", 1, 2),
    0x0045: ("CHECK_FLAG", 3, 4),
    0x0047: ("SET_PARAM", 2, 3),
    0x0048: ("SET_PARAM2", 2, 3),
    0x004E: ("UNK_4E", 1, 2),
    0x005A: ("UNK_5A", 0, 1),
    0x0060: ("UNK_60", 1, 2),
    0x0062: ("END_BLOCK", 1, 2),
    0x0063: ("UNK_63", 1, 2),
    0x0065: ("UNK_65", 1, 2),
    0x006A: ("UNK_6A", 0, 1),
    0x006D: ("UNK_6D", 1, 2),
    0x0076: ("UNK_76", 0, 1),
    0x0079: ("UNK_79", 1, 2),
    0x007A: ("UNK_7A", 0, 1),
    0x0080: ("UNK_80", 0, 1),
    0x0086: ("UNK_86", 0, 1),
    0x0098: ("UNK_98", 0, 1),
    0x0099: ("UNK_99", 0, 1),
    0x00B2: ("UNK_B2", 0, 1),
    0x00B4: ("UNK_B4", 1, 2),
    0x00B8: ("UNK_B8", 0, 1),
    0x00BD: ("SCENE_ID", 1, 2),
    0x00BE: ("UNK_BE", 0, 1),
    0xFFFF: ("JUMP_DEFAULT", 2, 3),
}

# Try walking from 0x2000
print("=== Instruction walk from 0x2000 ===")
pc = 0x2000 // 2  # word index
errors = 0
inst_count = 0

while pc < len(words) and errors < 3 and inst_count < 150:
    w = words[pc]

    if w == 0x0000:
        # Could be padding or part of a parameter
        pc += 1
        continue

    if w in OPCODES:
        name, nparams, total = OPCODES[w]
        params = words[pc+1:pc+total] if pc+total <= len(words) else []
        params_str = ' '.join(f'{p:04X}' for p in params)

        # Special formatting for text display
        if w == 0x0004 and len(params) >= 4:
            goff = params[1]
            glen = params[3]
            byte_off = goff * 2
            print(f"  @{pc*2:04X}: {name} glyph_off={goff} glyph_len={glen} (S2+0x{byte_off:04X}, {glen*2} bytes)")
        elif w == 0x000C or w == 0x000D:
            print(f"  @{pc*2:04X}: {name} type={params[0] if params else '?'} glyph_idx={params[1] if len(params)>1 else '?'}")
        else:
            print(f"  @{pc*2:04X}: {name} [{params_str}]")

        pc += total
        inst_count += 1
    else:
        # Unknown opcode - try to continue
        print(f"  @{pc*2:04X}: ??? opcode=0x{w:04X}")
        errors += 1
        pc += 1
        inst_count += 1

print(f"\nDecoded {inst_count} instructions, {errors} unknown opcodes")

# Now let me also verify with a second type-02 resource
print("\n\n=== Cross-validate with R1196 ===")
try:
    data2 = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1196_type02.raw', 'rb').read()
    sec2_off2 = struct.unpack_from('<I', data2, 0x18)[0]
    s1_2 = data2[28:sec2_off2]
    s2_2 = data2[sec2_off2:]

    words2 = []
    for i in range(0, len(s1_2)-1, 2):
        words2.append(struct.unpack_from('>H', s1_2, i)[0])

    print(f"R1196 Section 1: {len(s1_2)} bytes, Section 2: {len(s2_2)} bytes")

    # Find text display opcodes
    for i in range(len(words2) - 4):
        if (words2[i] == 0x0004 and words2[i+1] == 0x0000 and
            words2[i+3] == 0x0000):
            goff = words2[i+2]
            glen = words2[i+4] if i+4 < len(words2) else 0
            byte_off = goff * 2
            if byte_off < len(s2_2) and glen > 0:
                first_glyph = struct.unpack_from('>H', s2_2, byte_off)[0]
                end_byte = byte_off + glen * 2
                last_glyph = struct.unpack_from('>H', s2_2, end_byte - 2)[0] if end_byte <= len(s2_2) else 0
                print(f"  @S1+{i*2:04X}: goff={goff}, glen={glen}, S2+0x{byte_off:04X}, first=0x{first_glyph:04X}, last=0x{last_glyph:04X}")
except Exception as e:
    print(f"Error: {e}")
