import struct, os

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
for f in os.listdir(RESDIR):
    if f.startswith("0046_"):
        with open(os.path.join(RESDIR, f), "rb") as fh:
            data = fh.read()
        break

# Find the FFFF block containing offset 0x4462
target_off = 0x4462
# Search backwards for FFFF
start = target_off
while start > 0:
    v = struct.unpack(">H", data[start:start+2])[0]
    if v == 0xFFFF:
        break
    start -= 2

# Search forward for next FFFF
end = target_off + 4
while end < len(data) - 1:
    v = struct.unpack(">H", data[end:end+2])[0]
    if v == 0xFFFF:
        break
    end += 2

print("Block start=0x%X end=0x%X" % (start, end))

# Parse the block
msg = []
for p in range(start + 2, end, 2):
    v = struct.unpack(">H", data[p:p+2])[0]
    msg.append(v)

# Split by FFFE
parts = []
cur = []
for g in msg:
    if g == 0xFFFE:
        parts.append(cur)
        cur = []
    else:
        cur.append(g)
if cur:
    parts.append(cur)

print("Total parts: %d" % len(parts))
for pi, p in enumerate(parts):
    tg = [g for g in p if g < 0xFFC0]
    marked = []
    for g in tg:
        if g == 132:
            marked.append("*na*")
        elif g == 112:
            marked.append("*a*")
        elif g == 113:
            marked.append("*i*")
        elif g == 130:
            marked.append("*te*")
        elif g == 136:
            marked.append("*no*")
        elif g == 127:
            marked.append("*ta*")
        elif g == 123:
            marked.append("*shi*")
        elif g == 117:
            marked.append("*ka*")
        elif g == 124:
            marked.append("*su*")
        elif g == 142:
            marked.append("*ma*")
        elif g == 191:
            marked.append("*tsu*")
        elif g == 93:
            marked.append("*ra*")
        elif g == 149:
            marked.append("*yo*")
        else:
            marked.append(str(g))
    print("  p[%d] (%d text): %s" % (pi, len(tg), " ".join(marked)))

# Now also show the PREVIOUS FFFF block (which might be the speaker name)
prev_start = start - 2
while prev_start > 0:
    v = struct.unpack(">H", data[prev_start:prev_start+2])[0]
    if v == 0xFFFF:
        break
    prev_start -= 2

prev_msg = []
for p in range(prev_start + 2, start, 2):
    v = struct.unpack(">H", data[p:p+2])[0]
    prev_msg.append(v)
print()
print("Previous block (potential speaker name?):")
tg = [g for g in prev_msg if g < 0xFFC0]
print("  tg=%s" % tg)
print("DONE")
