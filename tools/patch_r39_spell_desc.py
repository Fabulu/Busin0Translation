"""
patch_r39_spell_desc.py — inject English SPELL DESCRIPTIONS into R39 block 2.

Runs AFTER build/inject_r39_v2.py (Step 3) and build/inject_r39_quest.py (Step 3.2),
operating IN-PLACE on build/packdata_resources/0039_type15.raw so it composes with the
equipment + quest edits. If that file is absent (e.g. R39_PRISTINE.flag dropped our
patched R39), this script ABORTS with a clear error — it must run inside the patched-R39
path or not at all.

R39 (0039_type15.raw) layout (15-record LE header, 16 bytes each = bytes 0..240):
  rec[0]  off=240   size=2462  block0  equipment/menu msgs   (inject_r39_v2)
  rec[1]  off=2704  size=936   block1  spell NAMES (pristine, romanized by atlas)
  rec[2]  off=3648  size=2148  block2  spell DESCRIPTIONS   <-- THIS PATCHER
  rec[3]  off=5808  ...        block3  combat-skill names
  rec[4]  off=6640  ...        block4  combo/tactic descriptions
  rec[5..14]                   ...     quest data (grown by inject_r39_quest)

BLOCK 2 internal format (58 FFFF-records, BE u16 glyph-cell stream):
  g1  = offset table: BE-u16 (value, 0x0000) pairs. slot0 value = record COUNT (57,
        self-referential header, PRESERVED VERBATIM). slots 1..57 = the BLOCK-2-RELATIVE
        byte offset of records g2..g58. Verified: value == record start byte (base = 0,
        i.e. relative to block-2 start). Pair-stride: odd u16 always 0x0000.
  g2  = [0x0000, 0xFFFE]  separator (space + line break) — PRESERVED VERBATIM.
  g3..g58 = the 56 spell descriptions.  g# == 1-based FFFF-record index.

ENCODING (the shared spell-font atlas == data/english_glyph_table.json):
  The spell font shares the SAME atlas as the spell NAMES (R39 block1, GS TBP
  0x3000), which carries the FULL char-32 set: A-Z (ids 33-58), a-z (ids 65-90),
  0-9 (ids 16-25), space (id 0), and punctuation ('.'=14, ','=12, "'"=7, '-'=13,
  '/'=15, ':'=26, etc.).  So descriptions render PROPER-CASE with punctuation —
  we encode via english_glyph_table.json exactly like block0 (inject_r39_v2.py),
  with NO lowercasing and NO punctuation-drop.  (The old LOWERCASE-only path that
  used a reverse-msg_glyph_map subset + .lower() + DROP_CHARS is preserved as a
  one-line revert behind USE_ENGLISH_ATLAS=False.)

  ' / '  -> 0xFFFE line break.   Each record terminates with 0xFFFF.
  Pristine records (g55/g56/g57 — no real source text) are copied verbatim (kept JP).

This is a SIZE-CHANGING block-2 rebuild (same risk class as inject_r39_quest, which once
caused the request softlock).  A PRISTINE-DIFF GATE asserts every byte OUTSIDE block 2 is
unchanged (modulo the constant grow-shift of the post-block-2 tail), and the header records
for recs 3..14 shift by exactly the block-2 delta while their SIZES are preserved.
"""

import struct, json, os, sys, math

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)
# stdout is cp1252 on Windows — NEVER print Japanese. ASCII-only summaries.

SECTOR = 2048
HEADER_RECORDS = 15
HEADER_BYTES = HEADER_RECORDS * 16  # 240

BUILD_PATH    = 'build/packdata_resources/0039_type15.raw'
PRISTINE_PATH = 'extracted/packdata_raw/0039_type15.raw'
JSON_PATH     = 'data/r39_spell_descriptions.json'

PRISTINE_JP_RECORDS = (55, 56, 57)  # ship pristine JP (no real source text)


