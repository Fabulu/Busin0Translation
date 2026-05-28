#!/usr/bin/env python3
"""
find_font_data.py - Font/glyph data and character encoding table scanner
for Busin 0: Wizardry Alternative Neo (PS2, 2003, Atlus/Racjin).

Scans the game EXE and PACKDATA.DIG for:
  1. Shift-JIS mapping tables in the EXE
  2. Font width arrays in the EXE
  3. TIM2 image headers in PACKDATA.DIG (first 50MB)
  4. ASCII strings referencing font/text keywords in the EXE
"""

import struct
import re
import os
import sys

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
PACK_PATH = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"
OUTPUT_PATH = r"C:\Programmieren\wizardrytranslation\dumps\font_analysis.txt"

PACK_SCAN_SIZE = 50 * 1024 * 1024  # 50 MB

out_lines = []

def log(msg=""):
    out_lines.append(msg)
    print(msg)

def section(title):
    log("")
    log("=" * 72)
    log("  " + title)
    log("=" * 72)

# ---------------------------------------------------------------------------
# 1. Search for Shift-JIS mapping tables in the EXE
# ---------------------------------------------------------------------------
def find_sjis_tables(data):
    section("1. SHIFT-JIS MAPPING TABLES IN EXE")
    log("Scanning for sequences of consecutive SJIS codepoints (>=16 entries)...")
    log("")

    results = []
    i = 0
    while i < len(data) - 3:
        hi, lo = data[i], data[i + 1]
        if (0x81 <= hi <= 0x9F or 0xE0 <= hi <= 0xEF) and \
           (0x40 <= lo <= 0x7E or 0x80 <= lo <= 0xFC):
            start = i
            prev_val = (hi << 8) | lo
            count = 1
            j = i + 2
            while j < len(data) - 1:
                h2, l2 = data[j], data[j + 1]
                if (0x81 <= h2 <= 0x9F or 0xE0 <= h2 <= 0xEF) and \
                   (0x40 <= l2 <= 0x7E or 0x80 <= l2 <= 0xFC):
                    cur_val = (h2 << 8) | l2
                    diff = cur_val - prev_val
                    if 1 <= diff <= 3:
                        count += 1
                        prev_val = cur_val
                        j += 2
                        continue
                break
            if count >= 16:
                first_val = (data[start] << 8) | data[start + 1]
                last_val = (data[j - 2] << 8) | data[j - 1]
                results.append((start, j - start, count, first_val, last_val))
                i = j
                continue
        i += 1

    if results:
        log("Found %d candidate SJIS mapping table(s):" % len(results))
        for offset, size, count, first, last in results:
            log("  Offset 0x%06X - 0x%06X: %d entries, range 0x%04X..0x%04X (%d bytes)" %
                (offset, offset+size-1, count, first, last, size))
            preview = []
            for k in range(min(8, count)):
                v = (data[offset + k*2] << 8) | data[offset + k*2 + 1]
                preview.append("0x%04X" % v)
            log("    First entries: %s..." % ', '.join(preview))
            try:
                sample_bytes = data[offset:offset + min(16, count*2)]
                decoded = sample_bytes.decode('shift_jis', errors='replace')
                log("    Decoded: %s" % decoded)
            except:
                pass
    else:
        log("  No consecutive SJIS mapping tables found.")

    log("")
    log("Scanning for SJIS range definition patterns (start/end pairs)...")
    range_results = []
    for i in range(0, len(data) - 7, 2):
        v1 = struct.unpack_from('>H', data, i)[0]
        v2 = struct.unpack_from('>H', data, i + 2)[0]
        v3 = struct.unpack_from('>H', data, i + 4)[0]
        v4 = struct.unpack_from('>H', data, i + 6)[0]
        if v1 == 0x8140 and v2 in (0x817E, 0x819E, 0x81FC, 0x81AC):
            range_results.append((i, v1, v2, v3, v4))
        elif v1 == 0x824F and v2 in (0x8258, 0x8259):
            range_results.append((i, v1, v2, v3, v4))
        elif v1 == 0x8260 and v2 in (0x8279, 0x827A):
            range_results.append((i, v1, v2, v3, v4))

    if range_results:
        log("  Found %d SJIS range marker(s):" % len(range_results))
        for off, v1, v2, v3, v4 in range_results:
            log("    0x%06X: 0x%04X 0x%04X 0x%04X 0x%04X" % (off, v1, v2, v3, v4))
    else:
        log("  No explicit SJIS range markers found.")

    return results


