"""
patch_r39_aa.py — inject English AA (Allied Action) text into R39 blocks 3, 4 and 5.

  block 3 (header rec[3]) : AA / technique NAMES        (40 records; g02..g40)
  block 4 (header rec[4]) : AA DESCRIPTIONS g03..g39 + party REQUIREMENTS g40..g85
  block 5 (header rec[5]) : AA-setup UI messages        (8 records; g02..g08)

Runs AFTER build/inject_r39_v2.py (Step 3), tools/patch_r39_inline.py (Step 3.1),
build/inject_r39_quest.py (Step 3.2) and tools/patch_r39_spell_desc.py (Step 3.3),
operating IN-PLACE on build/packdata_resources/0039_type15.raw.  Block offsets are
read from the CURRENT 15-record header (block 2 grows in Step 3.3, so blocks 3+
sit at shifted offsets).  If the build file is absent the script ABORTS.

Data: data/r39_aa_descriptions.json — 1-based FFFF-record (gNN) keys per block.
FAITHFUL per-record enumeration: one JSON entry per FFFF record, no dedup/split
(the pre-v159 spell-description misalignment must never be repeated).  Records
absent from the JSON (e.g. block4 g66, the empty record) are preserved verbatim.

Record formats (BE u16 glyph cells, records separated by 0xFFFF):
  g01 of each block = offset table: (value, 0x0000) pair-stride, value0 = record
      COUNT (self-referential, PRESERVED), values 1..N = block-relative byte
      offsets of g02..g(N+1).  Same layout patch_r39_spell_desc.py proved for
      block 2 (shipped + working in-game since v159).
  Every other record = content cells + 0xFFFE, then the 0xFFFF separator.

Block-4 description records mimic the pristine window discipline exactly:
ALWAYS 3 lines, EVERY line padded with glyph id 0 (space) to 27 visible cells
(the pristine g02 template is 3 x 27 spaces; all JP descriptions are 3 lines of
27 visible cells + trailing pads).  The JP inline FF07/FFF0 highlight codes are
dropped.  Names / requirements / UI messages are single-line unpadded records,
like their pristine counterparts.

This is a SIZE-CHANGING rebuild of blocks 3/4/5 (same risk class as Step 3.3).
A PRISTINE-DIFF GATE asserts every byte OUTSIDE blocks 3/4/5 is unchanged
(modulo the cumulative shift of the tail), all other header record SIZES are
preserved, and offsets shift by exactly the accumulated delta.  Pre-gates
assert blocks 4/5 enter byte-identical to pristine and block 3 enters at
pristine size/record shape (records g02..g10 may differ in CONTENT ONLY —
patch_r39_inline's fixed-size English abbreviations, which this patcher
supersedes with the full R1361/R1362 strip names).

Standalone:  python tools/patch_r39_aa.py [target_raw]
  target_raw defaults to build/packdata_resources/0039_type15.raw; pass a copy
  (e.g. in a scratch dir) for a dry-run that leaves the build tree untouched.
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
JSON_PATH     = 'data/r39_aa_descriptions.json'

DESC_LINE_CELLS = 27   # visible cells per block-4 description line (pristine)
DESC_LINES      = 3    # lines per block-4 description record (pristine)

# pristine per-block record counts (incl. the g01 offset table)
EXPECTED = {3: (40, 39), 4: (85, 84), 5: (8, 7)}   # blk -> (records, count_hdr)

TARGET = sys.argv[1] if len(sys.argv) > 1 else BUILD_PATH

# ---------------------------------------------------------------------------
# 0. Encoder — identical policy to patch_r39_spell_desc.py (english atlas,
#    proper case + punctuation, NO lowercasing, NO drops).
# ---------------------------------------------------------------------------
ENGLISH_ATLAS = {k: int(v) for k, v in
                 json.load(open('data/english_glyph_table.json', encoding='utf-8')).items()}

def encode_line(text):
    """One visible line -> list of BE-u16 glyph ids (no FFFE/FFFF)."""
    glyphs = []
    for ch in text:
        if ch in ENGLISH_ATLAS:
            glyphs.append(ENGLISH_ATLAS[ch])
        else:
            raise ValueError(
                f"english atlas cannot encode char {ch!r} (U+{ord(ch):04X}) "
                f"in {text!r} — extend english_glyph_table.json or rephrase")
    return glyphs


# ---------------------------------------------------------------------------
# 1. Record split / serialize helpers (same semantics as patch_r39_spell_desc)
# ---------------------------------------------------------------------------
def split_records(block):
    recs, cur, pos, n = [], [], 0, len(block)
    while pos + 1 < n:
        w = struct.unpack_from('>H', block, pos)[0]
        if w == 0xFFFF:
            recs.append(cur); cur = []
        else:
            cur.append(w)
        pos += 2
    assert pos == n, f"block not 2-byte aligned: pos={pos} n={n}"
    assert not cur, "block does not end on a 0xFFFF record separator"
    return recs

def cells_to_bytes(cells):
    out = bytearray()
    for c in cells:
        out += struct.pack('>H', c)
    out += struct.pack('>H', 0xFFFF)
    return out

def parse_offset_table(ot, expected_count):
    assert len(ot) % 2 == 1, f"offset table cell count {len(ot)} not odd (val,0,..,val)"
    vals, zeros = ot[0::2], ot[1::2]
    assert set(zeros) <= {0}, "offset-table padders are not all 0x0000"
    assert vals[0] == expected_count, \
        f"offset-table count header {vals[0]} != expected {expected_count}"
    return vals

def rebuild_block(records, new_records, blk):
    """Serialize records (g01 rebuilt to new start offsets). Returns bytes."""
    g1_len = len(records[0])
    n = len(records)
    # lay out with a fixed-length g01 placeholder
    starts, pos = [], 0
    for k in range(n):
        body = g1_len if k == 0 else len(new_records[k])
        starts.append(pos)
        pos += body * 2 + 2
    count_hdr = EXPECTED[blk][1]
    values = [count_hdr] + [starts[j] for j in range(1, n)]
    for v in values:
        assert 0 <= v <= 0xFFFF, f"blk{blk} offset-table value {v} overflows u16"
    new_ot = []
    for i, v in enumerate(values):
        new_ot.append(v)
        if i != len(values) - 1:
            new_ot.append(0)
    assert len(new_ot) == g1_len, \
        f"blk{blk} rebuilt offset table cells {len(new_ot)} != original {g1_len}"
    new_records[0] = new_ot
    out = bytearray()
    for rc in new_records:
        out += cells_to_bytes(rc)
    return out


# ---------------------------------------------------------------------------
# 2. Load inputs
# ---------------------------------------------------------------------------
if not os.path.exists(TARGET):
    sys.stderr.write(
        f"ERROR: {TARGET} not found. patch_r39_aa must run AFTER inject_r39_v2 "
        f"(R39_PRISTINE.flag may have dropped the patched R39). Aborting.\n")
    sys.exit(1)

raw = bytearray(open(TARGET, 'rb').read())
pristine = open(PRISTINE_PATH, 'rb').read()
spec = json.load(open(JSON_PATH, encoding='utf-8'))

names        = {int(k): v for k, v in spec['block3_names'].items()}
descriptions = {int(k): v for k, v in spec['block4_descriptions'].items()}
requirements = {int(k): v for k, v in spec['block4_requirements'].items()}
messages     = {int(k): v for k, v in spec['block5_messages'].items()}
print(f"R39 AA: {len(raw)} bytes in; {len(names)} names, {len(descriptions)} descriptions, "
      f"{len(requirements)} requirements, {len(messages)} ui messages")

header = []
for i in range(HEADER_RECORDS):
    header.append(list(struct.unpack_from('<4I', raw, i * 16)))
phdr = [struct.unpack_from('<4I', pristine, i * 16) for i in range(HEADER_RECORDS)]

# ---------------------------------------------------------------------------
# 3. Pre-gates: blocks 4/5 byte-identical to pristine; block 3 same shape
# ---------------------------------------------------------------------------
blocks = {}
for blk in (3, 4, 5):
    off, size = header[blk][2], header[blk][1]
    poff, psize = phdr[blk][2], phdr[blk][1]
    assert size == psize, f"blk{blk} size {size} != pristine {psize} — unexpected upstream edit"
    cur = bytes(raw[off:off + size])
    pri = pristine[poff:poff + psize]
    recs = split_records(cur)
    precs = split_records(pri)
    nrec, chdr = EXPECTED[blk]
    assert len(recs) == nrec and len(precs) == nrec, \
        f"blk{blk} record count {len(recs)}/{len(precs)} != {nrec}"
    parse_offset_table(recs[0], chdr)
    if blk == 3:
        # inline (Step 3.1) may have re-inked g02..g10 IN PLACE: cell counts equal
        for k in range(nrec):
            assert len(recs[k]) == len(precs[k]), \
                f"blk3 g{k+1:02d} cell count changed ({len(precs[k])}->{len(recs[k])})"
    else:
        assert cur == pri, f"blk{blk} in build differs from pristine — aborting."
    blocks[blk] = recs

# ---------------------------------------------------------------------------
# 4. Build new records
# ---------------------------------------------------------------------------
def line_record(text):
    """content + FFFE (the pristine single-line record shape)."""
    return encode_line(text) + [0xFFFE]

new_blocks = {}
counts = {'names': 0, 'descs': 0, 'reqs': 0, 'msgs': 0}

# block 3 — names
recs = [list(r) for r in blocks[3]]
for g, text in sorted(names.items()):
    assert 2 <= g <= 40, f"block3 name key g{g} out of range"
    recs[g - 1] = line_record(text)
    counts['names'] += 1
new_blocks[3] = rebuild_block(blocks[3], recs, 3)

# block 4 — descriptions (3 x 27 padded) + requirements (single line)
recs = [list(r) for r in blocks[4]]
for g, lines in sorted(descriptions.items()):
    assert 3 <= g <= 39, f"block4 description key g{g} out of range"
    assert isinstance(lines, list) and 1 <= len(lines) <= DESC_LINES, \
        f"block4 g{g}: descriptions must be lists of 1..{DESC_LINES} lines"
    cells = []
    for li in range(DESC_LINES):
        text = lines[li] if li < len(lines) else ''
        enc = encode_line(text)
        assert len(enc) <= DESC_LINE_CELLS, \
            f"block4 g{g} line {li+1} is {len(enc)} cells (max {DESC_LINE_CELLS}): {text!r}"
        cells += enc + [0] * (DESC_LINE_CELLS - len(enc)) + [0xFFFE]
    assert len(cells) == (DESC_LINE_CELLS + 1) * DESC_LINES  # 84, the g02 template shape
    recs[g - 1] = cells
    counts['descs'] += 1
for g, text in sorted(requirements.items()):
    assert 40 <= g <= 85 and g != 66, f"block4 requirement key g{g} out of range (g66 is empty)"
    recs[g - 1] = line_record(text)
    counts['reqs'] += 1
assert recs[65] == list(blocks[4][65]) and len(recs[65]) == 0, "block4 g66 must stay empty"
new_blocks[4] = rebuild_block(blocks[4], recs, 4)

# block 5 — ui messages
recs = [list(r) for r in blocks[5]]
for g, text in sorted(messages.items()):
    assert 2 <= g <= 8, f"block5 message key g{g} out of range"
    recs[g - 1] = line_record(text)
    counts['msgs'] += 1
new_blocks[5] = rebuild_block(blocks[5], recs, 5)

print(f"re-encoded: {counts['names']} names, {counts['descs']} descriptions, "
      f"{counts['reqs']} requirements, {counts['msgs']} ui messages")

# ---------------------------------------------------------------------------
# 5. Reassemble: splice the three rebuilt blocks, preserving inter-block gap
#    bytes verbatim and shifting everything after each block by its delta.
# ---------------------------------------------------------------------------
b3_off, b3_size = header[3][2], header[3][1]
b4_off, b4_size = header[4][2], header[4][1]
b5_off, b5_size = header[5][2], header[5][1]
assert b3_off < b4_off < b5_off, "unexpected block order"

gap34 = raw[b3_off + b3_size:b4_off]          # alignment pad bytes (verbatim)
gap45 = raw[b4_off + b4_size:b5_off]
tail  = raw[b5_off + b5_size:]                # blocks 6..14 (+ quest growth)

out = bytearray(raw[:b3_off])
new_off = {}
new_off[3] = len(out); out += new_blocks[3]
out += gap34
new_off[4] = len(out); out += new_blocks[4]
out += gap45
new_off[5] = len(out); out += new_blocks[5]
tail_pos = len(out)
out += tail

# ---------------------------------------------------------------------------
# 6. Rewrite header: recs 3/4/5 get new size+offset; later recs shift by the
#    total delta; sizes of all other recs are preserved.
# ---------------------------------------------------------------------------
total_delta = sum(len(new_blocks[b]) - header[b][1] for b in (3, 4, 5))
for i in range(HEADER_RECORDS):
    idx, size, off, z = header[i]
    if i in (3, 4, 5):
        size, off = len(new_blocks[i]), new_off[i]
    elif off > b5_off:                        # blocks 6..14 sit after block 5
        off += total_delta
    struct.pack_into('<4I', out, i * 16, idx, size, off, z)

# ---------------------------------------------------------------------------
# 7. PRISTINE-DIFF GATE — every byte outside blocks 3/4/5 unchanged vs input
# ---------------------------------------------------------------------------
assert out[HEADER_BYTES:b3_off] == raw[HEADER_BYTES:b3_off], \
    "PRISTINE-DIFF FAIL: bytes between header and block 3 changed"
assert out[tail_pos:tail_pos + len(tail)] == tail, \
    "PRISTINE-DIFF FAIL: post-block-5 tail not verbatim after shift"
for i in range(HEADER_RECORDS):
    nidx, nsize, noff, nz = struct.unpack_from('<4I', out, i * 16)
    oidx, osize, ooff, oz = header[i]
    assert nidx == oidx and nz == oz, f"rec[{i}] idx/z changed"
    if i in (3, 4, 5):
        continue
    assert nsize == osize, f"PRISTINE-DIFF FAIL: rec[{i}] size changed {osize}->{nsize}"
    exp_off = ooff + total_delta if ooff > b5_off else ooff
    assert noff == exp_off, f"PRISTINE-DIFF FAIL: rec[{i}] off {noff} != {exp_off}"
# re-split the rebuilt blocks and re-validate their offset tables
for blk in (3, 4, 5):
    nrecs = split_records(bytes(new_blocks[blk]))
    nrec, chdr = EXPECTED[blk]
    assert len(nrecs) == nrec
    vals = parse_offset_table(nrecs[0], chdr)
    pos = 0
    for k, rc in enumerate(nrecs):
        if k >= 1:
            assert vals[k] == pos, f"blk{blk} rebuilt table slot {k} ({vals[k]}) != g{k+1} start ({pos})"
        pos += len(rc) * 2 + 2
print(f"PRISTINE-DIFF GATE PASSED: blocks 3/4/5 rebuilt "
      f"({header[3][1]}->{len(new_blocks[3])}, {header[4][1]}->{len(new_blocks[4])}, "
      f"{header[5][1]}->{len(new_blocks[5])} bytes, total delta {total_delta:+d}); "
      f"all other bytes verbatim, header sizes preserved.")

# ---------------------------------------------------------------------------
# 8. Pad to sector boundary; write back.
# ---------------------------------------------------------------------------
sectors = math.ceil(len(out) / SECTOR)
out += b'\x00' * (sectors * SECTOR - len(out))
with open(TARGET, 'wb') as f:
    f.write(out)
print(f"Written {len(out)} bytes ({sectors} sectors) to {TARGET}")