# ---------------------------------------------------------------------------
# 0. Build the spell-font encoder.
#
# PROVEN (prior assessment): spell NAMES (R39 block1) already render PROPER-CASE
# through data/english_glyph_table.json, and that atlas (shared by names AND
# descriptions, GS TBP 0x3000) carries the FULL char-32 set — A-Z, a-z, 0-9, and
# punctuation ('.'=14, ','=12, "'"=7, '-'=13, '/'=15, etc.). So descriptions can,
# and now DO, render proper-case + punctuation. We mirror the proven block0
# encoder in build/inject_r39_v2.py: english_glyph_table.json, direct char->id,
# ' / ' -> 0xFFFE line break, NO lowercasing, NO punctuation-drop.
#
# REVERT SWITCH: flip USE_ENGLISH_ATLAS = False to fall back to the OLD lowercase
# spell-font encoder (reverse of msg_glyph_map, .lower() + DROP_CHARS) if a live
# test ever shows garble. One-line flip; everything else (offset-table rebuild,
# pristine-diff gate, g55/56/57 pristine) is unchanged.
# ---------------------------------------------------------------------------
USE_ENGLISH_ATLAS = True


def build_legacy_encoder():
    """OLD lowercase spell-font encoder (reverse of msg_glyph_map, ascii region).
    Kept ONLY as the revert path behind USE_ENGLISH_ATLAS = False."""
    m = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
    enc = {}  # ascii char -> glyph id
    for k, v in m.items():
        if not (isinstance(v, str) and len(v) == 1):
            continue
        o = ord(v)
        ch = None
        if 0x21 <= o <= 0x7E:            # halfwidth ascii (lowercase a-z live here)
            ch = v
        elif 0xFF01 <= o <= 0xFF5E:      # fullwidth ascii (digits / punct live here)
            ch = chr(o - 0xFEE0)
        if ch is None:
            continue
        # keep only the SPELL-FONT usable set; first id wins (lowest, stable)
        if ch in 'abcdefghijklmnopqrstuvwxyz0123456789/:?!~%':
            enc.setdefault(ch, int(k))
    enc[' '] = 0  # space = id 0 (confirmed by g2 separator and HP descriptions)
    return enc


# The English atlas: direct char -> glyph id (A=33, a=65, '.'=14, ','=12, etc.).
ENGLISH_ATLAS = {k: int(v) for k, v in
                 json.load(open('data/english_glyph_table.json', encoding='utf-8')).items()}

LEGACY_ENCODER = None  # lazily built only if the revert path is taken
DROP_CHARS = set(".,'-()\"")  # legacy-only: font subset lacks these


def encode_english(text):
    """Encode an English string to a list of BE-u16 spell-font glyph ids.
    ' / ' becomes a 0xFFFE line break.  Returns the glyph list WITHOUT the
    trailing 0xFFFF terminator.  Raises on any char the atlas cannot draw.

    USE_ENGLISH_ATLAS=True (default): mirrors build/inject_r39_v2.py's proven
    block0 encoder — full proper-case + punctuation via english_glyph_table.json,
    NO lowercasing, NO punctuation-drop.
    USE_ENGLISH_ATLAS=False: legacy lowercase+drop path (revert)."""
    global LEGACY_ENCODER
    if not USE_ENGLISH_ATLAS:
        if LEGACY_ENCODER is None:
            LEGACY_ENCODER = build_legacy_encoder()
        text = text.lower().replace(';', ' / ')
        parts = text.split(' / ')
        glyphs = []
        for pi, part in enumerate(parts):
            if pi > 0:
                glyphs.append(0xFFFE)
            for ch in part.strip():
                if ch in DROP_CHARS:
                    continue
                gid = LEGACY_ENCODER.get(ch)
                if gid is None:
                    raise ValueError(
                        f"spell font cannot encode char {ch!r} (U+{ord(ch):04X}) "
                        f"in {text!r} — extend the encoder or rephrase the JSON entry")
                glyphs.append(gid)
        return glyphs

    # Proper-case English atlas path (default).
    parts = text.split(' / ')
    glyphs = []
    for pi, part in enumerate(parts):
        if pi > 0:
            glyphs.append(0xFFFE)
        for ch in part.strip():
            if ch in ENGLISH_ATLAS:
                glyphs.append(ENGLISH_ATLAS[ch])
            else:
                raise ValueError(
                    f"english atlas cannot encode char {ch!r} (U+{ord(ch):04X}) "
                    f"in {text!r} — extend english_glyph_table.json or rephrase")
    return glyphs


