#!/usr/bin/env python3
"""
parse_packdata_toc.py - Analyze the PACKDATA.DIG table-of-contents / header entries.

Busin 0: Wizardry Alternative Neo (PS2, 2003)
Tries multiple hypotheses for how the 12-byte header entries encode sub-file locations.
"""

import struct
import os
import sys
from collections import Counter

INPUT   = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"
OUTFILE = r"C:\Programmieren\wizardrytranslation\dumps\packdata_toc_analysis.txt"

KNOWN_MAGICS = {
    b"TIM2": "TIM2 texture",
    b"\x89PNG": "PNG image",
    b"RIFF": "RIFF (WAV/AVI)",
    b"OggS": "Ogg Vorbis",
    b"BM":   "BMP image",
    b"PK\x03\x04": "ZIP",
    b"\x7fELF": "ELF executable",
    b"FORM": "IFF container",
    b"VAGp": "VAG audio",
    b"SShd": "SShd (PS2 sound)",
    b"SSbd": "SSbd (PS2 sound body)",
    b"Cmp\x00": "Compressed block",
    b"\x00\x00\x01\xba": "MPEG-PS",
    b"\x10\x00\x00\x00": "PS2 model/generic (0x10 header)",
    b"\x80\x00\x00\x00": "PS2 VIF/GIF data",
}

def identify_magic(data_16):
    if len(data_16) < 4:
        return "too short"
    for magic, name in KNOWN_MAGICS.items():
        if data_16[:len(magic)] == magic:
            return name
    if data_16 == b"\x00" * len(data_16):
        return "all-zero"
    try:
        text = data_16.decode("ascii")
        if all(32 <= ord(c) < 127 or c in "\r\n\t" for c in text):
            return f"ASCII text: {repr(text[:16])}"
    except:
        pass
    return f"unknown (first 4 bytes: {data_16[:4].hex()})"


