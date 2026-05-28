#!/usr/bin/env python3
"""Search all packdata resources for intro narration text patterns."""
import struct
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))

# === APPROACH 1: Original search for glyph pair 0x0353+0x02FE ===
target1 = struct.pack('>HH', 851, 766)
print("=== Search 1: Byte pattern 0x0353 0x02FE (assumed 十年) ===")
found1 = False
for i, entry in enumerate(manifest):
    if entry.get('skipped'):
        continue
    tc = entry['type_code']
    path = f'extracted/packdata_raw/{i:04d}_type{tc:02d}.raw'
    if not os.path.exists(path):
        continue
    data = open(path, 'rb').read()
    pos = data.find(target1)
    if pos >= 0:
        print(f'  R{i} (type {tc}): at offset {pos} (size {len(data)})')
        found1 = True
if not found1:
    print("  NO MATCHES")

# === APPROACH 2: Search for glyph 376 (か) in section 2 of type-2 resources ===
# The intro starts with かつて, so glyph 376 should appear near message start
print("\n=== Search 2: Resources with glyph 376 (か) near message start in sec2 ===")
for i, entry in enumerate(manifest):
    if entry.get('skipped'):
        continue
    tc = entry['type_code']
    if tc != 2:
        continue
    path = f'extracted/packdata_raw/{i:04d}_type{tc:02d}.raw'
    if not os.path.exists(path):
        continue
    data = open(path, 'rb').read()
    if len(data) < 28:
        continue
    sec2_off = struct.unpack_from('<I', data, 24)[0]
    if sec2_off == 0 or sec2_off >= len(data):
        continue
    sec2 = data[sec2_off:]
    # Find glyph 376 (0x0178) as BE uint16
    target_ka = struct.pack('>H', 376)
    pos = sec2.find(target_ka)
    while pos >= 0:
        # Check if it's at an even offset (aligned as uint16)
        if pos % 2 == 0:
            # Check if it's within first 5 glyphs of a message
            # Look backwards for FFFF or start of section
            msg_start = pos
            for j in range(1, 6):
                check_pos = pos - j * 2
                if check_pos < 0:
                    msg_start = 0
                    break
                val = struct.unpack_from('>H', sec2, check_pos)[0]
                if val == 0xFFFF:
                    msg_start = check_pos + 2
                    break
            glyph_offset = (pos - msg_start) // 2
            if glyph_offset <= 2:
                # Show context
                ctx_glyphs = []
                for k in range(min(20, (len(sec2) - pos) // 2)):
                    v = struct.unpack_from('>H', sec2, pos + k * 2)[0]
                    if v == 0xFFFF:
                        break
                    ctx_glyphs.append(v)
                print(f'  R{i}: ka at glyph pos {glyph_offset}, context: {ctx_glyphs[:15]}')
        pos = sec2.find(target_ka, pos + 2)

# === APPROACH 3: Check R1193 specifically ===
print("\n=== R1193 detailed analysis ===")
data = open('extracted/packdata_raw/1193_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 24)[0]
sec2 = data[sec2_off:]
pos = 0
msg_idx = 0
while pos < len(sec2) - 1:
    gs = []
    while pos < len(sec2) - 1:
        val = struct.unpack_from('>H', sec2, pos)[0]
        pos += 2
        if val == 0xFFFF:
            break
        gs.append(val)
    if len(gs) > 0:
        # Count glyphs in valid range (< 858)
        valid = sum(1 for g in gs if g < 858)
        high = sum(1 for g in gs if 858 <= g < 0xFFC0)
        ctrl = sum(1 for g in gs if g >= 0xFFC0)
        print(f'  M{msg_idx}: {len(gs)} total, {valid} valid, {high} high, {ctrl} ctrl')
        print(f'    First 30: {gs[:30]}')
    msg_idx += 1

# === APPROACH 4: Look for the intro text in ALL type-2 resources section 2 ===
# The intro has multiple sentences. Let's find resources where section 2 has
# messages of roughly the right length (25-40 glyphs per sentence, or longer for multiple)
print("\n=== Search 3: Type-2 resources with text-length messages (20-150 glyphs) ===")
for i in range(1180, 1210):
    entry = manifest[i]
    if entry.get('skipped'):
        continue
    tc = entry['type_code']
    if tc != 2:
        continue
    path = f'extracted/packdata_raw/{i:04d}_type{tc:02d}.raw'
    if not os.path.exists(path):
        continue
    data = open(path, 'rb').read()
    if len(data) < 28:
        continue
    sec2_off = struct.unpack_from('<I', data, 24)[0]
    sec2_size = struct.unpack_from('<I', data, 20)[0]
    if sec2_off == 0 or sec2_off >= len(data):
        print(f'  R{i}: no section 2')
        continue
    sec2 = data[sec2_off:sec2_off + sec2_size]
    pos = 0
    msg_idx = 0
    msgs = []
    while pos < len(sec2) - 1:
        gs = []
        while pos < len(sec2) - 1:
            val = struct.unpack_from('>H', sec2, pos)[0]
            pos += 2
            if val == 0xFFFF:
                break
            gs.append(val)
        if len(gs) > 0:
            msgs.append(gs)
        msg_idx += 1
    print(f'  R{i}: {len(msgs)} messages, sizes: {[len(m) for m in msgs]}')

# === APPROACH 5: Brute force - search ALL resources for byte 0x01 0x78 (376 as BE) ===
print("\n=== Search 4: All resources containing 0x0178 (glyph 376/ka) ===")
target_ka = struct.pack('>H', 376)
hits = []
for i, entry in enumerate(manifest):
    if entry.get('skipped'):
        continue
    tc = entry['type_code']
    path = f'extracted/packdata_raw/{i:04d}_type{tc:02d}.raw'
    if not os.path.exists(path):
        continue
    data = open(path, 'rb').read()
    if target_ka in data:
        hits.append((i, tc, len(data)))
print(f'  {len(hits)} resources contain 0x0178')
for ri, tc, sz in hits:
    if 1180 <= ri <= 1210:
        print(f'    R{ri} (type {tc}, size {sz}) <-- INTRO RANGE')

print("\nDone.")
