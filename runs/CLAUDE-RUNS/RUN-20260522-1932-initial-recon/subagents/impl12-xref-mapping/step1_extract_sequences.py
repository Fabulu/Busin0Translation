import struct, os, json
from collections import Counter, defaultdict

RES_DIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
GLYPH_MAX = 0x035A

def find_resource_file(idx):
    prefix = f"{idx:04d}_"
    for fn in os.listdir(RES_DIR):
        if fn.startswith(prefix) and fn.endswith(".bin"):
            return os.path.join(RES_DIR, fn)
    return None

def extract_glyph_stream(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    if len(data) < 4:
        return []
    first_ffff = None
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            first_ffff = off
            break
    if first_ffff is None:
        return []
    stream_data = data[first_ffff:]
    n = len(stream_data) // 2
    vals = struct.unpack(f">{n}H", stream_data[:n*2])
    messages = []
    cur = []
    for v in vals:
        if v == 0xFFFF:
            if cur:
                messages.append(cur)
            cur = []
        elif v == 0xFFFE:
            if cur:
                messages.append(cur)
            cur = []
        elif v >= 0xFFC0:
            pass
        else:
            cur.append(v)
    if cur:
        messages.append(cur)
    return messages

print("=== Extracting glyph sequences from resources 34-49 ===")
all_sequences = {}
all_glyphs_seen = Counter()

for idx in range(34, 50):
    fp = find_resource_file(idx)
    if fp is None:
        print(f"Resource {idx}: NOT FOUND")
        continue
    messages = extract_glyph_stream(fp)
    all_sequences[idx] = messages
    for msg in messages:
        for g in msg:
            if g <= GLYPH_MAX:
                all_glyphs_seen[g] += 1
    lengths = [len(m) for m in messages]
    short_msgs = [m for m in messages if 3 <= len(m) <= 7]
    print(f"Resource {idx}: {len(messages)} msgs, lengths: min={min(lengths) if lengths else 0}, max={max(lengths) if lengths else 0}")
    if short_msgs:
        print(f"  Short msgs (3-7 glyphs): {len(short_msgs)}")
        for i, m in enumerate(short_msgs[:5]):
            hex_str = " ".join(f"{g:04X}" for g in m)
            print(f"    [{i}] len={len(m)}: {hex_str}")
        if len(short_msgs) > 5:
            print(f"    ... and {len(short_msgs)-5} more")

print("\n=== Looking for consecutive short-message blocks ===")
for idx, messages in all_sequences.items():
    runs = []
    cur_run = []
    cur_start = 0
    for i, msg in enumerate(messages):
        if 3 <= len(msg) <= 8:
            if not cur_run:
                cur_start = i
            cur_run.append((i, msg))
        else:
            if len(cur_run) >= 5:
                runs.append((cur_start, cur_run[:]))
            cur_run = []
    if len(cur_run) >= 5:
        runs.append((cur_start, cur_run[:]))
    for start, run in runs:
        print(f"Resource {idx}: Run of {len(run)} short msgs starting at msg #{start}")
        for msg_i, msg in run:
            hex_str = " ".join(f"{g:04X}" for g in msg)
            print(f"  msg #{msg_i} len={len(msg)}: {hex_str}")
        all_g = [g for _, m in run for g in m]
        if all_g:
            print(f"  Glyph range: {min(all_g):04X}-{max(all_g):04X}, unique: {len(set(all_g))}")
        print()

print("\n=== Glyph clustering ===")
print(f"Total unique glyphs: {len(all_glyphs_seen)}")
sorted_glyphs = sorted(all_glyphs_seen.keys())
if sorted_glyphs:
    print(f"Range: {sorted_glyphs[0]:04X} - {sorted_glyphs[-1]:04X}")
    ranges = []
    cur_s = sorted_glyphs[0]
    cur_e = cur_s
    for g in sorted_glyphs[1:]:
        if g <= cur_e + 2:
            cur_e = g
        else:
            ranges.append((cur_s, cur_e, cur_e - cur_s + 1))
            cur_s = g
            cur_e = g
    ranges.append((cur_s, cur_e, cur_e - cur_s + 1))
    print(f"\nContiguous ranges (allowing gaps of 1):")
    for s, e, cnt in sorted(ranges, key=lambda x: -x[2])[:20]:
        total_freq = sum(all_glyphs_seen.get(g, 0) for g in range(s, e+1))
        print(f"  {s:04X}-{e:04X}: {cnt} glyphs, total freq={total_freq}")
