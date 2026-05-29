#!/usr/bin/env python3
"""
Deep analysis of Region H: 0x3C9A34-0x3C9D54
Try to determine the record structure.
"""
import json, struct, sys

sys.stdout.reconfigure(encoding='utf-8')

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"

def main():
    glyph_map = json.load(open(GLYPH_MAP_PATH, 'r', encoding='utf-8'))
    with open(EXE_PATH, 'rb') as f:
        exe = f.read()

    def decode(val):
        if val == 0: return '\u00B7'
        if 1 <= val <= 94: return chr(val + 0x20)
        ch = glyph_map.get(str(val))
        return ch if ch else f'[?{val}]'

    def is_kanji(val):
        return 95 <= val <= 881 and str(val) in glyph_map

    # Dump the raw hex of the region
    start = 0x3C9A00
    end = 0x3C9E00

    print("=== Raw hex dump with uint16 decode ===\n")

    for i in range(start, end, 16):
        raw = exe[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in raw)

        # Decode as uint16 LE
        u16s = [struct.unpack_from('<H', raw, j)[0] for j in range(0, min(len(raw)-1, 15), 2)]
        decoded = ''.join(decode(v) for v in u16s)

        # Mark kanji
        markers = ''.join('K' if is_kanji(v) else '.' for v in u16s)

        print(f"0x{i:06X}: {hex_str:<48s}  {decoded:<20s}  {markers}")

    # Now try to figure out the record structure
    # Look at the pattern of non-glyph values
    print("\n\n=== Non-glyph-range values (potential record boundaries) ===\n")

    for i in range(0x3C9A34, 0x3C9D54, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        if val > 881 and val != 0:
            print(f"  0x{i:06X}: {val:5d} (0x{val:04X})")

    # Also check what's in the wider context (before and after)
    print("\n\n=== Context: 0x3C9940-0x3C9A40 (before) ===\n")
    for i in range(0x3C9940, 0x3C9A40, 16):
        raw = exe[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in raw)
        u16s = [struct.unpack_from('<H', raw, j)[0] for j in range(0, 14, 2)]
        vals_str = ' '.join(f'{v:5d}' for v in u16s)
        print(f"0x{i:06X}: {hex_str}  | {vals_str}")

    print("\n\n=== Context: 0x3C9D50-0x3C9E10 (after, including tab IDs) ===\n")
    for i in range(0x3C9D50, 0x3C9E10, 16):
        raw = exe[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in raw)
        u16s = [struct.unpack_from('<H', raw, j)[0] for j in range(0, min(len(raw)-1, 14), 2)]
        vals_str = ' '.join(f'{v:5d}' for v in u16s)
        decoded = ''.join(decode(v) for v in u16s)
        print(f"0x{i:06X}: {hex_str}  | {vals_str}  | {decoded}")

    # Try different record sizes to find the right one
    print("\n\n=== Try 14-byte records starting at 0x3C9A34 ===\n")
    for rec_idx in range(0, 50):
        base = 0x3C9A34 + rec_idx * 14
        if base + 14 > len(exe):
            break
        vals = [struct.unpack_from('<H', exe, base + j)[0] for j in range(0, 14, 2)]
        decoded = ''.join(decode(v) for v in vals)
        kanji = ''.join(decode(v) for v in vals if is_kanji(v))
        print(f"  [{rec_idx:3d}] 0x{base:06X}: {decoded:20s}  kanji={kanji}")

    print("\n\n=== Try 12-byte records starting at 0x3C9A34 ===\n")
    for rec_idx in range(0, 50):
        base = 0x3C9A34 + rec_idx * 12
        if base + 12 > len(exe):
            break
        vals = [struct.unpack_from('<H', exe, base + j)[0] for j in range(0, 12, 2)]
        decoded = ''.join(decode(v) for v in vals)
        kanji = ''.join(decode(v) for v in vals if is_kanji(v))
        non_glyph = [(j, v) for j, v in enumerate(vals) if v > 881]
        print(f"  [{rec_idx:3d}] 0x{base:06X}: {decoded:20s}  kanji={kanji}  non_glyph={non_glyph}")


if __name__ == '__main__':
    main()
