"""
Empirical test: swap ONE glyph ID in R39 extra data.

Changes the FIRST occurrence of glyph 346 (0x015A = 力/STR kanji)
in the extra data section (offset 2702+) to glyph 51 (0x0033 = 'S'
if ASCII mapping is ord(c)-0x20).

Only modifies the extra data — does NOT touch the glyph stream (632-2701).
"""

import struct
import shutil
import sys
import os

R39_PATH = os.path.join(os.path.dirname(__file__), "..", "build", "packdata_resources", "0039_type15.raw")
R39_PATH = os.path.normpath(R39_PATH)

OLD_GLYPH = 346   # 0x015A — 力 (STR kanji)
NEW_GLYPH = 51    # 0x0033 — should be 'S' (ord('S')-0x20 = 51)
EXTRA_DATA_START = 2702

def main():
    data = bytearray(open(R39_PATH, "rb").read())
    print(f"Read {len(data)} bytes from {R39_PATH}")

    # Scan extra data for first occurrence of OLD_GLYPH as BE uint16
    old_be = struct.pack(">H", OLD_GLYPH)
    new_be = struct.pack(">H", NEW_GLYPH)

    extra = data[EXTRA_DATA_START:]
    pos = extra.find(old_be)

    # Make sure we're on an aligned boundary (even offset)
    while pos is not None and pos >= 0 and pos % 2 != 0:
        pos = extra.find(old_be, pos + 1)

    if pos is None or pos < 0:
        print("ERROR: glyph 346 (0x015A) not found in extra data!")
        sys.exit(1)

    abs_offset = EXTRA_DATA_START + pos
    print(f"Found glyph {OLD_GLYPH} (0x{OLD_GLYPH:04X}) at absolute offset {abs_offset} (extra data offset {pos})")
    print(f"Before: {' '.join(f'{b:02X}' for b in data[abs_offset-4:abs_offset+6])}")

    # Perform the swap
    data[abs_offset:abs_offset+2] = new_be

    print(f"After:  {' '.join(f'{b:02X}' for b in data[abs_offset-4:abs_offset+6])}")
    print(f"Replaced glyph {OLD_GLYPH} -> {NEW_GLYPH} (0x{OLD_GLYPH:04X} -> 0x{NEW_GLYPH:04X})")

    # Verify: glyph 51 is in page 0 (51 >> 8 = 0), cell 51
    page = NEW_GLYPH >> 8
    cell = NEW_GLYPH & 0xFF
    print(f"New glyph {NEW_GLYPH}: page {page}, cell {cell}")

    # Write back
    open(R39_PATH, "wb").write(data)
    print(f"Written modified R39 to {R39_PATH}")

    # Count remaining occurrences of old glyph for reference
    remaining = 0
    for i in range(0, len(data[EXTRA_DATA_START:]) - 1, 2):
        val = struct.unpack(">H", data[EXTRA_DATA_START + i:EXTRA_DATA_START + i + 2])[0]
        if val == OLD_GLYPH:
            remaining += 1
    print(f"Remaining occurrences of glyph {OLD_GLYPH} in extra data: {remaining}")

if __name__ == "__main__":
    main()
