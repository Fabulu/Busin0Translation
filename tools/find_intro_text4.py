#!/usr/bin/env python3
"""Decode R1193 M0 with msg_glyph_map - this should be the intro narration."""
import struct
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
print(f"msg_glyph_map: {len(gm)} entries")

# Read R1193 section 2
data = open('extracted/packdata_raw/1193_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 24)[0]
sec2 = data[sec2_off:]

# Parse all messages
pos = 0
msg_idx = 0
while pos < len(sec2) - 1:
    gs = []
    start = pos
    while pos < len(sec2) - 1:
        val = struct.unpack_from('>H', sec2, pos)[0]
        pos += 2
        if val == 0xFFFF:
            break
        gs.append(val)
    if len(gs) == 0:
        msg_idx += 1
        continue

    print(f"\n=== R1193 Message {msg_idx} ({len(gs)} glyphs) ===")
    text = ''
    for g in gs:
        if g == 0xFFFE:
            text += '\n'
        elif g >= 0xFFC0:
            text += f'[{g:04X}]'
        else:
            ch = gm.get(str(g))
            if ch:
                text += ch
            else:
                text += f'({g})'
    print(text)
    msg_idx += 1

# Also decode R1194
print("\n\n========== R1194 ==========")
data2 = open('extracted/packdata_raw/1194_type02.raw', 'rb').read()
sec2_off2 = struct.unpack_from('<I', data2, 24)[0]
if sec2_off2 > 0 and sec2_off2 < len(data2):
    sec2b = data2[sec2_off2:]
    pos = 0
    msg_idx = 0
    while pos < len(sec2b) - 1:
        gs = []
        while pos < len(sec2b) - 1:
            val = struct.unpack_from('>H', sec2b, pos)[0]
            pos += 2
            if val == 0xFFFF:
                break
            gs.append(val)
        if len(gs) == 0:
            msg_idx += 1
            continue
        print(f"\n=== R1194 Message {msg_idx} ({len(gs)} glyphs) ===")
        text = ''
        for g in gs:
            if g == 0xFFFE:
                text += '\n'
            elif g >= 0xFFC0:
                text += f'[{g:04X}]'
            else:
                ch = gm.get(str(g))
                if ch:
                    text += ch
                else:
                    text += f'({g})'
        print(text)
        msg_idx += 1

# Now check: what are glyph IDs for 三, 十, 年 in msg_glyph_map?
print("\n\n=== Searching for 三十年 in msg_glyph_map ===")
rev = {}
for gid, ch in gm.items():
    rev.setdefault(ch, []).append(int(gid))
for ch in ['三', '十', '年', '長', '血', '恐', '怖', '戦', '乱', '陥', '王', '国', '悲', '惨', '役', '記', '憶']:
    ids = rev.get(ch, [])
    print(f"  {ch} = glyph IDs: {ids}")
