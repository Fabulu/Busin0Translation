#!/usr/bin/env python3
"""Verify ISO contents v2: correct TOC parsing (sector-based offsets)."""
import struct, os, hashlib

SECTOR = 2048
ISO_PATH = 'C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v15.iso'
PACKDATA_V3 = 'C:/Programmieren/wizardrytranslation/build/PACKDATA_v3.DIG'
ORIG_ISO = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

report = []
def log(msg):
    print(msg)
    report.append(msg)

log("=" * 70)
log("ISO VERIFICATION REPORT v2")
log("=" * 70)

# Find PACKDATA in ISO
with open(ISO_PATH, 'rb') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)

    pack_lba = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0: break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'PACKDATA' in name:
            pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            pack_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
            log(f"PACKDATA: LBA={pack_lba}, size={pack_size:,}")
        pos += rec_len

log(f"\n--- TOC Entries (sector_offset, sector_count, type_code) ---")

# Read TOC from ISO PACKDATA
with open(ISO_PATH, 'rb') as iso:
    pack_byte_offset = pack_lba * SECTOR
    iso.seek(pack_byte_offset)
    # TOC: each entry is 12 bytes (<III)
    # Read enough for ~50 entries
    toc_raw = iso.read(12 * 100)

    for r_id in [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 48, 49]:
        sec_off, sec_cnt, tc = struct.unpack_from('<III', toc_raw, r_id * 12)
        byte_off = sec_off * SECTOR
        log(f"  R{r_id}: sector_off={sec_off}, sectors={sec_cnt}, type={tc}, byte_off={byte_off:#x}")

    # Now read R38 properly
    log(f"\n--- R38 Content Analysis ---")
    r38_sec_off, r38_sec_cnt, r38_tc = struct.unpack_from('<III', toc_raw, 38 * 12)
    r38_byte_off = r38_sec_off * SECTOR
    r38_byte_size = r38_sec_cnt * SECTOR

    iso.seek(pack_byte_offset + r38_byte_off)
    r38_data = iso.read(min(r38_byte_size, 8192))

    log(f"  R38: type={r38_tc}, {r38_sec_cnt} sectors = {r38_byte_size:,} bytes")
    log(f"  First 40 bytes (hex): {r38_data[:40].hex()}")

    # Find FFFF delimiters
    ffff_positions = []
    for i in range(0, len(r38_data) - 1, 2):
        val = struct.unpack_from('>H', r38_data, i)[0]
        if val == 0xFFFF:
            ffff_positions.append(i)
        if len(ffff_positions) >= 10:
            break

    log(f"  FFFF positions (first 10): {ffff_positions}")

    if ffff_positions:
        # Analyze first few messages
        boundaries = [0] + [p + 2 for p in ffff_positions]
        for mi in range(min(5, len(ffff_positions))):
            start = boundaries[mi]
            end = ffff_positions[mi]
            glyphs = []
            for i in range(start, end, 2):
                g = struct.unpack_from('>H', r38_data, i)[0]
                glyphs.append(g)

            ctrl = [g for g in glyphs if g >= 0xFB00]
            text = [g for g in glyphs if g < 0xFB00 and g > 0]
            eng = sum(1 for g in text if 33 <= g <= 90)
            jpn = sum(1 for g in text if g >= 95)

            log(f"  Msg {mi+1}: {len(glyphs)} glyphs, ctrl={len(ctrl)}, text={len(text)}, eng={eng}, jpn={jpn}")
            log(f"    Raw: {glyphs[:25]}")

            # Try to decode English glyphs
            chars = []
            glyph_table_rev = {}
            try:
                import json
                gt = json.load(open('C:/Programmieren/wizardrytranslation/data/english_glyph_table.json', encoding='utf-8'))
                glyph_table_rev = {v: k for k, v in gt.items()}
            except:
                pass

            for g in text:
                if g in glyph_table_rev:
                    chars.append(glyph_table_rev[g])
                else:
                    chars.append(f'[{g}]')
            if chars:
                log(f"    Decoded: {''.join(chars[:50])}")
    else:
        log(f"  NO FFFF delimiters found in first {len(r38_data)} bytes!")
        log(f"  This means R38 data may be wrong type or at wrong offset")

        # Show some raw values
        raw_vals = []
        for i in range(0, min(60, len(r38_data)), 2):
            raw_vals.append(struct.unpack_from('>H', r38_data, i)[0])
        log(f"  Raw big-endian values: {raw_vals}")
        raw_vals_le = []
        for i in range(0, min(60, len(r38_data)), 2):
            raw_vals_le.append(struct.unpack_from('<H', r38_data, i)[0])
        log(f"  Raw little-endian values: {raw_vals_le}")

    # Also check a type-2 resource (dialogue)
    log(f"\n--- Type-2 Resource Check (picking one with translations) ---")
    # Find first type-2 resource
    for r_id in range(50, 200):
        sec_off, sec_cnt, tc = struct.unpack_from('<III', toc_raw, r_id * 12)
        if tc == 2 and sec_cnt > 0:
            log(f"  Checking R{r_id} (type={tc}, sectors={sec_cnt})")
            iso.seek(pack_byte_offset + sec_off * SECTOR)
            rdata = iso.read(min(sec_cnt * SECTOR, 4096))

            # Find FFFF delimiters
            fps = []
            for i in range(0, len(rdata) - 1, 2):
                v = struct.unpack_from('>H', rdata, i)[0]
                if v == 0xFFFF:
                    fps.append(i)
                if len(fps) >= 5:
                    break

            if fps:
                # Check first message
                glyphs = []
                for i in range(0, fps[0], 2):
                    g = struct.unpack_from('>H', rdata, i)[0]
                    glyphs.append(g)
                text = [g for g in glyphs if 0 < g < 0xFB00]
                eng = sum(1 for g in text if 33 <= g <= 90)
                jpn = sum(1 for g in text if g >= 95)
                lang = "ENGLISH" if eng > jpn else "JAPANESE" if jpn > eng else "UNKNOWN"
                log(f"    First msg: {len(text)} text glyphs, eng={eng}, jpn={jpn} => {lang}")

                # Decode
                chars = []
                for g in text:
                    if g in glyph_table_rev:
                        chars.append(glyph_table_rev[g])
                    else:
                        chars.append(f'[{g}]')
                log(f"    Decoded: {''.join(chars[:60])}")

            break  # just check one

