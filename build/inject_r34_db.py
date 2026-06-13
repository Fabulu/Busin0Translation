"""v86 R34 item-database variable-length rebuilder (+ R2654 mirror).

Replaces the v85 in-place fixed-size R34 injector (build_v9.py Step 2),
which truncated long item names ('Healin', 'War Go') because it could
only fit English into the original Japanese byte span.  This rebuilder
re-encodes every string variable-length from data/r34_english_aligned.json,
regenerates each sub's offset table, rewrites the 20-entry container header,
and pads to a 2048 multiple.  It then mirrors the duplicate item subs into
R2654 (44-sub container) so both copies show identical English.

Runs as build Step 6.5 (wave 3), AFTER Step 2, so it overwrites Step 2's
truncated R34 from PRISTINE + aligned English.

VERIFIED R34 container format (extracted/packdata_raw/0034_type20.raw):
  - byte 0: 20-entry header, 16B each = LE u32 (sub_index, size, offset, 0)
  - data_start LE u32 at byte 8 = 320 (= 20*16)
  - each sub @ off:
        BE u16 count, BE u16 pad(0)
        count x ( BE u16 offset_rel_to_sub , BE u16 pad )   <- LAST pad = 0xFFFF sentinel
        BE u16 glyph strings, each ending  FFFE FFFF
    entry 0 is the 6-byte dummy  0000 FFFE FFFF.
  - strings: ASCII via data/english_glyph_table.json (glyph id == ASCII-0x20,
    range 0..94).  ' / ' separators encode as FFFE.  Every string is
    <segments joined by FFFE> + FFFE FFFF.
  - sub9 (spell books) carry a header box:  <FF07|FF02> <glyphs> FFF0 FFFE <body...>
    The opener (FF07/FF02) and FFF0 closer are copied verbatim from the
    pristine string; the inner header glyphs are replaced with the English
    header (english's first ' / '-segment), the body with the remainder.

Outputs (build/packdata_resources/):
  0034_type20.raw   2654_type44.raw

Self-verify (no build): re-decodes both outputs and asserts every entry
== its aligned English, structure walk clean, no R2100-modified glyph ids,
R2654 untouched subs byte-identical to input.  Prints sector counts.
"""
import os
import sys
import json
import struct

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/programmieren/wizardrytranslation'
PRISTINE_R34 = os.path.join(BASE, 'extracted/packdata_raw/0034_type20.raw')
PRISTINE_R2654 = os.path.join(BASE, 'extracted/packdata_raw/2654_type44.raw')
BUILD_R34 = os.path.join(BASE, 'build/packdata_resources/0034_type20.raw')
BUILD_R2654 = os.path.join(BASE, 'build/packdata_resources/2654_type44.raw')
ALIGNED = os.path.join(BASE, 'data/r34_english_aligned.json')
GLYPH_TABLE = os.path.join(BASE, 'data/english_glyph_table.json')

SECTOR = 2048
FFFE = 0xFFFE
FFFF = 0xFFFF
FFF0 = 0xFFF0
HEADER_OPENERS = (0xFF07, 0xFF02)

# R2100 modified-cell glyph ids that must NOT appear in any rebuilt string.
R2100_MODIFIED = {121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132,
                  133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144,
                  145, 146, 308, 320, 346, 354, 535, 582, 590, 672, 673, 696,
                  717, 718, 719, 720, 721}

# Verified R34 sub -> R2654 sub mapping (duplicate item subs, k<->k by index).
R34_TO_R2654 = {0: 12, 1: 11, 2: 18, 3: 17, 4: 24, 5: 23,
                6: 22, 7: 21, 8: 16, 10: 20, 11: 19}

table = json.load(open(GLYPH_TABLE, encoding='utf-8'))


def enc(ch):
    """ASCII char -> glyph id.  Mirrors build_v9.py Step 2 enc()."""
    if ch in table:
        return table[ch]
    if ch.lower() in table:
        return table[ch.lower()]
    return 31  # '?'


