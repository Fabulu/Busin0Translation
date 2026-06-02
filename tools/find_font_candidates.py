#!/usr/bin/env python3
"""
find_font_candidates.py - Find ALL resources that could be font/glyph textures
=============================================================================

Searches the entire PACKDATA.DIG TOC (2883 entries) for resources that:
1. Have sizes consistent with PSMT4 or PSMT8 texture data
2. Match known font page structure patterns
3. Are loaded by the chargen/UI state machine

Also analyzes the EXE for:
- Font page resource table at VA 0x4CA710 (file 0x3CA790)
- Cell data page table at VA 0x4DB100 (file 0x3DB180)
- Chargen state machine resource loading
- Any other tables referencing PACKDATA resource IDs
"""

import struct
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
RAW_DIR = os.path.join(BASE, "extracted", "packdata_raw")

SECTOR = 2048
TOC_ENTRIES = 2883
OUTLIER_INDICES = {1370, 2100}

# Known font resources (already tested/identified)
KNOWN_FONT = {
    1272: "R1272 - Main dialogue font (PSMT4 256x512)",
    1188: "R1188 - Name entry/chargen UI atlas (PSMT4 1024x1024)",
    1269: "R1269 - Kanji page 1 (PSMT8 512x512)",
    1270: "R1270 - Kanji page 2 (PSMT8 256x512)",
    1271: "R1271 - Kanji page 3 (PSMT8 256x512)",
    1273: "R1273 - Kanji page 4 (PSMT8 256x512)",
    1274: "R1274 - Kanji page 5 (PSMT8 512x512)",
    1275: "R1275 - Kanji page 6 (PSMT8 512x512)",
    1276: "R1276 - Kanji page 7 (PSMT8 512x512)",
    1303: "R1303 - Kanji page 0 (PSMT8 512x512)",
}

# Resources already tested (zeroed) with no effect on stat labels
TESTED_NO_EFFECT = {
    2100: "R2100 - type04 texture, zeroed, NO effect on stat labels",
    1188: "R1188 - zeroed, NO effect (per user report)",
    # R1215-R1311 zeroed, no effect
}
for i in range(1215, 1312):
    TESTED_NO_EFFECT[i] = f"R{i} - kanji page, zeroed, no effect"

# Expected sizes for various texture formats
TEXTURE_SIZES = {
    "PSMT4 128x128": 8192,
    "PSMT4 256x128": 16384,
    "PSMT4 256x256": 32768,
    "PSMT4 256x512": 65536,
    "PSMT4 512x256": 65536,
    "PSMT4 512x512": 131072,
    "PSMT4 1024x512": 262144,
    "PSMT4 1024x1024": 524288,
    "PSMT8 128x128": 16384,
    "PSMT8 256x128": 32768,
    "PSMT8 256x256": 65536,
    "PSMT8 256x512": 131072,
    "PSMT8 512x256": 131072,
    "PSMT8 512x512": 262144,
    "PSMT8 1024x512": 524288,
    "PSMT8 1024x1024": 1048576,
}


def read_toc():
    """Read the full PACKDATA TOC."""
    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)

    entries = []
    for i in range(TOC_ENTRIES):
        so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)
        byte_size = sc * SECTOR
        entries.append({
            "index": i,
            "sector_offset": so,
            "sector_count": sc,
            "type_code": tc,
            "byte_size": byte_size,
        })
    return entries


def analyze_resource_header(dig_path, entry):
    """Read the first 64 bytes of a resource to check for texture markers."""
    offset = entry["sector_offset"] * SECTOR
    if offset == 0 or entry["sector_count"] == 0:
        return None
    with open(dig_path, "rb") as f:
        f.seek(offset)
        header = f.read(min(256, entry["byte_size"]))
    return header


