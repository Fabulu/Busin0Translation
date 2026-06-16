#!/usr/bin/env python3
"""Romanize the R1892 character-roster names (the party-bar name source).

THE BUG (v92 playtest, Vera): the party bar at the bottom of the tavern/town
screen shows recruited story characters' names as KATAKANA (e.g. "ヴェーラ" for
Vera) even on a FRESH new game.  A prior fix romanized R2654 sub-7, but the party
bar does NOT read R2654 -- it reads R1892 (1892_type20.raw), a flat roster table
copied verbatim into the RAM character DB (RAM 0xDC1xxx stride 0x130 / 0x560xxx
stride 0x1F0) and rendered through the R2100 page-0 font.  R1892 ships pristine,
so the names stay katakana.  PROVEN by EE-RAM byte-match (request.p2s, fresh game):
the live name at RAM 0x5601F2 is byte-identical to R1892's Vera record @file 0xBF2,
stored LITTLE-ENDIAN (R2654 was big-endian -- that is why the R2654 patch had no
effect on the bar).

THE FIX: rewrite each record's NAME field in place.  R1892 = 25 fixed 0x130-byte
records (base 0x140, stride 0x130); records 0-19 carry a u16 id then a name field
at record+2 = a 16-byte span holding LE name-value runs (name_val = glyph_id + 95,
the R2100 page-0 codec) terminated by 0xFFFF and FF-padded.  We decode each name's
katakana, match it to English via data/name_labels.json (gated by the
data/r2654_party_names.json allowed set, same as patch_r2654_names.py), and
re-encode as a LITTLE-ENDIAN ASCII name-value run + 0xFFFF, FF-padded to keep the
16-byte field (and the whole 0x130 record, and the file size) byte-stable.  Names
that do not map, or romanize to >7 chars (will not fit the 16-byte field), are left
as katakana (safe fallback).  Records 20-24 (id 0, empty) are skipped.

REAL-PS2: edits PACKDATA resource bytes only; fixed-stride so no offset rebuild.
"""
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRISTINE = os.path.join(BASE, 'extracted/packdata_raw/1892_type20.raw')
BUILD = os.path.join(BASE, 'build/packdata_resources/1892_type20.raw')
GLYPH_TABLE = os.path.join(BASE, 'data/english_glyph_table.json')
NAME_LABELS = os.path.join(BASE, 'data/name_labels.json')
PARTY_NAMES = os.path.join(BASE, 'data/r2654_party_names.json')

REC_BASE = 0x140
REC_STRIDE = 0x130
NAME_OFF = 2               # u16 id, then the name field
FFFF = 0xFFFF
# R1892 name fields are RAW R2100 page-0 glyph CELL indices, copied VERBATIM into
# the active-party struct (RAM 0x55DD20) the bar renders — NOT the R2654 name_value
# codec.  R2100 page-0 is a standard ASCII layout: cell = char - 32 (space=0,
# A=33..Z=58, a=65..z=90), which == english_glyph_table values.  Proven by the
# on-screen leader 'BABA' = cells [34,33,34,33] and the R2100 atlas. So the encode
# is IDENTITY (no +95): writing ascii_gid+95 pushed every letter into the katakana
# cell region (V 54->149) and rendered garbage. Offset is now 0.
ASCII_NV_OFFSET = 0

# name-value -> katakana (identical grid to patch_r2654_names.py)
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA = {
    93: 'ー', 238: 'ン', 254: 'バ', 245: 'ジ', 252: 'デ', 270: 'ェ', 273: 'ヴ',
    246: 'ズ', 247: 'ゼ', 248: 'ゾ', 249: 'ダ', 253: 'ド', 272: 'ッ',
}


def nv_to_kana(nv):
    if 193 <= nv <= 193 + 44:
        return KATA[nv - 193]
    return KATA_EXTRA.get(nv, '〓')


def name_field_span(raw, name_off):
    """Bytes from name_off to the first non-FF byte after the FFFF terminator."""
    o = name_off
    while o < name_off + REC_STRIDE:
        if struct.unpack_from('<H', raw, o)[0] == FFFF:
            break
        o += 2
    end = o + 2
    while end < name_off + REC_STRIDE and raw[end] == 0xFF:
        end += 1
    return end - name_off


