#!/usr/bin/env python3
"""
Targeted NOP test for chargen stat label rendering.

Creates test ISOs that NOP specific JAL call sites in the chargen orchestrator
to identify which function renders stat label TEXT.

Call chain analysis:
  Chargen orchestrator (around 0x2F2500):
    0x2F2530: BEQ -> if flag set:
      0x2F2538: JAL 0x2F2240  (per-frame renderer - handles "phase 2" chargen)
    else:
      0x2F2548: JAL 0x2ED5E0  (chargen logic - game state transitions)
      0x2F2558: JAL 0x309870  (UI panel render - renders glyph tiles from tile array)
      0x2F2560: JAL 0x2F3450  (stat render - numbers only)
      0x2F2570: JAL 0x30CBE0  (some other render)

  Inside 0x2F2240 (per-frame renderer):
    0x2F22D0: JAL 0x30CD00  (state flag check, returns early if set)
    0x2F23F0: JAL 0x30AE20  (clears tile array buffer)
    ... many sub-calls for UI setup ...

  Inside 0x309870 (UI panel render):
    Iterates tile array, calls 0x306E20 per tile -> renders individual glyphs

VA to file offset: file_off = VA - 0x100000 + 0x80
"""

import shutil
import struct
import os

BASE_ISO = r"C:\Programmieren\wizardrytranslation\build\BUSIN0_EN_v37.iso"
EXE_PATH = r"C:\Programmieren\wizardrytranslation\build\SLPM_653.78_patched"
OUTPUT_DIR = r"C:\Programmieren\wizardrytranslation\build"

# EXE location in ISO (found from build system)
# The EXE is written at a specific LBA in the ISO. We need to find it.
# From patch_exe.py, the EXE is at the SLPM_653.78 file location in the ISO.

def va_to_file_offset(va):
    """Convert MIPS virtual address to EXE file offset."""
    return va - 0x100000 + 0x80

def find_exe_in_iso(iso_data):
    """Find the EXE start offset in the ISO by searching for the ELF header pattern."""
    # The PS2 EXE starts with MIPS code. Search for known bytes near the start.
    # Actually, let's search for "SLPM_653.78" in the ISO directory and find the LBA.
    # Or we can search for a known unique sequence from the EXE.

    # Read the first few bytes of the patched EXE
    with open(EXE_PATH, 'rb') as f:
        exe_header = f.read(64)

    # Search for this in the ISO
    pos = iso_data.find(exe_header)
    if pos >= 0:
        print(f"  Found EXE in ISO at offset 0x{pos:X} (LBA {pos // 2048})")
        return pos

    # Fallback: try searching sector by sector
    # PS2 ISOs use 2048-byte sectors, EXE typically starts at a sector boundary
    for lba in range(16, 30000):
        off = lba * 2048
        if iso_data[off:off+64] == exe_header:
            print(f"  Found EXE in ISO at LBA {lba} (offset 0x{off:X})")
            return off

    raise RuntimeError("Could not find EXE in ISO!")

def nop_jal_in_iso(iso_path, output_path, call_site_va, description):
    """
    NOP a JAL instruction at the given call site VA in the ISO's EXE.
    Replaces both the JAL and its delay slot with NOP.
    """
    print(f"\n{'='*60}")
    print(f"Creating: {os.path.basename(output_path)}")
    print(f"NOP'ing JAL at VA 0x{call_site_va:08X} ({description})")
    print(f"  File offset in EXE: 0x{va_to_file_offset(call_site_va):X}")

    # Copy ISO
    shutil.copy2(iso_path, output_path)

    with open(output_path, 'r+b') as f:
        iso_data = f.read()

    exe_offset = find_exe_in_iso(iso_data)

    # Calculate position in ISO
    exe_file_off = va_to_file_offset(call_site_va)
    iso_off = exe_offset + exe_file_off

    # Read current instruction to verify it's a JAL
    current = struct.unpack('<I', iso_data[iso_off:iso_off+4])[0]
    if (current >> 26) != 3:
        print(f"  WARNING: Instruction at VA 0x{call_site_va:08X} is NOT a JAL!")
        print(f"  Found: 0x{current:08X}")
        # Check if it's already NOP'd
        if current == 0:
            print(f"  (Already NOP'd)")
        return False

    target = ((current & 0x03FFFFFF) << 2) | (call_site_va & 0xF0000000)
    print(f"  Current: JAL 0x{target:08X} (raw: 0x{current:08X})")

    # Read delay slot
    delay = struct.unpack('<I', iso_data[iso_off+4:iso_off+8])[0]
    print(f"  Delay slot: 0x{delay:08X}")

    # NOP both JAL and delay slot
    nop = struct.pack('<I', 0x00000000)

    with open(output_path, 'r+b') as f:
        f.seek(iso_off)
        f.write(nop)  # NOP the JAL
        f.write(nop)  # NOP the delay slot

    print(f"  -> NOP'd JAL + delay slot at ISO offset 0x{iso_off:X}")
    print(f"  Output: {output_path}")
    return True