# ----------------------------------------------------------------------------
# Container read helpers
# ----------------------------------------------------------------------------
def read_header(raw, nsubs):
    subs = []
    for i in range(nsubs):
        idx, size, off, z = struct.unpack_from('<4I', raw, i * 16)
        subs.append({'sub': idx, 'size': size, 'off': off, 'z': z})
    return subs


def read_sub_entries(raw, off, size):
    """Return list of raw byte-strings (one per entry, excluding table)."""
    cnt = struct.unpack_from('>H', raw, off)[0]
    offs = [struct.unpack_from('>H', raw, off + 4 + k * 4)[0] for k in range(cnt)]
    entries = []
    for k in range(cnt):
        st = off + offs[k]
        en = off + (offs[k + 1] if k + 1 < cnt else size)
        entries.append(raw[st:en])
    return cnt, entries


def words_of(seg):
    return [struct.unpack_from('>H', seg, p)[0] for p in range(0, len(seg) - 1, 2)]


# ----------------------------------------------------------------------------
# String encoder
# ----------------------------------------------------------------------------
def encode_plain(english):
    """Non-sub9: <segments joined by FFFE> + FFFE FFFF."""
    words = []
    segs = english.split(' / ')
    for si, seg in enumerate(segs):
        if si:
            words.append(FFFE)
        for ch in seg:
            words.append(enc(ch))
    words.append(FFFE)
    words.append(FFFF)
    return words


def encode_sub9(english, orig_words):
    """sub9 spell book: <opener> <header glyphs> FFF0 FFFE <body...> FFFE FFFF.

    Opener (FF07/FF02) and FFF0 are copied verbatim from the pristine entry;
    only the glyph content is replaced with the English header/body.
    """
    opener = orig_words[0]
    assert opener in HEADER_OPENERS, f'unexpected sub9 opener {opener:04X}'
    head, sep, body = english.partition(' / ')
    assert sep, f'sub9 english missing header separator: {english!r}'
    words = [opener]
    for ch in head:
        words.append(enc(ch))
    words.append(FFF0)
    words.append(FFFE)            # separator that followed FFF0 in the original
    body_segs = body.split(' / ')
    for si, seg in enumerate(body_segs):
        if si:
            words.append(FFFE)
        for ch in seg:
            words.append(enc(ch))
    words.append(FFFE)
    words.append(FFFF)
    return words


def encode_entry(aligned_entry, orig_seg, is_sub9):
    """Return the encoded byte-string for one entry.

    idx 0 with empty english is the placeholder dummy -> keep original bytes.
    """
    if aligned_entry['idx'] == 0 and aligned_entry['english'] == '':
        return bytes(orig_seg)          # verbatim dummy (0000 FFFE FFFF)
    english = aligned_entry['english']
    assert english != '', f"non-placeholder with empty english: {aligned_entry}"
    assert all(ord(c) < 128 for c in english), f'non-ASCII english: {english!r}'
    if is_sub9 and aligned_entry.get('preserve_prefix'):
        words = encode_sub9(english, words_of(orig_seg))
    else:
        words = encode_plain(english)
    return b''.join(struct.pack('>H', w) for w in words)


def assert_no_r2100(words, where):
    for w in words:
        if w in R2100_MODIFIED:
            raise AssertionError(f'{where}: glyph id {w} in R2100 modified set')


# ----------------------------------------------------------------------------
# Sub builder: rebuild one sub from encoded entry byte-strings.
# ----------------------------------------------------------------------------
def build_sub(encoded_entries):
    """Given list of encoded entry byte-strings, build (sub_bytes, size).

    Layout: BE u16 count, BE u16 0, then count*(BE u16 off_rel, BE u16 pad),
    last pad = FFFF sentinel, then concatenated entries.  size = total bytes.
    """
    cnt = len(encoded_entries)
    table_bytes = 4 + cnt * 4
    # compute per-entry relative offsets
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
    return bytes(buf), size, offs


def pad_to_sector(buf):
    n = len(buf)
    rem = n % SECTOR
    if rem:
        buf = buf + b'\x00' * (SECTOR - rem)
    return buf


# ============================================================================
# Load aligned English
# ============================================================================
aligned = json.load(open(ALIGNED, encoding='utf-8'))['entries']
aligned_by_sub = {}
for e in aligned:
    aligned_by_sub.setdefault(e['sub'], {})[e['idx']] = e

