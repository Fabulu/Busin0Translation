#!/usr/bin/env python3
"""
analyze_sec1_refs.py -- Analyze how Section 1 of type-02 resources references Section 2 dialogue.

When Section 2 grows (English text longer than Japanese), event scripts in Section 1
may break if they contain byte-offset pointers into Section 2. This script searches
for all plausible reference mechanisms:
  - Byte offsets (relative to sec2 start) as LE u16 or LE u32
  - Absolute file offsets as LE u32
  - Message indices (0..N) encoded in various ways

Usage:
    cd C:/Programmieren/wizardrytranslation
    python tools/analyze_sec1_refs.py
"""
import struct, os, sys

os.chdir('C:/Programmieren/wizardrytranslation')
sys.stdout.reconfigure(encoding='utf-8')

# --- Load resource ---
data = open('extracted/packdata_raw/1198_type02.raw', 'rb').read()

print("=" * 70)
print("  SECTION 1 -> SECTION 2 REFERENCE ANALYSIS  (R1198)")
print("=" * 70)

# --- Header ---
print("\nHeader (28 bytes, 7 x LE u32):")
for i in range(0, 28, 4):
    val = struct.unpack_from('<I', data, i)[0]
    print(f"  +0x{i:02X} (+{i:2d}): {val:10d}  (0x{val:08X})")

sec2_size   = struct.unpack_from('<I', data, 0x14)[0]
sec2_off    = struct.unpack_from('<I', data, 0x18)[0]

print(f"\n  sec2_size   = {sec2_size} bytes")
print(f"  sec2_offset = {sec2_off} (0x{sec2_off:04X})")

sec2 = data[sec2_off : sec2_off + sec2_size]

# --- Map message start offsets within Section 2 ---
msg_starts = [0]
for i in range(0, len(sec2) - 1, 2):
    if struct.unpack_from('>H', sec2, i)[0] == 0xFFFF:
        next_start = i + 2
        if next_start < len(sec2):
            msg_starts.append(next_start)

print(f"\nSection 2: {len(msg_starts)} messages")
print(f"  Message start offsets (sec2-relative): {msg_starts[:20]}...")
if len(msg_starts) > 20:
    print(f"  ... {msg_starts[-5:]}")

section1 = data[28:sec2_off]
print(f"\nSection 1: {len(section1)} bytes (file offsets 28 .. {sec2_off})")

# =====================================================================
# STRATEGY 1: sec2-relative byte offsets as LE u16
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 1: sec2-relative byte offsets as LE u16")
print("=" * 70)
for mi, moff in enumerate(msg_starts):
    if moff > 0xFFFF:
        continue
    target = struct.pack('<H', moff)
    hits = []
    pos = 0
    while True:
        pos = section1.find(target, pos)
        if pos < 0:
            break
        hits.append(pos + 28)  # convert to file offset
        pos += 1
    # Skip offset 0 (too common) and very noisy results
    if moff == 0:
        print(f"  msg[{mi:3d}] offset {moff:6d}: {len(hits)} hits (skipped, too common)")
    elif hits:
        print(f"  msg[{mi:3d}] offset {moff:6d}: {len(hits)} hits at file offsets {hits[:8]}")

# =====================================================================
# STRATEGY 2: Absolute file offsets as LE u32
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 2: Absolute file offsets (sec2_off + msg_offset) as LE u32")
print("=" * 70)
for mi, moff in enumerate(msg_starts):
    abs_off = sec2_off + moff
    target = struct.pack('<I', abs_off)
    hits = []
    pos = 0
    while True:
        pos = section1.find(target, pos)
        if pos < 0:
            break
        hits.append(pos + 28)
        pos += 1
    if hits:
        print(f"  msg[{mi:3d}] abs_offset {abs_off:6d} (0x{abs_off:04X}): found at {hits[:8]}")