def scan_exe_font_tables():
    """Extract resource IDs from known EXE font tables."""
    with open(EXE_PATH, "rb") as f:
        exe_data = f.read()

    results = {}

    # System A: Font page resource table at file offset 0x3CA790
    # 700 entries x 8 bytes = (resource_handle, duplicate)
    # resource_handle = PACKDATA_resource_id << 16
    print("\n=== SYSTEM A: Font Page Resource Table (EXE 0x3CA790, VA 0x4CA710) ===")
    print(f"{'PageIdx':>8} {'ResHandle':>12} {'ResID':>6} {'Notes'}")
    print("-" * 60)

    sys_a_resources = set()
    table_off = 0x3CA790
    for page_idx in range(700):
        off = table_off + page_idx * 8
        if off + 8 > len(exe_data):
            break
        handle1 = struct.unpack_from("<I", exe_data, off)[0]
        handle2 = struct.unpack_from("<I", exe_data, off + 4)[0]
        res_id = handle1 >> 16
        if handle1 != 0:
            note = ""
            if res_id in KNOWN_FONT:
                note = f" ** KNOWN: {KNOWN_FONT[res_id]}"
            if res_id in TESTED_NO_EFFECT:
                note += " [TESTED-NO-EFFECT]"
            print(f"{page_idx:>8} {handle1:#12x} {res_id:>6}{note}")
            sys_a_resources.add(res_id)

    results["system_a"] = sys_a_resources

    # System B: Cell data page table at file offset 0x3DB180
    # 30 entries x 8 bytes = (desc_idx: u32, cell_data_va: u32)
    print(f"\n=== SYSTEM B: Cell Data Page Table (EXE 0x3DB180, VA 0x4DB100) ===")
    print(f"{'Page':>5} {'DescIdx':>8} {'CellDataVA':>12} {'Notes'}")
    print("-" * 60)

    table_off_b = 0x3DB180
    for page in range(30):
        off = table_off_b + page * 8
        if off + 8 > len(exe_data):
            break
        desc_idx, cell_va = struct.unpack_from("<II", exe_data, off)
        if desc_idx != 0 or cell_va != 0:
            # Cell data VA -> file offset
            file_off = cell_va - 0x0FFF80 if cell_va > 0x100000 else 0
            print(f"{page:>5} {desc_idx:>8} {cell_va:#12x}  (file 0x{file_off:X})")

    # System B cell data entries reference VRAM addresses, not resource IDs directly
    # The VRAM block pointer tells us which texture atlas is used
    # Let's decode some cell data entries to find VRAM references
    print(f"\n=== SYSTEM B: Cell Data VRAM References ===")
    print("Scanning cell data entries for unique VRAM block addresses...")

    vram_blocks = set()
    for page in range(30):
        off = table_off_b + page * 8
        if off + 8 > len(exe_data):
            break
        desc_idx, cell_va = struct.unpack_from("<II", exe_data, off)
        if cell_va == 0:
            continue
        cell_file_off = cell_va - 0x0FFF80 if cell_va > 0x100000 else None
        if cell_file_off is None or cell_file_off + 800 > len(exe_data):
            continue

        # Each cell = 8 bytes: U(u8), V(u8), W(u8), Flag(u8), VRAM_addr(u16), extra(u16)
        # Read up to 100 cells per page
        for cell_idx in range(100):
            co = cell_file_off + cell_idx * 8
            if co + 8 > len(exe_data):
                break
            u, v, w, flag = struct.unpack_from("BBBB", exe_data, co)
            vram_addr, extra = struct.unpack_from("<HH", exe_data, co + 4)

            # Stop if we hit all zeros (end of page)
            if u == 0 and v == 0 and w == 0 and flag == 0 and vram_addr == 0:
                break

            vram_blocks.add(vram_addr)

    print(f"Unique VRAM block addresses referenced by System B cells: {len(vram_blocks)}")
    for vb in sorted(vram_blocks):
        vram_byte = vb * 256  # blocks are 256 bytes
        print(f"  VRAM block 0x{vb:04X} (byte offset 0x{vram_byte:06X})")

    results["system_b_vram"] = vram_blocks

    # Scan chargen state machine for resource loads
    # VA 0x4DC404 area - look for immediate values that could be resource IDs
    print(f"\n=== CHARGEN STATE MACHINE RESOURCE LOADS ===")
    print("Scanning EXE for LUI/ORI patterns loading resource IDs near chargen code...")

    # Search for addiu/ori instructions that load values in the range 1000-2900
    # (valid PACKDATA resource indices)
    # Common MIPS patterns:
    #   LUI $reg, 0  ; ORI $reg, $reg, <resource_id>
    #   ADDIU $reg, $zero, <resource_id>

    chargen_resources = set()
    # Scan the chargen code region (VA 0x2ED000-0x2F6000 = file 0x1ED080-0x1F6080)
    scan_start = 0x1ED080
    scan_end = 0x1F6080

    for off in range(scan_start, min(scan_end, len(exe_data) - 4), 4):
        instr = struct.unpack_from("<I", exe_data, off)[0]

        # ADDIU $reg, $zero, imm16 (opcode 001001, rs=0)
        op = (instr >> 26) & 0x3F
        rs = (instr >> 21) & 0x1F
        imm = instr & 0xFFFF

        if op == 0x09 and rs == 0 and 32 <= imm <= 2882:  # ADDIU $reg, $zero, resource_id
            rt = (instr >> 16) & 0x1F
            chargen_resources.add(imm)

        # ORI $reg, $zero, imm16 (opcode 001101, rs=0)
        if op == 0x0D and rs == 0 and 32 <= imm <= 2882:
            chargen_resources.add(imm)

    if chargen_resources:
        print(f"Potential resource IDs loaded in chargen code region:")
        for rid in sorted(chargen_resources):
            note = ""
            if rid in KNOWN_FONT:
                note = f" ** {KNOWN_FONT[rid]}"
            print(f"  R{rid}{note}")

    results["chargen_resources"] = chargen_resources

    # Also scan the broader UI/rendering code for resource IDs
    # VA 0x300000-0x310000 = file 0x200080-0x210080 (text/font system)
    font_sys_resources = set()
    scan_start2 = 0x200080
    scan_end2 = 0x210080

    print(f"\n=== FONT SYSTEM CODE RESOURCE LOADS (VA 0x300000-0x310000) ===")
    for off in range(scan_start2, min(scan_end2, len(exe_data) - 4), 4):
        instr = struct.unpack_from("<I", exe_data, off)[0]
        op = (instr >> 26) & 0x3F
        rs = (instr >> 21) & 0x1F
        imm = instr & 0xFFFF

        if op == 0x09 and rs == 0 and 1000 <= imm <= 2000:
            font_sys_resources.add(imm)
        if op == 0x0D and rs == 0 and 1000 <= imm <= 2000:
            font_sys_resources.add(imm)

    if font_sys_resources:
        print(f"Resource IDs in font system code:")
        for rid in sorted(font_sys_resources):
            note = ""
            if rid in KNOWN_FONT:
                note = f" ** {KNOWN_FONT[rid]}"
            print(f"  R{rid}{note}")

    results["font_sys_resources"] = font_sys_resources

    return results


