"""Search PCSX2 save state (.p2s) for font atlas data in EE RAM.

Searches for pixel data from all three font resources:
  - R2100 (type-04): 4 sub-blocks of 32KB each (chargen stat kanji atlas)
  - R1272 (type-01): 256x512 PSMT4 = 65536 bytes (main dialogue font)
  - R1188 (type-01): 1024x1024 PSMT4 = 524288 bytes (name entry font)

Uses the BUILD resources (patched English) so signatures match what the
v9 ISO actually loads into RAM.

PCSX2 .p2s files are ZIP archives (older) or zstd-compressed blobs (Qt 1.7+).
The EE RAM (32 MB) is stored as "eeMemory.bin".

Usage:
    python tools/search_save_state.py <path_to_savestate.p2s>

Steps:
    1. Boot the v9 ISO FRESH from the title screen
       (do NOT load save states from older builds!)
    2. Navigate to the character creation stat screen
       (where the kanji/English stat labels appear)
    3. Press F1 in PCSX2 to create a save state
       (save states go to PCSX2/sstates/)
    4. Run this script on the .p2s file
"""
import sys
import os
import zipfile
import struct
import io

# ── Paths ──
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_RES = os.path.join(BASE, 'build', 'packdata_resources')
EXTRACTED_RAW = os.path.join(BASE, 'extracted', 'packdata_raw')

# ── Resource pixel data layout ──
# R2100 (type-04): 4 sub-blocks, each with 64-byte GIF header + 32768 bytes pixel data
# Descriptor table: 4 entries x 16 bytes at offset 0x00
#   [0] u32 sub_index  [4] u32 sub_size  [8] u32 data_offset  [12] u32 pad
R2100_GIF_HDR = 64
R2100_PIXEL_SIZE = 32768
R2100_NUM_SUBS = 4

# R1272 (type-01): raw offset 0x10 = start of GIF packet, +192 bytes header = pixel data
# Pixel data: 256x512 PSMT4 = 65536 bytes
R1272_RAW_PIXEL_OFF = 0xD0   # 0x10 (type-01 wrapper) + 0xC0 (192-byte GIF header)
R1272_PIXEL_SIZE = 65536

# R1188 (type-01): raw offset 0x10 = start of GIF packet, +3072 bytes header = pixel data
# Pixel data: 1024x1024 PSMT4 = 524288 bytes
R1188_RAW_PIXEL_OFF = 0xC10  # 0x10 (type-01 wrapper) + 0xC00 (3072-byte GIF header)
R1188_PIXEL_SIZE = 524288


