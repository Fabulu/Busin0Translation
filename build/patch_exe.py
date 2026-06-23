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

# single source of truth for proportional glyph metrics (advance + left-shift tables)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import glyph_metrics

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

    # ─── PATCH 11: Dialogue line-pitch (DEAD lever — superseded by Patch 12) ─
    # This patches the INTEGER pitch path `addiu $v0,$v0,0x18` at VA 0x3079DC.
    # GS-draw-stream tracing (Wave 1) proved this path is BYPASSED for live
    # dialogue: 0x3079D0 `bne metric,100` takes the FLOAT path (0x3079EC) unless
    # the runtime font_metric == 100, and it never is (~101-104), so the boxed
    # dialogue stayed 24px across 156 dumps even with this applied.  Harmless but
    # INERT — the real pitch lever is Patch 12 (the 0.24 float at 0x3076FC).
    print("\n--- Patch 11: Dialogue line-pitch INTEGER path (inert; see Patch 12) ---")
    pitch_off = 0x207A5C
    pitch_word = struct.unpack_from("<I", data, pitch_off)[0]
    if pitch_word == 0x24420018:  # addiu v0,v0,0x18
        data[pitch_off] = 0x12     # 0x18 -> 0x12 (low byte of the immediate)
        print(f"  OK   0x{pitch_off:06X}: addiu v0,v0,24 -> 18 (inert path)")
        patched_count += 1
    elif pitch_word == 0x24420012:
        print(f"  SKIP 0x{pitch_off:06X}: already 0x12")
    else:
        print(f"  WARN 0x{pitch_off:06X}: expected 0x24420018, got 0x{pitch_word:08X}")

    # ─── PATCH 12: Dialogue line-pitch FLOAT lever (24px -> 18px) ───────
    # The REAL boxed-dialogue per-line Y pitch is int(0.24 * font_metric), where
    # 0.24 is the float 0x3E75C28F assembled at VA 0x3076F8 (lui 0x3E75) + VA
    # 0x3076FC (ori 0xC28F), multiplied at 0x307714 and applied on the LIVE float
    # path at 0x3079EC (cvt.w.s $f20).  This path is what actually runs (Patch 11
    # is bypassed).  GS-draw-stream RE (Wave 1, func 0x307510, R1188 sprites at
    # TBP0=0x3000) measured 24px pitch in 156 dumps; the box frame is fixed
    # y=363..473 (~110px), so 24px fits only ~4 lines and lines 5+ draw off-box
    # and are lost.  Lowering 0.24 -> 0.18 makes the pitch int(0.18*~101)=18px so
    # ~6 lines fit.  Patch ONLY the low 2 bytes of the ori (the float mantissa);
    # X-advance/UV is an INDEPENDENT 0.24 at 0x30614C (the wide-letter-spacing
    # lever — NOT touched here).  NOTE: render-confirm with a fresh-boot GS dump
    # (expect ~18px) — the value 0.18 is render-plausible but not yet on-screen.
    print("\n--- Patch 12: Dialogue line-pitch FLOAT 0.24 -> 0.18 (fit ~6 lines) ---")
    fpitch_off = 0x20777C  # VA 0x3076FC: ori $v0,$v0,0xC28F  (0.24 float low half)
    fpitch_word = struct.unpack_from("<I", data, fpitch_off)[0]
    if fpitch_word == 0x3442C28F:                       # ori 0xC28F -> 0.24
        struct.pack_into("<I", data, fpitch_off, 0x344251EC)  # ori 0x51EC -> 0.18
        print(f"  OK   0x{fpitch_off:06X}: pitch float 0.24 -> 0.18")
        patched_count += 1
    elif fpitch_word == 0x344251EC:
        print(f"  SKIP 0x{fpitch_off:06X}: already 0.18")
    else:
        print(f"  WARN 0x{fpitch_off:06X}: expected 0x3442C28F, got 0x{fpitch_word:08X}")

    # ─── PATCH 13: Narration glyph advance 24px -> 18px + re-centering ──
    # The narration renderer (func 0x307da0, R1188 sprites at GS TBP0=0x3000)
    # advances every glyph by a fixed 24px on the default-metric (==100) INTEGER
    # path at VA 0x3097A4 `addiu v0,v0,0x18`.  Narration takes this integer path
    # (GS-dump-PROVEN: patching 0x3097A4 to 0x12 measured 18.0px per-glyph steps in
    # the user's Shift+F8 dumps 20260615173931/173938).  Lowering 0x18->0x12 makes
    # letters 18px (the user's chosen width).  But the line is CENTERED via a
    # glyph-COUNT formula: line-origin desc+0x3c = 224 - count*24 (the (c*2+c)<<3
    # idiom at VA 0x305988), consumed as x0 = (desc+0x3c)/2 + 167 = 279 - count*12.
    # At 24px that centers; at 18px the text would shift LEFT by count*3 unless the
    # count*24 term is reduced to count*18 in LOCKSTEP.  count*18 = ((c<<3)+c)<<1,
    # so the two-shift idiom changes: first sll sa 1->3, last sll sa 3->1, at BOTH
    # centering sites (desc+0x3c @0x305988/0x305990 and desc+0x3e @0x3059F8/0x305A00).
    # Result: x0 = (224 - count*18)/2 + 167 = 279 - count*9, re-centered for 18px.
    # The 0.18f at 0x3097B8 covers the float (wide-glyph metric!=100) path for
    # consistency.  Space-glyph narrowing is a SEPARATE diagnostic (not baked here).
    print("\n--- Patch 13: Narration advance 24->18px + re-center (count*24->*18) ---")
    narr = [
        (0x209824, 0x24420018, 0x24420012, "advance int 24->18 (0x3097A4)"),
        (0x209838, 0x3443C28F, 0x344351EC, "advance float 0.24->0.18 (0x3097B8)"),
        (0x205A08, 0x00052040, 0x000520C0, "center A sll 1->3 (0x305988)"),
        (0x205A10, 0x000420C0, 0x00042040, "center A sll 3->1 (0x305990)"),
        (0x205A78, 0x00052040, 0x000520C0, "center B sll 1->3 (0x3059F8)"),
        (0x205A80, 0x000420C0, 0x00042040, "center B sll 3->1 (0x305A00)"),
    ]
    for off, exp, new, desc in narr:
        word = struct.unpack_from("<I", data, off)[0]
        if word == exp:
            struct.pack_into("<I", data, off, new)
            print(f"  OK   0x{off:06X}: {desc}")
            patched_count += 1
        elif word == new:
            print(f"  SKIP 0x{off:06X}: already patched ({desc})")
        else:
            print(f"  WARN 0x{off:06X}: expected 0x{exp:08X}, got 0x{word:08X} ({desc})")

    # ─── PATCH 14: PROPORTIONAL narration spacing (advance LUT + draw-shift) ──
    # Replaces the old monospace space-only cave.  Each glyph advances by its OWN
    # ink width (tools/glyph_metrics.ADV = clamp(ink_width+3,6,23), space=9) AND is
    # drawn shifted left by its own left-bearing (glyph_metrics.LEFTSHIFT = ink_left)
    # so the ink starts at the pen -> UNIFORM 3px inter-letter gaps, no f/t collisions
    # (GS-dump + screenshot CONFIRMED in build/apply_prop_diag2.py / propdiag2, user-
    # approved).  Two trampolines, both in the 744B verified-clean rodata pad by the
    # interpreter handler table (never written across 30 scenes):
    #   STAGE 1 advance LUT cave @VA 0x4C7540 + 256B ADV table @0x4C7564; hook 0x3097A0
    #     (lui t0,0x4C; andi v1,s1,0xFF; addu t0; lbu v1,ADV[g]; penX += v1).
    #   STAGE 2 draw-shift cave @VA 0x4C7670 + 256B LEFTSHIFT table @0x4C7690; hook
    #     0x309750 (subtract LEFTSHIFT[g] from penX r7 before the draw-X add).
    # Tables come from tools/glyph_metrics.py — the SINGLE source the build wrap +
    # centering + tests all read, so they can never desync.  Plus the 3B per-line
    # re-center x24->x18 (0x308364/0x30836C) that Patch 13 missed.
    # KNOWN LIMITATION (Stage 3, see data/text_restructure_roadmap.md): line
    # centering still reserves count*18 (Patch 13), so lines drift ~11-34px with
    # proportional widths; summed-width centering is the remaining piece.
    print("\n--- Patch 14: PROPORTIONAL narration spacing (advance LUT + draw-shift) ---")
    P14_HOOK1, P14_CAVE1, P14_TBL1 = 0x209820, 0x3C75C0, 0x3C75E4   # VA 0x3097A0 / 0x4C7540 / 0x4C7564
    P14_HOOK2, P14_CAVE2, P14_TBL2 = 0x2097D0, 0x3C76F0, 0x3C7710   # VA 0x309750 / 0x4C7670 / 0x4C7690
    adv_cave = [0x3C08004C, 0x322300FF, 0x01034021, 0x91037564,
                0x87A201CE, 0x00431021, 0xA7A201CE, 0x080C25F8, 0x00000000]
    shift_cave = [0x3C01004C, 0x00310821, 0x90217690, 0x00E13823,
                  0x00EC6021, 0x080C25D6, 0x00000000]
    h1 = struct.unpack_from("<I", data, P14_HOOK1)[0]
    h2 = struct.unpack_from("<I", data, P14_HOOK2)[0]
    if struct.unpack_from("<I", data, P14_CAVE1)[0] == adv_cave[0] and h1 == 0x08131D50:
        print("  SKIP: proportional caves already installed")
    elif h1 == 0x87A201CE and h2 == 0x00EC6021:
        # Stage 1 — advance LUT
        for i, w in enumerate(adv_cave):
            struct.pack_into("<I", data, P14_CAVE1 + i * 4, w)
        data[P14_TBL1:P14_TBL1 + 256] = glyph_metrics.adv_table_256()
        struct.pack_into("<I", data, P14_HOOK1, 0x08131D50)      # j 0x4C7540
        struct.pack_into("<I", data, P14_HOOK1 + 4, 0x00000000)  # nop (delay slot)
        # Stage 2 — draw-shift
        for i, w in enumerate(shift_cave):
            struct.pack_into("<I", data, P14_CAVE2 + i * 4, w)
        data[P14_TBL2:P14_TBL2 + 256] = glyph_metrics.leftshift_table_256()
        struct.pack_into("<I", data, P14_HOOK2, 0x08131D9C)      # j 0x4C7670 (delay slot 0x309754 runs once)
        # 3B — per-line re-center x24 -> x18 (the site Patch 13 missed)
        for off, exp, new in [(0x2083E4, 0x00062040, 0x000620C0), (0x2083EC, 0x000420C0, 0x00042040)]:
            if struct.unpack_from("<I", data, off)[0] == exp:
                struct.pack_into("<I", data, off, new)
        print(f"  OK   advance LUT @0x4C7540 + draw-shift @0x4C7670 (avg {sum(glyph_metrics.ADV)/95:.1f}px); 3B re-center")
        patched_count += 1
    else:
        print(f"  WARN proportional caves not applied: hook1=0x{h1:08X} hook2=0x{h2:08X}")

    # ─── PATCH 19: CHARGEN Path-1 proportional spacing (advance LUT + draw-shift + summed centering)
    # The chargen prompt (R37) and description/personality (R38) glyph streams render through
    # Path 1 of the universal R1188 renderer func 0x307DA0 (data/chargen_spacing_backlog.md) —
    # NOT a separate R2100/R2138 font system.  Path 1 uses a FIXED 24px monospace pen
    # (`addiu v0,v0,0x18` @VA 0x308040) and a glyph-COUNT centering reserve (count*12 @VA
    # 0x307FBC..0x307FD4), giving the wide-monospace look seen in thing1-3/space1-6.  gid ==
    # char-32 CONFIRMED LIVE (thing2 eeMemory: "Select gender." u16-BE @0x12BD0AC are char-32
    # gids), the SAME index as glyph_metrics.ADV / build_v9 enc() / the Patch-14 resident tables.
    #
    # Three coordinated caves, all reading Patch-14's RESIDENT tables (no recomputed widths —
    # the #1-failure-mode gate):  ADV @VA 0x4C7564 (lbu 0x7564(0x4C0000)), LEFTSHIFT @VA
    # 0x4C7690 (lbu 0x7690(0x4C0000)).  Chargen pen is 0x1cc(sp) (narration uses 0x1ce(sp)) —
    # kept distinct so NO narration regression.  Caves live in the Patch-15-cleared rodata pad
    # 0x4D6600.. (file 0x3D6680; the run 0x4D65CE..0x4D6720 minus Patch-15's 0x4D65D0+0x28).
    # This pad is OFF the Patch-14 (0x4C7540-0x4C7790), Patch-20 (0x4C7860/0x4CAA30 NS caves),
    # Patch-6/16/18 caves — verified zero before each write.
    #
    #   STAGE 1 advance LUT  — hook 0x308040 (orig addiu v0,v0,0x18) -> j cave1; delay slot
    #     (orig sh v0,0x1cc(sp) @0x308044) -> nop.  cave1 @0x4D6600: re-read gid via lh
    #     v1,0x40(s1) (s1 NOT bumped until 0x308054, AFTER the advance); andi 0xFF; ADV[gid]
    #     from 0x7564(0x4C0000); pen(0x1cc(sp)) += ADV; store; j 0x308048 (past the orig store).
    #   STAGE 2 draw-shift (Option A, penX only — never hook inside shared draw 0x305E30) —
    #     hook 0x308018 (orig lh v1,0x1cc(sp)) -> j cave2; cave2 @0x4D6660: reload penX; gid via
    #     lh 0x40(s1); LEFTSHIFT[gid] from 0x7690(0x4C0000); penX(v1) -= LEFTSHIFT; j 0x30801C.
    #     Uses $at/$t9 ONLY ($t0 is LIVE here: set @0x308010, consumed @0x30802C).  Delay slot
    #     0x30801C (move a0,s5) is idempotent — left in place (runs once as delay, once on return).
    #   STAGE 3 summed-width centering — hook 0x307FBC (orig sll a0,a1,1, head of the count*12
    #     reserve) -> j cave3; displaced delay slot 0x307FC0 (orig addu a0,a0,a1) -> nop.  cave3
    #     @0x4D66A0: walk the line glyph array at s3+0x40 (LE i16 stride 2, -1 sentinel via bltz,
    #     EXACTLY the original count loop 0x307F54-0x307F84), SUM += ADV[gid]; sra SUM,1;
    #     pen(0x1cc(sp)) -= SUM/2; store; j 0x307FD8 (the existing store/continue target).  SUM
    #     accumulates in $t0 (DEAD here) — $v1 (=count) MUST be preserved: it flows to 0x307FE4.
    # Stage 1+3 ship TOGETHER (advance-without-centering = the documented drift bug); Stage 2 is
    # independent polish.  GATE: only install if Patch 14 installed its resident ADV table
    # (checked via the Patch-14 hook word @0x209820 == 0x08131D50).  file_off = VA - 0xFFF80.
    print("\n--- Patch 19: CHARGEN Path-1 proportional (advance LUT + draw-shift + summed centering) ---")
    P19_GATE = struct.unpack_from("<I", data, 0x209820)[0]   # Patch-14 HOOK1 (j 0x4C7540)
    # v122 RECON (chargenspaces.p2s, fresh, gp-0x62d8==5 CONFIRMED): the glyph cell at
    # lh 0x40(s1) is (char-32) << 8 — memory bytes [0x00, char-32], char-32 in the HIGH
    # byte of the LE halfword.  PROVEN: "Lives to hoard gold." @0xE148B2 decodes as cells
    # 0x2C00('L') 0x4900('i') ... (lo byte always 0x00, hi byte = char-32).  The v120 caves
    # `andi 0xFF` read the ZERO low byte -> gid=0 -> every glyph squashed to ADV[0]=9 (the
    # "wide/unformatted" look).  FIX: char-32 = cell >> 8 (srl 8), index resident ADV @0x7564.
    # ADV LUT confirmed live: ADV[' ']=9, ADV['M'-32=0x2D]=23.  Line-break cell 0xFEFF and
    # terminator 0xFFFF both have hi byte >=0x60 -> excluded from the width sum (cave3 sltiu).
    # SCOPE: all three stages gated on the screen-mode global lw $at,-0x62d8($gp) == 5 (chargen).
    # chargenspaces=5, mostbroken(request)=7, town/narration=7 -> request/narration/dialogue
    # take the STOCK fallback (24px advance / count*12 reserve), byte-for-byte the v121 behavior.
    # NO BLAST RADIUS: the only behavioral change is inside `if mode==5`.
    #
    # cave1 (advance) @ VA 0x4D6600 / file 0x3D6680  -> j 0x308048
    p19_cave1 = [
        0x8F819D28,  # lw   $at, -0x62d8($gp)    ; at = screen mode (RAM 0x4FED18)
        0x86230040,  # lh   $v1, 0x40($s1)       ; cell (s1 not yet bumped); = (char-32)<<8
        0x24080005,  # li   $t0, 5
        0x14280008,  # bne  $at, $t0, STOCK(0x4D6630) ; mode!=5 -> stock 24px
        0x00031A02,  # srl  $v1, $v1, 8          ; (delay) char-32 = HIGH byte
        0x3C08004C,  # lui  $t0, 0x4C            ; t0 = 0x4C0000 (resident ADV @+0x7564)
        0x01034021,  # addu $t0, $t0, $v1
        0x91087564,  # lbu  $t0, 0x7564($t0)     ; ADV[char-32]
        0x87A201CC,  # lh   $v0, 0x1cc($sp)      ; pen
        0x00481021,  # addu $v0, $v0, $t0        ; pen += ADV
        0x10000003,  # b    STORE(0x4D6638)
        0x00000000,  # nop
        0x87A201CC,  # STOCK: lh $v0, 0x1cc($sp)
        0x24420018,  # addiu $v0, $v0, 0x18      ; stock 24px monospace (request/narration)
        0xA7A201CC,  # STORE: sh $v0, 0x1cc($sp)
        0x080C2012,  # j    0x308048             ; past the original store
        0x00000000,  # nop
    ]
    # cave2 (draw-shift, left-bearing) @ VA 0x4D6660 / file 0x3D66E0  -> j 0x30801C
    p19_cave2 = [
        0x8F999D28,  # lw   $t9, -0x62d8($gp)    ; t9 = screen mode (t0 is LIVE here)
        0x87A301CC,  # lh   $v1, 0x1cc($sp)      ; penX (displaced hook instruction)
        0x24180005,  # li   $t8, 5
        0x17380006,  # bne  $t9, $t8, DONE(0x4D6688) ; mode!=5 -> no shift
        0x86390040,  # lh   $t9, 0x40($s1)       ; (delay) cell
        0x0019CA02,  # srl  $t9, $t9, 8          ; char-32 = HIGH byte
        0x3C01004C,  # lui  $at, 0x4C            ; at = 0x4C0000 (resident LEFTSHIFT @+0x7690)
        0x00390821,  # addu $at, $at, $t9
        0x90217690,  # lbu  $at, 0x7690($at)     ; LEFTSHIFT[char-32]
        0x00611823,  # subu $v1, $v1, $at        ; penX -= LEFTSHIFT (draw-X only)
        0x080C2007,  # DONE: j 0x30801C
        0x00000000,  # nop
    ]
    # cave3 (summed-width centering) @ VA 0x4D66A0 / file 0x3D6720  -> j 0x307FD8
    p19_cave3 = [
        0x8F899D28,  # lw   $t1, -0x62d8($gp)    ; t1 = screen mode
        0x240A0005,  # li   $t2, 5
        0x152A0014,  # bne  $t1, $t2, STOCK(0x4D66FC) ; mode!=5 -> stock count*12
        0x87A201CC,  # lh   $v0, 0x1cc($sp)      ; (delay) pen (=0 at line start)
        0x26660040,  # addiu $a2, $s3, 0x40      ; a2 = &glyph[0]
        0x00004021,  # move  $t0, $zero          ; t0 = SUM
        0x3C04004C,  # lui   $a0, 0x4C           ; a0 = 0x4C0000 (resident ADV @+0x7564)
        0x84C50000,  # LOOP: lh $a1, 0($a2)      ; a1 = cell (signed)
        0x240BFFFF,  # li    $t3, -1
        0x10AB0009,  # beq   $a1, $t3, DONE(0x4D66EC) ; 0xFFFF terminator (matches draw loop)
        0x00053A02,  # srl   $a3, $a1, 8         ; (delay) char-32 / break-code
        0x2CE10060,  # sltiu $at, $a3, 0x60      ; at=1 iff real glyph (<0x60); 0xFE break => 0
        0x10200003,  # beq   $at, $zero, SKIP(0x4D66E0) ; skip 0xFEFF line-break cell
        0x00873821,  # addu  $a3, $a0, $a3       ; (delay)
        0x90E77564,  # lbu   $a3, 0x7564($a3)    ; ADV[char-32]
        0x01074021,  # addu  $t0, $t0, $a3       ; SUM += ADV
        0x24C60002,  # SKIP: addiu $a2, $a2, 2
        0x1000FFF5,  # b     LOOP(0x4D66BC)
        0x00000000,  # nop  (delay)
        0x00084043,  # DONE: sra $t0, $t0, 1     ; SUM/2
        0x00481023,  # subu  $v0, $v0, $t0       ; pen -= SUM/2 (center origin)
        0x10000005,  # b     WRITE(0x4D670C)
        0x00000000,  # nop
        0x00052040,  # STOCK: sll $a0, $a1, 1    ; original count*12 reserve
        0x00852021,  # addu  $a0, $a0, $a1
        0x00042080,  # sll   $a0, $a0, 2         ; a0 = a1*12
        0x00441023,  # subu  $v0, $v0, $a0
        0xA7A201CC,  # WRITE: sh $v0, 0x1cc($sp)
        0x080C1FF6,  # j     0x307FD8            ; existing store/continue target
        0x00000000,  # nop
    ]
    P19_H1, P19_C1, P19_J1 = 0x2080C0, 0x3D6680, 0x08135980  # VA 0x308040 / cave1 0x4D6600
    P19_H2, P19_C2, P19_J2 = 0x208098, 0x3D66E0, 0x08135998  # VA 0x308018 / cave2 0x4D6660
    P19_H3, P19_C3, P19_J3 = 0x20803C, 0x3D6720, 0x081359A8  # VA 0x307FBC / cave3 0x4D66A0
    # v122: RE-ENABLED.  The v120 revert reasons are both resolved:
    #  (1) "andi 0xFF -> gid=0" -> caves now read the HIGH byte (srl 8); chargenspaces.p2s
    #      confirms cells are (char-32)<<8, so srl 8 yields the correct glyph index.
    #  (2) "no request/chargen discriminator" -> all three stages now gate on the screen-mode
    #      global lw $at,-0x62d8($gp) == 5 (chargen).  mostbroken(request)=7 -> stock fallback.
    if P19_GATE != 0x08131D50:
        print(f"  WARN Patch 14 not installed (hook=0x{P19_GATE:08X}) -> Patch 19 SKIPPED")
    else:
        h1 = struct.unpack_from("<I", data, P19_H1)[0]
        h2 = struct.unpack_from("<I", data, P19_H2)[0]
        h3 = struct.unpack_from("<I", data, P19_H3)[0]
        c1_free = all(b == 0 for b in data[P19_C1:P19_C1 + len(p19_cave1) * 4])
        c2_free = all(b == 0 for b in data[P19_C2:P19_C2 + len(p19_cave2) * 4])
        c3_free = all(b == 0 for b in data[P19_C3:P19_C3 + len(p19_cave3) * 4])
        c1_done = struct.unpack_from("<I", data, P19_C1)[0] == p19_cave1[0]
        already = (h1 == P19_J1 and h2 == P19_J2 and c1_done)  # Stage 3 intentionally unhooked
        # STAGE 3 INTENTIONALLY NOT HOOKED (v122 draw-math recon).  The draw-X is
        #   draw_X = penX(0x1cc) + box_origin(lh 0x3e(s3)) + s7,   where s7 = count*12
        #   (computed from $v1=count @0x307FE4..0x307FF0).  The ORIGINAL centering block
        #   (0x307FBC..0x307FD4) sets 0x1cc = 0 - count*12, so the two count*12 terms
        #   CANCEL: draw_X = box_origin + penX_advance.  With Stage 1 supplying a
        #   PROPORTIONAL penX advance, the text is already LEFT-ANCHORED at box_origin
        #   with correct per-glyph spacing — exactly the chargenspaces.p2s fix (the boxes
        #   were "too wide" purely from the 24px monospace advance, NOT mis-centering).
        #   Re-routing 0x1cc to -SUM/2 would leave the s7=count*12 term UNCANCELLED and
        #   shove the text right by count*12 - SUM/2 (a regression).  So Stage 3 stays
        #   pristine (stock count*12 reserve cancels s7); p19_cave3 is retained above for
        #   reference only.  Stage 1 + Stage 2 are the shipped fix.
        if already:
            print("  SKIP: chargen proportional caves already installed")
        elif (h1 == 0x24420018 and h2 == 0x87A301CC
              and (c1_free or c1_done) and c2_free):
            # Stage 1 — advance LUT cave + trampoline (also nop the displaced store @0x308044)
            for i, w in enumerate(p19_cave1):
                struct.pack_into("<I", data, P19_C1 + i * 4, w)
            struct.pack_into("<I", data, P19_H1, P19_J1)          # j cave1
            struct.pack_into("<I", data, P19_H1 + 4, 0x00000000)  # delay slot (was sh) -> nop
            # Stage 2 — draw-shift cave + trampoline (delay slot 0x30801C left: idempotent move)
            for i, w in enumerate(p19_cave2):
                struct.pack_into("<I", data, P19_C2 + i * 4, w)
            struct.pack_into("<I", data, P19_H2, P19_J2)          # j cave2
            print(f"  OK   Stage 1 advance LUT  @0x4D6600 (hook 0x308040, gate mode==5, ADV 0x7564, srl-8)")
            print(f"  OK   Stage 2 draw-shift   @0x4D6660 (hook 0x308018, gate mode==5, LEFTSHIFT 0x7690)")
            print(f"  ---  Stage 3 NOT hooked: stock count*12 cancels s7 -> left-anchored proportional")
            patched_count += 1
        else:
            print(f"  WARN Patch 19 not applied: h1=0x{h1:08X} h2=0x{h2:08X} "
                  f"c1_free={c1_free} c2_free={c2_free}")

    # ─── PATCH 20: NARRATION FIXED LEFT-MARGIN origin (replaces summed-width centering) ──
    # USER PREFERENCE (aheavyfog.p2s / noonewasinsight.p2s screenshots): narration must be
    # LEFT-ALIGNED with a CONSTANT left x for every line — NOT centered/right-anchored.
    # The old centering (Patch 13 count*18 reserve, and the v120 summed-width caves that
    # this block formerly installed) computed  desc+0x3c = BASE - line_width, so a WIDER
    # line started FURTHER LEFT and the right side of the box went unused (PROVEN in
    # aheavyfog: line left-edges measured 50/43/35 game-px for the 15/16/17-char lines,
    # i.e. left = window_x + 224 - count*18 — exact count*18 match).  The brief calls this
    # "summed-width CENTERING mis-aligns: every line shifts further left, right unused."
    #
    # FIX = make desc+0x3c / desc+0x3e a CONSTANT (independent of glyph count/width) so
    # every line shares the SAME left origin.  The renderer draws each glyph at
    # X = window_x + desc+0x3c + penX (penX starts 0 per line @0x30810C, +ADV per glyph),
    # so a constant desc+0x3c == a fixed left margin.  We patch the centering arithmetic
    # IN PLACE at the two store sites (NO cave needed):
    #   NS_A (desc+0x3c, horizontal origin — PROVEN horizontal by the screenshot count*18
    #     spread): VA 0x305980 `li $v1,0xE0` -> `li $v1,LEFT_A`; VA 0x305994
    #     `subu $v1,$v1,$a0` (the count*18 reserve) -> nop.  Result: sh $v1=LEFT_A,0x3c(s5).
    #   NS_B (desc+0x3e, the paired secondary origin): VA 0x3059F0 `li $v1,0xC0` ->
    #     `li $v1,LEFT_B`; VA 0x305A04 `subu $v1,$v1,$a0` -> nop.
    # LEFT_A/LEFT_B keep the original BASE delta (224-192 = 32) so the engine's two
    # anchors stay in their stock geometric relationship, just pinned to a fixed left.
    #   LEFT_A = -56 -> game_x ≈ 40 (window_x≈96 from aheavyfog anchor; clean left margin).
    #   LEFT_B = -88 (= LEFT_A - 32, preserving the original 0xE0/0xC0 delta).
    # INTERIM KNOB: text too far LEFT -> raise LEFT_A (e.g. -56 -> -46); too far RIGHT ->
    # lower (e.g. -56 -> -66).  Keep LEFT_B = LEFT_A - 32.
    #
    # SCOPE (NO BLAST RADIUS — verified by disasm):
    #   * These two stores fire ONLY on the alignment==3 path: gated by `bne s5+0xa6,0`
    #     (@0x305914 -> skip both) AND `bne s4+0x2a6,3` (@0x305978 -> skip 0x3c) /
    #     `bne s4+0x2a7,3` (@0x3059E8 -> skip 0x3e).  Non-narration text (align!=3) NEVER
    #     reaches these stores, so its origin is untouched.
    #   * The REQUEST MENU does NOT use this dispatcher at all: the request title/list and
    #     "REQUEST LIST" header render via draw_clamp12 @0x3A3300 (callers 0x155B60 /
    #     0x15CDF4 / 0x15CE4C / 0x15D778 / 0x15DBA8 — the tavern/request menu funcs), which
    #     is a SEPARATE renderer with ZERO calls into the 0x303C60 dispatcher that owns
    #     0x305988/0x3059F8.  Confirmed: NO `jal 0x303C60` exists anywhere; the dispatcher
    #     is reached only as a scheduler/handler node for the narration/message surface.
    #     => This patch CANNOT touch the request menu (the v120 "r t" break is Patch 19's
    #     chargen path 0x307DA0/0x308040, a different surface — out of B4's scope).
    #   * This SUPERSEDES Patch 13's count-shift edits (0x305988/0x305990/0x3059F8/0x305A00)
    #     — those sll's still run but their result $a0 is discarded once the subu is nop'd.
    # NO Patch-14 gate needed (no resident-table read here); installs unconditionally.
    #
    # DEAD-PER-RAM (2026-06-20 fresh-save recon): these four sites are on the
    # alignment==3 (mode-3) path of func 0x303C60.  Live narration descriptor
    # 0x565150[0]=0x1137AC0 has desc+0x2a6==0 / desc+0x2a7==0 / desc+0x2a8==0 =>
    # ALIGN-MODE 0, which routes through the X-dispatcher count*12 block @0x308308
    # (the PATCH 23 site), NOT this mode-3 path.  Patch 20's installed bytes
    # (li v1,-56 / nop) are therefore on a DEAD path for narration — ZERO runtime
    # effect.  They are LEFT IN PLACE (harmless, idempotent re-run) rather than
    # reverted, to avoid a spurious WARN; the load-bearing left-align is Patch 23.
    print("\n--- Patch 20: NARRATION fixed LEFT-MARGIN origin (DEAD-per-RAM mode-3 path; left as-is) ---")
    LEFT_A = -56            # desc+0x3c constant -> game_x ≈ 40 (left margin)
    LEFT_B = LEFT_A - 32    # desc+0x3e constant -> preserve original 0xE0-0xC0 = 32 delta
    li_a = 0x24030000 | (LEFT_A & 0xFFFF)   # li $v1, LEFT_A
    li_b = 0x24030000 | (LEFT_B & 0xFFFF)   # li $v1, LEFT_B
    NOP = 0x00000000
    SUBU = 0x00641823       # subu $v1,$v1,$a0  (the count*K reserve to kill)
    p20_sites = [
        # (file_off, expected_orig, new_word, desc)
        (0x205A00, 0x240300E0, li_a, "NS_A li v1,0xE0 -> li v1,%d (0x305980)" % LEFT_A),
        (0x205A14, SUBU,       NOP,  "NS_A subu (count*18 reserve) -> nop (0x305994)"),
        (0x205A70, 0x240300C0, li_b, "NS_B li v1,0xC0 -> li v1,%d (0x3059F0)" % LEFT_B),
        (0x205A84, SUBU,       NOP,  "NS_B subu (count*18 reserve) -> nop (0x305A04)"),
    ]
    for off, exp, new, desc in p20_sites:
        word = struct.unpack_from("<I", data, off)[0]
        if word == new:
            print(f"  SKIP 0x{off:06X}: already patched ({desc})")
        elif word == exp:
            struct.pack_into("<I", data, off, new)
            print(f"  OK   0x{off:06X}: {desc}")
            patched_count += 1
        else:
            print(f"  WARN 0x{off:06X}: expected 0x{exp:08X}, got 0x{word:08X} ({desc})")

    # ─── Patch 21: REVERTED (mode-2 origin @0x308378 — DEAD for narration) ─
    # v121 set this site to `move $a0,$a1` (0x00A02021) on the ASSUMPTION that live
    # narration drew via the alignment-dispatcher MODE-2 branch (lbu desc+0x2a7 == 2).
    # FRESH-SAVE RECON DISPROVES THAT (2026-06-20, heavyfog2/leftfield/mostbroken
    # eeMemory + GS): the live narration descriptor 0x565150[0]=0x1137AC0 has
    # desc+0x2a7(ALIGN)==0, so the X-dispatcher at 0x3082E4 (`bne a1,1`) jumps to the
    # align!=1 count*12 block @0x308308 and NEVER reaches the mode-2 check (0x308338
    # `bne a1,2`) or 0x308378.  => Patch 21 is PROVEN DEAD for narration, and its
    # `move a0,a1` ALSO had a false premise (a1 != box-left: leftfield wrote OFF the
    # LEFT edge).  The real left-align fix is PATCH 23 below at 0x308328.
    # REVERT: ship 0x308378 PRISTINE (0x00A42021 = addu a0,a1,a0).  This block writes
    # the ORIGINAL word over any stale 0x00A02021 a prior build left behind.
    print("\n--- Patch 21: REVERTED (restore mode-2 origin @0x308378 pristine; dead for narration) ---")
    P21_OFF = 0x2083F8        # VA 0x308378
    P21_ORIG = 0x00A42021     # addu $a0,$a1,$a0  (pristine: base + slack)
    P21_STALE = 0x00A02021    # move $a0,$a1      (the v121 dead edit to undo)
    p21 = struct.unpack_from("<I", data, P21_OFF)[0]
    if p21 == P21_ORIG:
        print(f"  SKIP 0x{P21_OFF:06X}: already pristine (0x{P21_ORIG:08X})")
    elif p21 == P21_STALE:
        struct.pack_into("<I", data, P21_OFF, P21_ORIG)
        print(f"  OK   0x{P21_OFF:06X}: restored move a0,a1 -> addu a0,a1,a0 (pristine, Patch 21 reverted)")
        patched_count += 1
    else:
        print(f"  WARN 0x{P21_OFF:06X}: expected 0x{P21_ORIG:08X} or 0x{P21_STALE:08X}, got 0x{p21:08X} -- left as-is")

    # ─── PATCH 22: REQUEST body overflow — path-B reserve count*24 -> count*18 ──
    # ROOT CAUSE (live-RAM proven, ramdumps/mostbroken.p2s + stillrt.p2s):
    #   The tavern request DESCRIPTION body renders through the universal R1188
    #   renderer's Block-2 (pen sp+0x1ce), reached via the align-mode dispatcher's
    #   v1==2 branch (addiu v0,zero,2; bne v1,v0 @0x308928).  Block-2 self-centers
    #   each line: origin = box_base + (box_width - reserve)/2, where the reserve
    #   idiom @0x30896C-0x308974 computes count*24 (sll1/addu/sll3 = a0*24) while
    #   the SHARED per-glyph advance is the Patch-14 proportional LUT (avg ~18px,
    #   from tools/glyph_metrics.py).  reserve(24) > advance(18) ⇒ the centering
    #   reserves a span ~33% too wide ⇒ origin lands too far LEFT and the line runs
    #   past the RIGHT edge (the both-edges overflow + garbled 'nce/laume/accept'
    #   columns in mostbroken).  The body is plain text — only 0xFFFE/0xFFFF codes,
    #   NO 0xFFD0-D7 tabs (live-decoded @0xE37880) — so the old tab-ladder theory
    #   is refuted, and mostbroken's narration array @0x565150 is empty so the body
    #   is NOT on the slot-0 narration path.
    # FIX (mirrors Patch-14's confirmed mode-2 0x308364/0x30836C count*24->18, same
    #   algebraic transform, v0/a0 register pair instead of a0/a2):
    #   (a) reserve idiom -> a0*18 via ((a0<<3)+a0)<<1:
    #       0x30896C  sll v0,a0,1  (0x00041040) -> sll v0,a0,3  (0x000410C0)
    #       0x308970  addu v0,v0,a0 (0x00441021) UNCHANGED
    #       0x308974  sll v0,v0,3  (0x000210C0) -> sll v0,v0,1  (0x00021040)
    #       (NOTE: P1's proposed 0x000420C0 at 0x30896C was a BUG — it decodes
    #        sll a0,a0,3, clobbering a0 that the next addu needs; correct rd=v0
    #        encoding is 0x000410C0.  RECON-corrected, live-decode verified.)
    #   (b) Block-2 default-metric per-glyph advance 24 -> 18 at BOTH pen-0x1ce
    #       sites so a default-metric glyph steps 18 to match the reserve:
    #       0x308CB0  addiu v0,v0,0x18 -> addiu v0,v0,0x12
    #       0x308D7C  addiu v0,v0,0x18 -> addiu v0,v0,0x12  (sibling v1==7 branch)
    # SCOPING (live-confirmed disjoint from narration — no regression):
    #   Path-B is pen sp+0x1ce, entered only via the align v1==2 branch.  Live
    #   narration (heavyfog2/leftfield) has desc@0x1137AC0 +0x2a8==0 -> the OTHER
    #   path (origin 0x308328, pen 0x1cc) and its advance is Block-3 @0x3097A4
    #   (Patch-14 LUT hook @0x3097A0) — DISJOINT file offsets.  Boxed dialogue is
    #   func 0x307510; chargen is Block-A pen-0x1cc @0x308040.  screen-mode gp-0x62d8
    #   ==7 for BOTH narration and request, so it is NOT a usable gate — the align-
    #   byte routing (v1==2 vs the 0x2a8==0 narration path) is the discriminator.
    #   18px target = avg of the resident Patch-14 ADV LUT (tools/glyph_metrics.py).
    print("\n--- Patch 22: REQUEST body reserve count*24->*18 + Block-2 advance 24->18 ---")
    p22_sites = [
        # (file_off, old_word, new_word, desc)
        (0x2089EC, 0x00041040, 0x000410C0, "reserve idiom head sll v0,a0,1 -> sll v0,a0,3 (0x30896C)"),
        (0x2089F4, 0x000210C0, 0x00021040, "reserve idiom tail sll v0,v0,3 -> sll v0,v0,1 (0x308974)"),
        (0x208D30, 0x24420018, 0x24420012, "Block-2 advance 24->18 (0x308CB0)"),
        (0x208DFC, 0x24420018, 0x24420012, "Block-2 advance 24->18 sibling (0x308D7C)"),
    ]
    for off, old, new, desc in p22_sites:
        word = struct.unpack_from("<I", data, off)[0]
        if word == old:
            struct.pack_into("<I", data, off, new)
            print(f"  OK   0x{off:06X}: {desc}")
            patched_count += 1
        elif word == new:
            print(f"  SKIP 0x{off:06X}: already patched ({desc})")
        else:
            print(f"  WARN 0x{off:06X}: expected 0x{old:08X}, got 0x{word:08X} ({desc})")
    # 0x308970 addu v0,v0,a0 (0x00441021) is intentionally NOT touched — it is the
    # middle term of the *18 idiom and is identical in the *24 and *18 forms.

    # ─── PATCH 23: NARRATION true LEFT-FLUSH at box origin (X-dispatcher 0x308328) ─
    # ROOT CAUSE (2026-06-20 fresh-save recon: heavyfog2/leftfield/mostbroken
    #   eeMemory.bin VA==offset + GS.bin, custom MIPS-LE decoder):
    #   Live narration descriptor 0x565150[0]=0x1137AC0 has boxX(desc+0x3c)==0 and
    #   ALIGN(desc+0x2a7)==0.  The X-dispatcher in func 0x307DA0:
    #     0x3082DC  lbu  a1,0x2a7(a0)   ; a1 = align = 0
    #     0x3082E0  addiu a0,zero,1
    #     0x3082E4  bne  a1,a0,0x308308 ; 0!=1 -> align!=1 block (count*12 reserve)
    #     0x308310  lh   a0,0x1cc(sp)   ; pen
    #     0x308314  sll  a1,a2,1
    #     0x308318  addu a1,a1,a2
    #     0x30831C  sll  a1,a1,2        ; a1 = count(a2)*12
    #     0x308328  subu a0,a0,a1       ; pen = pen - count*12   <-- THE SITE (live 0x00852023)
    #     0x30832C  beq  zero,zero,0x308380
    #     0x308330  sh   a0,0x1cc(sp)   ; store pen
    #   With boxX==0 and pen = -(count*12), wide narration lines get a NEGATIVE penX
    #   and clip off the LEFT edge (leftfield's 24-char "No one was in sight. Not"),
    #   while the right side of the box goes unused.  This is centering, not left-align.
    # FIX: replace `subu a0,a0,a1` (0x00852023) with `li a0,8` (0x24040008 =
    #   addiu a0,zero,8).  This DISCARDS the count*12 centering reserve and stores a
    #   CONSTANT pen=8, so every narration line left-flushes at boxX+8 (==8px since
    #   boxX==0) with glyphs flowing rightward — true left-align using the full width.
    # SCOPING (live-confirmed disjoint — no blast radius):
    #   0x308328 stores pen sp+0x1cc and is reached ONLY by the align!=1 branch.
    #   * Live narration (align==0) HITS it -> desired left-flush.
    #   * Request body (mostbroken: 0x565150[0]==0, empty narration array) uses the
    #     mode-2 pen sp+0x1ce path (Patch 22) -> DOES NOT hit 0x308328.
    #   * Boxed dialogue (func 0x307510) and chargen (Block-A advance 0x308040,
    #     gated mode==5) DO NOT use this dispatcher's centering.
    #   Caveat (de-risked per brief): any incidental other align==0 town text on this
    #   path also becomes left-flush — a net improvement matching the left-align intent.
    # VERIFY: after build, word@0x308328 (file 0x2083A8) == 0x24040008.
    print("\n--- Patch 23: NARRATION true LEFT-FLUSH (X-dispatcher count*12 reserve @0x308328 -> li a0,8) ---")
    P23_OFF = 0x2083A8        # VA 0x308328
    P23_ORIG = 0x00852023     # subu $a0,$a0,$a1  (count*12 centering reserve)
    P23_NEW = 0x24040008      # li $a0,8          (constant left inset; on-disk LE 08 00 04 24)
    p23 = struct.unpack_from("<I", data, P23_OFF)[0]
    if p23 == P23_NEW:
        print(f"  SKIP 0x{P23_OFF:06X}: narration already left-flush (li a0,8)")
    elif p23 == P23_ORIG:
        struct.pack_into("<I", data, P23_OFF, P23_NEW)
        print(f"  OK   0x{P23_OFF:06X}: subu a0,a0,a1 -> li a0,8 (narration left-flush at boxX+8)")
        patched_count += 1
    else:
        print(f"  WARN 0x{P23_OFF:06X}: expected 0x{P23_ORIG:08X}, got 0x{p23:08X} -- Patch 23 SKIPPED")

    # ─── PATCH 24: NARRATION boxX=+96 via the draw-X load (narration-only) ──
    # Narration (the fog/intro CENTER-anchored text drawn by fn 0x3060b0) is left-
    # aligned BUILD-side by padding every line to equal glyph count (build_v9.
    # pad_narration_left_align), but the aligned block then sits off the LEFT edge
    # because the narration descriptor's boxX (desc+0x3c) stays 0 -- a live data-write
    # breakpoint on 0x1137AFC proved it is only ever memset-zeroed, never set, so
    # there is no descriptor-setup store to retarget (the earlier cave attempt missed).
    # The user dialled boxX=+0x60 (96) live and it positions the aligned block cleanly.
    # The narration draw reads boxX per glyph at VA 0x30973c (lh t2,0x3c(s0)) and that
    # load lives in the NARRATION-ONLY branch (the jal 0x3060b0 draw, distinct from
    # dialogue's 0x307510); t2 then flows into the glyph X (addu t2,t2,t0 -> addu
    # t4,t4,t2).  Replace the load with `li t2,96` so every narration glyph uses
    # boxX=+96, WITHOUT touching the shared descriptor setup or any other render path.
    # NOTE: the 0x3060b0 draw path (and this 0x30973c boxX load) is SHARED by
    # narration AND boxed dialogue (e.g. R1196 g577 "Shady Man") -- an unconditional
    # `li t2,96` shoved dialogue +324px off the RIGHT (oops.p2s).  So GATE on
    # boxX==0: only narration has boxX 0 (memset default, never set); dialogue uses
    # -228, request uses count*12-184.  Cave: reload boxX, and only if it is 0
    # override t2 with 96; otherwise leave the real boxX so dialogue/request are
    # byte-identical.  Hook's delay slot (0x309740 lh v1,0x3e(s0)) still runs; the
    # cave rejoins at 0x309744.
    print("\n--- Patch 24: NARRATION boxX=+96 via draw-X load @0x30973c (gated boxX==0) ---")
    P24_OFF = 0x2097BC          # VA 0x30973c (lh t2,0x3c(s0) = read boxX)
    P24_ORIG = 0x860A003C       # lh   t2,0x3c(s0)
    P24_HOOK = 0x08132A8C       # j 0x4CAA30  (cave; Patch-16 freed pad)
    P24_CAVE_OFF = 0x3CAAB0     # VA 0x4CAA30
    P24_CAVE = [
        0x860A003C,  # lh    t2,0x3c(s0)        ; reload boxX
        0x15400002,  # bne   t2,zero,0x4CAA40   ; boxX!=0 (dialogue/request) -> keep
        0x00000000,  # nop                       ; (delay slot)
        0x240A0060,  # addiu t2,zero,96          ; boxX==0 (narration) -> t2=96
        0x080C25D1,  # j     0x309744            ; rejoin (after the delay-slot insn)
        0x00000000,  # nop                       ; (delay slot)
    ]
    p24 = struct.unpack_from("<I", data, P24_OFF)[0]
    if p24 == P24_HOOK:
        print(f"  SKIP 0x{P24_OFF:06X}: narration boxX gate already installed")
    elif p24 == P24_ORIG:
        if any(struct.unpack_from("<I", data, P24_CAVE_OFF + i * 4)[0] for i in range(len(P24_CAVE))):
            print(f"  WARN cave 0x4CAA30 not free -- Patch 24 SKIPPED")
        else:
            struct.pack_into("<I", data, P24_OFF, P24_HOOK)
            for i, w in enumerate(P24_CAVE):
                struct.pack_into("<I", data, P24_CAVE_OFF + i * 4, w)
            print(f"  OK   0x{P24_OFF:06X}: lh t2,0x3c(s0) -> j cave; cave sets boxX=96 only if boxX==0")
            patched_count += 1
    else:
        print(f"  WARN 0x{P24_OFF:06X}: expected 0x{P24_ORIG:08X}, got 0x{p24:08X} -- Patch 24 SKIPPED")

    # ─── PATCH 15: REVERTED (was the inert modal-latch gate, v102) ────────
    # v102 trampolined the modal's else-branch (VA 0x3A0890) to skip 3 latch
    # stores (gp-0x66F0/-0x66F4/-0x66F8 = RAM 0x4FE900/0x4FE8FC/0x4FE8F8) while
    # a request chooser is live.  RAM-proven WRONG (ramdumps/wearestillfucked.p2s):
    # the chooser's cancel/confirm input does NOT come from those latches — it reads
    # the per-pad EDGE struct at [gp-0x6438]->0x56D520+0x1C (a different address;
    # 0x4FE904=2 even when the latches are 0).  The latch-skip changed nothing and
    # the game still softlocked.  We therefore LEAVE the modal's 3 stores intact
    # (stock behaviour — modal ctx+0x22 bit0 is 0 in ALL saves incl. working ones).
    # If a prior build installed the v102 hook, restore the original stores so the
    # modal ships pristine.  The real fix is PATCH 16 below.
    print("\n--- Patch 15: REVERTED (inert modal-latch gate; restore modal pristine) ---")
    SL_HOOK = 0x2A0910     # VA 0x3A0890  sh zero,-0x66F0(gp)
    SL_DELAY = 0x2A0914    # VA 0x3A0894  sh zero,-0x66F4(gp)
    SL_CAVE = 0x3D6650     # VA 0x4D65D0  (the old 40-byte cave)
    SL_J_CAVE = 0x08135974  # j 0x4D65D0
    slh = struct.unpack_from("<I", data, SL_HOOK)[0]
    if slh == SL_J_CAVE:
        # undo: restore the 3 original modal stores and clear the old cave
        struct.pack_into("<I", data, SL_HOOK,  0xA7809910)  # sh zero,-0x66F0(gp)
        struct.pack_into("<I", data, SL_DELAY, 0xA780990C)  # sh zero,-0x66F4(gp)
        for i in range(10):
            struct.pack_into("<I", data, SL_CAVE + i * 4, 0x00000000)
        print(f"  OK   0x{SL_HOOK:06X}: restored modal stores; cleared old 0x4D65D0 cave")
    elif slh == 0xA7809910:
        print(f"  SKIP 0x{SL_HOOK:06X}: modal already pristine (no v102 hook present)")
    else:
        print(f"  WARN 0x{SL_HOOK:06X}: unexpected modal hook=0x{slh:08X} -- left as-is")

    # ─── PATCH 16: Tavern Request-list softlock — chooser stuck-in-state1 watchdog
    # ROOT CAUSE (disasm + RAM proven across request/requests3/4/5/requestbroken):
    #   The request chooser task (fn 0x158E00, ctx 0x011EDEC0, sub-ctx s3=ctx+0x04
    #   =0x011EDE40) gets STUCK forever in dispatch state 1 (sub-ctx+0x08 == 1).
    #   In state 1 it reads its cancel/confirm edge from the per-pad input struct
    #   [gp-0x6438]->0x56D520, then [0x56D520+0x1C] & 0x40 (cancel ->state6 teardown)
    #   / & 0x20 (confirm ->state2).  That edge never arrives, so it never reaches
    #   state6, never sets its completion bit (ctx+0x08 |= 0x40 @VA 0x1595D0), so the
    #   parent (fn 0x13CA50 @0x13CAD0..0x13CAE8: lbu 8(handle); if &0x40 -> sw zero,
    #   0x1C(parent)) never releases parent-ctx 0x01137880 +0x1C, and the chooser/
    #   modal nodes live forever -> input dead -> softlock.  (Proven across all 5
    #   saves: chooser sub-ctx+0x08==1, ctx+0x08==0, parent+0x1C==0x011EDEC0.)
    #   The v102 latch theory was wrong (see reverted PATCH 15).
    # FIX (option c — input-INDEPENDENT teardown, the only path not relying on the
    #   unknown reason the edge is starved): hook the chooser's OWN state-1 body at
    #   VA 0x158F48 (the cancel-edge read; single entry, no internal branch targets,
    #   nothing branches in — verified).  The cave:
    #     1. reads the edge word once;
    #     2. if cancel (&0x40)         -> force sub-ctx+0x08 = 6 (stock teardown);
    #     3. else if ANY edge bit set  -> reset watchdog, j 0x158F68 (stock confirm/
    #        navigation path — normal play is byte-for-byte unchanged);
    #     4. else (no input this frame)-> ++watchdog; if it reaches 300 frames (~5 s)
    #        of CONTINUOUS dead input while stuck in state1 -> force sub-ctx+0x08 = 6.
    #   Driving state 6 makes the STOCK chooser run state6 (set ctx+0x08 bit0x40,
    #   advance to state7) and state7 (scheduler unlink 0x14CEC0/0x14E470); the parent
    #   then releases its handle at 0x13CAE8 and the native exit restores fn=0x13BA00.
    #   No scheduler is poked directly.  The watchdog resets on ANY input edge, so it
    #   ONLY fires on a genuine input-dead softlock — never during active browsing.
    #   Scoped intrinsically to fn 0x158E00 / sub-ctx 0x011EDE40 (s3): ZERO blast
    #   radius on any other menu/scene.  Watchdog counter lives in a dedicated EXE
    #   pad word (0x4CAAA0) I own — no game struct touched.
    # VERIFY: frozen-state sim (request/requests3/4/5/requestbroken.p2s) collapses the
    #   task list to the working topology — chooser fn 0x158E00 GONE from the list,
    #   parent 0x01137880 +0x1C == 0 — in every linked-node save.
    # CAVE @ VA 0x4CAA30 (file 0x3CAAB0), 0x5C bytes; counter @ 0x4CAAA0 — both
    #   verified zero in the EXE and across ramdumps/*.p2s.  Off all other caves
    #   (0x4B0DD0 patch6, 0x4C7540 space, 0x4D65D0 old patch15).
    print("\n--- Patch 16: Request chooser stuck-state1 watchdog (cave @ 0x4CAA30) ---")
    RC_HOOK  = 0x058FC8    # VA 0x158F48  lw v1,-25656(gp)
    RC_ORIG  = 0x8F839BC8  # original instruction
    RC_DELAY = 0x058FCC    # VA 0x158F4C  lw v1,0x1C(v1)  (the j's delay slot)
    RC_DELAY_ORIG = 0x8C63001C
    RC_CAVE  = 0x3CAAB0    # VA 0x4CAA30
    RC_J     = 0x08132A8C  # j 0x4CAA30  (0x4CAA30>>2 = 0x132A8C)
    rc_cave_words = [
        0x8F839BC8,   # 0x4CAA30  lw   v1, -25656(gp)   ; v1 = ptr 0x56D520
        0x8C63001C,   # 0x4CAA34  lw   v1, 0x1C(v1)     ; v1 = edge word
        0x3C04004C,   # 0x4CAA38  lui  a0, 0x4C
        0x3484AAA0,   # 0x4CAA3C  ori  a0, a0, 0xAAA0   ; a0 = &watchdog (0x4CAAA0)
        0x30650040,   # 0x4CAA40  andi a1, v1, 0x40     ; cancel bit
        0x14A00009,   # 0x4CAA44  bne  a1, zero, 0x4CAA6C ; cancel -> teardown
        0x00000000,   # 0x4CAA48  nop
        0x1460000E,   # 0x4CAA4C  bne  v1, zero, 0x4CAA88 ; any input -> reset & rejoin
        0x00000000,   # 0x4CAA50  nop
        0x8C820000,   # 0x4CAA54  lw   v0, 0(a0)        ; watchdog (dead-input frame)
        0x24420001,   # 0x4CAA58  addiu v0, v0, 1
        0xAC820000,   # 0x4CAA5C  sw   v0, 0(a0)
        0x2C41012C,   # 0x4CAA60  sltiu at, v0, 300     ; <300 frames?
        0x14200006,   # 0x4CAA64  bne  at, zero, 0x4CAA80 ; under thresh -> LOOP (no reset!)
        0x00000000,   # 0x4CAA68  nop
        0x24030006,   # 0x4CAA6C  addiu v1, zero, 6     ; TEARDOWN: state6
        0xA6630008,   # 0x4CAA70  sh   v1, 8(s3)        ; sub-ctx+0x08 = 6
        0xAC800000,   # 0x4CAA74  sw   zero, 0(a0)      ; reset watchdog
        0x0805657E,   # 0x4CAA78  j    0x1595F8         ; chooser epilogue
        0x00000000,   # 0x4CAA7C  nop
        0x080563DA,   # 0x4CAA80  LOOP: j 0x158F68      ; stay in state1 (counter intact)
        0x00000000,   # 0x4CAA84  nop
        0xAC800000,   # 0x4CAA88  ALIVE: sw zero, 0(a0) ; input present -> reset watchdog
        0x080563DA,   # 0x4CAA8C  j    0x158F68         ; stock confirm/navigation path
        0x00000000,   # 0x4CAA90  nop
    ]
    rch = struct.unpack_from("<I", data, RC_HOOK)[0]
    rc_cave_now = data[RC_CAVE:RC_CAVE + len(rc_cave_words) * 4]
    rc_free = all(b == 0 for b in rc_cave_now)
    rc_done = struct.unpack_from("<I", data, RC_CAVE)[0] == rc_cave_words[0] and \
              struct.unpack_from("<I", data, RC_CAVE + 4)[0] == rc_cave_words[1]
    # OBSOLETE — permanently disabled. The request-list "softlock" was a SYMPTOM of our own
    # R39 corruption (the quest section-table at bytes 0..240 was not remapped when the
    # resource grew), now fixed at the data level in build/inject_r39_quest.py (block 10b).
    # The watchdog is no longer needed AND it force-closed the menu after ~300 idle frames,
    # so it is never installed. Cave words / hook constants kept above for reference only.
    if True:
        print("  Patch 16: OBSOLETE (request freeze root-fixed in R39) -> NOT installed")
    elif rch == RC_J and rc_done:
        print(f"  SKIP 0x{RC_HOOK:06X}: chooser watchdog already installed")
    elif rch == RC_ORIG and (rc_free or rc_done):
        for i, w in enumerate(rc_cave_words):
            struct.pack_into("<I", data, RC_CAVE + i * 4, w)
        # NOP the j's delay slot (VA 0x158F4C `lw r3,28(r3)`): r3 is GARBAGE here
        # (clobbered by jal 0x1589D0 at 0x158F40), so the leftover load would fault.
        # The cave re-does both loads (ptr + edge) correctly.
        struct.pack_into("<I", data, RC_DELAY, 0x00000000)
        struct.pack_into("<I", data, RC_HOOK, RC_J)   # hook -> j 0x4CAA30 (last)
        print(f"  OK   0x{RC_CAVE:06X}: {len(rc_cave_words)*4}-byte chooser stuck-state1 watchdog")
        print(f"  OK   0x{RC_HOOK:06X}: lw v1,-25656(gp) -> j 0x4CAA30 ; delay slot -> nop")
        patched_count += 1
    else:
        print(f"  WARN 0x{RC_HOOK:06X}: hook=0x{rch:08X} free={rc_free} -- Patch 16 SKIPPED")

    # ─── Patch 18: ONE-SHOT hub-pane rebuild on request->hub return (cave @ 0x4C7860) ─
    # ROOT (workflow wnbqrvw5c, disasm + 146-save verified): after the Requests chooser
    #   tears down, the parent submenu-host fn 0x13CA50 releases its child handle but the
    #   hub script is never re-pumped, so the hub pane stays un-rebuilt (ctx render fields
    #   +0xA0/+0xAC handles stale, +0xB0=3, +0x290 bit2=0).  A NORMAL submenu (message
    #   board) exit rebuilds via opcode 0x1A -> {jal 0x2F1B10 rewind; jal 0x2F3330 pump},
    #   which the request exit skips.
    # WHY THIS SUCCEEDS where Patch 17/18-prior FAILED: those hooked the PER-FRAME shared
    #   handler 0x2F2490 and polled ctx state -> fired mid-construction (black screen, then
    #   tavern-entry softlock).  THIS hooks the parent-release store at 0x13CAE8 INSIDE fn
    #   0x13CA50, which has ZERO jal/j callers (runs only as a scheduler node) and is
    #   ABSENT from the scheduler during construction (firsttavern/narration/chargen run
    #   under 0x13BA00/0x2F2490, NOT 0x13CA50 — verified).  The store is reached one-shot
    #   (child+0x1c!=0 @0x13CAB4 AND child+0x8&0x40 @0x13CAD8) and clears the handle, so it
    #   cannot re-fire.  EVENT-DRIVEN, not a per-frame poll.
    # GUARDS (146-save verified to fire on EXACTLY the 7 broken/request saves, skip all
    #   else): hub-ctx from global [0x4FEDBC] (gp-0x6234); A: ctx+0x00==0x011C3D20 (hub
    #   script base); B: ctx+0x290 & 4 == 0 (pane NOT shown).  0x13CA50 is a GENERIC submenu
    #   host so it also runs on message-board exit — GUARD B is MANDATORY: it skips a healthy
    #   hub (+0x290=4) so we never re-pump and leak GS handles (leftmessageboard/tavern104
    #   skip cleanly).  Then run ONLY the existing-node build body {0x2F1B10; 0x2F3330} (NOT
    #   0x2F2AE0/0x496310 -> would dup the node; NOT 0x2F2880 -> GOLD never runs it).
    # CAVE @ VA 0x4C7860 (file 0x3C78E0), 27 words (0x6C B), ends 0x4C78CC — zero in pristine
    #   EXE; firsttavern.p2s (pre-patch) shows it zero in RAM too (NOT runtime-written); off
    #   Patch14(0x4C7540-0x4C7790)/Patch16(0x4CAA30).  Live {flag,ptr} data sits at
    #   0x4C7828-0x4C785C (before the cave) — do NOT extend backward.
    print("\n--- Patch 18: ONE-SHOT hub-pane rebuild on request->hub return (cave @ 0x4C7860) ---")
    ON_HOOK = 0x03CB68    # VA 0x13CAE8  sw zero,0x1c(s1)  (parent releases child handle)
    ON_ORIG = 0xAE20001C
    ON_CAVE = 0x3C78E0    # VA 0x4C7860
    ON_J    = 0x08131E18  # j 0x4C7860
    on_cave_words = [
        0xAE20001C,   # 0x4C7860  sw   zero, 0x1c(s1)    ; displaced original (release handle)
        0x8F849DCC,   # 0x4C7864  lw   a0, -0x6234(gp)   ; a0 = hub-ctx global [0x4FEDBC]
        0x10800016,   # 0x4C7868  beq  a0, zero, 0x4C78C4 ; no menu -> SKIP
        0x00000000,   # 0x4C786C  nop
        0x8C820000,   # 0x4C7870  lw   v0, 0x0(a0)       ; script cursor
        0x3C03011C,   # 0x4C7874  lui  v1, 0x011C
        0x34633D20,   # 0x4C7878  ori  v1, v1, 0x3D20    ; v1 = 0x011C3D20 (hub script base)
        0x14430011,   # 0x4C787C  bne  v0, v1, 0x4C78C4  ; GUARD A: not the hub -> SKIP
        0x00000000,   # 0x4C7880  nop
        0x8C820290,   # 0x4C7884  lw   v0, 0x290(a0)     ; pane bitfield
        0x30420004,   # 0x4C7888  andi v0, v0, 0x4
        0x1440000D,   # 0x4C788C  bne  v0, zero, 0x4C78C4 ; GUARD B: pane already shown -> SKIP
        0x00000000,   # 0x4C7890  nop
        0x27BDFFE0,   # 0x4C7894  addiu sp, sp, -0x20
        0xAFBF0010,   # 0x4C7898  sw   ra, 0x10(sp)
        0xAFA40014,   # 0x4C789C  sw   a0, 0x14(sp)      ; preserve hub ctx across jal
        0x0C0BC6C4,   # 0x4C78A0  jal  0x2F1B10          ; rewind cursor to base
        0x00000000,   # 0x4C78A4  nop
        0x8FA40014,   # 0x4C78A8  lw   a0, 0x14(sp)      ; a0 = hub ctx
        0x0C0BCCCC,   # 0x4C78AC  jal  0x2F3330          ; pump -> realloc +A0/+AC, +B0=4, +290|=4
        0x00000000,   # 0x4C78B0  nop
        0x8FBF0010,   # 0x4C78B4  lw   ra, 0x10(sp)
        0x27BD0020,   # 0x4C78B8  addiu sp, sp, 0x20
        0x0804F2BC,   # 0x4C78BC  j    0x13CAF0          ; return (rebuilt path)
        0x00000000,   # 0x4C78C0  nop
        0x0804F2BC,   # 0x4C78C4  SKIP: j 0x13CAF0       ; return (guard-skip path)
        0x00000000,   # 0x4C78C8  nop
    ]
    onh = struct.unpack_from("<I", data, ON_HOOK)[0]
    on_cave_now = data[ON_CAVE:ON_CAVE + len(on_cave_words) * 4]
    on_free = all(b == 0 for b in on_cave_now)
    on_done = struct.unpack_from("<I", data, ON_CAVE)[0] == on_cave_words[0] and \
              struct.unpack_from("<I", data, ON_CAVE + 4)[0] == on_cave_words[1]
    # OBSOLETE — permanently disabled. Patch 18 tried to rebuild the hub menu after the
    # request exit, but the menu-gone was itself a downstream symptom of the R39 freeze (now
    # root-fixed in inject_r39_quest.py). The hook at 0x13CAE8 also never actually fires
    # (the parent bit-0x40 handshake is never set on the request path), so it was inert.
    # Never installed; cave words kept above for reference only.
    if True:
        print("  Patch 18: OBSOLETE (request freeze root-fixed in R39; hook was inert) -> NOT installed")
    elif onh == ON_J and on_done:
        print(f"  SKIP 0x{ON_HOOK:06X}: one-shot hub rebuild already installed")
    elif onh == ON_ORIG and (on_free or on_done):
        for i, w in enumerate(on_cave_words):
            struct.pack_into("<I", data, ON_CAVE + i * 4, w)
        for k in range(len(on_cave_words), 24):
            struct.pack_into("<I", data, ON_CAVE + k * 4, 0)
        struct.pack_into("<I", data, ON_HOOK, ON_J)
        print(f"  OK   0x{ON_CAVE:06X}: one-shot rebuild cave")
        patched_count += 1
    else:
        print(f"  WARN 0x{ON_HOOK:06X}: hook=0x{onh:08X} free={on_free} -- Patch 18 SKIPPED")

    # ─── Write output ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    print(f"\n=== Summary: {patched_count} patches applied ===")
    print(f"Written to {dst} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
