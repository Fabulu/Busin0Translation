#!/usr/bin/env python3
"""Wave-3: R2654 in-game Library short-name VARIABLE-LENGTH sub rebuilder.

The Library (R2654, 44-sub Format-A container, PACKDATA 2654_type44.raw) holds
~575 short NAME strings (monster compendium, magic library, AA list, guide
topics, ...) whose 4-10-glyph JP slots cannot fit English via the fixed-size
Step-2 route.  This script rebuilds ONLY the subs listed in
data/r2654_library_names.json with variable-length entries + a regenerated
per-sub offset table, then re-assembles the 44-sub container with a fresh
descriptor table (all other subs byte-identical), mirroring the two proven
prototypes:

  * tools/patch_r2654_names.py  build_sub()  (sub-7 roster rebuild)
  * build/inject_r34_db.py                   (R34 -> R2654 mirror subs)

Format-A sub layout (verified for ALL 44 subs, wave3 probe 2026-07-04):
    BE u16 count, BE u16 0,
    count x ( BE u16 off_rel_to_sub , BE u16 pad )   <- LAST pad = 0xFFFF
    entries: BE u16 glyph words, each entry ends FFFE FFFF
    (trailing-FFFE invariant: see build_v9.py Step 2 r_id==2654 comment and
     tests/test_v86_strips.test_R2654_structural)

Container layout: 44 x 16B LE descriptors (sub, size, off, 0) @0; byte 8 ==
first sub's offset == 704 (the "data_start" read by build_v9 Step 2); subs
16-byte aligned in original file order; file padded to a 2048 multiple.

RUN ORDER (build_v9 Step 6.5 list): AFTER build/inject_r34_db.py and
tools/patch_r2654_names.py -- this script reads the CURRENT built
build/packdata_resources/2654_type44.raw (Step-2 fixed-size body edits from
chunk_r2654_library_fix.json + item-DB mirror + sub-7 roster) and preserves
every unlisted sub / unlisted entry byte-identically.

Standalone dry-run:
    python tools/patch_r2654_library.py --in <base.raw> --out <patched.raw>

Gates (patch_r39_aa / patch_r39_spell_desc style -- every one is fatal):
  * PRISTINE-STRUCTURE guard: expected entry counts + signature entry bytes
    per listed sub against extracted/packdata_raw/2654_type44.raw (misaligned
    dict -> abort before writing anything).
  * Base-input structure walk of every listed sub (a Step-2 body write that
    ever clobbers a listed sub's offset table aborts the build loudly).
  * Self-verify: rebuilt subs decode back to the requested English, unlisted
    entries byte-identical, unlisted subs byte-identical, descriptor table
    consistent, sector aligned, no R2100-modified glyph id.
  * IDEMPOTENCE: re-running the transform on its own output is byte-identical.
"""
import argparse
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRISTINE = os.path.join(BASE, 'extracted/packdata_raw/2654_type44.raw')
BUILD = os.path.join(BASE, 'build/packdata_resources/2654_type44.raw')
NAMES_JSON = os.path.join(BASE, 'data/r2654_library_names.json')
GLYPH_TABLE = os.path.join(BASE, 'data/english_glyph_table.json')

NSUBS = 44
SECTOR = 2048
FFFE = 0xFFFE
FFFF = 0xFFFF

# R2100 modified-cell glyph ids that must NOT appear in any rebuilt string
# (mirrors build/inject_r34_db.py; pure-ASCII output can never hit these,
# the assert is a belt-and-braces guard).
R2100_MODIFIED = {121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132,
                  133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144,
                  145, 146, 308, 320, 346, 354, 535, 582, 590, 672, 673, 696,
                  717, 718, 719, 720, 721}

# ---------------------------------------------------------------------------
# PRISTINE-STRUCTURE signatures (misalignment gate).  Entry counts + raw bytes
# of one known entry per shipped sub, read from the pristine extract
# 2026-07-04.  If the dict/sub mapping ever drifts, we abort before writing.
#   sub 1  entry 1 = W SLASH kana        sub 28 entry 1 = BUBBLY SLIME kana
#   sub 41 entry 1 = CRETA kana          sub 43 entry 4 = "nashi" (None)
# ---------------------------------------------------------------------------
PRISTINE_COUNTS = {1: 38, 28: 154, 41: 57, 43: 10,
                   # v164 wave-4 subs (counts from pristine Format-A headers)
                   2: 38, 4: 18, 6: 21, 9: 43, 14: 31, 25: 31,
                   30: 26, 32: 9, 40: 91, 42: 105}
