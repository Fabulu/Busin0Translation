import struct, sys

SECTOR = 2048
ORIGINAL_ISO = "C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
PATCHED_ISO  = "C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v29.iso"

def read_r38(iso_path, label):
    results = []
    results.append("")
    results.append("=" * 70)
    results.append("  " + label)
    results.append("  " + iso_path)
    results.append("=" * 70)

    with open(iso_path, "rb") as f:
        # Read PVD at sector 16
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        results.append("PVD type code: %d" % pvd[0])

        # Root directory record from PVD offset 156
        root_rec = pvd[156:156+34]
        root_lba = struct.unpack_from('<I', root_rec, 2)[0]
        root_size = struct.unpack_from('<I', root_rec, 10)[0]
        results.append("Root dir LBA: %d, size: %d" % (root_lba, root_size))

        # Read root directory to find PACKDATA.DIG
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
            name = root_data[pos+33:pos+33+name_len]
            try:
                name_str = name.decode('ascii', errors='replace')
            except:
                name_str = repr(name)

            if 'PACKDATA' in name_str.upper():
                lba = struct.unpack_from('<I', root_data, pos + 2)[0]
                size = struct.unpack_from('<I', root_data, pos + 10)[0]
                results.append("Found: %s at LBA %d, size %d" % (name_str, lba, size))
                packdata_lba = lba

            pos += rec_len

        if packdata_lba is None:
            results.append("ERROR: PACKDATA.DIG not found!")
            return "\n".join(results)

        # Read R38 TOC entry (12 bytes each)
        toc_offset = packdata_lba * SECTOR + 38 * 12
        f.seek(toc_offset)
        toc_entry = f.read(12)
        r38_sector = struct.unpack_from('<I', toc_entry, 0)[0]
        r38_size_sectors = struct.unpack_from('<I', toc_entry, 4)[0]
        r38_flags = struct.unpack_from('<I', toc_entry, 8)[0]

        results.append("")
        results.append("R38 TOC entry:")
        results.append("  Sector offset: %d" % r38_sector)
        results.append("  Size (sectors): %d" % r38_size_sectors)
        results.append("  Flags/extra:    0x%08X" % r38_flags)
        results.append("  Data size:      %d bytes" % (r38_size_sectors * SECTOR))

        # Read R38 data
        r38_abs_offset = (packdata_lba + r38_sector) * SECTOR
        f.seek(r38_abs_offset)
        r38_data = f.read(min(r38_size_sectors * SECTOR, 4096))

        results.append("")
        results.append("R38 absolute offset: 0x%X (sector %d)" % (r38_abs_offset, packdata_lba + r38_sector))
        results.append("R38 data read: %d bytes" % len(r38_data))

        # Hex dump first 200 bytes
        results.append("")
        results.append("--- First 200 bytes hex dump ---")
        for i in range(0, min(200, len(r38_data)), 16):
            hex_part = " ".join("%02X" % r38_data[i+j] if i+j < len(r38_data) else "  " for j in range(16))
            ascii_part = "".join(
                chr(r38_data[i+j]) if 0x20 <= r38_data[i+j] < 0x7F else "."
                for j in range(16) if i+j < len(r38_data)
            )
            results.append("  %04X: %s  |%s|" % (i, hex_part, ascii_part))

        # Find first FFFF
        ffff_pos = None
        for i in range(0, len(r38_data) - 1, 2):
            if r38_data[i] == 0xFF and r38_data[i+1] == 0xFF:
                ffff_pos = i
                break

        is_increasing = False
        vals_16 = []

        if ffff_pos is not None:
            results.append("")
            results.append("First FFFF found at offset 0x%X (%d)" % (ffff_pos, ffff_pos))

            # Bytes BEFORE FFFF
            before = r38_data[:ffff_pos]
            results.append("")
            results.append("--- Bytes BEFORE first FFFF (%d bytes) ---" % len(before))
            if len(before) >= 4:
                results.append("  As 16-bit LE values:")
                for i in range(0, min(40, len(before)), 2):
                    if i+1 < len(before):
                        val = struct.unpack_from('<H', before, i)[0]
                        results.append("    [%d] = 0x%04X (%d)" % (i//2, val, val))

            for i in range(0, len(before)-1, 2):
                vals_16.append(struct.unpack_from('<H', before, i)[0])

            if vals_16:
                is_increasing = all(vals_16[i] <= vals_16[i+1] for i in range(len(vals_16)-1))
                ascii_range = sum(1 for v in vals_16 if 0x0020 <= v <= 0x007F)
                jp_range = sum(1 for v in vals_16 if v >= 0x0100)

                results.append("")
                results.append("  Analysis of pre-FFFF 16-bit values:")
                results.append("    Count: %d" % len(vals_16))
                results.append("    Monotonically increasing: %s" % is_increasing)
                results.append("    In ASCII range (0x20-0x7F): %d/%d" % (ascii_range, len(vals_16)))
                results.append("    In JP/high range (>=0x100): %d/%d" % (jp_range, len(vals_16)))
                results.append("    Min: 0x%04X, Max: 0x%04X" % (min(vals_16), max(vals_16)))

            # Bytes AFTER FFFF
            after_start = ffff_pos + 2
            after = r38_data[after_start:after_start+100]
            results.append("")
            results.append("--- First 100 bytes AFTER FFFF (message content) ---")
            for i in range(0, min(100, len(after)), 16):
                hex_part = " ".join("%02X" % after[i+j] if i+j < len(after) else "  " for j in range(16))
                ascii_part = "".join(
                    chr(after[i+j]) if 0x20 <= after[i+j] < 0x7F else "."
                    for j in range(16) if i+j < len(after)
                )
                results.append("  %04X: %s  |%s|" % (i, hex_part, ascii_part))

            # Glyph index interpretation
            results.append("")
            results.append("  Content as 16-bit LE glyph indices:")
            for i in range(0, min(60, len(after)), 2):
                if i+1 < len(after):
                    val = struct.unpack_from('<H', after, i)[0]
                    if val == 0xFFFF:
                        results.append("    [%d] = 0xFFFF (separator)" % (i//2))
                    elif val == 0xFFFE:
                        results.append("    [%d] = 0xFFFE (newline)" % (i//2))
                    elif 0x0020 <= val <= 0x007E:
                        results.append("    [%d] = 0x%04X = ASCII '%s'" % (i//2, val, chr(val)))
                    elif val < 0x0100:
                        results.append("    [%d] = 0x%04X (low glyph index)" % (i//2, val))
                    else:
                        results.append("    [%d] = 0x%04X (high/JP glyph index)" % (i//2, val))
        else:
            results.append("")
            results.append("No FFFF separator found in first 4KB!")

        # Verdict
        results.append("")
        results.append("--- VERDICT ---")
        if ffff_pos is not None and vals_16:
            if is_increasing and max(vals_16) > 0x100:
                results.append("  Pre-FFFF: OFFSET TABLE (monotonically increasing values)")
            elif sum(1 for v in vals_16 if 0x0020 <= v <= 0x007F) > len(vals_16) * 0.5:
                results.append("  Pre-FFFF: Likely ENGLISH glyph indices (ASCII-range values)")
            elif sum(1 for v in vals_16 if v >= 0x0100) > len(vals_16) * 0.5:
                results.append("  Pre-FFFF: Likely JAPANESE glyph indices (high values)")
            else:
                results.append("  Pre-FFFF: MIXED or OFFSET table")

            after_start2 = ffff_pos + 2
            after2 = r38_data[after_start2:after_start2+100]
            after_vals = []
            for i in range(0, min(60, len(after2))-1, 2):
                v = struct.unpack_from('<H', after2, i)[0]
                if v not in (0xFFFF, 0xFFFE):
                    after_vals.append(v)
            if after_vals:
                ascii_count = sum(1 for v in after_vals if 0x0020 <= v <= 0x007E)
                high_count = sum(1 for v in after_vals if v >= 0x0100)
                results.append("  Post-FFFF content: %d/%d ASCII-range, %d/%d high/JP-range" % (ascii_count, len(after_vals), high_count, len(after_vals)))
                if ascii_count > len(after_vals) * 0.5:
                    results.append("  ==> ENGLISH text detected")
                elif high_count > len(after_vals) * 0.3:
                    results.append("  ==> JAPANESE text detected")

    return "\n".join(results)


# Run for both ISOs
output = []
output.append("# R38 Hex Dump Comparison: Original vs v29 Patched")
output.append("# Generated: 2026-05-28")
output.append("")

output.append(read_r38(ORIGINAL_ISO, "ORIGINAL ISO (Japanese)"))
output.append("")
output.append(read_r38(PATCHED_ISO, "PATCHED ISO (v29 English)"))

full_output = "\n".join(output)
print(full_output)

# Write to file
outpath = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/hex_dump_r38.md"
with open(outpath, "w") as f:
    f.write("```\n")
    f.write(full_output)
    f.write("\n```\n")

print("\n\nDone - written to hex_dump_r38.md")
