import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import walk, extract_records, LENB
from patch_section1_offsets import parse_sec2_group_offsets
RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'

def load(res):
    raw = open(os.path.join(RAW, '%04d_type02.raw' % res), 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec1 = raw[0x20:sec2_off]
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    groups, _ = parse_sec2_group_offsets(sec2)
    return sec1, sec2, groups

res = 1197
sec1, sec2, groups = load(res)
ok, instrs = walk(sec1)
order = sorted(instrs)

# block pc for each GT group of interest
gt = {3:'NARR',4:'DIAL',7:'NARR',13:'NARR',904:'DIAL',926:'NARR',927:'DIAL'}
# block pcs from prior run
blockpc = {3:19246,4:19282,7:19324,13:19384,904:37325,926:37561,927:37591}

def opname(op):
    return '0x%02x' % op

for g, pc in blockpc.items():
    idx = order.index(pc)
    pre = order[max(0,idx-8):idx]
    seq = ['%s@%d'%(opname(instrs[p]),p) for p in pre]
    print('g%-4d %s display@%d  PRECEDING: %s' % (g, gt[g], pc, ' '.join(seq)))
