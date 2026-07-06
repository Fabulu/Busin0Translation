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

# v147 BATTLE-FIX: single source for the RELOCATED battle-traversed caves+tables.
# The original Patch-27 / Patch-14 caves and their ADV/LEFTSHIFT tables sat in the
# EE battle-heap arena (0x4B0E00..0x4FDE30); during battle the heap stomped that RAM
# and the box renderer's `j 0x4C7xxx` hook jumped into garbage -> no monsters / abort.
# _reloc_v147_design.py moves ONLY those battle-traversed pieces to verified-safe
# code-segment padding (below 0x4B0DCF), keeping the proportional-text LOGIC
# byte-faithful.  The inert/non-battle readers (P19/P25) KEEP the canonical
# tables at 0x4C7564/0x4C7690 (still written by Patch 14), which are intact in
# chargen/request mode (never battle).  v173 FINAL BATTLE-FIX: the v158 R2100
# tables (ADV2/LSH2) are DROPPED -- they softlocked battle at every arena
# placement -- so P26/P27/P29/P31 now read the GAME'S OWN canonical R1188 tables
# (ADV @0x4C7564 / LSH @0x4C7690, Patch 14) and NOTHING is written to
# 0x4B1000/0x4B1100 (arena stays pristine == the battle fix).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _reloc_v147_design as RELOC

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = os.path.join(os.path.dirname(__file__), "..", "extracted", "SLPM_653.78")
DST = os.path.join(os.path.dirname(__file__), "SLPM_653.78_patched")
EXPECTED_SIZE = 4_185_776

# ─── CHARGEN_DIAG (default OFF) ────────────────────────────────────────────
# When True, build/patch_exe.py installs ONLY a pure read+store DIAGNOSTIC cave
# at the chargen Block-1 draw site (VA 0x308040) instead of the production
# Patch-19 proportional caves, and writes the disambiguating register values to
# a fixed scratch RAM word (RAM 0x4CAAA0) that the user reads from a save's
# eeMemory.bin.  Production builds (CHARGEN_DIAG False) are BYTE-IDENTICAL to the
# current chargen region — the Patch-19 production caves install exactly as before.
# Toggle via the env var CHARGEN_DIAG=1 (no source edit needed for a debug build),
# or flip the default below.  See the W1-CHAR CHANGELOG + diag README for the
# decision table (scratch layout: gp, gate(gp), s5, penX, s3, s1, s3+0x290,
# s3+0x2a8, s1+0x290, s1+0x2a8, fire-counter, mode(absolute)).
CHARGEN_DIAG = (os.environ.get("CHARGEN_DIAG", "0") == "1")

# FIRE_DIAG (default OFF): box-renderer fire-counter diagnostic.  Hooks the ENTRY
# of every candidate box-text renderer + emitter (draw_clamp12 0x3A3300, blit
# 0x3A2E10, gsemit 0x483E10, 0x307510, caller family 0x15CBC0/0x1552B0/0x165C60,
# GIF builder 0x3B8820, narration 0x307DA0, old chargen 0x305E30) with a pure
# read+store trampoline that bumps a counter in scratch RAM 0x4DE060, then re-execs
# the displaced 2-word prologue and rejoins entry+8 -> ZERO behaviour change.  A
# fresh chargen-Status capture + request-list capture, read back at eeMemory 0x4DE060,
# names which renderer draws each box surface (r6-09 design; bug-fixed: 2-word
# displaced + nop delay slot like CHARGEN_DIAG, and k0/k1 scratch regs so $t9/$gp are
# never disturbed).  Toggle: FIRE_DIAG=1.  OFF => byte-identical production build.
FIRE_DIAG = (os.environ.get("FIRE_DIAG", "0") == "1")

