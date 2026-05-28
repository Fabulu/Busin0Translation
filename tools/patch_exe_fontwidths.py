"""
patch_exe_fontwidths.py
Patches the 4 font-width tables in the Wizardry PS2 EXE with
English-optimized character widths so text renders with tight spacing.

Only glyphs 0-94 (ASCII range) are patched. Positions 95-247 are left
untouched (Japanese / kanji glyphs).

Width tables (248 entries x 1 byte each) live at:
  0x3DDC48, 0x3DDD48, 0x3DDE48, 0x3DDF48
"""

import os
import shutil
import sys

SRC = os.path.join(os.path.dirname(__file__), "..", "extracted", "SLPM_653.78")
DST = os.path.join(os.path.dirname(__file__), "..", "build", "SLPM_653.78_patched")

TABLE_OFFSETS = [0x3DDC48, 0x3DDD48, 0x3DDE48, 0x3DDF48]
TABLE_SIZE = 248
PATCH_COUNT = 95  # glyphs 0-94

def build_english_widths():
    """Return a list of 95 optimal pixel widths for the ASCII glyph range."""
    w = [6] * PATCH_COUNT  # default: 6px

    # Glyph 0: space
    w[0] = 3

    # Glyphs 1-15: punctuation  (! " # $ % & ' ( ) * + , - . /)
    for i in range(1, 16):
        w[i] = 4
    # Some narrow punctuation gets 3px
    for i in [1, 7, 11, 12, 14]:  # ! ' + , .
        w[i] = 3

    # Glyphs 16-25: digits 0-9
    for i in range(16, 26):
        w[i] = 5

    # Glyphs 26-32: more punctuation (: ; < = > ? @)
    for i in range(26, 33):
        w[i] = 4
    # Colon and semicolon are narrow
    w[26] = 3  # :
    w[27] = 3  # ;

    # Glyphs 33-58: uppercase A-Z
    for i in range(33, 59):
        w[i] = 6
    # Narrow uppercase letters
    w[33 + ord('I') - ord('A')] = 4  # I -> glyph 41
    w[33 + ord('J') - ord('A')] = 5  # J -> glyph 42
    w[33 + ord('L') - ord('A')] = 5  # L -> glyph 44
    # Wide uppercase
    w[33 + ord('M') - ord('A')] = 7  # M -> glyph 45
    w[33 + ord('W') - ord('A')] = 7  # W -> glyph 55

    # Glyphs 59-64: [ \ ] ^ _ `
    for i in range(59, 65):
        w[i] = 4

    # Glyphs 65-90: lowercase a-z
    for i in range(65, 91):
        w[i] = 5
    # Narrow lowercase
    w[65 + ord('i') - ord('a')] = 3  # i -> glyph 73
    w[65 + ord('l') - ord('a')] = 3  # l -> glyph 76
    w[65 + ord('t') - ord('a')] = 4  # t -> glyph 84
    w[65 + ord('f') - ord('a')] = 4  # f -> glyph 70
    w[65 + ord('j') - ord('a')] = 4  # j -> glyph 74
    w[65 + ord('r') - ord('a')] = 4  # r -> glyph 82
    # Wide lowercase
    w[65 + ord('m') - ord('a')] = 6  # m -> glyph 77
    w[65 + ord('w') - ord('a')] = 6  # w -> glyph 87

    # Glyphs 91-94: { | } ~
    w[91] = 4  # {
    w[92] = 3  # |
    w[93] = 4  # }
    w[94] = 5  # ~

    return w


def main():
    src = os.path.normpath(SRC)
    dst = os.path.normpath(DST)

    if not os.path.isfile(src):
        print(f"ERROR: source EXE not found: {src}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

    widths = build_english_widths()
    patch_bytes = bytes(widths)

    with open(dst, "r+b") as f:
        for offset in TABLE_OFFSETS:
            f.seek(offset)
            old = list(f.read(PATCH_COUNT))
            f.seek(offset)
            f.write(patch_bytes)
            print(f"Patched table at 0x{offset:X}  (glyphs 0-{PATCH_COUNT - 1})")

    print(f"\nSaved patched EXE to: {dst}")
    print(f"Width map (glyphs 0-94): {list(patch_bytes)}")


if __name__ == "__main__":
    main()