# ---------------------------------------------------------------------------
# 1. Block-2 record split / offset-table helpers
# ---------------------------------------------------------------------------
def split_records(block):
    """Return list of records; each is the list of BE-u16 cells BEFORE its 0xFFFF.
    Record k (0-based) == g(k+1).  Asserts the block ends exactly on a 0xFFFF."""
    recs = []
    cur = []
    pos = 0
    n = len(block)
    while pos + 1 < n:
        w = struct.unpack_from('>H', block, pos)[0]
        if w == 0xFFFF:
            recs.append(cur)
            cur = []
        else:
            cur.append(w)
        pos += 2
    # the last 0xFFFF must land exactly at the block end (no trailing bytes)
    assert pos == n, f"block2 not 2-byte aligned: pos={pos} n={n}"
    return recs


def cells_to_bytes(cells):
    out = bytearray()
    for c in cells:
        out += struct.pack('>H', c)
    out += struct.pack('>H', 0xFFFF)
    return out


# ---------------------------------------------------------------------------
# 2. Load inputs
# ---------------------------------------------------------------------------
if not os.path.exists(BUILD_PATH):
    sys.stderr.write(
        f"ERROR: {BUILD_PATH} not found. patch_r39_spell_desc must run AFTER "
        f"inject_r39_v2 + inject_r39_quest (R39_PRISTINE.flag may have dropped "
        f"the patched R39). Aborting — refusing to patch a non-existent file.\n")
    sys.exit(1)

raw = bytearray(open(BUILD_PATH, 'rb').read())
pristine = open(PRISTINE_PATH, 'rb').read()

spec = json.load(open(JSON_PATH, encoding='utf-8'))
descriptions = {int(k): v for k, v in spec['descriptions'].items()}
json_pristine = set(spec.get('_pristine_jp_records', list(PRISTINE_JP_RECORDS)))
print(f"R39 spell-desc: {len(raw)} bytes in, {len(descriptions)} english descriptions")

# ---------------------------------------------------------------------------
# 3. Parse the 15-record header; locate block 2
# ---------------------------------------------------------------------------
header = []
for i in range(HEADER_RECORDS):
    idx, size, off, z = struct.unpack_from('<4I', raw, i * 16)
    header.append([idx, size, off, z])

B2_OFF  = header[2][2]
B2_SIZE = header[2][1]
assert B2_OFF == 3648 and B2_SIZE == 2148, \
    f"block2 header unexpected: off={B2_OFF} size={B2_SIZE}"
B2_END = B2_OFF + B2_SIZE  # 5796 — first byte AFTER block 2

# The post-quest build leaves block 2 byte-identical to pristine; assert it so the
# rebuild starts from a known-good block 2.
assert raw[B2_OFF:B2_END] == pristine[B2_OFF:B2_END], \
    "block2 in build file differs from pristine — unexpected upstream edit; aborting."

block2 = raw[B2_OFF:B2_END]
records = split_records(block2)  # records[k] == g(k+1)
assert len(records) == 58, f"expected 58 block2 records, got {len(records)}"

