"""
patch_exe.py  –  EXE binary patch accumulator for Busin 0 (SLPM_653.78)

Reads the original EXE, applies translation patches, writes patched output.
Patches applied:
  1. Save slot names       (Table 2G)  – fullwidth SJIS → ASCII
  2. Player-visible strings (Table 2L) – SJIS → ASCII
  3. NPC names              (Table 2F) – LE uint16 glyph IDs
"""

import os
import struct
import sys
import io

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = os.path.join(os.path.dirname(__file__), "..", "extracted", "SLPM_653.78")
DST = os.path.join(os.path.dirname(__file__), "SLPM_653.78_patched")
EXPECTED_SIZE = 4_185_776

def encode_glyph_ids(text):
    """Encode ASCII text as LE uint16 glyph IDs (glyph_id = ord(c) - 0x20)."""
    result = b""
    for c in text:
        glyph_id = ord(c) - 0x20
        result += struct.pack("<H", glyph_id)
    return result

def main():
    src = os.path.normpath(SRC)
    dst = os.path.normpath(DST)

    if not os.path.isfile(src):
        print(f"ERROR: source EXE not found: {src}", file=sys.stderr)
        sys.exit(1)

    data = bytearray(open(src, "rb").read())

    if len(data) != EXPECTED_SIZE:
        print(f"ERROR: EXE size mismatch: expected {EXPECTED_SIZE}, got {len(data)}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {src} ({len(data)} bytes)")
    patched_count = 0

    # ─── PATCH 1: Save Slot Names (Table 2G) ───────────────────────────
    # Fullwidth SJIS Japanese → plain ASCII, null-padded
    # Original SJIS strings (for verification):
    save_patches = [
        # (offset, slot_bytes, expected_sjis_hex, new_ascii)
        (0x3FC720, 16, "8261827482728268826d824f",              "BUSIN 0"),
        (0x3FC750, 32, "8261827482728268826d824f8366815b835e8250", "BUSIN 0 Data 1"),
        (0x3FC770, 32, "8261827482728268826d824f8366815b835e8251", "BUSIN 0 Data 2"),
        (0x3FC790, 32, "8261827482728268826d824f8366815b835e8252", "BUSIN 0 Data 3"),
        (0x3F9370, 24, "8261827482728268826d824f928692668366815b835e", "BUSIN 0 Suspend"),
        (0x3F9678, 12, "8261827482728268826d824f",                    "BUSIN 0"),
    ]

    print("\n--- Patch 1: Save Slot Names ---")
    for offset, avail, expected_hex, new_text in save_patches:
        expected_bytes = bytes.fromhex(expected_hex)
        actual = data[offset:offset + len(expected_bytes)]
        if actual == expected_bytes:
            encoded = new_text.encode("ascii")
            if len(encoded) + 1 > avail:
                print(f"  SKIP 0x{offset:06X}: new string too long ({len(encoded)+1} > {avail})")
                continue
            # Zero-fill then write
            for i in range(avail):
                data[offset + i] = 0
            for i, b in enumerate(encoded):
                data[offset + i] = b
            print(f"  OK   0x{offset:06X}: -> {new_text!r}")
            patched_count += 1
        else:
            # Check if already ASCII-patched
            actual_str = data[offset:offset + avail]
            null_pos = actual_str.find(b"\x00")
            snippet = actual_str[:null_pos] if null_pos >= 0 else actual_str
            try:
                decoded = snippet.decode("ascii")
                print(f"  SKIP 0x{offset:06X}: already ASCII ({decoded!r})")
            except UnicodeDecodeError:
                print(f"  WARN 0x{offset:06X}: unexpected bytes, skipping (got {actual.hex()})")

    # ─── PATCH 2: Player-Visible SJIS Strings (Table 2L) ──────────────
    # These are SJIS strings with a trailing 0x0a before the null.
    sjis_patches = [
        # (offset, avail, expected_sjis_hex, new_ascii)
        # "コンティニューロード！\n" → "Continue loading!\n"
        (0x3F8240, 32, "8352839383658342836a8385815b838d815b836881490a",
         "Continue loading!\n"),
        # "取り付ける人がいないよ。\n" → "No one can equip it.\n"
        (0x3F8260, 32, "8ee682e8957482af82e9906c82aa82a282c882a282e681420a",
         "No one can equip it.\n"),
    ]

    print("\n--- Patch 2: Player-Visible Strings ---")
    for offset, avail, expected_hex, new_text in sjis_patches:
        expected_bytes = bytes.fromhex(expected_hex)
        actual = data[offset:offset + len(expected_bytes)]
        if actual == expected_bytes:
            encoded = new_text.encode("ascii")
            if len(encoded) + 1 > avail:
                print(f"  SKIP 0x{offset:06X}: new string too long ({len(encoded)+1} > {avail})")
                continue
            for i in range(avail):
                data[offset + i] = 0
            for i, b in enumerate(encoded):
                data[offset + i] = b
            print(f"  OK   0x{offset:06X}: -> {new_text!r}")
            patched_count += 1
        else:
            actual_str = data[offset:offset + avail]
            null_pos = actual_str.find(b"\x00")
            snippet = actual_str[:null_pos] if null_pos >= 0 else actual_str
            try:
                decoded = snippet.decode("ascii")
                print(f"  SKIP 0x{offset:06X}: already ASCII ({decoded!r})")
            except UnicodeDecodeError:
                print(f"  WARN 0x{offset:06X}: unexpected bytes, skipping (got {actual.hex()})")

    # ─── PATCH 3: NPC Names (Table 2F) ─────────────────────────────────
    # At 0x3C93B0: two NPC names stored as LE uint16 glyph IDs, terminated by 0xFFFF
    # Layout (from recon):
    #   Name 1: 5 glyphs + 3x 0xFFFF padding  = 8 uint16 slots (16 bytes)
    #   Name 2: 4 glyphs + 4x 0xFFFF padding  = 8 uint16 slots (16 bytes) -- but actually 16 slots
    # Total region: 0x3C93B0 to 0x3C93D0 (first 24 uint16 = 48 bytes)

    NPC_OFFSET = 0x3C93B0
    NAME1_SLOTS = 8   # 16 bytes for name 1 entry
    NAME2_SLOTS = 16  # remaining 16 slots (includes padding/pointers after)

    # Expected original glyph IDs for verification
    expected_name1 = [196, 224, 93, 232, 193, 0xFFFF, 0xFFFF, 0xFFFF]
    expected_name2_prefix = [232, 265, 93, 212, 0xFFFF]

    print("\n--- Patch 3: NPC Names ---")

    # Read current data
    name1_data = struct.unpack("<8H", data[NPC_OFFSET:NPC_OFFSET + 16])
    name2_data = struct.unpack("<5H", data[NPC_OFFSET + 16:NPC_OFFSET + 26])

    if list(name1_data) == expected_name1:
        # Encode "Emilia" as glyph IDs, pad with 0xFFFF
        new_name1 = encode_glyph_ids("Emilia")
        # Pad remaining slots with 0xFFFF
        remaining = NAME1_SLOTS - len("Emilia")
        new_name1 += b"\xff\xff" * remaining
        data[NPC_OFFSET:NPC_OFFSET + 16] = new_name1
        print(f"  OK   0x{NPC_OFFSET:06X}: エミーリア -> 'Emilia' (6 glyphs + {remaining} pad)")
        patched_count += 1
    else:
        print(f"  WARN 0x{NPC_OFFSET:06X}: name 1 mismatch, got {list(name1_data)}")

    name2_offset = NPC_OFFSET + 16
    if list(name2_data) == expected_name2_prefix:
        # Encode "Lute" as glyph IDs, pad with 0xFFFF to fill 8 slots
        new_name2 = encode_glyph_ids("Lute")
        # The name2 entry has 4 glyphs originally + many 0xFFFF
        # Keep it to 8 slots (same as name1 region size)
        name2_total_slots = 8
        remaining = name2_total_slots - len("Lute")
        new_name2 += b"\xff\xff" * remaining
        data[name2_offset:name2_offset + name2_total_slots * 2] = new_name2
        print(f"  OK   0x{name2_offset:06X}: リュート -> 'Lute' (4 glyphs + {remaining} pad)")
        patched_count += 1
    else:
        print(f"  WARN 0x{name2_offset:06X}: name 2 mismatch, got {list(name2_data)}")

    # ─── PATCH 4: Banner Glyph IDs (新規登録 -> "New Reg.") ─────────────
    # The chargen banner "新規登録" is rendered using 4 EXE menu struct
    # records that reference R1272 font tile glyph IDs.  Each record has
    # a pair of glyph IDs (left/right 12x12 tiles composing one kanji).
    # We replace these with ASCII letter glyph IDs so the font atlas can
    # keep the original kanji tiles for stat label usage (avoids collision
    # with stat_719/720/721 entries in menu_labels.csv).
    #
    # Display order: 新(Ne) 規(w ) 登(Re) 録(g.) -> "New Reg."

    print("\n--- Patch 4: Banner Glyph IDs (新規登録 -> New Reg.) ---")
    banner_patches = [
        # (record_offset, old_g1, old_g2, new_g1, new_g2, label)
        (0x3C33F0, 719, 720, 46, 69, "新 -> Ne"),   # N=46, e=69
        (0x3C3428, 721, 722, 87,  0, "規 -> w_"),   # w=87, space=0
        (0x3C3268, 705, 706, 50, 69, "登 -> Re"),   # R=50, e=69
        (0x3C32A0, 707, 708, 71, 14, "録 -> g."),   # g=71, .=14
    ]

    for rec_off, old_g1, old_g2, new_g1, new_g2, label in banner_patches:
        changes = 0
        # Scan all u16 positions in the 56-byte record
        for i in range(0, 56, 2):
            val = struct.unpack_from("<H", data, rec_off + i)[0]
            if val == old_g1:
                struct.pack_into("<H", data, rec_off + i, new_g1)
                changes += 1
            elif val == old_g2:
                struct.pack_into("<H", data, rec_off + i, new_g2)
                changes += 1
        if changes > 0:
            print(f"  OK   0x{rec_off:06X}: {label} ({changes} u16 values patched)")
            patched_count += 1
        else:
            # Check if already patched
            check_val = struct.unpack_from("<H", data, rec_off + 26)[0]
            if check_val == new_g1:
                print(f"  SKIP 0x{rec_off:06X}: {label} (already patched)")
            else:
                print(f"  WARN 0x{rec_off:06X}: {label} (expected g1={old_g1}, got {check_val})")

    # ─── Write output ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    print(f"\n=== Summary: {patched_count} patches applied ===")
    print(f"Written to {dst} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