# === Compare with original ISO ===
log(f"\n--- Original ISO Same Resources ---")
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
        otoc = orig.read(12 * 100)

        r38_sec_off_o, r38_sec_cnt_o, r38_tc_o = struct.unpack_from('<III', otoc, 38 * 12)
        log(f"  Original R38: sector_off={r38_sec_off_o}, sectors={r38_sec_cnt_o}, type={r38_tc_o}")

        orig.seek(opack_lba * SECTOR + r38_sec_off_o * SECTOR)
        or38 = orig.read(200)
        oglyphs = []
        for i in range(0, len(or38) - 1, 2):
            g = struct.unpack_from('>H', or38, i)[0]
            oglyphs.append(g)
            if g == 0xFFFF:
                break
        log(f"  Original R38 first msg glyphs: {oglyphs[:25]}")

        # Compare TOC entries
        log(f"\n  TOC comparison (R38):")
        log(f"    Original: off={r38_sec_off_o}, cnt={r38_sec_cnt_o}, type={r38_tc_o}")
        log(f"    Patched:  off={r38_sec_off}, cnt={r38_sec_cnt}, type={r38_tc}")

        if r38_sec_off_o == r38_sec_off and r38_sec_cnt_o == r38_sec_cnt:
            log(f"    => TOC IDENTICAL -- checking if data actually differs")
            orig.seek(opack_lba * SECTOR + r38_sec_off_o * SECTOR)
            with open(ISO_PATH, 'rb') as iso2:
                iso2.seek(pack_lba * SECTOR + r38_sec_off * SECTOR)
                od = orig.read(r38_sec_cnt_o * SECTOR)
                pd = iso2.read(r38_sec_cnt * SECTOR)
                if od == pd:
                    log(f"    => DATA IDENTICAL -- R38 NOT PATCHED!")
                else:
                    diffs = sum(1 for a, b in zip(od, pd) if a != b)
                    log(f"    => DATA DIFFERS: {diffs} byte differences -- R38 IS PATCHED")

log("\n" + "=" * 70)

out_path = 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/debug_iso_verify.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("# ISO Verification Debug Report\n\n```\n")
    f.write('\n'.join(report))
    f.write("\n```\n")
print(f"\nReport written to {out_path}")