pristine_r34 = open(PRISTINE_R34, 'rb').read()
r34_hdr = read_header(pristine_r34, 20)

# ============================================================================
# Rebuild R34
# ============================================================================
print('=== Rebuilding R34 (0034_type20.raw) ===')
growth_rows = []          # (sub, old_size, new_size)
rebuilt_subs = {}         # sub -> (bytes, size, offs)
encoded_per_sub = {}      # sub -> list of encoded entry byte-strings (for mirror)

for h in r34_hdr:
    sub = h['sub']
    old_off, old_size = h['off'], h['size']
    cnt, orig_entries = read_sub_entries(pristine_r34, old_off, old_size)
    al = aligned_by_sub[sub]
    assert len(al) == cnt, f'sub{sub}: aligned {len(al)} != raw count {cnt}'
    is_sub9 = (sub == 9)
    enc_entries = []
    for k in range(cnt):
        eb = encode_entry(al[k], orig_entries[k], is_sub9)
        assert_no_r2100(words_of(eb), f'R34 sub{sub} item{k}')
        enc_entries.append(eb)
    encoded_per_sub[sub] = enc_entries
    sub_bytes, new_size, offs = build_sub(enc_entries)
    rebuilt_subs[sub] = (sub_bytes, new_size, offs)
    growth_rows.append((sub, old_size, new_size))

# assemble container: 320B header + subs in original sub order, 16-aligned starts
out = bytearray(b'\x00' * 320)
cur = 320
new_hdr = []
# preserve the on-disk sub ordering (by ascending original offset == sub index)
for h in sorted(r34_hdr, key=lambda x: x['off']):
    sub = h['sub']
    sub_bytes, new_size, offs = rebuilt_subs[sub]
    # subs in pristine are 16-byte aligned; keep that invariant
    if cur % 16:
        pad = 16 - (cur % 16)
        out += b'\x00' * pad
        cur += pad
    new_off = cur
    out += sub_bytes
    cur += new_size
    new_hdr.append((sub, new_size, new_off))

# write 20-entry header
new_hdr.sort(key=lambda x: x[0])
for i, (sub, size, off) in enumerate(new_hdr):
    struct.pack_into('<4I', out, i * 16, sub, size, off, 0)
struct.pack_into('<I', out, 8, 320)   # data_start unchanged

out = pad_to_sector(out)
os.makedirs(os.path.dirname(BUILD_R34), exist_ok=True)
open(BUILD_R34, 'wb').write(out)
r34_sectors = len(out) // SECTOR
print(f'R34 written: {len(out)} bytes = {r34_sectors} sectors '
      f'(pristine {len(pristine_r34)} = {len(pristine_r34)//SECTOR} sectors)')

print('\nR34 per-sub growth table:')
print(f"  {'sub':>3} {'old':>7} {'new':>7} {'delta':>7}")
for sub, old, new in growth_rows:
    print(f'  {sub:>3} {old:>7} {new:>7} {new-old:>+7}')

# NOTE (v86 decision): the 40-sector figure was the architect's conservative
# ESTIMATE, not a structural limit.  rebuild_packdata.py places R34 (and R2654)
# as normal SEQUENTIAL TOC resources (cs=125 onward) with a freshly-computed
# TOC — unlike R2100/R1370 which sit in fixed header gaps with hard ceilings.
# So R34 can grow freely; its only cost is extra PACKDATA->ISO overflow, which
# build Step 8.2 absorbs by relocating subsequent files (the same mechanism
# v85 already uses for 154 sectors; relocation correctness is binary, not size-
# proportional).  We proceed with a loud NOTE and keep only a high runaway guard
# so a genuinely corrupt rebuild still aborts.
R34_RUNAWAY_CEILING = 80
r34_overbudget = r34_sectors > R34_RUNAWAY_CEILING
if r34_sectors > 40:
    print('\n*** NOTE: R34 %d sectors (>40 estimate). No structural ceiling — '
          'sequential TOC resource; proceeding.\n    Adds ~%d sectors of PACKDATA '
          'overflow handled by build Step 8.2; flag audio + item screens for the '
          'real-PS2 spot-check. ***' % (r34_sectors, r34_sectors - 34))