def find_texture_candidates(toc):
    """Find all resources with sizes matching known texture formats."""
    print("\n=== TEXTURE SIZE CANDIDATES ===")
    print(f"{'Index':>6} {'Type':>5} {'ByteSize':>10} {'Sectors':>8} {'PixelData':>10} {'Format Match'}")
    print("-" * 80)

    candidates = []

    for entry in toc:
        idx = entry["index"]
        bs = entry["byte_size"]
        tc = entry["type_code"]

        if bs == 0:
            continue

        # Check if byte_size minus plausible headers matches a texture size
        for header_size in [0, 16, 32, 64, 128, 160, 192, 256, 512, 1024, 2048, 3072]:
            pixel_data = bs - header_size
            for fmt_name, fmt_size in TEXTURE_SIZES.items():
                if pixel_data == fmt_size:
                    tested = " [TESTED-NO-EFFECT]" if idx in TESTED_NO_EFFECT else ""
                    known = f" ** {KNOWN_FONT[idx]}" if idx in KNOWN_FONT else ""
                    candidates.append({
                        "index": idx,
                        "type_code": tc,
                        "byte_size": bs,
                        "header_size": header_size,
                        "pixel_data": pixel_data,
                        "format": fmt_name,
                        "tested": idx in TESTED_NO_EFFECT,
                        "known": idx in KNOWN_FONT,
                    })
                    if not (idx in TESTED_NO_EFFECT and idx not in KNOWN_FONT):
                        print(f"{idx:>6} {tc:>5} {bs:>10,} {entry['sector_count']:>8} {pixel_data:>10,} {fmt_name} (hdr={header_size}){tested}{known}")

    return candidates