PRISTINE_SIGNATURES = {
    (1, 1): bytes.fromhex('003700cd00e7011000cc0109fffeffff'),
    (28, 1): bytes.fromhex('00fe010000e8005d00cd00e700c200e1fffeffff'),
    (41, 1): bytes.fromhex('00c800ea00d0fffeffff'),
    (43, 4): bytes.fromhex('0084007bfffeffff'),
    # v164 wave-4 signatures (first non-blank pristine entry per sub)
    (2, 1): bytes.fromhex('008900a400910085003ffffeffff'),
    (4, 1): bytes.fromhex('033a031900dc010b00c200e900830089fffeffff'),
    (6, 1): bytes.fromhex('00c600e900df00ee008801db02e4fffeffff'),
    (9, 1): bytes.fromhex('03a001fa00850070007f00bf0082fffeffff'),
    (14, 1): bytes.fromhex('01320133010000ea00cd00ea011000d4fffeffff'),
    (25, 1): bytes.fromhex('00c100ea00c200fdfffeffff'),
    (30, 1): bytes.fromhex('0293026c02ca0085008100710082fffeffff'),
    (32, 1): bytes.fromhex('031402d4027a009703c300850082fffeffff'),
    (40, 1): bytes.fromhex('00c6005d00f6010300ec005dfffeffff'),
    (42, 1): bytes.fromhex('002c0036fffeffff'),
}

table = json.load(open(GLYPH_TABLE, encoding='utf-8'))


def enc(ch):
    """ASCII char -> glyph id.  Mirrors build_v9.py Step 2 / inject_r34_db."""
    if ch in table:
        return table[ch]
    if ch.lower() in table:
        return table[ch.lower()]
    return 31  # '?'


def encode_english(english):
    """English -> Format-A entry bytes: glyphs (+FFFE per ' / ') + FFFE FFFF."""
    assert english != '', 'empty english string'
    assert all(ord(c) < 128 for c in english), f'non-ASCII english: {english!r}'
    words = []
    for si, seg in enumerate(english.split(' / ')):
        if si:
            words.append(FFFE)
        for ch in seg:
            words.append(enc(ch))
    words.append(FFFE)
    words.append(FFFF)
    for w in words:
        assert w not in R2100_MODIFIED, \
            f'glyph id {w} in R2100 modified set for {english!r}'
    return b''.join(struct.pack('>H', w) for w in words)


# ---------------------------------------------------------------------------
# Container helpers (byte-identical conventions to the two prototypes)
# ---------------------------------------------------------------------------
def read_header(raw):
    return [dict(zip(('sub', 'size', 'off', 'z'),
                     struct.unpack_from('<4I', raw, i * 16)))
            for i in range(NSUBS)]


def parse_sub(raw, off, size, label):
    """Strict Format-A walk.  Returns list of raw entry byte-strings."""
    cnt = struct.unpack_from('>H', raw, off)[0]
    pad0 = struct.unpack_from('>H', raw, off + 2)[0]
    assert pad0 == 0, f'{label}: count-pad {pad0:#x} != 0 (offset table clobbered?)'
    table_end = 4 + cnt * 4
    assert 0 < cnt and table_end <= size, f'{label}: count {cnt} overruns size {size}'
    offs = []
    for k in range(cnt):
        v = struct.unpack_from('>H', raw, off + 4 + k * 4)[0]
        z = struct.unpack_from('>H', raw, off + 6 + k * 4)[0]
        expect = FFFF if k == cnt - 1 else 0
        assert z == expect, f'{label} entry{k}: table pad {z:#x} != {expect:#x}'
        offs.append(v)
    assert offs[0] == table_end, \
        f'{label}: first off {offs[0]} != table_end {table_end}'
    assert all(offs[i] <= offs[i + 1] for i in range(cnt - 1)), \
        f'{label}: offsets not monotonic'
    entries = []
    for k in range(cnt):
        st = off + offs[k]
        en = off + (offs[k + 1] if k + 1 < cnt else size)
        seg = raw[st:en]
        assert len(seg) >= 4 and seg[-4:] == b'\xff\xfe\xff\xff', \
            f'{label} entry{k}: missing FFFE FFFF terminator'
        entries.append(seg)
    return entries