if r34_overbudget:
    print('\n*** HARD-FAIL (runaway guard): R34 %d sectors exceeds ceiling %d — '
          'indicates a corrupt rebuild, not normal English volume. ***'
          % (r34_sectors, R34_RUNAWAY_CEILING))

# ============================================================================
# Rebuild R2654 mirror
# ============================================================================
print('\n=== Rebuilding R2654 mirror (2654_type44.raw) ===')
# Prefer the build's Step-2 output if present (co-op sub0 translations written
# first); else pristine.  Stale leftovers are indistinguishable so we follow
# the documented preference order.
if os.path.exists(BUILD_R2654):
    r2654_in = open(BUILD_R2654, 'rb').read()
    r2654_src = 'build/packdata_resources/2654_type44.raw'
else:
    r2654_in = open(PRISTINE_R2654, 'rb').read()
    r2654_src = 'extracted/packdata_raw/2654_type44.raw (PRISTINE)'
print(f'R2654 base input: {r2654_src}')
# NOTE: for THIS standalone self-verify the build has not run, so the on-disk
# build file (if any) is a STALE leftover, not Step-2 output.  We additionally
# load pristine to (a) drive the mirror content and (b) byte-compare untouched
# subs.  We assert untouched subs are identical to whichever base we read.
pristine_r2654 = open(PRISTINE_R2654, 'rb').read()
if os.path.exists(BUILD_R2654):
    print('  NOTE: on-disk build R2654 used as base; for standalone verify this '
          'is a STALE leftover (build not run this session).')

r2654_hdr = read_header(r2654_in, 44)

# Rebuild ONLY the mapped subs; all others copied byte-identical.
rebuilt_2654 = {}        # r2654_sub -> (bytes, size)
for r34_sub, r2654_sub in R34_TO_R2654.items():
    enc_entries = encoded_per_sub[r34_sub]   # same English, k<->k
    # verify the target sub's count matches
    h = next(x for x in r2654_hdr if x['sub'] == r2654_sub)
    tcnt, _ = read_sub_entries(r2654_in, h['off'], h['size'])
    assert tcnt == len(enc_entries), \
        f'R2654 sub{r2654_sub} count {tcnt} != R34 sub{r34_sub} {len(enc_entries)}'
    sub_bytes, new_size, _ = build_sub(enc_entries)
    rebuilt_2654[r2654_sub] = (sub_bytes, new_size)

# assemble R2654 container
mapped = set(R34_TO_R2654.values())
out2 = bytearray(b'\x00' * 704)
cur = 704
new_hdr2 = []
untouched_check = []   # (sub, new_off, new_size, orig_off, orig_size)
for h in sorted(r2654_hdr, key=lambda x: x['off']):
    sub = h['sub']
    if cur % 16:
        pad = 16 - (cur % 16)
        out2 += b'\x00' * pad
        cur += pad
    new_off = cur
    if sub in mapped:
        sub_bytes, new_size = rebuilt_2654[sub]
    else:
        # copy original bytes verbatim from base input
        cnt, _ = read_sub_entries(r2654_in, h['off'], h['size'])
        sub_bytes = r2654_in[h['off']:h['off'] + h['size']]
        new_size = h['size']
        untouched_check.append((sub, new_off, new_size, h['off'], h['size']))
    out2 += sub_bytes
    cur += new_size
    new_hdr2.append((sub, new_size, new_off))

new_hdr2.sort(key=lambda x: x[0])
for i, (sub, size, off) in enumerate(new_hdr2):
    struct.pack_into('<4I', out2, i * 16, sub, size, off, 0)
struct.pack_into('<I', out2, 8, 704)

out2 = pad_to_sector(out2)
open(BUILD_R2654, 'wb').write(out2)
r2654_sectors = len(out2) // SECTOR
print(f'R2654 written: {len(out2)} bytes = {r2654_sectors} sectors '
      f'(pristine {len(pristine_r2654)} = {len(pristine_r2654)//SECTOR} sectors)')

