#!/usr/bin/env python3
"""Phase-6: Romanize the R2654 party-bar / character-name roster (sub 7).

The premade-party + NPC names render in the party bar (Bar Luna Light roster)
as KATAKANA because they are stored in PACKDATA R2654 (2654_type44.raw) sub 7
as katakana NAME-VALUE runs.  The party bar renders these runs through the
R2100 page-0 font (GS-VRAM atlas tbp=0x2840, PSMT4 256x256 CT32), which ALSO
contains ASCII glyphs at glyph indices 0-94.

Name-value codec (data/xref_party.json):  glyph_index = name_val - 95
    name_val 193..238  -> glyph 98..142/97  (katakana grid)
ASCII therefore reachable via:             name_val = ascii_gid + 95
    ascii_gid 0..94 (data/english_glyph_table.json) -> name_val 95..189
    -> glyph 0..94 = R2100 page-0 ASCII cell.

This script:
  * reads build/packdata_resources/2654_type44.raw if present (Step-2 / inject_r34_db
    output, so co-op item-DB translations are preserved) else the pristine extract,
  * decodes sub 7's 47 name entries, matches each to English via the entry's
    decoded katakana through data/name_labels.json,
  * re-encodes matched names as ASCII name-value runs (+95 offset),
  * rebuilds ONLY sub 7 (fresh offset table) and re-assembles the 44-sub container
    with corrected header offsets/sizes (other subs byte-identical, incl. the
    inject_r34_db item-DB subs),
  * writes build/packdata_resources/2654_type44.raw.

RUN ORDER:  run AFTER build/inject_r34_db.py so its R2654 item-DB rewrite is the
base input here (this script leaves all non-sub-7 subs byte-identical).

NOTE (in-game assumption to verify): this assumes the chargen/party name renderer
applies the documented linear codec  glyph = name_val - 95  for name_val < 193
without clamping to the katakana range.  Render font R2100 page-0 ASCII presence
and the codec are both verified from data; the < 193 path is the single
unverified link and must be confirmed by an in-game party-bar screenshot.
"""
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRISTINE = os.path.join(BASE, 'extracted/packdata_raw/2654_type44.raw')
BUILD = os.path.join(BASE, 'build/packdata_resources/2654_type44.raw')
GLYPH_TABLE = os.path.join(BASE, 'data/english_glyph_table.json')
NAME_LABELS = os.path.join(BASE, 'data/name_labels.json')
PARTY_NAMES = os.path.join(BASE, 'data/r2654_party_names.json')

NSUBS = 44
NAME_SUB = 7
SECTOR = 2048
FFFE = 0xFFFE
FFFF = 0xFFFF
ASCII_NV_OFFSET = 95          # name_val = ascii_gid + 95
KATA_BASE = 193               # name_val 193..237 = katakana grid pos 0..44

# katakana grid pos 0..44 -> unicode (matches data/xref_party.json grid)
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
# extended name-value -> kana char (for matching name_labels keys)
KATA_EXTRA = {
    93: 'ー', 238: 'ン', 254: 'バ', 245: 'ジ', 252: 'デ', 270: 'ェ', 273: 'ヴ',
    246: 'ズ', 247: 'ゼ', 248: 'ゾ', 249: 'ダ', 253: 'ド', 272: 'ッ',
    # voiced (dakuten base 239: ga gi gu ge go .. ba bi bu be bo) +
    # handakuten (base 259: pa pi pu pe po) + small kana (base 264:
    # sya syu syo sa si su se so stsu). Names like ベルグラーノ/ヨッペン/
    # ミリィ/サミュエル decode to 〓 without these and fall back to katakana.
    239: 'ガ', 241: 'グ', 243: 'ゴ', 256: 'ブ', 257: 'ベ', 262: 'ペ',
    268: 'ィ', 265: 'ュ',
}


def nv_to_kana(nv):
    if KATA_BASE <= nv <= KATA_BASE + 44:
        return KATA[nv - KATA_BASE]
    return KATA_EXTRA.get(nv, '〓')   # geta mark = unknown