def main():
    file_size = os.path.getsize(INPUT)
    out_lines = []

    def log(msg=""):
        print(msg)
        out_lines.append(msg)

    log(f"=== PACKDATA.DIG TOC Analysis ===")
    log(f"File size: {file_size:,} bytes  ({file_size / 1024 / 1024:.1f} MB)")
    log(f"File size hex: 0x{file_size:X}")
    log()

    with open(INPUT, "rb") as f:
        header_region = f.read(65536)

        # Step 0: Raw hex dump of first 256 bytes
        log("--- Raw hex dump (first 256 bytes) ---")
        for i in range(0, 256, 16):
            hex_part = " ".join(f"{b:02x}" for b in header_region[i:i+16])
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in header_region[i:i+16])
            log(f"  {i:08x}: {hex_part:<48s}  {ascii_part}")
        log()

        # Step 1: Parse as 12-byte entries (3x uint32 LE)
        log("--- Parsing as 12-byte entries (3x uint32 LE) ---")
        entries_12 = []
        for i in range(0, len(header_region) - 11, 12):
            a, b, c = struct.unpack_from("<III", header_region, i)
            entries_12.append((a, b, c))

        for idx, (a, b, c) in enumerate(entries_12[:100]):
            log(f"  Entry {idx:4d} @ 0x{idx*12:06x}: "
                f"A={a:#10x} ({a:>10d})  B={b:#10x} ({b:>10d})  C={c:#10x} ({c:>10d})")
        log()

        # Step 1b: Parse as 8-byte entries (2x uint32 LE)
        log("--- Parsing as 8-byte entries (2x uint32 LE) ---")
        entries_8 = []
        for i in range(0, min(800, len(header_region) - 7), 8):
            a, b = struct.unpack_from("<II", header_region, i)
            entries_8.append((a, b))
        for idx, (a, b) in enumerate(entries_8[:100]):
            log(f"  Entry {idx:4d} @ 0x{idx*8:05x}: "
                f"A={a:#10x} ({a:>10d})  B={b:#10x} ({b:>10d})")
        log()

        # Step 1c: Parse as 16-byte entries (4x uint32 LE)
        log("--- Parsing as 16-byte entries (4x uint32 LE) ---")
        entries_16 = []
        for i in range(0, min(1600, len(header_region) - 15), 16):
            a, b, c, d = struct.unpack_from("<IIII", header_region, i)
            entries_16.append((a, b, c, d))
        for idx, (a, b, c, d) in enumerate(entries_16[:60]):
            log(f"  Entry {idx:4d} @ 0x{idx*16:05x}: "
                f"A={a:#10x}  B={b:#10x}  C={c:#10x}  D={d:#10x}")
        log()

        # Step 2: Header/data boundary search
        log("--- Searching for header/data boundary ---")
        for boundary in [0x800, 0x1000, 0x2000, 0x4000, 0x8000, 0x10000]:
            if boundary < len(header_region):
                sample = header_region[boundary:boundary+16]
                magic = identify_magic(sample)
                log(f"  At 0x{boundary:06x} ({boundary:>6d}): {sample[:16].hex()}  -> {magic}")

        log()
        log("  Checking for pattern transitions in field A (12-byte parse):")
        prev_a = 0
        for idx, (a, b, c) in enumerate(entries_12[:200]):
            if idx > 0:
                diff = a - prev_a
                if diff < 0 or diff > 0x10000:
                    log(f"    Big jump at entry {idx} (offset 0x{idx*12:x}): "
                        f"prev_A=0x{prev_a:x} -> A=0x{a:x} (diff=0x{diff & 0xFFFFFFFF:x})")
            prev_a = a
        log()

        log("  Is field A monotonically increasing (12-byte entries)?")
        mono_count = 0
        non_mono_idx = -1
        for idx in range(1, min(500, len(entries_12))):
            if entries_12[idx][0] >= entries_12[idx-1][0]:
                mono_count += 1
            else:
                if non_mono_idx < 0:
                    non_mono_idx = idx
        log(f"    Monotonic pairs: {mono_count} / {min(499, len(entries_12)-1)}")
        if non_mono_idx >= 0:
            log(f"    First non-monotonic at entry {non_mono_idx}")
        log()

        # Hypothesis A: (offset, length, type)
        log("=" * 70)
        log("HYPOTHESIS A: 12-byte entries = (offset, length, type)")
        log("=" * 70)
        for idx, (off, length, typ) in enumerate(entries_12[:40]):
            if off > 0 and off < file_size - 16:
                f.seek(off)
                sample = f.read(16)
                magic = identify_magic(sample)
                log(f"  [{idx:3d}] off=0x{off:08x} len=0x{length:08x} typ={typ}: "
                    f"{sample[:8].hex()} -> {magic}")
        log()

        # Hypothesis A2: offset * 2048 (sector-based)
        log("=" * 70)
        log("HYPOTHESIS A2: 12-byte = (sector_offset, length, type), sector=2048")
        log("=" * 70)
        for idx, (sec, length, typ) in enumerate(entries_12[:40]):
            off = sec * 2048
            if off > 0 and off < file_size - 16:
                f.seek(off)
                sample = f.read(16)
                magic = identify_magic(sample)
                log(f"  [{idx:3d}] sec=0x{sec:x} -> off=0x{off:08x} len={length}: "
                    f"{sample[:8].hex()} -> {magic}")
        log()

        # Hypothesis A3: offset * 2048, length * 2048
        log("=" * 70)
        log("HYPOTHESIS A3: 12-byte = (sector_offset, sector_count, type), sector=2048")
        log("=" * 70)
        for idx, (sec, cnt, typ) in enumerate(entries_12[:40]):
            off = sec * 2048
            sz  = cnt * 2048
            if off > 0 and off < file_size - 16:
                f.seek(off)
                sample = f.read(16)
                magic = identify_magic(sample)
                log(f"  [{idx:3d}] off=0x{off:08x} size=0x{sz:x} typ={typ}: "
                    f"{sample[:8].hex()} -> {magic}")
        log()

        # Hypothesis B: (id, offset, length)
        log("=" * 70)
        log("HYPOTHESIS B: 12-byte entries = (id, offset, length)")
        log("=" * 70)
        for idx, (id_val, off, length) in enumerate(entries_12[:40]):
            if off > 0 and off < file_size - 16:
                f.seek(off)
                sample = f.read(16)
                magic = identify_magic(sample)
                log(f"  [{idx:3d}] id=0x{id_val:x} off=0x{off:08x} len=0x{length:x}: "
                    f"{sample[:8].hex()} -> {magic}")
        log()

        # Hypothesis B2: (id, offset*2048, length)
        log("=" * 70)
        log("HYPOTHESIS B2: (id, sector_offset, length), sector=2048")
        log("=" * 70)
        for idx, (id_val, sec, length) in enumerate(entries_12[:40]):
            off = sec * 2048
            if off > 0 and off < file_size - 16:
                f.seek(off)
                sample = f.read(16)
                magic = identify_magic(sample)
                log(f"  [{idx:3d}] id=0x{id_val:x} off=0x{off:08x} len=0x{length:x}: "
                    f"{sample[:8].hex()} -> {magic}")
        log()

        # Hypothesis E: cumulative offset
        log("=" * 70)
        log("HYPOTHESIS E: field_A is cumulative offset")
        log("  Checking if A[i+1] == A[i] + B[i]")
        log("=" * 70)
        matches = 0
        for idx in range(min(50, len(entries_12) - 1)):
            a, b, c = entries_12[idx]
            a_next = entries_12[idx + 1][0]
            predicted = a + b
            diff = a_next - predicted
            marker = ""
            if abs(diff) < 0x100:
                marker = f" (diff={diff})" if diff != 0 else " <-- EXACT"
                matches += 1
            log(f"  [{idx:3d}] A=0x{a:x} + B=0x{b:x} = 0x{predicted:x}  "
                f"next_A=0x{a_next:x}{marker}")
        log(f"  Close matches: {matches}/50")
        log()

        # Hypothesis E2: cumulative with multipliers
        log("=" * 70)
        log("HYPOTHESIS E2: cumulative with multipliers")
        log("=" * 70)
        for mult in [1, 4, 16, 256, 512, 2048, 4096]:
            matches = 0
            for idx in range(min(50, len(entries_12) - 1)):
                a, b, c = entries_12[idx]
                a_next = entries_12[idx + 1][0]
                predicted = a + b * mult
                if a_next == predicted:
                    matches += 1
            log(f"  mult={mult:5d}: exact matches = {matches}/50")

        log()
        log("  Testing: (A_next - A) / B for each entry pair:")
        for idx in range(min(20, len(entries_12) - 1)):
            a, b, c = entries_12[idx]
            a_next = entries_12[idx + 1][0]
            gap = a_next - a
            if b > 0:
                ratio = gap / b
                log(f"    [{idx:3d}] gap=0x{gap:x}  B=0x{b:x}  ratio={ratio:.4f}")
            else:
                log(f"    [{idx:3d}] gap=0x{gap:x}  B=0x{b:x}  (B=0, skip)")
        log()

        # Hypothesis F: First uint32 is entry count
        log("=" * 70)
        log("HYPOTHESIS F: First uint32 is entry count, entries follow at offset 4")
        log("=" * 70)
        first_val = struct.unpack_from("<I", header_region, 0)[0]
        log(f"  First uint32 = {first_val} (0x{first_val:x})")
        log(f"  If count: {first_val} entries * 8 bytes = {first_val*8} (0x{first_val*8:x})")
        log(f"  If count: {first_val} entries * 12 bytes = {first_val*12} (0x{first_val*12:x})")
        log(f"  If count: {first_val} entries * 4 bytes = {first_val*4} (0x{first_val*4:x})")
        log()
        if first_val < 50000:
            log("  Parsing entries starting at offset 4 (8-byte entries):")
            for idx in range(min(20, first_val)):
                off = 4 + idx * 8
                a, b = struct.unpack_from("<II", header_region, off)
                log(f"    [{idx:3d}] A=0x{a:x}  B=0x{b:x}")
            log()
            log("  Parsing entries starting at offset 4 (12-byte entries):")
            for idx in range(min(20, first_val)):
                off = 4 + idx * 12
                if off + 12 <= len(header_region):
                    a, b, c = struct.unpack_from("<III", header_region, off)
                    log(f"    [{idx:3d}] A=0x{a:x}  B=0x{b:x}  C=0x{c:x}")
        log()

        # Hypothesis G: Sector-based with various sector sizes
        log("=" * 70)
        log("HYPOTHESIS G: Field A = cumulative sector offset, field B = sector count")
        log("=" * 70)
        for sector_size in [2048, 4096, 512, 256]:
            log(f"\n  --- Sector size = {sector_size} ---")
            valid = 0
            for idx, (a, b, c) in enumerate(entries_12[:30]):
                off = a * sector_size
                if off > 0 and off < file_size - 16:
                    f.seek(off)
                    sample = f.read(16)
                    magic = identify_magic(sample)
                    if "unknown" not in magic and "all-zero" not in magic:
                        valid += 1
                    if idx < 15:
                        log(f"    [{idx:3d}] A*{sector_size}=0x{off:08x}: "
                            f"{sample[:8].hex()} -> {magic}")
            log(f"    Recognized: {valid}/30")
        log()

        # Step 6: Look for structure changes
        log("=" * 70)
        log("STEP 6: Look for structure changes in the raw data")
        log("=" * 70)
        log("  Scanning uint32 values - looking for where 'header feel' changes:")
        for i in range(0, min(4096, len(header_region)), 4):
            val = struct.unpack_from("<I", header_region, i)[0]
            if val > 0x100000:
                log(f"    First large value (>1MB) at offset 0x{i:x}: 0x{val:x}")
                break

        log("  Scanning for runs of zero bytes:")
        zero_run_start = None
        zero_run_len = 0
        for i in range(len(header_region)):
            if header_region[i] == 0:
                if zero_run_start is None:
                    zero_run_start = i
                zero_run_len += 1
            else:
                if zero_run_len >= 32:
                    log(f"    Zero run: 0x{zero_run_start:x} - 0x{zero_run_start + zero_run_len:x} "
                        f"({zero_run_len} bytes)")
                zero_run_start = None
                zero_run_len = 0
        log()

        # Step 7: Scan for known magic numbers in first 1MB
        log("=" * 70)
        log("STEP 7: Scan for known magic numbers in first 1MB")
        log("=" * 70)
        f.seek(0)
        scan_data = f.read(1024 * 1024)

        magic_searches = [
            (b"TIM2", "TIM2 texture"),
            (b"VAGp", "VAG audio"),
            (b"SShd", "PS2 sound header"),
            (b"RIFF", "RIFF"),
            (b"BM", "BMP"),
            (b"\x89PNG", "PNG"),
        ]
        for magic, name in magic_searches:
            positions = []
            start = 0
            while True:
                pos = scan_data.find(magic, start)
                if pos < 0:
                    break
                positions.append(pos)
                start = pos + 1
                if len(positions) > 20:
                    break
            if positions:
                log(f"  {name}: found at offsets {[f'0x{p:x}' for p in positions[:10]]}")

        log()
        log("  Scanning for potential sub-file boundaries (aligned to 2048):")
        for off in range(0, min(file_size, 2 * 1024 * 1024), 2048):
            if off >= len(scan_data):
                f.seek(off)
                sample = f.read(16)
            else:
                sample = scan_data[off:off+16]
            if len(sample) >= 16:
                magic = identify_magic(sample)
                if "unknown" not in magic and "all-zero" not in magic:
                    log(f"    0x{off:08x}: {sample[:8].hex()} -> {magic}")
        log()

        # Step 8: Validate field A as raw offset for ALL entries
        log("=" * 70)
        log("STEP 8: Validate field A as raw offset - checking ALL entries")
        log("=" * 70)
        recognized = 0
        total_checked = 0
        for idx, (a, b, c) in enumerate(entries_12[:200]):
            if a > 0 and a < file_size - 16:
                f.seek(a)
                sample = f.read(16)
                magic = identify_magic(sample)
                total_checked += 1
                if "unknown" not in magic and "all-zero" not in magic:
                    recognized += 1
                    log(f"  [{idx:3d}] off=0x{a:08x}: {sample[:8].hex()} -> {magic}")
        log(f"  Total checked: {total_checked}, Recognized: {recognized}")
        log()

        # Step 9: Distribution analysis
        log("=" * 70)
        log("STEP 9: Distribution of field values")
        log("=" * 70)
        c_counter = Counter()
        b_counter_ranges = Counter()
        a_diffs = []
        for idx, (a, b, c) in enumerate(entries_12[:500]):
            c_counter[c] += 1
            if b < 0x10:
                b_counter_ranges["0x0-0xF"] += 1
            elif b < 0x100:
                b_counter_ranges["0x10-0xFF"] += 1
            elif b < 0x1000:
                b_counter_ranges["0x100-0xFFF"] += 1
            elif b < 0x10000:
                b_counter_ranges["0x1000-0xFFFF"] += 1
            else:
                b_counter_ranges["0x10000+"] += 1
            if idx > 0:
                a_diffs.append(a - entries_12[idx-1][0])

        log("  Field C value counts (first 500 entries):")
        for val, cnt in sorted(c_counter.items()):
            log(f"    C={val} (0x{val:x}): {cnt} times")
        log()
        log("  Field B range distribution (first 500 entries):")
        for rng, cnt in sorted(b_counter_ranges.items()):
            log(f"    {rng}: {cnt}")
        log()
        if a_diffs:
            log(f"  Field A diffs: min=0x{min(a_diffs):x}, max=0x{max(a_diffs) & 0xFFFFFFFF:x}, "
                f"median=0x{sorted(a_diffs)[len(a_diffs)//2]:x}")
        log()

        # Step 10: Where does the 12-byte entry pattern break?
        log("=" * 70)
        log("STEP 10: Looking for where 12-byte entry pattern breaks")
        log("=" * 70)
        f.seek(0)
        extended = f.read(262144)

        prev_a = 0
        break_idx = -1
        for idx in range(len(extended) // 12):
            a, b, c = struct.unpack_from("<III", extended, idx * 12)
            if idx > 5 and (a < prev_a or c > 0xFFFF):
                if break_idx < 0:
                    break_idx = idx
                    log(f"  Pattern break at entry {idx} (offset 0x{idx*12:x}):")
                    log(f"    prev_A=0x{prev_a:x}")
                    log(f"    this: A=0x{a:x} B=0x{b:x} C=0x{c:x}")
                    for j in range(max(0, idx-3), min(idx+5, len(extended)//12)):
                        aa, bb, cc = struct.unpack_from("<III", extended, j * 12)
                        log(f"      [{j:4d}] A=0x{aa:08x} B=0x{bb:08x} C=0x{cc:08x}")
                    break
            prev_a = a

        if break_idx < 0:
            log("  No clear pattern break found in first 256KB")
            count = 0
            for idx in range(len(extended) // 12):
                a, b, c = struct.unpack_from("<III", extended, idx * 12)
                if a == 0 and b == 0 and c == 0 and idx > 4:
                    log(f"  First all-zero entry at index {idx} (offset 0x{idx*12:x})")
                    break
                count += 1
            log(f"  Estimated entry count: {count}")
        log()

        # Hypothesis H: Sector-based with data_start offset
        log("=" * 70)
        log("HYPOTHESIS H: Sector-based with data_start offset")
        log("=" * 70)
        est_count = 0
        f.seek(0)
        scan_buf = f.read(262144)
        for idx in range(len(scan_buf) // 12):
            a, b, c = struct.unpack_from("<III", scan_buf, idx * 12)
            if a == 0 and b == 0 and c == 0 and idx > 4:
                est_count = idx
                break
            est_count = idx + 1

        log(f"  Estimated entry count: {est_count}")
        toc_size = est_count * 12
        log(f"  TOC size: {toc_size} bytes (0x{toc_size:x})")

        for sec_size in [2048, 4096, 512]:
            data_start = ((toc_size + sec_size - 1) // sec_size) * sec_size
            log(f"\n  data_start (sector {sec_size}): 0x{data_start:x}")

            for mult in [1, 2048, 4096, 512, 16, 4]:
                ok = 0
                for idx in range(min(10, est_count)):
                    a, b, c = struct.unpack_from("<III", scan_buf, idx * 12)
                    file_off = data_start + a * mult
                    if 0 < file_off < file_size - 16:
                        f.seek(file_off)
                        sample = f.read(16)
                        magic = identify_magic(sample)
                        if "unknown" not in magic and "all-zero" not in magic:
                            ok += 1
                if ok > 0:
                    log(f"    mult={mult}: {ok}/10 recognized")
                    for idx in range(min(10, est_count)):
                        a, b, c = struct.unpack_from("<III", scan_buf, idx * 12)
                        file_off = data_start + a * mult
                        if 0 < file_off < file_size - 16:
                            f.seek(file_off)
                            sample = f.read(16)
                            magic = identify_magic(sample)
                            log(f"      [{idx}] 0x{file_off:08x}: {sample[:8].hex()} -> {magic}")

        log()

        # Hypothesis I: First entry's field A (0x7d=125) is entry count
        log("=" * 70)
        log("HYPOTHESIS I: First entry field A (0x7d=125) is entry count")
        log("=" * 70)
        count_guess = entries_12[0][0]
        log(f"  count = {count_guess}")
        toc_end = 12 + count_guess * 12
        log(f"  TOC end = 12 + {count_guess}*12 = {toc_end} (0x{toc_end:x})")

        for sec_size in [2048, 4096]:
            ds = ((toc_end + sec_size - 1) // sec_size) * sec_size
            log(f"  data_start (sector {sec_size}): 0x{ds:x}")
            f.seek(ds)
            sample = f.read(16)
            log(f"    Data at 0x{ds:x}: {sample.hex()} -> {identify_magic(sample)}")

        log()
        log("  Entries 1..125, checking field A as raw offset:")
        for idx in range(1, min(count_guess + 1, 20)):
            a, b, c = entries_12[idx]
            if 0 < a < file_size - 16:
                f.seek(a)
                sample = f.read(16)
                log(f"    [{idx}] off=0x{a:x}: {sample[:8].hex()} -> {identify_magic(sample)}")
        log()

        # Hypothesis J: (byte_offset_relative, byte_size, type)
        log("=" * 70)
        log("HYPOTHESIS J: (byte_offset_relative, byte_size, type)")
        log("=" * 70)
        for data_start_guess in [0x800, 0x1000, 0x5DC, toc_end,
                                  ((toc_end + 2047) // 2048) * 2048]:
            log(f"\n  data_start = 0x{data_start_guess:x}:")
            ok = 0
            for idx, (a, b, c) in enumerate(entries_12[:20]):
                file_off = data_start_guess + a
                if 0 < file_off < file_size - 16:
                    f.seek(file_off)
                    sample = f.read(16)
                    magic = identify_magic(sample)
                    if "unknown" not in magic and "all-zero" not in magic:
                        ok += 1
                    if idx < 10:
                        log(f"    [{idx}] 0x{file_off:08x}: {sample[:8].hex()} -> {magic}")
            log(f"    Recognized: {ok}/20")
        log()

        # Step 14: Brute-force scan for sub-file boundaries
        log("=" * 70)
        log("STEP 14: Brute-force scan for sub-file boundaries")
        log("=" * 70)

        found_boundaries = []
        f.seek(0)
        chunk = f.read(4 * 1024 * 1024)

        for off in range(0, len(chunk), 16):
            sample = chunk[off:off+16]
            magic = identify_magic(sample)
            if "unknown" not in magic and "all-zero" not in magic and "too short" not in magic:
                found_boundaries.append((off, magic))

        log(f"  Found {len(found_boundaries)} potential sub-file starts in first 4MB:")
        for off, magic in found_boundaries[:50]:
            log(f"    0x{off:08x}: {magic}")

        a_values = set(e[0] for e in entries_12[:500])
        log()
        log("  Correlation with field A values:")
        for off, magic in found_boundaries[:50]:
            if off in a_values:
                log(f"    MATCH: 0x{off:x} in field A -> {magic}")
            for sec in [2048, 4096, 512]:
                if off // sec in a_values and off % sec == 0:
                    log(f"    MATCH: 0x{off:x} / {sec} = 0x{off//sec:x} in field A -> {magic}")

        log()

        # STEP 15: Sample data at various file positions
        log("=" * 70)
        log("STEP 15: Sample data at various file positions")
        log("=" * 70)
        for pos in range(0, min(file_size, 100*1024*1024), 10*1024*1024):
            f.seek(pos)
            sample = f.read(64)
            magic = identify_magic(sample[:16])
            hex_str = sample[:32].hex()
            log(f"  0x{pos:08x}: {hex_str}... -> {magic}")
        log()

        # STEP 16: Additional interpretations
        log("=" * 70)
        log("STEP 16: Additional interpretations")
        log("=" * 70)
        log("  Maybe entries are (type, offset_sectors, size_sectors)?")
        for idx, (a, b, c) in enumerate(entries_12[:20]):
            for ss in [2048, 4096]:
                off = b * ss
                sz = c * ss
                if 0 < off < file_size - 16:
                    f.seek(off)
                    sample = f.read(16)
                    magic = identify_magic(sample)
                    if "unknown" not in magic:
                        log(f"    [{idx}] type={a} off=0x{off:x} (B*{ss}) sz=0x{sz:x}: {magic}")

        log()
        log("  Maybe (offset_sectors, size_bytes, type)?")
        for idx, (a, b, c) in enumerate(entries_12[:20]):
            for ss in [2048, 4096, 512]:
                off = a * ss
                if 0 < off < file_size:
                    f.seek(off)
                    sample = f.read(16)
                    magic = identify_magic(sample)
                    if "unknown" not in magic:
                        log(f"    [{idx}] off=0x{off:x} (A*{ss}) sz={b} type={c}: {magic}")

        log()

    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
    with open(OUTFILE, "w", encoding="utf-8") as out:
        out.write("\n".join(out_lines))
    log(f"\nAnalysis written to: {OUTFILE}")


if __name__ == "__main__":
    main()
