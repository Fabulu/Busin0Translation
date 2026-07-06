import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import test_line_width as T
from sec1_disasm import LENB

# Build a synthetic type-02 blob with:
#   group 0: name-island. prefix label "Innkeeper" (9 glyphs, NO 0xFFFE), then
#            correctly-wrapped dialogue: line1=15 glyphs, 0xFFFE, line2=12 glyphs.
#            First on-screen line naive = 9+15 = 24 (>18 -> false positive).
#            After prefix exemption = 15 (<=18 -> OK).
#   group 1: GENUINE offender: a single 30-glyph line, NO name prefix.
#
# Section 1 must contain a walkable 0x14 covering the 9-glyph prefix of group 0,
# so the patcher's bucketing flags it as a name island.

def gly(n, base=1):  # n visible english glyphs (ids 1..94)
    return [base + (i % 90) for i in range(n)]

# --- Section 2 ---
g0 = gly(9) + gly(15) + [0xFFFE] + gly(12)   # name island, wrapped
g1 = gly(30)                                  # genuine offender
words = g0 + [0xFFFF] + g1 + [0xFFFF]
# group 0 starts at word 0, prefix length 9
sec2 = struct.pack('>%dH'%len(words), *words)

# --- Section 1 ---
# 0x14 NAME/LABEL: opcode(2) param(2) s16(2) off(4) cnt(4) = 14 bytes
# off=0 (group0 start), cnt=9 (the prefix). Then a terminating 0x00 NOP-ish?
# We need walk() to succeed from pc=0. opcode 0x14 len from LENB.
import struct as _s
s1 = bytearray()
# 0x14 record
s1 += _s.pack('>H', 0x14)      # opcode
s1 += _s.pack('>H', 0)         # param
s1 += _s.pack('>H', 0xFFFF)    # s16
s1 += _s.pack('>I', 0)         # off = 0 (group0 head)
s1 += _s.pack('>I', 9)         # cnt = 9 (prefix len)
assert len(s1) == LENB[0x14], (len(s1), LENB[0x14])
# pad to even; append zeros (opcode 0x00 must be valid/walkable -> length lookup)
# opcode 0 length:
s1 += _s.pack('>H', 0) * 4   # trailing zero opcodes (valid, walk to end)

# --- assemble type-02 blob: header 0x20 + sec1 + sec2 ---
HEADER = 0x20
sec1_off = HEADER
sec2_off = HEADER + len(s1)
header = bytearray(HEADER)
struct.pack_into('<I', header, 0x14, len(sec2))   # sec2_size
struct.pack_into('<I', header, 0x18, sec2_off)    # sec2_off
blob = bytes(header) + bytes(s1) + sec2

p = T.parse_type02(blob)
prefixes = T._name_island_prefix_lens(p)
print("detected name-island prefixes:", prefixes)
offenders = list(T._line_offenders(p, 9999))
print("offenders:", [(o[1], o[2], o[3][:30]) for o in offenders])

ok = (prefixes.get(0) == 9) and (len(offenders) == 1) and (offenders[0][1] == 1) and (offenders[0][2] == 30)
print("RESULT:", "PASS" if ok else "FAIL")