def check_type01_sub_headers(toc):
    """For type-01 resources, check if the sub-header contains texture metadata."""
    print("\n=== TYPE-01 RESOURCE SUB-HEADERS (potential textures) ===")
    print("Type-01 resources have a 16-byte sub-header followed by payload.")
    print(f"{'Index':>6} {'Size':>8} {'sub[0]':>10} {'sub[1](payld)':>12} {'sub[2]':>10} {'sub[3]':>10} {'Payload Fmt Match'}")
    print("-" * 100)

    interesting = []

    with open(DIG_PATH, "rb") as f:
        for entry in toc:
            idx = entry["index"]
            tc = entry["type_code"]
            bs = entry["byte_size"]

            if tc != 1 or bs < 32 or idx in OUTLIER_INDICES:
                continue

            offset = entry["sector_offset"] * SECTOR
            f.seek(offset)
            data = f.read(min(32, bs))
            if len(data) < 32:
                continue

            sub = struct.unpack_from("<IIII", data, 0)
            payload_size = sub[1]

            # Check if payload matches known texture sizes
            for fmt_name, fmt_size in TEXTURE_SIZES.items():
                # Payload includes GS header (~160-256 bytes) + pixel data
                for gs_header in [0, 96, 128, 160, 192, 256]:
                    if payload_size - gs_header == fmt_size:
                        tested = " [TESTED]" if idx in TESTED_NO_EFFECT else ""
                        known = f" ** {KNOWN_FONT[idx]}" if idx in KNOWN_FONT else ""
                        note = ""
                        if 30000 <= bs <= 600000 and idx not in TESTED_NO_EFFECT:
                            note = " <<< UNTESTED CANDIDATE"
                        print(f"{idx:>6} {bs:>8,} {sub[0]:#10x} {payload_size:>12,} {sub[2]:#10x} {sub[3]:#10x} {fmt_name} (gs_hdr={gs_header}){tested}{known}{note}")
                        interesting.append(idx)
                        break

    return interesting


def check_r1188_details(toc):
    """Deep analysis of R1188 - check if TOC index 1188 is the REAL R1188."""
    print("\n=== R1188 VERIFICATION ===")

    entry = toc[1188]
    print(f"TOC[1188]: sector_offset=0x{entry['sector_offset']:X}, sectors={entry['sector_count']}, type={entry['type_code']}, size={entry['byte_size']:,}")

    # Read and check the actual data
    with open(DIG_PATH, "rb") as f:
        offset = entry["sector_offset"] * SECTOR
        f.seek(offset)
        header = f.read(min(512, entry["byte_size"]))

    print(f"First 64 bytes: {header[:64].hex()}")

    if len(header) >= 16 and entry["type_code"] == 1:
        sub = struct.unpack_from("<IIII", header, 0)
        print(f"Sub-header: [{sub[0]:#x}, {sub[1]:#x}, {sub[2]:#x}, {sub[3]:#x}]")
        print(f"Payload size: {sub[1]:,} bytes")

        # Check payload for texture size match
        ps = sub[1]
        for gs_hdr in [0, 96, 128, 160, 192, 256, 3072]:
            pixel_data = ps - gs_hdr
            for fmt_name, fmt_size in TEXTURE_SIZES.items():
                if pixel_data == fmt_size:
                    print(f"  -> Matches {fmt_name} with {gs_hdr}-byte GS header")

    # Also check nearby indices
    print(f"\nNearby TOC entries for context:")
    for i in range(max(0, 1185), min(TOC_ENTRIES, 1195)):
        e = toc[i]
        note = ""
        if i in KNOWN_FONT:
            note = f" ** {KNOWN_FONT[i]}"
        if i in TESTED_NO_EFFECT:
            note += " [TESTED]"
        print(f"  TOC[{i}]: type={e['type_code']:>3}, size={e['byte_size']:>10,}, sectors={e['sector_count']:>5}{note}")


