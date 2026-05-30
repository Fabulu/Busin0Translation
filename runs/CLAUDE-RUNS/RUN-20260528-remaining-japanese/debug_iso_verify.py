#!/usr/bin/env python3
"""Verify ISO contents: check that PACKDATA, EXE, and translations are actually present."""
import struct, os, hashlib

SECTOR = 2048
ISO_PATH = 'C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v15.iso'
PACKDATA_V3 = 'C:/Programmieren/wizardrytranslation/build/PACKDATA_v3.DIG'
ORIG_ISO = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
V9_ISO = 'C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v9.iso'

report = []
def log(msg):
    print(msg)
    report.append(msg)

log("=" * 70)
log("ISO VERIFICATION REPORT")
log("=" * 70)

# === Check file sizes and timestamps ===
log("\n--- File Info ---")
for path, label in [(ISO_PATH, "v15 ISO"), (V9_ISO, "v9 ISO"), (ORIG_ISO, "Original ISO"), (PACKDATA_V3, "PACKDATA_v3.DIG")]:
    if os.path.exists(path):
        st = os.stat(path)
        log(f"  {label}: {st.st_size:,} bytes, mtime={st.st_mtime:.0f}")
    else:
        log(f"  {label}: NOT FOUND")

# === Check if v9 and v15 are identical ===
log("\n--- v9 vs v15 comparison ---")
if os.path.exists(V9_ISO) and os.path.exists(ISO_PATH):
    # Quick check: compare first 1MB + PACKDATA region
    with open(V9_ISO, 'rb') as f1, open(ISO_PATH, 'rb') as f2:
        h1 = hashlib.md5(f1.read(1024*1024)).hexdigest()
        h2 = hashlib.md5(f2.read(1024*1024)).hexdigest()
        log(f"  First 1MB MD5: v9={h1}, v15={h2}, match={h1==h2}")
        # Check sizes
        f1.seek(0, 2); f2.seek(0, 2)
        log(f"  File sizes: v9={f1.tell():,}, v15={f2.tell():,}, match={f1.tell()==f2.tell()}")

# === Parse ISO directory ===
log("\n--- ISO Directory Structure ---")
with open(ISO_PATH, 'rb') as iso:
    # Read PVD
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    vol_id = pvd[40:72].decode('ascii', errors='replace').strip()
    log(f"  Volume ID: '{vol_id}'")

    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    log(f"  Root dir: LBA={root_lba}, size={root_size}")

    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)

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
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        flags = root_dir[pos + 25]
        if name_len > 1:  # skip . and ..
            log(f"  File: '{name}' LBA={file_lba} size={file_size:,} flags={flags:#x}")

        if 'PACKDATA' in name:
            pack_lba = file_lba
            pack_size = file_size
        if 'SLPM' in name:
            exe_lba = file_lba
            exe_size = file_size
        pos += rec_len

# === Check PACKDATA size match ===
log("\n--- PACKDATA Size Check ---")
if pack_size is not None:
    v3_size = os.path.getsize(PACKDATA_V3) if os.path.exists(PACKDATA_V3) else 0
    log(f"  ISO PACKDATA size:  {pack_size:,}")
    log(f"  PACKDATA_v3 size:   {v3_size:,}")
    log(f"  Match: {pack_size == v3_size}")
    if pack_size != v3_size:
        log(f"  *** MISMATCH! ISO has different PACKDATA size than built file! ***")
        # Check original ISO PACKDATA size
        if os.path.exists(ORIG_ISO):
            with open(ORIG_ISO, 'rb') as orig:
                orig.seek(16 * SECTOR)
                opvd = orig.read(SECTOR)
                oroot_lba = struct.unpack_from('<I', opvd, 158)[0]
                oroot_size = struct.unpack_from('<I', opvd, 166)[0]
                orig.seek(oroot_lba * SECTOR)
                oroot = orig.read(oroot_size)
                opos = 0
                while opos < len(oroot):
                    orl = oroot[opos]
                    if orl == 0: break
                    onl = oroot[opos + 32]
                    oname = oroot[opos + 33:opos + 33 + onl].decode('ascii', errors='replace')
                    if 'PACKDATA' in oname:
                        orig_pack_size = struct.unpack_from('<I', oroot, opos + 10)[0]
                        log(f"  Original ISO PACKDATA size: {orig_pack_size:,}")
                        log(f"  ISO matches original? {pack_size == orig_pack_size}")
                        break
                    opos += orl

