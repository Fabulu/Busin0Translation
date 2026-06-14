"""
patch_exe.py  –  EXE binary patch accumulator for Busin 0 (SLPM_653.78)

Reads the original EXE, applies translation patches, writes patched output.
Patches applied:
  1. Save slot names       (Table 2G)  – fullwidth SJIS → ASCII
  2. Player-visible strings (Table 2L) – SJIS → ASCII
  3. NPC names              (Table 2F) – LE uint16 glyph IDs
  4. Banner glyph IDs       (bytes 24-47) – kanji pair tiles → ASCII
  5. Banner byte-50 glyph   (byte 50)     – third glyph ref per record
  6. NOP chargen RenderAllTiles            – hide kanji overlay
  7. Chargen gender glyphs                 – 男/女 → ♂/♀
  8. Font widths for name uppercase 121-146 – copy from 33-58
  9. Keyboard F/M metrics fix              – force non-zero for glyphs 38,45,70,77
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

    # ─── PATCH 5: Banner byte-50 glyph IDs (新規登録 -> "new ") ─────────
    # Each banner record has a THIRD glyph reference at byte 50 (offset +50
    # from record start).  Patch 4 handled bytes 24-47; this patch fixes
    # the remaining glyph at byte 50 so the full banner reads correctly.
    #
    # Display order: 新(n) 規(e) 登(w) 録( ) -> "new "

    print("\n--- Patch 5: Banner byte-50 glyph IDs ---")
    banner_byte50_patches = [
        # (abs_offset, expected_old, new_glyph, label)
        (0x3C3422, 498, 46, "rec 0x3C33F0 byte50: glyph 498 -> 46 (n)"),
        (0x3C345A, 499, 37, "rec 0x3C3428 byte50: glyph 499 -> 37 (e)"),
        (0x3C329A, 491, 55, "rec 0x3C3268 byte50: glyph 491 -> 55 (w)"),
        (0x3C32D2, 492,  0, "rec 0x3C32A0 byte50: glyph 492 ->  0 (space)"),
    ]

    for abs_off, old_val, new_val, label in banner_byte50_patches:
        cur = struct.unpack_from("<H", data, abs_off)[0]
        if cur == old_val:
            struct.pack_into("<H", data, abs_off, new_val)
            print(f"  OK   0x{abs_off:06X}: {label}")
            patched_count += 1
        elif cur == new_val:
            print(f"  SKIP 0x{abs_off:06X}: {label} (already patched)")
        else:
            print(f"  WARN 0x{abs_off:06X}: {label} (expected {old_val}, got {cur})")

    # ─── PATCH 6: Mode-gated RenderAllTiles trampoline ────────────────
    # (chargen kanji hidden, PORTRAITS PRESERVED)
    # RenderAllTiles (VA 0x30B840) is the universal System-2 tile renderer: it
    # draws BOTH the chargen kanji overlay AND every scene/dialogue PORTRAIT, via
    # the shared per-frame dispatcher 0x2F2490 (screen mode 5=chargen / 7=scene /
    # 8=dungeon-combat).  The OLD blanket NOP of its ONLY call (JAL 0x30B840 @
    # VA 0x2F2568 / file 0x1F25E8) hid the kanji but COLLATERALLY KILLED ALL
    # PORTRAITS (user-confirmed: reverting the NOP restores them).  Instead we
    # route the call through a trampoline in the code cave at VA 0x4B0DD0 (file
    # 0x3B0E50; 6688 zero bytes, no inbound refs) that reads the master screen-
    # mode global gp-0x62d8 (RAM 0x4FED18; the EXE itself compares it to ==8 at
    # VA 0x2F2270) and SKIPS RenderAllTiles ONLY when mode==5 (every chargen
    # sub-screen), tail-calling it via `j` (preserving $ra) for every other
    # frame.  Net: chargen kanji still hidden; portraits render everywhere else.
    # Trampoline (VA 0x4B0DD0): lbu $v0,-0x62d8($gp); addiu $at,$zero,5;
    #   beq $v0,$at,0x4B0DE8; nop; j 0x30B840; nop; jr $ra; nop.
    print("\n--- Patch 6: Mode-gated RenderAllTiles trampoline (portraits + clean chargen) ---")
    SITE = 0x1F25E8                       # JAL 0x30B840 (VA 0x2F2568)
    CAVE = 0x3B0E50                       # code cave (VA 0x4B0DD0)
    JAL_RAT = struct.pack("<I", 0x0C0C2E10)   # original JAL 0x30B840
    JAL_CAVE = 0x0C12C374                      # JAL 0x4B0DD0 (to trampoline)
    NOP4 = b"\x00\x00\x00\x00"
    TRAMP = bytes.fromhex(
        "289d8293" "05000124" "03004110" "00000000"
        "102e0c08" "00000000" "0800e003" "00000000")
    site = bytes(data[SITE:SITE + 4])
    cave = bytes(data[CAVE:CAVE + len(TRAMP)])
    if site not in (JAL_RAT, NOP4, struct.pack("<I", JAL_CAVE)):
        print(f"  WARN 0x{SITE:06X}: expected JAL 0x30B840 / NOP / JAL-cave, got {site.hex()}")
    elif cave != b"\x00" * len(TRAMP) and cave != TRAMP:
        print(f"  WARN 0x{CAVE:06X}: code cave not zero/trampoline ({cave[:8].hex()}...) — Patch 6 SKIPPED")
    else:
        data[CAVE:CAVE + len(TRAMP)] = TRAMP
        struct.pack_into("<I", data, SITE, JAL_CAVE)
        print(f"  OK   0x{CAVE:06X}: 32-byte mode-gate trampoline (skip RenderAllTiles iff mode==5)")
        print(f"  OK   0x{SITE:06X}: JAL 0x30B840 -> JAL 0x4B0DD0 (trampoline)")
        patched_count += 1

    # ─── PATCH 7: Chargen gender glyph IDs (男/女 -> ♂/♀) ──────────────
    # The chargen parameter table has hardcoded glyph IDs for gender display.
    # Original: 353 (male kanji) and 349 (female kanji) rendered via System B.
    # Patch to use 672 (♂) and 673 (♀) which have correct bitmaps in R2100.
    print("\n--- Patch 7: Chargen gender glyphs (353->672, 349->673) ---")
    gender_patches = [
        (0x3C289E, 353, 672, "male: 353 -> 672 (♂)"),
        (0x3C28E6, 349, 673, "female: 349 -> 673 (♀)"),
    ]
    for off, old_val, new_val, label in gender_patches:
        cur = struct.unpack_from("<H", data, off)[0]
        if cur == old_val:
            struct.pack_into("<H", data, off, new_val)
            print(f"  OK   0x{off:06X}: {label}")
            patched_count += 1
        elif cur == new_val:
            print(f"  SKIP 0x{off:06X}: {label} (already patched)")
        else:
            print(f"  WARN 0x{off:06X}: {label} (expected {old_val}, got {cur})")

    # ─── PATCH 8: Font widths for duplicate uppercase at 121-146 ─────
    # R37 name groups use remapped glyph IDs 121-146 for uppercase A-Z
    # (avoiding keyboard metrics pollution at 33-58). Copy the font widths
    # from positions 33-58 to 121-146 so names render with correct spacing.
    # (Moved from 95-120: those slots shared columns with lowercase j-~, causing
    # ~4-row cell overread artifacts: subscript marks on r/y, overbar on V.)
    WIDTH_TABLES = [0x3DDC48, 0x3DDD48, 0x3DDE48, 0x3DDF48]
    print("\n--- Patch 8: Font widths for name uppercase (121-146) ---")
    for tbl in WIDTH_TABLES:
        for i in range(26):
            src_off = tbl + 33 + i    # original A-Z width
            dst_off = tbl + 121 + i   # duplicate slot width
            data[dst_off] = data[src_off]
        print(f"  OK   0x{tbl:06X}: copied widths 33-58 -> 121-146")
        patched_count += 1

    # ─── PATCH 9: Keyboard F/M metrics fix ─────────────────────────────
    # The keyboard atlas builder at VA 0x463680 has an unrolled loop that
    # calls JAL 0x3A2D10 for each glyph to fetch font metrics (width).
    # For glyphs F(38), M(45), f(70), m(77), the R37 name group data
    # pollutes the font metrics table, returning 0 width, which causes
    # these keys to render as invisible/collapsed on the chargen keyboard.
    #
    # Fix: Replace each JAL+delay-slot with ADDIU v0,zero,1 + NOP.
    # This forces a non-zero width (1) so the glyph renders normally.
    # The SH v0 instruction after each block stores the result correctly.
    #
    # Pattern per glyph (28-byte blocks starting at file 0x36376C):
    #   ADDIU a3, zero, <glyph_id>   (untouched)
    #   JAL 0x3A2D10  -> ADDIU v0, zero, 1  (0x24020001)
    #   DADDU t0,s3,zero -> NOP              (0x00000000)
    #   SH v0, <off>(s4)                     (untouched)

    print("\n--- Patch 9: Keyboard F/M metrics fix (glyphs 38,45,70,77) ---")
    kbd_fm_patches = [
        # (jal_file_offset, glyph_id, label)
        (0x363B78, 38, "F(38)"),
        (0x363C3C, 45, "M(45)"),
        (0x363EF8, 70, "f(70)"),
        (0x363FBC, 77, "m(77)"),
    ]

    expected_jal_bytes = struct.pack("<I", 0x0C0E8B44)   # JAL 0x3A2D10
    expected_daddu     = struct.pack("<I", 0x0260402D)   # DADDU t0, s3, zero
    new_addiu_v0       = struct.pack("<I", 0x24020001)   # ADDIU v0, zero, 1
    new_nop            = struct.pack("<I", 0x00000000)   # NOP

    for jal_off, glyph_id, label in kbd_fm_patches:
        actual_jal   = data[jal_off:jal_off + 4]
        actual_daddu = data[jal_off + 4:jal_off + 8]

        if actual_jal == expected_jal_bytes and actual_daddu == expected_daddu:
            # Verify the ADDIU a3 before has the correct glyph ID
            addiu_a3 = struct.unpack_from("<I", data, jal_off - 4)[0]
            if (addiu_a3 >> 16) != 0x2407 or (addiu_a3 & 0xFFFF) != glyph_id:
                print(f"  WARN 0x{jal_off:06X}: {label} ADDIU a3 mismatch (0x{addiu_a3:08X}), skipping")
                continue
            data[jal_off:jal_off + 4] = new_addiu_v0
            data[jal_off + 4:jal_off + 8] = new_nop
            print(f"  OK   0x{jal_off:06X}: {label} JAL+DADDU -> ADDIU v0,1 + NOP")
            patched_count += 1
        elif actual_jal == new_addiu_v0 and actual_daddu == new_nop:
            print(f"  SKIP 0x{jal_off:06X}: {label} (already patched)")
        else:
            print(f"  WARN 0x{jal_off:06X}: {label} unexpected bytes ({actual_jal.hex()} {actual_daddu.hex()})")

    # ─── PATCH 10: Page-0 cursor validity for keyboard name buttons ───
    # The keyboard grid validity check at VA 0x494300 uses a page table
    # at VA 0x4DB100 (file 0x3DB180) to determine if a cell's glyph is a
    # valid cursor target. Page 0 (glyphs 0x0000-0x00FF) maps to sub_index
    # 9 which fails the type==5 check, making space cells unreachable.
    # Change page 0's sub_index from 9 to 0 so zero-padded keyboard cells
    # (where name gen buttons were) become reachable by the cursor.
    # Name gen is triggered by grid position (function pointer table),
    # not by glyph value, so space cells at button positions still work.
    print("\n--- Patch 10: Page-0 cursor validity ---")
    page0_off = 0x3DB180  # page table byte for page 0
    if data[page0_off] == 9:
        data[page0_off] = 0
        print(f"  OK   0x{page0_off:06X}: page 0 sub_index 9 -> 0")
        patched_count += 1
    elif data[page0_off] == 0:
        print(f"  SKIP 0x{page0_off:06X}: already patched")
    else:
        print(f"  WARN 0x{page0_off:06X}: expected 9, got {data[page0_off]}")

    # ─── PATCH 11: Dialogue line-pitch smoosh (24px -> 18px) ───────────
    # The boxed-dialogue text renderer advances the per-line Y cursor by a
    # hardcoded 24px: `addiu $v0,$v0,0x18` at VA 0x3079DC (file 0x207A5C).
    # English wraps to more lines than the JP original, so at 24px a 4th line
    # clips and a 5th overflows the fixed ~103px box. Tighten the pitch to
    # 18px so 4 lines fit comfortably (the user's "smoosh it a little"). This
    # is the DIALOGUE pitch ONLY -- do NOT touch the narration/menu pitch
    # constants at 0x2087F0 / 0x208D30 / 0x209824.
    print("\n--- Patch 11: Dialogue line-pitch smoosh (24 -> 18 px) ---")
    pitch_off = 0x207A5C
    pitch_word = struct.unpack_from("<I", data, pitch_off)[0]
    if pitch_word == 0x24420018:  # addiu v0,v0,0x18
        data[pitch_off] = 0x12     # 0x18 -> 0x12 (low byte of the immediate)
        print(f"  OK   0x{pitch_off:06X}: addiu v0,v0,24 -> 18")
        patched_count += 1
    elif pitch_word == 0x24420012:
        print(f"  SKIP 0x{pitch_off:06X}: already smooshed")
    else:
        print(f"  WARN 0x{pitch_off:06X}: expected 0x24420018, got 0x{pitch_word:08X}")

    # ─── Write output ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    print(f"\n=== Summary: {patched_count} patches applied ===")
    print(f"Written to {dst} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
