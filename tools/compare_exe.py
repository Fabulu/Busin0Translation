"""
compare_exe.py - Binary comparison of original vs patched EXE
Finds ALL byte differences and classifies them as expected or unexpected.
"""
import struct, sys, os, io
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

ORIG = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "extracted", "SLPM_653.78"))
PATCHED = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "build", "SLPM_653.78_patched"))

orig = open(ORIG, "rb").read()
patched = open(PATCHED, "rb").read()

assert len(orig) == len(patched) == 4_185_776, f"Size mismatch: orig={len(orig)}, patched={len(patched)}"

# ── Known patch regions (from patch_exe.py) ──
# Each entry: (start, end_exclusive, patch_id, description)
KNOWN_PATCHES = [
    # Patch 1: Save Slot Names
    (0x3FC720, 0x3FC720 + 16, 1, "Save slot: 'BUSIN 0' title"),
    (0x3FC750, 0x3FC750 + 32, 1, "Save slot: 'BUSIN 0 Data 1'"),
    (0x3FC770, 0x3FC770 + 32, 1, "Save slot: 'BUSIN 0 Data 2'"),
    (0x3FC790, 0x3FC790 + 32, 1, "Save slot: 'BUSIN 0 Data 3'"),
    (0x3F9370, 0x3F9370 + 24, 1, "Save slot: 'BUSIN 0 Suspend'"),
    (0x3F9678, 0x3F9678 + 12, 1, "Save slot: 'BUSIN 0' (short)"),
    # Patch 2: Player-Visible Strings
    (0x3F8240, 0x3F8240 + 32, 2, "String: 'Continue loading!'"),
    (0x3F8260, 0x3F8260 + 32, 2, "String: 'No one can equip it.'"),
    # Patch 3: NPC Names
    (0x3C93B0, 0x3C93B0 + 16, 3, "NPC name 1: Emilia"),
    (0x3C93C0, 0x3C93C0 + 16, 3, "NPC name 2: Lute"),
    # Patch 4: Banner glyph IDs (scan entire 56-byte records)
    (0x3C33F0, 0x3C33F0 + 56, 4, "Banner rec: 新->Ne"),
    (0x3C3428, 0x3C3428 + 56, 4, "Banner rec: 規->w_"),
    (0x3C3268, 0x3C3268 + 56, 4, "Banner rec: 登->Re"),
    (0x3C32A0, 0x3C32A0 + 56, 4, "Banner rec: 録->g."),
    # Patch 5: Banner byte-50 (already covered by Patch 4 record ranges above,
    # but list explicitly for classification)
    (0x3C3422, 0x3C3422 + 2, 5, "Banner byte50: n"),
    (0x3C345A, 0x3C345A + 2, 5, "Banner byte50: e"),
    (0x3C329A, 0x3C329A + 2, 5, "Banner byte50: w"),
    (0x3C32D2, 0x3C32D2 + 2, 5, "Banner byte50: space"),
    # Patch 6: NOP RenderAllTiles
    (0x1F25E8, 0x1F25E8 + 4, 6, "NOP RenderAllTiles JAL"),
]

# ── Sensitive regions to check ──
SENSITIVE_REGIONS = [
    (0x3D8D10, 0x3DA000, "Cell data table"),
    (0x3DDC48, 0x3DDF48, "Font width tables"),
    (0x36C600, 0x36E1D0, "Keyboard code area"),
    (0x3B316C, 0x3B316C + 256, "Glyph table @ 0x3B316C"),
    (0x3C0882, 0x3C0882 + 256, "Glyph table @ 0x3C0882"),
    (0x3CA6DA, 0x3CA6DA + 256, "Glyph table @ 0x3CA6DA"),
    (0x3D1384, 0x3D1384 + 256, "Glyph table @ 0x3D1384"),
    (0x3D0000, 0x3E0000, "Extended range 0x3D0000-0x3E0000 (cell/font/bitmap)"),
]

# ── Find all differences ──
diffs = []
for i in range(len(orig)):
    if orig[i] != patched[i]:
        diffs.append(i)

print(f"Total bytes differing: {len(diffs)}")
print(f"File size: {len(orig)} bytes (0x{len(orig):X})")
print()