# === Read R38 from ISO's PACKDATA to check for English text ===
log("\n--- R38 (Main Dialogue) Content Check ---")
if pack_lba is not None:
    with open(ISO_PATH, 'rb') as iso:
        # TOC is at the start of PACKDATA
        # Each TOC entry is 12 bytes: offset(4) + size(4) + type(4)
        iso.seek(pack_lba * SECTOR)
        toc_entry_38 = iso.read(12 * 100)  # read enough TOC entries

        # R38 is entry index 38
        r38_off = struct.unpack_from('<I', toc_entry_38, 38 * 12)[0]
        r38_size = struct.unpack_from('<I', toc_entry_38, 38 * 12 + 4)[0]
        r38_type = struct.unpack_from('<I', toc_entry_38, 38 * 12 + 8)[0]
        log(f"  R38 TOC: offset={r38_off:#x}, size={r38_size:,}, type={r38_type}")

        # Read first 200 bytes of R38
        iso.seek(pack_lba * SECTOR + r38_off)
        r38_data = iso.read(min(r38_size, 2000))

        # Find first few FFFF-delimited messages
        ffff_positions = []
        for i in range(0, len(r38_data) - 1, 2):
            val = struct.unpack_from('>H', r38_data, i)[0]
            if val == 0xFFFF:
                ffff_positions.append(i)
            if len(ffff_positions) >= 5:
                break

        log(f"  First 5 FFFF positions: {ffff_positions}")

        # Analyze glyphs in first message (after any control codes)
        if len(ffff_positions) >= 2:
            msg_start = 0
            msg_end = ffff_positions[0]
            glyphs = []
            for i in range(msg_start, msg_end, 2):
                g = struct.unpack_from('>H', r38_data, i)[0]
                glyphs.append(g)

            # Filter out control codes (0xFB00+ range)
            text_glyphs = [g for g in glyphs if g < 0xFB00]

            english_count = sum(1 for g in text_glyphs if 33 <= g <= 90)
            japanese_count = sum(1 for g in text_glyphs if g >= 95)
            zero_count = sum(1 for g in text_glyphs if g == 0)

            log(f"  First message: {len(glyphs)} glyphs total, {len(text_glyphs)} text glyphs")
            log(f"  English-range (33-90): {english_count}")
            log(f"  Japanese-range (95+):  {japanese_count}")
            log(f"  Zeros (padding):       {zero_count}")

            if english_count > japanese_count and english_count > 0:
                log(f"  ==> ENGLISH text detected in R38!")
            elif japanese_count > english_count:
                log(f"  ==> JAPANESE text detected in R38 -- PACKDATA NOT PATCHED!")
            else:
                log(f"  ==> Inconclusive (might be padding/empty)")

            # Show raw glyph values
            log(f"  First msg raw glyphs: {glyphs[:30]}")

        # Check messages 2-4
        for mi in range(1, min(4, len(ffff_positions))):
            start = ffff_positions[mi - 1] + 2
            end = ffff_positions[mi]
            glyphs = []
            for i in range(start, end, 2):
                g = struct.unpack_from('>H', r38_data, i)[0]
                glyphs.append(g)
            text_glyphs = [g for g in glyphs if g < 0xFB00]
            eng = sum(1 for g in text_glyphs if 33 <= g <= 90)
            jpn = sum(1 for g in text_glyphs if g >= 95)
            lang = "EN" if eng > jpn else "JP" if jpn > eng else "??"
            log(f"  Msg {mi+1}: {len(text_glyphs)} glyphs, eng={eng} jpn={jpn} => {lang}")

# === Check EXE for patches ===
log("\n--- EXE Patch Check ---")
if exe_lba is not None:
    with open(ISO_PATH, 'rb') as iso:
        iso.seek(exe_lba * SECTOR)
        exe_data = iso.read(exe_size)
        log(f"  EXE size in ISO: {len(exe_data):,}")

        # Check save slot names at 0x3FC720
        # EXE loads at 0x100000, file offset = vaddr - 0x100000 + header
        # Actually let's just search for known English strings
        # Search for "Save" text as ASCII
        save_pos = exe_data.find(b'Save')
        if save_pos >= 0:
            log(f"  Found 'Save' at EXE offset {save_pos:#x}")
            log(f"  Context: {exe_data[save_pos:save_pos+20]}")
        else:
            log(f"  'Save' NOT found in EXE")

        # Check if patched EXE file exists and compare
        patched_exe = 'C:/Programmieren/wizardrytranslation/build/SLPM_653.78_patched'
        if os.path.exists(patched_exe):
            patched_data = open(patched_exe, 'rb').read()
            log(f"  Patched EXE file size: {len(patched_data):,}")
            # Compare first 1KB
            match_start = exe_data[:1024] == patched_data[:1024]
            # Compare at 0x3FC720 region (file offset approximation)
            log(f"  First 1KB match: {match_start}")
            # MD5
            h_iso = hashlib.md5(exe_data).hexdigest()
            h_pat = hashlib.md5(patched_data).hexdigest()
            log(f"  ISO EXE MD5:     {h_iso}")
            log(f"  Patched EXE MD5: {h_pat}")
            log(f"  EXE match: {h_iso == h_pat}")

