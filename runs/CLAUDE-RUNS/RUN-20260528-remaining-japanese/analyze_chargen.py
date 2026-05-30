#!/usr/bin/env python3
"""Exhaustive decode of the chargen area in the Busin 0 EXE."""

import json, struct, sys

EXE = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"

with open(GLYPH_MAP, "r", encoding="utf-8") as f:
    gm = json.load(f)

with open(EXE, "rb") as f:
    exe = f.read()

def decode_glyph(gid):
    """Decode a glyph ID to its character."""
    s = str(gid)
    if s in gm:
        return gm[s]
    return f"[{gid}]"

def parse_text_entries(start, end, label=""):
    """Parse a region as sequential glyph-pair entries separated by FFFE/FFFF."""
    results = []
    pos = start
    current_entry_start = pos
    current_glyphs = []

    while pos < end - 1:
        val = struct.unpack_from("<H", exe, pos)[0]

        if val == 0xFFFF:
            # End of entry
            if current_glyphs:
                text = "".join(decode_glyph(g) for g in current_glyphs)
                results.append({
                    "offset": current_entry_start,
                    "glyph_ids": current_glyphs[:],
                    "text": text,
                    "raw_bytes": exe[current_entry_start:pos+2].hex()
                })
            current_glyphs = []
            pos += 2
            current_entry_start = pos
        elif val == 0xFFFE:
            # Line break within entry
            current_glyphs.append("FFFE")
            pos += 2
        elif val == 0x0000 and not current_glyphs:
            # Skip null padding
            pos += 2
            current_entry_start = pos
        else:
            # Could be flag+glyph pair or just a value
            # Check if this looks like a (flag, glyph) pair
            if pos + 3 < end:
                b0 = exe[pos]
                b1 = exe[pos+1]
                b2 = exe[pos+2]
                b3 = exe[pos+3]

                # Type-2 MSG format: flag byte, then glyph_id as uint16 LE, but here
                # it might be simpler. Let's try reading as uint16 pairs.
                # Actually the EXE text seems to use raw glyph IDs as uint16 LE
                glyph_id = val
                if glyph_id < 2000:  # reasonable glyph range
                    current_glyphs.append(glyph_id)
                pos += 2
            else:
                pos += 2

    # Don't forget last entry
    if current_glyphs:
        text = "".join(decode_glyph(g) for g in current_glyphs)
        results.append({
            "offset": current_entry_start,
            "glyph_ids": current_glyphs[:],
            "text": text,
            "raw_bytes": exe[current_entry_start:pos].hex()
        })

    return results

def scan_for_text_blocks(start, end):
    """More flexible scan: find sequences of valid glyph IDs."""
    results = []
    pos = start

    while pos < end - 1:
        val = struct.unpack_from("<H", exe, pos)[0]

        if val == 0xFFFF or val == 0xFFFE or val == 0x0000:
            pos += 2
            continue

        # Check if this could be start of a glyph sequence
        if str(val) in gm and val < 2000:
            entry_start = pos
            glyphs = []
            text_pos = pos
            while text_pos < end - 1:
                v = struct.unpack_from("<H", exe, text_pos)[0]
                if v == 0xFFFF:
                    text_pos += 2
                    break
                elif v == 0xFFFE:
                    glyphs.append(("BREAK", 0xFFFE))
                    text_pos += 2
                elif str(v) in gm and v < 2000:
                    glyphs.append((gm[str(v)], v))
                    text_pos += 2
                else:
                    # Unknown value - might be flag or end
                    break

            if len(glyphs) >= 1:
                text = "".join(g[0] if g[0] != "BREAK" else "|" for g in glyphs)
                gids = [g[1] for g in glyphs]
                results.append({
                    "offset": entry_start,
                    "hex_offset": f"0x{entry_start:06X}",
                    "glyph_ids": gids,
                    "text": text,
                    "length": len(glyphs)
                })
                pos = text_pos
            else:
                pos += 2
        else:
            pos += 2

    return results

print("=" * 80)
print("CHARGEN AREA ANALYSIS: 0x3C83C0 - 0x3C93A0")
print("=" * 80)

# First, let's do a raw hex dump of key areas to understand the format
print("\n--- Raw hex at 0x3C83C0 (first 128 bytes) ---")
for i in range(0, 128, 16):
    off = 0x3C83C0 + i
    hexb = exe[off:off+16].hex()
    hexf = " ".join(hexb[j:j+4] for j in range(0, len(hexb), 4))
    print(f"  0x{off:06X}: {hexf}")

# Scan the full chargen area
print("\n--- Decoded text blocks in chargen area (0x3C83C0 - 0x3C93A0) ---")
blocks = scan_for_text_blocks(0x3C83C0, 0x3C93A0)
for b in blocks:
    print(f"  {b['hex_offset']}: [{','.join(str(g) for g in b['glyph_ids'])}] -> \"{b['text']}\"")