if not any(
    section1.find(struct.pack('<I', sec2_off + mo)) >= 0
    for mo in msg_starts[:20]
):
    print("  (no matches found)")

# =====================================================================
# STRATEGY 3: Message indices in LE u16 context
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 3: Look for opcode+message_index patterns")
print("=" * 70)
# Many game engines use a 'show_message' opcode followed by a message index.
# Search for repeated patterns where a constant byte precedes sequential msg indices.

# First, dump section 1 as LE u16 words
s1_words = []
for i in range(0, len(section1) - 1, 2):
    s1_words.append(struct.unpack_from('<H', section1, i)[0])

# Look for any word W where W appears before several different small values (0..87)
# that correspond to message indices
from collections import Counter
preceding_words = Counter()
for i in range(1, len(s1_words)):
    if 0 <= s1_words[i] <= 87:
        preceding_words[s1_words[i - 1]] += 1

print("  Most common LE u16 words preceding values 0..87:")
for word, count in preceding_words.most_common(15):
    # Show which indices follow this word
    indices_after = [s1_words[i] for i in range(1, len(s1_words))
                     if s1_words[i - 1] == word and 0 <= s1_words[i] <= 87]
    unique = sorted(set(indices_after))
    print(f"    0x{word:04X} ({word:5d}): {count} times, indices: {unique[:20]}")

# =====================================================================
# STRATEGY 4: Dump Section 1 as LE u32 words, look for pointer-like values
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 4: LE u32 words in Section 1 that look like sec2 offsets")
print("=" * 70)
ptr_hits = []
for i in range(0, len(section1) - 3, 4):
    val = struct.unpack_from('<I', section1, i)[0]
    # Check if it's a plausible offset into Section 2
    if sec2_off <= val < sec2_off + sec2_size:
        rel = val - sec2_off
        # Check if it's an even offset (u16 boundary)
        if rel % 2 == 0:
            ptr_hits.append((i + 28, val, rel))
    # Also check relative offset
    if 0 < val < sec2_size and val % 2 == 0:
        ptr_hits.append((i + 28, val, val))

if ptr_hits:
    print(f"  Found {len(ptr_hits)} potential pointers:")
    for foff, val, rel in ptr_hits[:30]:
        is_msg = rel in msg_starts
        tag = " <-- MSG START" if is_msg else ""
        print(f"    file+0x{foff:04X}: value=0x{val:08X} (sec2_rel={rel}){tag}")
else:
    print("  (no pointer-like values found)")

# =====================================================================
# STRATEGY 5: Hex dump first 512 bytes of Section 1
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 5: Hex dump of Section 1 (first 512 bytes)")
print("=" * 70)
for i in range(0, min(512, len(section1)), 16):
    hex_part = ' '.join(f'{section1[i+j]:02X}' for j in range(min(16, len(section1) - i)))
    asc_part = ''.join(
        chr(section1[i+j]) if 32 <= section1[i+j] < 127 else '.'
        for j in range(min(16, len(section1) - i))
    )
    print(f"  {i+28:5d} (0x{i+28:04X}): {hex_part:<48s} {asc_part}")

# =====================================================================
# STRATEGY 6: Look for a message offset table in Section 1
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 6: Scan for embedded offset tables in Section 1")
print("=" * 70)
# Look for runs of monotonically increasing LE u16 or LE u32 values
# that match message start positions

# Check LE u16 table
for start in range(0, len(section1) - 20, 2):
    # Read 10 consecutive LE u16 values
    vals = [struct.unpack_from('<H', section1, start + j * 2)[0] for j in range(10)]
    # Check if monotonically increasing and matching msg_starts
    if all(vals[j] < vals[j + 1] for j in range(9)):
        matches = sum(1 for v in vals if v in msg_starts)
        if matches >= 5:
            print(f"  LE u16 table at section1+{start} (file+{start+28}):")
            print(f"    values: {vals}")
            print(f"    matches: {matches}/10")

