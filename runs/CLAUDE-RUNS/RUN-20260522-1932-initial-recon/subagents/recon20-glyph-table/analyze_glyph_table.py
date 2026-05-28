import struct
EXE = r"C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
d = open(EXE, "rb").read()
print("EXE size: %d bytes" % len(d))
print()
print("=" * 72)
print("FONT DESCRIPTOR STRUCTS (28 bytes each)")
print("=" * 72)
pat = bytes([0x80,0x80,0x80,0x80,0x00,0x01,0x00,0x01])
for off in range(0x3C0600, 0x3C0900):
    if d[off:off+8] == pat:
        s = off - 12
        r = d[s:s+28]
        f0,f1,f2,f3 = struct.unpack_from("<HHHH", r, 0)
        tag = "TERM" if f0 == 0xFFFF else ""
        print("  0x%06X: type=%04X nGlyphs=%3d texA=0x%04X texB=0x%04X %s" % (s,f0,f1,f2,f3,tag))

print()
print("=" * 72)
print("ASCII GLYPH INDEX TABLE at 0x3C0870")
print("=" * 72)
T = 0x3C0870
ents = []
for j in range(200):
    o = T + j * 2
    v = struct.unpack_from("<H", d, o)[0]
    if v == 0 and j > 0:
        nx = [struct.unpack_from("<H", d, o+k*2)[0] for k in range(1,4)]
        if all(x==0 for x in nx): break
    ents.append(v)
print("Entries: %d, range %d-%d" % (len(ents), min(ents), max(ents)))
for j,v in enumerate(ents):
    ac = 0x20 + j
    c = chr(ac) if 32 <= ac < 127 else "?"
    print("  [%3d] 0x%02X(%s) -> glyph %3d" % (j, ac, c, v))
miss = sorted(set(range(min(ents),max(ents)+1)) - set(ents))
print("Missing: %s" % miss)

print()
print("=" * 72)
print("PER-GLYPH STRUCTS at 0x3C0E78 (28 bytes each)")
print("=" * 72)
BASE = 0x3C0E78
f240 = struct.pack("<ff", 240.0, 240.0)
n = 0
while d[BASE+n*28:BASE+n*28+8] == f240 and n < 2000: n += 1
print("%d entries with float 240.0" % n)
print("Glyph  Metric  Row  Col")
for i in range(n):
    o = BASE + i * 28
    print("  %3d    %3d    %d    %d" % (i, d[o+9], d[o+17], d[o+18]))

f480 = struct.pack("<ff", 480.0, 480.0)
o480 = BASE + n * 28
m = 0
while d[o480+m*28:o480+m*28+8] == f480 and m < 2000: m += 1
print("%d entries with float 480.0" % m)
print("Total: %d" % (n+m))
