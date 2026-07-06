import sys, os, struct, glob, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records

HEADER_SIZE = 0x20
RAW_DIR = 'build/packdata_resources'

def res_id(path):
    b = os.path.basename(path)
    return int(b.split('_')[0])

def load_sec(data):
    sec2_size = struct.unpack_from('<I', data, 0x14)[0]
    sec2_off  = struct.unpack_from('<I', data, 0x18)[0]
    sec1 = bytes(data[HEADER_SIZE:sec2_off])
    sec2 = bytes(data[sec2_off:sec2_off+sec2_size])
    return sec1, sec2

def parse_groups(sec2):
    n = len(sec2)//2
    groups=[]; start=0
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    for i,w in enumerate(words):
        if w==0xFFFF:
            groups.append((start,i)); start=i+1
    return groups, words, start

def find_group(groups, woff):
    for gi,(gs,ge) in enumerate(groups):
        if gs <= woff <= ge:
            return gi
    return None

# stats
total_groups=0
groups_with_ffd2=0
groups_with_fffe=0
# Per 0x04 DISPLAY_TEXT block analysis
blocks=[]   # each: dict(res, pc, off, cnt, groups=[gi...], has_ffd2_any, has_name_island_any)
res_summaries={}

files = sorted(glob.glob(os.path.join(RAW_DIR,'*_type02.raw')))
for f in files:
    rid = res_id(f)
    data = open(f,'rb').read()
    try:
        sec1, sec2 = load_sec(data)
    except Exception as e:
        continue
    groups, words, trailing = parse_groups(sec2)
    if not groups:
        continue
    ok, instrs = walk(sec1)
    recs = extract_records(sec1, instrs)
    # per-group flags
    g_ffd2=[False]*len(groups)
    g_fffe=[False]*len(groups)
    g_nameisland=[False]*len(groups)
    for gi,(gs,ge) in enumerate(groups):
        seg = words[gs:ge]
        if 0xFFD2 in seg: g_ffd2[gi]=True
        if 0xFFFE in seg: g_fffe[gi]=True
    # name-island: a 0x14 label whose off falls into a group with a clean prefix at 0
    label_groups=set()
    for r in recs['label']:
        gi = find_group(groups, r['off'])
        if gi is not None:
            label_groups.add(gi)
            g_nameisland[gi]=True
    total_groups += len(groups)
    groups_with_ffd2 += sum(g_ffd2)
    groups_with_fffe += sum(g_fffe)
    # Build DISPLAY_TEXT blocks: each 0x04 (off,cnt) -> covered groups
    rblocks=[]
    for r in recs['display']:
        off=r['off']; cnt=r['cnt']
        if cnt==0: continue
        endw = off+cnt
        gset=set()
        gi0=find_group(groups, off)
        gi1=find_group(groups, min(endw-1, (groups[-1][1] if groups else 0)))
        if gi0 is None:
            continue
        if gi1 is None: gi1=gi0
        for gi in range(gi0, gi1+1):
            gset.add(gi)
        gl=sorted(gset)
        has_ffd2 = any(g_ffd2[gi] for gi in gl)
        has_name = any(g_nameisland[gi] for gi in gl)
        rblocks.append(dict(pc=r['pc'],off=off,cnt=cnt,groups=gl,
                            has_ffd2=has_ffd2,has_name=has_name))
        blocks.append(dict(res=rid,pc=r['pc'],groups=gl,has_ffd2=has_ffd2,has_name=has_name))
    res_summaries[rid]=dict(n_groups=len(groups),
                            g_ffd2=[gi for gi in range(len(groups)) if g_ffd2[gi]],
                            g_nameisland=[gi for gi in range(len(groups)) if g_nameisland[gi]],
                            n_blocks=len(rblocks))

print("=== CORPUS TOTALS ===")
print(f"type02 files scanned: {len(files)}")
print(f"total groups: {total_groups}")
print(f"groups with >=1 0xFFD2 (page break): {groups_with_ffd2}")
print(f"groups with >=1 0xFFFE (line break): {groups_with_fffe}")
print()
print("=== 0x04 DISPLAY_TEXT BLOCK CLASSIFICATION ===")
print(f"total DISPLAY_TEXT blocks (cnt>0): {len(blocks)}")
nh = sum(1 for b in blocks if b['has_name'])
nf = sum(1 for b in blocks if b['has_ffd2'])
print(f"blocks containing a name-island (0x14): {nh}")
print(f"blocks containing >=1 0xFFD2: {nf}")
# Cross tab
nn_nf = sum(1 for b in blocks if not b['has_name'] and b['has_ffd2'])
nn_n_nf = sum(1 for b in blocks if not b['has_name'] and not b['has_ffd2'])
hn_nf = sum(1 for b in blocks if b['has_name'] and b['has_ffd2'])
hn_n_nf = sum(1 for b in blocks if b['has_name'] and not b['has_ffd2'])
print()
print("CROSS-TAB (name-island x has-FFD2):")
print(f"  name=Y ffd2=Y : {hn_nf}")
print(f"  name=Y ffd2=N : {hn_n_nf}")
print(f"  name=N ffd2=Y : {nn_nf}   <-- CRITICAL: no name but JP used page break")
print(f"  name=N ffd2=N : {nn_n_nf}")
print()
print("=== CRITICAL: name=N ffd2=Y blocks (would these be narration false-positives?) ===")
crit=[b for b in blocks if not b['has_name'] and b['has_ffd2']]
for b in crit[:60]:
    print(f"  R{b['res']} pc=0x{b['pc']:X} groups={b['groups']}")
print(f"  ... total {len(crit)}")

# Save full data
json.dump({'res_summaries':res_summaries,
           'crit_blocks':[{'res':b['res'],'pc':b['pc'],'groups':b['groups']} for b in crit]},
          open('build/recon_pag/jp_pagination/scan_out.json','w'), indent=1)