def build_sub(encoded_entries):
    """Rebuild one sub (prototype-identical: fresh offset table + payload)."""
    cnt = len(encoded_entries)
    offs, cur = [], 4 + cnt * 4
    for e in encoded_entries:
        offs.append(cur)
        cur += len(e)
    buf = bytearray()
    buf += struct.pack('>HH', cnt, 0)
    for k in range(cnt):
        buf += struct.pack('>HH', offs[k], FFFF if k == cnt - 1 else 0)
    for e in encoded_entries:
        buf += e
    assert len(buf) == cur
    return bytes(buf), cur


def pad_to_sector(buf):
    rem = len(buf) % SECTOR
    return buf + b'\x00' * (SECTOR - rem) if rem else buf


def load_names():
    doc = json.load(open(NAMES_JSON, encoding='utf-8'))
    names = {}
    for k, v in doc.items():
        if k.startswith('_'):
            continue
        names[int(k)] = {int(g): e for g, e in v.items()}
    return names


def transform(base, names):
    """Pure function: base container bytes -> patched container bytes.

    Also returns per-sub rebuild info for reporting/self-verify.
    """
    hdr = read_header(base)
    subs_present = sorted(h['sub'] for h in hdr)
    assert subs_present == list(range(NSUBS)), \
        f'container does not hold subs 0..43: {subs_present}'

    rebuilt = {}   # sub -> (bytes, size, n_translated, n_kept)
    for sub, ent_map in sorted(names.items()):
        h = next(x for x in hdr if x['sub'] == sub)
        entries = parse_sub(base, h['off'], h['size'], f'base sub{sub}')
        assert max(ent_map) < len(entries), \
            f'sub{sub}: listed entry {max(ent_map)} >= count {len(entries)}'
        enc_entries, n_tr = [], 0
        for k, seg in enumerate(entries):
            if k in ent_map:
                enc_entries.append(encode_english(ent_map[k]))
                n_tr += 1
            else:
                enc_entries.append(seg)          # keep verbatim
        sub_bytes, size = build_sub(enc_entries)
        rebuilt[sub] = (sub_bytes, size, n_tr, len(entries) - n_tr)

    # re-assemble container (prototype-identical: original offset order,
    # 16-byte aligned sub starts, fresh LE descriptor table, sector pad)
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
        if sub in rebuilt:
            sub_bytes, new_size = rebuilt[sub][0], rebuilt[sub][1]
        else:
            sub_bytes = base[h['off']:h['off'] + h['size']]
            new_size = h['size']
        out += sub_bytes
        cur += new_size
        new_hdr.append((sub, new_size, new_off))

    new_hdr.sort(key=lambda x: x[0])
    for i, (sub, size, off) in enumerate(new_hdr):
        struct.pack_into('<4I', out, i * 16, sub, size, off, 0)

    return bytes(pad_to_sector(out)), rebuilt


def decode_ascii(seg):
    """Decode a rebuilt entry back to English (' / ' for FFFE separators)."""
    words = [struct.unpack_from('>H', seg, p)[0] for p in range(0, len(seg) - 1, 2)]
    inv = {v: k for k, v in table.items() if v <= 94}
    out = []
    for w in words:
        if w == FFFF:
            break
        if w == FFFE:
            out.append(' / ')
        elif w in inv:
            out.append(inv[w])
        else:
            out.append(f'[{w}]')
    text = ''.join(out)
    return text[:-3] if text.endswith(' / ') else text