# ---------------------------------------------------------------------------
# 2. Font width arrays in the EXE
# ---------------------------------------------------------------------------
def find_width_tables(data):
    section("2. FONT WIDTH ARRAYS IN EXE")
    log("Scanning for sequences of small byte values (4-16) with length >= 32...")
    log("")

    results = []
    i = 0
    while i < len(data):
        if 4 <= data[i] <= 16:
            start = i
            j = i
            while j < len(data) and 4 <= data[j] <= 16:
                j += 1
            length = j - start
            if length >= 32:
                unique = len(set(data[start:j]))
                results.append((start, length, unique))
            i = j
        else:
            i += 1

    if results:
        results.sort(key=lambda x: -x[1])
        log("Found %d candidate width table(s):" % len(results))
        for offset, length, unique in results[:30]:
            sample = ' '.join('%2d' % data[offset+k] for k in range(min(24, length)))
            log("  0x%06X: %d bytes, %d unique values" % (offset, length, unique))
            log("    Sample: [%s...]" % sample)
            vals = list(data[offset:offset+length])
            avg = sum(vals) / len(vals)
            log("    Avg width: %.1f" % avg)
    else:
        log("  No candidate width tables found.")

    log("")
    log("Scanning for 16-bit width tables (2 bytes per entry, values 4-32)...")
    results16 = []
    i = 0
    while i < len(data) - 1:
        v = struct.unpack_from('<H', data, i)[0]
        if 4 <= v <= 32:
            start = i
            j = i
            count = 0
            while j < len(data) - 1:
                v2 = struct.unpack_from('<H', data, j)[0]
                if 4 <= v2 <= 32:
                    count += 1
                    j += 2
                else:
                    break
            if count >= 32:
                results16.append((start, count))
            i = j if j > i else i + 2
        else:
            i += 2

    if results16:
        results16.sort(key=lambda x: -x[1])
        log("Found %d candidate 16-bit width table(s):" % len(results16))
        for offset, count in results16[:15]:
            sample = ' '.join('%2d' % struct.unpack_from('<H', data, offset+k*2)[0]
                              for k in range(min(16, count)))
            log("  0x%06X: %d entries" % (offset, count))
            log("    Sample: [%s...]" % sample)
    else:
        log("  No 16-bit width tables found.")

    return results


