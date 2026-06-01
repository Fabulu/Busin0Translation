import struct

SECTOR = 2048
ORIGINAL_ISO = "C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
PATCHED_ISO  = "C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v29.iso"

def read_r38(iso_path, label):
    out = []
    out.append("")
    out.append("=" * 70)
    out.append("  " + label)
    out.append("=" * 70)

    with open(iso_path, "rb") as f:
        # PVD sector 16
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        root_rec = pvd[156:156+34]
        root_lba = struct.unpack_from('<I', root_rec, 2)[0]
        root_size = struct.unpack_from('<I', root_rec, 10)[0]

        # Find PACKDATA.DIG
        f.seek(root_lba * SECTOR)
        root_data = f.read(root_size)
        packdata_lba = None
        pos = 0
        while pos < len(root_data):
            rec_len = root_data[pos]
            if rec_len == 0:
                pos = ((pos // SECTOR) + 1) * SECTOR
                if pos >= len(root_data):
                    break
                continue
            name_len = root_data[pos + 32]
            name_str = root_data[pos+33:pos+33+name_len].decode('ascii', errors='replace')
            if 'PACKDATA' in name_str.upper():
                packdata_lba = struct.unpack_from('<I', root_data, pos + 2)[0]
                out.append("PACKDATA.DIG LBA: %d" % packdata_lba)
            pos += rec_len

        if packdata_lba is None:
            out.append("ERROR: PACKDATA.DIG not found!")
            return "\n".join(out)

        # R38 TOC (LE 32-bit entries, 12 bytes each)
        toc_offset = packdata_lba * SECTOR + 38 * 12
        f.seek(toc_offset)
        toc_entry = f.read(12)
        r38_sector = struct.unpack_from('<I', toc_entry, 0)[0]
        r38_size_sectors = struct.unpack_from('<I', toc_entry, 4)[0]
        out.append("R38 sector offset: %d, size: %d sectors (%d bytes)" % (r38_sector, r38_size_sectors, r38_size_sectors * SECTOR))

        # Read R38 data
        r38_abs = (packdata_lba + r38_sector) * SECTOR
        f.seek(r38_abs)
        data = f.read(r38_size_sectors * SECTOR)
        out.append("R38 data: %d bytes total" % len(data))

        # Hex dump first 208 bytes (13 rows of 16)
        out.append("")
        out.append("--- First 208 bytes ---")
        for i in range(0, min(208, len(data)), 16):
            hx = " ".join("%02X" % data[i+j] for j in range(16) if i+j < len(data))
            asc = "".join(chr(data[i+j]) if 0x20 <= data[i+j] < 0x7F else "." for j in range(16) if i+j < len(data))
            out.append("  %04X: %-48s |%s|" % (i, hx, asc))

        # The MSG format uses BIG-ENDIAN 16-bit glyph indices
        # Find first FF FF separator (aligned to 2 bytes)
        ffff_pos = None
        for i in range(0, len(data) - 1, 2):
            if data[i] == 0xFF and data[i+1] == 0xFF:
                ffff_pos = i
                break

        if ffff_pos is None:
            out.append("No FFFF found!")
            return "\n".join(out)

        out.append("")
        out.append("First FFFF at offset 0x%X (%d)" % (ffff_pos, ffff_pos))
        out.append("Pre-FFFF region = %d bytes = offset/header table" % ffff_pos)

        # Show message content after FFFF (using BE 16-bit)
        # Find multiple messages separated by FFFF
        msg_start = ffff_pos + 2  # skip first FFFF
        out.append("")
        out.append("--- Message content (BE 16-bit glyph indices) ---")
        out.append("--- First 30 messages ---")

        pos = msg_start
        msg_count = 0
        while pos < len(data) - 1 and msg_count < 30:
            # Collect glyphs until next FFFF
            glyphs = []
            while pos < len(data) - 1:
                val = struct.unpack_from('>H', data, pos)[0]
                pos += 2
                if val == 0xFFFF:
                    break
                glyphs.append(val)

            if not glyphs:
                msg_count += 1
                continue

            # Render: try to show as characters
            rendered = []
            for g in glyphs:
                if g == 0xFFFE:
                    rendered.append("\\n")
                elif 0x0021 <= g <= 0x007E:
                    rendered.append(chr(g))
                else:
                    rendered.append("{%04X}" % g)

            text = "".join(rendered)
            is_ascii = sum(1 for g in glyphs if 0x0021 <= g <= 0x007E and g != 0xFFFE)
            is_jp = sum(1 for g in glyphs if g >= 0x0100 and g not in (0xFFFE, 0xFFFF))
            tag = "EN" if is_ascii > is_jp else "JP" if is_jp > 0 else "??"

            out.append("  msg[%d] [%s] = %s" % (msg_count, tag, text))
            msg_count += 1

        # Count all messages and classify
        out.append("")
        out.append("--- Full file statistics ---")
        pos = msg_start
        total_msgs = 0
        en_msgs = 0
        jp_msgs = 0
        while pos < len(data) - 1:
            glyphs = []
            while pos < len(data) - 1:
                val = struct.unpack_from('>H', data, pos)[0]
                pos += 2
                if val == 0xFFFF:
                    break
                glyphs.append(val)
            if not glyphs:
                total_msgs += 1
                continue
            is_ascii = sum(1 for g in glyphs if 0x0021 <= g <= 0x007E and g != 0xFFFE)
            is_jp = sum(1 for g in glyphs if g >= 0x0100 and g not in (0xFFFE, 0xFFFF))
            if is_ascii > is_jp:
                en_msgs += 1
            elif is_jp > 0:
                jp_msgs += 1
            total_msgs += 1

        out.append("  Total messages: %d" % total_msgs)
        out.append("  English: %d" % en_msgs)
        out.append("  Japanese: %d" % jp_msgs)
        out.append("  Other/empty: %d" % (total_msgs - en_msgs - jp_msgs))

    return "\n".join(out)


# Run
lines = []
lines.append("# R38 Hex Dump Comparison: Original JP vs v29 EN")
lines.append("# Date: 2026-05-28")
lines.append("# Glyph indices are BIG-ENDIAN 16-bit values")
lines.append("# ASCII-range (0x0021-0x007E) = English glyphs")
lines.append("# High range (>=0x0100) = Japanese glyphs")

lines.append(read_r38(ORIGINAL_ISO, "ORIGINAL ISO (Japanese)"))
lines.append("")
lines.append(read_r38(PATCHED_ISO, "v29 PATCHED ISO (English)"))

result = "\n".join(lines)
print(result)

outpath = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/hex_dump_r38.md"
with open(outpath, "w") as f:
    f.write("```\n")
    f.write(result)
    f.write("\n```\n")

print("\n\nWritten to hex_dump_r38.md")
