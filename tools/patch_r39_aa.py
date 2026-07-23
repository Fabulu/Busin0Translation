"""
patch_r39_aa.py — inject English AA (Allied Action) text into R39 blocks 3, 4 and 5,
plus (wave 3, Jul 2026) blocks 10-14.

  block 3  (header rec[3])  : AA / technique NAMES       (40 records; g02..g40)
  block 4  (header rec[4])  : AA DESCRIPTIONS g03..g39 + party REQUIREMENTS g40..g85
  block 5  (header rec[5])  : AA-setup UI messages       (8 records; g02..g08)
  block 10 (header rec[10]) : item SP-activation msgs    (24 records; g03..g24)
  block 11 (header rec[11]) : potential-ability names    (22 records; g02..g22)
  block 12 (header rec[12]) : quest-client / guild names (15 records; g03..g15)
  block 13 (header rec[13]) : equip-category labels      (107 records; ONLY g87..g107
                              patched — g03..g86 carry patch_r39_inline's in-place
                              English ink and are preserved verbatim)
  block 14 (header rec[14]) : party-rank battle msgs     (10 records; g02..g05 +
                              g07..g10 — g06 was already rebuilt variable-size by
                              inject_r39_quest (G650) and is preserved verbatim)

NOTE (bug fixed in passing): inject_r39_quest grows block-14 g06 (+38 bytes) but
does NOT update block 14's OWN g01 offset table, so the shipped table pointed
g07..g10 at stale offsets (238/308/350/392 vs actual 276/346/388/430).  This
patcher rebuilds every touched block's g01 from actual record starts, healing it.

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
MAX_LINE_CELLS  = 27   # widest allowed visible line in blocks 10/14 (block-4 window proof)
MAX_LABEL_CELLS = 24   # widest allowed single-line label in blocks 11/12/13
MAX_REQ_CELLS   = 17   # block-4 AA requirement field: hard-clips at 18 cells on-screen
                       # (measured, issue "All Mem" cutoff); 17 keeps a 1-cell overscan margin

# pristine per-block record counts (incl. the g01 offset table)
EXPECTED = {3: (40, 39), 4: (85, 84), 5: (8, 7),
            10: (24, 23), 11: (22, 21), 12: (15, 14), 13: (107, 106), 14: (10, 9)}
REBUILD_BLOCKS = (3, 4, 5, 10, 11, 12, 13, 14)      # ascending file order (asserted)

# per-block entry-state policy for the pre-gates:
#   'pristine'  — block must enter byte-identical to pristine
#   'shape'     — record count + per-record cell counts must equal pristine
#                 (records may have been re-inked IN PLACE by an upstream step)
#   block 14    — special-cased: g06 may differ in size (inject_r39_quest G650)
ENTRY_POLICY = {3: 'shape', 4: 'pristine', 5: 'pristine',
                10: 'pristine', 11: 'pristine', 12: 'shape', 13: 'shape', 14: 'g06-free'}

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


# highlight tokens for blocks 10/14 message lines ({HL}=0xFF01 on, {/HL}=0xFFF0 off).
# Pristine never lets a highlight span cross an FFFE line break, so tokens must be
# balanced WITHIN each line — enforced below.
HL_TOKENS = {'{HL}': 0xFF01, '{/HL}': 0xFFF0}

def encode_line_tokens(text):
    """One line with optional {HL}/{/HL} tokens -> (cells, visible_count)."""
    cells, visible, pos, depth = [], 0, 0, 0
    while pos < len(text):
        for tok, code in HL_TOKENS.items():
            if text.startswith(tok, pos):
                depth += 1 if code == 0xFF01 else -1
                assert depth in (0, 1), f"unbalanced highlight tokens in {text!r}"
                cells.append(code)
                pos += len(tok)
                break
        else:
            cells += encode_line(text[pos])
            visible += 1
            pos += 1
    assert depth == 0, f"highlight left open at end of line: {text!r}"
    return cells, visible


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
sp_msgs      = {int(k): v for k, v in spec['block10_sp_messages'].items()}
trait_names  = {int(k): v for k, v in spec['block11_trait_names'].items()}
client_names = {int(k): v for k, v in spec['block12_client_names'].items()}
troop_labels = {int(k): v for k, v in spec['block13_troop_labels'].items()}
rank_msgs    = {int(k): v for k, v in spec['block14_rank_messages'].items()}
print(f"R39 AA: {len(raw)} bytes in; {len(names)} names, {len(descriptions)} descriptions, "
      f"{len(requirements)} requirements, {len(messages)} ui messages, "
      f"{len(sp_msgs)} sp msgs, {len(trait_names)} traits, {len(client_names)} clients, "
      f"{len(troop_labels)} troop labels, {len(rank_msgs)} rank msgs")

header = []
for i in range(HEADER_RECORDS):
    header.append(list(struct.unpack_from('<4I', raw, i * 16)))
phdr = [struct.unpack_from('<4I', pristine, i * 16) for i in range(HEADER_RECORDS)]

# ---------------------------------------------------------------------------
# 3. Pre-gates (per-block ENTRY_POLICY).  A failed pre-gate usually means this
#    patcher already ran on the target — rebuild from Step 1 for a clean input.
# ---------------------------------------------------------------------------
blocks = {}
for blk in REBUILD_BLOCKS:
    off, size = header[blk][2], header[blk][1]
    poff, psize = phdr[blk][2], phdr[blk][1]
    cur = bytes(raw[off:off + size])
    pri = pristine[poff:poff + psize]
    recs = split_records(cur)
    precs = split_records(pri)
    nrec, chdr = EXPECTED[blk]
    assert len(recs) == nrec and len(precs) == nrec, \
        f"blk{blk} record count {len(recs)}/{len(precs)} != {nrec} (already patched?)"
    parse_offset_table(recs[0], chdr)
    policy = ENTRY_POLICY[blk]
    if policy == 'pristine':
        assert size == psize, f"blk{blk} size {size} != pristine {psize} — unexpected upstream edit"
        assert cur == pri, f"blk{blk} in build differs from pristine — aborting (already patched?)"
    elif policy == 'shape':
        assert size == psize, f"blk{blk} size {size} != pristine {psize} — unexpected upstream edit"
        # an upstream step may have re-inked records IN PLACE: cell counts equal
        for k in range(nrec):
            assert len(recs[k]) == len(precs[k]), \
                f"blk{blk} g{k+1:02d} cell count changed ({len(precs[k])}->{len(recs[k])}) (already patched?)"
    else:                                   # block 14: g06 rebuilt upstream (G650)
        assert blk == 14
        for k in range(nrec):
            if k == 5:                      # g06 — inject_r39_quest English, any size
                continue
            if k == 0:                      # g01 — table VALUES may be stale (see docstring)
                assert len(recs[k]) == len(precs[k]), \
                    f"blk14 g01 cell count changed ({len(precs[k])}->{len(recs[k])})"
                continue
            assert recs[k] == precs[k], \
                f"blk14 g{k+1:02d} differs from pristine — aborting (already patched?)"
    blocks[blk] = recs

# ---------------------------------------------------------------------------
# 4. Build new records
# ---------------------------------------------------------------------------
def line_record(text):
    """content + FFFE (the pristine single-line record shape)."""
    return encode_line(text) + [0xFFFE]

def label_record(text, blk, g):
    """single-line label with width guard (blocks 11/12/13)."""
    enc = encode_line(text)
    assert len(enc) <= MAX_LABEL_CELLS, \
        f"blk{blk} g{g} label is {len(enc)} cells (max {MAX_LABEL_CELLS}): {text!r}"
    return enc + [0xFFFE]

def req_record(text, g):
    """block-4 AA requirement, single line with the narrow requirement-field guard.
    Separate from line_record() on purpose: line_record also emits block5 messages
    (e.g. g03 'All Allied Actions removed.' = 27 cells) which live in a wider field."""
    enc = encode_line(text)
    assert len(enc) <= MAX_REQ_CELLS, \
        f"blk4 g{g} requirement is {len(enc)} cells (max {MAX_REQ_CELLS}): {text!r}"
    return enc + [0xFFFE]

def lines_record(lines, blk, g):
    """multi-line message record (blocks 10/14): every line -> cells + FFFE,
    exactly the pristine shape.  Lines may carry {HL}/{/HL} tokens."""
    assert isinstance(lines, list) and len(lines) >= 1, f"blk{blk} g{g}: need a list of lines"
    cells = []
    for li, text in enumerate(lines):
        enc, visible = encode_line_tokens(text)
        assert visible <= MAX_LINE_CELLS, \
            f"blk{blk} g{g} line {li+1} is {visible} visible cells (max {MAX_LINE_CELLS}): {text!r}"
        cells += enc + [0xFFFE]
    return cells

new_blocks = {}
patched = {blk: set() for blk in REBUILD_BLOCKS}   # 0-based record indices we replace
counts = {'names': 0, 'descs': 0, 'reqs': 0, 'msgs': 0,
          'sp': 0, 'traits': 0, 'clients': 0, 'troops': 0, 'ranks': 0}

# block 3 — names
recs = [list(r) for r in blocks[3]]
for g, text in sorted(names.items()):
    assert 2 <= g <= 40, f"block3 name key g{g} out of range"
    recs[g - 1] = line_record(text)
    patched[3].add(g - 1)
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
    patched[4].add(g - 1)
    counts['descs'] += 1
for g, text in sorted(requirements.items()):
    assert 40 <= g <= 85 and g != 66, f"block4 requirement key g{g} out of range (g66 is empty)"
    recs[g - 1] = req_record(text, g)
    patched[4].add(g - 1)
    counts['reqs'] += 1
assert recs[65] == list(blocks[4][65]) and len(recs[65]) == 0, "block4 g66 must stay empty"
new_blocks[4] = rebuild_block(blocks[4], recs, 4)

# block 5 — ui messages
recs = [list(r) for r in blocks[5]]
for g, text in sorted(messages.items()):
    assert 2 <= g <= 8, f"block5 message key g{g} out of range"
    recs[g - 1] = line_record(text)
    patched[5].add(g - 1)
    counts['msgs'] += 1
new_blocks[5] = rebuild_block(blocks[5], recs, 5)

# block 10 — item SP-activation messages (multi-line; g02 blank preserved)
recs = [list(r) for r in blocks[10]]
for g, lines in sorted(sp_msgs.items()):
    assert 3 <= g <= 24, f"block10 sp message key g{g} out of range"
    recs[g - 1] = lines_record(lines, 10, g)
    patched[10].add(g - 1)
    counts['sp'] += 1
new_blocks[10] = rebuild_block(blocks[10], recs, 10)

# block 11 — potential-ability / trait names
recs = [list(r) for r in blocks[11]]
for g, text in sorted(trait_names.items()):
    assert 2 <= g <= 22, f"block11 trait key g{g} out of range"
    recs[g - 1] = label_record(text, 11, g)
    patched[11].add(g - 1)
    counts['traits'] += 1
new_blocks[11] = rebuild_block(blocks[11], recs, 11)

# block 12 — quest-client / guild names (g02 blank preserved)
recs = [list(r) for r in blocks[12]]
for g, text in sorted(client_names.items()):
    assert 3 <= g <= 15, f"block12 client key g{g} out of range"
    recs[g - 1] = label_record(text, 12, g)
    patched[12].add(g - 1)
    counts['clients'] += 1
new_blocks[12] = rebuild_block(blocks[12], recs, 12)

# block 13 — spellbook labels ONLY (g03..g86 keep patch_r39_inline's English ink)
recs = [list(r) for r in blocks[13]]
for g, text in sorted(troop_labels.items()):
    assert 87 <= g <= 107, f"block13 troop label key g{g} out of range (only g87..g107)"
    recs[g - 1] = label_record(text, 13, g)
    patched[13].add(g - 1)
    counts['troops'] += 1
new_blocks[13] = rebuild_block(blocks[13], recs, 13)

# block 14 — party-rank messages (g06 = inject_r39_quest G650, preserved verbatim)
recs = [list(r) for r in blocks[14]]
for g, lines in sorted(rank_msgs.items()):
    assert 2 <= g <= 10 and g != 6, f"block14 rank message key g{g} out of range (g06 is upstream's)"
    recs[g - 1] = lines_record(lines, 14, g)
    patched[14].add(g - 1)
    counts['ranks'] += 1
assert recs[5] == list(blocks[14][5]), "block14 g06 must stay verbatim"
new_blocks[14] = rebuild_block(blocks[14], recs, 14)

print(f"re-encoded: {counts['names']} names, {counts['descs']} descriptions, "
      f"{counts['reqs']} requirements, {counts['msgs']} ui messages, "
      f"{counts['sp']} sp msgs, {counts['traits']} traits, {counts['clients']} clients, "
      f"{counts['troops']} troop labels, {counts['ranks']} rank msgs")

# ---------------------------------------------------------------------------
# 5. Reassemble: splice every rebuilt block in file order, preserving the
#    inter-block gap bytes (incl. untouched blocks 6..9) verbatim and shifting
#    everything after each block by its cumulative delta.
# ---------------------------------------------------------------------------
segs = sorted(REBUILD_BLOCKS, key=lambda b: header[b][2])
assert list(segs) == list(REBUILD_BLOCKS), "unexpected block order in file"
for a, b in zip(segs, segs[1:]):
    assert header[a][2] + header[a][1] <= header[b][2], f"blk{a}/blk{b} overlap"

first_off = header[segs[0]][2]
out = bytearray(raw[:first_off])
new_off, gap_checks = {}, []      # gap_checks: (new_pos, old_slice) for the gate
for i, blk in enumerate(segs):
    off, size = header[blk][2], header[blk][1]
    new_off[blk] = len(out)
    out += new_blocks[blk]
    gap_end = header[segs[i + 1]][2] if i + 1 < len(segs) else len(raw)
    gap = raw[off + size:gap_end]  # pad bytes / untouched blocks / file tail
    gap_checks.append((len(out), bytes(gap)))
    out += gap

def shift_for(old_off):
    """cumulative size delta of all rebuilt blocks that lie BEFORE old_off."""
    return sum(len(new_blocks[b]) - header[b][1]
               for b in REBUILD_BLOCKS if header[b][2] < old_off)

total_delta = sum(len(new_blocks[b]) - header[b][1] for b in REBUILD_BLOCKS)

# ---------------------------------------------------------------------------
# 6. Rewrite header: rebuilt recs get new size+offset; every other rec keeps
#    its size and shifts by the delta of the rebuilt blocks before it.
# ---------------------------------------------------------------------------
for i in range(HEADER_RECORDS):
    idx, size, off, z = header[i]
    if i in REBUILD_BLOCKS:
        size, off = len(new_blocks[i]), new_off[i]
    else:
        off += shift_for(off)
    struct.pack_into('<4I', out, i * 16, idx, size, off, z)

# ---------------------------------------------------------------------------
# 7. PRISTINE-DIFF GATE — every byte outside the rebuilt blocks unchanged
#    vs input (modulo shift), untouched header record sizes preserved.
# ---------------------------------------------------------------------------
assert out[HEADER_BYTES:first_off] == raw[HEADER_BYTES:first_off], \
    "PRISTINE-DIFF FAIL: bytes between header and first rebuilt block changed"
for new_pos, old_slice in gap_checks:
    assert out[new_pos:new_pos + len(old_slice)] == old_slice, \
        "PRISTINE-DIFF FAIL: inter-block gap / tail not verbatim after shift"
for i in range(HEADER_RECORDS):
    nidx, nsize, noff, nz = struct.unpack_from('<4I', out, i * 16)
    oidx, osize, ooff, oz = header[i]
    assert nidx == oidx and nz == oz, f"rec[{i}] idx/z changed"
    if i in REBUILD_BLOCKS:
        continue
    assert nsize == osize, f"PRISTINE-DIFF FAIL: rec[{i}] size changed {osize}->{nsize}"
    exp_off = ooff + shift_for(ooff)
    assert noff == exp_off, f"PRISTINE-DIFF FAIL: rec[{i}] off {noff} != {exp_off}"
# re-split the rebuilt blocks: validate offset tables AND that every record we
# did not patch survives byte-for-byte from the input state.
for blk in REBUILD_BLOCKS:
    nrecs = split_records(bytes(new_blocks[blk]))
    nrec, chdr = EXPECTED[blk]
    assert len(nrecs) == nrec
    vals = parse_offset_table(nrecs[0], chdr)
    pos = 0
    for k, rc in enumerate(nrecs):
        if k >= 1:
            assert vals[k] == pos, f"blk{blk} rebuilt table slot {k} ({vals[k]}) != g{k+1} start ({pos})"
        if k >= 1 and k not in patched[blk]:
            assert rc == list(blocks[blk][k]), \
                f"blk{blk} g{k+1:02d} was not a target but its content changed"
        pos += len(rc) * 2 + 2
deltas = ', '.join(f"blk{b} {header[b][1]}->{len(new_blocks[b])}" for b in REBUILD_BLOCKS)
print(f"PRISTINE-DIFF GATE PASSED: {deltas} bytes; total delta {total_delta:+d}; "
      f"all other bytes verbatim, untouched header sizes preserved.")

# ---------------------------------------------------------------------------
# 8. Trim carried-over sector padding, pad to sector boundary; write back.
#    (The splice keeps the input's tail verbatim, which includes the previous
#    step's zero padding — without the trim the file gains a dead sector per
#    step and breaks tests/test_r39_section_table.py's 16-sector cap.)
# ---------------------------------------------------------------------------
content_end = new_off[segs[-1]] + len(new_blocks[segs[-1]])
dropped = bytes(out[content_end:])
assert set(dropped) <= {0}, \
    f"non-zero bytes after the last block (blk{segs[-1]}) — refusing to trim tail padding"
out = out[:content_end]
sectors = math.ceil(len(out) / SECTOR)
assert sectors * SECTOR <= 32768, \
    f"R39 would exceed the 16-sector cap ({sectors} sectors) — shorten translations"
out += b'\x00' * (sectors * SECTOR - len(out))
with open(TARGET, 'wb') as f:
    f.write(out)
print(f"Written {len(out)} bytes ({sectors} sectors, content {content_end}) to {TARGET}")