# ---------------------------------------------------------------------------
# 3. TIM2 headers in PACKDATA.DIG
# ---------------------------------------------------------------------------
def find_tim2_headers(pack_path, scan_size):
    section("3. TIM2 IMAGE HEADERS IN PACKDATA.DIG")
    log("Scanning first %d MB for TIM2 magic (0x54494D32)..." % (scan_size // (1024*1024)))
    log("")

    results = []
    with open(pack_path, 'rb') as f:
        chunk_size = 4 * 1024 * 1024
        overlap = 64
        pos = 0
        prev_tail = b''
        while pos < scan_size:
            read_size = min(chunk_size, scan_size - pos)
            chunk = f.read(read_size)
            if not chunk:
                break
            search_data = prev_tail + chunk
            search_offset = pos - len(prev_tail)

            idx = 0
            while idx < len(search_data) - 16:
                idx = search_data.find(b'TIM2', idx)
                if idx == -1:
                    break
                abs_offset = search_offset + idx
                if idx + 16 <= len(search_data):
                    hdr = search_data[idx:idx+16]
                    version = hdr[4]
                    alignment = hdr[5]
                    num_images = struct.unpack_from('<H', hdr, 6)[0]
                    info = {}
                    if idx + 48 + 16 <= len(search_data):
                        entry = search_data[idx+16:idx+64]
                        total_size = struct.unpack_from('<I', entry, 0)[0]
                        clut_size = struct.unpack_from('<I', entry, 4)[0]
                        img_size = struct.unpack_from('<I', entry, 8)[0]
                        header_size = struct.unpack_from('<H', entry, 12)[0]
                        clut_colors = struct.unpack_from('<H', entry, 14)[0]
                        img_format = entry[16]
                        mip_count = entry[17]
                        clut_type = struct.unpack_from('<H', entry, 18)[0]
                        width = struct.unpack_from('<H', entry, 20)[0]
                        height = struct.unpack_from('<H', entry, 22)[0]
                        info = {
                            'total_size': total_size,
                            'clut_size': clut_size,
                            'img_size': img_size,
                            'width': width,
                            'height': height,
                            'img_format': img_format,
                            'clut_colors': clut_colors,
                        }
                    results.append((abs_offset, version, num_images, info))
                idx += 4

            prev_tail = chunk[-overlap:] if len(chunk) >= overlap else chunk
            pos += read_size

    if results:
        log("Found %d TIM2 header(s):" % len(results))
        font_candidates = []
        for offset, ver, nimages, info in results:
            w = info.get('width', '?')
            h = info.get('height', '?')
            fmt = info.get('img_format', '?')
            fmt_names = {0: '16-bit', 1: '24-bit', 2: '32-bit', 3: '4-bit indexed',
                         4: '8-bit indexed', 5: '4-bit', 6: '8-bit'}
            fmt_str = fmt_names.get(fmt, 'type%s' % fmt)
            clut = info.get('clut_colors', '?')
            total = info.get('total_size', 0)
            img_sz = info.get('img_size', 0)

            is_font = False
            if isinstance(w, int) and isinstance(h, int):
                if (w in (128, 256, 512, 1024) and h in (128, 256, 512, 1024)):
                    is_font = True
                if w >= 128 and h >= 128 and (w * h >= 128 * 128):
                    is_font = True

            marker = " <<< FONT CANDIDATE" if is_font else ""
            log("  0x%08X: v%d, %d img(s), %sx%s, %s, %s CLUT colors, imgSize=%s, totalSize=%s%s" %
                (offset, ver, nimages, w, h, fmt_str, clut, img_sz, total, marker))
            if is_font:
                font_candidates.append((offset, w, h, fmt, info))

        if font_candidates:
            log("")
            log("=== %d font texture candidate(s) ===" % len(font_candidates))
            for offset, w, h, fmt, info in font_candidates:
                log("  0x%08X: %dx%d" % (offset, w, h))
                for glyph_sz in (8, 10, 12, 14, 16, 18, 20, 24, 32):
                    if w % glyph_sz == 0 and h % glyph_sz == 0:
                        cols = w // glyph_sz
                        rows = h // glyph_sz
                        total_glyphs = cols * rows
                        log("    If %dx%d glyphs: %dx%d grid = %d glyphs" %
                            (glyph_sz, glyph_sz, cols, rows, total_glyphs))
    else:
        log("  No TIM2 headers found in first 50 MB.")

    log("")
    log("Also scanning for non-TIM2 font signatures...")
    with open(pack_path, 'rb') as f:
        scan = f.read(scan_size)

    for pattern, label in [(b'.fnt', '.fnt'), (b'FONT', 'FONT'), (b'font', 'font'),
                            (b'.FNT', '.FNT'), (b'FNTA', 'FNTA')]:
        for m in re.finditer(re.escape(pattern), scan):
            ctx = scan[max(0, m.start()-8):m.start()+32]
            printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
            log("  '%s' at 0x%08X: %s" % (label, m.start(), printable))

    return results


# ---------------------------------------------------------------------------
# 4. ASCII strings referencing font/text keywords in EXE
# ---------------------------------------------------------------------------
def find_font_strings(data):
    section("4. FONT/TEXT-RELATED STRINGS IN EXE")
    log("Searching for ASCII strings containing font/text keywords...")
    log("")

    keywords = [b'font', b'fnt', b'char', b'glyph', b'text', b'msg',
                b'kanji', b'kana', b'ascii', b'sjis', b'shift',
                b'letter', b'width', b'kern', b'string', b'dialog',
                b'menu', b'encode', b'decode']

    found = set()
    for m in re.finditer(rb'[\x20-\x7E]{4,80}\x00', data):
        s = m.group()[:-1]
        s_lower = s.lower()
        for kw in keywords:
            if kw in s_lower:
                offset = m.start()
                found.add((offset, s.decode('ascii', errors='replace')))
                break

    if found:
        sorted_found = sorted(found)
        log("Found %d matching string(s):" % len(sorted_found))
        for offset, s in sorted_found:
            log("  0x%06X: \"%s\"" % (offset, s))
    else:
        log("  No font/text-related strings found.")

    log("")
    log("Searching for format strings that suggest text rendering...")
    for kw in [b'%s', b'%d', b'%c', b'%02x']:
        count = data.count(kw)
        log("  '%s' format specifier count: %d" % (kw.decode(), count))

    return found


# ---------------------------------------------------------------------------
# 5. Character code tables / lookup tables
# ---------------------------------------------------------------------------
def find_char_tables(data):
    section("5. CHARACTER CODE TABLES / LOOKUP TABLES")
    log("Scanning for sequential 16-bit value tables (potential char code LUTs)...")
    log("")

    results = []
    for i in range(0, len(data) - 64, 2):
        v0 = struct.unpack_from('<H', data, i)[0]
        if v0 == 0 or v0 == 0xFFFF:
            continue
        count = 1
        for j in range(i + 2, min(i + 2000, len(data) - 1), 2):
            vn = struct.unpack_from('<H', data, j)[0]
            expected = v0 + count
            if vn == expected:
                count += 1
            else:
                break
        if count >= 32:
            results.append((i, v0, count))

    # Also big-endian SJIS-specific
    for i in range(0, len(data) - 64, 2):
        v0 = struct.unpack_from('>H', data, i)[0]
        if v0 == 0 or v0 == 0xFFFF:
            continue
        if 0x8140 <= v0 <= 0x8160:
            count = 1
            for j in range(i + 2, min(i + 2000, len(data) - 1), 2):
                vn = struct.unpack_from('>H', data, j)[0]
                expected = v0 + count
                if vn == expected or (vn - v0 - count) <= 2:
                    count += 1
                else:
                    break
            if count >= 16:
                results.append((i, v0, count))

    if results:
        results.sort(key=lambda x: -x[2])
        log("Found %d sequential value table(s):" % len(results))
        for offset, start_val, count in results[:20]:
            log("  0x%06X: starts at %d (0x%04X), %d sequential entries" %
                (offset, start_val, start_val, count))
            sample = []
            for k in range(min(8, count)):
                v = struct.unpack_from('<H', data, offset + k * 2)[0]
                sample.append("0x%04X" % v)
            log("    Values: %s..." % ', '.join(sample))
    else:
        log("  No sequential value tables found.")

    log("")
    log("Scanning for 256-byte lookup tables (byte->index mappings)...")
    lut_results = []
    for i in range(0, len(data) - 256):
        chunk = data[i:i+256]
        unique = set(chunk)
        if len(unique) >= 32 and max(chunk) <= 255 and min(chunk) < 32:
            ctrl_zeros = sum(1 for b in chunk[:32] if b == 0 or b == 0xFF)
            if ctrl_zeros >= 20:
                ascii_vals = set(chunk[0x20:0x7F])
                if len(ascii_vals) >= 40:
                    lut_results.append((i, len(unique), chunk))

    if lut_results:
        log("Found %d candidate 256-byte LUT(s):" % len(lut_results))
        for offset, nunique, chunk in lut_results[:10]:
            log("  0x%06X: %d unique values" % (offset, nunique))
            sample = ' '.join('%3d' % chunk[0x20+k] for k in range(16))
            log("    Mapping for ' '..'/': [%s]" % sample)
            sample2 = ' '.join('%3d' % chunk[0x41+k] for k in range(min(16, 26)))
            log("    Mapping for 'A'..'P': [%s]" % sample2)
    else:
        log("  No 256-byte LUTs found.")


# ---------------------------------------------------------------------------
# 6. SJIS code patterns in EXE (MIPS R5900)
# ---------------------------------------------------------------------------
def find_sjis_code_patterns(data):
    section("6. SJIS CODE PATTERNS IN EXE (MIPS R5900)")
    log("Looking for SJIS lead-byte check constants (0x81, 0x9F, 0xE0, 0xEF)...")
    log("")

    sjis_constants = {
        0x0081: 'SJIS lead byte start (0x81)',
        0x009F: 'SJIS lead byte end (0x9F)',
        0x00A0: 'SJIS lead byte end+1 (0xA0)',
        0x00E0: 'SJIS lead byte start2 (0xE0)',
        0x00EF: 'SJIS lead byte end2 (0xEF)',
        0x00F0: 'SJIS lead byte end2+1 (0xF0)',
        0x0040: 'SJIS trail byte start (0x40)',
        0x007E: 'SJIS trail byte mid-end (0x7E)',
        0x007F: 'SJIS trail byte gap (0x7F)',
        0x0080: 'SJIS trail byte start2 (0x80)',
        0x00FC: 'SJIS trail byte end (0xFC)',
        0x8140: 'SJIS full-width space',
        0x824F: 'SJIS digit 0',
        0x8260: 'SJIS uppercase A',
        0x8281: 'SJIS lowercase a',
        0x8340: 'SJIS katakana start',
    }

    for const, desc in sorted(sjis_constants.items()):
        pattern = struct.pack('<H', const)
        count = 0
        locations = []
        idx = 0
        while idx < len(data) - 1:
            idx = data.find(pattern, idx)
            if idx == -1:
                break
            if idx % 2 == 0:
                count += 1
                if len(locations) < 5:
                    locations.append(idx)
            idx += 2
        if count > 0 and count < 200:
            locs = ', '.join('0x%06X' % l for l in locations)
            extra = ' ... +%d more' % (count-5) if count > 5 else ''
            log("  %s: %d occurrence(s) at %s%s" % (desc, count, locs, extra))

    log("")
    log("Searching for 0x8140 (SJIS space) as 32-bit LE value...")
    pattern32 = struct.pack('<I', 0x8140)
    count = data.count(pattern32)
    log("  Found %d occurrence(s) of 0x00008140" % count)
    pattern32be = struct.pack('>I', 0x8140)
    count = data.count(pattern32be)
    log("  Found %d occurrence(s) of 0x81400000" % count)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log("=" * 72)
    log("  FONT DATA ANALYSIS: Busin 0 - Wizardry Alternative Neo")
    log("  PS2 EXE: SLPM_653.78")
    log("  Pack file: PACKDATA.DIG (first 50 MB)")
    log("=" * 72)

    log("\nLoading EXE: %s" % EXE_PATH)
    with open(EXE_PATH, 'rb') as f:
        exe_data = f.read()
    log("  Size: %d bytes (%.1f MB)" % (len(exe_data), len(exe_data)/1024/1024))

    find_sjis_tables(exe_data)
    find_width_tables(exe_data)
    find_font_strings(exe_data)
    find_char_tables(exe_data)
    find_sjis_code_patterns(exe_data)

    log("\nLoading PACKDATA.DIG (first %d MB)..." % (PACK_SCAN_SIZE // (1024*1024)))
    find_tim2_headers(PACK_PATH, PACK_SCAN_SIZE)

    section("SUMMARY")
    log("Analysis complete. Review candidates above for font data locations.")
    log("Key areas to investigate further:")
    log("  - SJIS tables: check if they map byte sequences to glyph indices")
    log("  - Width tables: verify if values correspond to rendered character widths")
    log("  - TIM2 candidates: extract and view as images to confirm font textures")
    log("  - Font strings: trace references to understand rendering pipeline")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    log("\nResults written to: %s" % OUTPUT_PATH)


if __name__ == '__main__':
    main()