def read_header(raw, nsubs):
    return [dict(zip(('sub', 'size', 'off', 'z'),
                     struct.unpack_from('<4I', raw, i * 16)))
            for i in range(nsubs)]


def read_sub_entries(raw, off, size):
    """Return list of raw entry byte-strings (excluding the offset table)."""
    cnt = struct.unpack_from('>H', raw, off)[0]
    offs = [struct.unpack_from('>H', raw, off + 4 + k * 4)[0] for k in range(cnt)]
    entries = []
    for k in range(cnt):
        st = off + offs[k]
        en = off + (offs[k + 1] if k + 1 < cnt else size)
        entries.append(raw[st:en])
    return cnt, entries


def words_of(seg):
    return [struct.unpack_from('>H', seg, p)[0]
            for p in range(0, len(seg) - 1, 2)]


def build_sub(encoded_entries):
    """Rebuild one sub from encoded entry byte-strings (inject_r34_db format).

    Layout: BE u16 count, BE u16 0, count*(BE u16 off_rel, BE u16 pad),
    last pad = FFFF sentinel, then concatenated entries.
    """
    cnt = len(encoded_entries)
    table_bytes = 4 + cnt * 4
    offs = []
    cur = table_bytes
    for e in encoded_entries:
        offs.append(cur)
        cur += len(e)
    size = cur
    buf = bytearray()
    buf += struct.pack('>HH', cnt, 0)
    for k in range(cnt):
        pad = FFFF if k == cnt - 1 else 0
        buf += struct.pack('>HH', offs[k], pad)
    for e in encoded_entries:
        buf += e
    assert len(buf) == size
    return bytes(buf), size


def pad_to_sector(buf):
    rem = len(buf) % SECTOR
    return buf + b'\x00' * (SECTOR - rem) if rem else buf


