"""
Patch a single MSG resource: replace its glyph stream with an encoded English version.

Usage:
    python tools/patch_msg_resource.py <resource_index> <encoded_bin> [--output <path>]
    python tools/patch_msg_resource.py --batch <encoded_dir>

The tool reads the original raw resource from extracted/packdata_raw/,
replaces the glyph-stream portion with the supplied encoded data,
updates the sub-header payload_size, pads to a 2048-byte sector boundary,
and writes the result to build/packdata_resources/NNNN_typeNN.raw.
"""

import struct
import sys
import os
import math
import glob
import argparse

SECTOR = 2048
RAW_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "extracted", "packdata_raw"))
BUILD_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "packdata_resources"))


def find_raw_file(resource_index):
    """Locate the raw file for a given resource index."""
    pattern = os.path.join(RAW_DIR, f"{resource_index:04d}_type*.raw")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No raw file for resource {resource_index} in {RAW_DIR}")
    return matches[0]


def parse_type_code_from_filename(filename):
    """Extract integer type code from filename like 0042_type01.raw."""
    base = os.path.basename(filename)
    parts = base.split("_type")
    if len(parts) != 2:
        raise ValueError(f"Cannot parse type code from: {base}")
    tc_str = parts[1].replace(".raw", "").replace(".bin", "")
    return int(tc_str)


def count_sequential_table(payload):
    """
    Count sequential table entries at the start of the payload.
    Each entry is 16 bytes: [id(LE32), field1, field2, field3] where id = 1,2,3,...
    Returns 0 if no sequential table is present.
    """
    if len(payload) < 16:
        return 0
    first4 = struct.unpack_from("<I", payload, 0)[0]
    if first4 != 1:
        return 0
    max_entries = min(256, len(payload) // 16)
    count = 0
    for e in range(max_entries):
        off = e * 16
        if off + 16 > len(payload):
            break
        entry_id = struct.unpack_from("<I", payload, off)[0]
        if entry_id == e + 1:
            count = e + 1
        else:
            break
    return count


def detect_header_region(payload):
    """
    Detect how many bytes at the start of the payload constitute the
    preserved header (sequential table).

    The encoded_bin from Phase C replaces everything after the sequential
    table.  For Format A resources it includes a rebuilt offset table plus
    glyph data.  For Format B it includes the config block plus glyph data.

    Returns: byte offset where the replaceable region starts.
    """
    return count_sequential_table(payload) * 16


def patch_msg_resource(resource_index, encoded_bin_path, output_path=None):
    """
    Patch a MSG resource with an encoded English glyph stream.

    Steps:
      1. Read the original raw resource (16-byte sub-header + payload + padding)
      2. Detect sequential table (preserved header)
      3. Replace everything after sequential table with encoded_bin contents
      4. Update sub-header payload_size field
      5. Pad to 2048-byte sector boundary
      6. Write to build/packdata_resources/
    """
    # 1. Read original raw resource
    raw_path = find_raw_file(resource_index)
    with open(raw_path, "rb") as f:
        raw_data = f.read()

    type_code = parse_type_code_from_filename(raw_path)
    original_size = len(raw_data)

    if len(raw_data) < 16:
        raise ValueError(f"Raw file too small: {len(raw_data)} bytes")

    # 2. Parse sub-header (first 16 bytes of the raw block)
    h_zero1, h_payload_size, h_stride, h_zero2 = struct.unpack_from("<IIII", raw_data, 0)
    payload = raw_data[16:16 + h_payload_size]

    # 3. Detect header region (sequential table entries we must preserve)
    header_end = detect_header_region(payload)
    preserved_header = payload[:header_end]

    # 4. Read encoded English glyph stream
    with open(encoded_bin_path, "rb") as f:
        encoded_stream = f.read()

    # 5. Build new payload = preserved sequential table + encoded stream
    new_payload = preserved_header + encoded_stream
    new_payload_size = len(new_payload)

    # 6. Build new sub-header (preserve stride and zero2 from original)
    new_sub_header = struct.pack("<IIII", 0, new_payload_size, h_stride, h_zero2)

    # 7. Assemble full block and pad to sector boundary
    block = new_sub_header + new_payload
    needed_sectors = math.ceil(len(block) / SECTOR)
    pad_len = (needed_sectors * SECTOR) - len(block)
    padded_block = block + b"\x00" * pad_len

    # 8. Determine output path
    if output_path is None:
        os.makedirs(BUILD_DIR, exist_ok=True)
        out_fname = f"{resource_index:04d}_type{type_code:02d}.raw"
        output_path = os.path.join(BUILD_DIR, out_fname)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(padded_block)

    # Report
    old_sectors = original_size // SECTOR
    print(f"Patched resource {resource_index}:")
    print(f"  Original:  {h_payload_size} bytes payload, {old_sectors} sectors")
    print(f"  New:       {new_payload_size} bytes payload, {needed_sectors} sectors")
    print(f"  Header:    {header_end} bytes preserved (sequential table)")
    print(f"  Encoded:   {len(encoded_stream)} bytes")
    print(f"  Sector delta: {needed_sectors - old_sectors:+d}")
    print(f"  Written to: {output_path}")

    return output_path


def patch_all(encoded_dir, output_dir=None):
    """Batch mode: patch all resources that have encoded .bin files in encoded_dir."""
    if output_dir is None:
        output_dir = BUILD_DIR
    os.makedirs(output_dir, exist_ok=True)

    bin_files = glob.glob(os.path.join(encoded_dir, "*.bin"))
    if not bin_files:
        print(f"No .bin files found in {encoded_dir}")
        return

    patched = 0
    errors = []
    for bin_path in sorted(bin_files):
        base = os.path.basename(bin_path)
        try:
            resource_index = int(os.path.splitext(base)[0])
        except ValueError:
            print(f"  Skipping non-numeric filename: {base}")
            continue
        try:
            patch_msg_resource(resource_index, bin_path)
            patched += 1
        except Exception as e:
            errors.append((resource_index, str(e)))
            print(f"  ERROR resource {resource_index}: {e}")

    print(f"\nBatch Summary: {patched} patched, {len(errors)} errors")
    for idx, msg in errors:
        print(f"  Resource {idx}: {msg}")


def main():
    parser = argparse.ArgumentParser(description="Patch MSG resource with English glyph stream")
    parser.add_argument("resource_index", type=int, nargs="?", help="Resource index (e.g. 42)")
    parser.add_argument("encoded_bin", type=str, nargs="?", help="Path to encoded .bin file")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--batch", type=str, default=None, help="Batch: directory with {index}.bin files")
    args = parser.parse_args()

    if args.batch:
        patch_all(args.batch)
    elif args.resource_index is not None and args.encoded_bin is not None:
        patch_msg_resource(args.resource_index, args.encoded_bin, args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
