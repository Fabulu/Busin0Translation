#!/usr/bin/env python3
"""Deep check: type-2 dialogue resources in ISO vs original."""
import struct, os, hashlib, json

SECTOR = 2048
ISO_PATH = 'C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v15.iso'
ORIG_ISO = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

report = []
def log(msg):
    print(msg)
    report.append(msg)

# Load glyph table for decoding
gt = json.load(open('C:/Programmieren/wizardrytranslation/data/english_glyph_table.json', encoding='utf-8'))
glyph_rev = {v: k for k, v in gt.items()}

def decode_glyphs(glyphs):
    chars = []
    for g in glyphs:
        if g == 0xFFFE:
            chars.append(' / ')
        elif g in glyph_rev:
            chars.append(glyph_rev[g])
        elif g == 0:
            pass
        elif g >= 0xFB00:
            pass  # control
        else:
            chars.append(f'[{g}]')
    return ''.join(chars)

def get_pack_info(iso_path):
    with open(iso_path, 'rb') as iso:
        iso.seek(16 * SECTOR)
        pvd = iso.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        iso.seek(root_lba * SECTOR)
        root_dir = iso.read(root_size)
        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0: break
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
            if 'PACKDATA' in name:
                return struct.unpack_from('<I', root_dir, pos + 2)[0]
            pos += rec_len

pack_lba = get_pack_info(ISO_PATH)
opack_lba = get_pack_info(ORIG_ISO)

log("=" * 70)
log("TYPE-2 DIALOGUE RESOURCES: PATCHED vs ORIGINAL")
log("=" * 70)

# Read TOC from both ISOs
with open(ISO_PATH, 'rb') as iso, open(ORIG_ISO, 'rb') as orig:
    iso.seek(pack_lba * SECTOR)
    toc = iso.read(12 * 3000)
    orig.seek(opack_lba * SECTOR)
    otoc = orig.read(12 * 3000)

    # Count total type-2 resources and check which are patched
    n_entries = len(toc) // 12
    type2_total = 0
    type2_patched = 0
    type2_identical = 0
    type2_english = 0
    type2_japanese = 0
    type2_mixed = 0

    sample_japanese = []  # Resources that still appear Japanese

    for r_id in range(min(n_entries, 2700)):
        sec_off, sec_cnt, tc = struct.unpack_from('<III', toc, r_id * 12)
        if tc != 2 or sec_cnt == 0:
            continue
        type2_total += 1

        osec_off, osec_cnt, otc = struct.unpack_from('<III', otoc, r_id * 12)

        # Read first 2KB from both
        iso.seek(pack_lba * SECTOR + sec_off * SECTOR)
        data = iso.read(min(sec_cnt * SECTOR, 2048))

        orig.seek(opack_lba * SECTOR + osec_off * SECTOR)
        odata = orig.read(min(osec_cnt * SECTOR, 2048))

        is_patched = (data != odata)
        if is_patched:
            type2_patched += 1

        # Analyze first message
        ffff_pos = None
        for i in range(0, len(data) - 1, 2):
            v = struct.unpack_from('>H', data, i)[0]
            if v == 0xFFFF:
                ffff_pos = i
                break

        if ffff_pos and ffff_pos > 0:
            glyphs = []
            for i in range(0, ffff_pos, 2):
                g = struct.unpack_from('>H', data, i)[0]
                glyphs.append(g)
            text = [g for g in glyphs if 0 < g < 0xFB00]
            eng = sum(1 for g in text if 33 <= g <= 90)
            jpn = sum(1 for g in text if g >= 95)

            if eng > 0 and jpn == 0:
                type2_english += 1
            elif jpn > 0 and eng == 0:
                type2_japanese += 1
                if len(sample_japanese) < 10:
                    decoded = decode_glyphs(text[:30])
                    sample_japanese.append((r_id, is_patched, len(text), eng, jpn, decoded))
            elif eng > 0 and jpn > 0:
                type2_mixed += 1
        else:
            type2_identical += 1  # no FFFF found, probably empty/binary

    log(f"\nType-2 resources total:     {type2_total}")
    log(f"Patched (differ from orig): {type2_patched}")
    log(f"Identical to original:      {type2_total - type2_patched}")
    log(f"")
    log(f"First-message language:")
    log(f"  English:  {type2_english}")
    log(f"  Japanese: {type2_japanese}")
    log(f"  Mixed:    {type2_mixed}")
    log(f"  No FFFF:  {type2_identical}")

    log(f"\n--- Sample Japanese Type-2 Resources ---")
    for r_id, patched, ntext, eng, jpn, decoded in sample_japanese:
        status = "PATCHED" if patched else "UNPATCHED"
        log(f"  R{r_id} [{status}]: {ntext} text glyphs, eng={eng}, jpn={jpn}")
        log(f"    Decoded: {decoded}")

# Also check the type-1 resources
log(f"\n{'='*70}")
log("TYPE-1 RESOURCES CHECK (R34-R49)")
log(f"{'='*70}")

with open(ISO_PATH, 'rb') as iso, open(ORIG_ISO, 'rb') as orig:
    iso.seek(pack_lba * SECTOR)
    toc = iso.read(12 * 100)
    orig.seek(opack_lba * SECTOR)
    otoc = orig.read(12 * 100)

    for r_id in [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 48, 49]:
        sec_off, sec_cnt, tc = struct.unpack_from('<III', toc, r_id * 12)
        osec_off, osec_cnt, otc = struct.unpack_from('<III', otoc, r_id * 12)

        iso.seek(pack_lba * SECTOR + sec_off * SECTOR)
        data = iso.read(sec_cnt * SECTOR)
        orig.seek(opack_lba * SECTOR + osec_off * SECTOR)
        odata = orig.read(osec_cnt * SECTOR)

        patched = data != odata[:len(data)] if len(odata) >= len(data) else True

        # Count messages with FFFF
        fps = []
        for i in range(0, len(data) - 1, 2):
            v = struct.unpack_from('>H', data, i)[0]
            if v == 0xFFFF:
                fps.append(i)

        # Check language of messages 2-5
        eng_msgs = 0
        jpn_msgs = 0
        if len(fps) >= 2:
            for mi in range(1, min(10, len(fps))):
                start = fps[mi - 1] + 2
                end = fps[mi]
                glyphs = []
                for i in range(start, end, 2):
                    g = struct.unpack_from('>H', data, i)[0]
                    glyphs.append(g)
                text = [g for g in glyphs if 0 < g < 0xFB00]
                eng = sum(1 for g in text if 33 <= g <= 90)
                jpn = sum(1 for g in text if g >= 95)
                if eng > jpn:
                    eng_msgs += 1
                elif jpn > eng:
                    jpn_msgs += 1

        status = "PATCHED" if patched else "SAME"
        log(f"  R{r_id} type={tc}: {len(fps)} msgs, [{status}], eng_msgs={eng_msgs}, jpn_msgs={jpn_msgs}")

log("\n" + "=" * 70)
log("CONCLUSION")
log("=" * 70)

out_path = 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/debug_iso_verify.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("# ISO Verification Debug Report\n\n```\n")
    f.write('\n'.join(report))
    f.write("\n```\n")
print(f"\nReport written to {out_path}")