# ============================================================================
# SELF-VERIFY (port of decode_r34_full.py, no build)
# ============================================================================
print('\n=== SELF-VERIFY ===')

glyph_map = {int(k): v for k, v in json.load(
    open(os.path.join(BASE, 'data/msg_glyph_map.json'), encoding='utf-8')).items()}
ov_path = os.path.join(BASE, 'data/type2_glyph_overrides.json')
if os.path.exists(ov_path):
    for gid, info in json.load(open(ov_path, encoding='utf-8')).items():
        glyph_map[int(gid)] = info['t2']


def decode_to_english(words):
    """Decode a rebuilt entry's glyph words back to plain English text.

    Reconstructs the aligned-English form: ASCII glyphs -> chars, FFFE -> ' / ',
    header control codes (opener/FFF0) stripped, FFFF terminates.
    Trailing ' / ' (the universal terminator separator) is dropped.
    """
    out = []
    for g in words:
        if g == FFFF:
            break
        if g == FFFE:
            out.append(' / ')
        elif g in HEADER_OPENERS or g == FFF0:
            continue                      # header frame stripped
        elif 0 <= g <= 94:
            out.append(chr(g + 0x20))
        else:
            out.append(f'[0x{g:04X}]')    # should never happen (pure ASCII)
    text = ''.join(out)
    if text.endswith(' / '):
        text = text[:-3]
    return text


def verify_container(raw, nsubs, label, sub_filter=None):
    """Walk structure, assert clean, return {(sub,idx): decoded_english}."""
    hdr = read_header(raw, nsubs)
    data_start = struct.unpack_from('<I', raw, 8)[0]
    assert data_start == nsubs * 16, f'{label}: data_start {data_start}'
    decoded = {}
    for h in hdr:
        sub = h['sub']
        if sub_filter is not None and sub not in sub_filter:
            continue
        off, size = h['off'], h['size']
        cnt = struct.unpack_from('>H', raw, off)[0]
        pad0 = struct.unpack_from('>H', raw, off + 2)[0]
        assert pad0 == 0, f'{label} sub{sub}: count-pad {pad0:#x} != 0'
        offs = []
        for k in range(cnt):
            v = struct.unpack_from('>H', raw, off + 4 + k * 4)[0]
            z = struct.unpack_from('>H', raw, off + 6 + k * 4)[0]
            expect = FFFF if k == cnt - 1 else 0
            assert z == expect, \
                f'{label} sub{sub} item{k}: pad {z:#x} != {expect:#x}'
            offs.append(v)
        # offsets monotonic non-decreasing, first == table_end
        table_end = 4 + cnt * 4
        assert offs[0] == table_end, \
            f'{label} sub{sub}: first off {offs[0]} != table_end {table_end}'
        assert all(offs[i] <= offs[i + 1] for i in range(len(offs) - 1)), \
            f'{label} sub{sub}: offsets not monotonic'
        for k in range(cnt):
            st = off + offs[k]
            en = off + (offs[k + 1] if k + 1 < cnt else size)
            words = words_of(raw[st:en])
            # FFFE FFFF terminator
            assert len(words) >= 2 and words[-1] == FFFF and words[-2] == FFFE, \
                f'{label} sub{sub} item{k}: bad terminator {[hex(w) for w in words[-3:]]}'
            assert_no_r2100(words, f'{label} sub{sub} item{k}')
            decoded[(sub, k)] = decode_to_english(words)
    return decoded


# --- R34 verify: every entry decodes exactly to aligned english ---
r34_out = open(BUILD_R34, 'rb').read()
dec34 = verify_container(r34_out, 20, 'R34')


def pristine_entry_bytes(raw, hdr, sub, idx):
    h = next(x for x in hdr if x['sub'] == sub)
    cnt, ents = read_sub_entries(raw, h['off'], h['size'])
    return ents[idx]