def load_font_signatures():
    """Load pixel data signatures from all three font resources.

    Returns dict: { label: (pixel_data_bytes, description) }
    Uses BUILD resources (patched English) first, falls back to extracted originals.
    """
    sigs = {}

    # ── R2100 sub-blocks ──
    r2100_path = os.path.join(BUILD_RES, '2100_type04.raw')
    if os.path.exists(r2100_path):
        r2100 = open(r2100_path, 'rb').read()
        for i in range(R2100_NUM_SUBS):
            sub_idx, sub_size, data_off, _ = struct.unpack_from('<IIII', r2100, i * 16)
            pixel_off = data_off + R2100_GIF_HDR
            pixels = r2100[pixel_off:pixel_off + R2100_PIXEL_SIZE]
            if len(pixels) == R2100_PIXEL_SIZE:
                sigs[f'R2100_sub{i}'] = (pixels, f'R2100 sub-block {i} (32KB, chargen kanji)')
        print(f"  R2100: loaded {sum(1 for k in sigs if k.startswith('R2100'))} sub-blocks from build")
    else:
        # Fall back to pre-extracted pixel files
        for i in range(R2100_NUM_SUBS):
            path = os.path.join(EXTRACTED_RAW, f'r2100_sub{i}_pixels.bin')
            if os.path.exists(path):
                pixels = open(path, 'rb').read()
                sigs[f'R2100_sub{i}'] = (pixels, f'R2100 sub-block {i} (32KB, chargen kanji)')
        loaded = sum(1 for k in sigs if k.startswith('R2100'))
        if loaded:
            print(f"  R2100: loaded {loaded} sub-blocks from extracted/packdata_raw")
        else:
            print(f"  R2100: NOT FOUND")

    # ── R1272 (main dialogue font) ──
    r1272_path = os.path.join(BUILD_RES, '1272_type01.raw')
    if os.path.exists(r1272_path):
        r1272 = open(r1272_path, 'rb').read()
        pixels = r1272[R1272_RAW_PIXEL_OFF:R1272_RAW_PIXEL_OFF + R1272_PIXEL_SIZE]
        if len(pixels) == R1272_PIXEL_SIZE:
            sigs['R1272'] = (pixels, f'R1272 (65KB, 256x512 PSMT4, main dialogue font)')
            print(f"  R1272: loaded {len(pixels)} bytes from build")
        else:
            print(f"  R1272: pixel data too short ({len(pixels)} < {R1272_PIXEL_SIZE})")
    else:
        # Try extracted .bin (which has 192-byte header + pixels + 64-byte palette)
        r1272_bin = os.path.join(BASE, 'extracted', 'packdata_resources', '1272_type01.bin')
        if os.path.exists(r1272_bin):
            bindata = open(r1272_bin, 'rb').read()
            pixels = bindata[192:192 + R1272_PIXEL_SIZE]
            if len(pixels) == R1272_PIXEL_SIZE:
                sigs['R1272'] = (pixels, f'R1272 (65KB, main dialogue font, from extracted)')
                print(f"  R1272: loaded {len(pixels)} bytes from extracted .bin")
        else:
            print(f"  R1272: NOT FOUND")

    # ── R1188 (name entry font) ──
    r1188_path = os.path.join(BUILD_RES, '1188_type01.raw')
    if os.path.exists(r1188_path):
        r1188 = open(r1188_path, 'rb').read()
        pixels = r1188[R1188_RAW_PIXEL_OFF:R1188_RAW_PIXEL_OFF + R1188_PIXEL_SIZE]
        if len(pixels) == R1188_PIXEL_SIZE:
            sigs['R1188'] = (pixels, f'R1188 (512KB, 1024x1024 PSMT4, name entry font)')
            print(f"  R1188: loaded {len(pixels)} bytes from build")
        else:
            print(f"  R1188: pixel data too short ({len(pixels)} < {R1188_PIXEL_SIZE})")
    else:
        r1188_bin = os.path.join(BASE, 'extracted', 'packdata_resources', '1188_type01.bin')
        if os.path.exists(r1188_bin):
            bindata = open(r1188_bin, 'rb').read()
            pixels = bindata[3072:3072 + R1188_PIXEL_SIZE]
            if len(pixels) == R1188_PIXEL_SIZE:
                sigs['R1188'] = (pixels, f'R1188 (512KB, name entry font, from extracted)')
                print(f"  R1188: loaded {len(pixels)} bytes from extracted .bin")
        else:
            print(f"  R1188: NOT FOUND")

    return sigs


