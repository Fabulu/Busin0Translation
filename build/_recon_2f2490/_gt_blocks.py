import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import walk, extract_records
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
recs = extract_records(sec1, instrs)
# Map each display block to covered groups
def covered(off, cnt):
    end = off + cnt
    return [gi for gi, (gs, ge) in enumerate(groups) if not (ge < off or gs >= end)]

# For GT groups, find any display block covering them
gt = [3,4,7,9,10,13,904,922,925,926,927,929]
blockcov = {}  # gi -> list of (block_pc, covered_groups, n_label_in_block)
label_off = {L['pc']: L['off'] for L in recs['label']}
label_groups = set()
for L in recs['label']:
    for gi,(gs,ge) in enumerate(groups):
        if gs<=L['off']<=ge:
            label_groups.add(gi); break
for D in recs['display']:
    if D['cnt']==0: continue
    cov = covered(D['off'], D['cnt'])
    for gi in cov:
        blockcov.setdefault(gi, []).append((D['pc'], D['off'], D['cnt'], len(cov)))

for g in gt:
    gs,ge = groups[g] if g < len(groups) else (None,None)
    print('g%-4d span=[%s,%s] islabel=%s blocks=%s' % (g, gs, ge, g in label_groups, blockcov.get(g)))
