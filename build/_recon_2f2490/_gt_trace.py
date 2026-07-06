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

def beu32(b, o): return struct.unpack_from('>I', b, o)[0]
res = 1197
sec1, groups = load(res)
ok, instrs = walk(sec1)
order = sorted(instrs)
# print opcode trace between two pcs covering g3..g13 (pc ~19182..19400) showing 0x0C/0x0D/0x48/0x04
lo, hi = 19150, 19420
for pc in order:
    if lo <= pc <= hi:
        op = instrs[pc]
        extra = ''
        if op == 0x04:
            off = beu32(sec1, pc+2); cnt = beu32(sec1, pc+6)
            g = [gi for gi,(gs,ge) in enumerate(groups) if not (ge<off or gs>=off+cnt)]
            extra = ' DISPLAY off=%d cnt=%d grps=%s' % (off, cnt, g[:4])
        tag = ''
        if op in (0x0C,0x0D,0x48,0x47): tag = ' <<<STATE'
        print('  @%-6d op=0x%02x%s%s' % (pc, op, extra, tag))