# === Compare ISO's PACKDATA content with built PACKDATA ===
log("\n--- PACKDATA Binary Comparison ---")
if pack_lba is not None and os.path.exists(PACKDATA_V3):
    with open(ISO_PATH, 'rb') as iso, open(PACKDATA_V3, 'rb') as v3:
        # Compare first 64KB (TOC region)
        iso.seek(pack_lba * SECTOR)
        iso_toc = iso.read(65536)
        v3_toc = v3.read(65536)
        if iso_toc == v3_toc:
            log(f"  First 64KB (TOC): MATCH")
        else:
            diffs = sum(1 for a, b in zip(iso_toc, v3_toc) if a != b)
            log(f"  First 64KB (TOC): {diffs} differing bytes!")

        # Compare R38 region
        r38_off_v = struct.unpack_from('<I', v3_toc, 38 * 12)[0]
        iso.seek(pack_lba * SECTOR + r38_off)
        v3.seek(r38_off_v)
        iso_r38 = iso.read(4096)
        v3_r38 = v3.read(4096)
        if iso_r38 == v3_r38:
            log(f"  R38 first 4KB: MATCH")
        else:
            diffs = sum(1 for a, b in zip(iso_r38, v3_r38) if a != b)
            log(f"  R38 first 4KB: {diffs} differing bytes!")

        # Overall hash comparison
        iso.seek(pack_lba * SECTOR)
        iso_all = iso.read(pack_size if pack_size else v3.seek(0,2))
        v3.seek(0)
        v3_all = v3.read()
        h_iso = hashlib.md5(iso_all).hexdigest()
        h_v3 = hashlib.md5(v3_all).hexdigest()
        log(f"  ISO PACKDATA MD5: {h_iso}")
        log(f"  V3 file MD5:      {h_v3}")
        log(f"  Full PACKDATA match: {h_iso == h_v3}")

# === Also check original ISO for comparison ===
log("\n--- Original ISO PACKDATA R38 Check ---")
if os.path.exists(ORIG_ISO):
    with open(ORIG_ISO, 'rb') as orig:
        orig.seek(16 * SECTOR)
        opvd = orig.read(SECTOR)
        oroot_lba = struct.unpack_from('<I', opvd, 158)[0]
        oroot_size = struct.unpack_from('<I', opvd, 166)[0]
        orig.seek(oroot_lba * SECTOR)
        oroot = orig.read(oroot_size)
        opos = 0
        opack_lba = None
        while opos < len(oroot):
            orl = oroot[opos]
            if orl == 0: break
            onl = oroot[opos + 32]
            oname = oroot[opos + 33:opos + 33 + onl].decode('ascii', errors='replace')
            if 'PACKDATA' in oname:
                opack_lba = struct.unpack_from('<I', oroot, opos + 2)[0]
                break
            opos += orl

        if opack_lba:
            orig.seek(opack_lba * SECTOR)
            otoc = orig.read(12 * 50)
            or38_off = struct.unpack_from('<I', otoc, 38 * 12)[0]
            orig.seek(opack_lba * SECTOR + or38_off)
            or38 = orig.read(200)
            oglyphs = []
            for i in range(0, len(or38) - 1, 2):
                g = struct.unpack_from('>H', or38, i)[0]
                if g == 0xFFFF:
                    break
                oglyphs.append(g)
            text_g = [g for g in oglyphs if g < 0xFB00]
            eng = sum(1 for g in text_g if 33 <= g <= 90)
            jpn = sum(1 for g in text_g if g >= 95)
            log(f"  Original R38 msg1: {len(text_g)} glyphs, eng={eng}, jpn={jpn}")
            log(f"  Original glyphs: {oglyphs[:20]}")

# === Summary ===
log("\n" + "=" * 70)
log("SUMMARY")
log("=" * 70)

# Write report
out_path = 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/debug_iso_verify.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("# ISO Verification Debug Report\n\n```\n")
    f.write('\n'.join(report))
    f.write("\n```\n")
print(f"\nReport written to {out_path}")
