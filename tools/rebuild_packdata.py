"""
Rebuild PACKDATA.DIG from individual resource files with updated TOC.

Usage:
    python tools/rebuild_packdata.py [--output <path>]
    python tools/rebuild_packdata.py --verify [--verify-path <path>]

Reads the original PACKDATA.DIG header region, then for each of 2883 TOC
entries selects either a modified .raw from build/packdata_resources/ or the
original from extracted/packdata_raw/.  Writes resources sequentially with
updated TOC sector offsets and counts.

Output: build/PACKDATA.DIG (default)
"""

import struct
import sys
import os
import math
import glob
import json
import argparse

SECTOR = 2048
TOC_ENTRIES = 2883
HEADER_SECTORS = 125
HEADER_BYTES = HEADER_SECTORS * SECTOR   # 256,000 bytes
OUTLIER_INDICES = {1370, 2100}

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ORIGINAL_DIG = os.path.join(BASE_DIR, "extracted", "PACKDATA.DIG")
RAW_DIR = os.path.join(BASE_DIR, "extracted", "packdata_raw")
MODIFIED_DIR = os.path.join(BASE_DIR, "build", "packdata_resources")
MANIFEST_PATH = os.path.join(BASE_DIR, "extracted", "packdata_resources", "manifest.json")
DEFAULT_OUTPUT = os.path.join(BASE_DIR, "build", "PACKDATA.DIG")