# ── Group consecutive diffs into regions ──
diff_regions = []
if diffs:
    start = diffs[0]
    end = diffs[0]
    for d in diffs[1:]:
        if d <= end + 8:  # gap of up to 8 bytes = same region
            end = d
        else:
            diff_regions.append((start, end + 1))
            start = d
            end = d
    diff_regions.append((start, end + 1))

print(f"Difference regions (gap <= 8 bytes merged): {len(diff_regions)}")
print("=" * 90)

def classify(offset):
    """Return (patch_id, description) if offset falls in a known patch, else None."""
    for s, e, pid, desc in KNOWN_PATCHES:
        if s <= offset < e:
            return (pid, desc)
    return None

# ── Report each region ──
unexpected_regions = []
for rstart, rend in diff_regions:
    nbytes = sum(1 for i in range(rstart, rend) if orig[i] != patched[i])

    # Classify
    classifications = set()
    unclassified_offsets = []
    for i in range(rstart, rend):
        if orig[i] != patched[i]:
            c = classify(i)
            if c:
                classifications.add(c)
            else:
                unclassified_offsets.append(i)

    is_expected = len(unclassified_offsets) == 0
    tag = "EXPECTED" if is_expected else "*** UNEXPECTED ***"

    print(f"\nRegion 0x{rstart:06X} - 0x{rend:06X} ({nbytes} bytes changed) [{tag}]")
    for pid, desc in sorted(classifications):
        print(f"  Patch {pid}: {desc}")

    if unclassified_offsets:
        unexpected_regions.append((rstart, rend, unclassified_offsets))
        print(f"  UNCLASSIFIED bytes: {len(unclassified_offsets)}")
        # Show detail for up to 32 unclassified bytes
        for off in unclassified_offsets[:32]:
            print(f"    0x{off:06X}: 0x{orig[off]:02X} -> 0x{patched[off]:02X}")
        if len(unclassified_offsets) > 32:
            print(f"    ... and {len(unclassified_offsets) - 32} more")

    # Show hex dump for small regions
    if nbytes <= 24:
        orig_hex = " ".join(f"{orig[i]:02X}" for i in range(rstart, rend))
        patch_hex = " ".join(f"{patched[i]:02X}" for i in range(rstart, rend))
        print(f"  orig:    {orig_hex}")
        print(f"  patched: {patch_hex}")

# ── Sensitive region scan ──
print("\n" + "=" * 90)
print("SENSITIVE REGION SCAN")
print("=" * 90)
for sstart, send, sname in SENSITIVE_REGIONS:
    region_diffs = [i for i in diffs if sstart <= i < send]
    if region_diffs:
        # Check if all are classified
        uncl = [i for i in region_diffs if classify(i) is None]
        if uncl:
            print(f"\n  *** ALERT *** {sname} (0x{sstart:06X}-0x{send:06X}): {len(region_diffs)} diffs, {len(uncl)} UNCLASSIFIED!")
            for off in uncl[:20]:
                print(f"    0x{off:06X}: 0x{orig[off]:02X} -> 0x{patched[off]:02X}")
        else:
            print(f"  OK  {sname}: {len(region_diffs)} diffs (all classified as known patches)")
    else:
        print(f"  CLEAN  {sname}: no differences")

# ── Summary ──
print("\n" + "=" * 90)
print("SUMMARY")
print("=" * 90)
classified_count = len(diffs) - sum(len(u) for _, _, u in unexpected_regions)
print(f"  Total bytes changed:     {len(diffs)}")
print(f"  Classified (expected):   {classified_count}")
print(f"  UNCLASSIFIED:            {len(diffs) - classified_count}")
print(f"  Unexpected regions:      {len(unexpected_regions)}")

if unexpected_regions:
    print("\n  *** WARNING: UNEXPECTED MODIFICATIONS DETECTED ***")
    for rstart, rend, ucl in unexpected_regions:
        print(f"    0x{rstart:06X}-0x{rend:06X}: {len(ucl)} unclassified bytes")
else:
    print("\n  All modifications match known patches. No collateral damage detected.")
