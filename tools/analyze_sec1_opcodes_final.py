"""Final summary: Section 1 Event Script Format for Type-02 Resources.

FORMAT OVERVIEW:
- Stream of big-endian 16-bit words
- Variable-length instructions
- First word = opcode, followed by N parameter words

ADDRESSING:
- Section 2 text references use GLYPH INDICES (word indices), not byte offsets
- To get byte offset: glyph_index * 2
- Jump targets are byte offsets within Section 1 itself

VERIFIED OPCODES:
  0x0003 (3 words): SETUP/INIT - params: value1, value2
  0x0004 (5 words): DISPLAY_TEXT - params: 0x0000, glyph_offset, 0x0000, glyph_count
  0x0006 (7 words): COND_BIT_TEST - params: entity_id, mask_type, 0x0000, bitmask_hi, bitmask_lo, jump_addr
  0x0007 (7 words): COND_BIT_TEST2 - same as 0x0006
  0x0008 (3 words): JUMP_ELSE - params: 0x0000, jump_addr
  0x000B (3 words): JUMP - params: 0x0000, jump_addr
  0x000C (3 words): SET_NAME_REF - params: type, glyph_index (character name display)
  0x000D (3 words): CLEAR_NAME_REF - params: type, glyph_index
  0x0010 (2 words): WAIT/SYNC - params: delay
  0x0012 (3 words): SET_REGISTER - params: 0x0000, register_id
  0x0016 (6 words): SWITCH_CASE - params: case_type, match_val1, match_val2, result, jump_addr
  0x0017 (5 words): ENTITY_SETUP - params: entity_type, p1, p2, p3
  0x001A (3 words): SET_STATE - params: state_id, value
  0x002B (2 words): LOOP/REPEAT - params: count

STRUCTURAL PATTERN (R1198):
  Bytes 0x0000-0x00FF: Initialization (scene setup, state variables)
  Bytes 0x0100-0x1E50: Main loop (12 iterations for characters 1-14)
    Each iteration:
      001A 00BD XX     -- set scene/character ID
      0016 0002 FFFF... -- switch default branch
      002B 0005        -- loop over 6 party slots (0-5)
      For each slot:
        0016 0001 0000 SLOT 0000 ADDR  -- case for slot index
        0006 CHAR_ID 0040 0000 MASK 0000 ADDR  -- test character bits
        000B 0000 ADDR / 0008 0000 ADDR  -- jumps
        000C 0002 GLYPH_IDX  -- set character name reference
  Bytes 0x1E50-0x1EA0: Cleanup (000D 0002 GLYPH_IDX for each name)
  Bytes 0x1EA0-0x2000: Entity/scene setup
  Bytes 0x2000-0x2580: Dialogue display section
    Repeated pattern:
      0012 0000 REG    -- set text register
      0004 0000 GOFF 0000 GLEN  -- display text
      ... (scene control between dialogues)
  Bytes 0x2580-0x3224: Zero padding

CHARACTER ENTITY IDs (spaced 57 apart):
  0x005B (91), 0x0094 (148), 0x00CD (205),
  0x0106 (262), 0x013F (319), 0x0178 (376)
  = 6 party member slots
"""

import struct

# Quick verification across multiple type-02 resources
files = [
    ('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'R1198'),
    ('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1196_type02.raw', 'R1196'),
    ('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1200_type02.raw', 'R1200'),
]

for filepath, name in files:
    try:
        data = open(filepath, 'rb').read()
    except:
        continue

    sec2_off = struct.unpack_from('<I', data, 0x18)[0]
    s1 = data[28:sec2_off]
    s2 = data[sec2_off:]

    words = []
    for i in range(0, len(s1)-1, 2):
        words.append(struct.unpack_from('>H', s1, i)[0])

    # Count text display opcodes
    text_ops = 0
    all_end_ok = True
    for i in range(len(words) - 4):
        if words[i] == 0x0004 and words[i+1] == 0x0000 and words[i+3] == 0x0000:
            goff = words[i+2]
            glen = words[i+4] if i+4 < len(words) else 0
            byte_off = goff * 2
            byte_len = glen * 2
            end = byte_off + byte_len
            if byte_off < len(s2) and end <= len(s2) and glen > 0:
                last_glyph = struct.unpack_from('>H', s2, end - 2)[0]
                if last_glyph != 0xFFFF:
                    all_end_ok = False
                text_ops += 1

    # Count name refs
    name_refs = sum(1 for i in range(len(words)-2) if words[i] == 0x000C)
    name_clears = sum(1 for i in range(len(words)-2) if words[i] == 0x000D)
    jumps = sum(1 for i in range(len(words)-2) if words[i] in (0x000B, 0x0008))
    conditionals = sum(1 for i in range(len(words)-6) if words[i] in (0x0006, 0x0007))

    print(f"{name}: S1={len(s1)}B, S2={len(s2)}B")
    print(f"  Text displays: {text_ops}, all end at FFFF: {all_end_ok}")
    print(f"  Name refs: {name_refs}, Name clears: {name_clears}")
    print(f"  Jumps: {jumps}, Conditionals: {conditionals}")
    print()
