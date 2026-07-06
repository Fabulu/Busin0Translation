import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import walk, LENB
from patch_section1_offsets import parse_sec2_group_offsets
RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'
def load(res):
    raw = open(os.path.join(RAW, '%04d_type02.raw' % res), 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec1 = raw[0x20:sec2_off]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    groups, _ = parse_sec2_group_offsets(sec2)
    return sec1, groups
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
res=1197
sec1,groups=load(res)
ok,instrs=walk(sec1)
# dump operands of every 0x47 / 0x48 / 0x0C / 0x0D in pc range
for pc in sorted(instrs):
    op=instrs[pc]
    if op==0x47:
        print('@%-6d 0x47 a=%d b=%d (window-pos, NO chan write)'%(pc, beu16(sec1,pc+2), beu16(sec1,pc+4)))
    elif op==0x48:
        print('@%-6d 0x48 a=%d b=%d c=%d (WINDOW+chan write)'%(pc, beu16(sec1,pc+2), beu16(sec1,pc+4), beu16(sec1,pc+6)))
    elif op==0x0C:
        print('@%-6d 0x0C a=%d b=%d (SET name chan)'%(pc, beu16(sec1,pc+2), beu16(sec1,pc+4)))
    elif op==0x0D:
        print('@%-6d 0x0D a=%d b=%d (CLEAR name chan)'%(pc, beu16(sec1,pc+2), beu16(sec1,pc+4)))
    if pc>19420: break
