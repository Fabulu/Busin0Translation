"""Search PCSX2 save state (.p2s) for R2100 sub-block pixel data in EE RAM.

PCSX2 .p2s files are ZIP archives containing multiple entries. The EE RAM
(32 MB) is stored in an entry called "eeMemory.bin" (or similar). This script
extracts that entry and searches for known R2100 pixel signatures to find
where the game loaded the font atlas in memory.

Usage:
    python tools/search_savestate_ram.py <path_to_savestate.p2s>

Steps for the user:
    1. Boot the game fresh (do NOT load save states from older builds)
    2. Navigate to the character creation stat screen (where kanji labels appear)
    3. Create a save state: F1 (or Shift+F2 to pick a slot)
       - Save states go to the PCSX2 sstates/ directory
    4. Run this script on the .p2s file
"""
import sys
import os
import zipfile
import struct
import io
import zstandard  # PCSX2 1.7+ uses zstd compression

# Path to extracted R2100 sub-block pixel files
PIXELS_DIR = r'C:\Programmieren\wizardrytranslation\extracted\packdata_raw'

def load_r2100_pixels():
    """Load all 4 R2100 sub-block pixel files."""
    subs = []
    for i in range(4):
        path = os.path.join(PIXELS_DIR, f'r2100_sub{i}_pixels.bin')
        if os.path.exists(path):
            data = open(path, 'rb').read()
            subs.append((i, data))
            print(f"  Loaded sub {i}: {len(data)} bytes")
        else:
            print(f"  WARNING: {path} not found")
    return subs


