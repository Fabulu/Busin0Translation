#!/usr/bin/env python3
"""
extract_from_iso.py -- Extract R38, R1272, and EXE directly from v15 ISO
and verify their contents (English vs Japanese).
"""
import struct, os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ISO = "C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v15.iso"
OUT = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese"
SECTOR = 2048

report = []
def log(s=""):
    print(s)
    report.append(s)

log("=" * 70)
log("  DEFINITIVE ISO EXTRACTION TEST - v15")
log("=" * 70)

# ── STEP 1: Read PVD, find root directory, find PACKDATA.DIG LBA ──
with open(ISO, "rb") as f:
    # PVD at sector 16
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_lba = struct.unpack_from("<I", pvd, 158)[0]
    root_size = struct.unpack_from("<I", pvd, 166)[0]
    log(f"\nPVD: root dir LBA={root_lba}, size={root_size}")

    # Read root directory
    f.seek(root_lba * SECTOR)
    root_dir = f.read(root_size)

    pack_lba = None
    pack_size = None
    exe_lba = None
    exe_size = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode("ascii", errors="replace")
        file_lba = struct.unpack_from("<I", root_dir, pos + 2)[0]
        file_size = struct.unpack_from("<I", root_dir, pos + 10)[0]
        log(f"  File: {name:30s}  LBA={file_lba:8d}  size={file_size:12,}")
        if "PACKDATA" in name:
            pack_lba = file_lba
            pack_size = file_size
        if "SLPM" in name:
            exe_lba = file_lba
            exe_size = file_size
        pos += rec_len

    if pack_lba is None:
        log("ERROR: PACKDATA.DIG not found!")
        sys.exit(1)

    log(f"\nPACKDATA.DIG: LBA={pack_lba}, size={pack_size:,}")

    # ── STEP 2: Read TOC from PACKDATA.DIG ──
    f.seek(pack_lba * SECTOR)
    toc_data = f.read(2883 * 12)
    toc = []
    for i in range(2883):
        so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)
        toc.append((so, sc, tc))

    # ── STEP 3: Extract R38 ──
    log("\n" + "=" * 70)
    log("  R38 EXTRACTION")
    log("=" * 70)

    r38_so, r38_sc, r38_tc = toc[38]
    r38_abs_offset = pack_lba * SECTOR + r38_so * SECTOR
    r38_byte_size = r38_sc * SECTOR
    log(f"  TOC[38]: sector_offset={r38_so}, sector_count={r38_sc}, type={r38_tc}")
    log(f"  Absolute offset in ISO: {r38_abs_offset:,} (0x{r38_abs_offset:X})")
    log(f"  Data size: {r38_byte_size:,} bytes")

    f.seek(r38_abs_offset)
    r38_raw = f.read(r38_byte_size)

    # Save raw
    r38_path = os.path.join(OUT, "r38_from_iso.bin")
    with open(r38_path, "wb") as out:
        out.write(r38_raw)
    log(f"  Saved to: {r38_path}")

    # Parse sub-header
    sub_hdr = struct.unpack_from("<IIII", r38_raw, 0)
    log(f"  Sub-header: {sub_hdr}")
    payload_size = sub_hdr[1]
    log(f"  Payload size: {payload_size:,}")

    # Find messages in the payload (after 16-byte sub-header)
    payload = r38_raw[16:16 + payload_size]
    log(f"  Payload bytes: {len(payload):,}")

    # Parse FFFF-delimited messages
    messages = []
    current = []
    for i in range(0, len(payload) - 1, 2):
        w = struct.unpack_from(">H", payload, i)[0]
        if w == 0xFFFF:
            messages.append(current)
            current = []
        else:
            current.append(w)
    if current:
        messages.append(current)

    log(f"  Total messages: {len(messages)}")

    # Reverse glyph table for decoding
    glyph_to_char = {}
    for i in range(95):
        glyph_to_char[i] = chr(i + 0x20)  # glyph 0 = space, 1 = !, etc.

    # Load full glyph map for Japanese decoding
    glyph_map_path = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
    try:
        glyph_map = json.load(open(glyph_map_path, encoding="utf-8"))
        # glyph_map is {str(glyph_id): char}
        log(f"  Loaded glyph map: {len(glyph_map)} entries")
    except:
        glyph_map = {}

    ascii_msg_count = 0
    jp_msg_count = 0
    mixed_msg_count = 0

    log(f"\n  --- First 20 messages ---")
    for mi, msg in enumerate(messages[:20]):
        if not msg:
            log(f"  MSG {mi}: (empty)")
            continue

        ascii_glyphs = [g for g in msg if g < 95]
        jp_glyphs = [g for g in msg if 95 <= g < 0xFB00]
        ctrl_codes = [g for g in msg if g >= 0xFB00]

        # Classify
        total_text = len(ascii_glyphs) + len(jp_glyphs)
        if total_text == 0:
            tag = "CTRL-ONLY"
        elif len(jp_glyphs) == 0:
            tag = "ENGLISH"
            ascii_msg_count += 1
        elif len(ascii_glyphs) == 0:
            tag = "JAPANESE"
            jp_msg_count += 1
        else:
            tag = "MIXED"
            mixed_msg_count += 1

        # Decode
        decoded = ""
        for g in msg:
            if g == 0xFFFE:
                decoded += "\\n"
            elif g >= 0xFB00:
                decoded += f"[{g:04X}]"
            elif g < 95:
                decoded += glyph_to_char.get(g, "?")
            else:
                ch = glyph_map.get(str(g), None)
                decoded += ch if ch else f"<{g}>"

        raw_ids = msg[:15]
        log(f"  MSG {mi} [{tag}]: glyphs={raw_ids}{'...' if len(msg)>15 else ''}")
        log(f"    Decoded: {decoded[:100]}{'...' if len(decoded)>100 else ''}")

    # Full statistics
    log(f"\n  --- Full R38 statistics (all {len(messages)} messages) ---")
    full_ascii = 0
    full_jp = 0
    full_mixed = 0
    full_ctrl = 0
    for msg in messages:
        if not msg:
            continue
        ascii_g = sum(1 for g in msg if g < 95)
        jp_g = sum(1 for g in msg if 95 <= g < 0xFB00)
        total = ascii_g + jp_g
        if total == 0:
            full_ctrl += 1
        elif jp_g == 0:
            full_ascii += 1
        elif ascii_g == 0:
            full_jp += 1
        else:
            full_mixed += 1

    log(f"  ENGLISH-only messages: {full_ascii}")
    log(f"  JAPANESE-only messages: {full_jp}")
    log(f"  MIXED messages: {full_mixed}")
    log(f"  CTRL-only messages: {full_ctrl}")
    log(f"  VERDICT: {'ENGLISH' if full_ascii > full_jp else 'JAPANESE'} dominates R38")

    # ── STEP 4: Extract R1272 (font atlas) ──
    log("\n" + "=" * 70)
    log("  R1272 EXTRACTION (Font Atlas)")
    log("=" * 70)

    r1272_so, r1272_sc, r1272_tc = toc[1272]
    r1272_abs = pack_lba * SECTOR + r1272_so * SECTOR
    r1272_size = r1272_sc * SECTOR
    log(f"  TOC[1272]: sector_offset={r1272_so}, sector_count={r1272_sc}, type={r1272_tc}")
    log(f"  Data size: {r1272_size:,} bytes")

    f.seek(r1272_abs)
    r1272_raw = f.read(r1272_size)

    r1272_path = os.path.join(OUT, "r1272_from_iso.bin")
    with open(r1272_path, "wb") as out:
        out.write(r1272_raw)
    log(f"  Saved to: {r1272_path}")

    # Sub-header
    sub1272 = struct.unpack_from("<IIII", r1272_raw, 0)
    log(f"  Sub-header: {sub1272}")
    payload1272 = r1272_raw[16:16 + sub1272[1]]
    log(f"  Payload size: {len(payload1272):,}")

    # Check for English letter bitmaps
    # The font atlas is PSMT4 (4-bit indexed color), 256x512
    # Each glyph cell is 21x42 pixels, packed at 4bpp = 21*42/2 = 441 bytes
    # But the atlas is stored as a linear framebuffer: 256 wide at 4bpp = 128 bytes/row
    # Grid: 256/21 = 12 cols, 512/42 = 12 rows = 144 cells (but actually uses ~882)
    # Actually the atlas is bigger. Let's just check if the payload looks like our patched font.

    # Compare with our built font atlas
    built_font = "C:/Programmieren/wizardrytranslation/build/english_font_atlas.bin"
    if os.path.exists(built_font):
        built_data = open(built_font, "rb").read()
        log(f"  Built font atlas size: {len(built_data):,}")
        log(f"  ISO R1272 payload size: {len(payload1272):,}")

        if payload1272[:100] == built_data[:100]:
            log(f"  MATCH: First 100 bytes identical - English font IS present")
        else:
            log(f"  MISMATCH: First 100 bytes differ")
            log(f"    ISO:   {payload1272[:32].hex()}")
            log(f"    Built: {built_data[:32].hex()}")

        # Check a known English letter region - glyph 33 = 'A'
        # In the atlas, glyph 33 should have non-zero pixel data
        # Let's check if the bitmaps are the same
        match_bytes = sum(1 for a, b in zip(payload1272, built_data) if a == b)
        total_cmp = min(len(payload1272), len(built_data))
        pct = match_bytes / total_cmp * 100 if total_cmp > 0 else 0
        log(f"  Byte match: {match_bytes:,} / {total_cmp:,} = {pct:.1f}%")

        if pct > 95:
            log(f"  VERDICT: English font atlas IS in the ISO")
        elif pct > 50:
            log(f"  VERDICT: Partially matching font atlas")
        else:
            log(f"  VERDICT: Font atlas does NOT match English version")
    else:
        log(f"  No built font atlas found for comparison")

    # Also check: are there non-zero pixels in the ASCII glyph region?
    # Glyphs 0-94 are in the first ~95 cells
    # Row-major in a 256-wide 4bpp buffer
    # Let's just check if early bytes are non-zero (would indicate bitmaps present)
    nonzero_early = sum(1 for b in payload1272[:4096] if b != 0)
    log(f"  Non-zero bytes in first 4096: {nonzero_early}")
    if nonzero_early > 100:
        log(f"  Font atlas has bitmap data in ASCII glyph region")

    # ── STEP 5: Extract EXE and check save slot patches ──
    log("\n" + "=" * 70)
    log("  EXE EXTRACTION (SLPM_653.78)")
    log("=" * 70)

    if exe_lba is None:
        log("  ERROR: EXE not found in root directory!")
    else:
        f.seek(exe_lba * SECTOR)
        exe_raw = f.read(exe_size)
        log(f"  EXE size: {len(exe_raw):,} bytes")

        exe_path = os.path.join(OUT, "exe_from_iso.bin")
        with open(exe_path, "wb") as out:
            out.write(exe_raw)
        log(f"  Saved to: {exe_path}")

        # Check save slot patches
        save_patches = [
            (0x3FC720, "BUSIN 0"),
            (0x3FC750, "BUSIN 0 Data 1"),
            (0x3FC770, "BUSIN 0 Data 2"),
            (0x3FC790, "BUSIN 0 Data 3"),
            (0x3F9370, "BUSIN 0 Suspend"),
        ]

        log(f"\n  --- Save Slot Name Patches ---")
        all_patched = True
        for offset, expected in save_patches:
            if offset + len(expected) > len(exe_raw):
                log(f"  OFFSET 0x{offset:X}: OUT OF RANGE")
                all_patched = False
                continue
            actual = exe_raw[offset:offset + len(expected)]
            actual_str = actual.decode("ascii", errors="replace")
            match = actual == expected.encode("ascii")
            log(f"  0x{offset:X}: expected={expected!r:25s} actual={actual_str!r:25s} {'OK' if match else 'MISMATCH'}")
            if not match:
                all_patched = False
                # Show hex
                log(f"    Hex: {exe_raw[offset:offset+32].hex()}")

        if all_patched:
            log(f"  VERDICT: Save slot patches ARE present in EXE")
        else:
            log(f"  VERDICT: Save slot patches are NOT fully applied")

        # Also check: look for Japanese SJIS save slot strings
        sjis_busin = bytes.fromhex("8261827482728268826d824f")  # fullwidth BUSIN 0
        found_sjis = exe_raw.find(sjis_busin)
        if found_sjis >= 0:
            log(f"  WARNING: Original Japanese SJIS 'BUSIN 0' still found at offset 0x{found_sjis:X}")
        else:
            log(f"  Original Japanese SJIS save strings: NOT found (good, patched out)")

log("\n" + "=" * 70)
log("  SUMMARY")
log("=" * 70)
log(f"  R38: {'ENGLISH' if full_ascii > full_jp else 'JAPANESE'} ({full_ascii} EN, {full_jp} JP, {full_mixed} mixed)")
log(f"  R1272: Font atlas extracted and compared")
log(f"  EXE: Save slot patches checked")
log("=" * 70)

# Write report
report_path = os.path.join(OUT, "debug_iso_extract.md")
with open(report_path, "w", encoding="utf-8") as rpt:
    rpt.write("# Definitive ISO Extraction Test - v15\n\n")
    rpt.write("**Date:** 2026-05-28\n")
    rpt.write(f"**ISO:** `{ISO}`\n\n")
    rpt.write("```\n")
    for line in report:
        rpt.write(line + "\n")
    rpt.write("```\n")

print(f"\nReport written to: {report_path}")