def scan_exe_for_resource_1188():
    """Find ALL references to resource 1188 in the EXE."""
    print("\n=== EXE REFERENCES TO RESOURCE INDEX 1188 ===")

    with open(EXE_PATH, "rb") as f:
        exe_data = f.read()

    target = 1188  # 0x4A4

    # Search for ADDIU $reg, $zero, 0x4A4
    # ADDIU opcode = 001001, rs=00000, rt=XXXXX, imm=0x04A4
    # = 0x240X04A4 where X is rt register
    print(f"Searching for MIPS instructions loading immediate 0x{target:04X} ({target})...")

    for off in range(0, len(exe_data) - 4, 4):
        instr = struct.unpack_from("<I", exe_data, off)[0]
        op = (instr >> 26) & 0x3F
        rs = (instr >> 21) & 0x1F
        rt = (instr >> 16) & 0x1F
        imm = instr & 0xFFFF

        # ADDIU $rt, $zero, 1188
        if op == 0x09 and rs == 0 and imm == target:
            va = off + 0x0FFF80
            print(f"  ADDIU ${rt}, $zero, {target} at file 0x{off:X} (VA 0x{va:X})")

        # ORI $rt, $zero, 1188
        if op == 0x0D and rs == 0 and imm == target:
            va = off + 0x0FFF80
            print(f"  ORI ${rt}, $zero, {target} at file 0x{off:X} (VA 0x{va:X})")

        # LUI $rt, 0x04A4 (unlikely but check)
        if op == 0x0F and imm == target:
            va = off + 0x0FFF80
            print(f"  LUI ${rt}, {target} at file 0x{off:X} (VA 0x{va:X})")

    # Also check data section for the value 1188 as uint16 or uint32
    print(f"\nSearching data sections for uint16 value {target} (0x{target:04X})...")

    # The resource handle format is resource_id << 16
    handle = target << 16  # 0x04A40000

    for off in range(0, len(exe_data) - 4, 4):
        val = struct.unpack_from("<I", exe_data, off)[0]
        if val == handle:
            va = off + 0x0FFF80
            # Check if this is in the font page resource table
            in_table = "FONT_TABLE" if 0x3CA790 <= off < 0x3CA790 + 700 * 8 else ""
            print(f"  Handle 0x{handle:08X} at file 0x{off:X} (VA 0x{va:X}) {in_table}")


def scan_exe_descriptor_tables():
    """Look for descriptor/struct tables that reference R1188's VRAM addresses."""
    print("\n=== SCANNING EXE FOR R1188 VRAM BLOCK REFERENCES ===")

    with open(EXE_PATH, "rb") as f:
        exe_data = f.read()

    # R1188 uploads to VRAM starting around block 0xA000-0xB000
    # The cell data entries reference VRAM blocks like 0xAD70, 0xAB10, etc.
    # These are the stat label VRAM addresses from font_page_dispatch.md
    stat_vram = {
        0xAD70: "STR (glyph 346)",
        0xAB10: "FTH1/shin (glyph 308)",
        0xABD0: "FTH3/kokoro (glyph 320)",
        0xADF0: "FTH2/kou (glyph 354)",
    }

    for vram_block, label in stat_vram.items():
        # Search for this uint16 value in the EXE data section
        target_bytes = struct.pack("<H", vram_block)
        count = 0
        for off in range(0x300000, min(0x400000, len(exe_data) - 2)):
            if exe_data[off:off+2] == target_bytes:
                va = off + 0x0FFF80
                print(f"  VRAM 0x{vram_block:04X} ({label}) at file 0x{off:X} (VA 0x{va:X})")
                count += 1
                if count > 5:
                    print(f"    ... and more")
                    break


def check_chargen_resource_loads_detailed():
    """Disassemble chargen code to find JAL to resource load functions."""
    print("\n=== CHARGEN CODE: JAL TO RESOURCE LOAD FUNCTIONS ===")

    with open(EXE_PATH, "rb") as f:
        exe_data = f.read()

    # Known resource load functions:
    # 0x180EF0 - resource flag check
    # 0x180F20 - resource flag set
    # 0x180FD0 - full resource load
    # 0x127078 - get_sub_resource

    load_funcs = {
        0x180EF0: "resource_flag_check",
        0x180F20: "resource_flag_set",
        0x180FD0: "resource_load_full",
        0x127078: "get_sub_resource",
    }

    # Scan chargen code region for JAL instructions to these functions
    # JAL target = (instr & 0x03FFFFFF) << 2
    scan_regions = [
        (0x1ED080, 0x1F6080, "Chargen main (VA 0x2ED000-0x2F6000)"),
        (0x200080, 0x210080, "Font system (VA 0x300000-0x310000)"),
        (0x020080, 0x030080, "Early init (VA 0x120000-0x130000)"),
    ]

    for scan_start, scan_end, region_name in scan_regions:
        print(f"\n  Region: {region_name}")
        for off in range(scan_start, min(scan_end, len(exe_data) - 4), 4):
            instr = struct.unpack_from("<I", exe_data, off)[0]
            op = (instr >> 26) & 0x3F

            if op == 0x03:  # JAL
                target = (instr & 0x03FFFFFF) << 2
                if target in load_funcs:
                    va = off + 0x0FFF80
                    # Look at the preceding instruction for the argument
                    if off >= 4:
                        prev_instr = struct.unpack_from("<I", exe_data, off - 4)[0]
                        prev_op = (prev_instr >> 26) & 0x3F
                        prev_rs = (prev_instr >> 21) & 0x1F
                        prev_imm = prev_instr & 0xFFFF
                        arg_str = ""
                        if prev_op == 0x09 and prev_rs == 0:  # ADDIU $rt, $zero, imm
                            arg_str = f" (arg={prev_imm}, R{prev_imm})"
                        elif prev_op == 0x0D and prev_rs == 0:  # ORI
                            arg_str = f" (arg={prev_imm}, R{prev_imm})"
                        print(f"    VA 0x{va:X}: JAL {load_funcs[target]}{arg_str}")


