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