# ---------------------------------------------------------------------------
# 4. Parse + validate the offset table (g1 = records[0])
# ---------------------------------------------------------------------------
ot = records[0]                      # flat list of BE-u16 cells
# Verified stride: value0, 0x0000, value1, 0x0000, ..., valueN  — i.e. 58 VALUES at
# even indices, a 0x0000 padder after every value EXCEPT THE LAST.  So cell count =
# 2*58 - 1 = 115 (odd).  value0 = self-referential record COUNT (57); value1..57 =
# block-2-relative byte offsets of records g2..g58.
assert len(ot) % 2 == 1, f"offset table cell count {len(ot)} (expected odd: val,0,val,..,val)"
ot_values = ot[0::2]
ot_zeros  = ot[1::2]
assert set(ot_zeros) == {0}, "offset-table inter-value padders are not all 0x0000"
HEADER_COUNT = ot_values[0]          # self-referential record count (57) — PRESERVE
assert HEADER_COUNT == 57, f"offset-table header count expected 57, got {HEADER_COUNT}"
# slots 1..57 = block-2-relative byte offsets of records g2..g58.
data_offsets = ot_values[1:]
assert len(data_offsets) == 57, f"expected 57 data offsets, got {len(data_offsets)}"

# Compute the pristine record START offsets to confirm the table semantics + base.
starts = []
pos = 0
for k, rc in enumerate(records):
    starts.append(pos)
    pos += len(rc) * 2 + 2           # cells + FFFF
# records g2..g58 start at starts[1..57]; the table values must equal those.
for j, val in enumerate(data_offsets):
    gstart = starts[j + 1]
    assert val == gstart, \
        f"offset-table slot {j+1} ({val}) != g{j+2} start ({gstart}) — base assumption wrong"
print(f"offset-table format OK: 1 header(count={HEADER_COUNT}) + 57 block-relative "
      f"start offsets, (value,0x0000) pair-stride")

# ---------------------------------------------------------------------------
# 5. Re-encode g3..g58 (records[2..57]); keep g1/g2 + pristine g55/56/57 verbatim
# ---------------------------------------------------------------------------
new_records = [list(r) for r in records]  # start from pristine (verbatim copies)
encoded = 0
budget_notes = []
for g in range(3, 59):               # g3..g58
    k = g - 1                        # records index
    if g in json_pristine or g not in descriptions:
        continue                     # keep pristine JP (g55/56/57 + any omitted)
    en = descriptions[g].strip()
    cells = encode_english(en)
    new_records[k] = cells
    encoded += 1
    old_cells = len(records[k])
    if len(cells) != old_cells:
        budget_notes.append((g, old_cells, len(cells), en))
print(f"re-encoded {encoded} english spell descriptions")

# ---------------------------------------------------------------------------
# 6. Rebuild the offset table (g1) to the NEW record start offsets
#    Layout: same (value,0x0000) pair-stride, same header-count slot, 57 data slots.
# ---------------------------------------------------------------------------
# First lay out g2..g58 bodies AFTER a placeholder g1 of the SAME cell length as the
# original (the table size is fixed: 1 header + 57 entries => identical cell count,
# so g1's byte length never changes and downstream offsets are stable to compute).
g1_len_cells = len(records[0])
new_starts = []
pos = 0
for k in range(58):
    new_starts.append(pos)
    if k == 0:
        body = g1_len_cells          # placeholder, real cells filled below
    else:
        body = len(new_records[k])
    pos += body * 2 + 2

# Build the new g1 cells with the EXACT pristine stride: value, 0, value, 0, ...,
# value (no trailing 0 after the last value).  58 values = count + 57 offsets.
values = [HEADER_COUNT] + [new_starts[j] for j in range(1, 58)]  # 58 values
for v in values:
    assert 0 <= v <= 0xFFFF, f"offset-table value {v} overflows u16"
new_ot = []
for i, v in enumerate(values):
    new_ot.append(v)
    if i != len(values) - 1:         # 0x0000 padder after every value but the last
        new_ot.append(0)
assert len(new_ot) == g1_len_cells, \
    f"rebuilt offset table cell count {len(new_ot)} != original {g1_len_cells}"
new_records[0] = new_ot

