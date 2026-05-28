"""Analyze Section 1 event script opcodes for type-02 resources."""
import struct
import sys

def analyze(filepath):
    data = open(filepath, 'rb').read()
    sec2_off = struct.unpack_from('<I', data, 0x18)[0]
    s1 = data[28:sec2_off]

    print(f"Section 1: {len(s1)} bytes, {len(s1)//2} words")

    words = []
    for i in range(0, len(s1)-1, 2):
        words.append(struct.unpack_from('>H', s1, i)[0])

    # Dump words 148..240 to see repeating block
    print("\n=== Words from offset 0x0128 (repeating block region) ===")
    for i in range(148, min(240, len(words))):
        print(f"[{i:4d}] @{i*2:04X}: 0x{words[i]:04X} ({words[i]})")

    # Now try to identify instruction boundaries by looking at the
    # repeating patterns in the hex dump.
    # From hex dump analysis:
    # At 0x0128: 00 06 00 16 00 01 00 00 00 00 00 00 01 92
    # = words: 0006 0016 0001 0000 0000 0000 0192
    # Then: 00 06 00 5B 00 40 00 00 20 00 00 00 01 50
    # = words: 0006 005B 0040 0000 2000 0000 0150
    # Then: 00 0B 00 00 01 92
    # = words: 000B 0000 0192

    # Hypothesis: opcodes are the first word, and each opcode has a fixed number of params
    # Let me try to walk through assuming certain opcodes have certain lengths

    # Let me try another approach: look at what follows each instance of common opcodes
    # Focus on opcodes 0x0003, 0x0006, 0x0007, 0x0008, 0x000B, 0x000C, 0x001A, 0x0012

    print("\n=== Instances of key opcodes with context ===")
    for opcode in [0x0003, 0x0006, 0x0007, 0x0008, 0x000B, 0x000C, 0x0012, 0x001A, 0x0016, 0x0004]:
        positions = [i for i, w in enumerate(words) if w == opcode]
        print(f"\nOpcode 0x{opcode:04X}: {len(positions)} occurrences")
        for pos in positions[:6]:
            ctx = words[pos:pos+10]
            ctx_str = ' '.join(f'{w:04X}' for w in ctx)
            print(f"  @{pos*2:04X}: {ctx_str}")

    # Now look for what might be message display opcodes
    # R1198 has 88 messages (0-87).
    # Look for sequential message indices
    print("\n=== Searching for sequential message indices (0-87) ===")
    # Find all positions where values 0-87 appear
    for target_idx in range(0, 10):
        positions = [i for i, w in enumerate(words) if w == target_idx]
        print(f"  msg_idx={target_idx}: appears at word positions {positions[:10]}...")

    # Look for a specific pattern: any opcode followed by incrementing indices
    print("\n=== Looking for opcode + incrementing index pattern ===")
    for field_offset in range(1, 8):
        # Check if words[i] is always the same when words[i+field_offset] increments
        sequences = []
        for i in range(len(words) - field_offset - 1):
            if words[i + field_offset] < 88 and i + field_offset + 1 < len(words):
                # Check if next occurrence of same opcode pattern has next index
                for j in range(i+1, min(i+50, len(words) - field_offset)):
                    if (words[j] == words[i] and
                        words[j + field_offset] == words[i + field_offset] + 1 and
                        words[j + field_offset] < 88):
                        sequences.append((i, j, words[i], field_offset, words[i+field_offset], words[j+field_offset]))
                        break

        if sequences:
            print(f"\n  field_offset={field_offset}: {len(sequences)} sequential pairs found")
            for s in sequences[:5]:
                i, j, op, fo, v1, v2 = s
                ctx1 = ' '.join(f'{words[i+k]:04X}' for k in range(min(fo+3, 10)))
                ctx2 = ' '.join(f'{words[j+k]:04X}' for k in range(min(fo+3, 10)))
                print(f"    @{i*2:04X}: {ctx1}")
                print(f"    @{j*2:04X}: {ctx2}")

if __name__ == '__main__':
    analyze('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw')
