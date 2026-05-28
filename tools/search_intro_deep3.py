#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep search for intro narration - approach 3."""
import zipfile
import struct
import sys
import os

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89\u306f\u30d0\u30f3\u30af\u30a9\u30fc\u306e\u6226\u5f79\u3068\u4eba\u3005\u306b\u8a18\u61b6\u3055\u308c\u308b\u3002'

# === Search for ALL occurrences of SJIS fragments of the sentence ===
print("=== Searching SJIS fragments of intro sentence ===")
sjis_full = sentence.encode('shift-jis')
# Search every 4-byte window
for start in range(0, len(sjis_full) - 3, 2):
    fragment = sjis_full[start:start+4]
    pos = 0
    while True:
        pos = ram.find(fragment, pos)
        if pos < 0:
            break
        # Try to extend the match
        match_len = 4
        while start + match_len <= len(sjis_full) and pos + match_len <= len(ram):
            if ram[pos + match_len - 1] == sjis_full[start + match_len - 1]:
                match_len += 1
            else:
                break
        match_len -= 1
        if match_len >= 6:  # At least 3 SJIS chars
            matched_sjis = ram[pos:pos+match_len]
            try:
                decoded = matched_sjis.decode('shift-jis', errors='replace')
            except:
                decoded = '?'
            print(f"  Match at 0x{pos:08X}: {match_len} bytes = '{decoded}'")
            print(f"    hex: {ram[pos:pos+match_len+10].hex()}")
        pos += 1

# === Search for file references related to intro/events ===
print("\n=== File path strings in RAM ===")
for keyword in [b'intro', b'INTRO', b'open', b'OPEN', b'event', b'EVENT',
                b'story', b'STORY', b'scena', b'SCENA', b'prolog', b'PROLOG',
                b'.msg', b'.MSG', b'.scr', b'.SCR', b'.dat', b'.txt']:
    pos = 0
    count = 0
    while count < 10:
        pos = ram.find(keyword, pos)
        if pos < 0:
            break
        # Extract surrounding context as ASCII
        start = pos
        # Scan backwards to find start of string
        while start > 0 and ram[start-1] >= 32 and ram[start-1] < 127:
            start -= 1
            if pos - start > 60:
                break
        # Scan forwards to find end
        end = pos + len(keyword)
        while end < len(ram) and ram[end] >= 32 and ram[end] < 127:
            end += 1
            if end - pos > 80:
                break
        text = ram[start:end].decode('ascii', errors='replace')
        if len(text) >= 5 and ('.' in text or '/' in text or '\\' in text):
            print(f"  0x{start:08X}: {text}")
        pos += 1
        count += 1

# === Look for PACKDATA.DIG table of contents in RAM ===
print("\n=== PACKDATA references in RAM ===")
for keyword in [b'PACKDATA', b'packdata', b'PACK']:
    pos = 0
    count = 0
    while count < 5:
        pos = ram.find(keyword, pos)
        if pos < 0: break
        ctx = ram[max(0,pos-8):pos+40]
        text = ctx.decode('ascii', errors='replace')
        print(f"  0x{pos:08X}: {text}")
        pos += 1
        count += 1

# === Search for the kanji compound 戦役 (seneki = campaign) specifically ===
# This is an unusual word that would be distinctive
print("\n=== Searching for rare word 'seneki' ===")
seneki_sjis = b'\x90\xed\x96\xf0'  # 戦役 in SJIS
pos = 0
count = 0
while count < 20:
    pos = ram.find(seneki_sjis, pos)
    if pos < 0: break
    ctx = ram[max(0,pos-20):pos+24]
    try:
        decoded = ctx.decode('shift-jis', errors='replace')
    except:
        decoded = '?'
    print(f"  0x{pos:08X}: hex={ctx.hex()}")
    print(f"    decoded: {decoded}")
    pos += 1
    count += 1

# Also EUC-JP
seneki_euc = '\u6226\u5f79'.encode('euc-jp')
pos = ram.find(seneki_euc)
if pos >= 0:
    print(f"  EUC-JP seneki at 0x{pos:08X}")

# UTF-16LE
seneki_u16 = '\u6226\u5f79'.encode('utf-16-le')
pos = 0
count = 0
while count < 5:
    pos = ram.find(seneki_u16, pos)
    if pos < 0: break
    ctx = ram[max(0,pos-8):pos+12]
    print(f"  UTF16LE seneki at 0x{pos:08X}: {ctx.hex()}")
    pos += 1
    count += 1

# === Check: maybe text is stored character-by-character with some struct per char ===
# e.g., each displayed character has (x, y, char_code, color)
# The text has about 25 chars spread across 3 lines
# Try to find sequences of SJIS codes with regular spacing
print("\n=== Searching for SJIS codes with stride ===")
first_char_sjis = b'\x82\xbb'  # そ
second_char_sjis = b'\x82\xcc'  # の
for stride in range(4, 33, 2):
    pos = 0
    while True:
        pos = ram.find(first_char_sjis, pos)
        if pos < 0: break
        if pos + stride + 2 <= len(ram):
            if ram[pos+stride:pos+stride+2] == second_char_sjis:
                # Check third char too
                third_char_sjis = b'\x94\xdf'  # 悲
                if pos + 2*stride + 2 <= len(ram) and ram[pos+2*stride:pos+2*stride+2] == third_char_sjis:
                    print(f"  Stride {stride}: 'sono-hisan' at 0x{pos:08X}")
                    # Show the full strided sequence
                    for i in range(min(10, len(sentence))):
                        char_at = ram[pos+i*stride:pos+i*stride+2]
                        print(f"    char {i}: {char_at.hex()}")
        pos += 1

print("\n=== Done ===")