def main():
    if not os.path.exists(BASE_ISO):
        print(f"ERROR: Base ISO not found: {BASE_ISO}")
        return

    print("Targeted NOP Test for Chargen Stat Labels")
    print("=" * 60)
    print()
    print("Call chain in chargen orchestrator:")
    print("  0x2F2538: JAL 0x2F2240 (per-frame renderer, phase 2)")
    print("  0x2F2548: JAL 0x2ED5E0 (chargen logic)")
    print("  0x2F2558: JAL 0x309870 (UI panel render - renders glyphs)")
    print("  0x2F2560: JAL 0x2F3450 (stat numbers only)")
    print("  0x2F2570: JAL 0x30CBE0 (tile flush/render)")
    print()
    print("Inside per-frame renderer (0x2F2240):")
    print("  0x2F23F0: JAL 0x30AE20 (clear tile buffer)")
    print()

    # Test A: NOP JAL 0x2F2240 at call site 0x2F2538
    # This is the "per-frame renderer" for phase 2 chargen
    # If stat labels disappear: the labels come from this function
    nop_jal_in_iso(
        BASE_ISO,
        os.path.join(OUTPUT_DIR, "BUSIN0_EN_v36_nop_2F2240.iso"),
        0x2F2538,
        "per-frame renderer (phase 2 chargen)"
    )

    # Test B: NOP JAL 0x2ED5E0 at call site 0x2F2548
    # This is chargen logic (game state transitions)
    # Probably won't affect rendering, but worth checking
    nop_jal_in_iso(
        BASE_ISO,
        os.path.join(OUTPUT_DIR, "BUSIN0_EN_v36_nop_2ED5E0.iso"),
        0x2F2548,
        "chargen logic"
    )

    # Test C: NOP JAL 0x309870 at call site 0x2F2558
    # This is the UI panel render - iterates tiles and renders glyphs
    # MOST LIKELY candidate for stat labels
    nop_jal_in_iso(
        BASE_ISO,
        os.path.join(OUTPUT_DIR, "BUSIN0_EN_v36_nop_309870.iso"),
        0x2F2558,
        "UI panel render (glyph tiles)"
    )

    # Test D: NOP JAL 0x30CBE0 at call site 0x2F2570
    # This might be a tile flush/commit function
    nop_jal_in_iso(
        BASE_ISO,
        os.path.join(OUTPUT_DIR, "BUSIN0_EN_v36_nop_30CBE0.iso"),
        0x2F2570,
        "tile flush/render commit"
    )

    # Test E: NOP JAL 0x30AE20 inside per-frame renderer at 0x2F23F0
    # This clears the tile buffer. If labels disappear, they're rendered
    # into this buffer and then flushed by another call.
    nop_jal_in_iso(
        BASE_ISO,
        os.path.join(OUTPUT_DIR, "BUSIN0_EN_v36_nop_30AE20.iso"),
        0x2F23F0,
        "clear tile buffer (inside per-frame renderer)"
    )

    print()
    print("=" * 60)
    print("TEST PLAN:")
    print("=" * 60)
    print()
    print("Boot each ISO FRESH (no save states!) and navigate to chargen stats.")
    print()
    print("A) nop_2F2240.iso  - NOP per-frame renderer call")
    print("   -> If labels gone: they're rendered in phase 2 path")
    print("   -> If labels present: they're in phase 1 path (2ED5E0+309870)")
    print()
    print("B) nop_2ED5E0.iso  - NOP chargen logic call")
    print("   -> If labels gone: logic function has side-effect on rendering")
    print("   -> If game breaks: this is needed for state machine (expected)")
    print()
    print("C) nop_309870.iso  - NOP UI panel render call")
    print("   -> If labels gone: THIS renders the stat labels as glyph tiles")
    print("   -> Most likely candidate")
    print()
    print("D) nop_30CBE0.iso  - NOP tile flush/commit")
    print("   -> If labels gone: this commits/flushes the tile render")
    print()
    print("E) nop_30AE20.iso  - NOP tile buffer clear (inside per-frame renderer)")
    print("   -> If labels show garbage: confirms tiles are rendered into this buffer")
    print()
    print("NOTE: The orchestrator has TWO paths:")
    print("  Path 1 (flag clear): 2ED5E0 -> 309870 -> 2F3450 -> 30CBE0")
    print("  Path 2 (flag set):   2F2240 (which has its own full render pipeline)")
    print("  The stat labels likely appear in Path 1 (initial chargen)")
    print("  and Path 2 (after allocation/during review)")


if __name__ == "__main__":
    main()