def extract_ee_ram_from_p2s(p2s_path):
    """Extract EE RAM from a PCSX2 save state.

    PCSX2 save states can be:
    - ZIP archives (older PCSX2 versions)
    - Zstandard-compressed archives (PCSX2 1.7+/Qt)

    The EE RAM is typically in an entry called 'eeMemory.bin'.
    """
    print(f"\nOpening save state: {p2s_path}")
    file_size = os.path.getsize(p2s_path)
    print(f"  File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    raw = open(p2s_path, 'rb').read()

    # Check magic bytes
    magic = raw[:4]
    print(f"  Magic: {magic.hex()} ({magic!r})")

    # Try ZIP first
    if magic[:2] == b'PK':
        print("  Format: ZIP archive")
        return extract_from_zip(p2s_path)

    # Try zstd (PCSX2 Qt 1.7+)
    if magic == b'\x28\xb5\x2f\xfd':
        print("  Format: Zstandard compressed")
        return extract_from_zstd(raw)

    # Could be raw or another format - try treating the whole thing as memory
    print(f"  Unknown format (magic: {magic.hex()})")
    print("  Attempting to treat as raw data and search anyway...")
    return raw


def extract_from_zip(p2s_path):
    """Extract EE RAM from a ZIP-format save state."""
    with zipfile.ZipFile(p2s_path, 'r') as zf:
        names = zf.namelist()
        print(f"  ZIP entries: {names}")

        # Look for EE memory
        ee_candidates = [n for n in names if 'ee' in n.lower() and 'mem' in n.lower()]
        if not ee_candidates:
            # Try any large entry (EE RAM is 32MB)
            ee_candidates = []
            for n in names:
                info = zf.getinfo(n)
                print(f"    {n}: {info.file_size:,} bytes")
                if info.file_size >= 32 * 1024 * 1024:
                    ee_candidates.append(n)

        if not ee_candidates:
            print("  ERROR: Could not find EE RAM entry in ZIP")
            print("  Available entries:")
            for n in names:
                info = zf.getinfo(n)
                print(f"    {n}: {info.file_size:,} bytes")
            return None

        entry = ee_candidates[0]
        print(f"  Extracting: {entry}")
        return zf.read(entry)


def extract_from_zstd(raw_data):
    """Extract EE RAM from a zstd-compressed save state.

    PCSX2 Qt uses zstd. The decompressed data is a binary blob containing
    multiple sections. EE RAM (32MB = 0x02000000) is typically one of the
    larger sections.
    """
    dctx = zstandard.ZstdDecompressor()
    try:
        decompressed = dctx.decompress(raw_data, max_output_size=256 * 1024 * 1024)
    except Exception as e:
        print(f"  Zstd decompression failed: {e}")
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


def search_for_pixels(ram, sub_pixels_list):
    """Search RAM for R2100 sub-block pixel data."""
    print(f"\nSearching {len(ram):,} bytes of RAM...")

    results = {}

    for sub_idx, pixels in sub_pixels_list:
        print(f"\n--- Sub-block {sub_idx} ({len(pixels)} bytes) ---")

        # Try exact match of full pixel data
        pos = ram.find(pixels)
        if pos >= 0:
            print(f"  EXACT MATCH at offset 0x{pos:08X} ({pos:,})")
            results[sub_idx] = ('exact', pos)
            continue

        # Try matching shorter signatures at various positions
        sig_lengths = [256, 128, 64, 32, 16]
        sig_offsets = [0, 1152, 4096, 8192, 16384, 24576]

        found = False
        for sig_off in sig_offsets:
            if found:
                break
            for sig_len in sig_lengths:
                if sig_off + sig_len > len(pixels):
                    continue
                sig = pixels[sig_off:sig_off + sig_len]

                # Skip all-FF or all-00 signatures
                if len(set(sig)) <= 2:
                    continue

                pos = ram.find(sig)
                if pos >= 0:
                    # Found signature - calculate where the full block would start
                    block_start = pos - sig_off
                    print(f"  SIGNATURE MATCH: {sig_len}-byte sig from pixel offset {sig_off}")
                    print(f"    Found at RAM offset 0x{pos:08X}")
                    print(f"    Implied block start: 0x{block_start:08X}")

                    # Verify by checking another region
                    verify_off = 4096 if sig_off != 4096 else 8192
                    if verify_off + 16 <= len(pixels) and block_start + verify_off + 16 <= len(ram):
                        verify_sig = pixels[verify_off:verify_off + 16]
                        if ram[block_start + verify_off:block_start + verify_off + 16] == verify_sig:
                            print(f"    VERIFIED with cross-check at pixel offset {verify_off}")
                            results[sub_idx] = ('sig_verified', block_start)
                        else:
                            print(f"    Cross-check FAILED - may be false positive")
                            # Keep searching
                            next_pos = pos + 1
                            while next_pos < len(ram):
                                next_pos = ram.find(sig, next_pos)
                                if next_pos < 0:
                                    break
                                bs2 = next_pos - sig_off
                                if bs2 + verify_off + 16 <= len(ram):
                                    if ram[bs2 + verify_off:bs2 + verify_off + 16] == verify_sig:
                                        print(f"    FOUND VERIFIED at 0x{bs2:08X}")
                                        results[sub_idx] = ('sig_verified', bs2)
                                        found = True
                                        break
                                next_pos += 1
                            if not found:
                                results[sub_idx] = ('sig_unverified', block_start)
                    else:
                        results[sub_idx] = ('sig_only', block_start)

                    found = True
                    break

        if not found:
            print(f"  NOT FOUND in RAM")

            # Try swizzled search - the data might be stored in GS VRAM swizzle order
            # Use a smaller, more tolerant search
            for sig_off in [1152, 4096, 8192]:
                sig = pixels[sig_off:sig_off + 8]
                if len(set(sig)) <= 2:
                    continue
                pos = 0
                count = 0
                while pos < len(ram) and count < 5:
                    pos = ram.find(sig, pos)
                    if pos < 0:
                        break
                    count += 1
                    print(f"  8-byte match at 0x{pos:08X} (sig from offset {sig_off})")
                    pos += 1
                if count == 0:
                    print(f"  No 8-byte matches for sig from offset {sig_off}")

    return results


def analyze_results(results):
    """Analyze where R2100 sub-blocks were found in EE RAM."""
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    if not results:
        print("No R2100 sub-blocks found in RAM.")
        print("\nPossible reasons:")
        print("  - The font atlas is not loaded at this game screen")
        print("  - The data is stored swizzled/transformed in VRAM")
        print("  - The data is in GS memory (separate from EE RAM)")
        print("\nNote: GS (Graphics Synthesizer) has its own 4MB VRAM.")
        print("Textures actively used for rendering are in GS VRAM,")
        print("not EE RAM. The .p2s may include GS VRAM as a separate section.")
        return

    addrs = []
    for sub_idx in sorted(results.keys()):
        match_type, addr = results[sub_idx]
        print(f"  Sub {sub_idx}: 0x{addr:08X} ({match_type})")
        addrs.append(addr)

    if len(addrs) >= 2:
        print(f"\n  Spacing between sub-blocks:")
        for i in range(1, len(addrs)):
            diff = addrs[i] - addrs[i-1]
            print(f"    Sub {i-1} -> Sub {i}: {diff:,} bytes (0x{diff:X})")

    if addrs:
        print(f"\n  EE RAM range: 0x00000000 - 0x01FFFFFF (32 MB)")
        for sub_idx in sorted(results.keys()):
            _, addr = results[sub_idx]
            if addr < 0x02000000:
                print(f"  Sub {sub_idx} at 0x{addr:08X} is in EE RAM")
            elif addr < 0x02800000:
                print(f"  Sub {sub_idx} at 0x{addr:08X} might be in scratchpad or IOP RAM")
            else:
                print(f"  Sub {sub_idx} at 0x{addr:08X} is outside EE RAM - may be GS VRAM in dump")


def search_for_gs_vram_entry(raw_data):
    """Look for GS VRAM section markers in the save state data."""
    markers = [b'gsMemory', b'GS', b'vram', b'VRAM', b'gsRegs']
    print("\nSearching for GS-related section markers...")
    for marker in markers:
        pos = 0
        while True:
            pos = raw_data.find(marker, pos)
            if pos < 0:
                break
            context = raw_data[max(0,pos-8):pos+len(marker)+8]
            print(f"  Found '{marker.decode('ascii', errors='replace')}' at offset 0x{pos:08X}")
            print(f"    Context: {context.hex()}")
            pos += 1


def main():
    if len(sys.argv) < 2:
        print("PCSX2 Save State RAM Searcher")
        print("=" * 40)
        print()
        print("Usage: python tools/search_savestate_ram.py <savestate.p2s>")
        print()
        print("INSTRUCTIONS:")
        print("  1. Boot the game FRESH from the title screen")
        print("     (do NOT load old save states!)")
        print("  2. Navigate to the character creation stat screen")
        print("     (where the kanji stat labels appear)")
        print("  3. Press F1 in PCSX2 to create a save state")
        print("     (or Shift+F2 to choose a specific slot)")
        print()

        # Find save state directory
        sstates_dir = os.path.join(
            os.path.expanduser('~'),
            'OneDrive - Berner Fachhochschule', 'Dokumente', 'PCSX2', 'sstates'
        )
        if os.path.isdir(sstates_dir):
            p2s_files = [f for f in os.listdir(sstates_dir) if f.endswith('.p2s')]
            if p2s_files:
                print(f"  Found save states in: {sstates_dir}")
                for f in sorted(p2s_files):
                    size = os.path.getsize(os.path.join(sstates_dir, f))
                    print(f"    {f}  ({size/1024/1024:.1f} MB)")
            else:
                print(f"  Save state directory: {sstates_dir}")
                print("  (no .p2s files found yet)")

        print()
        print("  4. Run this script with the .p2s file path")
        print()
        print("The PCSX2 serial for this game is SLPM-65378.")
        print("Save states will be named like: SLPM-65378 (XXX).p2s")
        sys.exit(0)

    p2s_path = sys.argv[1]
    if not os.path.exists(p2s_path):
        print(f"ERROR: File not found: {p2s_path}")
        sys.exit(1)

    # Load R2100 pixel data
    print("Loading R2100 sub-block pixel signatures...")
    subs = load_r2100_pixels()
    if not subs:
        print("ERROR: No R2100 pixel files found")
        sys.exit(1)

    # Extract RAM from save state
    ram = extract_ee_ram_from_p2s(p2s_path)
    if ram is None:
        print("ERROR: Could not extract RAM from save state")
        sys.exit(1)

    # Also search for section markers
    raw_data = open(p2s_path, 'rb').read()
    search_for_gs_vram_entry(ram)

    # Search for R2100 pixels
    results = search_for_pixels(ram, subs)
    analyze_results(results)

    # Additional: dump surrounding context if found
    if results:
        print("\n" + "=" * 60)
        print("CONTEXT AROUND FOUND BLOCKS")
        print("=" * 60)
        for sub_idx in sorted(results.keys()):
            _, addr = results[sub_idx]
            # Check what's before the pixel data (should be GIF header)
            if addr >= 64:
                pre = ram[addr-64:addr]
                print(f"\n  64 bytes BEFORE sub {sub_idx} pixels (possible GIF header):")
                for row in range(0, 64, 16):
                    hex_str = ' '.join(f'{b:02x}' for b in pre[row:row+16])
                    print(f"    0x{addr-64+row:08X}: {hex_str}")

            # Check what's after
            end = addr + 32768
            if end + 64 <= len(ram):
                post = ram[end:end+64]
                print(f"  64 bytes AFTER sub {sub_idx} pixels:")
                for row in range(0, 64, 16):
                    hex_str = ' '.join(f'{b:02x}' for b in post[row:row+16])
                    print(f"    0x{end+row:08X}: {hex_str}")


if __name__ == '__main__':
    main()