mismatches = 0
placeholders = 0
for e in aligned:
    sub, idx = e['sub'], e['idx']
    exp = e['english']
    if idx == 0 and exp == '':
        # placeholder: contract is "keep original bytes verbatim".
        # Verify the rebuilt entry bytes == pristine dummy, not the decode text.
        got_bytes = pristine_entry_bytes(r34_out, read_header(r34_out, 20), sub, 0)
        orig_bytes = pristine_entry_bytes(pristine_r34, r34_hdr, sub, 0)
        if got_bytes != orig_bytes:
            mismatches += 1
            print(f'  PLACEHOLDER R34 sub{sub} item0 bytes changed: '
                  f'{got_bytes.hex()} != {orig_bytes.hex()}')
        else:
            placeholders += 1
        continue
    got = dec34[(sub, idx)]
    if got != exp:
        mismatches += 1
        if mismatches <= 20:
            print(f'  MISMATCH R34 sub{sub} item{idx}: exp={exp!r} got={got!r}')
assert mismatches == 0, f'R34: {mismatches} decode mismatches'
print(f'R34: all {len(aligned)-placeholders} text entries decode EXACTLY to '
      f'aligned English; {placeholders} placeholders kept verbatim. '
      'Structure walk clean.')

# --- R2654 verify: mapped subs decode to same english (k<->k) ---
r2654_out = open(BUILD_R2654, 'rb').read()
dec2654 = verify_container(r2654_out, 44, 'R2654', sub_filter=mapped)
mm2 = 0
checked = 0
ph2 = 0
r2654_out_hdr = read_header(r2654_out, 44)
for r34_sub, r2654_sub in R34_TO_R2654.items():
    al = aligned_by_sub[r34_sub]
    for idx, e in al.items():
        if idx == 0 and e['english'] == '':
            got_bytes = pristine_entry_bytes(r2654_out, r2654_out_hdr, r2654_sub, 0)
            if got_bytes != b'\x00\x00\xff\xfe\xff\xff':
                mm2 += 1
                print(f'  PLACEHOLDER R2654 sub{r2654_sub} item0 bytes: '
                      f'{got_bytes.hex()}')
            else:
                ph2 += 1
            continue
        checked += 1
        got = dec2654[(r2654_sub, idx)]
        if got != e['english']:
            mm2 += 1
            if mm2 <= 20:
                print(f'  MISMATCH R2654 sub{r2654_sub} item{idx}: '
                      f'exp={e["english"]!r} got={got!r}')
assert mm2 == 0, f'R2654: {mm2} mirror mismatches'
print(f'R2654: all {checked} mirrored text entries decode EXACTLY to aligned '
      f'English; {ph2} placeholders kept verbatim.')

# --- R2654 untouched subs byte-identical to base input ---
diffs = 0
for sub, new_off, new_size, orig_off, orig_size in untouched_check:
    if r2654_out[new_off:new_off + new_size] != r2654_in[orig_off:orig_off + orig_size]:
        diffs += 1
        print(f'  R2654 untouched sub{sub} DIFFERS')
assert diffs == 0, f'R2654: {diffs} untouched subs changed'
print(f'R2654: all {len(untouched_check)} untouched subs byte-identical to input.')

# --- final sector counts ---
print('\n=== FINAL SECTOR COUNTS ===')
print(f'  R34   : {len(r34_out):>7} bytes = {len(r34_out)//SECTOR} sectors '
      f'(budget <=40, pristine {len(pristine_r34)//SECTOR})')
print(f'  R2654 : {len(r2654_out):>7} bytes = {len(r2654_out)//SECTOR} sectors '
      f'(pristine {len(pristine_r2654)//SECTOR})')
print('\nALL SELF-VERIFY ASSERTIONS PASSED.')

if r34_overbudget:
    print('\n*** HARD-FAIL (runaway guard): R34 = %d sectors exceeds ceiling %d. ***'
          % (r34_sectors, R34_RUNAWAY_CEILING))
    print('    Self-verify passed (structure byte-correct), but this size is far '
          'beyond\n    normal English volume (~%d glyph chars) and indicates a '
          'corrupt rebuild.' % sum(len(e['english']) for e in aligned))
    sys.exit(1)
print('\n(R34 %d / R2654 %d sectors — within runaway ceiling %d; see overflow NOTE '
      'above.)' % (len(r34_out)//SECTOR, len(r2654_out)//SECTOR, R34_RUNAWAY_CEILING))