def load_manifest():
    """Load the extraction manifest for original TOC metadata."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)
    manifest = {}
    for entry in entries:
        manifest[entry["index"]] = entry
    return manifest


def find_resource_file(index):
    """
    Find the resource file to use for a given index.
    Prefers modified .raw in build/packdata_resources/ over original.
    Returns (filepath, is_modified).
    """
    pattern = os.path.join(MODIFIED_DIR, f"{index:04d}_type*.raw")
    matches = glob.glob(pattern)
    if matches:
        return matches[0], True

    pattern = os.path.join(RAW_DIR, f"{index:04d}_type*.raw")
    matches = glob.glob(pattern)
    if matches:
        return matches[0], False

    raise FileNotFoundError(f"No resource file found for index {index}")


def read_original_toc():
    """Read the original TOC (2883 x 12 bytes) from PACKDATA.DIG."""
    with open(ORIGINAL_DIG, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
    toc = []
    for i in range(TOC_ENTRIES):
        so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)
        toc.append((so, sc, tc))
    return toc


def read_original_header_region():
    """Read the full header region (first 256,000 bytes) from PACKDATA.DIG."""
    with open(ORIGINAL_DIG, "rb") as f:
        return f.read(HEADER_BYTES)


def rebuild_packdata(output_path=None):
    """
    Rebuild PACKDATA.DIG with updated TOC and resource data.

    Algorithm:
      1. Read original header region (256,000 bytes)
      2. Read original TOC to get type codes and outlier entries
      3. For each non-outlier entry, load resource (modified or original)
      4. Compute new sector offsets sequentially
      5. Write new TOC + padding + all resources
    """
    if output_path is None:
        output_path = DEFAULT_OUTPUT

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print("Loading original TOC and manifest...")
    original_toc = read_original_toc()
    original_header = read_original_header_region()
    manifest = load_manifest()

    # Phase 1: Collect resource data and compute new TOC
    print("Phase 1: Loading resources and computing new TOC...")
    new_toc = [None] * TOC_ENTRIES
    resource_data = {}
    running_sector = HEADER_SECTORS
    modified_count = 0
    original_count = 0

    for i in range(TOC_ENTRIES):
        if i in OUTLIER_INDICES:
            new_toc[i] = original_toc[i]
            continue

        mentry = manifest.get(i)
        if mentry is None or mentry.get("skipped"):
            new_toc[i] = original_toc[i]
            continue

        try:
            filepath, is_modified = find_resource_file(i)
        except FileNotFoundError as e:
            print(f"  WARNING: {e} - preserving original TOC")
            new_toc[i] = original_toc[i]
            continue

        with open(filepath, "rb") as f:
            raw_block = f.read()

        if is_modified:
            modified_count += 1
        else:
            original_count += 1

        # Ensure sector alignment
        padded = raw_block
        remainder = len(padded) % SECTOR
        if remainder != 0:
            padded = padded + b"\x00" * (SECTOR - remainder)

        needed_sectors = len(padded) // SECTOR
        tc = original_toc[i][2]

        new_toc[i] = (running_sector, needed_sectors, tc)
        resource_data[i] = padded
        running_sector += needed_sectors

        if (i + 1) % 500 == 0:
            print(f"  Progress: {i + 1}/{TOC_ENTRIES}")

    print(f"  {modified_count} modified, {original_count} original")
    print(f"  Total sectors: {running_sector} ({running_sector * SECTOR:,} bytes)")

    # Phase 2: Write rebuilt file
    print(f"Phase 2: Writing {output_path}...")

    with open(output_path, "wb") as f:
        # Write new TOC
        toc_bytes = bytearray(TOC_ENTRIES * 12)
        for i in range(TOC_ENTRIES):
            so, sc, tc = new_toc[i]
            struct.pack_into("<III", toc_bytes, i * 12, so, sc, tc)
        f.write(toc_bytes)

        # Write rest of header region (preserves data after TOC)
        toc_size = TOC_ENTRIES * 12  # 34,596 bytes
        f.write(original_header[toc_size:])

        assert f.tell() == HEADER_BYTES, (
            f"Header region size mismatch: {f.tell()} != {HEADER_BYTES}"
        )

        # Write resources sequentially
        for i in range(TOC_ENTRIES):
            if i in OUTLIER_INDICES:
                continue
            if i not in resource_data:
                continue

            expected_offset = new_toc[i][0] * SECTOR
            current_pos = f.tell()
            if current_pos != expected_offset:
                if current_pos < expected_offset:
                    f.write(b"\x00" * (expected_offset - current_pos))
                else:
                    raise ValueError(
                        f"Resource {i}: pos {current_pos} > expected {expected_offset}"
                    )

            f.write(resource_data[i])

            if (i + 1) % 500 == 0:
                print(f"  Write progress: {i + 1}/{TOC_ENTRIES}")

        final_size = f.tell()

    orig_size = os.path.getsize(ORIGINAL_DIG)
    print(f"\nRebuild complete:")
    print(f"  Output: {output_path}")
    print(f"  Size: {final_size:,} bytes ({final_size // SECTOR} sectors)")
    print(f"  Original: {orig_size:,} bytes")
    print(f"  Delta: {final_size - orig_size:+,} bytes")
    return output_path


def verify_rebuild(rebuilt_path=None):
    """Quick verification of a rebuilt PACKDATA.DIG."""
    if rebuilt_path is None:
        rebuilt_path = DEFAULT_OUTPUT

    if not os.path.exists(rebuilt_path):
        print(f"File not found: {rebuilt_path}")
        return False

    file_size = os.path.getsize(rebuilt_path)
    print(f"Verifying {rebuilt_path} ({file_size:,} bytes)...")

    with open(rebuilt_path, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)

    errors = []
    prev_end = HEADER_SECTORS

    for i in range(TOC_ENTRIES):
        so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)

        if i in OUTLIER_INDICES:
            if so == 0 and sc == 0 and tc == 0:
                errors.append(f"Entry {i}: outlier is all zeros")
            continue

        end_byte = (so + sc) * SECTOR
        if end_byte > file_size:
            errors.append(f"Entry {i}: past EOF ({end_byte} > {file_size})")
            continue

        if so != prev_end and so >= HEADER_SECTORS:
            errors.append(f"Entry {i}: gap/overlap at sector {prev_end} -> {so}")

        if so >= HEADER_SECTORS:
            prev_end = so + sc

        # Spot-check sub-header
        with open(rebuilt_path, "rb") as fv:
            fv.seek(so * SECTOR)
            hdr = fv.read(16)
            if len(hdr) == 16:
                z1, ps, stride, z2 = struct.unpack("<IIII", hdr)
                if z1 != 0:
                    errors.append(f"Entry {i}: sub-header zero1 = {z1}")
                if ps > sc * SECTOR:
                    errors.append(f"Entry {i}: payload {ps} > block {sc * SECTOR}")

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
        return False
    else:
        print("Verification PASSED.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Rebuild PACKDATA.DIG")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-path", type=str, default=None)
    args = parser.parse_args()

    if args.verify:
        path = args.verify_path or args.output or DEFAULT_OUTPUT
        ok = verify_rebuild(path)
        sys.exit(0 if ok else 1)
    else:
        rebuild_packdata(args.output)


if __name__ == "__main__":
    main()
