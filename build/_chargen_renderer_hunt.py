import struct

PATCHED = r"C:\programmieren\wizardrytranslation\build\SLPM_653.78_patched"
PRISTINE = r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"

def load(p):
    with open(p, "rb") as f:
        return f.read()

pat = load(PATCHED)
pri = load(PRISTINE)

def va2off(va):
    return va - 0x100000 + 0x80

def off2va(off):
    return off - 0x80 + 0x100000

# loadable text span
TEXT_VA_LO = 0x100000
TEXT_VA_HI = 0x4FDC80
OFF_LO = va2off(TEXT_VA_LO)
OFF_HI = va2off(TEXT_VA_HI)

data = pri  # scan pristine for structure (patched only differs at known cave)

def w(buf, off):
    return struct.unpack_from("<I", buf, off)[0]

# ---- 1. find all jal to 3060B0 and 305E30 (sprite-emit primitives) ----
def jal_word(target):
    return 0x0C000000 | ((target >> 2) & 0x03FFFFFF)

targets = {0x3060B0: jal_word(0x3060B0), 0x305E30: jal_word(0x305E30)}
print("JAL targets:", {hex(k): hex(v) for k,v in targets.items()})

jal_hits = {0x3060B0: [], 0x305E30: []}
off = OFF_LO
while off + 4 <= OFF_HI:
    word = w(data, off)
    for t, jw in targets.items():
        if word == jw:
            jal_hits[t].append(off2va(off))
    off += 4

for t in jal_hits:
    print(f"\njal 0x{t:06X} callers ({len(jal_hits[t])}):")
    for va in jal_hits[t]:
        inside = (0x307DA0 <= va < 0x309864)
        print(f"  VA 0x{va:06X} {'[inside 0x307DA0]' if inside else ''}")

# ---- 2. find all 'ori at,zero,0x8000' = 0x34018000 ----
print("\n=== ori at,zero,0x8000 (0x34018000) hits ===")
ori_hits = []
off = OFF_LO
while off + 4 <= OFF_HI:
    if w(data, off) == 0x34018000:
        ori_hits.append(off2va(off))
    off += 4
for va in ori_hits:
    inside = (0x307DA0 <= va < 0x309864)
    print(f"  VA 0x{va:06X} {'[inside 0x307DA0]' if inside else ''}")

# ---- 3. find addiu with immediate 0x18 (low half 0x0018, opcode 9) ----
# addiu rt,rs,0x0018 -> 0x24..0018 ; opcode 001001 -> top 6 bits = 0x09
# word = 0x24RSRT00.. actually big picture: bits31-26=001001
# we'll filter words where (word>>26)==9 and (word & 0xFFFF)==0x0018
print("\n=== addiu *,*,0x18 (imm 0x0018, opcode 9) hits ===")
adv24 = []
off = OFF_LO
while off + 4 <= OFF_HI:
    word = w(data, off)
    if (word >> 26) == 9 and (word & 0xFFFF) == 0x0018:
        adv24.append((off2va(off), word))
    off += 4
for va, word in adv24:
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    inside = (0x307DA0 <= va < 0x309864)
    print(f"  VA 0x{va:06X} addiu r{rt},r{rs},0x18  word=0x{word:08X} {'[inside 0x307DA0]' if inside else ''}")