def self_verify(base, out, names, rebuilt):
    hdr_b = {h['sub']: h for h in read_header(base)}
    hdr_o = read_header(out)

    # descriptor table consistency
    assert sorted(h['sub'] for h in hdr_o) == list(range(NSUBS)), 'dup/missing subs'
    by_off = sorted(hdr_o, key=lambda h: h['off'])
    assert by_off[0]['off'] == NSUBS * 16, \
        f'first sub off {by_off[0]["off"]} != {NSUBS * 16}'
    assert struct.unpack_from('<I', out, 8)[0] == NSUBS * 16, \
        'byte-8 data_start (sub-0 offset) != 704'
    pos = NSUBS * 16
    for h in by_off:
        assert h['off'] % 16 == 0, f'sub{h["sub"]} off not 16-aligned'
        assert h['off'] >= pos, f'sub{h["sub"]} overlaps previous sub'
        pos = h['off'] + h['size']
    assert pos <= len(out), 'last sub overruns file'
    assert len(out) % SECTOR == 0, 'output not sector aligned'
    assert all(b == 0 for b in out[pos:]), 'nonzero bytes in sector padding'

    # unlisted subs byte-identical to base
    mism = 0
    for h in hdr_o:
        if h['sub'] in names:
            continue
        ob = hdr_b[h['sub']]
        if out[h['off']:h['off'] + h['size']] != base[ob['off']:ob['off'] + ob['size']]:
            print(f'  MISMATCH untouched sub {h["sub"]}')
            mism += 1
    assert mism == 0, f'{mism} untouched subs changed'

    # rebuilt subs: listed entries decode to English, unlisted byte-preserved
    for sub, ent_map in sorted(names.items()):
        h = next(x for x in hdr_o if x['sub'] == sub)
        ents_out = parse_sub(out, h['off'], h['size'], f'out sub{sub}')
        ob = hdr_b[sub]
        ents_base = parse_sub(base, ob['off'], ob['size'], f'base sub{sub}')
        assert len(ents_out) == len(ents_base), f'sub{sub} entry count changed'
        for k, seg in enumerate(ents_out):
            if k in ent_map:
                got = decode_ascii(seg)
                assert got == ent_map[k], \
                    f'sub{sub} entry{k}: decodes {got!r} != {ent_map[k]!r}'
            else:
                assert seg == ents_base[k], \
                    f'sub{sub} entry{k}: unlisted entry bytes changed'
    print('  self-verify OK: descriptors consistent, untouched subs identical, '
          'all listed entries decode to English, unlisted entries preserved')


def main():
    ap = argparse.ArgumentParser(description='R2654 library name sub rebuilder')
    ap.add_argument('--in', dest='inp', default=None,
                    help='base container (default: built file, else pristine)')
    ap.add_argument('--out', dest='outp', default=None,
                    help='output path (default: built file)')
    args = ap.parse_args()

    names = load_names()
    n_total = sum(len(v) for v in names.values())
    print(f'R2654 library rebuilder: {len(names)} subs, {n_total} names '
          f'({", ".join("sub" + str(s) for s in sorted(names))})')

    # ---- PRISTINE-STRUCTURE gate (misalignment guard, fatal) ----
    pristine = open(PRISTINE, 'rb').read()
    p_hdr = {h['sub']: h for h in read_header(pristine)}
    for sub in names:
        h = p_hdr[sub]
        ents = parse_sub(pristine, h['off'], h['size'], f'pristine sub{sub}')
        assert len(ents) == PRISTINE_COUNTS.get(sub, len(ents)), (
            f'PRISTINE GATE: sub{sub} count {len(ents)} != expected '
            f'{PRISTINE_COUNTS[sub]} -- names dict misaligned, ABORT')
        assert sub in PRISTINE_COUNTS, (
            f'PRISTINE GATE: sub{sub} has no expected-count entry -- add its '
            f'count + signature to PRISTINE_COUNTS/PRISTINE_SIGNATURES first')
    for (sub, k), sig in PRISTINE_SIGNATURES.items():
        if sub not in names:
            continue
        h = p_hdr[sub]
        ents = parse_sub(pristine, h['off'], h['size'], f'pristine sub{sub}')
        assert ents[k] == sig, (
            f'PRISTINE GATE: sub{sub} entry{k} signature mismatch '
            f'({ents[k].hex()} != {sig.hex()}) -- layout drifted, ABORT')
    print('  pristine-structure gate OK '
          f'({len([s for s in PRISTINE_SIGNATURES if s[0] in names])} signatures)')

    # ---- base input ----
    inp = args.inp
    if inp is None:
        inp = BUILD if os.path.exists(BUILD) else PRISTINE
    base = open(inp, 'rb').read()
    print(f'  base input: {inp} ({len(base)} bytes = {len(base)//SECTOR} sectors)')

    out, rebuilt = transform(base, names)

    print('  per-sub rebuild:')
    hdr_b = {h['sub']: h for h in read_header(base)}
    for sub, (_, size, n_tr, n_keep) in sorted(rebuilt.items()):
        print(f'    sub {sub:2d}: {hdr_b[sub]["size"]:6d} -> {size:6d} bytes, '
              f'{n_tr} translated, {n_keep} kept verbatim')

    # ---- gates on the result ----
    self_verify(base, out, names, rebuilt)

    out2, _ = transform(out, names)
    assert out2 == out, 'IDEMPOTENCE GATE: second run differs from first'
    print('  idempotence gate OK (re-run on own output is byte-identical)')

    outp = args.outp or BUILD
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, 'wb').write(out)
    print(f'R2654 written: {len(out)} bytes = {len(out)//SECTOR} sectors -> {outp}')


if __name__ == '__main__':
    main()