# Now scan broader area
print("\n" + "=" * 80)
print("BROADER AREA ANALYSIS: 0x3C8000 - 0x3C9E00")
print("=" * 80)
blocks_broad = scan_for_text_blocks(0x3C8000, 0x3C9E00)
for b in blocks_broad:
    print(f"  {b['hex_offset']}: [{','.join(str(g) for g in b['glyph_ids'])}] -> \"{b['text']}\"")

# Let's also try a different parsing approach - maybe the format uses
# 4 bytes per glyph (flag + padding + glyph_id)
print("\n" + "=" * 80)
print("ALTERNATE PARSE: 4-byte entries (byte flag + byte pad + uint16 glyph)")
print("=" * 80)

def parse_4byte_entries(start, end):
    """Try parsing as 4-byte entries: flag(1) + pad(1) + glyph_id(2)."""
    results = []
    pos = start
    current_start = pos
    current_glyphs = []

    while pos < end - 3:
        flag = exe[pos]
        pad = exe[pos+1]
        glyph_id = struct.unpack_from("<H", exe, pos+2)[0]

        if flag == 0xFF and pad == 0xFF:
            # FFFF terminator (as 2 bytes at pos, then next 2 bytes)
            if current_glyphs:
                text = "".join(decode_glyph(g[1]) for g in current_glyphs)
                results.append({
                    "offset": current_start,
                    "entries": current_glyphs[:],
                    "text": text
                })
            current_glyphs = []
            pos += 2  # just skip the FFFF
            current_start = pos
            continue

        if glyph_id < 2000 and str(glyph_id) in gm:
            current_glyphs.append((flag, glyph_id))
            pos += 4
        else:
            pos += 2
            current_start = pos

    return results

# Let's look at the actual byte pattern around known content
print("\n--- Byte-level analysis around 0x3C83C0 ---")
for off in range(0x3C83C0, 0x3C83C0 + 256, 2):
    val = struct.unpack_from("<H", exe, off)[0]
    decoded = ""
    if val == 0xFFFF:
        decoded = "TERM"
    elif val == 0xFFFE:
        decoded = "BREAK"
    elif str(val) in gm:
        decoded = f"-> {gm[str(val)]}"
    elif val == 0:
        decoded = "NULL"
    else:
        decoded = f"?? (0x{val:04X})"
    print(f"  0x{off:06X}: 0x{val:04X} ({val:5d}) {decoded}")

# Specifically search for alignment glyphs
print("\n" + "=" * 80)
print("SEARCHING FOR SPECIFIC CHARGEN GLYPHS")
print("=" * 80)

# Known chargen-related glyph IDs
search_glyphs = {
    520: "善 (Good)",
    289: "悪 (Evil)",
    337: "中 (Middle/Neutral-1)",
    340: "立 (Standing/Neutral-2)",
    518: "男 (Male)",
    349: "女 (Female-1)",
    418: "女 (Female-2)",
    286: "戦 (War/Fighter)",
    309: "忍 (Ninja)",
    315: "盗 (Thief)",
    401: "侍 (Samurai)",
    470: "中 (Middle-2)",
    1029: "僧 (Monk/Priest)",
    1174: "狂 (Mad/Berserker)",
}

for gid, desc in search_glyphs.items():
    gid_bytes = struct.pack("<H", gid)
    # Search in chargen area
    start = 0x3C8000
    end = 0x3C9E00
    pos = start
    locations = []
    while pos < end - 1:
        idx = exe.find(gid_bytes, pos, end)
        if idx == -1:
            break
        locations.append(idx)
        pos = idx + 2
    if locations:
        locs_str = ", ".join(f"0x{l:06X}" for l in locations)
        print(f"  Glyph {gid:4d} {desc}: found at {locs_str}")
    else:
        print(f"  Glyph {gid:4d} {desc}: NOT found in chargen area")

# Also search whole EXE for these near each other
print("\n--- Search for 善(520) in full EXE ---")
gid_bytes = struct.pack("<H", 520)
pos = 0
while pos < len(exe) - 1:
    idx = exe.find(gid_bytes, pos)
    if idx == -1:
        break
    # Show context
    ctx_before = exe[max(0,idx-8):idx].hex()
    ctx_after = exe[idx+2:idx+10].hex()
    print(f"  0x{idx:06X}: ...{ctx_before} [0802] {ctx_after}...")
    pos = idx + 2

print("\n--- Search for 悪(289) in full EXE ---")
gid_bytes = struct.pack("<H", 289)
pos = 0
locs = []
while pos < len(exe) - 1:
    idx = exe.find(gid_bytes, pos)
    if idx == -1:
        break
    locs.append(idx)
    pos = idx + 2
print(f"  Found {len(locs)} occurrences")
for l in locs[:20]:
    ctx_before = exe[max(0,l-8):l].hex()
    ctx_after = exe[l+2:l+10].hex()
    print(f"  0x{l:06X}: ...{ctx_before} [2101] {ctx_after}...")