# Check LE u32 table
for start in range(0, len(section1) - 40, 4):
    vals = [struct.unpack_from('<I', section1, start + j * 4)[0] for j in range(10)]
    if all(vals[j] < vals[j + 1] for j in range(9)):
        matches = sum(1 for v in vals if v in msg_starts)
        if matches >= 5:
            print(f"  LE u32 table at section1+{start} (file+{start+28}):")
            print(f"    values: {vals}")
            print(f"    matches: {matches}/10")

# =====================================================================
# STRATEGY 7: Check if Section 1 contains u16 word indices (not byte offsets)
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 7: Word-index references (byte_offset / 2)")
print("=" * 70)
msg_word_starts = [m // 2 for m in msg_starts]
for mi, widx in enumerate(msg_word_starts):
    if widx == 0 or widx > 0xFFFF:
        continue
    target = struct.pack('<H', widx)
    hits = []
    pos = 0
    while True:
        pos = section1.find(target, pos)
        if pos < 0:
            break
        hits.append(pos + 28)
        pos += 1
    if hits and len(hits) <= 5:
        print(f"  msg[{mi:3d}] word_index {widx}: {len(hits)} hits at file offsets {hits[:8]}")


# =====================================================================
# STRATEGY 8: Look for FFFF as command delimiters in Section 1
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 8: FFFF command delimiters in Section 1 (BE u16)")
print("=" * 70)

ffff_positions = []
for i in range(0, len(section1) - 1, 2):
    val = struct.unpack_from('>H', section1, i)[0]
    if val == 0xFFFF:
        ffff_positions.append(i)

print(f"  FFFF count in Section 1: {len(ffff_positions)}")
print(f"  Positions (sec1-relative): {ffff_positions[:30]}")

# Show commands between FFFF delimiters
print("\n  Commands between FFFF delimiters (first 25):")
boundaries = [-2] + ffff_positions + [len(section1)]
for ci in range(min(25, len(boundaries) - 1)):
    start = boundaries[ci] + 2
    end = boundaries[ci + 1]
    if end <= start:
        continue
    chunk = section1[start:end]
    words = []
    for j in range(0, len(chunk) - 1, 2):
        words.append(struct.unpack_from('>H', chunk, j)[0])
    if len(words) <= 20:
        hexw = ' '.join(f'{w:04X}' for w in words)
    else:
        hexw = ' '.join(f'{w:04X}' for w in words[:10]) + f' ... ({len(words)} words total)'
    print(f"    cmd[{ci:2d}] file+{start+28:5d}: {hexw}")

# =====================================================================
# STRATEGY 9: Look at Section 1 as BE u16 stream and find small values 0-87
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 9: BE u16 words in Section 1 (look for message indices)")
print("=" * 70)

# Instead of LE, try BE u16 since the hex dump looks big-endian
s1_be_words = []
for i in range(0, len(section1) - 1, 2):
    s1_be_words.append(struct.unpack_from('>H', section1, i)[0])

# Find where small message-index-sized values appear with preceding opcode
from collections import Counter
be_preceding = Counter()
for i in range(1, len(s1_be_words)):
    if 0 <= s1_be_words[i] <= 87:
        be_preceding[s1_be_words[i - 1]] += 1

print("  Most common BE u16 words preceding values 0..87:")
for word, count in be_preceding.most_common(20):
    indices_after = sorted(set(
        s1_be_words[i] for i in range(1, len(s1_be_words))
        if s1_be_words[i - 1] == word and 0 <= s1_be_words[i] <= 87
    ))
    print(f"    0x{word:04X} ({word:5d}): {count} times, unique indices: {indices_after[:25]}")

# =====================================================================
# STRATEGY 10: Look for a specific 'show message' pattern
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 10: Pairs where BE u16 word is followed by sequential indices 0,1,2...")
print("=" * 70)

# For each possible opcode, check if it appears before msg indices 0, 1, 2, etc.
for word, count in be_preceding.most_common(30):
    positions = [i for i in range(1, len(s1_be_words))
                 if s1_be_words[i - 1] == word and 0 <= s1_be_words[i] <= 87]
    indices = [s1_be_words[p] for p in positions]
    unique_indices = sorted(set(indices))

    # Check coverage: how many of 0..87 are referenced?
    coverage = len([x for x in unique_indices if x <= 87])
    max_idx = max(unique_indices) if unique_indices else -1

    if coverage >= 5 and len(unique_indices) >= 3:
        # Show context around each hit
        print(f"\n  Opcode 0x{word:04X}: {coverage} unique indices covered, max={max_idx}")
        for p in positions[:10]:
            # Show 3 words before and 3 words after
            ctx_start = max(0, p - 3)
            ctx_end = min(len(s1_be_words), p + 4)
            ctx = s1_be_words[ctx_start:ctx_end]
            ctx_str = ' '.join(f'{w:04X}' for w in ctx)
            marker_pos = p - ctx_start
            print(f"    pos {p*2+28}: ... {ctx_str}  (index={s1_be_words[p]})")

# =====================================================================
# STRATEGY 11: Cross-reference multiple type-02 resources
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 11: Compare with other type-02 resources")
print("=" * 70)

import glob
type2_files = sorted(glob.glob('extracted/packdata_raw/*_type02.raw'))[:20]
for fpath in type2_files[:10]:
    fname = os.path.basename(fpath)
    d = open(fpath, 'rb').read()
    if len(d) < 28:
        continue
    s2_size = struct.unpack_from('<I', d, 0x14)[0]
    s2_off = struct.unpack_from('<I', d, 0x18)[0]
    if s2_off == 0 or s2_off >= len(d):
        continue
    s2 = d[s2_off:s2_off + s2_size]
    # Count messages
    msg_count = 0
    for i in range(0, len(s2) - 1, 2):
        if struct.unpack_from('>H', s2, i)[0] == 0xFFFF:
            msg_count += 1
    s1 = d[28:s2_off]
    # Count FFFF in section 1
    s1_ffff = 0
    for i in range(0, len(s1) - 1, 2):
        if struct.unpack_from('>H', s1, i)[0] == 0xFFFF:
            s1_ffff += 1
    print(f"  {fname}: total={len(d)}, s1={len(s1)}B, s2={s2_size}B ({msg_count} msgs), s1_FFFF={s1_ffff}")


# =====================================================================
# STRATEGY 12: Deep dive into repeating 310-word command blocks
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 12: Deep dive into the repeating 310-word command blocks")
print("=" * 70)

# The FFFF-delimited blocks after the first one are each 310 BE u16 words
# Starting values: 0x0386, 0x05F6, 0x0866, 0x0AD6, 0x0D46, 0x0FB6, 0x1226, 0x1496, 0x1706, 0x1976, 0x1BE6
# Differences: 0x270 = 624 each

block_starts_raw = []
for ci in range(min(len(boundaries) - 1, 30)):
    start = boundaries[ci] + 2
    end = boundaries[ci + 1]
    if end - start == 620:  # 310 words * 2 bytes
        words_block = []
        for j in range(0, 620, 2):
            words_block.append(struct.unpack_from('>H', section1, start + j)[0])
        block_starts_raw.append((start + 28, words_block))

print(f"  Found {len(block_starts_raw)} blocks of exactly 310 words")

if block_starts_raw:
    # Show first block fully
    foff, words_block = block_starts_raw[0]
    print(f"\n  First 310-word block at file offset {foff}:")
    for i in range(0, len(words_block), 10):
        chunk = words_block[i:i+10]
        line = ' '.join(f'{w:04X}' for w in chunk)
        print(f"    [{i:3d}]: {line}")

    # Compare first few words of each block to find the variable parts
    print(f"\n  Comparing first 20 words of each block:")
    for bi, (foff, wb) in enumerate(block_starts_raw[:5]):
        first20 = ' '.join(f'{w:04X}' for w in wb[:20])
        print(f"    block[{bi}] @ {foff}: {first20}")

    # Check which positions differ between blocks
    if len(block_starts_raw) >= 2:
        print(f"\n  Positions that differ between blocks (first 2):")
        _, b0 = block_starts_raw[0]
        _, b1 = block_starts_raw[1]
        for i in range(min(len(b0), len(b1))):
            if b0[i] != b1[i]:
                # Show value across all blocks at this position
                vals = [wb[i] for _, wb in block_starts_raw[:6]]
                diffs = [vals[j+1] - vals[j] for j in range(len(vals)-1)]
                print(f"      word[{i:3d}]: values={[f'0x{v:04X}' for v in vals]}, diffs={diffs}")

# =====================================================================
# STRATEGY 13: Look for message index values in the variable parts
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 13: Map variable values to potential message indices")
print("=" * 70)

if len(block_starts_raw) >= 2:
    _, b0 = block_starts_raw[0]
    _, b1 = block_starts_raw[1]
    diff_positions = [i for i in range(min(len(b0), len(b1))) if b0[i] != b1[i]]

    print(f"  {len(diff_positions)} positions differ between blocks")

    # For each differing position, show all values across blocks
    for pos in diff_positions[:20]:
        vals = [wb[pos] for _, wb in block_starts_raw]
        # Check if these look like message indices (sequential small values)
        if all(0 <= v <= 200 for v in vals):
            is_sequential = all(vals[j] < vals[j+1] for j in range(len(vals)-1))
            print(f"  word[{pos:3d}]: {vals}  {'SEQUENTIAL!' if is_sequential else ''}")
        else:
            print(f"  word[{pos:3d}]: {[f'0x{v:04X}' for v in vals]}")

# =====================================================================
# STRATEGY 14: Focus on the 0x0016 opcode pattern
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 14: The 0016 opcode and its arguments")
print("=" * 70)

# Pattern observed: ... 0006 0016 0001 0000 XXXX ...
# where XXXX could be a message index
# Also: ... 0006 0016 0002 ...
for i in range(len(s1_be_words) - 5):
    if s1_be_words[i] == 0x0016:
        ctx = s1_be_words[max(0, i-3):min(len(s1_be_words), i+8)]
        ctx_str = ' '.join(f'{w:04X}' for w in ctx)
        print(f"  pos {i*2+28:5d}: ... {ctx_str}")

# =====================================================================
# STRATEGY 15: Focus on the area right after block 0 header
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 15: Scan for opcode 0x0012 (potential 'show message'?)")
print("=" * 70)

for i in range(len(s1_be_words) - 5):
    if s1_be_words[i] == 0x0012:
        ctx = s1_be_words[max(0, i-2):min(len(s1_be_words), i+8)]
        ctx_str = ' '.join(f'{w:04X}' for w in ctx)
        print(f"  pos {i*2+28:5d}: ... {ctx_str}")
        if i*2+28 > 2000:
            break  # enough


# =====================================================================
# STRATEGY 16: Verify the +624 values are section-1 jump targets, not sec2 refs
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 16: Are the +624 increment values SECTION 1 byte offsets?")
print("=" * 70)

# Block 0 starts at section1 offset 298 (=326-28), block 1 at 922, etc.
# Each block is 620 bytes = 310 words.
# 922 - 298 = 624 bytes = the increment!
# So these values are ABSOLUTE byte offsets within Section 1 (from byte 28).

# Let's verify: word[1] of each block contains a value.
# Block 0: word[1] = 0x0386 = 902.  Block 0 starts at sec1_offset 298.
# Block 1: word[1] = 0x05F6 = 1526. Block 1 starts at sec1_offset 922.
# The end of block 0 = 298 + 620 = 918, then 2 bytes of FFFF, then 2 bytes FFFF = 922
# So 0x0386 = 902 is WITHIN block 0 (298..918). offset 902-298 = 604 words into block

# These look like SELF-REFERENCES (jump targets within Section 1 itself)
# They are NOT Section 2 references at all!

# Verify by checking if the block start values match section1 byte offsets
for bi, (foff, wb) in enumerate(block_starts_raw[:5]):
    sec1_start = foff - 28  # section1-relative start
    val_at_1 = wb[1]
    sec1_end = sec1_start + 620
    print(f"  Block {bi}: sec1 range [{sec1_start}..{sec1_end}], word[1]=0x{val_at_1:04X}={val_at_1}")
    print(f"    word[1] is {'WITHIN' if sec1_start <= val_at_1 <= sec1_end else 'OUTSIDE'} this block")

# Now check word[306] which had values [4, 5, 6, 7, 8, 9] -- sequential!
# These look like simple loop counters or indices, NOT message indices
print()
print("  word[306] values across blocks (increments by 1, look like loop counters):")
for bi, (foff, wb) in enumerate(block_starts_raw):
    print(f"    block[{bi:2d}]: word[306] = {wb[306]}")

# =====================================================================
# STRATEGY 17: Find the ACTUAL message references
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 17: Search for the 'tail' section (after repeating blocks)")
print("=" * 70)

# The repeating blocks end. What comes after?
last_ffff_idx = ffff_positions[-1] if ffff_positions else 0
tail_start = last_ffff_idx + 2
tail = section1[tail_start:]
print(f"  Tail starts at section1 offset {tail_start} (file offset {tail_start+28})")
print(f"  Tail size: {len(tail)} bytes")

# Dump tail as BE u16
print(f"\n  Tail hex dump (BE u16 words):")
tail_words = []
for i in range(0, len(tail) - 1, 2):
    tail_words.append(struct.unpack_from('>H', tail, i)[0])

for i in range(0, min(len(tail_words), 200), 10):
    chunk = tail_words[i:i+10]
    line = ' '.join(f'{w:04X}' for w in chunk)
    print(f"    [{i:3d}] +{tail_start+i*2+28}: {line}")

# =====================================================================
# STRATEGY 18: Search the tail for message index values
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 18: Search tail section for message-index-like patterns")
print("=" * 70)

# Look for values 0..87 in the tail, with context
print("  Values 0-87 in tail (with 2 words context):")
for i in range(len(tail_words)):
    if 0 < tail_words[i] <= 87:  # skip 0 as too common
        ctx_start = max(0, i - 2)
        ctx_end = min(len(tail_words), i + 3)
        ctx = tail_words[ctx_start:ctx_end]
        ctx_str = ' '.join(f'{w:04X}' for w in ctx)
        marker = i - ctx_start
        print(f"    tail[{i:3d}] val={tail_words[i]:3d} (0x{tail_words[i]:04X}): {ctx_str}")

# =====================================================================
# STRATEGY 19: Check the non-repeating initial section for msg refs
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 19: Initial header/preamble area (before first FFFF)")
print("=" * 70)

preamble = section1[:ffff_positions[0]] if ffff_positions else section1[:200]
pre_words = []
for i in range(0, len(preamble) - 1, 2):
    pre_words.append(struct.unpack_from('>H', preamble, i)[0])

print(f"  Preamble: {len(preamble)} bytes ({len(pre_words)} BE u16 words)")
for i in range(0, len(pre_words), 10):
    chunk = pre_words[i:i+10]
    line = ' '.join(f'{w:04X}' for w in chunk)
    print(f"    [{i:3d}] +{i*2+28}: {line}")


# =====================================================================
# STRATEGY 20: Check word[53], word[103], word[153], word[203], word[253], word[303]
# These had values like [0x012D, 0x0130, 0x0131...] - NOT +624 pattern
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 20: Non-624 variable words in blocks (potential msg refs)")
print("=" * 70)

# word[53] pattern: 0x012D=301, 0x0130=304, 0x0131=305, 0x0132=306...
# These are NOT message indices (too large). But 0x012D = 301 decimal.
# Could be resource IDs? Character IDs?
non_624_positions = []
if len(block_starts_raw) >= 2:
    _, b0 = block_starts_raw[0]
    _, b1 = block_starts_raw[1]
    for i in range(min(len(b0), len(b1))):
        if b0[i] != b1[i]:
            diff = b1[i] - b0[i]
            if diff != 624 and diff != 0:
                vals = [wb[i] for _, wb in block_starts_raw]
                non_624_positions.append((i, vals))

    print(f"  Non-624 variable positions: {len(non_624_positions)}")
    for pos, vals in non_624_positions:
        diffs = [vals[j+1] - vals[j] for j in range(len(vals)-1)]
        print(f"    word[{pos:3d}]: {vals}  diffs={diffs}")

# =====================================================================
# STRATEGY 21: What does each 310-word block reference in terms of messages?
# Look at the CONTEXT around opcode 0x0016 within each block
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 21: Detailed opcode analysis within one block")
print("=" * 70)

if block_starts_raw:
    foff, wb = block_starts_raw[0]
    # The pattern we see is:
    # ... 0006 0016 0001 0000 XXXX 0000 YYYY 0006 ZZZZ ...
    # where XXXX = 0,1,2,3,4,5 (loop counter)
    # YYYY = sec1 offset
    # ZZZZ = some other value
    #
    # Let's extract these structured sub-commands
    print(f"  Block 0 (file offset {foff}), searching for pattern 0006 0016:")
    for i in range(len(wb) - 8):
        if wb[i] == 0x0006 and wb[i+1] == 0x0016:
            ctx = wb[i:min(len(wb), i+12)]
            ctx_str = ' '.join(f'{w:04X}' for w in ctx)
            print(f"    wb[{i:3d}]: {ctx_str}")
            # The value after 0016 0001 0000 is a counter
            # The value after that (0000 XXXX) could be an important ref
            if i + 6 < len(wb):
                counter = wb[i+4]
                ref_val = wb[i+6]
                print(f"           counter={counter}, next_ref=0x{ref_val:04X}={ref_val}")

# =====================================================================
# STRATEGY 22: Check if the block contains explicit msg index references
# by looking at the area around known message-displaying commands
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 22: Full dump of block[0] with annotations")
print("=" * 70)

if block_starts_raw:
    foff, wb = block_starts_raw[0]
    for i in range(0, len(wb), 10):
        chunk = wb[i:i+10]
        line = ' '.join(f'{w:04X}' for w in chunk)
        # Annotate known patterns
        annotations = []
        for j, w in enumerate(chunk):
            if w == 0x0016:
                annotations.append(f"w[{i+j}]=OPCODE_16")
            elif w == 0x0006:
                annotations.append(f"w[{i+j}]=OPCODE_06")
            elif w == 0x000B:
                annotations.append(f"w[{i+j}]=OPCODE_0B")
            elif w == 0x0007:
                annotations.append(f"w[{i+j}]=OPCODE_07")
            elif w == 0x000C:
                annotations.append(f"w[{i+j}]=OPCODE_0C")
            elif w == 0x0008:
                annotations.append(f"w[{i+j}]=OPCODE_08")
        ann = ' | ' + ', '.join(annotations) if annotations else ''
        print(f"    [{i:3d}]: {line}{ann}")


# =====================================================================
# STRATEGY 23: CRITICAL TEST -- verify the self-referencing hypothesis
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 23: Verify that ALL large values in blocks are section1 offsets")
print("=" * 70)

if block_starts_raw:
    foff, wb = block_starts_raw[0]
    sec1_total = len(section1)

    # Extract all values > 100 that could be offsets
    large_vals = [(i, wb[i]) for i in range(len(wb)) if wb[i] > 100]
    in_sec1 = [(i, v) for i, v in large_vals if v < sec1_total]
    in_sec2_range = [(i, v) for i, v in large_vals if sec2_off <= v < sec2_off + sec2_size]

    print(f"  Values > 100 in block[0]: {len(large_vals)}")
    print(f"  Values that fall within sec1 range (0..{sec1_total}): {len(in_sec1)}")
    print(f"  Values that fall within sec2 file offset range ({sec2_off}..{sec2_off+sec2_size}): {len(in_sec2_range)}")

    # Show the ones NOT in sec1 range
    outside = [(i, v) for i, v in large_vals if v >= sec1_total]
    if outside:
        print(f"\n  Values OUTSIDE sec1 range:")
        for i, v in outside[:20]:
            print(f"    wb[{i:3d}]: 0x{v:04X} = {v}")

# =====================================================================
# STRATEGY 24: Verify word[306] = message index hypothesis
# Show what Section 2 message 4, 5, 6 etc. contain
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 24: What are Section 2 messages 4-14? (word[306] values)")
print("=" * 70)

import json
gmap_path = 'data/msg_glyph_map.json'
if os.path.exists(gmap_path):
    gmap = json.load(open(gmap_path, encoding='utf-8'))
else:
    gmap = {}

# Parse all messages
all_msgs = []
msg_glyphs = []
for i in range(0, len(sec2) - 1, 2):
    val = struct.unpack_from('>H', sec2, i)[0]
    if val == 0xFFFF:
        all_msgs.append(msg_glyphs)
        msg_glyphs = []
    else:
        msg_glyphs.append(val)

print(f"  Total messages in Section 2: {len(all_msgs)}")
for mi in range(min(len(all_msgs), 88)):
    glyphs = all_msgs[mi]
    text = ''
    for g in glyphs:
        if g == 0xFFFE:
            text += ' / '
        elif g >= 0xFB00:
            text += f'<{g:04X}>'
        elif str(g) in gmap:
            text += gmap[str(g)]
        else:
            text += f'[{g}]'
    if mi <= 20 or (4 <= mi <= 14):
        print(f"  msg[{mi:2d}]: {text[:80]}")

# =====================================================================
# STRATEGY 25: Check the 0x0012 opcode - is it "show message by index"?
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 25: Opcode 0x0012 pattern analysis")
print("=" * 70)

# From the hex dump we see patterns like:
# 0012 0000 00DA  (0x12, 0x0000, 0x00DA)
# 0012 0000 00B2
# 0012 0000 00E4
# 0012 0000 0098
# 0012 0000 0086
# These values (0xDA=218, 0xB2=178, 0xE4=228, 0x98=152, 0x86=134)
# don't look like message indices. They might be coordinates or sprite IDs.

# Let's look at ALL 0x0012 occurrences systematically
for i in range(len(s1_be_words) - 3):
    if s1_be_words[i] == 0x0012:
        ctx = s1_be_words[max(0, i-2):min(len(s1_be_words), i+6)]
        ctx_str = ' '.join(f'{w:04X}' for w in ctx)
        print(f"  sec1 word {i} (file+{i*2+28}): {ctx_str}")

# =====================================================================
# STRATEGY 26: The DEFINITIVE test - search for explicit message indices
# by opcode 0x0047 which appears in the tail with msg-like values
# =====================================================================
print("\n" + "=" * 70)
print("STRATEGY 26: Opcode 0x0047 analysis (appears with msg-like values)")
print("=" * 70)

for i in range(len(s1_be_words) - 3):
    if s1_be_words[i] == 0x0047:
        ctx = s1_be_words[max(0, i-4):min(len(s1_be_words), i+6)]
        ctx_str = ' '.join(f'{w:04X}' for w in ctx)
        print(f"  sec1 word {i} (file+{i*2+28}): {ctx_str}")

print("\n" + "=" * 70)
print("  ANALYSIS COMPLETE")
print("=" * 70)
