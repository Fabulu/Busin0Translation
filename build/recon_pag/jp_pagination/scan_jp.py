import sys, os, struct, glob, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records

HEADER_SIZE=0x20
RAW_DIR='extracted/packdata_raw'
def res_id(p): return int(os.path.basename(p).split('_')[0])
def load_sec(d):
    s=struct.unpack_from('<I',d,0x14)[0]; o=struct.unpack_from('<I',d,0x18)[0]
    return bytes(d[HEADER_SIZE:o]), bytes(d[o:o+s])
def parse_groups(sec2):
    n=len(sec2)//2; words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[];start=0
    for i,w in enumerate(words):
        if w==0xFFFF: groups.append((start,i)); start=i+1
    return groups,words,start
def find_group(groups,w):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=w<=ge: return gi
    return None

files=sorted(glob.glob(os.path.join(RAW_DIR,'*_type02.raw')))
total_groups=0; gffd2=0; gfffe=0
blocks=[]
# also collect: for each FFD2-containing group, is there a name-island in the SAME 0x04 block?
crit=[]
walk_fail=[]
for f in files:
    rid=res_id(f); d=open(f,'rb').read()
    try: sec1,sec2=load_sec(d)
    except: continue
    groups,words,trailing=parse_groups(sec2)
    if not groups: continue
    ok,instrs=walk(sec1)
    if not ok: walk_fail.append(rid)
    recs=extract_records(sec1,instrs)
    g_ffd2=[(0xFFD2 in words[gs:ge]) for gs,ge in groups]
    g_fffe=[(0xFFFE in words[gs:ge]) for gs,ge in groups]
    nameisland=set()
    for r in recs['label']:
        gi=find_group(groups,r['off'])
        if gi is not None: nameisland.add(gi)
    total_groups+=len(groups); gffd2+=sum(g_ffd2); gfffe+=sum(g_fffe)
    for r in recs['display']:
        off=r['off']; cnt=r['cnt']
        if cnt==0: continue
        gi0=find_group(groups,off)
        gi1=find_group(groups,min(off+cnt-1, groups[-1][1]))
        if gi0 is None: continue
        if gi1 is None: gi1=gi0
        gl=list(range(gi0,gi1+1))
        hf=any(g_ffd2[gi] for gi in gl)
        hn=any(gi in nameisland for gi in gl)
        blocks.append((rid,r['pc'],gl,hf,hn))

print("PRISTINE JP CORPUS")
print(f"files={len(files)} total_groups={total_groups} groups_w_FFD2={gffd2} groups_w_FFFE={gfffe}")
print(f"walk_fail resources: {walk_fail}")
print(f"total DISPLAY_TEXT blocks: {len(blocks)}")
hn_hf=sum(1 for b in blocks if b[4] and b[3])
hn_nf=sum(1 for b in blocks if b[4] and not b[3])
nn_hf=sum(1 for b in blocks if not b[4] and b[3])
nn_nf=sum(1 for b in blocks if not b[4] and not b[3])
print("CROSS-TAB name-island x FFD2:")
print(f"  name=Y ffd2=Y : {hn_hf}")
print(f"  name=Y ffd2=N : {hn_nf}")
print(f"  name=N ffd2=Y : {nn_hf}   <-- narration false-positive risk")
print(f"  name=N ffd2=N : {nn_nf}")
print()
print("name=N ffd2=Y blocks:")
for b in blocks:
    if not b[4] and b[3]:
        print(f"  R{b[0]} pc=0x{b[1]:X} groups={b[2]}")
json.dump([(b[0],b[1],b[2],b[3],b[4]) for b in blocks], open('build/recon_pag/jp_pagination/jp_blocks.json','w'))