def analyze_untested_candidates(toc, exe_results):
    """Produce a final list of untested texture resource candidates."""
    print("\n" + "=" * 80)
    print("  FINAL ANALYSIS: UNTESTED FONT/TEXTURE CANDIDATES")
    print("=" * 80)

    # Combine all known resource IDs from EXE tables
    all_exe_refs = set()
    for key in ["system_a", "chargen_resources", "font_sys_resources"]:
        if key in exe_results:
            all_exe_refs |= exe_results[key]

    # Find resources in the size range for font textures that haven't been tested
    print("\nResources with texture-compatible sizes NOT yet tested:")
    print(f"{'Index':>6} {'Type':>5} {'Size':>10} {'InEXE':>6} {'Notes'}")
    print("-" * 70)

    for entry in toc:
        idx = entry["index"]
        bs = entry["byte_size"]
        tc = entry["type_code"]

        if bs == 0 or idx in OUTLIER_INDICES:
            continue
        if idx in TESTED_NO_EFFECT:
            continue

        # Check if this resource's pixel data matches a texture size
        is_texture_candidate = False
        matching_fmt = ""
        for header_size in [0, 16, 32, 64, 128, 160, 192, 256, 512, 1024, 2048, 3072]:
            pixel_data = bs - header_size
            for fmt_name, fmt_size in TEXTURE_SIZES.items():
                if pixel_data == fmt_size:
                    is_texture_candidate = True
                    matching_fmt = f"{fmt_name} (hdr={header_size})"
                    break
            if is_texture_candidate:
                break

        if not is_texture_candidate:
            continue

        in_exe = "YES" if idx in all_exe_refs else "no"
        known = f" ** {KNOWN_FONT[idx]}" if idx in KNOWN_FONT else ""

        # Highlight resources near the chargen cluster (1150-1400) and system resources (0-100)
        priority = ""
        if 1150 <= idx <= 1400:
            priority = " [CHARGEN CLUSTER]"
        elif idx < 100:
            priority = " [SYSTEM RANGE]"
        elif idx in all_exe_refs:
            priority = " [EXE REFERENCED]"

        print(f"{idx:>6} {tc:>5} {bs:>10,} {in_exe:>6} {matching_fmt}{known}{priority}")


def main():
    print("=" * 80)
    print("  PACKDATA FONT RESOURCE HUNTER")
    print("  Searching 2883 resources for mystery stat label font")
    print("=" * 80)

    toc = read_toc()

    # 1. Full TOC overview by type
    print("\n=== TOC TYPE DISTRIBUTION ===")
    type_counts = {}
    for e in toc:
        tc = e["type_code"]
        type_counts[tc] = type_counts.get(tc, 0) + 1
    for tc in sorted(type_counts):
        print(f"  type {tc:>3}: {type_counts[tc]:>5} resources")

    # 2. Check R1188 in detail
    check_r1188_details(toc)

    # 3. Scan EXE font tables
    exe_results = scan_exe_font_tables()

    # 4. Find texture-size candidates
    candidates = find_texture_candidates(toc)

    # 5. Check type-01 sub-headers
    check_type01_sub_headers(toc)

    # 6. Scan EXE for R1188 references
    scan_exe_for_resource_1188()

    # 7. Check VRAM block references
    scan_exe_descriptor_tables()

    # 8. Chargen resource load analysis
    check_chargen_resource_loads_detailed()

    # 9. Final candidate list
    analyze_untested_candidates(toc, exe_results)

    print("\n\nDONE.")


if __name__ == "__main__":
    main()