# ---------------------------------------------------------------------------
# 7. Serialize the new block 2 and compute the delta
# ---------------------------------------------------------------------------
new_block2 = bytearray()
for rc in new_records:
    new_block2 += cells_to_bytes(rc)
new_b2_size = len(new_block2)
delta = new_b2_size - B2_SIZE
print(f"block2: {B2_SIZE} -> {new_b2_size} bytes (delta {delta:+d})")

# ---------------------------------------------------------------------------
# 8. Reassemble: [0:B2_OFF] + new_block2 + raw[B2_END:]  (tail shifts by delta)
# ---------------------------------------------------------------------------
prefix = raw[:B2_OFF]            # bytes 0..3648 (header + block0 + block1)
tail   = raw[B2_END:]           # blocks 3..14 + quest data (verbatim, just shifted)
out = bytearray(prefix) + new_block2 + tail

# ---------------------------------------------------------------------------
# 9. Rewrite header records: rec2 size := new; recs with off >= B2_END shift +delta.
#    rec sizes (except rec2) are preserved.  recs 0,1 unchanged.
# ---------------------------------------------------------------------------
for i in range(HEADER_RECORDS):
    idx, size, off, z = header[i]
    if i == 2:
        size = new_b2_size
    elif off >= B2_END:
        off = off + delta
    struct.pack_into('<4I', out, i * 16, idx, size, off, z)

# ---------------------------------------------------------------------------
# 10. PRISTINE-DIFF GATE — every byte OUTSIDE block 2 must be unchanged.
#   (a) header[0:32] (recs 0,1) byte-identical
#   (b) bytes [32:B2_OFF] (rec2 desc not counted; block0+block1 region after header)
#       — i.e. everything from end-of-header to start-of-block2 — byte-identical
#   (c) the post-block-2 tail appears VERBATIM at its shifted position
#   (d) header recs 3..14: size unchanged, offset == old + delta
# ---------------------------------------------------------------------------
# (a) recs 0 and 1 unchanged
assert out[0:32] == raw[0:32], "PRISTINE-DIFF FAIL: header recs 0/1 changed"
# (b) bytes from header end to block2 start (240..3648) unchanged
assert out[HEADER_BYTES:B2_OFF] == raw[HEADER_BYTES:B2_OFF], \
    "PRISTINE-DIFF FAIL: block0/block1 bytes (240..3648) changed"
# (c) tail verbatim at shifted position
new_b2_end = B2_OFF + new_b2_size
assert out[new_b2_end:new_b2_end + len(tail)] == tail, \
    "PRISTINE-DIFF FAIL: post-block2 tail (blocks 3..14 + quest) not verbatim after shift"
# (d) header recs 3..14
for i in range(HEADER_RECORDS):
    if i == 2:
        continue
    nidx, nsize, noff, nz = struct.unpack_from('<4I', out, i * 16)
    oidx, osize, ooff, oz = header[i]
    assert nsize == osize, f"PRISTINE-DIFF FAIL: rec[{i}] size changed {osize}->{nsize}"
    exp_off = ooff + delta if ooff >= B2_END else ooff
    assert noff == exp_off, f"PRISTINE-DIFF FAIL: rec[{i}] off {noff} != {exp_off}"
print("PRISTINE-DIFF GATE PASSED: all bytes outside block 2 unchanged; "
      "header recs 3..14 shifted by delta with sizes preserved.")

# ---------------------------------------------------------------------------
# 11. Pad to sector boundary; write back.
# ---------------------------------------------------------------------------
sectors = math.ceil(len(out) / SECTOR)
padded = sectors * SECTOR
out += b'\x00' * (padded - len(out))
with open(BUILD_PATH, 'wb') as f:
    f.write(out)
print(f"Written {len(out)} bytes ({sectors} sectors) to {BUILD_PATH}")
if budget_notes:
    grew = sum(1 for _, o, n, _ in budget_notes if n > o)
    print(f"  {len(budget_notes)} records changed cell length ({grew} grew); "
          f"block2 offset table + header recompute absorbs the size change.")
