import struct
import os
from collections import Counter

# === PART 1: Analyze UEDA.MSG glyph frequency ===
msg_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\IMAGE\EVENT\UEDA.MSG"
with open(msg_path, "rb") as f:
    msg_data = f.read()

print(f"UEDA.MSG size: {len(msg_data)} bytes")

glyphs = []
i = 0
while i + 1 < len(msg_data):
    val = struct.unpack(">H", msg_data[i:i+2])[0]
    glyphs.append(val)
    i += 2

total_glyphs = len(glyphs)
print(f"Total uint16 values: {total_glyphs}")

ffff_count = glyphs.count(0xFFFF)
fffe_count = glyphs.count(0xFFFE)
print(f"FFFF count: {ffff_count}")
print(f"FFFE count: {fffe_count}")

non_control = [g for g in glyphs if g < 0xFF00]
freq = Counter(non_control)
total_nc = len(non_control)
print(f"Non-control glyphs: {total_nc}")
print(f"Unique glyph indices: {len(freq)}")

print("\n=== TOP 80 GLYPH FREQUENCIES (BUSIN 1 / English) ===")
print(f"{'Rank':>4} {'Index':>6} {'Hex':>6} {'Count':>6} {'Pct':>7}")
for rank, (glyph, count) in enumerate(freq.most_common(80), 1):
    pct = count / total_nc * 100
    print(f"{rank:4d} {glyph:6d} 0x{glyph:04X} {count:6d} {pct:6.2f}%")

print("\n=== ANALYSIS: ASCII or Japanese encoding? ===")
top20 = freq.most_common(20)
top_indices = [g for g, c in top20]
max_idx = max(freq.keys())
min_idx = min(freq.keys())
print(f"Min glyph index: {min_idx} (0x{min_idx:04X})")
print(f"Max glyph index: {max_idx} (0x{max_idx:04X})")
print(f"Top 20 indices: {[hex(g) for g in top_indices]}")

low_indices = sum(1 for g in freq if g < 256)
high_indices = sum(1 for g in freq if g >= 256)
print(f"Unique glyphs with index < 256: {low_indices}")
print(f"Unique glyphs with index >= 256: {high_indices}")

if top20:
    top_pct = top20[0][1] / total_nc * 100
    print(f"Top glyph 0x{top20[0][0]:04X} frequency: {top_pct:.2f}%")
    if top_pct > 12:
        print("-> High frequency top glyph suggests SPACE character (English-like)")
    else:
        print("-> Lower frequency top glyph suggests Japanese-like distribution")

print("\n=== GLYPH INDEX RANGE DISTRIBUTION ===")
ranges = [(0, 0x7F, "0x00-0x7F (ASCII)"), (0x80, 0xFF, "0x80-0xFF"),
          (0x100, 0x1FF, "0x100-0x1FF"), (0x200, 0x3FF, "0x200-0x3FF"),
          (0x400, 0x7FF, "0x400-0x7FF"), (0x800, 0xFFF, "0x800-0xFFF"),
          (0x1000, 0x1FFF, "0x1000-0x1FFF"), (0x2000, 0x3FFF, "0x2000-0x3FFF"),
          (0x4000, 0x7FFF, "0x4000-0x7FFF"), (0x8000, 0xFEFF, "0x8000-0xFEFF")]
for lo, hi, label in ranges:
    count = sum(c for g, c in freq.items() if lo <= g <= hi)
    unique = sum(1 for g in freq if lo <= g <= hi)
    if count > 0:
        print(f"  {label}: {unique} unique, {count} occurrences ({count/total_nc*100:.1f}%)")

# === PART 2: BUSIN 1 EXE font descriptor search ===
print("\n" + "="*60)
print("=== PART 2: BUSIN 1 EXE font descriptor search ===")
print("="*60)

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
with open(exe_path, "rb") as f:
    exe_data = f.read()
print(f"BUSIN 1 EXE size: {len(exe_data)} bytes (0x{len(exe_data):X})")

b0_path = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
with open(b0_path, "rb") as f:
    b0_data = f.read()
print(f"BUSIN 0 EXE size: {len(b0_data)} bytes (0x{len(b0_data):X})")

print("\n--- BUSIN 0 font descriptor reference (at 0x3C0700) ---")
for i in range(5):
    off = 0x3C0700 + i * 28
    chunk = b0_data[off:off+28]
    vals = struct.unpack("<7I", chunk)
    print(f"  Entry {i}: {' '.join(f'{v:08X}' for v in vals)}")