# ─── DISABLE_P27_P14 (default OFF) ─────────────────────────────────────────
# BATTLE-ROOT-CAUSE CONFIRM build only.  When DISABLE_P27_P14=1, the Patch 27
# hook (VA 0x3A31A0 -> j 0x4C7410) and the Patch 14 hooks (VA 0x3097A0 ->
# j 0x4C7540 / VA 0x309750 -> j 0x4C7670) are NOT written -- those sites stay
# PRISTINE -- so NOTHING in the EXE jumps into the runtime game-managed heap band
# at 0x4C7370-0x4C7700.  Because Patch 19/24/25/26 all gate on the Patch-14 marker
# (file 0x209820 == 0x08131D50), disabling Patch 14 also auto-skips those (no extra
# jumps into 0x4C7xxx).  This reverts box/narration/chargen text to STOCK monospace
# but lets the battle arena bind run uncorrupted -- the CONFIRM test for the cave
# placement hypothesis.  Default (env unset) => Patch 27 + 14 applied as normal;
# the production build is BYTE-IDENTICAL to before this gate existed.
DISABLE_P27_P14 = (os.environ.get("DISABLE_P27_P14", "0") == "1")

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
    print("\n--- Patch 6: Mode-gated RenderAllTiles trampoline (portraits + clean chargen) [v148 RELOCATED] ---")
    SITE = 0x1F25E8                       # JAL 0x30B840 (VA 0x2F2568)
    # v148 BATTLE-ARENA EVACUATION: the old trampoline @VA 0x4B0DD0 sat in the run that
    # ends exactly at the arena (0x4B0E00) -- a false-safe placement.  It is RELOCATED to
    # verified-zero .text padding @VA RELOC.P6_VA (0x4B0D4C).  The trampoline's internal
    # `beq` is PC-relative (invariant under relocation) and `j 0x30B840` is absolute
    # (unchanged), so the 8 words ship BYTE-IDENTICAL; only the cave base + the JAL hook's
    # target change.  This ALSO restores Patch 6 to live: the old JAL-cave guard checked the
    # stale 0x0C12C374 (the previous base) while the build had already moved on, leaving the
    # gate effectively inert; the correct relocated JAL re-arms the mode==5 chargen-kanji-skip
    # + portrait gating.
    CAVE = RELOC.fo(RELOC.P6_VA)          # code cave (VA RELOC.P6_VA = 0x4B0D4C)
    JAL_RAT = struct.pack("<I", 0x0C0C2E10)   # original JAL 0x30B840
    JAL_OLD_CAVE = 0x0C12C374                 # legacy JAL 0x4B0DD0 (stale base -> migrate)
    JAL_CAVE = 0x0C000000 | (RELOC.P6_VA >> 2)  # JAL RELOC.P6_VA (relocated trampoline)
    NOP4 = b"\x00\x00\x00\x00"
    TRAMP = bytes.fromhex(
        "289d8293" "05000124" "03004110" "00000000"
        "102e0c08" "00000000" "0800e003" "00000000")
    site = bytes(data[SITE:SITE + 4])
    cave = bytes(data[CAVE:CAVE + len(TRAMP)])
    if os.environ.get("DISABLE_PATCH6") == "1":
        # Battle-isolation test build only: leave the JAL site STOCK
        # (0x0C0C2E10) and the cave unwritten so Patch 6 can be isolated.
        # Default behavior (env var unset) is UNCHANGED — Patch 6 applies.
        print("  SKIP Patch 6 DISABLED via DISABLE_PATCH6=1 (battle-isolation test)")
    elif site not in (JAL_RAT, NOP4,
                      struct.pack("<I", JAL_CAVE), struct.pack("<I", JAL_OLD_CAVE)):
        print(f"  WARN 0x{SITE:06X}: expected JAL 0x30B840 / NOP / JAL-cave, got {site.hex()}")
    elif cave != b"\x00" * len(TRAMP) and cave != TRAMP:
        print(f"  WARN 0x{CAVE:06X}: code cave not zero/trampoline ({cave[:8].hex()}...) — Patch 6 SKIPPED")
    else:
        RELOC.assert_install_safe(RELOC.P6_VA, len(TRAMP), "Patch 6 trampoline")
        data[CAVE:CAVE + len(TRAMP)] = TRAMP
        struct.pack_into("<I", data, SITE, JAL_CAVE)
        print(f"  OK   0x{CAVE:06X}: 32-byte mode-gate trampoline @VA 0x{RELOC.P6_VA:06X} "
              f"(skip RenderAllTiles iff mode==5)")
        print(f"  OK   0x{SITE:06X}: JAL 0x30B840 -> JAL 0x{RELOC.P6_VA:06X} (relocated trampoline)")
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

    # ─── PATCH: Item-name PILL width (treasure/alchemy capsule) ─────────
    # The rounded item-name capsule is engine-drawn at a fixed ~185px width; long
    # English item names ("Town Return Potion", "Zateal Spell Book") spill past its
    # rounded caps.  Width is a box-draw immediate at VA 0x13F688 (addiu a1,zero,185;
    # a2=8 = corner radius -> a rounded pill).  Of only 5 sites project-wide that set
    # exactly 185, this is the strongest 2D-UI match.  In-place .text immediate, VA far
    # below the battle arena (0x13F688 << 0x4B0DCF) -- SAFE class, NOT a cave.  BLIND
    # candidate, VERIFY-BY-EYE: tune PILL_W (too wide / too narrow); if the pill does
    # NOT change on-screen, swap PILL_VA to the next candidate (0x170EC4).
    PILL_VA, PILL_W = 0x13F688, 440   # candidate site; target px (orig 185; #1@260 grew -> more headroom)
    print("\n--- Patch: item-name pill width 185 -> %d @VA 0x%06X ---" % (PILL_W, PILL_VA))
    pill_off = PILL_VA - 0x100000 + 0x80
    pill_word = struct.unpack_from("<I", data, pill_off)[0]
    _rt = (pill_word >> 16) & 31
    if (pill_word >> 26) == 0x09 and ((pill_word >> 21) & 31) == 0 and (pill_word & 0xFFFF) == 0xB9:
        struct.pack_into("<I", data, pill_off, (0x24000000 | (_rt << 16)) | (PILL_W & 0xFFFF))
        print(f"  OK   0x{pill_off:06X}: pill width 185 -> {PILL_W} (addiu ${_rt})")
        patched_count += 1
    else:
        print(f"  WARN 0x{pill_off:06X}: expected addiu rt,zero,185, got 0x{pill_word:08X}")

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
    print("\n--- Patch 14: PROPORTIONAL narration spacing (advance LUT + draw-shift) [v148 RELOCATED below arena] ---")
    # v148 BATTLE-ARENA EVACUATION: although Patch-14's caves were proven never-stomped
    # in-arena, the audit relocates them out anyway so NOTHING ships in the arena and the
    # guardrail can forbid the arena outright.  cave1 0x4C7540 -> RELOC.P14C1_VA (0x4B049C),
    # cave2 0x4C7670 -> RELOC.P14C2_VA (0x4B047C), both verified-zero .text padding.  The
    # caves' words are BYTE-IDENTICAL (absolute `j` rejoins + table reads are unchanged); only
    # the cave base + the two hook j-targets (= the gate marker @0x209820) change.  The
    # canonical 256-byte ADV/LSH tables STAY at 0x4C7564 / 0x4C7690 (whitelisted resident
    # rodata, read by the caves AND the chargen/request readers P19/25/26).  NOTHING is
    # written into the PsII libgraph SDK data block at 0x4AF2E0..0x4AF400.
    P14_HOOK1 = 0x209820   # VA 0x3097A0  (advance hook; the gate marker word)
    P14_HOOK2 = 0x2097D0   # VA 0x309750  (draw-shift hook)
    P14_TBL1  = 0x3C75E4   # file off VA 0x4C7564 (canonical 256B ADV)
    P14_TBL2  = 0x3C7710   # file off VA 0x4C7690 (canonical 256B LEFTSHIFT)
    NEW_H1 = RELOC.P14_HOOK1_JWORD   # j RELOC.P14C1_VA (0x4B049C) -- gate marker
    NEW_H2 = RELOC.P14_HOOK2_JWORD   # j RELOC.P14C2_VA (0x4B047C)
    p14c1 = RELOC.P14C1_WORDS        # relocated cave1 words (byte-identical)
    p14c2 = RELOC.P14C2_WORDS        # relocated cave2 words (byte-identical)
    f_c1  = RELOC.fo(RELOC.P14C1_VA) # file off VA RELOC.P14C1_VA
    f_c2  = RELOC.fo(RELOC.P14C2_VA) # file off VA RELOC.P14C2_VA
    h1 = struct.unpack_from("<I", data, P14_HOOK1)[0]
    h2 = struct.unpack_from("<I", data, P14_HOOK2)[0]
    if DISABLE_P27_P14:
        # CONFIRM build: leave 0x3097A0 / 0x309750 PRISTINE (no j into a cave).
        # Patch 19/24/25/26 auto-skip (their gate marker @0x209820 stays 0x87A201CE).
        print("  SKIP Patch 14 DISABLED via DISABLE_P27_P14=1 (battle-root-cause CONFIRM build)")
    elif h1 == NEW_H1 and struct.unpack_from("<I", data, f_c1)[0] == p14c1[0]:
        print("  SKIP: in-arena proportional caves already installed")
    elif h1 == 0x87A201CE and h2 == 0x00EC6021:
        RELOC.assert_install_safe(RELOC.P14C1_VA, len(p14c1) * 4, "Patch 14 cave1")
        RELOC.assert_install_safe(RELOC.P14C2_VA, len(p14c2) * 4, "Patch 14 cave2")
        # ---- canonical 256B tables (whitelisted resident rodata; caves + P19/25/26 read) ----
        RELOC.assert_install_safe(0x4C7564, 256, "Patch 14 ADV table", allow_canonical_table=True)
        RELOC.assert_install_safe(0x4C7690, 256, "Patch 14 LSH table", allow_canonical_table=True)
        data[P14_TBL1:P14_TBL1 + 256] = glyph_metrics.adv_table_256()
        data[P14_TBL2:P14_TBL2 + 256] = glyph_metrics.leftshift_table_256()
        # ---- Stage-1 advance cave (relocated @RELOC.P14C1_VA) ----
        for i, w in enumerate(p14c1):
            struct.pack_into("<I", data, f_c1 + i * 4, w)
        struct.pack_into("<I", data, P14_HOOK1, NEW_H1)          # j P14C1_VA (gate marker)
        struct.pack_into("<I", data, P14_HOOK1 + 4, 0x00000000)  # nop (delay slot)
        # ---- Stage-2 draw-shift cave (relocated @RELOC.P14C2_VA) ----
        for i, w in enumerate(p14c2):
            struct.pack_into("<I", data, f_c2 + i * 4, w)
        struct.pack_into("<I", data, P14_HOOK2, NEW_H2)          # j 0x4C7670 (delay slot 0x309754 runs once)
        # 3B — per-line re-center x24 -> x18 (the site Patch 13 missed)
        for off, exp, new in [(0x2083E4, 0x00062040, 0x000620C0), (0x2083EC, 0x000420C0, 0x00042040)]:
            if struct.unpack_from("<I", data, off)[0] == exp:
                struct.pack_into("<I", data, off, new)
        print(f"  OK   advance LUT @0x{RELOC.P14C1_VA:06X} + draw-shift @0x{RELOC.P14C2_VA:06X} "
              f"(RELOCATED below arena; avg {sum(glyph_metrics.ADV)/95:.1f}px); "
              f"canonical 256B tables @0x4C7564/0x4C7690; gate marker @0x209820=0x{NEW_H1:08X}")
        patched_count += 1
    else:
        print(f"  WARN proportional caves not applied: hook1=0x{h1:08X} hook2=0x{h2:08X}")

    # ─── R2100 METRIC TABLES (v158) — DROPPED in v173 (FINAL battle-softlock fix) ──────
    # The v158 R2100 tables (ADV2/LSH2) were PROVEN to cause the intermittent empty-monster
    # battle softlock at BOTH placements they were ever installed at: the arena-start hole
    # 0x4B1000/0x4B1100 (dump "Emptyfuckyou") AND the deep RANK-2 0x4C785F/0x4C7790 (dump
    # "mfs").  ANY of our resident data inside the battle arena is DMA-swept into camera/
    # monster setup.  The user's pristine-EXE test (no R2100 tables) works.  FINAL FIX: DO
    # NOT install these tables anywhere.  The chargen/request caves (Patches 26/27/29/31)
    # now read the GAME'S OWN canonical R1188 tables (ADV @0x4C7564 / LSH @0x4C7690, written
    # by Patch 14 and intact in every battle dump), so 0x4B1000/0x4B1100 stay PRISTINE-ZERO
    # and the arena == pristine.  Chargen reverts to the mild pre-v158 "Ge nde r" spacing
    # (acceptable: softlock >> spacing).  The install block below is intentionally a NO-OP;
    # it only ASSERTS the arena regions ship zero (the battle fix).
    print("\n--- R2100 metric tables: DROPPED (v173 battle-softlock fix); arena stays pristine ---")
    T2_ADV_FO = RELOC.fo(0x4B1000)   # old ADV2 slot (must remain zero)
    T2_LSH_FO = RELOC.fo(0x4B1100)   # old LSH2 slot (must remain zero)
    assert all(b == 0 for b in data[T2_ADV_FO:T2_ADV_FO + 256]) and \
        all(b == 0 for b in data[T2_LSH_FO:T2_LSH_FO + 256]), (
        "arena-start hole 0x4B1000/0x4B1100 is NOT zero -- v173 requires it PRISTINE "
        "(no R2100 table); another patch claimed the slot. Battle fix broken."
    )
    print("  OK   0x4B1000/0x4B1100 pristine-zero (no in-arena table); caves read canonical "
          "ADV @0x4C7564 / LSH @0x4C7690")
    # NOTE (v173): the legacy v158 install (bake glyph_metrics.ADV2/LEFTSHIFT2 into the
    # arena-start hole and point the caves there) is DELETED.  Its root-cause context lives
    # in the header comment above; glyph_metrics still carries ADV2/LEFTSHIFT2 for reference
    # + the metrics gates, but NOTHING consumes them in the EXE now.

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
    # ─── CHARGEN_DIAG: pure read+store instrumentation (replaces Patch 19 when ON) ──
    # The chargen Block-1 draw site (jal 0x305E30 @VA 0x308030; per-glyph advance
    # store @VA 0x308040 `addiu v0,v0,0x18` then `sh v0,0x1cc(sp)` @0x308044) is
    # CHARGEN-EXCLUSIVE — jal 0x305E30 appears EXACTLY ONCE EXE-wide (recon-proven),
    # so a hook here NEVER fires on narration/request/dialogue/town surfaces.  No
    # mode gate is needed for surface isolation; surface isolation is structural.
    #
    # The cave is a PURE read+store: it clobbers ONLY $at/$t8/$t9 (verified DEAD at
    # this site — the chargen loop 0x307F30..0x308058 and its tail use only
    # v0/v1/t0/a0/a1/a2/a3/s0/s1/s2/s3/s5/sp; no $at/$t8/$t9 read across the hook),
    # re-does the stock 24px advance+store byte-identically, then j 0x308048 (past
    # the displaced store).  So the shared renderer 0x307DA0 / blitter 0x305E30
    # behave EXACTLY as in the current monospace build — narration (Patch 14/24) and
    # request (Patch 22) take their normal paths untouched (this hook is the only
    # change, and it is on a chargen-only instruction).
    #
    # SCRATCH @ RAM 0x4CAAA0 (file 0x3CAB20; 74 verified-zero bytes; off all caves).
    #   The user reads these dwords from the save's eeMemory.bin (RAM addr == file
    #   offset for the EXE image; the scratch IS EXE-resident data so eeMemory[
    #   0x4CAAA0 ..] holds the last-drawn-glyph capture):
    #     +0x00 gp        : the renderer's LIVE $gp at draw time          (W2 test)
    #     +0x04 gate(gp)  : mem[$gp-0x62d8] as the renderer's $gp resolves (W2 test)
    #     +0x08 s5        : live draw-X candidate (return of 0x305E30)     (W4 test)
    #     +0x0C penX      : sp+0x1cc (the pen Patch 19 wrote)              (W4 test)
    #     +0x10 s3        : descriptor candidate (box_origin lh 0x3e(s3))
    #     +0x14 s1        : current glyph-cell pointer
    #     +0x18 s3+0x290  : Block-1 enable bitfield (bit 0x100)            (R1 test)
    #     +0x1C s3+0x2a8  : count-reserve gate (==1?)                      (R1 test)
    #     +0x20 s1+0x290  : per-task-literal field via the cell-ptr base
    #     +0x24 s1+0x2a8  : per-task-literal field via the cell-ptr base
    #     +0x28 counter   : ++ each glyph draw (proves the cave FIRED at all)
    #     +0x2C mode(abs) : mem[0x4FED18] read by ABSOLUTE addr (gp-independent;
    #                       compare vs +0x04 — if +0x04 != +0x2C the renderer's $gp
    #                       does NOT resolve the mode global => W2 confirmed).
    # DECISION TABLE (planner reads scratch from a fresh chargen save):
    #   * +0x00 gp != 0x504FF0  OR  +0x04 gate != 5  (while +0x2C mode == 5)
    #         -> W2 CONFIRMED (gp-relative gate fails) -> next-round fix = replace
    #            the gp gate with a descriptor-field gate (e.g. s3+0x290 & 0x100).
    #   * +0x00/+0x04 correct (gp==0x504FF0, gate==5) but +0x08 s5 advances by a
    #     CONSTANT across glyphs while +0x0C penX varies
    #         -> W4 CONFIRMED (draw-X is s5; sp+0x1cc dead) -> fix = retarget the
    #            advance into 0x305E30's returned s5.
    #   * +0x28 counter == 0 in a chargen save -> the draw site was never reached
    #     for the captured frame (text drew via a different path; re-capture mid-draw
    #     or escalate to live debugger BP on 0x305E30).
    DIAG_HOOK   = 0x2080C0   # VA 0x308040  addiu v0,v0,0x18  (pristine stride store head)
    DIAG_HOOK_ORIG = 0x24420018
    DIAG_DELAY  = 0x2080C4   # VA 0x308044  sh v0,0x1cc(sp)   -> nop
    DIAG_DELAY_ORIG = 0xA7A201CC
    DIAG_CAVE   = 0x3C7810   # VA 0x4C7790 (file 0x3C7810; after Patch-14 LEFTSHIFT tbl)
    DIAG_J_TO_CAVE = 0x08000000 | (0x4C7790 >> 2)   # j 0x4C7790
    DIAG_SCRATCH = 0x4CAAA0  # RAM addr the user dumps from eeMemory.bin
    diag_cave = [
        0x3C19004C,  # 0x4C7790  lui   t9, 0x4C            ; t9 = hi(scratch)
        0x3739AAA0,  # 0x4C7794  ori   t9, t9, 0xAAA0      ; t9 = &scratch (0x4CAAA0)
        0xAF3C0000,  # 0x4C7798  sw    gp, 0(t9)           ; +0x00 = live $gp
        0x8F819D28,  # 0x4C779C  lw    at, -0x62d8(gp)     ; gate as renderer's gp resolves it
        0xAF210004,  # 0x4C77A0  sw    at, 4(t9)           ; +0x04 = mem[$gp-0x62d8]
        0xAF350008,  # 0x4C77A4  sw    s5, 8(t9)           ; +0x08 = s5 (draw-X candidate)
        0x87A101CC,  # 0x4C77A8  lh    at, 0x1cc(sp)       ; original penX (pre stock advance)
        0xAF21000C,  # 0x4C77AC  sw    at, 12(t9)          ; +0x0C = penX (sp+0x1cc)
        0xAF330010,  # 0x4C77B0  sw    s3, 16(t9)          ; +0x10 = s3 (descriptor candidate)
        0xAF310014,  # 0x4C77B4  sw    s1, 20(t9)          ; +0x14 = s1 (cell ptr)
        0x8E610290,  # 0x4C77B8  lw    at, 0x290(s3)       ; Block-1 enable bitfield (s3 base)
        0xAF210018,  # 0x4C77BC  sw    at, 24(t9)          ; +0x18 = mem[s3+0x290]
        0x926102A8,  # 0x4C77C0  lbu   at, 0x2a8(s3)       ; count-reserve gate (s3 base)
        0xAF21001C,  # 0x4C77C4  sw    at, 28(t9)          ; +0x1C = mem[s3+0x2a8]
        0x8E210290,  # 0x4C77C8  lw    at, 0x290(s1)       ; per-task-literal (s1 base)
        0xAF210020,  # 0x4C77CC  sw    at, 32(t9)          ; +0x20 = mem[s1+0x290]
        0x922102A8,  # 0x4C77D0  lbu   at, 0x2a8(s1)       ; per-task-literal (s1 base)
        0xAF210024,  # 0x4C77D4  sw    at, 36(t9)          ; +0x24 = mem[s1+0x2a8]
        0x8F210028,  # 0x4C77D8  lw    at, 40(t9)          ; fire counter
        0x24210001,  # 0x4C77DC  addiu at, at, 1
        0xAF210028,  # 0x4C77E0  sw    at, 40(t9)          ; +0x28 = ++counter
        0x3C180050,  # 0x4C77E4  lui   t8, 0x50            ; t8 = 0x500000
        0x8F01ED18,  # 0x4C77E8  lw    at, -0x12E8(t8)     ; mode @0x4FED18 (ABSOLUTE, gp-free)
        0xAF21002C,  # 0x4C77EC  sw    at, 44(t9)          ; +0x2C = mode(absolute)
        0x87A201CC,  # 0x4C77F0  lh    v0, 0x1cc(sp)       ; --- stock advance (byte-identical) ---
        0x24420018,  # 0x4C77F4  addiu v0, v0, 0x18        ; stock 24px monospace
        0xA7A201CC,  # 0x4C77F8  sh    v0, 0x1cc(sp)       ; stock store (was the nop'd delay slot)
        0x080C2012,  # 0x4C77FC  j     0x308048            ; rejoin past the original store
        0x00000000,  # 0x4C7800  nop  (delay)
    ]
    print("\n--- Patch 19: CHARGEN Path-1 proportional (advance LUT + draw-shift + summed centering) ---")
    if CHARGEN_DIAG:
        print("  ** CHARGEN_DIAG ON ** -> install ONLY the read+store diagnostic cave; "
              "Patch 19 production caves SKIPPED")
        h = struct.unpack_from("<I", data, DIAG_HOOK)[0]
        d = struct.unpack_from("<I", data, DIAG_DELAY)[0]
        cave_free = all(b == 0 for b in data[DIAG_CAVE:DIAG_CAVE + len(diag_cave) * 4])
        cave_done = struct.unpack_from("<I", data, DIAG_CAVE)[0] == diag_cave[0]
        # VERIFY hook-site instruction BEFORE patching (struct.unpack_from of the
        # known stride store head + its delay slot).
        if h == DIAG_J_TO_CAVE and cave_done:
            print(f"  SKIP 0x{DIAG_HOOK:06X}: diagnostic cave already installed")
        elif h == DIAG_HOOK_ORIG and d == DIAG_DELAY_ORIG and (cave_free or cave_done):
            for i, w in enumerate(diag_cave):
                struct.pack_into("<I", data, DIAG_CAVE + i * 4, w)
            struct.pack_into("<I", data, DIAG_HOOK, DIAG_J_TO_CAVE)   # j 0x4C7790
            struct.pack_into("<I", data, DIAG_DELAY, 0x00000000)      # delay slot -> nop
            # VERIFY cave bytes AFTER assembling (struct.unpack_from round-trip).
            for i, w in enumerate(diag_cave):
                got = struct.unpack_from("<I", data, DIAG_CAVE + i * 4)[0]
                assert got == w, f"diag cave verify FAIL @word {i}: {got:#010x} != {w:#010x}"
            assert struct.unpack_from("<I", data, DIAG_HOOK)[0] == DIAG_J_TO_CAVE
            assert struct.unpack_from("<I", data, DIAG_DELAY)[0] == 0
            print(f"  OK   0x{DIAG_HOOK:06X}: addiu v0,v0,0x18 -> j 0x4C7790 (diag cave); delay -> nop")
            print(f"  OK   0x{DIAG_CAVE:06X}: {len(diag_cave)*4}-byte read+store cave -> scratch @0x{DIAG_SCRATCH:06X}")
            print(f"  ---  scratch layout: +0 gp / +4 gate(gp) / +8 s5 / +0xC penX / +0x10 s3 / "
                  f"+0x14 s1 / +0x18 s3+290 / +0x1C s3+2a8 / +0x20 s1+290 / +0x24 s1+2a8 / "
                  f"+0x28 counter / +0x2C mode(abs)")
            patched_count += 1
        else:
            print(f"  WARN diag NOT applied: hook=0x{h:08X} delay=0x{d:08X} "
                  f"cave_free={cave_free} cave_done={cave_done} -- Patch 19 region left as-is")
        # IMPORTANT: when DIAG is ON we do NOT run the production Patch-19 install
        # below (its hooks 0x308040/0x308018 would collide with the diag hook).
        P19_GATE = None
    else:
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
    # v148 P2 CLEANUP: the Stage-3 summed-width-centering cave (formerly p19_cave3 @VA
    # 0x4D66A0) was NEVER hooked (stock count*12 reserve cancels s7 -> already left-anchored;
    # see the rationale below).  Its dead word-list + constants P19_H3/C3/J3 are DELETED in
    # v148 -- they were footguns (an in-arena placement that nothing referenced).
    # v148 BATTLE-ARENA EVACUATION: cave1 0x4D6600 -> RELOC.P19C1_VA (0x4AB5A8),
    # cave2 0x4D6660 -> RELOC.P19C2_VA (0x4AFA70), both verified-zero .text padding.
    # The cave words are BYTE-IDENTICAL (internal branches are PC-relative -> invariant;
    # `j 0x308048`/`j 0x30801C` rejoins + ADV/LSH table reads are absolute -> unchanged);
    # only the cave base + each hook's j-immediate change.  (Stage-3 cave3 @0x4D66A0 was
    # NEVER hooked -- its dead constants P19_H3/C3/J3 are removed in v148.)
    P19_H1, P19_C1, P19_J1 = 0x2080C0, RELOC.fo(RELOC.P19C1_VA), RELOC.P19C1_HOOK_JWORD  # VA 0x308040 / cave1
    P19_H2, P19_C2, P19_J2 = 0x208098, RELOC.fo(RELOC.P19C2_VA), RELOC.P19C2_HOOK_JWORD  # VA 0x308018 / cave2
    # v122: RE-ENABLED.  The v120 revert reasons are both resolved:
    #  (1) "andi 0xFF -> gid=0" -> caves now read the HIGH byte (srl 8); chargenspaces.p2s
    #      confirms cells are (char-32)<<8, so srl 8 yields the correct glyph index.
    #  (2) "no request/chargen discriminator" -> all three stages now gate on the screen-mode
    #      global lw $at,-0x62d8($gp) == 5 (chargen).  mostbroken(request)=7 -> stock fallback.
    if CHARGEN_DIAG:
        # DIAG path already installed above; production Patch-19 caves are intentionally
        # NOT installed (they would collide with the diagnostic hook at 0x308040).
        pass
    elif P19_GATE != RELOC.NEW_GATE_MARKER:
        print(f"  WARN Patch 14 not installed (hook=0x{P19_GATE:08X}) -> Patch 19 SKIPPED")
    else:
        h1 = struct.unpack_from("<I", data, P19_H1)[0]
        h2 = struct.unpack_from("<I", data, P19_H2)[0]
        c1_free = all(b == 0 for b in data[P19_C1:P19_C1 + len(p19_cave1) * 4])
        c2_free = all(b == 0 for b in data[P19_C2:P19_C2 + len(p19_cave2) * 4])
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
        #   pristine (stock count*12 reserve cancels s7); the dead Stage-3 cave was DELETED
        #   in v148 (P2 cleanup).  Stage 1 + Stage 2 are the shipped fix.
        if already:
            print("  SKIP: chargen proportional caves already installed")
        elif (h1 == 0x24420018 and h2 == 0x87A301CC
              and (c1_free or c1_done) and c2_free):
            RELOC.assert_install_safe(RELOC.P19C1_VA, len(p19_cave1) * 4, "Patch 19 cave1")
            RELOC.assert_install_safe(RELOC.P19C2_VA, len(p19_cave2) * 4, "Patch 19 cave2")
            # Stage 1 — advance LUT cave + trampoline (also nop the displaced store @0x308044)
            for i, w in enumerate(p19_cave1):
                struct.pack_into("<I", data, P19_C1 + i * 4, w)
            struct.pack_into("<I", data, P19_H1, P19_J1)          # j cave1
            struct.pack_into("<I", data, P19_H1 + 4, 0x00000000)  # delay slot (was sh) -> nop
            # Stage 2 — draw-shift cave + trampoline (delay slot 0x30801C left: idempotent move)
            for i, w in enumerate(p19_cave2):
                struct.pack_into("<I", data, P19_C2 + i * 4, w)
            struct.pack_into("<I", data, P19_H2, P19_J2)          # j cave2
            print(f"  OK   Stage 1 advance LUT  @0x{RELOC.P19C1_VA:06X} (hook 0x308040, gate mode==5, ADV 0x7564, srl-8)")
            print(f"  OK   Stage 2 draw-shift   @0x{RELOC.P19C2_VA:06X} (hook 0x308018, gate mode==5, LEFTSHIFT 0x7690)")
            print(f"  ---  Stage 3 NOT hooked: stock count*12 cancels s7 -> left-anchored proportional")
            patched_count += 1
        else:
            print(f"  WARN Patch 19 not applied: h1=0x{h1:08X} h2=0x{h2:08X} "
                  f"c1_free={c1_free} c2_free={c2_free}")

    # ─── PATCH 26: CHARGEN body text PROPORTIONAL (the REAL renderer, func 0x307510) ──
    # Patch 19 was LIVE-PROVEN INERT: it hooks the dead `jal 0x305E30` Block-1 path
    # (CHARGEN_DIAG cave recorded fire-counter==0 while mode 0x4FED18==5; see memory
    # project_chargen_drawpath_falsified).  recon3+recon4 traced the ACTUAL chargen text
    # renderer to func 0x307510 (Loop A: 0x307DA0 line-walk -> 0x307510 glyph blit ->
    # 0x3060B0 sprite emit).  Its per-glyph advance is MONOSPACE, branch-selected by the
    # caller's font SIZE arg [sp+0xE0]==[sp+0x178] at the 0x3079D0 bne (==100 integer
    # 0x3079DC / !=100 float 0x3079E8 -- BOTH constant strides, neither proportional).
    #
    # FIX = ONE hook + ONE cave that advances the cursor by the per-glyph ADV width,
    # gated to chargen (mem[0x4FED18]==5).  v158: the table is the R2100 ADV2
    # @RELOC.ADV2_VA (this renderer draws the R2100 upright 16px font, NOT R1188 —
    # see the R2100-tables block above).  The hook
    # sits at 0x3079CC, ONE instr BEFORE the size bne, so it covers BOTH branches (the
    # integer-vs-float question is MOOT).  mode!=5 falls through to a byte-identical STOCK
    # -> ZERO blast radius on the ~10 other size-100 callers (town/shop menus, name-entry,
    # status).  Loop A is a plain L->R cursor walk with NO centering reserve, so
    # proportional advance cannot mis-center.
    #
    # Two corrections vs recon4-R4's draft cave (both load-bearing):
    #  (1) v1 PRESERVED: v1 holds the literal 100 (set @0x3079BC, inside the loop) that the
    #      0x3079D0 `bne v0,v1` needs.  The draft clobbered v1 with the gate constant, which
    #      would have made the STOCK `bne v0,5` -> broke size-select for every non-chargen
    #      caller.  The gate constant lives in a0 (dead here) instead; v1 is untouched on
    #      the STOCK path (chargen path may clobber it -- re-set @0x3079BC next glyph).
    #  (2) ABSOLUTE mode read (lui 0x50 / lw -0x12E8) instead of gp-relative, removing the
    #      unconfirmed $gp-resolves-the-mode-global risk (the round-2 W2 hypothesis).
    #
    # gid recovery (no live glyph reg at the advance): re-run the loop fetch -- s7 indexes a
    # BE-u16 glyph-id table at s1 and only ++ at the tail 0x307A10 (AFTER the advance), so
    # 0(s7) still points at the CURRENT glyph.  ASCII guard sltiu<95 -> kanji over-index
    # falls to STOCK (stock mono stride for that glyph).
    #
    # CAVE VA 0x4C7790 is SHARED with the CHARGEN_DIAG cave -> Patch 26 installs only in
    # PRODUCTION (not CHARGEN_DIAG).  Gated on Patch-14 installed (0x209820==0x08131D50,
    # the resident ADV table).  Stat abbrevs Str/Int/... + Sex/Race/Align/Class/tabs/OK are
    # R2138 sub7 pre-rendered SPRITES (different compositor) -- EXPECTED to stay unchanged;
    # Patch 26 fixes the chargen BODY text only.  Request text is a SEPARATE path (Loop B /
    # Patch-25) -- NOT touched here.  (All cross-refs to other patches are hyphenated on
    # purpose: the Patch-25 scope test isolates its block with a find() on the spaced
    # banner string, so an un-hyphenated mention here would hijack that anchor.)
    # v148 BATTLE-ARENA EVACUATION: the production cave moves 0x4C7790 -> RELOC.P26_VA
    # (0x4B0414), verified-zero .text padding.  The cave's two internal branches to STOCK
    # are PC-relative (invariant) and the `j 0x307A00`/`j 0x3079D0` rejoins + the ADV table
    # read are absolute (unchanged), so the 26 words ship BYTE-IDENTICAL; only the cave base
    # + the hook's j-immediate change.  (The CHARGEN_DIAG debug cave still uses 0x4C7790 --
    # it is mutually exclusive with production Patch 26 and out of the battle-path arena.)
    print("\n--- Patch 26: CHARGEN body text PROPORTIONAL (real renderer 0x307510 Loop A) [v148 RELOCATED] ---")
    P26_HOOK = 0x207A4C            # VA 0x3079CC, pristine 0x8FA200E0 (lw v0,0xe0(sp))
    P26_CAVE = RELOC.fo(RELOC.P26_VA)   # VA RELOC.P26_VA (0x4B0414)
    P26_J_TO_CAVE = RELOC.P26_HOOK_JWORD  # j RELOC.P26_VA
    P26_CAVE_WORDS = [
        0x3C010050,  # lui   at,0x50
        0x8C21ED18,  # lw    at,-0x12E8(at)   ; at = mem[0x4FED18] (mode, abs)
        0x24040005,  # addiu a0,zero,5
        0x14240014,  # bne   at,a0,+0x14      ; mode!=5 -> STOCK (PC-rel, invariant)
        0x00000000,  # 0x4C77A0  nop
        0x96E20000,  # 0x4C77A4  lhu   v0,0(s7)         ; current glyph INDEX
        0x00021040,  # 0x4C77A8  sll   v0,v0,1
        0x02221021,  # 0x4C77AC  addu  v0,s1,v0
        0x90430000,  # 0x4C77B0  lbu   v1,0(v0)
        0x90440001,  # 0x4C77B4  lbu   a0,1(v0)
        0x00031A00,  # 0x4C77B8  sll   v1,v1,8
        0x00641025,  # 0x4C77BC  or    v0,v1,a0         ; BE-u16 glyph id
        0x3042FFFF,  # 0x4C77C0  andi  v0,v0,0xffff
        0x2C41005F,  # 0x4C77C4  sltiu at,v0,95         ; ASCII guard
        0x10200009,  # 0x4C77C8  beqz  at,0x4C77F0      ; gid>=95 -> STOCK
        0x00000000,  # 0x4C77CC  nop
        0x86430000,  # 0x4C77D0  lh    v1,0(s2)         ; cursor X
        0x3C01004C,  # 0x4C77D4  lui   at,0x4C          ; v173: canonical ADV table base 0x4C0000
        0x00220821,  # 0x4C77D8  addu  at,at,v0
        0x90217564,  # 0x4C77DC  lbu   at,0x7564(at)    ; ADV[gid] @0x4C7564 (canonical R1188)
        0x00611821,  # 0x4C77E0  addu  v1,v1,at         ; cursor += ADV
        0xA6430000,  # 0x4C77E4  sh    v1,0(s2)
        0x080C1E80,  # 0x4C77E8  j     0x307A00         ; loop tail (proportional done)
        0x00000000,  # 0x4C77EC  nop
        0x080C1E74,  # 0x4C77F0  j     0x3079D0         ; STOCK: original size-select bne
        0x8FA200E0,  # 0x4C77F4  lw    v0,0xe0(sp)      ; (delay) displaced hook insn; v1 intact
    ]
    P26_GATE = struct.unpack_from("<I", data, 0x209820)[0]   # Patch-14 hook (j 0x4C7540)
    if CHARGEN_DIAG:
        print("  ** CHARGEN_DIAG ON ** -> Patch 26 SKIPPED (diag owns cave 0x4C7790)")
    elif P26_GATE != RELOC.NEW_GATE_MARKER:
        print(f"  WARN Patch 14 not installed (hook=0x{P26_GATE:08X}) -> Patch 26 SKIPPED")
    else:
        hook_now = struct.unpack_from("<I", data, P26_HOOK)[0]
        cave_free = all(
            struct.unpack_from("<I", data, P26_CAVE + i * 4)[0] == 0
            for i in range(len(P26_CAVE_WORDS))
        )
        if hook_now == 0x8FA200E0 and cave_free:
            RELOC.assert_install_safe(RELOC.P26_VA, len(P26_CAVE_WORDS) * 4, "Patch 26 cave")
            for i, w in enumerate(P26_CAVE_WORDS):
                struct.pack_into("<I", data, P26_CAVE + i * 4, w)
            struct.pack_into("<I", data, P26_HOOK, P26_J_TO_CAVE)   # j RELOC.P26_VA
            assert struct.unpack_from("<I", data, P26_HOOK)[0] == P26_J_TO_CAVE
            assert struct.unpack_from("<I", data, P26_CAVE)[0] == 0x3C010050
            patched_count += 1
            print(f"  OK   0x3079CC -> j 0x{RELOC.P26_VA:06X}; 26-word ADV cave (abs mode==5 gate, "
                  f"canonical ADV @0x{RELOC.ADV2_VA:06X}, v1-preserving STOCK); chargen body now proportional")
        else:
            print(f"  WARN Patch 26 not applied: hook=0x{hook_now:08X} cave_free={cave_free}")

    # ─── FIRE_DIAG: box-renderer fire-counter (env FIRE_DIAG=1; pure read+store) ──────
    if FIRE_DIAG:
        print("\n--- FIRE_DIAG: box-renderer fire-counter (FIRE_DIAG=1) ---")
        FD_SCRATCH = 0x4DE060   # VA; eeMemory offset == VA; verified zero pristine+patched
        FD_CAVE = 0x4C7410      # VA; RUNTIME-RESIDENT free run (180B) beside the proven-live
                                # Patch-14 cave.  The old 0x4B0E00 is in a churn band the game
                                # OVERWRITES at runtime (live-confirmed) -> trampolines destroyed
                                # -> counters never incremented / high-freq hooks crashed.
        # $t8 (ptr) + $t0 (mode base) + $at (value): all DEAD at a function entry AND
        # PRESERVED across interrupts (the EE int handler saves/restores GPRs).  Do NOT
        # use $k0/$k1 here -- the int handler uses them as its own scratch and does NOT
        # preserve them, so a VBlank/DMA interrupt landing inside a high-frequency hook
        # (0x483E10/0x3B8820 fire 1000s/frame) corrupts the scratch ptr -> garbage store
        # -> black-screen crash.  And NOT $t9 -- it carries the PIC entry addr for .cpload.
        AT, A0, A1, RP, RM, SP, RA = 1, 4, 5, 24, 8, 29, 31

        def _efo(va):
            return va - 0x100000 + 0x80

        def _j(va):
            return 0x08000000 | ((va >> 2) & 0x03FFFFFF)

        def _lui(rt, imm):
            return (0x0F << 26) | (rt << 16) | (imm & 0xFFFF)

        def _ori(rt, rs, imm):
            return (0x0D << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

        def _itype(op, rt, base, off):
            return (op << 26) | (base << 21) | (rt << 16) | (off & 0xFFFF)

        def _lw(rt, base, off):
            return _itype(0x23, rt, base, off)

        def _sw(rt, base, off):
            return _itype(0x2B, rt, base, off)

        def _lh(rt, base, off):
            return _itype(0x21, rt, base, off)

        def _sh(rt, base, off):
            return _itype(0x29, rt, base, off)

        def _addiu(rt, rs, imm):
            return _itype(0x09, rt, rs, imm)

        SCR_HI, SCR_LO = FD_SCRATCH >> 16, FD_SCRATCH & 0xFFFF
        # (entry VA, counter slot, capture-args?)
        FD_HOOKS = [
            (0x3A3300, 0x00, True),    # draw_clamp12 (THE crux) + capture a0/a1/pitch/track/mode
            (0x3A2E10, 0x14, False),   # glyph-blit
            (0x483E10, 0x18, False),   # gsemit (universal sprite emit)
            (0x307510, 0x1C, False),   # the "eliminated" chargen sub-formatter
            (0x15CBC0, 0x20, False),   # request field drawer
            (0x1552B0, 0x24, False),   # menu list
            (0x165C60, 0x28, False),   # menu panel
            (0x3B8820, 0x2C, False),   # GIF builder
            (0x307DA0, 0x30, False),   # narration/dialogue host (control)
            (0x305E30, 0x34, False),   # old Block-1 chargen blit (control)
        ]

        # FIRE_SET=min -> install ONLY the menu-level renderers as SIMPLE counters (no
        # [sp] arg-capture).  Excludes the high-frequency engine emitters (blit 0x3A2E10,
        # gsemit 0x483E10, GIF builder 0x3B8820) + the dialogue host 0x307DA0 -- those fire
        # 1000s/frame in the DMA/render path and a detour there can disturb timing / black-
        # screen on boot.  The kept set still answers the only question that matters: which
        # renderer draws the box text (clamp12 0x3A3300 vs 0x307510 vs neither) and via
        # which caller (0x15CBC0/0x1552B0/0x165C60).  Default ("all") installs everything.
        FIRE_SET = os.environ.get("FIRE_SET", "all")
        if FIRE_SET == "min":
            _keep = {0x3A3300, 0x3A2E10, 0x483E10, 0x15CBC0}
            # 0x3A2E10 (glyph-blit) is reached by jalr from the text WALKER -> capture $ra
            # (the walker's return addr) + a0/a1 to NAME the indirect-dispatched renderer.
            FD_HOOKS = [
                (va, slot, ("ra" if va == 0x3A2E10 else None))
                for (va, slot, cap) in FD_HOOKS if va in _keep
            ]
            print(f"  (FIRE_SET=min: {len(FD_HOOKS)} menu-level hooks, simple counters only)")

        def _is_branch(x):  # reject PC-relative words from being relocated into the cave
            op = x >> 26
            if op in (0x02, 0x03, 0x01) or 0x04 <= op <= 0x07 or 0x14 <= op <= 0x17:
                return True
            if op == 0 and (x & 0x3F) in (0x08, 0x09):  # jr/jalr
                return True
            if op == 0x11 and ((x >> 21) & 0x1F) == 0x08:  # bc1
                return True
            return False

        tramp = FD_CAVE
        installs = []
        fd_ok = True
        for (va, slot, cap) in FD_HOOKS:
            e = _efo(va)
            w0 = struct.unpack_from("<I", data, e)[0]
            w1 = struct.unpack_from("<I", data, e + 4)[0]
            if (w0 & 0xFFFF0000) != 0x27BD0000:
                print(f"  WARN {va:#08x}: entry w0=0x{w0:08X} is not addiu sp,sp -> FIRE_DIAG ABORTED")
                fd_ok = False
                break
            if _is_branch(w1):
                print(f"  WARN {va:#08x}: entry+4 w1=0x{w1:08X} is PC-relative (cannot relocate) -> ABORTED")
                fd_ok = False
                break
            words = [
                _lui(RP, SCR_HI), _ori(RP, RP, SCR_LO),
                _lw(AT, RP, slot), _addiu(AT, AT, 1), _sw(AT, RP, slot),
            ]
            if cap == "ra":
                # Name the indirect-dispatched walker: $ra at the blit entry = the call site
                # INSIDE the walker (instruction after its jal/jalr 0x3A2E10).  Plus the last
                # glyph args.  ra/a0/a1 are live-at-entry and sp-independent -> capture as-is.
                words += [
                    _sw(RA, RP, 0x40),   # caller return addr (the WALKER)  <== KEY
                    _sw(A0, RP, 0x44),   # arg0
                    _sw(A1, RP, 0x48),   # arg1
                ]
            elif cap:
                words += [
                    _sw(A0, RP, 0x04), _sw(A1, RP, 0x08),        # flags, count (read before sp moves)
                    _lh(AT, SP, 0x00), _sh(AT, RP, 0x0C),        # pitch  ([sp+0x110] post-prologue == [sp+0] here)
                    _lh(AT, SP, 0x10), _sh(AT, RP, 0x0E),        # track  ([sp+0x120] == [sp+0x10] here)
                    _lui(RM, 0x50), _lw(AT, RM, 0xED18), _sw(AT, RP, 0x10),  # mode @0x4FED18 (absolute)
                ]
            words += [w0, w1, _j(va + 8), 0x00000000]   # re-exec displaced 2-word prologue, rejoin entry+8
            tfo = _efo(tramp)
            if any(struct.unpack_from("<I", data, tfo + i * 4)[0] != 0 for i in range(len(words))):
                print(f"  WARN cave @0x{tramp:X} not all-zero for {va:#08x} -> ABORTED")
                fd_ok = False
                break
            for i, wd in enumerate(words):
                struct.pack_into("<I", data, tfo + i * 4, wd)
            struct.pack_into("<I", data, e, _j(tramp))       # entry  -> j tramp
            struct.pack_into("<I", data, e + 4, 0x00000000)  # delay  -> nop (2nd insn moved into cave)
            installs.append((va, tramp, len(words)))
            tramp += len(words) * 4
        if fd_ok:
            # scratch ships zero in the EXE image (verified) and accumulates at runtime.
            patched_count += 1
            print(f"  OK   {len(installs)} entry hooks -> trampolines 0x4B0E00..0x{tramp:X}; "
                  f"counters @0x4DE060 (k0/k1, 2-word displaced + nop slot, j entry+8)")
            for va, t, n in installs:
                print(f"       0x{va:06X} -> j 0x{t:X}  ({n} words)")

    # ─── PATCH 27: BOX-TEXT PROPORTIONAL spacing (the REAL renderer, func 0x3A2EF0) ─────
    # THE fix.  After the whole hunt, the FIRE_DIAG $ra-capture proved chargen Status text
    # AND the tavern request body/labels are drawn by func 0x3A2EF0 (a char-32 glyph-stream
    # renderer just before draw_clamp12) -- NOT 0x305E30/0x307510/0x308xxx/draw_clamp12
    # (all live-proven dead/0 for this text).  Its per-glyph X cursor s1 advances by a
    # CONSTANT monospace pitch [sp+0xD0] at 0x3A31A0-0x3A31B4 (glyph X = baseX[sp+0xE0]+s1;
    # s1 reset to 0 on 0xFFFE linebreak).  Proportional = advance by ADV[gid] instead.
    #
    # Hook 0x3A31A0 (the pitch load) -> cave; gid recovered via lbu v1,-1(s2) (s2 already
    # bumped +2; gid is char-32 <95 so the hi byte is 0 -> index the resident Patch-14 ADV
    # table @0x4C7564 DIRECTLY, no +0x20).  Left-anchored renderer -> advance-only fix, no
    # centering coupling.  GATE: 0x3A2EF0 is NOT text-exclusive (its wrapper 0x3A3260 has
    # ~250 callers), so gate on mode mem[0x4FED18]: ==5 (chargen) OR ==7 (request) ->
    # proportional, else byte-identical STOCK (re-does the original pitch path).  NOTE mode 7
    # is shared by request + town menus -> some town menus may also go proportional; flagged
    # for playtest.  Cave @0x4C7410 (resident, verified live; the FIRE_DIAG cave reuses it ->
    # Patch 27 installs only in PRODUCTION, not FIRE_DIAG).  Gated on Patch-14 installed.
    if DISABLE_P27_P14:
        # CONFIRM build: leave 0x3A31A0 / 0x3A31A4 PRISTINE -- no j into a relocated cave.
        print("\n--- Patch 27: SKIPPED via DISABLE_P27_P14=1 (battle-root-cause CONFIRM build) ---")
    elif not FIRE_DIAG:
        print("\n--- Patch 27: BOX-TEXT proportional (real renderer 0x3A2EF0, mode 5/7 gated) [v147 RELOCATED] ---")
        P27_HOOK = 0x2A3220      # VA 0x3A31A0, pristine 0x8FA300D0 (lw v1,0xD0(sp) = pitch)
        P27_DELAY = 0x2A3224     # VA 0x3A31A4, pristine 0x00031C3C (dsll32) -> nop
        # v147 BATTLE-FIX (SIMPLIFIED): the cave is RELOCATED out of the heap arena (was VA
        # 0x4C7410, which SOME battle phases heap-stomp -> `j 0x4C7410` jumped into garbage ->
        # no monsters/abort; PROVEN: word0 0x3C030050 -> 0x3C010050 in battlebreak/fightsoftlock
        # dumps).  New home = RELOC.P27_VA in verified-safe code-segment padding (pad after a
        # `jr ra` epilogue, zero in pristine + every live dump).  The cave is BYTE-FAITHFUL to
        # the production 0x4C7410 cave -- it reads the CANONICAL 256-byte ADV table directly
        # (lbu 0x7564(0x4C0000), intact across all dumps).  NO table relocation, NO ASCII guard,
        # NO 95-byte shrink.  Mode gate via $v1 (chargen==5 / request==7) -> battle takes the
        # register-faithful STOCK path.  Only the cave base + its hook's j-target changed.
        P27_CAVE = RELOC.fo(RELOC.P27_VA)
        P27_J_TO_CAVE = RELOC.P27_HOOK_JWORD   # j RELOC.P27_VA
        P27_CAVE_WORDS = RELOC.P27_WORDS
        P27_GATE = struct.unpack_from("<I", data, 0x209820)[0]   # Patch-14 marker (relocated)
        if P27_GATE != RELOC.NEW_GATE_MARKER:
            print(f"  WARN Patch 14 not installed (hook=0x{P27_GATE:08X}) -> Patch 27 SKIPPED")
        else:
            hook_now = struct.unpack_from("<I", data, P27_HOOK)[0]
            cave_free = all(
                struct.unpack_from("<I", data, P27_CAVE + i * 4)[0] == 0
                for i in range(len(P27_CAVE_WORDS))
            )
            if hook_now == 0x8FA300D0 and cave_free:
                RELOC.assert_install_safe(RELOC.P27_VA, len(P27_CAVE_WORDS) * 4, "Patch 27 cave")
                for i, wd in enumerate(P27_CAVE_WORDS):
                    struct.pack_into("<I", data, P27_CAVE + i * 4, wd)
                struct.pack_into("<I", data, P27_HOOK, P27_J_TO_CAVE)     # j RELOC.P27_VA
                struct.pack_into("<I", data, P27_DELAY, 0x00000000)       # delay -> nop
                assert struct.unpack_from("<I", data, P27_HOOK)[0] == P27_J_TO_CAVE
                assert struct.unpack_from("<I", data, P27_CAVE)[0] == P27_CAVE_WORDS[0]
                patched_count += 1
                print(f"  OK   0x3A31A0 -> j 0x{RELOC.P27_VA:06X} (RELOCATED below arena); "
                      f"{len(P27_CAVE_WORDS)}-word cave (gid lbu -1(s2), canonical ADV @0x{RELOC.ADV2_VA:06X}, "
                      "mode==5/7 gate via $v1 -> battle-safe STOCK path); chargen + request box text proportional")
            else:
                print(f"  WARN Patch 27 not applied: hook=0x{hook_now:08X} cave_free={cave_free}")

    # ─── PATCH 29: BOX-TEXT first-letter-gap fix — LEFTSHIFT draw-shift (renderer 0x3A2EF0) ──
    # Patch 27 gave renderer 0x3A2EF0 proportional ADVANCE but NOT the companion left-bearing
    # draw-shift (LSH) that the narration renderer already has (Patch 14 cave2).  So box ink
    # lands at baseX+pen+ink_left(gid) and the gap balloons after a low-bearing leading capital
    # ("A....llocate").  Patch 29 mirrors Patch 14 cave2 for BOTH glyph draw-X sites in 0x3A2EF0
    # (0x3A30F4 path A, 0x3A3170 path B — both pristine `addu v1,v0,v1`), hooking each with a
    # `jal` into ONE shared subroutine (ra is free in the 0x3A2EF0 loop: saved 0x3A2EF8, restored
    # only at exit 0x3A31D8).  The sub reloads baseX (sp+0xE0; v0 is clobbered by the jal delay
    # slot lbu v0,off(sp)), recovers gid via `lbu -1(s2)` (same as Patch 27), reads LEFTSHIFT2[gid]
    # from the R2100 table @0x4C7790 (RANK-2: this renderer draws the R2100 upright font), and
    # subtracts it from draw-X.  MODE-GATE on 0x4FED18 in {5,7}: for battle (mode 8) and the ~250
    # other callers the sub returns the byte-identical STOCK draw-X (baseX+pen).  Because no
    # contiguous >=52B safe .text hole remains below the arena, the sub is SPLIT across two
    # verified-zero pads — frag1 @0x4B0C48 (40B) + frag2 @0x4B0BC8 (16B) — both < 0x4B0DCF and
    # clear of the libgraph block; see _reloc_v147_design build_p29().  Gated on Patch 14 (LSH
    # table resident) and skipped in the DISABLE_P27_P14 / FIRE_DIAG diagnostic builds.
    if DISABLE_P27_P14:
        print("\n--- Patch 29: SKIPPED via DISABLE_P27_P14=1 (battle-root-cause CONFIRM build) ---")
    elif FIRE_DIAG:
        print("\n--- Patch 29: SKIPPED (FIRE_DIAG diagnostic build) ---")
    else:
        print("\n--- Patch 29: BOX-TEXT first-letter-gap LSH (renderer 0x3A2EF0, mode 5/7 gated) ---")
        P29_HOOK1_FO = RELOC.fo(RELOC.P29_HOOK1)   # file 0x2A3174 (VA 0x3A30F4)
        P29_HOOK2_FO = RELOC.fo(RELOC.P29_HOOK2)   # file 0x2A31F0 (VA 0x3A3170)
        P29_F1_FO    = RELOC.fo(RELOC.P29_F1_VA)
        P29_F2_FO    = RELOC.fo(RELOC.P29_F2_VA)
        P29_JW       = RELOC.P29_HOOK_JWORD        # jal 0x4B0C48
        gate = struct.unpack_from("<I", data, 0x209820)[0]   # Patch-14 marker (LSH table resident)
        h1 = struct.unpack_from("<I", data, P29_HOOK1_FO)[0]
        h2 = struct.unpack_from("<I", data, P29_HOOK2_FO)[0]
        if gate != RELOC.NEW_GATE_MARKER:
            print(f"  WARN Patch 14 not installed (marker=0x{gate:08X}) -> Patch 29 SKIPPED (no LSH table)")
        elif h1 == P29_JW and h2 == P29_JW:
            print("  SKIP Patch 29 already installed (both sites jal cave)")
        elif h1 == RELOC.P29_ORIG_SITE and h2 == RELOC.P29_ORIG_SITE:
            f1_free = all(struct.unpack_from("<I", data, P29_F1_FO + i * 4)[0] == 0
                          for i in range(len(RELOC.P29_F1_WORDS)))
            f2_free = all(struct.unpack_from("<I", data, P29_F2_FO + i * 4)[0] == 0
                          for i in range(len(RELOC.P29_F2_WORDS)))
            if not (f1_free and f2_free):
                print(f"  WARN Patch 29 cave pads not zero (f1={f1_free} f2={f2_free}) -> SKIPPED")
            else:
                RELOC.assert_install_safe(RELOC.P29_F1_VA, len(RELOC.P29_F1_WORDS) * 4, "Patch 29 frag1")
                RELOC.assert_install_safe(RELOC.P29_F2_VA, len(RELOC.P29_F2_WORDS) * 4, "Patch 29 frag2")
                for i, wd in enumerate(RELOC.P29_F1_WORDS):
                    struct.pack_into("<I", data, P29_F1_FO + i * 4, wd)
                for i, wd in enumerate(RELOC.P29_F2_WORDS):
                    struct.pack_into("<I", data, P29_F2_FO + i * 4, wd)
                struct.pack_into("<I", data, P29_HOOK1_FO, P29_JW)   # jal cave (delay slot 0x3A30F8 left as-is)
                struct.pack_into("<I", data, P29_HOOK2_FO, P29_JW)   # jal cave (delay slot 0x3A3174 left as-is)
                assert struct.unpack_from("<I", data, P29_HOOK1_FO)[0] == P29_JW
                assert struct.unpack_from("<I", data, P29_HOOK2_FO)[0] == P29_JW
                assert struct.unpack_from("<I", data, P29_F1_FO)[0] == RELOC.P29_F1_WORDS[0]
                patched_count += 1
                print(f"  OK   0x3A30F4 + 0x3A3170 -> jal 0x{RELOC.P29_F1_VA:06X} (2 hooks); "
                      f"frag1 {len(RELOC.P29_F1_WORDS)}w @0x{RELOC.P29_F1_VA:06X} + frag2 "
                      f"{len(RELOC.P29_F2_WORDS)}w @0x{RELOC.P29_F2_VA:06X} "
                      f"(gid lbu -1(s2), canonical LSH @0x{RELOC.LSH2_VA:06X}, mode==5/7 gate -> battle-safe STOCK)")
        else:
            print(f"  WARN Patch 29 sites not pristine: h1=0x{h1:08X} h2=0x{h2:08X} -> SKIPPED")

    # ─── PATCH 31: CHARGEN DESCRIPTION-box first-letter-gap LSH (renderer 0x307510) ─────────
    # Patch 26 gave the LIVE chargen body/description renderer func 0x307510 (line-walk
    # 0x307DA0 -> glyph blit 0x307510 -> emit 0x3060B0) a proportional ADVANCE (hook
    # @0x3079CC, gated mem[0x4FED18]==5) but NOT the companion left-bearing draw-shift, so
    # the race/alignment DESCRIPTION boxes render with uneven "random spaces".  Patch 31 is
    # the 0x307510 analogue of Patch 29 (which did this for the OTHER renderer 0x3A2EF0):
    # it subtracts LEFTSHIFT2[gid] (R2100 table @0x4C7790, RANK-2 -- this renderer draws the
    # R2100 upright font) from the draw-X, mode-gated ==5 exactly like Patch 26 so ADV+LSH stay
    # in lockstep and every other surface (town/menus at other modes, battle) is byte-
    # identical (subu 0).  Single draw-X site 0x307974 (`lh t2,0(s2)`, the penX read that
    # flows to `addu t2,t2,t0` draw-X @0x307980); hook -> j frag1, the pristine delay slot
    # 0x307978 (`lh t1,0(v0)`) is left as the j delay slot.  gid = the ACTUAL drawn glyph,
    # stored `sd v0,0x10(sp)` @0x307960 (recovered via lhu 0x10(sp); == Patch 26's advanced
    # gid on the desc text), ASCII-guarded (sltiu<95 + movz -> gid>=95 subtracts nothing).
    # Sub is BRANCHLESS + split across two verified-zero post-`jr ra` .text pads below the
    # arena: frag1 @0x4AFA00 (40B) + frag2 @0x4AB5EC (20B); see _reloc build_p31().  Gated on
    # Patch 14 (LSH table resident) and skipped in the DISABLE_P27_P14 / FIRE_DIAG builds.
    if DISABLE_P27_P14:
        print("\n--- Patch 31: SKIPPED via DISABLE_P27_P14=1 (battle-root-cause CONFIRM build) ---")
    elif FIRE_DIAG:
        print("\n--- Patch 31: SKIPPED (FIRE_DIAG diagnostic build) ---")
    else:
        print("\n--- Patch 31: CHARGEN desc-box LSH (renderer 0x307510, mode 5 gated) ---")
        P31_HOOK_FO = RELOC.fo(RELOC.P31_HOOK)     # file 0x2079F4 (VA 0x307974)
        P31_F1_FO   = RELOC.fo(RELOC.P31_F1_VA)
        P31_F2_FO   = RELOC.fo(RELOC.P31_F2_VA)
        P31_JW      = RELOC.P31_HOOK_JWORD         # j 0x4AFA00
        gate = struct.unpack_from("<I", data, 0x209820)[0]   # Patch-14 marker (LSH table resident)
        h = struct.unpack_from("<I", data, P31_HOOK_FO)[0]
        if gate != RELOC.NEW_GATE_MARKER:
            print(f"  WARN Patch 14 not installed (marker=0x{gate:08X}) -> Patch 31 SKIPPED (no LSH table)")
        elif h == P31_JW:
            print("  SKIP Patch 31 already installed (draw-X site j cave)")
        elif h == RELOC.P31_ORIG_SITE:
            f1_free = all(struct.unpack_from("<I", data, P31_F1_FO + i * 4)[0] == 0
                          for i in range(len(RELOC.P31_F1_WORDS)))
            f2_free = all(struct.unpack_from("<I", data, P31_F2_FO + i * 4)[0] == 0
                          for i in range(len(RELOC.P31_F2_WORDS)))
            if not (f1_free and f2_free):
                print(f"  WARN Patch 31 cave pads not zero (f1={f1_free} f2={f2_free}) -> SKIPPED")
            else:
                RELOC.assert_install_safe(RELOC.P31_F1_VA, len(RELOC.P31_F1_WORDS) * 4, "Patch 31 frag1")
                RELOC.assert_install_safe(RELOC.P31_F2_VA, len(RELOC.P31_F2_WORDS) * 4, "Patch 31 frag2")
                for i, wd in enumerate(RELOC.P31_F1_WORDS):
                    struct.pack_into("<I", data, P31_F1_FO + i * 4, wd)
                for i, wd in enumerate(RELOC.P31_F2_WORDS):
                    struct.pack_into("<I", data, P31_F2_FO + i * 4, wd)
                struct.pack_into("<I", data, P31_HOOK_FO, P31_JW)   # j cave (delay slot 0x307978 left as-is)
                assert struct.unpack_from("<I", data, P31_HOOK_FO)[0] == P31_JW
                assert struct.unpack_from("<I", data, P31_F1_FO)[0] == RELOC.P31_F1_WORDS[0]
                assert struct.unpack_from("<I", data, P31_F2_FO)[0] == RELOC.P31_F2_WORDS[0]
                patched_count += 1
                print(f"  OK   0x307974 -> j 0x{RELOC.P31_F1_VA:06X}; frag1 {len(RELOC.P31_F1_WORDS)}w "
                      f"@0x{RELOC.P31_F1_VA:06X} + frag2 {len(RELOC.P31_F2_WORDS)}w @0x{RELOC.P31_F2_VA:06X} "
                      f"(gid lhu 0x10(sp), canonical LSH @0x{RELOC.LSH2_VA:06X}, mode==5 gate -> stock draw-X elsewhere)")
        else:
            print(f"  WARN Patch 31 site not pristine: h=0x{h:08X} -> SKIPPED")

    # ─── PATCH 28: CHARGEN race-list nudge-left (REAL lever — race-NAME pen origin) ─────────
    # The race-select name list (Human/Elf/Gnome/Dwarf/Hobbit/+) overflows the parchment RIGHT edge
    # after Patch 27's proportional widening.  LIVE-TRACED (PCSX2 run-until-return walk-up of the
    # draw chain 0x3A3260<-0x319D8C<-0x142A60<-0x144A90<-0x14BED0): the name column's horizontal
    # PEN ORIGIN is an immediate in the race-select list renderer 0x14BED0 --
    #   VA 0x14C070 (file 0x4C0F0):  addiu v0,zero,-104   (word 0x2402FF98)
    # sets pen-X = -104 (rel. to the box origin); the per-char loop advances it by glyph widths.
    # The OLD edit to coord table 0x4D0270 (X 16->-28) was DEAD: that table positions the OFF-SCREEN
    # marker icons at X=-232, NOT the names (proven live -- the -28 loaded in RAM but the names never
    # moved a pixel).  0x4D0270 is now left PRISTINE.  Make the origin more negative to shift names
    # left.  BATTLE-SAFE: 0x14BED0 is chargen-only (exactly 2 callers, both the chargen menu module;
    # reads race field 0x49e; mode-gated 0x4FED18==5) and this is a plain in-place .text immediate at
    # VA 0x14C070 << 0x4B0DCF -- no cave, arena/battle rules N/A.  Only the low-16 immediate changes.
    # PATCH 28: chargen race-NAME column left-nudge -- the REAL lever, LIVE-TRACED (finally).
    # A MEMORY-READ breakpoint on the live "Human" glyph data (RAM 0x00E144D4, verified all 6 race
    # names) + a run-until-return walk-up of the GENUINE race-name draw chain
    #   renderer 0x3A2EF0 <- wrapper 0x3A3260 <- site-B 0x4913AC <- 0x142410 <- func 0x149820
    # landed on the origin.  0x149820 (dispatched indirectly by the chargen list renderer 0x14BED0)
    # sets the two column X origins that flow to 0x142410:
    #   0x1498A0: addiu t2,zero,-216  = MARKER column (off-screen)
    #   0x1498A8: addiu t3,zero,-104  = NAME column   <-- this one
    # (matches the independently-found "names at -104, markers at -232".)  Shift the -104 more
    # negative to pull the race names left off the parchment right edge.  The three prior candidates
    # were all FALSIFIED -- 0x4D0270 (off-screen markers), 0x14C070 (the Sex info-banner, moved the
    # banner not the names), and t0=17 (a2, wrong param) -- because none was anchored on an actual
    # race-name glyph; this one is.  SAFETY: 0x149820 has 0 direct callers (indirect jalr from the
    # chargen module only) -> chargen-dispatched; plain in-place .text immediate at VA 0x1498A8 <<
    # 0x4B0DCF (no cave, arena rules N/A).  CONFIRM ON BOOT that ONLY the race names move; tune
    # P28_NEW if it over/under-shoots.
    # UPDATE (v156): the REAL X lever was finally traced byte-for-byte. baseX (sp+0xE0) <- t2=-216.
    # v154 proved the sibling 0x1498A8 (t3=-104) is the Y axis (box moved UP, names unchanged); its
    # neighbour t2=-216 is the X. 0x142410 is dispatched to 3 handlers (0x149710/0x149820/0x149DE0) by
    # item selection state, EACH carrying the same t2=-216, so ALL THREE shift together:
    #   VA 0x149788 (file 0x49808), 0x1498A0 (file 0x49920), 0x149E5C (file 0x49EDC) = addiu t2,zero,-216
    # baseX = sext16(t2)+28; more negative = further left. Chargen-only (dispatch table 0x4B6180 +
    # 0x142410's 3 callers live only in the 0x14Cxxx chargen module -> the shared renderer stays
    # byte-identical for battle/town). Plain in-place .text immediates (all << 0x4B0DCF), no cave.
    # The five earlier candidates (0x4D0270, 0x14C070, t0=17, 0x1498A8 Y-axis) stay PRISTINE. Tune P28_NEW.
    print("\n--- Patch 28: chargen race-NAME column nudge-left (3x addiu t2,zero,-216) ---")
    P28_SITES = (0x49808, 0x49920, 0x49EDC)   # file offs of VA 0x149788 / 0x1498A0 / 0x149E5C
    # v158: REVERTED TO STOCK (-216).  The right-edge overflow Patch 28 compensated for
    # (-241 in v156, -260 overshoot in v157) was caused by the WRONG-FONT advance bloat:
    # the name lists flow through 0x3A2EF0 (P27), which applied R1188 ADV (avg 17.4px) to
    # the R2100 16px font ("H u m a n" ~97px).  With the R2100 ADV2 tables (avg 10.4px)
    # "Human" is ~56px and fits at the stock origin, so the nudge is no longer needed.
    # Set P28_NEW more negative again ONLY if a fresh capture still shows right-edge
    # clipping.  word = 0x240A0000 | (P28_NEW & 0xFFFF).
    P28_NEW = -216                            # STOCK. tune here if a capture shows clipping
    if not all(struct.unpack_from("<I", data, s)[0] == 0x240AFF28 for s in P28_SITES):  # addiu t2,zero,-216
        vals = [f"0x{struct.unpack_from('<I', data, s)[0]:08X}" for s in P28_SITES]
        print(f"  WARN race-name X sites not all pristine ({vals}) -> Patch 28 SKIPPED")
    elif P28_NEW == -216:
        print("  SKIP race-name column X stays STOCK -216 (v158: R2100 ADV2 tables removed the overflow)")
    else:
        for s in P28_SITES:
            struct.pack_into("<h", data, s, P28_NEW)   # rewrite low-16 immediate only
        patched_count += 1
        print(f"  OK   race-name column X -216 -> {P28_NEW} ({-216 - P28_NEW}px left) x3 handlers")

    # ─── PATCH 30: CHARGEN SIDEBAR value-column left-shift (in-place .text immediate) ──
    # The chargen SIDEBAR VALUE fields (Sex / Race:Human / Align:Good / Class:Fight)
    # overflow their boxes on the RIGHT on ALL chargen screens.  They share ONE base-X
    # immediate, traced end-to-end to the renderer baseX:
    #   VA 0x14C0A0 (file 0x4C120)  addiu t3,zero,72  (word 0x240B0048) -- the shared
    #   value-column base X, the t3 arg to `jal 0x144A90` @0x14C09C (chargen module
    #   0x14BED0; the value graph 0x144A90/0x142A60 has ONLY chargen-module callers).
    # Change 72 -> 44 (word 0x240B002C, ~28px left).  Plain in-place .text immediate at
    # VA 0x14C0A0 << 0x4B0DCF -- chargen-only, no cave, no mode-gate (structural surface
    # isolation).  Do NOT touch 0x14C070 (the Sex info-banner v0=-104) or 0x14C0A0's
    # NEIGHBOURS.  Gate strictly on the pristine word 0x240B0048.
    print("\n--- Patch 30: chargen sidebar value-column left-shift (72 -> 44) ---")
    P30_OFF = 0x4C120                         # file off of VA 0x14C0A0
    P30_PRISTINE = 0x240B0048                 # addiu t3,zero,72
    P30_NEW = 0x240B002C                      # addiu t3,zero,44  (~28px left)
    cur30 = struct.unpack_from("<I", data, P30_OFF)[0]
    if cur30 == P30_PRISTINE:
        struct.pack_into("<I", data, P30_OFF, P30_NEW)
        print(f"  OK   0x14C0A0: sidebar value-column base X 72 -> 44 (28px left)")
        patched_count += 1
    elif cur30 == P30_NEW:
        print(f"  SKIP 0x14C0A0: already 44 (0x{P30_NEW:08X})")
    else:
        print(f"  WARN 0x14C0A0 = 0x{cur30:08X}, expected pristine 0x{P30_PRISTINE:08X} -> Patch 30 SKIPPED")

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
    # v148 BATTLE-ARENA EVACUATION: the cave moves 0x4CAA30 -> RELOC.P24_VA (0x4AFA58),
    # verified-zero .text padding.  The cave's `bne` is PC-relative (invariant) and
    # `j 0x309744` is absolute (unchanged), so the 6 words ship BYTE-IDENTICAL; only the
    # cave base + the hook's j-immediate change.
    print("\n--- Patch 24: NARRATION boxX=+96 via draw-X load @0x30973c (gated boxX==0) [v148 RELOCATED] ---")
    P24_OFF = 0x2097BC          # VA 0x30973c (lh t2,0x3c(s0) = read boxX)
    P24_ORIG = 0x860A003C       # lh   t2,0x3c(s0)
    P24_HOOK = RELOC.P24_HOOK_JWORD  # j RELOC.P24_VA (0x4AFA58)
    P24_CAVE_OFF = RELOC.fo(RELOC.P24_VA)   # VA RELOC.P24_VA
    P24_CAVE = [
        0x860A003C,  # lh    t2,0x3c(s0)        ; reload boxX
        0x15400002,  # bne   t2,zero,+2         ; boxX!=0 (dialogue/request) -> keep (PC-rel)
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
            print(f"  WARN cave 0x{RELOC.P24_VA:06X} not free -- Patch 24 SKIPPED")
        else:
            RELOC.assert_install_safe(RELOC.P24_VA, len(P24_CAVE) * 4, "Patch 24 cave")
            struct.pack_into("<I", data, P24_OFF, P24_HOOK)
            for i, w in enumerate(P24_CAVE):
                struct.pack_into("<I", data, P24_CAVE_OFF + i * 4, w)
            print(f"  OK   0x{P24_OFF:06X}: lh t2,0x3c(s0) -> j 0x{RELOC.P24_VA:06X}; "
                  f"cave sets boxX=96 only if boxX==0")
            patched_count += 1
    else:
        print(f"  WARN 0x{P24_OFF:06X}: expected 0x{P24_ORIG:08X}, got 0x{p24:08X} -- Patch 24 SKIPPED")

    # ─── PATCH 25: REQUEST body PROPORTIONAL advance (mirror Patch 14) + Option-B fixed margin ─
    # GOAL (Issue B horizontal overflow): the tavern request DESCRIPTION body renders through
    #   the universal R1188 renderer's Block-2 (pen sp+0x1ce), reached via the align-mode
    #   dispatcher's v1==2 branch (addiu v0,zero,2; bne v1,v0 @0x308928).  Patch 22 already
    #   pinned the Block-2 DEFAULT-metric advance to a flat 18px monospace (addiu v0,v0,0x18
    #   -> 0x12 @0x308CB0) and converted the centering reserve to count*18 (@0x30896C/0x308974).
    #   Patch 25 replaces the flat 18px step with the SAME per-glyph proportional advance the
    #   narration body uses (Patch 14's resident ADV table @VA 0x4C7564, gid = cell>>8), so the
    #   verbose English compresses ~17-20% horizontally (avg ADV ~17.4px, real-text ~14.7px vs
    #   18px mono) and stops over-running the parchment.
    #
    # HOOK (structural gate — instruction address, no runtime flag needed):
    #   VA 0x308CAC (file 0x208D2C, pristine 0x87A201CE = lh v0,0x1ce(sp)) is the head of the
    #   Block-2 DEFAULT-metric advance.  It is reached ONLY by the align v1==2 Block-2 branch
    #   (request body).  Narration's identical default advance is the SEPARATE site 0x3097A4
    #   (already Patch-14-hooked @0x3097A0); dialogue is func 0x307510; chargen is 0x308040
    #   (pen sp+0x1cc).  So hooking 0x308CAC affects ONLY the request body — no blast radius.
    #   Hook -> j 0x4CAA48 (cave); the delay slot 0x308CB0 (Patch-22's addiu v0,v0,0x12) is
    #   nop'd (the cave reloads pen, so the displaced/skipped step is harmless either way).
    #
    # CAVE @ VA 0x4CAA48 (file 0x3CAAC8), 10 words / 40 B — the verified-zero pad immediately
    #   AFTER Patch-24's cave (0x4CAA30..0x4CAA48) and BEFORE the (never-installed, obsolete)
    #   Patch-16 watchdog region.  cave reads the current glyph cell at 2(s5) (s5 is NOT bumped
    #   until 0x308CD8, so 2(s5) still holds the current cell — same trick as Patch 19's re-read),
    #   derives gid = cell>>8 (cells are (char-32)<<8, hi byte = gid), looks up ADV[gid] from the
    #   RESIDENT Patch-14 table @0x4C7564, adds it to pen sp+0x1ce, stores, and rejoins
    #   j 0x308CD8 (0x080C2336 — the s5 bump / next-glyph target both default & COP2 paths reach).
    #   Scratch regs: at/t8/t9 ONLY (v0 = pen, overwritten downstream); s5/v1 preserved.
    #
    # OPTION B (fixed left margin, align==2 only): a proportional advance WITHOUT also fixing the
    #   count*18 centering reserve re-introduces the Patch-19 Stage-3 drift (reserve assumes
    #   count*18 but glyphs now step ADV != 18).  Mirroring Patch 20's Option B, we pin the line
    #   origin to a FIXED left margin by neutralizing the count term at VA 0x308968
    #   (subu a0,v0,a0  ->  move a0,zero), so the reserve idiom @0x30896C..0x308974 computes
    #   0*18 = 0 and origin = box_base (count-independent).  0x308968 is on the align v1==2
    #   Block-2 path ONLY (same structural gate as Patch 22), so this is align==2-scoped with no
    #   runtime flag — narration (pen 0x1cc / 0x308328) and dialogue/chargen never reach it.
    #
    # GATE: install ONLY if the Patch-14 resident ADV table is present — the marker word
    #   file 0x209820 (VA 0x3097A0) == 0x08131D50 (Patch-14's j 0x4C7540).  WARN-and-skip on
    #   mismatch (the cave's ADV lookup would read garbage otherwise).
    #
    # !!! LIVE CONTINGENCY (OFF BY DEFAULT — flip PATCH25_ENABLE only after a live confirm) !!!
    #   reconB4 says the body takes the DEFAULT (sp+0x110==100) advance path and is
    #   left-anchorable -> Option B (fixed margin) is correct.  But reconB3 measured the body
    #   as COUNT-ANCHORED / centered (origin = box_base + (box_width-count)*18) from the live
    #   requestissue.p2s RAM, which CONTRADICTS left-anchorability.  This conflict can ONLY be
    #   settled with the live PCSX2 EE debugger (break 0x4CAA48 to confirm the hook fires per
    #   glyph on the DEFAULT path; break 0x308964 to read box_width; confirm the body is
    #   left-anchorable, not centered).  If the body is CENTERED, Option B is WRONG and Option A
    #   (summed-ADV re-center) is required instead.  Because that confirmation is not yet
    #   available (cannot drive the live debugger here), Patch 25 ships DISABLED so it cannot
    #   regress the current Patch-22 18px-mono behaviour.  Set PATCH25_ENABLE = True ONLY after
    #   the live confirm.  file_off = VA - 0x100000 + 0x80.
    # v158 NOTE: if this is ever enabled, first decide the table -- the request-desc
    # body renders in the R2100 upright font (requestissue.p2s), so the cave's
    # lbu 0x7564 (canonical R1188 ADV) likely needs to become the R2100 ADV2 read
    # (lui 0x4C / lbu 0x785F, RELOC.ADV2_VA) like Patches 26/27 (RANK-2).
    PATCH25_ENABLE = False   # <-- flip to True ONLY after live-debugger confirms DEFAULT path + left-anchor
    print("\n--- Patch 25: REQUEST body proportional advance @0x308CAC + Option-B fixed margin (align==2) ---")
    P25_HOOK   = 0x208D2C        # VA 0x308CAC  lh v0,0x1ce(sp)  (Block-2 default advance head)
    P25_HOOK_ORIG = 0x87A201CE   # pristine displaced instruction
    P25_HOOK_J = 0x08132A92      # j 0x4CAA48 (cave)
    P25_DELAY  = 0x208D30        # VA 0x308CB0  (Patch-22 addiu v0,v0,0x12 / pristine 0x18) -> nop
    P25_CAVE   = 0x3CAAC8        # VA 0x4CAA48 (40-byte cave, verified zero, after Patch-24 cave)
    P25_MARGIN_OFF  = 0x2089E8   # VA 0x308968  subu a0,v0,a0 (count reserve) -> move a0,zero
    P25_MARGIN_ORIG = 0x00442023 # subu $a0,$v0,$a0
    P25_MARGIN_NEW  = 0x00002021 # move $a0,$zero  (a0=0 -> reserve = 0*18 = 0 -> origin = box_base)
    P25_GATE_OFF    = 0x209820   # VA 0x3097A0  Patch-14 marker
    P25_GATE_VAL    = RELOC.NEW_GATE_MARKER # j relocated P14 cave1 (Patch-14 installed, v147)
    p25_cave = [
        0x96A20002,  # 0x4CAA48  lhu  v0, 2(s5)        ; v0 = current glyph cell (s5 not yet bumped)
        0x0002C202,  # 0x4CAA4C  srl  t8, v0, 8        ; t8 = gid = cell>>8 (hi byte = char-32)
        0x3C01004C,  # 0x4CAA50  lui  at, 0x4C         ; at = 0x4C0000 (resident ADV @+0x7564)
        0x00380821,  # 0x4CAA54  addu at, at, t8       ; at = 0x4C0000 + gid
        0x90397564,  # 0x4CAA58  lbu  t9, 0x7564(at)   ; t9 = ADV[gid]
        0x87A201CE,  # 0x4CAA5C  lh   v0, 0x1ce(sp)    ; v0 = pen (displaced hook insn)
        0x00591021,  # 0x4CAA60  addu v0, v0, t9       ; pen += ADV
        0xA7A201CE,  # 0x4CAA64  sh   v0, 0x1ce(sp)    ; store pen
        0x080C2336,  # 0x4CAA68  j    0x308CD8         ; rejoin (s5 bump / next glyph)
        0x00000000,  # 0x4CAA6C  nop  (delay slot)
    ]
    if not PATCH25_ENABLE:
        # OFF-by-default: verify the install preconditions still hold (so a future enable is a
        # one-line flip), then leave the EXE byte-identical to the Patch-22 18px-mono behaviour.
        h25 = struct.unpack_from("<I", data, P25_HOOK)[0]
        gate = struct.unpack_from("<I", data, P25_GATE_OFF)[0]
        cave_free = all(b == 0 for b in data[P25_CAVE:P25_CAVE + len(p25_cave) * 4])
        margin = struct.unpack_from("<I", data, P25_MARGIN_OFF)[0]
        print(f"  DISABLED (PATCH25_ENABLE=False, awaiting live confirm DEFAULT-path + left-anchor)")
        print(f"  precheck: hook@0x{P25_HOOK:06X}=0x{h25:08X} (want 0x{P25_HOOK_ORIG:08X}); "
              f"marker@0x{P25_GATE_OFF:06X}=0x{gate:08X} (want 0x{P25_GATE_VAL:08X})")
        print(f"  precheck: cave@0x4CAA48 free={cave_free}; reserve@0x308968=0x{margin:08X} "
              f"(want 0x{P25_MARGIN_ORIG:08X})")
    else:
        h25 = struct.unpack_from("<I", data, P25_HOOK)[0]
        gate = struct.unpack_from("<I", data, P25_GATE_OFF)[0]
        cave_free = all(b == 0 for b in data[P25_CAVE:P25_CAVE + len(p25_cave) * 4])
        cave_done = struct.unpack_from("<I", data, P25_CAVE)[0] == p25_cave[0]
        margin = struct.unpack_from("<I", data, P25_MARGIN_OFF)[0]
        if gate != P25_GATE_VAL:
            print(f"  WARN Patch 14 not installed (marker 0x{gate:08X}) -> Patch 25 SKIPPED")
        elif h25 == P25_HOOK_J and cave_done:
            print(f"  SKIP 0x{P25_HOOK:06X}: request-body proportional advance already installed")
        elif h25 == P25_HOOK_ORIG and (cave_free or cave_done):
            # advance cave + trampoline (nop the displaced/Patch-22 advance delay slot)
            for i, w in enumerate(p25_cave):
                struct.pack_into("<I", data, P25_CAVE + i * 4, w)
            struct.pack_into("<I", data, P25_HOOK, P25_HOOK_J)      # j 0x4CAA48
            struct.pack_into("<I", data, P25_DELAY, 0x00000000)     # delay slot -> nop
            # Option B: pin line origin to fixed left margin (align==2 only)
            if margin == P25_MARGIN_NEW:
                pass  # already neutralized
            elif margin == P25_MARGIN_ORIG:
                struct.pack_into("<I", data, P25_MARGIN_OFF, P25_MARGIN_NEW)
            else:
                print(f"  WARN 0x{P25_MARGIN_OFF:06X}: reserve idiom 0x{margin:08X} unexpected -- margin left as-is")
            print(f"  OK   0x{P25_CAVE:06X}: request-body proportional ADV cave (gid=cell>>8, ADV@0x4C7564)")
            print(f"  OK   0x{P25_HOOK:06X}: lh v0,0x1ce(sp) -> j 0x4CAA48; delay slot -> nop")
            print(f"  OK   0x{P25_MARGIN_OFF:06X}: subu a0,v0,a0 -> move a0,zero (Option B fixed left margin)")
            patched_count += 1
        else:
            print(f"  WARN 0x{P25_HOOK:06X}: hook=0x{h25:08X} cave_free={cave_free} -- Patch 25 SKIPPED")

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

    # ─── PATCH 16: DELETED (v148 P2 cleanup) ──────────────────────────────
    # Was a tavern request-list "softlock" watchdog (cave @0x4CAA30 + counter @0x4CAAA0,
    # hook @VA 0x158F48).  PERMANENTLY OBSOLETE: that freeze was a SYMPTOM of our own R39
    # quest section-table corruption, root-fixed at the data level in
    # build/inject_r39_quest.py (block 10b).  The watchdog was NEVER installed (`if True`
    # short-circuit) AND it force-closed the menu after ~300 idle frames -- a footgun.
    # v148 DELETES all its dead constants + cave words (RC_HOOK/RC_CAVE/rc_cave_words/etc.).
    # NOTE: 0x4CAA30 (the old watchdog pad) is now wholly FREE -- Patch 24's cave evacuated
    # OUT of it to RELOC.P24_VA (0x4AFA58) in dead .text padding below the arena.
    print("\n--- Patch 16: DELETED (request freeze root-fixed in R39; dead constants removed v148) ---")

    # ─── Patch 18: DELETED (v148 P2 cleanup) ──────────────────────────────
    # Was a one-shot hub-pane rebuild (cave @0x4C7860, hook @VA 0x13CAE8) for the
    # request->hub return.  PERMANENTLY OBSOLETE: the missing hub pane was a downstream
    # symptom of the R39 quest-table freeze, root-fixed in build/inject_r39_quest.py; and
    # the hook never actually fired (the parent bit-0x40 handshake is never set on the
    # request path), so it was inert.  It was NEVER installed (`if True` short-circuit).
    # v148 DELETES all its dead constants + cave words (ON_HOOK/ON_CAVE/on_cave_words/etc.).
    # CORRECTION of the old comment: the 0x4C7860 pad is NOT "NOT runtime-written" -- it sits
    # ABOVE the arena boundary (0x4C7860 >= 0x4B0E00), i.e. INSIDE the EE battle-heap arena,
    # so the game CAN write it at runtime.  That is exactly why nothing may be cave-installed
    # there; the v148 guardrail (RELOC.assert_install_safe) now forbids any such placement.
    print("\n--- Patch 18: DELETED (request freeze root-fixed in R39; dead constants removed v148) ---")

    # ─── Write output ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    print(f"\n=== Summary: {patched_count} patches applied ===")
    print(f"Written to {dst} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