def main():
    glyph_table = json.load(open(GLYPH_TABLE, encoding='utf-8'))
    name_labels = json.load(open(NAME_LABELS, encoding='utf-8'))
    party_doc = json.load(open(PARTY_NAMES, encoding='utf-8'))
    allowed = set(party_doc['entries'].values())   # English names we will write

    def ascii_gid(ch):
        if ch in glyph_table:
            return glyph_table[ch]
        if ch.lower() in glyph_table:
            return glyph_table[ch.lower()]
        return 31   # '?'

    def encode_english(eng):
        words = [ascii_gid(c) + ASCII_NV_OFFSET for c in eng]
        for w in words:
            assert 0 <= w <= 0xFFEF, f'name_val out of range for {eng!r}: {w}'
        words += [FFFE, FFFF]
        return b''.join(struct.pack('>H', w) for w in words)

    if os.path.exists(BUILD):
        raw = open(BUILD, 'rb').read()
        src = 'build/packdata_resources/2654_type44.raw (Step-2/inject_r34_db output)'
    else:
        raw = open(PRISTINE, 'rb').read()
        src = 'extracted/packdata_raw/2654_type44.raw (PRISTINE)'
    print(f'R2654 base input: {src}  ({len(raw)} bytes)')

    hdr = read_header(raw, NSUBS)
    name_h = next(h for h in hdr if h['sub'] == NAME_SUB)
    cnt, entries = read_sub_entries(raw, name_h['off'], name_h['size'])
    print(f'sub {NAME_SUB}: off=0x{name_h["off"]:06x} size=0x{name_h["size"]:04x} '
          f'count={cnt}')

    # ---- rebuild sub 7 entries ----
    new_entries = []
    changed = []
    for k, seg in enumerate(entries):
        vals = [w for w in words_of(seg) if w not in (FFFE, FFFF)]
        kana = ''.join(nv_to_kana(v) for v in vals)
        eng = name_labels.get(kana)
        if eng and eng in allowed:
            new_entries.append(encode_english(eng))
            changed.append((k, kana, eng, len(seg), len(new_entries[-1])))
        else:
            new_entries.append(seg)            # keep katakana verbatim
    new_sub7, new_sub7_size = build_sub(new_entries)
    print(f'sub {NAME_SUB} rebuilt: {len(new_entries)} entries, '
          f'{name_h["size"]} -> {new_sub7_size} bytes, {len(changed)} romanized')
    for k, kana, eng, ol, nl in changed:
        print(f'  entry {k:2d}  {kana:<10s} -> {eng:<10s} ({ol}B -> {nl}B)')

    # ---- re-assemble 44-sub container (mirror inject_r34_db layout) ----
    out = bytearray(b'\x00' * (NSUBS * 16))
    cur = NSUBS * 16
    new_hdr = []
    for h in sorted(hdr, key=lambda x: x['off']):
        sub = h['sub']
        if cur % 16:
            pad = 16 - (cur % 16)
            out += b'\x00' * pad
            cur += pad
        new_off = cur
        if sub == NAME_SUB:
            sub_bytes, new_size = new_sub7, new_sub7_size
        else:
            sub_bytes = raw[h['off']:h['off'] + h['size']]
            new_size = h['size']
        out += sub_bytes
        cur += new_size
        new_hdr.append((sub, new_size, new_off))

    new_hdr.sort(key=lambda x: x[0])
    for i, (sub, size, off) in enumerate(new_hdr):
        struct.pack_into('<4I', out, i * 16, sub, size, off, 0)

    out = pad_to_sector(out)
    os.makedirs(os.path.dirname(BUILD), exist_ok=True)
    open(BUILD, 'wb').write(out)
    print(f'R2654 written: {len(out)} bytes = {len(out)//SECTOR} sectors '
          f'-> {BUILD}')

    # ---- self-verify: re-decode patched sub 7 ----
    print('\n=== SELF-VERIFY ===')
    raw2 = open(BUILD, 'rb').read()
    hdr2 = read_header(raw2, NSUBS)
    # 1) all non-sub-7 subs byte-identical to the base input
    base_hdr = {h['sub']: h for h in hdr}
    mism = 0
    for h in hdr2:
        if h['sub'] == NAME_SUB:
            continue
        ob = base_hdr[h['sub']]
        a = raw[ob['off']:ob['off'] + ob['size']]
        b = raw2[h['off']:h['off'] + h['size']]
        if a != b:
            print(f'  MISMATCH sub {h["sub"]}: size {ob["size"]} vs {h["size"]}')
            mism += 1
    print(f'  non-sub-7 subs byte-identical: {"OK" if mism == 0 else f"{mism} MISMATCH"}')

    # 2) decode patched sub 7, confirm romaji present
    name_h2 = next(h for h in hdr2 if h['sub'] == NAME_SUB)
    cnt2, entries2 = read_sub_entries(raw2, name_h2['off'], name_h2['size'])
    assert cnt2 == cnt, f'entry count changed {cnt} -> {cnt2}'

    def decode_entry(seg):
        out_s = []
        for w in words_of(seg):
            if w == FFFF:
                break
            if w == FFFE:
                continue
            if ASCII_NV_OFFSET <= w <= ASCII_NV_OFFSET + 94:   # ASCII range
                out_s.append(chr((w - ASCII_NV_OFFSET) + 0x20))
            else:
                out_s.append('[' + nv_to_kana(w) + ']')        # katakana kept
        return ''.join(out_s)

    ok = 0
    want = {eng for _, _, eng, _, _ in changed}
    seen = set()
    for k, seg in enumerate(entries2):
        d = decode_entry(seg)
        if d in want:
            seen.add(d)
            ok += 1
    print(f'  romaji decoded back from patched sub 7: {sorted(seen)}')
    missing = want - seen
    print(f'  expected {len(want)} romanized, found {len(seen)}'
          + (f', MISSING {sorted(missing)}' if missing else ' (all present)'))

    # 3) show the premade-party trio explicitly
    for target in ('Vera', 'Konde', 'Erika'):
        present = target in seen
        print(f'  premade-party {target}: {"OK" if present else "NOT FOUND"}')

    print('\nDONE.' if mism == 0 and not missing else '\nDONE WITH WARNINGS.')


if __name__ == '__main__':
    main()