print("\n--- BUSIN 0 glyph table sample (at 0x3C0870) ---")
for i in range(20):
    off = 0x3C0870 + i * 2
    val = struct.unpack("<H", b0_data[off:off+2])[0]
    print(f"  Glyph[{i}]: 0x{val:04X} ({val})")

b0_desc_header = b0_data[0x3C0700:0x3C0700+16]
print(f"BUSIN 0 descriptor header bytes: {b0_desc_header.hex()}")

# Search for exact 4-byte pattern match
search_pattern = b0_data[0x3C0700:0x3C0700+4]
print(f"\nSearching BUSIN 1 for pattern: {search_pattern.hex()}")
hits = []
search_start = 0x3B0000
search_end = min(0x4D0000, len(exe_data))
for off in range(search_start, search_end):
    if exe_data[off:off+4] == search_pattern:
        hits.append(off)
if hits:
    print(f"Found {len(hits)} matches")
    for h in hits[:20]:
        print(f"  0x{h:06X}: {exe_data[h:h+28].hex()}")
else:
    print("No exact matches found")

# Search for 28-byte struct arrays with small first fields
print("\n--- Searching for 28-byte font descriptor arrays ---")
candidates = []
for off in range(search_start, search_end - 84, 4):
    try:
        vals = struct.unpack("<7I", exe_data[off:off+28])
        if 4 <= vals[0] <= 64 and 4 <= vals[1] <= 64:
            vals2 = struct.unpack("<7I", exe_data[off+28:off+56])
            if 4 <= vals2[0] <= 64 and 4 <= vals2[1] <= 64:
                vals3 = struct.unpack("<7I", exe_data[off+56:off+84])
                if 4 <= vals3[0] <= 64 and 4 <= vals3[1] <= 64:
                    candidates.append(off)
    except:
        pass

print(f"Found {len(candidates)} candidate locations")
for c in candidates[:30]:
    print(f"\n  Candidate at 0x{c:06X}:")
    for j in range(min(4, (search_end - c) // 28)):
        vals = struct.unpack("<7I", exe_data[c + j*28 : c + j*28 + 28])
        print(f"    [{j}] {' '.join(f'{v:08X}' for v in vals)}")

# Search for glyph table regions
print("\n--- Searching for glyph table regions ---")
glyph_table_candidates = []
for off in range(search_start, search_end - 200, 2):
    is_table = True
    for k in range(50):
        v = struct.unpack("<H", exe_data[off + k*2 : off + k*2 + 2])[0]
        if v >= 0x4000 and v < 0xFF00:
            is_table = False
            break
    if is_table:
        sample_vals = [struct.unpack("<H", exe_data[off + k*2 : off + k*2 + 2])[0] for k in range(50)]
        valid = sum(1 for v in sample_vals if 0 < v < 0x2000)
        if valid > 30:
            glyph_table_candidates.append((off, sample_vals[:10]))

deduped = []
for off, samp in glyph_table_candidates:
    if not deduped or off - deduped[-1][0] > 100:
        deduped.append((off, samp))

print(f"Found {len(deduped)} candidate glyph table regions")
for off, samp in deduped[:10]:
    print(f"  0x{off:06X}: {[hex(v) for v in samp]}")

# === PART 3: English frequency correlation ===
print("\n" + "="*60)
print("=== PART 3: English frequency correlation ===")
print("="*60)

english_freq = {
    'space': 18.0, 'e': 10.3, 't': 7.5, 'a': 6.5, 'o': 6.2,
    'i': 5.7, 'n': 5.6, 's': 5.1, 'h': 4.9, 'r': 4.8,
    'd': 3.3, 'l': 3.3, 'u': 2.3, 'w': 2.0, 'm': 1.9,
    'f': 1.8, 'c': 1.7, 'g': 1.6, 'y': 1.6, 'p': 1.5,
}

print(f"\n{'Rank':>4} {'Glyph':>8} {'Actual':>8} {'EngChar':>9} {'EngPct':>6} {'Match':>7}")
eng_chars = list(english_freq.keys())
for rank, (glyph, count) in enumerate(freq.most_common(20)):
    pct = count / total_nc * 100
    if rank < len(eng_chars):
        ec = eng_chars[rank]
        ep = english_freq[ec]
        match = "YES" if abs(pct - ep) < ep * 0.4 else "maybe" if abs(pct - ep) < ep else "NO"
        print(f"{rank+1:4d} 0x{glyph:04X} {pct:7.2f}% {ec:>9} {ep:5.1f}% {match:>7}")

print("\nDone.")
