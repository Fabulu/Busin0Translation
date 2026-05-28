#!/usr/bin/env python3
"""Confirm the intro text is pre-rendered: check MOVIE dir and TEMP1.LZH."""
import struct
import sys
sys.stdout.reconfigure(encoding='utf-8')

iso_path = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

# Read MOVIE directory
with open(iso_path, 'rb') as f:
    # Root dir at LBA 261
    f.seek(261 * 2048)
    root_dir = f.read(2048)

# Find MOVIE directory entry
pos = 0
movie_lba = 0
movie_size = 0
while pos < len(root_dir):
    rec_len = root_dir[pos]
    if rec_len == 0:
        break
    name_len = root_dir[pos + 32]
    name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
    if 'MOVIE' in name:
        movie_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        movie_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        print(f"MOVIE dir: LBA={movie_lba}, size={movie_size}")
    pos += rec_len

# Read MOVIE directory
if movie_lba:
    with open(iso_path, 'rb') as f:
        f.seek(movie_lba * 2048)
        movie_dir = f.read(movie_size)

    print("\n=== MOVIE directory contents ===")
    pos = 0
    while pos < len(movie_dir):
        rec_len = movie_dir[pos]
        if rec_len == 0:
            pos = ((pos // 2048) + 1) * 2048
            if pos >= len(movie_dir):
                break
            continue
        lba = struct.unpack_from('<I', movie_dir, pos + 2)[0]
        size = struct.unpack_from('<I', movie_dir, pos + 10)[0]
        flags = movie_dir[pos + 25]
        name_len = movie_dir[pos + 32]
        name = movie_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        is_dir = (flags & 2) != 0
        print(f"  {name:30s} LBA={lba:8d} size={size:12d} ({size/1024/1024:.1f} MB)")
        pos += rec_len

# === Check BSN2_0.DSI - likely a data/script file ===
print("\n=== Checking BSN2_0.DSI header ===")
with open(iso_path, 'rb') as f:
    f.seek(426020 * 2048)
    dsi_header = f.read(4096)
print(f"DSI first 64 bytes: {dsi_header[:64].hex()}")
# Check for text in first 64KB
dsi_data = None
with open(iso_path, 'rb') as f:
    f.seek(426020 * 2048)
    dsi_data = f.read(min(63176704, 1024 * 1024))  # Read first 1MB

# Search DSI for intro text
for word_name, word in [('seneki', '\u6226\u5f79'), ('bankuoo', '\u30d0\u30f3\u30af\u30a9\u30fc'),
                        ('hisan', '\u60b2\u60e8'), ('kioku', '\u8a18\u61b6')]:
    for enc in ['shift-jis', 'utf-16-le']:
        try:
            target = word.encode(enc)
            fpos = dsi_data.find(target)
            if fpos >= 0:
                print(f"  '{word_name}' ({enc}) in DSI at +0x{fpos:08X}")
        except:
            pass

# === Check TEMP1.LZH ===
print("\n=== TEMP1.LZH header ===")
with open(iso_path, 'rb') as f:
    f.seek(459188 * 2048)
    temp_header = f.read(256)
print(f"TEMP1.LZH first 64 bytes: {temp_header[:64].hex()}")

# === Now let's look at the ELF more carefully for intro rendering code ===
print("\n=== Searching ELF for intro-related strings ===")
with open(iso_path, 'rb') as f:
    f.seek(457143 * 2048)
    elf_data = f.read(4185776)

# Search for strings related to intro, opening, movie
for keyword in [b'intro', b'INTRO', b'open', b'OPEN', b'prolog', b'PROLOG',
                b'movie', b'MOVIE', b'event', b'EVENT', b'narr', b'NARR',
                b'story', b'STORY', b'scenario', b'demo', b'DEMO',
                b'.pss', b'.PSS', b'.ipd', b'.IPD', b'.str', b'.STR',
                b'font', b'FONT', b'text', b'TEXT']:
    pos = 0
    count = 0
    while count < 5:
        pos = elf_data.find(keyword, pos)
        if pos < 0:
            break
        # Get surrounding context
        start = pos
        while start > 0 and elf_data[start-1] >= 32 and elf_data[start-1] < 127:
            start -= 1
            if pos - start > 40:
                break
        end = pos + len(keyword)
        while end < len(elf_data) and elf_data[end] >= 32 and elf_data[end] < 127:
            end += 1
            if end - pos > 60:
                break
        text = elf_data[start:end].decode('ascii', errors='replace')
        if len(text) >= len(keyword):
            print(f"  +0x{start:08X}: {text}")
        pos += 1
        count += 1

# === Search for Japanese text blocks in the ELF ===
print("\n=== Japanese text blocks in ELF ===")
# Find all null-terminated SJIS strings > 10 chars containing Japanese
sjis_strings = []
i = 0
while i < len(elf_data):
    if elf_data[i] == 0:
        i += 1
        continue
    # Find end of string
    end = i
    while end < len(elf_data) and elf_data[end] != 0:
        end += 1
    if end - i >= 6:
        try:
            s = elf_data[i:end].decode('shift-jis')
            jp_count = sum(1 for c in s if ord(c) > 0x3000)
            if jp_count >= 3:
                sjis_strings.append((i, s))
        except:
            pass
    i = end + 1

print(f"  Found {len(sjis_strings)} Japanese strings in ELF")
for offset, text in sjis_strings[:50]:
    print(f"  +0x{offset:08X}: {text[:80]}")

# Check if any contain intro-related content
for offset, text in sjis_strings:
    for check in ['\u6226\u5f79', '\u60b2\u60e8', '\u30d0\u30f3\u30af\u30a9\u30fc',
                  '\u8a18\u61b6', '\u4eba\u3005', '\u6226\u4e89']:
        if check in text:
            print(f"\n  MATCH: +0x{offset:08X}: {text}")

print("\n=== Done ===")
