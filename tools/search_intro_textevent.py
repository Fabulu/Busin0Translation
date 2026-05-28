#!/usr/bin/env python3
"""Search for TextEvent system details and find where intro text is stored."""
import struct
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

iso_path = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

# Read ELF
with open(iso_path, 'rb') as f:
    f.seek(457143 * 2048)
    elf_data = f.read(4185776)

# Find all strings containing 'event', 'text', 'font' (case insensitive)
print("=== All TextEvent/event/font related strings in ELF ===")
i = 0
event_strings = []
while i < len(elf_data):
    if elf_data[i] == 0:
        i += 1
        continue
    end = i
    while end < len(elf_data) and elf_data[end] != 0:
        end += 1
    if end - i >= 5:
        try:
            s = elf_data[i:end].decode('ascii')
            sl = s.lower()
            if any(kw in sl for kw in ['textevent', 'event_font', 'event_text',
                                        'fcd_event', 'text_event', 'xcntbuf',
                                        'narration', 'scenario', 'script',
                                        'wall_event', 'wallevent',
                                        'intro', 'opening', 'prologue']):
                print(f"  +0x{i:08X}: {s}")
                event_strings.append((i, s))
        except:
            pass
    i = end + 1

# === Search for FCD references ===
print("\n=== All FCD_ references ===")
i = 0
while i < len(elf_data):
    if elf_data[i] == 0:
        i += 1
        continue
    end = i
    while end < len(elf_data) and elf_data[end] != 0:
        end += 1
    if end - i >= 3:
        try:
            s = elf_data[i:end].decode('ascii')
            if 'FCD_' in s:
                print(f"  +0x{i:08X}: {s}")
        except:
            pass
    i = end + 1

# === Now check the MOVIE/BSN2_0.DSI file more thoroughly ===
# It's 30.8 MB - might contain intro sequences
print("\n=== Checking MOVIE/BSN2_0.DSI for text ===")
with open(iso_path, 'rb') as f:
    f.seek(285 * 2048)  # MOVIE/BSN2_0.DSI at LBA 285
    dsi_movie = f.read(32243712)

print(f"MOVIE DSI size: {len(dsi_movie)} bytes")
print(f"Header: {dsi_movie[:128].hex()}")

# Search for text
for word_name, word in [('seneki', '\u6226\u5f79'), ('bankuoo', '\u30d0\u30f3\u30af'),
                        ('hisan', '\u60b2\u60e8'), ('sono', '\u305d\u306e')]:
    for enc in ['shift-jis', 'utf-16-le']:
        try:
            target = word.encode(enc)
            fpos = dsi_movie.find(target)
            if fpos >= 0:
                print(f"  '{word_name}' ({enc}) at +0x{fpos:08X}")
        except:
            pass

# === Also check the OTHER BSN2_0.DSI at LBA 426020 (root level) ===
print("\n=== Checking root BSN2_0.DSI for text ===")
with open(iso_path, 'rb') as f:
    f.seek(426020 * 2048)
    dsi_root = f.read(min(63176704, 10 * 1024 * 1024))  # First 10MB

print(f"Root DSI header: {dsi_root[:128].hex()}")

for word_name, word in [('seneki', '\u6226\u5f79'), ('bankuoo', '\u30d0\u30f3\u30af'),
                        ('hisan', '\u60b2\u60e8'), ('sono_hisan', '\u305d\u306e\u60b2')]:
    for enc in ['shift-jis', 'utf-16-le']:
        try:
            target = word.encode(enc)
            fpos = dsi_root.find(target)
            if fpos >= 0:
                ctx = dsi_root[max(0,fpos-10):fpos+len(target)+30]
                try:
                    decoded = ctx.decode(enc, errors='replace')
                except:
                    decoded = ctx.hex()
                print(f"  '{word_name}' ({enc}) at +0x{fpos:08X}: {decoded[:60]}")
        except:
            pass

# Also search full root DSI
print("\n=== Full root DSI search (63MB) ===")
with open(iso_path, 'rb') as f:
    f.seek(426020 * 2048)
    offset = 0
    chunk_size = 10 * 1024 * 1024
    while offset < 63176704:
        chunk = f.read(chunk_size)
        if not chunk:
            break
        for word_name, word in [('seneki', '\u6226\u5f79'), ('bankuoo', '\u30d0\u30f3\u30af\u30a9\u30fc')]:
            target = word.encode('shift-jis')
            fpos = chunk.find(target)
            if fpos >= 0:
                abs_pos = offset + fpos
                ctx = chunk[max(0,fpos-10):fpos+len(target)+30]
                print(f"  '{word_name}' in root DSI at +0x{abs_pos:08X}")
        offset += chunk_size

# === Search TEMP1.LZH for text (it's RIFF/WAV format) ===
print("\n=== TEMP1.LZH format ===")
# Header showed: RIFF....WAVE - it's actually a WAV audio file!
print("TEMP1.LZH is actually a WAV audio file (RIFF/WAVE header)")

# === Let's look at the actual loaded data in RAM for TextEvent ===
print("\n=== Searching RAM for TextEvent data ===")
import zipfile
z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# Find FCD_event_font and FCD_event_frame references in RAM
for keyword in [b'FCD_event_font', b'FCD_event_frame', b'FCD_wallevent',
                b'TEXTEVENT', b'textevent']:
    pos = ram.find(keyword)
    if pos >= 0:
        print(f"  '{keyword.decode()}' in RAM at 0x{pos:08X}")

# The TextEvent system loads data from PACKDATA.DIG resources
# Let's find which PACKDATA resource indices are referenced by the TextEvent code
# First, find the ELF entry point and code for TextEvent
entry_point = struct.unpack_from('<I', elf_data, 24)[0]
print(f"\n  ELF entry point: 0x{entry_point:08X}")

# The ELF is loaded at 0x00100000 in PS2 memory
# Let's search RAM for "TextEvent" related function pointers
for name in [b'TextEvent', b'textevent', b'XCNTBUF']:
    pos = ram.find(name)
    if pos >= 0:
        print(f"  '{name.decode()}' in RAM at 0x{pos:08X}")

print("\n=== Done ===")