def extract_ee_ram_from_p2s(p2s_path):
    """Extract EE RAM from a PCSX2 save state.

    Handles both ZIP archives (older PCSX2) and zstd-compressed (Qt 1.7+).
    Returns the full decompressed blob (which contains eeMemory.bin at some offset).
    """
    print(f"\nOpening save state: {p2s_path}")
    file_size = os.path.getsize(p2s_path)
    print(f"  File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    raw = open(p2s_path, 'rb').read()
    magic = raw[:4]
    print(f"  Magic: {magic.hex()} ({magic!r})")

    # ZIP format
    if magic[:2] == b'PK':
        print("  Format: ZIP archive")
        return _extract_from_zip(p2s_path)

    # Zstandard (PCSX2 Qt 1.7+)
    if magic == b'\x28\xb5\x2f\xfd':
        print("  Format: Zstandard compressed")
        return _extract_from_zstd(raw)

    print(f"  Unknown format (magic: {magic.hex()})")
    print("  Treating entire file as raw data...")
    return raw


def _extract_from_zip(p2s_path):
    """Extract EE RAM from a ZIP-format save state."""
    with zipfile.ZipFile(p2s_path, 'r') as zf:
        names = zf.namelist()
        print(f"  ZIP entries: {names}")

        ee_candidates = [n for n in names if 'ee' in n.lower() and 'mem' in n.lower()]
        if not ee_candidates:
            ee_candidates = []
            for n in names:
                info = zf.getinfo(n)
                print(f"    {n}: {info.file_size:,} bytes")
                if info.file_size >= 32 * 1024 * 1024:
                    ee_candidates.append(n)

        if not ee_candidates:
            print("  ERROR: Could not find EE RAM entry in ZIP")
            for n in names:
                info = zf.getinfo(n)
                print(f"    {n}: {info.file_size:,} bytes")
            return None

        entry = ee_candidates[0]
        print(f"  Extracting: {entry}")
        return zf.read(entry)


def _extract_from_zstd(raw_data):
    """Extract EE RAM from a zstd-compressed save state."""
    try:
        import zstandard
    except ImportError:
        print("  ERROR: 'zstandard' package not installed.")
        print("  Install with: pip install zstandard")
        sys.exit(1)

    dctx = zstandard.ZstdDecompressor()
    try:
        decompressed = dctx.decompress(raw_data, max_output_size=256 * 1024 * 1024)
    except Exception as e:
        print(f"  Single-shot decompression failed: {e}")
        print("  Trying streaming decompression...")
        reader = dctx.stream_reader(io.BytesIO(raw_data))
        chunks = []
        while True:
            chunk = reader.read(1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        decompressed = b''.join(chunks)

    print(f"  Decompressed size: {len(decompressed):,} bytes ({len(decompressed)/1024/1024:.1f} MB)")
    return decompressed


def find_high_entropy_sig(pixels, sig_len=64):
    """Find a high-entropy signature region within pixel data.

    Skips low-entropy regions (all-zero, all-FF, repetitive GIF headers)
    and returns the offset+data of the first region with many unique bytes.
    """
    best_off = None
    best_uniq = 0
    for off in range(0, len(pixels) - sig_len, 256):
        chunk = pixels[off:off + sig_len]
        uniq = len(set(chunk))
        if uniq > best_uniq:
            best_uniq = uniq
            best_off = off
        if uniq >= 40:  # Good enough
            break
    return best_off, best_uniq


def search_for_data(ram, label, pixels, description):
    """Search RAM for a font resource's pixel data.

    Tries:
    1. Full exact match
    2. Large signature match (256 bytes) with cross-verification
    3. Medium signature match (64 bytes) from high-entropy region
    4. Small signature scan (16 bytes) for partial matches

    Returns (match_type, ram_offset) or None.
    """
    print(f"\n{'='*60}")
    print(f"  {label}: {description}")
    print(f"  Pixel data size: {len(pixels):,} bytes")
    print(f"{'='*60}")

    # ── 1. Full exact match ──
    pos = ram.find(pixels)
    if pos >= 0:
        print(f"  EXACT MATCH at RAM 0x{pos:08X} ({pos:,})")
        return ('exact', pos)

    # ── 2. Signature-based search ──
    # Pick multiple signature regions from different parts of the data
    sig_configs = [
        # (offset_in_pixels, length)
        (len(pixels) // 4, 256),      # 25% into data
        (len(pixels) // 2, 256),      # 50% into data
        (len(pixels) * 3 // 4, 256),  # 75% into data
    ]

    # Also add high-entropy regions
    he_off, he_uniq = find_high_entropy_sig(pixels, 64)
    if he_off is not None:
        sig_configs.insert(0, (he_off, 256))

    for sig_off, sig_len in sig_configs:
        if sig_off + sig_len > len(pixels):
            sig_len = min(sig_len, len(pixels) - sig_off)
        if sig_len < 16:
            continue

        sig = pixels[sig_off:sig_off + sig_len]

        # Skip low-entropy signatures
        if len(set(sig)) <= 4:
            continue

        pos = ram.find(sig)
        if pos >= 0:
            block_start = pos - sig_off
            if block_start < 0:
                continue

            print(f"  SIGNATURE MATCH: {sig_len}-byte sig from pixel offset 0x{sig_off:X}")
            print(f"    Sig found at RAM 0x{pos:08X}")
            print(f"    Implied pixel block start: RAM 0x{block_start:08X}")

            # Cross-verify with a different region
            verify_off = sig_off + len(pixels) // 3
            if verify_off + 16 > len(pixels):
                verify_off = sig_off // 2
            if verify_off == sig_off:
                verify_off = min(sig_off + 4096, len(pixels) - 16)

            if block_start + verify_off + 16 <= len(ram) and verify_off + 16 <= len(pixels):
                verify_sig = pixels[verify_off:verify_off + 16]
                if len(set(verify_sig)) > 2:  # Only verify with non-trivial data
                    if ram[block_start + verify_off:block_start + verify_off + 16] == verify_sig:
                        print(f"    VERIFIED with cross-check at pixel offset 0x{verify_off:X}")
                        return ('sig_verified', block_start)
                    else:
                        print(f"    Cross-check FAILED at offset 0x{verify_off:X}")
                        # Try next occurrence
                        next_pos = pos + 1
                        attempts = 0
                        while next_pos < len(ram) and attempts < 20:
                            next_pos = ram.find(sig, next_pos)
                            if next_pos < 0:
                                break
                            bs2 = next_pos - sig_off
                            if bs2 >= 0 and bs2 + verify_off + 16 <= len(ram):
                                if ram[bs2 + verify_off:bs2 + verify_off + 16] == verify_sig:
                                    print(f"    VERIFIED at alternate location: RAM 0x{bs2:08X}")
                                    return ('sig_verified', bs2)
                            next_pos += 1
                            attempts += 1
                        # Accept unverified if it's the only match
                        print(f"    Accepting unverified match at 0x{block_start:08X}")
                        return ('sig_unverified', block_start)
                else:
                    return ('sig_trivial_verify', block_start)
            else:
                return ('sig_only', block_start)

    # ── 3. Small signature scan ──
    print(f"  No large signatures found. Trying 16-byte scan...")
    # Pick a distinctive 16-byte chunk from the middle
    mid = len(pixels) // 2
    for scan_off in [mid, mid + 4096, mid - 4096, len(pixels) // 4]:
        if scan_off < 0 or scan_off + 16 > len(pixels):
            continue
        sig = pixels[scan_off:scan_off + 16]
        if len(set(sig)) <= 3:
            continue

        matches = []
        pos = 0
        while len(matches) < 10:
            pos = ram.find(sig, pos)
            if pos < 0:
                break
            matches.append(pos)
            pos += 1

        if matches:
            for m in matches[:5]:
                implied = m - scan_off
                print(f"    16-byte match at RAM 0x{m:08X} (implied start 0x{implied:08X})")
            if len(matches) == 1:
                implied = matches[0] - scan_off
                return ('small_sig_unique', implied)
        else:
            print(f"    No 16-byte matches for sig at pixel offset 0x{scan_off:X}")

    print(f"  NOT FOUND in RAM")
    return None


def classify_address(addr, label):
    """Classify a RAM address into memory regions."""
    regions = [
        (0x00000000, 0x00100000, "EE kernel / low memory"),
        (0x00100000, 0x00200000, "ELF .text (game EXE code)"),
        (0x00200000, 0x00400000, "ELF .data / .bss (game EXE data)"),
        (0x00400000, 0x01000000, "Game heap / dynamic allocations"),
        (0x01000000, 0x01800000, "Upper heap (large buffers)"),
        (0x01800000, 0x01FC0000, "Stack / high memory"),
        (0x01FC0000, 0x02000000, "Scratchpad / reserved"),
        (0x02000000, 0x10000000, "Beyond EE RAM (save state blob)"),
    ]
    for start, end, desc in regions:
        if start <= addr < end:
            return desc
    return "Unknown region"


def analyze_all_results(all_results):
    """Print comprehensive analysis of all found font data."""
    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY — Font Atlas Locations in EE RAM")
    print("=" * 70)

    if not all_results:
        print("\n  No font data found in RAM.")
        print("  Possible reasons:")
        print("    - Font atlases may be in GS VRAM (4MB, separate from EE RAM)")
        print("    - Data may be swizzled/transformed before upload to GS")
        print("    - The screen may not have these resources loaded yet")
        print("    - The save state format may need different extraction")
        return

    print(f"\n  {'Resource':<20} {'RAM Address':>12}  {'Match Type':<18} {'Region'}")
    print(f"  {'-'*20} {'-'*12}  {'-'*18} {'-'*30}")

    for label in sorted(all_results.keys()):
        result = all_results[label]
        if result is None:
            print(f"  {label:<20} {'NOT FOUND':>12}")
            continue
        match_type, addr = result
        region = classify_address(addr, label)
        print(f"  {label:<20} 0x{addr:08X}  {match_type:<18} {region}")

    # Group by resource
    print("\n  --- Detailed Analysis ---")

    # R2100 sub-blocks
    r2100_results = {k: v for k, v in all_results.items() if k.startswith('R2100') and v}
    if r2100_results:
        addrs = [v[1] for v in r2100_results.values()]
        print(f"\n  R2100 (chargen stat kanji atlas):")
        print(f"    {len(r2100_results)} of 4 sub-blocks found in RAM")
        if len(addrs) >= 2:
            for i in range(1, len(addrs)):
                diff = addrs[i] - addrs[i-1]
                print(f"    Sub {i-1} -> Sub {i} spacing: {diff:,} bytes (0x{diff:X})")
        if addrs:
            base = min(addrs)
            print(f"    Base address: 0x{base:08X} -> {classify_address(base, 'R2100')}")

    # R1272
    if 'R1272' in all_results and all_results['R1272']:
        _, addr = all_results['R1272']
        print(f"\n  R1272 (main dialogue font, 256x512 PSMT4):")
        print(f"    Found at RAM 0x{addr:08X}")
        print(f"    Region: {classify_address(addr, 'R1272')}")
        print(f"    Size in RAM: 65,536 bytes (0x10000)")

    # R1188
    if 'R1188' in all_results and all_results['R1188']:
        _, addr = all_results['R1188']
        print(f"\n  R1188 (name entry font, 1024x1024 PSMT4):")
        print(f"    Found at RAM 0x{addr:08X}")
        print(f"    Region: {classify_address(addr, 'R1188')}")
        print(f"    Size in RAM: 524,288 bytes (0x80000)")

    # Cross-resource analysis
    found_addrs = {k: v[1] for k, v in all_results.items() if v}
    if len(found_addrs) >= 2:
        print(f"\n  --- Cross-Resource Distances ---")
        keys = sorted(found_addrs.keys())
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                diff = found_addrs[keys[j]] - found_addrs[keys[i]]
                print(f"    {keys[i]} -> {keys[j]}: {diff:,} bytes (0x{diff:X})")


def dump_context(ram, all_results):
    """Dump hex context around each found location."""
    print("\n" + "=" * 70)
    print("  CONTEXT DUMPS (hex around each found location)")
    print("=" * 70)

    sizes = {
        'R1272': R1272_PIXEL_SIZE,
        'R1188': R1188_PIXEL_SIZE,
    }
    for i in range(4):
        sizes[f'R2100_sub{i}'] = R2100_PIXEL_SIZE

    for label in sorted(all_results.keys()):
        result = all_results[label]
        if result is None:
            continue
        _, addr = result
        pixel_size = sizes.get(label, 32768)

        # Show 128 bytes before (resource header / GIF tags)
        pre_size = 128
        if addr >= pre_size:
            pre = ram[addr - pre_size:addr]
            print(f"\n  {label}: {pre_size} bytes BEFORE pixel data (headers/GIF tags):")
            for row in range(0, pre_size, 16):
                hex_str = ' '.join(f'{b:02x}' for b in pre[row:row+16])
                asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in pre[row:row+16])
                print(f"    0x{addr-pre_size+row:08X}: {hex_str}  {asc}")

        # Show 64 bytes after pixel data ends
        end = addr + pixel_size
        if end + 64 <= len(ram):
            post = ram[end:end + 64]
            print(f"  {label}: 64 bytes AFTER pixel data (offset 0x{end:08X}):")
            for row in range(0, 64, 16):
                hex_str = ' '.join(f'{b:02x}' for b in post[row:row+16])
                print(f"    0x{end+row:08X}: {hex_str}")


def main():
    if len(sys.argv) < 2:
        print("PCSX2 Save State Font Atlas Searcher")
        print("=" * 45)
        print()
        print("Searches EE RAM for R2100, R1272, and R1188 font pixel data.")
        print()
        print("Usage: python tools/search_save_state.py <savestate.p2s>")
        print()
        print("INSTRUCTIONS:")
        print("  1. Boot the v9 ISO FRESH from the title screen")
        print("     (do NOT load save states from older builds!)")
        print("  2. Navigate to the character creation stat screen")
        print("     (where the kanji/English stat labels appear)")
        print("  3. Press F1 in PCSX2 to create a save state")
        print("     (save states go to the PCSX2/sstates/ directory)")
        print("  4. Run this script with the .p2s file path")
        print()

        # List available save states
        sstates_dir = os.path.join(
            os.path.expanduser('~'),
            'OneDrive - Berner Fachhochschule', 'Dokumente', 'PCSX2', 'sstates'
        )
        if os.path.isdir(sstates_dir):
            p2s_files = sorted(
                [f for f in os.listdir(sstates_dir) if f.endswith('.p2s')],
                key=lambda f: os.path.getmtime(os.path.join(sstates_dir, f)),
                reverse=True
            )
            if p2s_files:
                print(f"  Found save states in: {sstates_dir}")
                for f in p2s_files[:10]:
                    size = os.path.getsize(os.path.join(sstates_dir, f))
                    print(f"    {f}  ({size/1024/1024:.1f} MB)")
                if len(p2s_files) > 10:
                    print(f"    ... and {len(p2s_files)-10} more")
            else:
                print(f"  Save state directory exists: {sstates_dir}")
                print("  (no .p2s files found yet - create one with F1 in PCSX2)")
        else:
            print(f"  Expected save state directory not found:")
            print(f"    {sstates_dir}")

        print()
        print("  PCSX2 serial for this game: SLPM-65378")
        print("  Save states are named: SLPM-65378 (XXX).p2s")
        sys.exit(0)

    p2s_path = sys.argv[1]
    if not os.path.exists(p2s_path):
        print(f"ERROR: File not found: {p2s_path}")
        sys.exit(1)

    # ── Load font pixel signatures ──
    print("Loading font resource pixel signatures...")
    sigs = load_font_signatures()
    if not sigs:
        print("ERROR: No font resource data found.")
        print("  Expected build resources in: " + BUILD_RES)
        print("  Or extracted resources in: " + EXTRACTED_RAW)
        sys.exit(1)
    print(f"  Total signatures: {len(sigs)}")

    # ── Extract RAM from save state ──
    ram = extract_ee_ram_from_p2s(p2s_path)
    if ram is None:
        print("ERROR: Could not extract data from save state")
        sys.exit(1)

    # For zstd format, the full decompressed blob contains EE RAM embedded.
    # EE RAM is 32MB. Try to locate it within the blob if blob > 32MB.
    EE_RAM_SIZE = 32 * 1024 * 1024
    if len(ram) > EE_RAM_SIZE * 2:
        print(f"\n  Decompressed blob is {len(ram)/1024/1024:.1f} MB (contains multiple sections)")
        print(f"  Searching the ENTIRE blob for font data...")
        print(f"  (EE RAM is somewhere within these {len(ram)/1024/1024:.1f} MB)")

    # ── Search for all font resources ──
    all_results = {}
    for label in sorted(sigs.keys()):
        pixels, desc = sigs[label]
        result = search_for_data(ram, label, pixels, desc)
        all_results[label] = result

    # ── Analysis ──
    analyze_all_results(all_results)
    dump_context(ram, all_results)

    # ── Final guidance ──
    found_any = any(v is not None for v in all_results.values())
    print("\n" + "=" * 70)
    if found_any:
        print("  NEXT STEPS:")
        print("  The RAM addresses above tell us where the game loaded each font.")
        print("  Cross-reference with the EXE's file loading code to determine")
        print("  which PACKDATA resource provides the data at each address.")
        print()
        print("  Key questions answered by this data:")
        print("    - Is the chargen stat font from R2100 or loaded elsewhere?")
        print("    - Where does R1272 (dialogue font) live in RAM?")
        print("    - Is R1188 (name entry font) loaded during chargen?")
    else:
        print("  NO FONT DATA FOUND IN EE RAM.")
        print()
        print("  The font pixel data may be:")
        print("    1. Already uploaded to GS VRAM (4MB, separate from EE RAM)")
        print("       -> The game may DMA the data directly from disc to GS")
        print("    2. Transformed/swizzled before use")
        print("       -> Try searching for the GIF header bytes instead")
        print("    3. Not loaded on this particular game screen")
        print("       -> Try creating a save state at a different point")
    print("=" * 70)


if __name__ == '__main__':
    main()