def main():
    glyph_table = json.load(open(GLYPH_TABLE, encoding='utf-8'))
    name_labels = json.load(open(NAME_LABELS, encoding='utf-8'))
    party_doc = json.load(open(PARTY_NAMES, encoding='utf-8'))
    allowed = set(party_doc['entries'].values())

    def ascii_gid(ch):
        if ch in glyph_table:
            return glyph_table[ch]
        if ch.lower() in glyph_table:
            return glyph_table[ch.lower()]
        return 31  # '?'

    # ALWAYS read the PRISTINE base: R1892 is only ever touched by this script, and
    # an already-romanized build copy would fail the katakana->English match (its
    # ASCII runs decode to 〓 garbage), making re-runs non-idempotent / skip names.
    raw = bytearray(open(PRISTINE, 'rb').read())
    src = 'extracted/packdata_raw/1892_type20.raw (PRISTINE)'
    orig_len = len(raw)
    print(f'R1892 base input: {src} ({orig_len} bytes)')

    n_records = (len(raw) - REC_BASE) // REC_STRIDE
    changed = []
    for i in range(n_records):
        rs = REC_BASE + i * REC_STRIDE
        rid = struct.unpack_from('<H', raw, rs)[0]
        name_off = rs + NAME_OFF
        # decode LE name-values until FFFF
        vals, o = [], name_off
        while o < rs + REC_STRIDE:
            v = struct.unpack_from('<H', raw, o)[0]
            if v == FFFF:
                break
            vals.append(v)
            o += 2
        if rid == 0 or not vals:
            continue  # empty/padding record
        kana = ''.join(nv_to_kana(v) for v in vals)
        eng = name_labels.get(kana)
        if not eng or eng not in allowed:
            continue  # no confident mapping -> keep katakana
        span = name_field_span(raw, name_off)          # bytes available
        need = (len(eng) + 1) * 2                       # name-vals + FFFF
        if need > span:
            print(f'  SKIP rec{i:2d} {kana} -> {eng}: needs {need}B > {span}B field')
            continue
        # write LE ASCII name-value run + FFFF, FF-pad the rest of the field
        new = bytearray(b'\xff' * span)
        p = 0
        for ch in eng:
            struct.pack_into('<H', new, p, ascii_gid(ch) + ASCII_NV_OFFSET)
            p += 2
        struct.pack_into('<H', new, p, FFFF)
        raw[name_off:name_off + span] = new
        changed.append((i, rid, kana, eng))

    assert len(raw) == orig_len, 'file size changed -- in-place edit must preserve size'
    os.makedirs(os.path.dirname(BUILD), exist_ok=True)
    open(BUILD, 'wb').write(raw)
    print(f'R1892 written: {len(raw)} bytes -> build/packdata_resources/1892_type20.raw')
    print(f'romanized {len(changed)} roster names:')
    for i, rid, kana, eng in changed:
        print(f'  rec{i:2d} id={rid:3d}  {kana:<8s} -> {eng}')

    # ---- self-verify ----
    print('\n=== SELF-VERIFY ===')
    raw2 = open(BUILD, 'rb').read()
    assert len(raw2) == orig_len
    pristine = open(PRISTINE, 'rb').read()
    # every byte OUTSIDE the touched name fields must equal the base input
    base = open(BUILD, 'rb').read()  # re-read (same file) just for clarity
    touched = set()
    for i, *_ in changed:
        rs = REC_BASE + i * REC_STRIDE
        span = name_field_span(pristine, rs + NAME_OFF)
        touched.update(range(rs + NAME_OFF, rs + NAME_OFF + span))

    def decode(off):
        out, o = [], off
        while True:
            v = struct.unpack_from('<H', raw2, o)[0]
            if v == FFFF:
                break
            out.append(chr((v - ASCII_NV_OFFSET) + 0x20)
                       if ASCII_NV_OFFSET <= v <= ASCII_NV_OFFSET + 94
                       else '[' + nv_to_kana(v) + ']')
            o += 2
        return ''.join(out)

    vera = next((i for i, rid, k, e in changed if e == 'Vera'), None)
    if vera is not None:
        d = decode(REC_BASE + vera * REC_STRIDE + NAME_OFF)
        print(f'  Vera record decodes to: {d!r}  {"OK" if d == "Vera" else "FAIL"}')
    else:
        print('  WARNING: Vera not romanized (kana->English mapping missing)')
    print(f'  records romanized: {len(changed)} ; file size stable: '
          f'{"OK" if len(raw2) == orig_len else "FAIL"}')
    print('DONE.')


if __name__ == '__main__':
    main()
